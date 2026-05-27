"""
AXIOM Evidence Adapter — Semgrep / SAST Scanner

Provider-agnostic: any SAST tool that produces compatible JSON can use this adapter.
Compatible output format: Semgrep JSON, or simplified summary with critical_findings/high_findings.

Adapter law — may only emit:
    security_scan_clean

Must not emit:
    human_reviewed, unit_tests_passed, integration_tests_passed, rollback_available
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from axiom.evidence.canonical import partial_proof_vector, source_block

BLOCKING_SEVERITIES = {"ERROR", "CRITICAL", "HIGH"}


def _normalize_severity(value: Any) -> str:
    return str(value or "INFO").upper()


def _severity_from_native_result(result: dict[str, Any]) -> str:
    extra = result.get("extra", {}) or {}
    severity = extra.get("severity")
    if not severity:
        metadata = extra.get("metadata", {}) or {}
        severity = metadata.get("severity") or metadata.get("impact")
    return _normalize_severity(severity)


def _blocking_findings(report: dict[str, Any]) -> list[dict[str, Any]]:
    native = report.get("results", [])
    if isinstance(native, list) and native:
        return [r for r in native if _severity_from_native_result(r) in BLOCKING_SEVERITIES]

    simplified = report.get("findings", [])
    if isinstance(simplified, list) and simplified:
        return [r for r in simplified if _normalize_severity(r.get("severity")) in BLOCKING_SEVERITIES]

    critical = int(report.get("critical_findings") or 0)
    high = int(report.get("high_findings") or 0)
    if critical or high:
        return [{"id": "aggregate", "severity": "CRITICAL" if critical else "HIGH",
                 "summary": f"critical={critical}, high={high}"}]
    return []


def from_report(
    report_path: str | Path,
    *,
    target: str = "unknown-target",
    environment: str = "unknown",
    commit: str = "unknown",
    branch: str = "main",
    service: str | None = None,
    source_trust: str = "high",
    now_epoch: int | None = None,
) -> dict[str, Any]:
    report = json.loads(Path(report_path).read_text(encoding="utf-8"))
    blocking = _blocking_findings(report)
    clean = len(blocking) == 0
    report_ref = str(report.get("report_ref") or f"semgrep_report:{Path(report_path).name}")
    collected_at = int(now_epoch if now_epoch is not None else time.time())

    scope = {"target": str(report.get("target") or target), "commit": str(report.get("commit") or commit),
             "branch": branch, "environment": environment}
    if service:
        scope["service"] = service

    contradictions = []
    if not clean:
        contradictions.append({"type": "security_scan_failure", "severity": "critical",
                                "summary": f"Semgrep: {len(blocking)} blocking finding(s).",
                                "report_ref": report_ref})

    return partial_proof_vector(
        source=source_block(provider="semgrep", kind="sast_scan", ref=report_ref, collected_at=collected_at),
        claims={
            "security_scan_clean": {
                "status": "passed" if clean else "failed",
                "tool": "semgrep",
                "report_ref": report_ref,
                "blocking_findings": len(blocking),
            }
        },
        evidence_refs=[report_ref],
        scope=scope,
        contradictions=contradictions,
        proof_level="P4_EXECUTED",
        source_trust=source_trust,
        freshness_epoch=collected_at,
        extra={
            "security_evidence": {
                "scanner": "semgrep", "scan_status": "passed" if clean else "failed",
                "report_ref": report_ref, "blocking_findings": len(blocking),
            }
        },
    )
