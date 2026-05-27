from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any


BLOCKING_SEVERITIES = {"ERROR", "CRITICAL", "HIGH"}


def load_semgrep_report(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _normalize_severity(value: Any) -> str:
    return str(value or "INFO").upper()


def _severity_from_native_result(result: dict[str, Any]) -> str:
    extra = result.get("extra", {}) or {}
    severity = extra.get("severity")

    if not severity:
        metadata = extra.get("metadata", {}) or {}
        severity = metadata.get("severity") or metadata.get("impact")

    return _normalize_severity(severity)


def _native_results(report: dict[str, Any]) -> list[dict[str, Any]]:
    results = report.get("results", [])
    return results if isinstance(results, list) else []


def _simplified_findings(report: dict[str, Any]) -> list[dict[str, Any]]:
    findings = report.get("findings", [])
    return findings if isinstance(findings, list) else []


def _report_ref(report_path: str | Path, report: dict[str, Any]) -> str:
    return str(report.get("report_ref") or f"semgrep_report:{Path(report_path).name}")


def _target(report: dict[str, Any], fallback: str) -> str:
    return str(report.get("target") or fallback)


def _commit(report: dict[str, Any], fallback: str) -> str:
    return str(report.get("commit") or fallback)


def _blocking_findings(report: dict[str, Any]) -> list[dict[str, Any]]:
    native = _native_results(report)
    if native:
        return [
            item for item in native
            if _severity_from_native_result(item) in BLOCKING_SEVERITIES
        ]

    simplified = _simplified_findings(report)
    if simplified:
        return [
            item for item in simplified
            if _normalize_severity(item.get("severity")) in BLOCKING_SEVERITIES
        ]

    critical = int(report.get("critical_findings") or 0)
    high = int(report.get("high_findings") or 0)
    if critical or high:
        return [
            {
                "id": "aggregate-count",
                "severity": "CRITICAL" if critical else "HIGH",
                "summary": f"Aggregate Semgrep report contains critical={critical}, high={high}.",
            }
        ]

    return []


def semgrep_to_partial_proof_vector(
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
    """Convert a Semgrep report into a partial AXIOM ProofVector.

    Important proof-hygiene rule:
    this connector only emits evidence Semgrep can actually support.

    It may emit:
    - security_scan_clean
    - scanner metadata
    - report reference
    - blocking findings
    - freshness timestamp

    It must not emit unrelated dimensions such as:
    - human_reviewed
    - rollback_available
    - unit_tests_passed
    - integration_tests_passed
    """

    report = load_semgrep_report(report_path)
    blocking = _blocking_findings(report)
    report_ref = _report_ref(report_path, report)
    clean = len(blocking) == 0

    scope = {
        "target": _target(report, target),
        "commit": _commit(report, commit),
        "branch": branch,
        "environment": environment,
    }
    if service:
        scope["service"] = service

    contradictions = []
    if not clean:
        contradictions.append(
            {
                "type": "security_scan_failure",
                "severity": "critical",
                "summary": f"Semgrep reported {len(blocking)} blocking finding(s).",
                "report_ref": report_ref,
            }
        )

    proof_vector = {
        "meta": {
            "proof_level": "P4_EXECUTED",
            "source_trust": source_trust,
            "freshness_epoch": int(now_epoch if now_epoch is not None else time.time()),
            "reproducibility": "reproducible",
            "independence": "single_source",
        },
        "scope": scope,
        "dimensions": {
            "security_scan_clean": {
                "status": "passed" if clean else "failed",
                "tool": "semgrep",
                "report_ref": report_ref,
                "blocking_findings": len(blocking),
                "total_findings": len(_native_results(report)) or len(_simplified_findings(report)),
            }
        },
        "security_evidence": {
            "scanner": "semgrep",
            "scan_status": "passed" if clean else "failed",
            "report_ref": report_ref,
            "blocking_findings": len(blocking),
            "total_findings": len(_native_results(report)) or len(_simplified_findings(report)),
        },
        "limitations": [],
        "contradictions": contradictions,
        "evidence_refs": [report_ref],
    }

    return proof_vector


def write_proof_vector(proof_vector: dict[str, Any], out_path: str | Path) -> None:
    path = Path(out_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(proof_vector, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
