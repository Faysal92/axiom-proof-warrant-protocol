from datetime import datetime, timedelta, timezone
from uuid import uuid4

from .challenge import build_next_actions
from .crypto import sign_payload
from .models import ExecutionWarrant

def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

def utc_plus_minutes(minutes: int) -> str:
    return (datetime.now(timezone.utc) + timedelta(minutes=minutes)).replace(microsecond=0).isoformat().replace("+00:00", "Z")

def build_warrant(
    *,
    action: dict,
    proof_vector: dict,
    requirement_vector: dict,
    decision: str,
    reason: str,
    missing_evidence: list[str],
    gap_reason: str,
    expires_in_minutes: int = 30,
) -> dict:
    resubmit_allowed = decision in {"SUSPEND", "REQUIRE_HUMAN_REVIEW"}
    warrant = {
        "warrant_id": f"wrn_{uuid4().hex[:12]}",
        "protocol_version": "axiom-proof-warrant-v0.1.1",
        "warrant_type": "EXECUTION_WARRANT",
        "status": "ISSUED" if decision in {"ALLOW", "CONDITIONAL"} else "SUSPENDED" if decision == "SUSPEND" else decision,
        "created_at": utc_now(),
        "expires_at": utc_plus_minutes(expires_in_minutes),
        "actor": action.get("actor", {}),
        "action": action.get("action", {}),
        "claim": action.get("claim", {}),
        "action_weight": action.get("action_weight", {}),
        "required_proof": {
            "min_proof_level": requirement_vector.get("min_meta", {}).get("required_level"),
            "required_evidence": requirement_vector.get("mandatory_dimensions", []),
        },
        "provided_proof": {
            "proof_level": proof_vector.get("meta", {}).get("proof_level"),
            "evidence_refs": proof_vector.get("evidence_refs", []),
            "dimensions": proof_vector.get("dimensions", {}),
            "limitations": proof_vector.get("limitations", []),
            "contradictions": proof_vector.get("contradictions", []),
        },
        "missing_evidence": missing_evidence,
        "proof_gap": {
            "required_level": requirement_vector.get("min_meta", {}).get("required_level"),
            "provided_level": proof_vector.get("meta", {}).get("proof_level"),
            "gap_reason": gap_reason,
        },
        "decision": decision,
        "reason": reason,
        "challenge": {
            "resubmit_allowed": resubmit_allowed,
            "missing_evidence": missing_evidence,
            "next_actions": build_next_actions(missing_evidence),
        },
        "ledger": {
            "ledger_action": "APPEND",
            "append_reason": "Warrant decision recorded for auditability.",
            "evaluator_version": "axiom-reference-python-v0.1.1",
        },
    }
    warrant["signature"] = sign_payload(warrant)

    # Runtime validation: if this fails, the reference implementation must not emit the warrant.
    ExecutionWarrant.model_validate(warrant)
    return warrant
