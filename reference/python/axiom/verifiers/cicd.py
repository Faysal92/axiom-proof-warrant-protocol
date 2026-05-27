from __future__ import annotations

from axiom.schemas import Claim, SourceBundle, VerifiedEvidence
from .base import FAILED, MISSING, PASSED, SourceVerifier, find_by_id, scope_matches


class CIRunVerifier(SourceVerifier):
    provider = "ci"
    source_kind = "run"
    supported_claim_types = {"ci_run", "ci_checks"}

    def verify(self, claim: Claim, sources: SourceBundle, *, action_scope: dict) -> VerifiedEvidence:
        run = find_by_id(sources.ci.get("runs", []), "id", claim.ref)
        if run is None:
            return self.result(claim, status=MISSING, reason="CI run was not found in source bundle.")

        if not scope_matches(claim=claim, item=run, action_scope=action_scope):
            return self.result(claim, status=FAILED, reason="CI run scope does not match requested action.", details={"run": run})

        if str(run.get("status", "unknown")).lower() not in {"passed", "success", "ok"}:
            return self.result(claim, status=FAILED, reason="CI run did not pass.", details={"run": run})

        checks = {str(c.get("name")): str(c.get("status", "unknown")).lower() for c in run.get("checks", [])}
        missing_or_failed = [name for name in claim.required_checks if checks.get(name) not in {"passed", "success", "ok"}]
        if missing_or_failed:
            return self.result(
                claim,
                status=FAILED,
                reason="Required CI checks are missing or failed.",
                details={"missing_or_failed_checks": missing_or_failed, "checks": checks},
            )

        return self.result(claim, status=PASSED, reason="CI run and required checks passed.", details={"run": run})


class SecurityScanVerifier(SourceVerifier):
    provider = "ci"
    source_kind = "security_scan"
    supported_claim_types = {"security_scan", "sast_scan"}

    def verify(self, claim: Claim, sources: SourceBundle, *, action_scope: dict) -> VerifiedEvidence:
        scan = find_by_id(sources.ci.get("security_scans", []), "id", claim.ref)
        if scan is None:
            return self.result(claim, status=MISSING, reason="Security scan was not found in source bundle.")

        if not scope_matches(claim=claim, item=scan, action_scope=action_scope):
            return self.result(claim, status=FAILED, reason="Security scan scope does not match requested action.", details={"scan": scan})

        if scan.get("clean") is not True:
            return self.result(claim, status=FAILED, reason="Security scan is not clean.", details={"scan": scan})

        return self.result(claim, status=PASSED, reason="Security scan is clean and matches action scope.", details={"scan": scan})
