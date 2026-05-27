from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any


def load_github_checks_report(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _is_successful_check(check: dict[str, Any]) -> bool:
    conclusion = str(check.get("conclusion") or check.get("status") or "").lower()
    return conclusion in {"success", "passed", "pass", "ok"}


def _check_name(check: dict[str, Any]) -> str:
    return str(check.get("name") or check.get("check_name") or "").lower()


def _find_check(checks: list[dict[str, Any]], keywords: tuple[str, ...]) -> dict[str, Any] | None:
    for check in checks:
        name = _check_name(check)
        if any(keyword in name for keyword in keywords):
            return check
    return None


def _check_ref(check: dict[str, Any], fallback_prefix: str) -> str:
    run_id = check.get("run_id") or check.get("id") or check.get("external_id") or "unknown"
    name = check.get("name") or check.get("check_name") or fallback_prefix
    return f"github_check:{run_id}:{name}"


def github_checks_to_partial_proof_vector(
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
    """Convert a GitHub Checks / GitHub Actions report into a partial ProofVector.

    Proof hygiene rule:
    this connector only emits CI-owned evidence.

    It may emit:
    - unit_tests_passed
    - integration_tests_passed
    - CI metadata and evidence refs

    It must not emit:
    - security_scan_clean
    - human_reviewed
    - rollback_available
    """

    report = load_github_checks_report(report_path)
    checks = report.get("check_runs") or report.get("checks") or []
    if not isinstance(checks, list):
        checks = []

    unit_check = _find_check(checks, ("unit", "pytest", "test-unit"))
    integration_check = _find_check(checks, ("integration", "e2e", "test-integration"))

    dimensions: dict[str, Any] = {}
    evidence_refs: list[str] = []
    limitations: list[dict[str, Any]] = []

    if unit_check is not None:
        passed = _is_successful_check(unit_check)
        ref = _check_ref(unit_check, "unit_tests")
        evidence_refs.append(ref)
        dimensions["unit_tests_passed"] = {
            "status": "passed" if passed else "failed",
            "tool": "github_actions",
            "ref": ref,
            "name": unit_check.get("name") or unit_check.get("check_name"),
            "conclusion": unit_check.get("conclusion") or unit_check.get("status"),
        }
    else:
        limitations.append({
            "type": "missing_ci_check",
            "domain": "unit_tests",
            "severity": "medium",
            "summary": "No unit test check was found in the GitHub checks report.",
        })

    if integration_check is not None:
        passed = _is_successful_check(integration_check)
        ref = _check_ref(integration_check, "integration_tests")
        evidence_refs.append(ref)
        dimensions["integration_tests_passed"] = {
            "status": "passed" if passed else "failed",
            "tool": "github_actions",
            "ref": ref,
            "name": integration_check.get("name") or integration_check.get("check_name"),
            "conclusion": integration_check.get("conclusion") or integration_check.get("status"),
        }
    else:
        limitations.append({
            "type": "missing_ci_check",
            "domain": "integration_tests",
            "severity": "medium",
            "summary": "No integration test check was found in the GitHub checks report.",
        })

    scope = {
        "target": str(report.get("target") or target),
        "commit": str(commit or report.get("head_sha") or report.get("commit") or "unknown"),
        "branch": str(branch or report.get("branch") or "main"),
        "environment": environment,
    }
    if service:
        scope["service"] = service

    return {
        "meta": {
            "proof_level": "P4_EXECUTED",
            "source_trust": source_trust,
            "freshness_epoch": int(now_epoch if now_epoch is not None else time.time()),
            "reproducibility": "reproducible",
            "independence": "single_source",
        },
        "scope": scope,
        "dimensions": dimensions,
        "limitations": limitations,
        "contradictions": [],
        "evidence_refs": evidence_refs,
        "ci_evidence": {
            "provider": "github_actions",
            "report_ref": str(report_path),
            "total_checks": len(checks),
        },
    }
