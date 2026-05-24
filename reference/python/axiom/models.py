from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class AXIOMModel(BaseModel):
    model_config = ConfigDict(extra="allow", frozen=True)


class Actor(AXIOMModel):
    actor_id: str
    actor_type: str
    identity_verified: bool = False


class ActionSpec(AXIOMModel):
    action_type: str
    target: str
    environment: str = "unknown"


class ActionRequest(AXIOMModel):
    actor: Actor
    action: ActionSpec
    claim: dict[str, Any] = Field(default_factory=dict)
    action_weight: dict[str, Any] = Field(default_factory=dict)


class ProofMeta(AXIOMModel):
    proof_level: str
    source_trust: str | None = None
    freshness_epoch: int | None = None
    reproducibility: str | None = None
    independence: str | None = None


class ProofVector(AXIOMModel):
    meta: ProofMeta
    scope: dict[str, Any] = Field(default_factory=dict)
    dimensions: dict[str, Any] = Field(default_factory=dict)
    limitations: list[dict[str, Any]] = Field(default_factory=list)
    contradictions: list[dict[str, Any]] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)


class RequirementVector(AXIOMModel):
    action: str
    target: str
    context: dict[str, Any] = Field(default_factory=dict)
    min_meta: dict[str, Any] = Field(default_factory=dict)
    required_scope: dict[str, Any] = Field(default_factory=dict)
    mandatory_dimensions: list[str] = Field(default_factory=list)
    critical_requirements: list[str] = Field(default_factory=list)
    risk_policy: dict[str, Any] = Field(default_factory=dict)


class PolicyDocument(AXIOMModel):
    policy_id: str = "unknown_policy"
    policy_version: str = "0.0.0"
    requirement: RequirementVector


class ChallengeResponse(AXIOMModel):
    resubmit_allowed: bool
    missing_evidence: list[str] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)


class ExecutionWarrant(AXIOMModel):
    warrant_id: str
    protocol_version: str
    warrant_type: Literal["EXECUTION_WARRANT"]
    status: str
    created_at: datetime | str
    expires_at: datetime | str
    actor: dict[str, Any]
    action: dict[str, Any]
    claim: dict[str, Any] = Field(default_factory=dict)
    action_weight: dict[str, Any] = Field(default_factory=dict)
    required_proof: dict[str, Any]
    provided_proof: dict[str, Any]
    missing_evidence: list[str]
    proof_gap: dict[str, Any]
    decision: str
    reason: str
    challenge: dict[str, Any]
    ledger: dict[str, Any]
    signature: dict[str, Any]
