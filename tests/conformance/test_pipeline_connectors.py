from __future__ import annotations

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "reference" / "python"))

from axiom.connectors.github_checks import github_checks_to_partial_proof_vector
from axiom.connectors.github_reviews import github_reviews_to_partial_proof_vector
from axiom.connectors.rollback import rollback_to_partial_proof_vector
from axiom.connectors.semgrep import semgrep_to_partial_proof_vector
from axiom.evaluator import evaluate
from axiom.proof_router import merge_proof_vectors


def load_json(path: Path) -> dict:
    import json
    return json.loads(path.read_text(encoding="utf-8"))


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_github_checks_connector_emits_only_ci_evidence():
    proof = github_checks_to_partial_proof_vector(
        ROOT / "examples" / "github" / "check_runs_passed.json",
        target="payment-api",
        environment="production",
        service="payments",
        now_epoch=1779100000,
    )

    assert proof["dimensions"]["unit_tests_passed"]["status"] == "passed"
    assert proof["dimensions"]["integration_tests_passed"]["status"] == "passed"

    assert "security_scan_clean" not in proof["dimensions"]
    assert "human_reviewed" not in proof["dimensions"]
    assert "rollback_available" not in proof["dimensions"]


def test_github_reviews_connector_emits_only_review_evidence():
    proof = github_reviews_to_partial_proof_vector(
        ROOT / "examples" / "github" / "pr_reviews_approved.json",
        target="payment-api",
        environment="production",
        service="payments",
        now_epoch=1779100000,
    )

    assert proof["dimensions"]["human_reviewed"]["status"] == "passed"
    assert proof["dimensions"]["human_reviewed"]["approved_reviews"] == 1

    assert "security_scan_clean" not in proof["dimensions"]
    assert "unit_tests_passed" not in proof["dimensions"]
    assert "integration_tests_passed" not in proof["dimensions"]
    assert "rollback_available" not in proof["dimensions"]


def test_rollback_connector_emits_only_rollback_evidence():
    proof = rollback_to_partial_proof_vector(
        ROOT / "examples" / "rollback" / "rollback_plan_available.json",
        target="payment-api",
        environment="production",
        service="payments",
        now_epoch=1779100000,
    )

    assert proof["dimensions"]["rollback_available"]["status"] == "passed"

    assert "security_scan_clean" not in proof["dimensions"]
    assert "unit_tests_passed" not in proof["dimensions"]
    assert "integration_tests_passed" not in proof["dimensions"]
    assert "human_reviewed" not in proof["dimensions"]


def test_full_pipeline_proofs_merge_to_allow():
    ci = github_checks_to_partial_proof_vector(
        ROOT / "examples" / "github" / "check_runs_passed.json",
        target="payment-api",
        environment="production",
        service="payments",
        now_epoch=1779100000,
    )
    review = github_reviews_to_partial_proof_vector(
        ROOT / "examples" / "github" / "pr_reviews_approved.json",
        target="payment-api",
        environment="production",
        service="payments",
        now_epoch=1779100000,
    )
    rollback = rollback_to_partial_proof_vector(
        ROOT / "examples" / "rollback" / "rollback_plan_available.json",
        target="payment-api",
        environment="production",
        service="payments",
        now_epoch=1779100000,
    )
    security = semgrep_to_partial_proof_vector(
        ROOT / "examples" / "scanners" / "semgrep_clean_scan.json",
        target="payment-api",
        environment="production",
        commit="abc123",
        branch="main",
        service="payments",
        now_epoch=1779100000,
    )

    merged = merge_proof_vectors(ci, review, rollback, security)
    action = load_json(ROOT / "examples" / "deploy_payment_api.action.json")
    policy = load_yaml(ROOT / "examples" / "security_policy.yml")
    warrant = evaluate(action=action, proof_vector=merged, policy=policy, now_epoch=1779100001)

    assert warrant["decision"] == "ALLOW"


def test_missing_pr_review_requires_human_review():
    ci = github_checks_to_partial_proof_vector(
        ROOT / "examples" / "github" / "check_runs_passed.json",
        target="payment-api",
        environment="production",
        service="payments",
        now_epoch=1779100000,
    )
    review = github_reviews_to_partial_proof_vector(
        ROOT / "examples" / "github" / "pr_reviews_missing.json",
        target="payment-api",
        environment="production",
        service="payments",
        now_epoch=1779100000,
    )
    rollback = rollback_to_partial_proof_vector(
        ROOT / "examples" / "rollback" / "rollback_plan_available.json",
        target="payment-api",
        environment="production",
        service="payments",
        now_epoch=1779100000,
    )
    security = semgrep_to_partial_proof_vector(
        ROOT / "examples" / "scanners" / "semgrep_clean_scan.json",
        target="payment-api",
        environment="production",
        commit="abc123",
        branch="main",
        service="payments",
        now_epoch=1779100000,
    )

    merged = merge_proof_vectors(ci, review, rollback, security)
    action = load_json(ROOT / "examples" / "deploy_payment_api.action.json")
    policy = load_yaml(ROOT / "examples" / "security_policy.yml")
    warrant = evaluate(action=action, proof_vector=merged, policy=policy, now_epoch=1779100001)

    assert warrant["decision"] == "REQUIRE_HUMAN_REVIEW"
    assert "human_reviewed:failed" in warrant["missing_evidence"]


def test_integration_check_failure_suspends_not_allow():
    ci = github_checks_to_partial_proof_vector(
        ROOT / "examples" / "github" / "check_runs_integration_failed.json",
        target="payment-api",
        environment="production",
        service="payments",
        now_epoch=1779100000,
    )
    review = github_reviews_to_partial_proof_vector(
        ROOT / "examples" / "github" / "pr_reviews_approved.json",
        target="payment-api",
        environment="production",
        service="payments",
        now_epoch=1779100000,
    )
    rollback = rollback_to_partial_proof_vector(
        ROOT / "examples" / "rollback" / "rollback_plan_available.json",
        target="payment-api",
        environment="production",
        service="payments",
        now_epoch=1779100000,
    )
    security = semgrep_to_partial_proof_vector(
        ROOT / "examples" / "scanners" / "semgrep_clean_scan.json",
        target="payment-api",
        environment="production",
        commit="abc123",
        branch="main",
        service="payments",
        now_epoch=1779100000,
    )

    merged = merge_proof_vectors(ci, review, rollback, security)
    action = load_json(ROOT / "examples" / "deploy_payment_api.action.json")
    policy = load_yaml(ROOT / "examples" / "security_policy.yml")
    warrant = evaluate(action=action, proof_vector=merged, policy=policy, now_epoch=1779100001)

    assert warrant["decision"] == "SUSPEND"
    assert "integration_tests_passed:failed" in warrant["missing_evidence"]
