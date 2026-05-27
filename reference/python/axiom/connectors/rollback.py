from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any


def load_rollback_report(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def rollback_to_partial_proof_vector(
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
    """Convert a rollback plan artifact into a partial ProofVector.

    Proof hygiene rule:
    this connector only emits rollback-owned evidence.
    """

    report = load_rollback_report(report_path)
    available = bool(report.get("rollback_available") or report.get("available"))
    verified = bool(report.get("verified", available))
    plan_ref = str(report.get("plan_ref") or f"rollback_plan:{Path(report_path).name}")
    status = "passed" if available and verified else "failed"

    scope = {
        "target": str(report.get("target") or target),
        "commit": str(commit or report.get("commit") or "unknown"),
        "branch": str(branch or report.get("branch") or "main"),
        "environment": str(report.get("environment") or environment),
    }
    if service:
        scope["service"] = service

    limitations = []
    if status != "passed":
        limitations.append({
            "type": "rollback_unavailable",
            "domain": "rollback_available",
            "severity": "high",
            "summary": "Rollback plan is missing, unavailable, or unverified.",
        })

    return {
        "meta": {
            "proof_level": "P4_EXECUTED" if status == "passed" else "P2_SOURCE_BACKED",
            "source_trust": source_trust,
            "freshness_epoch": int(now_epoch if now_epoch is not None else time.time()),
            "reproducibility": "reproducible",
            "independence": "single_source",
        },
        "scope": scope,
        "dimensions": {
            "rollback_available": {
                "status": status,
                "artifact": plan_ref,
                "verified": verified,
                "strategy": report.get("strategy") or "unknown",
            }
        },
        "limitations": limitations,
        "contradictions": [],
        "evidence_refs": [plan_ref],
        "rollback_evidence": {
            "report_ref": str(report_path),
            "plan_ref": plan_ref,
            "available": available,
            "verified": verified,
        },
    }
