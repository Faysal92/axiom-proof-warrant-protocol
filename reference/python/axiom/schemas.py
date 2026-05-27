from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from .models import (
    ActionRequest,
    ActionSpec,
    Actor,
    ExecutionWarrant,
    PolicyDocument,
    ProofVector,
    RequirementVector,
)


class AXIOMSchema(BaseModel):
    """Strict-enough schema base for enterprise integration inputs.

    We keep `extra="allow"` for forward compatibility across enterprises, but
    security decisions must only use fields that verifiers explicitly check.
    """

    model_config = ConfigDict(extra="allow")


class Claim(AXIOMSchema):
    """A claim made by an agent or workflow.

    A claim is not trusted. It is a pointer to evidence that must be checked by
    a Source Verifier before the policy kernel can rely on it.
    """

    claim_id: str
    type: str
    ref: str
    dimension: str
    source_hint: str | None = None
    required_status: str | None = None
    target: str | None = None
    environment: str | None = None
    max_age_hours: int | None = None
    min_approvals: int | None = None
    required_checks: list[str] = Field(default_factory=list)
    commit: str | None = None


class Evidence(AXIOMSchema):
    """Unverified evidence pointer.

    This object is useful for normalizers and adapters, but it is not sufficient
    to authorize an action until converted into VerifiedEvidence by a verifier.
    """

    claim_id: str
    source_provider: str
    source_kind: str
    ref: str
    payload: dict[str, Any] = Field(default_factory=dict)


class VerifiedEvidence(AXIOMSchema):
    """Evidence after source verification.

    This is the first object the AXIOM policy kernel is allowed to trust.
    """

    claim_id: str
    claim_type: str
    dimension: str
    status: Literal["passed", "failed", "missing", "expired", "unknown"]
    source_provider: str
    source_kind: str
    ref: str
    checked_at: int
    evidence_ref: str
    reason: str
    details: dict[str, Any] = Field(default_factory=dict)


class RiskProfile(AXIOMSchema):
    criticality: Literal["low", "medium", "high", "critical"] = "medium"
    blast_radius: str | None = None
    reversible: bool | None = None
    data_sensitivity: str | None = None
    score: float | None = None


class ActionEnvelope(AXIOMSchema):
    """Product-facing action envelope used by SDK/API flows.

    It extends the existing ActionRequest shape without breaking v0.1.x examples.
    """

    actor: Actor
    action: ActionSpec
    claim: dict[str, Any] = Field(default_factory=dict)
    action_weight: dict[str, Any] = Field(default_factory=dict)
    risk_profile: RiskProfile | None = None
    evidence_claims: list[Claim] = Field(default_factory=list)


class SourceBundle(AXIOMSchema):
    """Local/test source bundle used by the MVP source verifiers.

    Enterprise adapters can replace this with live API clients while keeping the
    same verifier outputs.
    """

    jira: dict[str, Any] = Field(default_factory=dict)
    github: dict[str, Any] = Field(default_factory=dict)
    ci: dict[str, Any] = Field(default_factory=dict)
    rollback: dict[str, Any] = Field(default_factory=dict)
    deployment_windows: dict[str, Any] = Field(default_factory=dict)
    cloud: dict[str, Any] = Field(default_factory=dict)


__all__ = [
    "ActionRequest",
    "ActionSpec",
    "Actor",
    "ExecutionWarrant",
    "PolicyDocument",
    "ProofVector",
    "RequirementVector",
    "Claim",
    "Evidence",
    "VerifiedEvidence",
    "RiskProfile",
    "ActionEnvelope",
    "SourceBundle",
]
