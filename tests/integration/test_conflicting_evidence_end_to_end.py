from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "reference" / "python"))

from axiom.api import app
from axiom.evaluator import evaluate
from axiom.evidence.adapters.external_api import payload_to_proof_vector
from axiom.ledger import append_ledger_entry, verify_ledger


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def evidence_event(event_id: str, provider: str, status: str) -> dict:
    return {
        "event_id": event_id,
        "source": {
            "provider": provider,
            "kind": "security_scan",
            "name": provider,
            "trust_level": "high",
            "collected_at": 1779100000,
        },
        "subject": {
            "target": "payment-api",
            "environment": "production",
            "commit": "abc123",
            "branch": "main",
            "service": "payments",
        },
        "claims": {
            "security_scan_clean": {"status": status, "scanner": provider},
        },
        "evidence_refs": [f"{provider}:scan:{status}"],
    }


def base_deploy_proofs() -> list[dict]:
    return [
        {
            "event_id": "ev_ci_passed",
            "source": {"provider": "github_actions", "kind": "ci_checks", "trust_level": "high", "collected_at": 1779100000},
            "subject": {"target": "payment-api", "environment": "production", "commit": "abc123", "branch": "main", "service": "payments"},
            "claims": {"unit_tests_passed": True, "integration_tests_passed": True},
            "evidence_refs": ["github_check_run:ci:123"],
        },
        {
            "event_id": "ev_review_approved",
            "source": {"provider": "github", "kind": "pull_request_review", "trust_level": "high", "collected_at": 1779100000},
            "subject": {"target": "payment-api", "environment": "production", "commit": "abc123", "branch": "main", "service": "payments"},
            "claims": {"human_reviewed": True},
            "evidence_refs": ["github_pr_review:42"],
        },
        {
            "event_id": "ev_rollback_available",
            "source": {"provider": "runbook", "kind": "rollback_plan", "trust_level": "high", "collected_at": 1779100000},
            "subject": {"target": "payment-api", "environment": "production", "commit": "abc123", "branch": "main", "service": "payments"},
            "claims": {"rollback_available": True},
            "evidence_refs": ["rollback_plan:45"],
        },
    ]


def test_conflicting_security_sources_block_deployment():
    action = load_json(ROOT / "examples" / "deploy_payment_api.action.json")
    policy = load_yaml(ROOT / "examples" / "security_policy.yml")
    evidence = [
        *base_deploy_proofs(),
        evidence_event("ev_semgrep_clean", "semgrep", "passed"),
        evidence_event("ev_snyk_failed", "snyk", "failed"),
    ]

    proof = payload_to_proof_vector(evidence)
    warrant = evaluate(action=action, proof_vector=proof, policy=policy, now_epoch=1779100001)

    assert any(item["type"] == "dimension_conflict" for item in proof["contradictions"])
    assert warrant["decision"] == "BLOCK"
    assert "contradiction:dimension_conflict" in warrant["missing_evidence"]


def test_api_evaluate_from_evidence_blocks_conflicting_security_sources():
    client = TestClient(app)
    action = load_json(ROOT / "examples" / "deploy_payment_api.action.json")
    policy = load_yaml(ROOT / "examples" / "security_policy.yml")
    evidence = [
        *base_deploy_proofs(),
        evidence_event("ev_semgrep_clean", "semgrep", "passed"),
        evidence_event("ev_snyk_failed", "snyk", "failed"),
    ]

    response = client.post(
        "/v1/warrants/evaluate-from-evidence",
        json={"action": action, "evidence": evidence, "policy": policy},
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["warrant"]["decision"] == "BLOCK"
    assert any(item["type"] == "dimension_conflict" for item in body["proof_vector"]["contradictions"])


def test_ledger_verifies_after_multiple_real_decisions(tmp_path: Path):
    action = load_json(ROOT / "examples" / "deploy_payment_api.action.json")
    policy = load_yaml(ROOT / "examples" / "security_policy.yml")
    allow_proof = payload_to_proof_vector([*base_deploy_proofs(), evidence_event("ev_semgrep_clean", "semgrep", "passed")])
    block_proof = payload_to_proof_vector([
        *base_deploy_proofs(),
        evidence_event("ev_semgrep_clean_2", "semgrep", "passed"),
        evidence_event("ev_snyk_failed_2", "snyk", "failed"),
    ])

    allow_warrant = evaluate(action=action, proof_vector=allow_proof, policy=policy, now_epoch=1779100001)
    block_warrant = evaluate(action=action, proof_vector=block_proof, policy=policy, now_epoch=1779100001)

    ledger = tmp_path / "proof_ledger.jsonl"
    append_ledger_entry(ledger, allow_warrant)
    append_ledger_entry(ledger, block_warrant)

    assert verify_ledger(ledger) is True
    lines = ledger.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    assert json.loads(lines[0])["previous_hash"] == "GENESIS"
    assert json.loads(lines[1])["previous_hash"] == json.loads(lines[0])["current_hash"]
