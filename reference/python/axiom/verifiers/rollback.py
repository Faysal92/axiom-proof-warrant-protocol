from __future__ import annotations

from axiom.schemas import Claim, SourceBundle, VerifiedEvidence
from .base import EXPIRED, FAILED, MISSING, PASSED, SourceVerifier, find_by_id, is_fresh, scope_matches


class RollbackPlanVerifier(SourceVerifier):
    provider = "rollback"
    source_kind = "plan"
    supported_claim_types = {"rollback_plan", "backup_snapshot"}

    def verify(self, claim: Claim, sources: SourceBundle, *, action_scope: dict) -> VerifiedEvidence:
        plan = find_by_id(sources.rollback.get("plans", []), "id", claim.ref)
        if plan is None:
            return self.result(claim, status=MISSING, reason="Rollback plan was not found in source bundle.")

        if not scope_matches(claim=claim, item=plan, action_scope=action_scope):
            return self.result(claim, status=FAILED, reason="Rollback plan scope does not match requested action.", details={"plan": plan})

        if plan.get("available") is not True:
            return self.result(claim, status=FAILED, reason="Rollback plan is not marked available.", details={"plan": plan})

        if not is_fresh(plan.get("updated_at_epoch") or plan.get("created_at_epoch"), claim.max_age_hours):
            return self.result(claim, status=EXPIRED, reason="Rollback evidence is older than the allowed freshness window.", details={"plan": plan})

        return self.result(claim, status=PASSED, reason="Rollback plan exists, is available, fresh, and matches action scope.", details={"plan": plan})
