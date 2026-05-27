from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from .demo_domains import DEMO_DOMAIN_SCENARIOS, get_domain_context, list_domain_scenarios
from .models import AxiomRuntimeResult, RawEnterpriseContext, VerificationDetail
from .runtime import AxiomRuntime


router = APIRouter()
runtime = AxiomRuntime()


def _humanize(value: str | None) -> str:
    if not value:
        return "Unknown"
    return value.replace("_", " ").replace("-", " ").strip().title()


def _factor_type(status: str) -> str:
    if status == "PASSED":
        return "verified"
    if status == "WARNING":
        return "warning"
    if status == "MISSING":
        return "missing"
    return "conflict"


def _risk_level(result: AxiomRuntimeResult) -> str:
    action_type = result.envelope.action_request.get("action_type")

    if result.decision in {"DENY", "ESCALATE"}:
        return "high"

    if action_type in {"execute_wire_transfer", "isolate_endpoint"}:
        return "high" if result.decision != "ALLOW" else "controlled"

    if result.decision == "SUSPEND":
        return "elevated"

    return "controlled"


def _summary(result: AxiomRuntimeResult) -> dict[str, Any]:
    action = result.envelope.action_request

    return {
        "action": action.get("action_type") or "unknown_action",
        "action_label": _humanize(action.get("action_type")),
        "target": action.get("target") or "unknown_target",
        "domain": action.get("domain") or result.envelope.domain or "custom",
        "domain_label": _humanize(action.get("domain") or result.envelope.domain),
        "actor": action.get("actor") or "unknown_actor",
        "environment": action.get("environment"),
        "risk_level": _risk_level(result),
        "claims_extracted": len(result.envelope.claims),
        "sources_checked": len(result.verified_sources),
        "missing_proofs": len(result.warrant.missing_evidence),
    }


def _trust_matrix(result: AxiomRuntimeResult) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    for row in result.declared_vs_verified:
        rows.append(
            {
                "claim": _humanize(row.label),
                "declared": row.declared.replace("Agent claims: ", ""),
                "source": row.verified,
                "status": row.status,
                "source_hint": row.source_hint,
            }
        )

    return rows


def _reason_factors(result: AxiomRuntimeResult) -> list[dict[str, Any]]:
    factors: list[dict[str, Any]] = []

    for item in result.verified_sources:
        label = _humanize(item.claim_type or item.source_name)
        factors.append(
            {
                "type": _factor_type(item.status),
                "label": label,
                "source": item.source_name,
                "detail": item.message,
            }
        )

    if not factors and result.reason:
        factors.append(
            {
                "type": "warning",
                "label": "Insufficient context",
                "source": "AXIOM Runtime",
                "detail": result.reason,
            }
        )

    return factors


def _proof_label(missing: str) -> str:
    mapping = {
        "human_approval_present": "Verified human approval",
        "rollback_plan_available": "Verified fallback or rollback plan",
        "fraud_score_clean": "Clean fraud-risk verification",
        "amount_requested": "Additional approval for high-value action",
        "asset_criticality": "Security lead approval for critical asset",
        "target": "Explicit target system or business object",
        "action_type": "Explicit intended action",
        "actor_id": "Identified requesting agent",
    }
    return mapping.get(missing, _humanize(missing))


def _next_required_proofs(result: AxiomRuntimeResult) -> list[str]:
    if result.decision == "ALLOW":
        return ["All required proof satisfied. Action is warrant-ready."]

    if result.warrant.missing_evidence:
        return [_proof_label(item) for item in result.warrant.missing_evidence]

    if result.decision == "ESCALATE":
        return ["Human approval from the responsible owner"]

    if result.decision == "DENY":
        return ["Correct the conflicting or policy-violating evidence"]

    return ["Provide additional source-verified evidence"]


def _decision_room_payload(result: AxiomRuntimeResult, scenario: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = result.model_dump(mode="json")
    payload["scenario"] = scenario
    payload["summary"] = _summary(result)
    payload["trust_matrix"] = _trust_matrix(result)
    payload["reason_factors"] = _reason_factors(result)
    payload["next_required_proofs"] = _next_required_proofs(result)
    payload["doctrine"] = "AXIOM separates what the agent says from what your systems can prove."
    return payload


@router.get("/v1/runtime/scenarios")
def runtime_scenarios() -> list[dict]:
    return list_domain_scenarios()


@router.post("/v1/runtime/evaluate/{scenario_id}")
def runtime_evaluate_scenario(scenario_id: str) -> dict:
    if scenario_id not in DEMO_DOMAIN_SCENARIOS:
        raise HTTPException(status_code=404, detail=f"Unknown scenario_id: {scenario_id}")

    context = get_domain_context(scenario_id)
    result = runtime.evaluate_context(context)
    scenario = DEMO_DOMAIN_SCENARIOS[scenario_id].model_dump(mode="json")

    return _decision_room_payload(result, scenario=scenario)


@router.post("/v1/intake/normalize")
def intake_normalize(context: RawEnterpriseContext) -> dict:
    normalized, sanitized, envelope = runtime.normalize_context(context)
    return {
        "normalized_draft": normalized.model_dump(mode="json"),
        "sanitized_draft": sanitized.model_dump(mode="json"),
        "canonical_action_envelope": envelope.model_dump(mode="json") if envelope else None,
        "next_step": "source_verification_required" if envelope else "insufficient_context",
        "doctrine": "AXIOM separates what the agent says from what your systems can prove.",
    }


@router.post("/v1/intake/evaluate")
def intake_evaluate(context: RawEnterpriseContext) -> dict:
    result = runtime.evaluate_context(context)
    scenario = {
        "id": "custom_context",
        "domain": result.envelope.domain or "Custom",
        "title": "Custom agent action request",
        "severity": "warning",
        "expected_decision": result.decision,
        "description": "User-provided raw enterprise context evaluated through AXIOM runtime.",
        "raw_text": context.raw_text or "",
    }
    return _decision_room_payload(result, scenario=scenario)
