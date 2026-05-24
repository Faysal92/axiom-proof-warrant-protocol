import json
from pathlib import Path
import sys

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "reference" / "python"))

from axiom.crypto import verify_signature
from axiom.evaluator import evaluate
from axiom.ledger import append_ledger_entry, verify_ledger


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_yaml(path):
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))


def examples(name):
    return ROOT / "examples" / name


def test_missing_proof_suspends_not_blocks():
    action = load_json(examples("deploy_payment_api.action.json"))
    proof = load_json(examples("deploy_payment_api.missing_proof_vector.json"))
    policy = load_yaml(examples("production_policy.yml"))

    warrant = evaluate(action=action, proof_vector=proof, policy=policy, now_epoch=1779100001)

    assert warrant["decision"] == "SUSPEND"
    assert "integration_tests_passed" in warrant["missing_evidence"]
    assert "security_scan_clean" in warrant["missing_evidence"]
    assert "rollback_available" in warrant["missing_evidence"]
    assert warrant["challenge"]["resubmit_allowed"] is True
    assert verify_signature(warrant)


def test_failed_security_scan_blocks():
    action = load_json(examples("deploy_payment_api.action.json"))
    proof = load_json(examples("deploy_payment_api.failed_security_scan.proof_vector.json"))
    policy = load_yaml(examples("production_policy.yml"))

    warrant = evaluate(action=action, proof_vector=proof, policy=policy, now_epoch=1779100001)

    assert warrant["decision"] == "BLOCK"
    assert any(item.startswith("contradiction:") or item == "security_scan_clean:failed" for item in warrant["missing_evidence"])


def test_sufficient_p4_proof_allows():
    action = load_json(examples("deploy_payment_api.action.json"))
    proof = load_json(examples("deploy_payment_api.good_proof_vector.json"))
    policy = load_yaml(examples("production_policy.yml"))

    warrant = evaluate(action=action, proof_vector=proof, policy=policy, now_epoch=1779100001)

    assert warrant["decision"] == "ALLOW"
    assert warrant["missing_evidence"] == []
    assert verify_signature(warrant)


def test_only_human_review_missing_requires_human_review():
    action = load_json(examples("deploy_payment_api.action.json"))
    proof = load_json(examples("deploy_payment_api.human_review_missing.proof_vector.json"))
    policy = load_yaml(examples("production_policy.yml"))

    warrant = evaluate(action=action, proof_vector=proof, policy=policy, now_epoch=1779100001)

    assert warrant["decision"] == "REQUIRE_HUMAN_REVIEW"
    assert warrant["missing_evidence"] == ["human_reviewed:failed"]


def test_risk_bound_blocks_even_with_good_proof():
    action = load_json(examples("deploy_payment_api.action.json"))
    proof = load_json(examples("deploy_payment_api.good_proof_vector.json"))
    policy = load_yaml(examples("strict_risk_policy.yml"))

    warrant = evaluate(action=action, proof_vector=proof, policy=policy, now_epoch=1779100001)

    assert warrant["decision"] == "BLOCK"
    assert any(item.startswith("risk_bound_exceeded") for item in warrant["missing_evidence"])


def test_ledger_hash_chain(tmp_path):
    action = load_json(examples("deploy_payment_api.action.json"))
    proof = load_json(examples("deploy_payment_api.missing_proof_vector.json"))
    policy = load_yaml(examples("production_policy.yml"))

    warrant = evaluate(action=action, proof_vector=proof, policy=policy, now_epoch=1779100001)

    ledger_path = tmp_path / "ledger.jsonl"
    append_ledger_entry(ledger_path, warrant)
    assert verify_ledger(ledger_path)


def test_semgrep_clean_scan_allows_with_security_policy():
    action = load_json(examples("deploy_payment_api.action.json"))
    proof = load_json(examples("deploy_payment_api.semgrep_clean.proof_vector.json"))
    policy = load_yaml(examples("security_policy.yml"))

    warrant = evaluate(action=action, proof_vector=proof, policy=policy, now_epoch=1779100001)

    assert warrant["decision"] == "ALLOW"
    assert warrant["missing_evidence"] == []
    assert verify_signature(warrant)


def test_semgrep_failed_scan_blocks_with_security_policy():
    action = load_json(examples("deploy_payment_api.action.json"))
    proof = load_json(examples("deploy_payment_api.semgrep_failed.proof_vector.json"))
    policy = load_yaml(examples("security_policy.yml"))

    warrant = evaluate(action=action, proof_vector=proof, policy=policy, now_epoch=1779100001)

    assert warrant["decision"] == "BLOCK"
    assert any(item.startswith("contradiction:security_scan_failure") or item == "security_scan_clean:failed" for item in warrant["missing_evidence"])
    assert verify_signature(warrant)


def test_semgrep_missing_scan_suspends_with_security_policy():
    action = load_json(examples("deploy_payment_api.action.json"))
    proof = load_json(examples("deploy_payment_api.semgrep_missing.proof_vector.json"))
    policy = load_yaml(examples("security_policy.yml"))

    warrant = evaluate(action=action, proof_vector=proof, policy=policy, now_epoch=1779100001)

    assert warrant["decision"] == "SUSPEND"
    assert "security_scan_clean" in warrant["missing_evidence"]
    assert warrant["challenge"]["resubmit_allowed"] is True
    assert verify_signature(warrant)
