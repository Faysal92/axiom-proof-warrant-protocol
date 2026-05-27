from __future__ import annotations

from abc import ABC, abstractmethod

from .models import CanonicalActionEnvelope, ExtractedClaim, VerificationDetail


class BaseSourceVerifier(ABC):
    claim_types: set[str] = set()

    @abstractmethod
    def verify(self, claim: ExtractedClaim, envelope: CanonicalActionEnvelope) -> VerificationDetail:
        raise NotImplementedError


class ChangeManagementVerifier(BaseSourceVerifier):
    claim_types = {"change_ticket_approved"}

    def verify(self, claim: ExtractedClaim, envelope: CanonicalActionEnvelope) -> VerificationDetail:
        ticket_id = str(claim.identifiers.get("ticket_id", "UNKNOWN"))
        passed = ticket_id == "CHG-1001"
        return VerificationDetail(
            claim_id=claim.claim_id,
            claim_type=claim.claim_type,
            source_name="Change Management",
            status="PASSED" if passed else "WARNING",
            message=f"Ticket {ticket_id} is approved." if passed else f"Ticket {ticket_id} is pending or not fully approved.",
            payload_snapshot={"ticket_id": ticket_id, "status": "approved" if passed else "pending"},
        )


class SourceControlVerifier(BaseSourceVerifier):
    claim_types = {"pull_request_reviewed"}

    def verify(self, claim: ExtractedClaim, envelope: CanonicalActionEnvelope) -> VerificationDetail:
        pr = claim.identifiers.get("pull_request")
        return VerificationDetail(
            claim_id=claim.claim_id,
            claim_type=claim.claim_type,
            source_name="Source Control",
            status="PASSED",
            message=f"Pull request #{pr} has required review metadata.",
            payload_snapshot={"pull_request": pr, "reviewed": True},
        )


class CISystemVerifier(BaseSourceVerifier):
    claim_types = {"ci_checks_passed"}

    def verify(self, claim: ExtractedClaim, envelope: CanonicalActionEnvelope) -> VerificationDetail:
        return VerificationDetail(
            claim_id=claim.claim_id,
            claim_type=claim.claim_type,
            source_name="CI System",
            status="PASSED",
            message="CI checks are marked as passed in the simulated source.",
            payload_snapshot={"ci_status": "passed"},
        )


class SecurityScannerVerifier(BaseSourceVerifier):
    claim_types = {"security_scan_clean"}

    def verify(self, claim: ExtractedClaim, envelope: CanonicalActionEnvelope) -> VerificationDetail:
        clean = claim.claimed_value == "clean"
        return VerificationDetail(
            claim_id=claim.claim_id,
            claim_type=claim.claim_type,
            source_name="Security Scanner",
            status="PASSED" if clean else "FAILED",
            message="Security scan is clean." if clean else "Security scan is not clean or not proven.",
            payload_snapshot={"scan_status": "clean" if clean else "unknown_or_failed"},
        )


class RollbackVerifier(BaseSourceVerifier):
    claim_types = {"rollback_plan_available"}

    def verify(self, claim: ExtractedClaim, envelope: CanonicalActionEnvelope) -> VerificationDetail:
        ok = claim.claimed_value in {"available", "verified", "exists"}
        return VerificationDetail(
            claim_id=claim.claim_id,
            claim_type=claim.claim_type,
            source_name="Rollback Registry",
            status="PASSED" if ok else "MISSING",
            message="Rollback plan is available." if ok else "Rollback plan is missing or unverified.",
            payload_snapshot={"rollback_available": ok},
        )


class ERPVerifier(BaseSourceVerifier):
    claim_types = {"invoice_approved"}

    def verify(self, claim: ExtractedClaim, envelope: CanonicalActionEnvelope) -> VerificationDetail:
        invoice_id = claim.identifiers.get("invoice_id", "UNKNOWN")
        return VerificationDetail(
            claim_id=claim.claim_id,
            claim_type=claim.claim_type,
            source_name="ERP System",
            status="PASSED",
            message=f"Invoice {invoice_id} is approved for payment.",
            payload_snapshot={"invoice_id": invoice_id, "status": "approved"},
        )


class BeneficiaryRegistryVerifier(BaseSourceVerifier):
    claim_types = {"beneficiary_verified"}

    def verify(self, claim: ExtractedClaim, envelope: CanonicalActionEnvelope) -> VerificationDetail:
        return VerificationDetail(
            claim_id=claim.claim_id,
            claim_type=claim.claim_type,
            source_name="Beneficiary Registry",
            status="PASSED",
            message="Beneficiary record matches simulated compliance registry.",
            payload_snapshot={"beneficiary_verified": True},
        )


class PaymentPolicyVerifier(BaseSourceVerifier):
    claim_types = {"amount_requested"}

    def verify(self, claim: ExtractedClaim, envelope: CanonicalActionEnvelope) -> VerificationDetail:
        amount = claim.claimed_value or 0
        action_type = envelope.action_request.get("action_type")

        threshold = 300 if action_type == "approve_refund" else 10000
        high_value = bool(amount and amount > threshold)

        return VerificationDetail(
            claim_id=claim.claim_id,
            claim_type=claim.claim_type,
            source_name="Payment Policy",
            status="WARNING" if high_value else "PASSED",
            message=(
                f"Requested amount is {amount}. Threshold is {threshold}. Proportional proof is required."
                if high_value
                else f"Requested amount {amount} is within autonomous threshold {threshold}."
            ),
            payload_snapshot={"amount": amount, "threshold": threshold},
        )


class AntiFraudVerifier(BaseSourceVerifier):
    claim_types = {"fraud_score_clean"}

    def verify(self, claim: ExtractedClaim, envelope: CanonicalActionEnvelope) -> VerificationDetail:
        return VerificationDetail(
            claim_id=claim.claim_id,
            claim_type=claim.claim_type,
            source_name="Anti-Fraud Engine",
            status="WARNING",
            message="Fraud engine detected operational anomaly: out-of-hours/high-velocity transfer.",
            payload_snapshot={"risk_score": 72, "flags": ["out_of_hours_activity"]},
        )


class EDRVerifier(BaseSourceVerifier):
    claim_types = {"edr_alert_confirmed"}

    def verify(self, claim: ExtractedClaim, envelope: CanonicalActionEnvelope) -> VerificationDetail:
        return VerificationDetail(
            claim_id=claim.claim_id,
            claim_type=claim.claim_type,
            source_name="EDR Core API",
            status="PASSED",
            message="Critical endpoint alert confirmed by EDR source.",
            payload_snapshot={"severity": "critical"},
        )


class CMDBVerifier(BaseSourceVerifier):
    claim_types = {"asset_criticality"}

    def verify(self, claim: ExtractedClaim, envelope: CanonicalActionEnvelope) -> VerificationDetail:
        critical = claim.claimed_value == "tier-1-executive"
        return VerificationDetail(
            claim_id=claim.claim_id,
            claim_type=claim.claim_type,
            source_name="CMDB Inventory",
            status="FAILED" if critical else "PASSED",
            message="Asset is a Tier-1 Executive asset; blast radius is high." if critical else "Asset criticality is acceptable.",
            payload_snapshot={"criticality": claim.claimed_value},
        )


class CRMVerifier(BaseSourceVerifier):
    claim_types = {"customer_refund_requested"}

    def verify(self, claim: ExtractedClaim, envelope: CanonicalActionEnvelope) -> VerificationDetail:
        return VerificationDetail(
            claim_id=claim.claim_id,
            claim_type=claim.claim_type,
            source_name="CRM",
            status="PASSED",
            message="Customer exists and refund request is recorded.",
            payload_snapshot={"customer_exists": True},
        )


class ApprovalSystemVerifier(BaseSourceVerifier):
    claim_types = {"human_approval_present"}

    def verify(self, claim: ExtractedClaim, envelope: CanonicalActionEnvelope) -> VerificationDetail:
        present = claim.claimed_value == "present"
        return VerificationDetail(
            claim_id=claim.claim_id,
            claim_type=claim.claim_type,
            source_name="Approval System",
            status="PASSED" if present else "MISSING",
            message="Human approval is present." if present else "Human approval is not verified.",
            payload_snapshot={"approval_present": present},
        )


class VerifierRegistry:
    """Router between claims and source verifiers.

    In production, these verifiers become real connectors.
    The registry contract remains the same.
    """

    def __init__(self, verifiers: list[BaseSourceVerifier] | None = None) -> None:
        self.verifiers = verifiers or [
            ChangeManagementVerifier(),
            SourceControlVerifier(),
            CISystemVerifier(),
            SecurityScannerVerifier(),
            RollbackVerifier(),
            ERPVerifier(),
            BeneficiaryRegistryVerifier(),
            PaymentPolicyVerifier(),
            AntiFraudVerifier(),
            EDRVerifier(),
            CMDBVerifier(),
            CRMVerifier(),
            ApprovalSystemVerifier(),
        ]
        self.by_claim_type: dict[str, BaseSourceVerifier] = {}
        for verifier in self.verifiers:
            for claim_type in verifier.claim_types:
                self.by_claim_type[claim_type] = verifier

    def verify(self, envelope: CanonicalActionEnvelope) -> list[VerificationDetail]:
        details: list[VerificationDetail] = []

        for claim in envelope.claims:
            verifier = self.by_claim_type.get(claim.claim_type)
            if verifier is None:
                details.append(
                    VerificationDetail(
                        claim_id=claim.claim_id,
                        claim_type=claim.claim_type,
                        source_name=claim.source_hint or "Unknown Source",
                        status="WARNING",
                        message="Claim type is not mapped to a dedicated source verifier in this demo.",
                        payload_snapshot={},
                    )
                )
                continue

            details.append(verifier.verify(claim, envelope))

        action_type = envelope.action_request.get("action_type")

        if action_type == "execute_wire_transfer":
            if not any(c.claim_type == "human_approval_present" for c in envelope.claims):
                details.append(
                    VerificationDetail(
                        source_name="Approval System",
                        claim_type="human_approval_present",
                        status="MISSING",
                        message="Human approval is missing for high-risk transfer.",
                        payload_snapshot={},
                    )
                )

        if action_type == "approve_refund":
            if not any(c.claim_type == "human_approval_present" for c in envelope.claims):
                details.append(
                    VerificationDetail(
                        source_name="Approval System",
                        claim_type="human_approval_present",
                        status="MISSING",
                        message="Manager approval is missing for refund above autonomous threshold.",
                        payload_snapshot={},
                    )
                )

        if action_type == "isolate_endpoint":
            if not any(c.claim_type == "rollback_plan_available" for c in envelope.claims):
                details.append(
                    VerificationDetail(
                        source_name="Rollback Registry",
                        claim_type="rollback_plan_available",
                        status="MISSING",
                        message="No automated fallback or reconnection plan was provided.",
                        payload_snapshot={},
                    )
                )

        return details
