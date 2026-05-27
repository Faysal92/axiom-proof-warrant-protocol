from __future__ import annotations

from axiom.schemas import Claim, SourceBundle, VerifiedEvidence
from .base import FAILED, MISSING, PASSED, SourceVerifier, find_by_id, scope_matches


class DeploymentWindowVerifier(SourceVerifier):
    provider = "deployment_windows"
    source_kind = "window"
    supported_claim_types = {"deployment_window", "change_window"}

    def verify(self, claim: Claim, sources: SourceBundle, *, action_scope: dict) -> VerifiedEvidence:
        window = find_by_id(sources.deployment_windows.get("windows", []), "id", claim.ref)
        if window is None:
            return self.result(claim, status=MISSING, reason="Deployment window was not found in source bundle.")

        if not scope_matches(claim=claim, item=window, action_scope=action_scope):
            return self.result(claim, status=FAILED, reason="Deployment window scope does not match requested action.", details={"window": window})

        if window.get("allowed") is not True:
            return self.result(claim, status=FAILED, reason="Deployment window is not currently allowed.", details={"window": window})

        return self.result(claim, status=PASSED, reason="Deployment window allows the requested action.", details={"window": window})
