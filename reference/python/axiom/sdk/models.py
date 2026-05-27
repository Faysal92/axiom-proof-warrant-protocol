from __future__ import annotations

import hashlib
import hmac
import json
import os
import time
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


Decision = Literal["ALLOW", "SUSPEND", "DENY", "ESCALATE"]
VerificationStatus = Literal["PASSED", "WARNING", "FAILED", "MISSING"]
InputMode = Literal["paste_context", "upload_bundle", "canonical_envelope"]


class AxiomStrictModel(BaseModel):
    """Strict base model.

    This forbids hidden fields like:
    {"verification_status": "unverified", "verified": true}
    """

    model_config = ConfigDict(extra="forbid")


class RawEnterpriseContext(AxiomStrictModel):
    """Flexible intake object.

    This accepts messy enterprise context. It never represents verified proof.
    """

    input_mode: InputMode = "paste_context"
    raw_text: str | None = None
    raw_bundle: dict[str, Any] | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ExtractedAction(AxiomStrictModel):
    """Action intent extracted from raw context.

    None means unknown. The normalizer must not invent identifiers.
    """

    domain: str | None = None
    actor_id: str | None = None
    actor_type: str | None = None
    action_type: str | None = None
    target: str | None = None
    environment: str | None = None
    raw_text: str | None = None


class ExtractedClaim(AxiomStrictModel):
    """Agent-declared claim, never verified at intake stage."""

    claim_id: str
    claim_type: str
    source_hint: str | None = None
    identifiers: dict[str, Any] = Field(default_factory=dict)
    claimed_value: Any | None = None
    verification_status: Literal["unverified"] = "unverified"
    raw_text: str
    confidence: Literal["low", "medium", "high"] = "medium"


class NormalizedDraft(AxiomStrictModel):
    """Output of the normalizer.

    This object is structured but still untrusted.
    """

    extracted_action: ExtractedAction | None = None
    extracted_claims: list[ExtractedClaim] = Field(default_factory=list)
    missing_structural_fields: list[str] = Field(default_factory=list)
    ambiguities: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    raw_references: list[dict[str, Any]] = Field(default_factory=list)
    confidence: Literal["low", "medium", "high"] = "medium"


class SanitizedDraft(AxiomStrictModel):
    """Output of the SafetySanitizer.

    Still not verified proof. Only safe enough to build an envelope.
    """

    extracted_action: ExtractedAction | None = None
    extracted_claims: list[ExtractedClaim] = Field(default_factory=list)
    rejected_items: list[dict[str, Any]] = Field(default_factory=list)
    missing_structural_fields: list[str] = Field(default_factory=list)
    ambiguities: list[str] = Field(default_factory=list)
    sanitizer_warnings: list[str] = Field(default_factory=list)
    safe_to_build_envelope: bool = False


class CanonicalActionEnvelope(AxiomStrictModel):
    """Stable SDK boundary between flexible intake and runtime governance."""

    domain: str | None = None
    action_request: dict[str, Any]
    claims: list[ExtractedClaim] = Field(default_factory=list)
    missing_structural_fields: list[str] = Field(default_factory=list)
    ambiguities: list[str] = Field(default_factory=list)
    source_hints: list[str] = Field(default_factory=list)


class VerificationDetail(AxiomStrictModel):
    """Source verifier output."""

    claim_id: str | None = None
    claim_type: str | None = None
    source_name: str
    status: VerificationStatus
    message: str
    payload_snapshot: dict[str, Any] = Field(default_factory=dict)


class DeclaredVsVerifiedRow(AxiomStrictModel):
    """UI-friendly comparison row."""

    label: str
    declared: str
    source_hint: str | None = None
    verified: str
    status: Literal["verified", "warning", "conflict", "missing"]


class ExecutionWarrant(AxiomStrictModel):
    protocol_version: str = "axiom-proof-warrant-v0.1.7"
    warrant_id: str
    decision: Decision
    reason: str
    action_request: dict[str, Any]
    missing_evidence: list[str] = Field(default_factory=list)
    verified_evidence_hash: str
    policy_id: str | None = "demo-cross-domain-policy-v0.1.7"
    issued_at_epoch: int
    signature: str


class LedgerPreview(AxiomStrictModel):
    ledger_action: Literal["APPEND"] = "APPEND"
    warrant_id: str
    decision: Decision
    warrant_hash: str
    audit_note: str


class AxiomRuntimeResult(AxiomStrictModel):
    raw_context: RawEnterpriseContext
    normalized_draft: NormalizedDraft
    sanitized_draft: SanitizedDraft
    envelope: CanonicalActionEnvelope
    declared_vs_verified: list[DeclaredVsVerifiedRow]
    verified_sources: list[VerificationDetail]
    decision: Decision
    reason: str
    warrant: ExecutionWarrant
    ledger_preview: LedgerPreview


def canonical_json(value: Any) -> str:
    if isinstance(value, BaseModel):
        value = value.model_dump(mode="json")
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_hex(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def sign_warrant(payload: dict[str, Any]) -> str:
    secret = os.getenv("AXIOM_WARRANT_SECRET", "axiom-demo-secret-change-me")
    return hmac.new(
        secret.encode("utf-8"),
        canonical_json(payload).encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def issue_warrant(
    decision: Decision,
    reason: str,
    action_request: dict[str, Any],
    missing_evidence: list[str],
    verified_sources: list[VerificationDetail],
    policy_id: str | None = "demo-cross-domain-policy-v0.1.7",
) -> ExecutionWarrant:
    issued_at = int(time.time())
    verified_evidence_hash = sha256_hex([v.model_dump(mode="json") for v in verified_sources])

    unsigned = {
        "protocol_version": "axiom-proof-warrant-v0.1.7",
        "decision": decision,
        "reason": reason,
        "action_request": action_request,
        "missing_evidence": missing_evidence,
        "verified_evidence_hash": verified_evidence_hash,
        "policy_id": policy_id,
        "issued_at_epoch": issued_at,
    }

    warrant_id = f"wrn_{sha256_hex(unsigned)[:12]}"
    signature = sign_warrant({**unsigned, "warrant_id": warrant_id})

    return ExecutionWarrant(
        warrant_id=warrant_id,
        decision=decision,
        reason=reason,
        action_request=action_request,
        missing_evidence=missing_evidence,
        verified_evidence_hash=verified_evidence_hash,
        policy_id=policy_id,
        issued_at_epoch=issued_at,
        signature=signature,
    )
