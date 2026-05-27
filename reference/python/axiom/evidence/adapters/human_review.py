"""
AXIOM Evidence Adapter — Human Review (GitHub PR, GitLab MR, manual approval)

Provider-agnostic: normalizes review/approval data from any source.

Adapter law — may only emit:
    human_reviewed

Must not emit:
    security_scan_clean, unit_tests_passed, integration_tests_passed, rollback_available
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from axiom.evidence.canonical import partial_proof_vector, source_block


def _detect_provider(report: dict) -> str:
    if report.get("merge_request_iid") or report.get("gitlab_project_id"):
        return "gitlab"
    if "pull_request" in report or "pr_number" in report or "reviews" in report:
        return "github"
    return report.get("provider", "manual")


def _extract_approvals(report: dict) -> list[dict]:
    reviews = report.get("reviews") or report.get("approvals") or report.get("pull_request_reviews") or []
    if not isinstance(reviews, list):
        return []
    return [r for r in reviews if str(r.get("state") or r.get("status") or "").upper() in {"APPROVED", "APPROVE"}]


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
    provider = _detect_provider(report)
    collected_at = int(now_epoch if now_epoch is not None else time.time())

    approvals = _extract_approvals(report)
    pr_ref = str(report.get("pr_number") or report.get("merge_request_iid") or report.get("ref") or "unknown")
    review_refs = [
        f"{provider}_review:{pr_ref}:{r.get('id') or r.get('review_id') or i}"
        for i, r in enumerate(approvals, 1)
    ]

    status = "passed" if approvals else "failed"
    limitations = []
    if not approvals:
        limitations.append({"type": "missing_human_review", "domain": "human_reviewed",
                             "severity": "high", "summary": f"No approved review found in {provider}."})

    scope = {
        "target": str(report.get("target") or target),
        "commit": str(commit or report.get("head_sha") or report.get("commit") or "unknown"),
        "branch": str(branch or report.get("branch") or "main"),
        "environment": environment,
    }
    if service:
        scope["service"] = service

    report_ref = f"{provider}_review_report:{Path(report_path).name}"

    return partial_proof_vector(
        source=source_block(provider=provider, kind="human_review", ref=report_ref, collected_at=collected_at),
        claims={
            "human_reviewed": {
                "status": status,
                "tool": provider,
                "approved_reviews": len(approvals),
                "review_refs": review_refs,
            }
        },
        evidence_refs=review_refs or [f"{provider}_review:{pr_ref}:none"],
        scope=scope,
        limitations=limitations,
        proof_level="P4_EXECUTED",
        source_trust=source_trust,
        freshness_epoch=collected_at,
        extra={"review_evidence": {"provider": provider, "report_ref": report_ref,
                                    "pr_ref": pr_ref, "approved_reviews": len(approvals)}},
    )
