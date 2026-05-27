from __future__ import annotations

from axiom.schemas import Claim, SourceBundle, VerifiedEvidence
from .base import FAILED, MISSING, PASSED, SourceVerifier, find_by_id, scope_matches


class GitHubPullRequestVerifier(SourceVerifier):
    provider = "github"
    source_kind = "pull_request"
    supported_claim_types = {"github_pr", "pull_request", "code_review"}

    def verify(self, claim: Claim, sources: SourceBundle, *, action_scope: dict) -> VerifiedEvidence:
        pr = find_by_id(sources.github.get("pull_requests", []), "number", claim.ref)
        if pr is None:
            return self.result(claim, status=MISSING, reason="Pull request was not found in GitHub source bundle.")

        if not scope_matches(claim=claim, item=pr, action_scope=action_scope):
            return self.result(claim, status=FAILED, reason="Pull request scope does not match requested action.", details={"pull_request": pr})

        if claim.commit and pr.get("head_sha") and str(pr.get("head_sha")) != str(claim.commit):
            return self.result(claim, status=FAILED, reason="Pull request head SHA does not match required commit.", details={"pull_request": pr})

        approvals = [r for r in pr.get("reviews", []) if str(r.get("state", "")).upper() == "APPROVED"]
        if len(approvals) < int(claim.min_approvals or 1):
            return self.result(
                claim,
                status=FAILED,
                reason=f"Pull request has {len(approvals)} approval(s), expected {claim.min_approvals or 1}.",
                details={"pull_request": pr, "approvals": approvals},
            )

        checks = {str(c.get("name")): str(c.get("status", c.get("conclusion", "unknown"))).lower() for c in pr.get("checks", [])}
        missing_or_failed = [name for name in claim.required_checks if checks.get(name) not in {"passed", "success", "ok", "completed"}]
        if missing_or_failed:
            return self.result(
                claim,
                status=FAILED,
                reason="Required pull request checks are missing or failed.",
                details={"missing_or_failed_checks": missing_or_failed, "checks": checks},
            )

        return self.result(claim, status=PASSED, reason="Pull request has required approvals and checks.", details={"pull_request": pr})
