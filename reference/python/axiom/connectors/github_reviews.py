from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any


def load_github_reviews_report(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _reviews(report: dict[str, Any]) -> list[dict[str, Any]]:
    reviews = report.get("reviews") or report.get("pull_request_reviews") or []
    return reviews if isinstance(reviews, list) else []


def github_reviews_to_partial_proof_vector(
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
    """Convert a GitHub PR review report into a partial ProofVector.

    Proof hygiene rule:
    this connector only emits review-owned evidence.

    It may emit:
    - human_reviewed
    - reviewer metadata and PR review refs

    It must not emit:
    - security_scan_clean
    - unit_tests_passed
    - integration_tests_passed
    - rollback_available
    """

    report = load_github_reviews_report(report_path)
    reviews = _reviews(report)
    approvals = [r for r in reviews if str(r.get("state") or "").upper() == "APPROVED"]

    pr_number = report.get("pr_number") or report.get("pull_request") or "unknown"
    review_refs = [
        f"github_pr_review:{pr_number}:{r.get('id') or r.get('review_id') or index}"
        for index, r in enumerate(approvals, start=1)
    ]

    status = "passed" if approvals else "failed"

    scope = {
        "target": str(report.get("target") or target),
        "commit": str(commit or report.get("head_sha") or report.get("commit") or "unknown"),
        "branch": str(branch or report.get("branch") or "main"),
        "environment": environment,
    }
    if service:
        scope["service"] = service

    limitations = []
    if not approvals:
        limitations.append({
            "type": "missing_human_review",
            "domain": "human_reviewed",
            "severity": "high",
            "summary": "No APPROVED GitHub PR review was found.",
        })

    return {
        "meta": {
            "proof_level": "P4_EXECUTED",
            "source_trust": source_trust,
            "freshness_epoch": int(now_epoch if now_epoch is not None else time.time()),
            "reproducibility": "reproducible",
            "independence": "single_source",
        },
        "scope": scope,
        "dimensions": {
            "human_reviewed": {
                "status": status,
                "tool": "github_pull_request_review",
                "approved_reviews": len(approvals),
                "review_refs": review_refs,
            }
        },
        "limitations": limitations,
        "contradictions": [],
        "evidence_refs": review_refs or [f"github_pr_review:{pr_number}:none"],
        "review_evidence": {
            "provider": "github",
            "report_ref": str(report_path),
            "pr_number": pr_number,
            "approved_reviews": len(approvals),
        },
    }
