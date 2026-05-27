from __future__ import annotations

from pathlib import Path

from axiom.source_verification import evaluate_action_request, load_json, load_yaml

ROOT = Path(__file__).resolve().parents[2]
ACTION = ROOT / "examples/devops/deploy_to_production.action_request.json"
POLICY = ROOT / "examples/devops/devops_prod_policy.yml"
ALLOW = ROOT / "examples/devops/sources_allow.json"
MISSING_ROLLBACK = ROOT / "examples/devops/sources_missing_rollback.json"
FAILED_SECURITY = ROOT / "examples/devops/sources_failed_security.json"
UNAPPROVED_TICKET = ROOT / "examples/devops/sources_unapproved_ticket.json"


def evaluate_with(sources_path: Path):
    return evaluate_action_request(
        action_request=load_json(ACTION),
        sources=load_json(sources_path),
        policy=load_yaml(POLICY),
    )


def test_source_verified_devops_flow_allows_when_all_proofs_are_verified():
    result = evaluate_with(ALLOW)

    assert result["warrant"]["decision"] == "ALLOW"
    assert result["proof_vector"]["source_verification"]["passed"] == 6
    assert result["warrant"]["missing_evidence"] == []


def test_source_verified_devops_flow_suspends_when_rollback_is_missing():
    result = evaluate_with(MISSING_ROLLBACK)

    assert result["warrant"]["decision"] == "SUSPEND"
    assert "rollback_available" in result["warrant"]["missing_evidence"]


def test_source_verified_devops_flow_blocks_when_security_scan_fails():
    result = evaluate_with(FAILED_SECURITY)

    assert result["warrant"]["decision"] == "BLOCK"
    assert "contradiction:security_scan_failure" in result["warrant"]["missing_evidence"]


def test_source_verified_devops_flow_suspends_when_ticket_claim_is_not_approved_at_source():
    result = evaluate_with(UNAPPROVED_TICKET)

    assert result["warrant"]["decision"] == "SUSPEND"
    assert "change_ticket_approved:failed" in result["warrant"]["missing_evidence"]
