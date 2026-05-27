from fastapi.testclient import TestClient

from axiom.demo_api import app


client = TestClient(app)


def test_custom_template_endpoint_returns_payload():
    response = client.get("/v1/demo/custom-template")

    assert response.status_code == 200
    payload = response.json()

    assert "action_request" in payload
    assert "sources" in payload
    assert "policy" in payload


def test_evaluate_custom_payload_returns_warrant():
    template = client.get("/v1/demo/custom-template").json()

    response = client.post("/v1/demo/evaluate-custom", json=template)

    assert response.status_code == 200
    payload = response.json()

    assert payload["warrant"]["decision"] in {"ALLOW", "SUSPEND", "BLOCK", "DENY", "ESCALATE"}
    assert "verified_evidence" in payload
    assert "ledger_preview" in payload
