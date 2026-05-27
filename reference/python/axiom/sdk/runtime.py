from __future__ import annotations

import re
import uuid

from .models import (
    AxiomRuntimeResult,
    CanonicalActionEnvelope,
    DeclaredVsVerifiedRow,
    Decision,
    ExtractedAction,
    ExtractedClaim,
    LedgerPreview,
    NormalizedDraft,
    RawEnterpriseContext,
    SanitizedDraft,
    VerificationDetail,
    issue_warrant,
    sha256_hex,
)
from .verifiers import VerifierRegistry


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


class DeterministicIntakeNormalizer:
    """Demo-safe deterministic normalizer.

    Extracts unverified claims. Never verifies, never approves, never invents IDs.
    """

    def normalize(self, context: RawEnterpriseContext) -> NormalizedDraft:
        raw_text = context.raw_text or ""
        lowered = raw_text.lower()

        action = ExtractedAction(raw_text=raw_text)
        claims: list[ExtractedClaim] = []
        ambiguities: list[str] = []

        actor = re.search(r"\b(agent[_\-a-zA-Z0-9]+|sec_agent_bot|support_agent_ai)\b", raw_text)
        if actor:
            action.actor_id = actor.group(1)
            action.actor_type = "ai_agent"

        if "wire transfer" in lowered or "transfer" in lowered:
            action.domain = "finance"
            action.action_type = "execute_wire_transfer"
        elif "isolate" in lowered or "quarantine" in lowered:
            action.domain = "cyber"
            action.action_type = "isolate_endpoint"
        elif "refund" in lowered:
            action.domain = "support"
            action.action_type = "approve_refund"
        elif "deploy" in lowered:
            action.domain = "devops"
            action.action_type = "deploy_to_production" if ("prod" in lowered or "production" in lowered) else "deploy"

        if "production" in lowered or "prod" in lowered:
            action.environment = "production"
        elif "staging" in lowered:
            action.environment = "staging"

        for pattern in [
            r"\b(payment-api)\b",
            r"\b(prod-db)\b",
            r"\b(FIN-\d+)\b",
            r"\b(ACME)\b",
            r"\b(customer\s+[A-Z0-9_-]+)\b",
        ]:
            match = re.search(pattern, raw_text, re.IGNORECASE)
            if match:
                action.target = match.group(1)
                break

        if action.action_type == "approve_refund" and action.target is None and "customer" in lowered:
            action.target = "customer_refund_case"

        ticket = re.search(r"\b(CHG-\d+)\b", raw_text, re.IGNORECASE)
        if ticket:
            ticket_id = ticket.group(1).upper()
            claims.append(
                ExtractedClaim(
                    claim_id=_id("claim"),
                    claim_type="change_ticket_approved",
                    source_hint="change_management",
                    identifiers={"ticket_id": ticket_id},
                    claimed_value="approved" if "approved" in lowered else "unknown",
                    raw_text=self._slice(raw_text, ticket_id),
                )
            )

        pr = re.search(r"\bPR\s*#?\s*(\d+)\b", raw_text, re.IGNORECASE)
        if pr:
            pr_id = int(pr.group(1))
            claims.append(
                ExtractedClaim(
                    claim_id=_id("claim"),
                    claim_type="pull_request_reviewed",
                    source_hint="source_control",
                    identifiers={"pull_request": pr_id},
                    claimed_value="reviewed" if ("approved" in lowered or "review" in lowered) else "unknown",
                    raw_text=self._slice(raw_text, pr.group(0)),
                )
            )

        if re.search(r"\b(ci|ci/cd|cicd|pipeline|pipelines)\b", lowered):
            claims.append(
                ExtractedClaim(
                    claim_id=_id("claim"),
                    claim_type="ci_checks_passed",
                    source_hint="ci_system",
                    claimed_value="passed" if re.search(r"\b(passed|green|success|successful)\b", lowered) else "unknown",
                    raw_text=self._slice(raw_text, "CI"),
                )
            )

        if "security scan" in lowered or "semgrep" in lowered or "snyk" in lowered:
            claims.append(
                ExtractedClaim(
                    claim_id=_id("claim"),
                    claim_type="security_scan_clean",
                    source_hint="security_scanner",
                    claimed_value="clean" if "clean" in lowered else "unknown",
                    raw_text=self._slice(raw_text, "security"),
                )
            )

        if "rollback" in lowered:
            claims.append(
                ExtractedClaim(
                    claim_id=_id("claim"),
                    claim_type="rollback_plan_available",
                    source_hint="runbook_registry",
                    claimed_value="available" if ("available" in lowered or "verified" in lowered or "exists" in lowered) else "unknown",
                    raw_text=self._slice(raw_text, "rollback"),
                )
            )

        invoice = re.search(r"\b(INV-\d+)\b", raw_text, re.IGNORECASE)
        if invoice:
            invoice_id = invoice.group(1).upper()
            claims.append(
                ExtractedClaim(
                    claim_id=_id("claim"),
                    claim_type="invoice_approved",
                    source_hint="erp_system",
                    identifiers={"invoice_id": invoice_id},
                    claimed_value="approved" if "approved" in lowered else "unknown",
                    raw_text=self._slice(raw_text, invoice_id),
                )
            )

        if "beneficiary" in lowered or "iban" in lowered:
            claims.append(
                ExtractedClaim(
                    claim_id=_id("claim"),
                    claim_type="beneficiary_verified",
                    source_hint="beneficiary_registry",
                    identifiers={"beneficiary": "ACME"} if "acme" in lowered else {},
                    claimed_value="verified" if "verified" in lowered else "unknown",
                    raw_text=self._slice(raw_text, "beneficiary"),
                )
            )

        amount = re.search(r"(€|EUR\s*)\s?([0-9][0-9\s,.]*)", raw_text, re.IGNORECASE)
        if amount:
            digits = re.sub(r"[^\d]", "", amount.group(2))
            amount_value = float(digits) if digits else None
            claims.append(
                ExtractedClaim(
                    claim_id=_id("claim"),
                    claim_type="amount_requested",
                    source_hint="payment_policy",
                    claimed_value=amount_value,
                    raw_text=self._slice(raw_text, amount.group(0)),
                )
            )

        if "fraud" in lowered:
            claims.append(
                ExtractedClaim(
                    claim_id=_id("claim"),
                    claim_type="fraud_score_clean",
                    source_hint="anti_fraud_engine",
                    claimed_value="clean" if "clean" in lowered else "unknown",
                    raw_text=self._slice(raw_text, "fraud"),
                )
            )

        if "edr" in lowered or "ransomware" in lowered or "critical alert" in lowered:
            claims.append(
                ExtractedClaim(
                    claim_id=_id("claim"),
                    claim_type="edr_alert_confirmed",
                    source_hint="edr",
                    claimed_value="critical" if ("critical" in lowered or "ransomware" in lowered) else "unknown",
                    raw_text=self._slice(raw_text, "EDR"),
                )
            )

        if "vip" in lowered or "cfo" in lowered or "chief financial officer" in lowered:
            claims.append(
                ExtractedClaim(
                    claim_id=_id("claim"),
                    claim_type="asset_criticality",
                    source_hint="cmdb",
                    claimed_value="tier-1-executive",
                    raw_text=self._slice(raw_text, "CFO" if "cfo" in lowered else "asset"),
                )
            )

        if "customer" in lowered and "refund" in lowered:
            claims.append(
                ExtractedClaim(
                    claim_id=_id("claim"),
                    claim_type="customer_refund_requested",
                    source_hint="crm",
                    claimed_value="requested",
                    raw_text=self._slice(raw_text, "refund"),
                )
            )

        if "manager approval" in lowered or "human approval" in lowered:
            claims.append(
                ExtractedClaim(
                    claim_id=_id("claim"),
                    claim_type="human_approval_present",
                    source_hint="approval_system",
                    claimed_value="present" if ("present" in lowered or "approved" in lowered) else "unknown",
                    raw_text=self._slice(raw_text, "approval"),
                )
            )

        missing = []
        for field in ["actor_id", "action_type", "target"]:
            if getattr(action, field) in (None, ""):
                missing.append(field)

        if not raw_text.strip():
            ambiguities.append("empty_raw_context")

        return NormalizedDraft(
            extracted_action=action,
            extracted_claims=claims,
            missing_structural_fields=missing,
            ambiguities=ambiguities,
            assumptions=[],
            raw_references=[{"raw_text": raw_text[:500]}] if raw_text else [],
            confidence="medium" if claims else "low",
        )

    def _slice(self, raw_text: str, token: str) -> str:
        lowered = raw_text.lower()
        idx = lowered.find(token.lower())
        if idx < 0:
            return token
        start = max(0, idx - 60)
        end = min(len(raw_text), idx + len(token) + 100)
        return raw_text[start:end].strip()


class SafetySanitizer:
    def sanitize(self, draft: NormalizedDraft) -> SanitizedDraft:
        rejected: list[dict] = []
        warnings: list[str] = []
        safe_claims: list[ExtractedClaim] = []

        for claim in draft.extracted_claims:
            if claim.verification_status != "unverified":
                rejected.append({"claim_id": claim.claim_id, "reason": "Normalizer cannot mark evidence as verified."})
                continue

            if not claim.raw_text:
                rejected.append({"claim_id": claim.claim_id, "reason": "Claim without raw_text provenance is rejected."})
                continue

            safe_claims.append(claim)

        safe_to_build = draft.extracted_action is not None and "action_type" not in draft.missing_structural_fields

        if draft.assumptions:
            warnings.append("Normalizer assumptions are preserved but never used as proof.")

        if draft.missing_structural_fields:
            warnings.append("Missing structural fields may force SUSPEND or ESCALATE.")

        return SanitizedDraft(
            extracted_action=draft.extracted_action,
            extracted_claims=safe_claims,
            rejected_items=rejected,
            missing_structural_fields=draft.missing_structural_fields,
            ambiguities=draft.ambiguities,
            sanitizer_warnings=warnings,
            safe_to_build_envelope=safe_to_build,
        )


class CanonicalEnvelopeBuilder:
    def build(self, sanitized: SanitizedDraft) -> CanonicalActionEnvelope:
        action = sanitized.extracted_action or ExtractedAction()

        action_request = {
            "domain": action.domain,
            "actor": action.actor_id,
            "actor_type": action.actor_type,
            "action_type": action.action_type,
            "target": action.target,
            "environment": action.environment,
        }

        source_hints = sorted({claim.source_hint for claim in sanitized.extracted_claims if claim.source_hint})

        return CanonicalActionEnvelope(
            domain=action.domain,
            action_request=action_request,
            claims=sanitized.extracted_claims,
            missing_structural_fields=sanitized.missing_structural_fields,
            ambiguities=sanitized.ambiguities,
            source_hints=source_hints,
        )


class PolicyKernel:
    def decide(
        self,
        envelope: CanonicalActionEnvelope,
        verified_sources: list[VerificationDetail],
    ) -> tuple[Decision, str, list[str]]:
        action_type = envelope.action_request.get("action_type")

        if not action_type:
            return "SUSPEND", "Cannot evaluate action: action_type is missing.", ["action_type"]

        if not envelope.action_request.get("target"):
            return "SUSPEND", "Cannot issue warrant: target is missing from the action request.", ["target"]

        failed = [v for v in verified_sources if v.status == "FAILED"]
        missing = [v for v in verified_sources if v.status == "MISSING"]
        warnings = [v for v in verified_sources if v.status == "WARNING"]

        if action_type == "isolate_endpoint" and (failed or missing):
            return (
                "ESCALATE",
                "Cyber action touches a critical asset or lacks fallback proof. Escalation required.",
                [v.claim_type or v.source_name for v in failed + missing],
            )

        if action_type == "approve_refund" and (failed or missing or warnings):
            return (
                "DENY",
                "Refund action violates autonomous threshold or lacks required approval.",
                [v.claim_type or v.source_name for v in failed + missing + warnings],
            )

        if action_type == "execute_wire_transfer" and (warnings or missing or failed):
            return (
                "SUSPEND",
                "High-risk financial action requires verified fraud score and approval.",
                [v.claim_type or v.source_name for v in warnings + missing + failed],
            )

        if failed:
            return (
                "DENY",
                "At least one source-verified evidence item contradicts the agent-declared claim.",
                [v.claim_type or v.source_name for v in failed],
            )

        if missing:
            return (
                "SUSPEND",
                "Required evidence is missing. Declared proof is not verified proof.",
                [v.claim_type or v.source_name for v in missing],
            )

        if warnings:
            return (
                "SUSPEND",
                "Source verification returned warnings. Proportional proof is not satisfied.",
                [v.claim_type or v.source_name for v in warnings],
            )

        return "ALLOW", "All agent-declared claims match source-verified evidence. Policy satisfied.", []


class AxiomRuntime:
    """Stable SDK façade.

    Product code should depend on:
    - normalize_context()
    - evaluate_context()
    - evaluate_envelope()
    """

    def __init__(self) -> None:
        self.normalizer = DeterministicIntakeNormalizer()
        self.sanitizer = SafetySanitizer()
        self.builder = CanonicalEnvelopeBuilder()
        self.verifiers = VerifierRegistry()
        self.policy = PolicyKernel()

    def normalize_context(self, context: RawEnterpriseContext) -> tuple[NormalizedDraft, SanitizedDraft, CanonicalActionEnvelope | None]:
        draft = self.normalizer.normalize(context)
        sanitized = self.sanitizer.sanitize(draft)
        envelope = self.builder.build(sanitized) if sanitized.safe_to_build_envelope else None
        return draft, sanitized, envelope

    def evaluate_context(self, context: RawEnterpriseContext) -> AxiomRuntimeResult:
        draft, sanitized, envelope = self.normalize_context(context)

        if envelope is None:
            action_request = {
                "domain": None,
                "actor": None,
                "actor_type": None,
                "action_type": None,
                "target": None,
                "environment": None,
            }
            decision: Decision = "SUSPEND"
            reason = "Cannot build canonical action envelope from intake context."
            missing = sanitized.missing_structural_fields
            verified: list[VerificationDetail] = []
            declared_vs_verified: list[DeclaredVsVerifiedRow] = []
            envelope = CanonicalActionEnvelope(domain=None, action_request=action_request)
        else:
            verified = self.verifiers.verify(envelope)
            decision, reason, missing = self.policy.decide(envelope, verified)
            action_request = envelope.action_request
            declared_vs_verified = self._declared_vs_verified(envelope, verified)

        warrant = issue_warrant(
            decision=decision,
            reason=reason,
            action_request=action_request,
            missing_evidence=missing,
            verified_sources=verified,
        )

        ledger = LedgerPreview(
            warrant_id=warrant.warrant_id,
            decision=decision,
            warrant_hash=sha256_hex(warrant.model_dump(mode="json")),
            audit_note="Demo ledger preview. Production deployments append this entry to the Proof Ledger.",
        )

        return AxiomRuntimeResult(
            raw_context=context,
            normalized_draft=draft,
            sanitized_draft=sanitized,
            envelope=envelope,
            declared_vs_verified=declared_vs_verified,
            verified_sources=verified,
            decision=decision,
            reason=reason,
            warrant=warrant,
            ledger_preview=ledger,
        )

    def evaluate_envelope(self, envelope: CanonicalActionEnvelope, context: RawEnterpriseContext | None = None) -> AxiomRuntimeResult:
        context = context or RawEnterpriseContext(raw_text="")
        verified = self.verifiers.verify(envelope)
        decision, reason, missing = self.policy.decide(envelope, verified)

        warrant = issue_warrant(
            decision=decision,
            reason=reason,
            action_request=envelope.action_request,
            missing_evidence=missing,
            verified_sources=verified,
        )

        ledger = LedgerPreview(
            warrant_id=warrant.warrant_id,
            decision=decision,
            warrant_hash=sha256_hex(warrant.model_dump(mode="json")),
            audit_note="Demo ledger preview. Production deployments append this entry to the Proof Ledger.",
        )

        draft = NormalizedDraft(extracted_action=None)
        sanitized = SanitizedDraft(safe_to_build_envelope=True)

        return AxiomRuntimeResult(
            raw_context=context,
            normalized_draft=draft,
            sanitized_draft=sanitized,
            envelope=envelope,
            declared_vs_verified=self._declared_vs_verified(envelope, verified),
            verified_sources=verified,
            decision=decision,
            reason=reason,
            warrant=warrant,
            ledger_preview=ledger,
        )

    def _declared_vs_verified(
        self,
        envelope: CanonicalActionEnvelope,
        verified_sources: list[VerificationDetail],
    ) -> list[DeclaredVsVerifiedRow]:
        by_claim_id = {v.claim_id: v for v in verified_sources if v.claim_id}
        rows: list[DeclaredVsVerifiedRow] = []

        for claim in envelope.claims:
            detail = by_claim_id.get(claim.claim_id)

            if detail is None:
                rows.append(
                    DeclaredVsVerifiedRow(
                        label=claim.claim_type,
                        declared=str(claim.claimed_value),
                        source_hint=claim.source_hint,
                        verified="No verifier response.",
                        status="missing",
                    )
                )
                continue

            if detail.status == "PASSED":
                status = "verified"
            elif detail.status == "WARNING":
                status = "warning"
            elif detail.status == "MISSING":
                status = "missing"
            else:
                status = "conflict"

            rows.append(
                DeclaredVsVerifiedRow(
                    label=claim.claim_type,
                    declared=f"Agent claims: {claim.claimed_value}",
                    source_hint=claim.source_hint,
                    verified=f"{detail.source_name}: {detail.message}",
                    status=status,
                )
            )

        for detail in verified_sources:
            if detail.claim_id:
                continue

            rows.append(
                DeclaredVsVerifiedRow(
                    label=detail.claim_type or detail.source_name,
                    declared="No explicit agent claim.",
                    source_hint=None,
                    verified=f"{detail.source_name}: {detail.message}",
                    status="missing" if detail.status == "MISSING" else "warning",
                )
            )

        return rows
