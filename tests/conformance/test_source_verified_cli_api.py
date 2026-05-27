from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from fastapi.testclient import TestClient

from axiom.api import app
from axiom.source_verification import load_json, load_yaml

ROOT = Path(__file__).resolve().parents[2]
ACTION = ROOT / "examples/devops/deploy_to_production.action_request.json"
SOURCES = ROOT / "examples/devops/sources_allow.json"
POLICY = ROOT / "examples/devops/devops_prod_policy.yml"


def test_verify_action_cli_outputs_warrant_and_proof(tmp_path):
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "reference/python")
    out = tmp_path / "warrant.json"
    proof = tmp_path / "proof.json"
    verified = tmp_path / "verified.json"
    ledger = tmp_path / "ledger.jsonl"

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "axiom.cli",
            "verify-action",
            "--action-request",
            str(ACTION),
            "--sources",
            str(SOURCES),
            "--policy",
            str(POLICY),
            "--out",
            str(out),
            "--proof-out",
            str(proof),
            "--verified-out",
            str(verified),
            "--ledger",
            str(ledger),
        ],
        cwd=ROOT,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    assert result.returncode == 0, result.stdout
    warrant = json.loads(out.read_text())
    proof_vector = json.loads(proof.read_text())
    verified_evidence = json.loads(verified.read_text())

    assert warrant["decision"] == "ALLOW"
    assert proof_vector["source_verification"]["passed"] == 6
    assert len(verified_evidence) == 6
    assert ledger.exists()


def test_source_verified_api_endpoint_allows_when_sources_are_valid():
    client = TestClient(app)
    response = client.post(
        "/v1/actions/evaluate",
        json={
            "action_request": load_json(ACTION),
            "sources": load_json(SOURCES),
            "policy": load_yaml(POLICY),
        },
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["warrant"]["decision"] == "ALLOW"
    assert payload["proof_vector"]["source_verification"]["verified_claims"] == 6
    assert len(payload["verified_evidence"]) == 6
