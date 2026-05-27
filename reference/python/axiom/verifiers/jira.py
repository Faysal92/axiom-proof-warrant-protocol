from __future__ import annotations

from axiom.schemas import Claim, SourceBundle, VerifiedEvidence
from .base import EXPIRED, FAILED, MISSING, PASSED, SourceVerifier, find_by_id, is_fresh, scope_matches


class JiraTicketVerifier(SourceVerifier):
    provider = "jira"
    source_kind = "ticket"
    supported_claim_types = {"jira_ticket", "change_ticket", "incident_ticket"}

    def verify(self, claim: Claim, sources: SourceBundle, *, action_scope: dict) -> VerifiedEvidence:
        ticket = find_by_id(sources.jira.get("tickets", []), "id", claim.ref)
        if ticket is None:
            return self.result(claim, status=MISSING, reason="Ticket was not found in Jira source bundle.")

        required_status = (claim.required_status or "approved").lower()
        actual_status = str(ticket.get("status", "unknown")).lower()
        if actual_status != required_status:
            return self.result(
                claim,
                status=FAILED,
                reason=f"Ticket status is {actual_status}, expected {required_status}.",
                details={"ticket": ticket},
            )

        if not scope_matches(claim=claim, item=ticket, action_scope=action_scope):
            return self.result(
                claim,
                status=FAILED,
                reason="Ticket scope does not match the requested action target/environment.",
                details={"ticket": ticket, "action_scope": action_scope},
            )

        if not is_fresh(ticket.get("updated_at_epoch") or ticket.get("created_at_epoch"), claim.max_age_hours):
            return self.result(claim, status=EXPIRED, reason="Ticket evidence is older than the allowed freshness window.", details={"ticket": ticket})

        return self.result(claim, status=PASSED, reason="Jira ticket exists, is approved, fresh, and matches action scope.", details={"ticket": ticket})
