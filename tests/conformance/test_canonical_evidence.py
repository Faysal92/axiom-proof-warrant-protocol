from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import yaml
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "reference" / "python"))

from axiom.api import app
from axiom.evaluator import evaluate
from axiom.evidence.adapters.external_api import payload_to_proof_vector
from axiom.evidence.adapters.local_json import local_json_to_events, local_json_to_proof_vector


def load_json(path: Path) -> dict:
    import json
    return json.loads(path.read_text(encoding="utf-8"))


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_local_json_canonical_evidence_allows_non_code_action():
    proof = local_json_to_proof_vector(ROOT / "examples" / "generic" / "wire_transfer_clean.evidence.json")
    action = load_json(ROOT / "examples" / "generic" / "wire_transfer.action.json")
    policy = load_yaml(ROOT / "examples" / "generic" / "wire_transfer_policy.yml")

    warrant = evaluate(action=action, proof_vector=proof, policy=policy, now_epoch=1779100001)

    assert warrant["decision"] == "ALLOW"
    assert proof["dimensions"]["fraud_score_below_threshold"]["status"] == "passed"
    assert proof["dimensions"]["beneficiary_verified"]["status"] == "passed"
    assert proof["dimensions"]["human_reviewed"]["status"] == "passed"


def test_external_api_payload_high_risk_blocks_non_code_action():
    payload = load_json(ROOT / "examples" / "generic" / "wire_transfer_high_risk.evidence.json")
    proof = payload_to_proof_vector(payload)
    action = load_json(ROOT / "examples" / "generic" / "wire_transfer.action.json")
    policy = load_yaml(ROOT / "examples" / "generic" / "wire_transfer_policy.yml")

    warrant = evaluate(action=action, proof_vector=proof, policy=policy, now_epoch=1779100001)

    assert warrant["decision"] == "BLOCK"
    assert any(item.startswith("contradiction:fraud_risk_above_threshold") for item in warrant["missing_evidence"])


def test_jsonl_canonical_evidence_missing_human_review_requires_review():
    events = local_json_to_events(ROOT / "examples" / "generic" / "wire_transfer_missing_review.evidence.jsonl")
    assert len(events) == 1

    proof = local_json_to_proof_vector(ROOT / "examples" / "generic" / "wire_transfer_missing_review.evidence.jsonl")
    action = load_json(ROOT / "examples" / "generic" / "wire_transfer.action.json")
    policy = load_yaml(ROOT / "examples" / "generic" / "wire_transfer_policy.yml")

    warrant = evaluate(action=action, proof_vector=proof, policy=policy, now_epoch=1779100001)

    assert warrant["decision"] == "REQUIRE_HUMAN_REVIEW"
    assert warrant["missing_evidence"] == ["human_reviewed"]


def test_cli_evidence_eval_works_with_canonical_json(tmp_path: Path):
    out = tmp_path / "wire_transfer.warrant.json"
    proof_out = tmp_path / "wire_transfer.proof_vector.json"

    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "reference" / "python")

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "axiom.cli",
            "evidence-eval",
            "--action",
            str(ROOT / "examples" / "generic" / "wire_transfer.action.json"),
            "--evidence",
            str(ROOT / "examples" / "generic" / "wire_transfer_clean.evidence.json"),
            "--policy",
            str(ROOT / "examples" / "generic" / "wire_transfer_policy.yml"),
            "--out",
            str(out),
            "--proof-out",
            str(proof_out),
            "--ledger",
            str(tmp_path / "ledger.jsonl"),
        ],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "Decision: ALLOW" in result.stdout
    assert load_json(out)["decision"] == "ALLOW"
    assert "fraud_score_below_threshold" in load_json(proof_out)["dimensions"]


def test_api_convert_and_evaluate_from_evidence():
    client = TestClient(app)
    evidence = load_json(ROOT / "examples" / "generic" / "wire_transfer_clean.evidence.json")
    action = load_json(ROOT / "examples" / "generic" / "wire_transfer.action.json")
    policy = load_yaml(ROOT / "examples" / "generic" / "wire_transfer_policy.yml")

    convert = client.post("/v1/evidence/convert", json={"evidence": evidence})
    assert convert.status_code == 200, convert.text
    assert convert.json()["events_count"] == 2
    assert "human_reviewed" in convert.json()["proof_vector"]["dimensions"]

    evaluated = client.post(
        "/v1/warrants/evaluate-from-evidence",
        json={"action": action, "evidence": evidence, "policy": policy},
    )
    assert evaluated.status_code == 200, evaluated.text
    body = evaluated.json()
    assert body["warrant"]["decision"] == "ALLOW"
    assert "proof_vector" in body
