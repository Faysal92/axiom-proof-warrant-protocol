from __future__ import annotations

import json
from pathlib import Path
import sys

import yaml
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "reference" / "python"))

from axiom.api import app


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_api_evaluate_returns_warrant():
    client = TestClient(app)

    response = client.post(
        "/v1/warrants/evaluate",
        json={
            "action": load_json(ROOT / "examples" / "deploy_payment_api.action.json"),
            "proof_vector": load_json(ROOT / "examples" / "deploy_payment_api.semgrep_clean.proof_vector.json"),
            "policy": load_yaml(ROOT / "examples" / "security_policy.yml"),
            "write_ledger": False,
        },
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["warrant"]["decision"] == "ALLOW"
    assert body["warrant"]["warrant_type"] == "EXECUTION_WARRANT"


def test_api_evaluate_can_append_ledger(tmp_path):
    client = TestClient(app)
    ledger_path = tmp_path / "api_ledger.jsonl"

    response = client.post(
        "/v1/warrants/evaluate",
        json={
            "action": load_json(ROOT / "examples" / "deploy_payment_api.action.json"),
            "proof_vector": load_json(ROOT / "examples" / "deploy_payment_api.semgrep_failed.proof_vector.json"),
            "policy": load_yaml(ROOT / "examples" / "security_policy.yml"),
            "write_ledger": True,
            "ledger_path": str(ledger_path),
        },
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["warrant"]["decision"] == "BLOCK"
    assert body["ledger_entry"]["decision"] == "BLOCK"
    assert ledger_path.exists()
