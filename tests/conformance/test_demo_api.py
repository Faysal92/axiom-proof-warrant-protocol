from fastapi.testclient import TestClient

from axiom.demo_api import app


def test_demo_scenarios_are_available() -> None:
    client = TestClient(app)
    response = client.get("/v1/demo/scenarios")
    assert response.status_code == 200
    scenario_ids = {item["id"] for item in response.json()}
    assert "allow_prod_deploy" in scenario_ids
    assert "suspend_missing_rollback" in scenario_ids
    assert "block_failed_security" in scenario_ids


def test_demo_allow_scenario_returns_warrant() -> None:
    client = TestClient(app)
    response = client.post("/v1/demo/evaluate", json={"scenario_id": "allow_prod_deploy"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["warrant"]["decision"] == "ALLOW"
    assert payload["warrant"]["signature"]["algorithm"] == "HMAC-SHA256"
    assert payload["ledger_preview"]["warrant_hash"].startswith("sha256:")


def test_demo_missing_rollback_suspends() -> None:
    client = TestClient(app)
    response = client.post("/v1/demo/evaluate", json={"scenario_id": "suspend_missing_rollback"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["warrant"]["decision"] == "SUSPEND"
    assert any("rollback_available" in item for item in payload["warrant"]["missing_evidence"])


def test_demo_failed_security_blocks() -> None:
    client = TestClient(app)
    response = client.post("/v1/demo/evaluate", json={"scenario_id": "block_failed_security"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["warrant"]["decision"] == "BLOCK"
    assert payload["proof_vector"]["contradictions"]
