"""
AXIOM Evidence Adapter — Rollback Plan

Provider-agnostic: any rollback artifact (JSON file, API response, CI artifact).

Adapter law — may only emit:
    rollback_available
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from axiom.evidence.canonical import partial_proof_vector, source_block


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
    collected_at = int(now_epoch if now_epoch is not None else time.time())

    available = bool(report.get("rollback_available") or report.get("available"))
    verified = bool(report.get("verified", available))
    plan_ref = str(report.get("plan_ref") or f"rollback_plan:{Path(report_path).name}")
    status = "passed" if (available and verified) else "failed"

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
        limitations.append({"type": "rollback_unavailable", "domain": "rollback_available",
                             "severity": "high", "summary": "Rollback plan missing, unavailable, or unverified."})

    return partial_proof_vector(
        source=source_block(provider="rollback_registry", kind="rollback_plan", ref=plan_ref, collected_at=collected_at),
        claims={
            "rollback_available": {
                "status": status, "artifact": plan_ref,
                "verified": verified, "strategy": report.get("strategy") or "unknown",
            }
        },
        evidence_refs=[plan_ref],
        scope=scope,
        limitations=limitations,
        proof_level="P4_EXECUTED" if status == "passed" else "P2_SOURCE_BACKED",
        source_trust=source_trust,
        freshness_epoch=collected_at,
        extra={"rollback_evidence": {"report_ref": str(report_path), "plan_ref": plan_ref,
                                      "available": available, "verified": verified}},
    )
