from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from .enums import Decision, DimensionState, PROOF_LEVEL_ORDER
from .models import ActionRequest, PolicyDocument, ProofVector


@dataclass(frozen=True)
class PolicyEvaluation:
    decision: str
    reason: str
    missing_evidence: list[str] = field(default_factory=list)
    gap_reason: str = "No material proof gap."


class PolicyEngine:
    def __init__(self, now_epoch: int | None = None):
        self.now_epoch = now_epoch or int(time.time())

    def evaluate(self, *, action: dict, proof_vector: dict, policy: dict) -> PolicyEvaluation:
        action_model = ActionRequest.model_validate(action)
        proof_model = ProofVector.model_validate(proof_vector)
        policy_model = PolicyDocument.model_validate(policy)

        requirement = policy_model.requirement
        proof = proof_model

        required_level = requirement.min_meta.get("required_level", "P0_UNSUPPORTED")
        provided_level = proof.meta.proof_level

        # 1. Contradictions are a hard block.
        if proof.contradictions:
            return PolicyEvaluation(
                decision=Decision.BLOCK.value,
                reason="Contradicted evidence blocks the requested action.",
                missing_evidence=[f"contradiction:{item.get('type', 'unknown')}" for item in proof.contradictions],
                gap_reason="One or more evidence items contradict the requested action.",
            )

        # 2. Failed mandatory proof is different from missing proof.
        failed_dimensions = self._failed_dimensions(requirement.mandatory_dimensions, proof.dimensions)

        if (
            "security_scan_clean" in failed_dimensions
            and requirement.risk_policy.get("block_on_failed_security_scan", False)
        ):
            return PolicyEvaluation(
                decision=Decision.BLOCK.value,
                reason="Security scan failed and policy blocks execution.",
                missing_evidence=["security_scan_clean:failed"],
                gap_reason="A required security proof failed, so the action cannot be authorized.",
            )

        # 3. Numeric risk bound.
        final_weight = float(action_model.action_weight.get("final_weight", 0.0))
        max_risk_score = requirement.risk_policy.get("max_risk_score")
        if max_risk_score is not None and final_weight > float(max_risk_score):
            return PolicyEvaluation(
                decision=Decision.BLOCK.value,
                reason="Action weight exceeds the policy risk bound.",
                missing_evidence=[f"risk_bound_exceeded:{final_weight}>{max_risk_score}"],
                gap_reason="The action consequence weight exceeds the maximum risk permitted by policy.",
            )

        # 4. Missing mandatory dimensions.
        missing_evidence = self._missing_dimensions(requirement.mandatory_dimensions, proof.dimensions)

        # 5. Failed mandatory dimensions that are not hard-blocking become proof gaps.
        missing_evidence.extend(f"{item}:failed" for item in failed_dimensions if item not in {"security_scan_clean"})

        # 6. Scope.
        missing_evidence.extend(self._scope_mismatches(requirement.required_scope, proof.scope))

        # 7. Staleness.
        if self._stale_evidence(
            requirement.min_meta.get("max_age_seconds"),
            proof.meta.freshness_epoch,
        ):
            missing_evidence.append("stale_evidence")

        # 8. Limitations intersecting critical requirements.
        missing_evidence.extend(
            self._critical_limitation_intersections(
                requirement.critical_requirements,
                proof.limitations,
            )
        )

        # 9. Proof level.
        if self._level_value(provided_level) < self._level_value(required_level):
            missing_evidence.append(f"proof_level_below_required:{provided_level}<required:{required_level}")

        # 10. Decision.
        if missing_evidence:
            if set(missing_evidence) == {"human_reviewed"} or set(missing_evidence) == {"human_reviewed:failed"}:
                return PolicyEvaluation(
                    decision=Decision.REQUIRE_HUMAN_REVIEW.value,
                    reason="Human review is required before execution.",
                    missing_evidence=missing_evidence,
                    gap_reason="The only missing requirement is human review.",
                )

            return PolicyEvaluation(
                decision=Decision.SUSPEND.value,
                reason="Provided proof is not proportional to the consequence of the action.",
                missing_evidence=missing_evidence,
                gap_reason="Missing or insufficient proof prevents a valid Execution Warrant.",
            )

        return PolicyEvaluation(
            decision=Decision.ALLOW.value,
            reason="Proof covers the requirement vector for this action.",
            missing_evidence=[],
            gap_reason="No material proof gap.",
        )

    @staticmethod
    def _level_value(level: str | None) -> int:
        return PROOF_LEVEL_ORDER.get(level or "P0_UNSUPPORTED", 0)

    @staticmethod
    def _dimension_state(dimensions: dict[str, Any], name: str) -> str:
        if name not in dimensions:
            return DimensionState.MISSING.value

        value = dimensions.get(name)

        if value is True:
            return DimensionState.PASSED.value
        if value is False:
            return DimensionState.FAILED.value

        if isinstance(value, dict):
            status = str(value.get("status", "unknown")).lower()
            if status in {DimensionState.PASSED.value, "pass", "passed", "success", "ok"}:
                return DimensionState.PASSED.value
            if status in {DimensionState.FAILED.value, "fail", "failed", "error"}:
                return DimensionState.FAILED.value
            if status in {DimensionState.MISSING.value, "not_run", "not_available"}:
                return DimensionState.MISSING.value

        return DimensionState.UNKNOWN.value

    def _missing_dimensions(self, required: list[str], dimensions: dict[str, Any]) -> list[str]:
        missing: list[str] = []
        for dimension in required:
            state = self._dimension_state(dimensions, dimension)
            if state in {DimensionState.MISSING.value, DimensionState.UNKNOWN.value}:
                missing.append(dimension)
        return missing

    def _failed_dimensions(self, required: list[str], dimensions: dict[str, Any]) -> list[str]:
        failed: list[str] = []
        for dimension in required:
            if self._dimension_state(dimensions, dimension) == DimensionState.FAILED.value:
                failed.append(dimension)
        return failed

    @staticmethod
    def _scope_mismatches(required_scope: dict[str, Any], proof_scope: dict[str, Any]) -> list[str]:
        mismatches: list[str] = []
        for key, expected in required_scope.items():
            actual = proof_scope.get(key)
            if actual != expected:
                mismatches.append(f"scope_mismatch:{key}:expected={expected}:actual={actual}")
        return mismatches

    def _stale_evidence(self, max_age_seconds: int | None, freshness_epoch: int | None) -> bool:
        if not max_age_seconds or not freshness_epoch:
            return False
        return (self.now_epoch - int(freshness_epoch)) > int(max_age_seconds)

    @staticmethod
    def _critical_limitation_intersections(critical_requirements: list[str], limitations: list[dict[str, Any]]) -> list[str]:
        critical = set(critical_requirements or [])
        intersections: list[str] = []
        for limitation in limitations or []:
            domain = limitation.get("domain") or limitation.get("type")
            if domain in critical:
                intersections.append(f"limitation_intersects_critical_requirement:{domain}")
        return intersections
