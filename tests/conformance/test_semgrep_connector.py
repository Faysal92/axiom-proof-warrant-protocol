from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]

sys.path.insert(0, str(ROOT / "reference" / "python"))

from axiom.connectors.semgrep import semgrep_to_partial_proof_vector
from axiom.evaluator import evaluate
from axiom.proof_router import merge_proof_vectors


def load_json(path: Path) -> dict:
    import json
    return json.loads(path.read_text(encoding="utf-8"))


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_semgrep_connector_emits_only_security_evidence():
    proof = semgrep_to_partial_proof_vector(
        ROOT / "examples" / "scanners" / "semgrep_failed_scan.json",
        target="payment-api",
        environment="production",
        commit="abc123",
        now_epoch=1779100000,
    )

    assert "security_scan_clean" in proof["dimensions"]
    assert proof["dimensions"]["security_scan_clean"]["status"] == "failed"
    assert proof["security_evidence"]["scanner"] == "semgrep"

    # Proof hygiene: Semgrep must not invent evidence it does not own.
    assert "human_reviewed" not in proof["dimensions"]
    assert "rollback_available" not in proof["dimensions"]
    assert "unit_tests_passed" not in proof["dimensions"]
    assert "integration_tests_passed" not in proof["dimensions"]

    assert proof["evidence_refs"] == ["semgrep_report:semgrep_failed_scan.json"]


def test_semgrep_connector_uses_dynamic_freshness_epoch():
    before = int(time.time()) - 2
    proof = semgrep_to_partial_proof_vector(
        ROOT / "examples" / "scanners" / "semgrep_clean_scan.json",
        target="payment-api",
        environment="production",
        commit="abc123",
    )
    after = int(time.time()) + 2

    assert before <= proof["meta"]["freshness_epoch"] <= after


def test_semgrep_failed_report_blocks_after_proof_router_merge():
    base = load_json(ROOT / "examples" / "deploy_payment_api.ci_review_rollback.proof_vector.json")
    semgrep = semgrep_to_partial_proof_vector(
        ROOT / "examples" / "scanners" / "semgrep_failed_scan.json",
        target="payment-api",
        environment="production",
        commit="abc123",
        branch="main",
        service="payments",
        now_epoch=1779100000,
    )
    merged = merge_proof_vectors(base, semgrep)

    action = load_json(ROOT / "examples" / "deploy_payment_api.action.json")
    policy = load_yaml(ROOT / "examples" / "security_policy.yml")
    warrant = evaluate(action=action, proof_vector=merged, policy=policy, now_epoch=1779100001)

    assert warrant["decision"] == "BLOCK"
    assert any(item.startswith("contradiction:security_scan_failure") for item in warrant["missing_evidence"])


def test_semgrep_clean_report_allows_after_proof_router_merge():
    base = load_json(ROOT / "examples" / "deploy_payment_api.ci_review_rollback.proof_vector.json")
    semgrep = semgrep_to_partial_proof_vector(
        ROOT / "examples" / "scanners" / "semgrep_clean_scan.json",
        target="payment-api",
        environment="production",
        commit="abc123",
        branch="main",
        service="payments",
        now_epoch=1779100000,
    )
    merged = merge_proof_vectors(base, semgrep)

    action = load_json(ROOT / "examples" / "deploy_payment_api.action.json")
    policy = load_yaml(ROOT / "examples" / "security_policy.yml")
    warrant = evaluate(action=action, proof_vector=merged, policy=policy, now_epoch=1779100001)

    assert warrant["decision"] == "ALLOW"


def test_cli_semgrep_proof_subprocess_has_correct_pythonpath(tmp_path):
    out = tmp_path / "semgrep.partial_proof_vector.json"

    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "reference" / "python")

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "axiom.cli",
            "semgrep-proof",
            "--report",
            str(ROOT / "examples" / "scanners" / "semgrep_clean_scan.json"),
            "--target",
            "payment-api",
            "--environment",
            "production",
            "--commit",
            "abc123",
            "--out",
            str(out),
        ],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    proof = load_json(out)
    assert proof["dimensions"]["security_scan_clean"]["status"] == "passed"
    assert "human_reviewed" not in proof["dimensions"]
