from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Iterable

import yaml

from .evaluator import evaluate
from .ledger import append_ledger_entry
from .models import ActionRequest
from .schemas import ActionEnvelope, Claim, SourceBundle, VerifiedEvidence
from .verifiers import DEFAULT_VERIFIERS, SourceVerifier


def load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_yaml(path: str | Path) -> dict[str, Any]:
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))


def action_scope(action_request: ActionEnvelope | dict[str, Any]) -> dict[str, Any]:
    envelope = action_request if isinstance(action_request, ActionEnvelope) else ActionEnvelope.model_validate(action_request)
    return {
        "action_type": envelope.action.action_type,
        "target": envelope.action.target,
        "environment": envelope.action.environment,
    }


def verify_action_claims(
    *,
    action_request: ActionEnvelope | dict[str, Any],
    sources: SourceBundle | dict[str, Any],
    verifiers: Iterable[SourceVerifier] | None = None,
) -> list[VerifiedEvidence]:
    """Verify agent claims against source-of-truth systems.

    The normalizer and Pydantic schemas can structure claims, but this function
    is what turns claims into trusted evidence.
    """
    envelope = action_request if isinstance(action_request, ActionEnvelope) else ActionEnvelope.model_validate(action_request)
    source_bundle = sources if isinstance(sources, SourceBundle) else SourceBundle.model_validate(sources)
    verifier_list = list(verifiers or DEFAULT_VERIFIERS)
    scope = action_scope(envelope)

    results: list[VerifiedEvidence] = []
    for claim in envelope.evidence_claims:
        handler = next((verifier for verifier in verifier_list if verifier.can_handle(claim)), None)
        if handler is None:
            results.append(
                VerifiedEvidence(
                    claim_id=claim.claim_id,
                    claim_type=claim.type,
                    dimension=claim.dimension,
                    status="unknown",
                    source_provider=claim.source_hint or "unknown",
                    source_kind=claim.type,
                    ref=claim.ref,
                    checked_at=int(time.time()),
                    evidence_ref=f"unknown:{claim.type}:{claim.ref}",
                    reason="No source verifier is registered for this claim type.",
                    details={},
                )
            )
            continue
        results.append(handler.verify(claim, source_bundle, action_scope=scope))

    return results


def verified_evidence_to_proof_vector(
    verified_evidence: list[VerifiedEvidence | dict[str, Any]],
    *,
    action_request: ActionEnvelope | dict[str, Any],
    proof_level: str = "P4_EXECUTED",
    source_trust: str = "high",
) -> dict[str, Any]:
    """Convert source-verified evidence into an AXIOM ProofVector."""
    envelope = action_request if isinstance(action_request, ActionEnvelope) else ActionEnvelope.model_validate(action_request)
    verified = [item if isinstance(item, VerifiedEvidence) else VerifiedEvidence.model_validate(item) for item in verified_evidence]
    now = int(time.time())

    dimensions: dict[str, Any] = {}
    evidence_refs: list[str] = []
    limitations: list[dict[str, Any]] = []
    contradictions: list[dict[str, Any]] = []

    for item in verified:
        dimensions[item.dimension] = {
            "status": item.status,
            "verified": item.status == "passed",
            "claim_id": item.claim_id,
            "claim_type": item.claim_type,
            "source_provider": item.source_provider,
            "source_kind": item.source_kind,
            "ref": item.ref,
            "checked_at": item.checked_at,
            "reason": item.reason,
            "details": item.details,
        }
        evidence_refs.append(item.evidence_ref)

        if item.status in {"missing", "expired", "unknown"}:
            limitations.append(
                {
                    "type": item.status,
                    "domain": item.dimension,
                    "source": item.evidence_ref,
                    "summary": item.reason,
                }
            )

        if item.status == "failed" and item.dimension == "security_scan_clean":
            contradictions.append(
                {
                    "type": "security_scan_failure",
                    "severity": "critical",
                    "source": item.evidence_ref,
                    "summary": item.reason,
                }
            )

    return {
        "meta": {
            "proof_level": proof_level,
            "source_trust": source_trust,
            "freshness_epoch": now,
            "reproducibility": "source_verified",
            "independence": "multi_source" if len({item.source_provider for item in verified}) > 1 else "single_source",
        },
        "scope": {
            "target": envelope.action.target,
            "environment": envelope.action.environment,
            "action_type": envelope.action.action_type,
        },
        "dimensions": dimensions,
        "limitations": limitations,
        "contradictions": contradictions,
        "evidence_refs": sorted(set(evidence_refs)),
        "source_verification": {
            "verified_claims": len(verified),
            "passed": sum(1 for item in verified if item.status == "passed"),
            "failed": sum(1 for item in verified if item.status == "failed"),
            "missing": sum(1 for item in verified if item.status == "missing"),
            "expired": sum(1 for item in verified if item.status == "expired"),
            "unknown": sum(1 for item in verified if item.status == "unknown"),
        },
    }


def evaluate_action_request(
    *,
    action_request: ActionEnvelope | dict[str, Any],
    sources: SourceBundle | dict[str, Any],
    policy: dict[str, Any],
    ledger_path: str | Path | None = None,
) -> dict[str, Any]:
    """End-to-end product API: action request + source data -> warrant."""
    envelope = action_request if isinstance(action_request, ActionEnvelope) else ActionEnvelope.model_validate(action_request)
    verified = verify_action_claims(action_request=envelope, sources=sources)
    proof_vector = verified_evidence_to_proof_vector(verified, action_request=envelope)

    # Existing evaluator expects the v0.1 action schema. Extra fields remain in
    # the ActionEnvelope, but the kernel only receives the minimal action object.
    action_for_kernel = ActionRequest(
        actor=envelope.actor,
        action=envelope.action,
        claim=envelope.claim,
        action_weight=envelope.action_weight,
    ).model_dump(mode="json")

    warrant = evaluate(action=action_for_kernel, proof_vector=proof_vector, policy=policy)
    if ledger_path:
        append_ledger_entry(Path(ledger_path), warrant)

    return {
        "verified_evidence": [item.model_dump(mode="json") for item in verified],
        "proof_vector": proof_vector,
        "warrant": warrant,
    }
