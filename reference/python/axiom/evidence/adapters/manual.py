"""
AXIOM Evidence Adapter — Manual / Generic JSON

The escape hatch for any source AXIOM doesn't have a native adapter for:
    GitLab CI, Jenkins, SIEM, EDR, Terraform plan, Kubernetes events,
    internal approval systems, external APIs, custom scripts.

Input: a JSON file with a `claims` dict and optional metadata.

Schema:
{
  "provider": "gitlab",          // optional, defaults to "manual"
  "kind": "pipeline",            // optional, defaults to "manual_evidence"
  "ref": "pipeline:98765",       // optional
  "target": "payment-api",       // optional
  "environment": "production",   // optional
  "commit": "sha123",            // optional
  "branch": "main",              // optional
  "claims": {
    "unit_tests_passed": {"status": "passed", "ref": "gitlab_job:123"},
    "integration_tests_passed": {"status": "passed", "ref": "gitlab_job:124"}
  },
  "evidence_refs": ["gitlab_pipeline:98765"],   // optional
  "limitations": [],                             // optional
  "contradictions": []                           // optional
}

Adapter law:
    The manual adapter emits exactly what the JSON file claims, no more.
    The caller is responsible for claim accuracy.
    Proof hygiene is enforced by policy, not by the adapter.
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
    source_trust: str = "medium",
    now_epoch: int | None = None,
) -> dict[str, Any]:
    report = json.loads(Path(report_path).read_text(encoding="utf-8"))
    collected_at = int(now_epoch if now_epoch is not None else time.time())

    claims = report.get("claims")
    if not isinstance(claims, dict) or not claims:
        raise ValueError(
            f"Manual evidence adapter requires a non-empty 'claims' dict in {report_path}. "
            "Example: {\"claims\": {\"unit_tests_passed\": {\"status\": \"passed\"}}}"
        )

    provider = str(report.get("provider") or "manual")
    kind = str(report.get("kind") or "manual_evidence")
    ref = str(report.get("ref") or f"manual_evidence:{Path(report_path).name}")
    evidence_refs = list(report.get("evidence_refs") or [ref])

    scope = {
        "target": str(report.get("target") or target),
        "commit": str(commit or report.get("commit") or "unknown"),
        "branch": str(branch or report.get("branch") or "main"),
        "environment": str(report.get("environment") or environment),
    }
    if service:
        scope["service"] = service

    return partial_proof_vector(
        source=source_block(provider=provider, kind=kind, ref=ref, collected_at=collected_at),
        claims=claims,
        evidence_refs=evidence_refs,
        scope=scope,
        limitations=list(report.get("limitations") or []),
        contradictions=list(report.get("contradictions") or []),
        proof_level=str(report.get("proof_level") or "P3_CROSS_CHECKED"),
        source_trust=source_trust,
        freshness_epoch=collected_at,
    )
