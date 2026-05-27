from __future__ import annotations

from pathlib import Path

from axiom.source_verification import load_json, verify_action_claims, verified_evidence_to_proof_vector

ROOT = Path(__file__).resolve().parents[2]
ACTION = ROOT / "examples/devops/deploy_to_production.action_request.json"
ALLOW = ROOT / "examples/devops/sources_allow.json"
MISSING_ROLLBACK = ROOT / "examples/devops/sources_missing_rollback.json"
FAILED_SECURITY = ROOT / "examples/devops/sources_failed_security.json"


def test_source_verifiers_turn_agent_claims_into_verified_evidence():
    verified = verify_action_claims(action_request=load_json(ACTION), sources=load_json(ALLOW))

    assert len(verified) == 6
    assert all(item.status == "passed" for item in verified)
    assert {item.dimension for item in verified} >= {
        "change_ticket_approved",
        "github_pr_approved",
        "ci_checks_passed",
        "security_scan_clean",
        "rollback_available",
        "deployment_window_allowed",
    }


def test_pydantic_claim_is_not_enough_missing_source_stays_missing():
    verified = verify_action_claims(action_request=load_json(ACTION), sources=load_json(MISSING_ROLLBACK))
    rollback = next(item for item in verified if item.dimension == "rollback_available")

    assert rollback.status == "missing"
    assert "not found" in rollback.reason.lower()


def test_failed_security_scan_becomes_contradiction_in_proof_vector():
    action_request = load_json(ACTION)
    verified = verify_action_claims(action_request=action_request, sources=load_json(FAILED_SECURITY))
    proof = verified_evidence_to_proof_vector(verified, action_request=action_request)

    assert proof["dimensions"]["security_scan_clean"]["status"] == "failed"
    assert proof["contradictions"][0]["type"] == "security_scan_failure"
