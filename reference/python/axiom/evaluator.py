from __future__ import annotations

from .policy_engine import PolicyEngine
from .warrant import build_warrant


def evaluate(
    *,
    action: dict,
    proof_vector: dict,
    policy: dict,
    now_epoch: int | None = None,
) -> dict:
    engine = PolicyEngine(now_epoch=now_epoch)
    result = engine.evaluate(action=action, proof_vector=proof_vector, policy=policy)

    requirement = policy.get("requirement", policy)

    return build_warrant(
        action=action,
        proof_vector=proof_vector,
        requirement_vector=requirement,
        decision=result.decision,
        reason=result.reason,
        missing_evidence=result.missing_evidence,
        gap_reason=result.gap_reason,
    )
