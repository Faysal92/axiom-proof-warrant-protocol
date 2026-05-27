"""
AXIOM Evidence Adapter — CI Checks (GitHub Actions, GitLab Pipelines, Jenkins)

Provider-agnostic: normalizes CI output from any provider into canonical proof.
Input format: JSON with a `check_runs` or `checks` array, or simplified key-value outcomes.

Adapter law — may only emit:
    unit_tests_passed, integration_tests_passed

Must not emit:
    security_scan_clean, human_reviewed, rollback_available
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from axiom.evidence.canonical import partial_proof_vector, source_block


def _normalize_conclusion(value: Any) -> str:
    v = str(value or "").lower()
    if v in {"success", "passed", "pass", "ok"}:
        return "passed"
    if v in {"failure", "failed", "fail", "error", "cancelled"}:
        return "failed"
    return v


def _find_check(checks: list[dict], keywords: tuple[str, ...]) -> dict | None:
    for c in checks:
        name = str(c.get("name") or c.get("check_name") or "").lower()
        if any(k in name for k in keywords):
            return c
    return None


def _check_ref(check: dict, prefix: str) -> str:
    run_id = check.get("run_id") or check.get("id") or check.get("external_id") or "unknown"
    name = check.get("name") or check.get("check_name") or prefix
    return f"ci_check:{run_id}:{name}"


def _detect_provider(report: dict) -> str:
    if report.get("gitlab_pipeline_id") or report.get("pipeline_source"):
        return "gitlab"
    if report.get("jenkins_build_id") or report.get("jenkins_url"):
        return "jenkins"
    if report.get("github_run_id") or "check_runs" in report:
        return "github_actions"
    return report.get("provider", "ci")


def from_report(
    report_path: str | Path,
    *,
    target: str = "unknown-target",
    environment: str = "unknown",
    commit: str | None = None,
    branch: str | None = None,
    service: str | None = None,
    source_trust: str = "high",
    now_epoch: int | None = None,
) -> dict[str, Any]:
    report = json.loads(Path(report_path).read_text(encoding="utf-8"))
    checks = report.get("check_runs") or report.get("checks") or report.get("jobs") or []
    if not isinstance(checks, list):
        checks = []

    provider = _detect_provider(report)
    collected_at = int(now_epoch if now_epoch is not None else time.time())

    unit_check = _find_check(checks, ("unit", "pytest", "test-unit", "tests-unit"))
    integration_check = _find_check(checks, ("integration", "e2e", "test-integration", "tests-integration"))

    claims: dict[str, Any] = {}
    evidence_refs: list[str] = []
    limitations: list[dict[str, Any]] = []

    if unit_check is not None:
        status = _normalize_conclusion(unit_check.get("conclusion") or unit_check.get("status"))
        ref = _check_ref(unit_check, "unit_tests")
        evidence_refs.append(ref)
        claims["unit_tests_passed"] = {"status": status, "tool": provider, "ref": ref,
                                        "name": unit_check.get("name")}
    else:
        limitations.append({"type": "missing_ci_check", "domain": "unit_tests",
                             "severity": "medium", "summary": "No unit test check found."})

    if integration_check is not None:
        status = _normalize_conclusion(integration_check.get("conclusion") or integration_check.get("status"))
        ref = _check_ref(integration_check, "integration_tests")
        evidence_refs.append(ref)
        claims["integration_tests_passed"] = {"status": status, "tool": provider, "ref": ref,
                                               "name": integration_check.get("name")}
    else:
        limitations.append({"type": "missing_ci_check", "domain": "integration_tests",
                             "severity": "medium", "summary": "No integration test check found."})

    scope = {
        "target": str(report.get("target") or target),
        "commit": str(commit or report.get("head_sha") or report.get("commit") or "unknown"),
        "branch": str(branch or report.get("branch") or "main"),
        "environment": environment,
    }
    if service:
        scope["service"] = service

    report_ref = f"ci_report:{Path(report_path).name}"

    return partial_proof_vector(
        source=source_block(provider=provider, kind="ci_checks", ref=report_ref, collected_at=collected_at),
        claims=claims,
        evidence_refs=evidence_refs,
        scope=scope,
        limitations=limitations,
        proof_level="P4_EXECUTED",
        source_trust=source_trust,
        freshness_epoch=collected_at,
        extra={"ci_evidence": {"provider": provider, "report_ref": report_ref, "total_checks": len(checks)}},
    )
