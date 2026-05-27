from __future__ import annotations

import copy
from typing import Any, Literal

import yaml
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .crypto import sha256_hex
from .source_verification import evaluate_action_request


BASE_ACTION_REQUEST: dict[str, Any] = {
    "actor": {
        "actor_id": "agent_ops_01",
        "actor_type": "ai_ops_agent",
        "identity_verified": True,
    },
    "action": {
        "action_type": "deploy_to_production",
        "target": "prod.payment-api",
        "environment": "production",
    },
    "claim": {
        "summary": "Deploy payment-api after a generated patch.",
        "requested_by": "agent_ops_01",
        "raw_intent": "Ship the patch to production now. I have the ticket, PR, CI, security scan and rollback plan.",
    },
    "action_weight": {
        "final_weight": 0.86,
        "criticality": "high",
    },
    "risk_profile": {
        "criticality": "high",
        "blast_radius": "customer_payments",
        "reversible": True,
        "data_sensitivity": "high",
        "score": 0.86,
    },
    "evidence_claims": [
        {
            "claim_id": "clm_change_ticket",
            "type": "jira_ticket",
            "ref": "CHG-1001",
            "dimension": "change_ticket_approved",
            "required_status": "approved",
            "target": "prod.payment-api",
            "environment": "production",
            "max_age_hours": 72,
        },
        {
            "claim_id": "clm_pr_review",
            "type": "github_pr",
            "ref": "42",
            "dimension": "github_pr_approved",
            "min_approvals": 2,
            "required_checks": ["unit-tests", "integration-tests", "semgrep"],
            "commit": "abc123",
            "target": "prod.payment-api",
            "environment": "production",
        },
        {
            "claim_id": "clm_ci_run",
            "type": "ci_run",
            "ref": "run-9001",
            "dimension": "ci_checks_passed",
            "required_checks": ["unit-tests", "integration-tests"],
            "target": "prod.payment-api",
            "environment": "production",
        },
        {
            "claim_id": "clm_security_scan",
            "type": "security_scan",
            "ref": "scan-9002",
            "dimension": "security_scan_clean",
            "target": "prod.payment-api",
            "environment": "production",
        },
        {
            "claim_id": "clm_rollback",
            "type": "rollback_plan",
            "ref": "rb-payment-api-v1",
            "dimension": "rollback_available",
            "target": "prod.payment-api",
            "environment": "production",
            "max_age_hours": 168,
        },
        {
            "claim_id": "clm_deployment_window",
            "type": "deployment_window",
            "ref": "window-prod-standard",
            "dimension": "deployment_window_allowed",
            "target": "prod.payment-api",
            "environment": "production",
        },
    ],
}

BASE_POLICY: dict[str, Any] = {
    "policy_id": "devops_prod_source_verified_policy",
    "policy_version": "0.1.7-demo",
    "requirement": {
        "action": "deploy_to_production",
        "target": "prod.payment-api",
        "context": {
            "description": "Production deployment must be backed by source-verified evidence."
        },
        "min_meta": {"required_level": "P4_EXECUTED", "max_age_seconds": 86400},
        "required_scope": {
            "target": "prod.payment-api",
            "environment": "production",
            "action_type": "deploy_to_production",
        },
        "mandatory_dimensions": [
            "change_ticket_approved",
            "github_pr_approved",
            "ci_checks_passed",
            "security_scan_clean",
            "rollback_available",
            "deployment_window_allowed",
        ],
        "critical_requirements": ["security_scan_clean"],
        "risk_policy": {"block_on_failed_security_scan": True, "max_risk_score": 0.95},
    },
}

BASE_SOURCES: dict[str, Any] = {
    "jira": {
        "tickets": [
            {
                "id": "CHG-1001",
                "status": "approved",
                "target": "prod.payment-api",
                "environment": "production",
                "approver": "sre-lead",
                "updated_at_epoch": 4102444800,
            }
        ]
    },
    "github": {
        "pull_requests": [
            {
                "number": "42",
                "target": "prod.payment-api",
                "environment": "production",
                "head_sha": "abc123",
                "reviews": [
                    {"user": "alice", "state": "APPROVED"},
                    {"user": "bob", "state": "APPROVED"},
                ],
                "checks": [
                    {"name": "unit-tests", "status": "passed"},
                    {"name": "integration-tests", "status": "passed"},
                    {"name": "semgrep", "status": "passed"},
                ],
            }
        ]
    },
    "ci": {
        "runs": [
            {
                "id": "run-9001",
                "status": "passed",
                "target": "prod.payment-api",
                "environment": "production",
                "checks": [
                    {"name": "unit-tests", "status": "passed"},
                    {"name": "integration-tests", "status": "passed"},
                ],
            }
        ],
        "security_scans": [
            {
                "id": "scan-9002",
                "clean": True,
                "target": "prod.payment-api",
                "environment": "production",
                "tool": "semgrep",
                "critical_findings": 0,
            }
        ],
    },
    "rollback": {
        "plans": [
            {
                "id": "rb-payment-api-v1",
                "available": True,
                "target": "prod.payment-api",
                "environment": "production",
                "updated_at_epoch": 4102444800,
            }
        ]
    },
    "deployment_windows": {
        "windows": [
            {
                "id": "window-prod-standard",
                "allowed": True,
                "target": "prod.payment-api",
                "environment": "production",
            }
        ]
    },
}


class ScenarioSummary(BaseModel):
    id: str
    title: str
    expected_decision: str
    severity: Literal["success", "warning", "danger"]
    description: str


class DemoEvaluateRequest(BaseModel):
    scenario_id: str = Field(default="allow_prod_deploy")
    write_ledger: bool = False


class PipelineStep(BaseModel):
    key: str
    label: str
    status: Literal["idle", "running", "ok", "warning", "failed"]
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class DemoEvaluateResponse(BaseModel):
    scenario: ScenarioSummary
    raw_agent_context: list[str]
    action_request: dict[str, Any]
    simulated_sources: dict[str, Any]
    policy_yaml: str
    pipeline: list[PipelineStep]
    verified_evidence: list[dict[str, Any]]
    proof_vector: dict[str, Any]
    warrant: dict[str, Any]
    ledger_preview: dict[str, Any]


def _scenario_summaries() -> list[ScenarioSummary]:
    return [
        ScenarioSummary(
            id="allow_prod_deploy",
            title="ALLOW — production deploy is fully proven",
            expected_decision="ALLOW",
            severity="success",
            description="All source verifiers pass: ticket approved, PR reviewed, CI passed, security scan clean, rollback available, deployment window open.",
        ),
        ScenarioSummary(
            id="suspend_missing_rollback",
            title="SUSPEND — rollback proof is missing",
            expected_decision="SUSPEND",
            severity="warning",
            description="The agent claims rollback exists, but the rollback source does not contain a matching plan.",
        ),
        ScenarioSummary(
            id="block_failed_security",
            title="BLOCK — security scan failed",
            expected_decision="BLOCK",
            severity="danger",
            description="A critical security finding contradicts the requested production deployment.",
        ),
        ScenarioSummary(
            id="suspend_unapproved_ticket",
            title="SUSPEND — change ticket is not approved",
            expected_decision="SUSPEND",
            severity="warning",
            description="The change ticket exists but is not approved, so the action is not sufficiently proven.",
        ),
    ]


def _summary_by_id(scenario_id: str) -> ScenarioSummary:
    for item in _scenario_summaries():
        if item.id == scenario_id:
            return item
    raise HTTPException(status_code=404, detail=f"Unknown scenario_id: {scenario_id}")


def _sources_for_scenario(scenario_id: str) -> dict[str, Any]:
    sources = copy.deepcopy(BASE_SOURCES)

    if scenario_id == "allow_prod_deploy":
        return sources

    if scenario_id == "suspend_missing_rollback":
        sources["rollback"]["plans"] = []
        return sources

    if scenario_id == "block_failed_security":
        sources["ci"]["security_scans"][0]["clean"] = False
        sources["ci"]["security_scans"][0]["critical_findings"] = 1
        sources["ci"]["security_scans"][0]["finding_summary"] = "Critical SQL injection finding in payment-api route."
        return sources

    if scenario_id == "suspend_unapproved_ticket":
        sources["jira"]["tickets"][0]["status"] = "pending"
        sources["jira"]["tickets"][0]["approver"] = None
        return sources

    raise HTTPException(status_code=404, detail=f"Unknown scenario_id: {scenario_id}")


def _raw_context_for_scenario(scenario_id: str) -> list[str]:
    common = [
        "agent_ops_01 proposes: deploy payment-api to production now.",
        "The agent claims: change ticket CHG-1001 exists and is approved.",
        "The agent claims: GitHub PR #42 has two approvals and required checks.",
        "The agent claims: CI run run-9001 passed.",
        "The agent claims: Semgrep scan scan-9002 is clean.",
        "The agent claims: rollback plan rb-payment-api-v1 is available.",
    ]
    if scenario_id == "suspend_missing_rollback":
        common.append("Enterprise source says: no matching rollback plan found.")
    elif scenario_id == "block_failed_security":
        common.append("Enterprise source says: security scan contains one critical finding.")
    elif scenario_id == "suspend_unapproved_ticket":
        common.append("Enterprise source says: change ticket exists but is still pending.")
    else:
        common.append("Enterprise sources confirm all claimed evidence.")
    return common


def _status_for_step(decision: str, verified: list[dict[str, Any]], proof_vector: dict[str, Any]) -> list[PipelineStep]:
    failed = [item for item in verified if item.get("status") == "failed"]
    missing = [item for item in verified if item.get("status") in {"missing", "expired", "unknown"}]
    verified_ok = not failed and not missing
    has_blocking_contradiction = bool(proof_vector.get("contradictions"))

    policy_status: Literal["ok", "warning", "failed"]
    if decision == "ALLOW":
        policy_status = "ok"
    elif decision == "BLOCK":
        policy_status = "failed"
    else:
        policy_status = "warning"

    return [
        PipelineStep(
            key="intake",
            label="1. Intake",
            status="ok",
            message="Raw agent intent and enterprise context received.",
            details={"input": "raw agent logs + proposed action + claimed evidence"},
        ),
        PipelineStep(
            key="normalizer",
            label="2. Normalizer",
            status="ok",
            message="Intent extracted into a canonical AXIOM action request.",
            details={"law": "The normalizer prepares; it does not decide."},
        ),
        PipelineStep(
            key="schemas",
            label="3. Pydantic Schemas",
            status="ok",
            message="ActionRequest and evidence claims are structurally valid.",
            details={"law": "Pydantic structures. It does not prove."},
        ),
        PipelineStep(
            key="verifiers",
            label="4. Source Verifiers",
            status="ok" if verified_ok else "warning" if not failed else "failed",
            message="Evidence checked at the source. AXIOM does not trust agent claims.",
            details={
                "passed": sum(1 for item in verified if item.get("status") == "passed"),
                "failed": len(failed),
                "missing_or_unknown": len(missing),
            },
        ),
        PipelineStep(
            key="policy",
            label="5. Policy Kernel",
            status=policy_status,
            message="Deterministic policy evaluated verified evidence against required proof.",
            details={"decision": decision, "contradictions": has_blocking_contradiction},
        ),
        PipelineStep(
            key="warrant",
            label="6. Warrant Engine",
            status="ok" if decision == "ALLOW" else "warning" if decision != "BLOCK" else "failed",
            message="Execution Warrant generated with decision, reason, missing evidence and signature.",
            details={"decision": decision},
        ),
        PipelineStep(
            key="ledger",
            label="7. Proof Ledger",
            status="ok",
            message="Decision is ready to be recorded for auditability.",
            details={"mode": "demo ledger preview"},
        ),
    ]


app = FastAPI(
    title="AXIOM Demo API",
    version="0.1.7-demo",
    description="React demo API for the AXIOM proof-of-action tunnel. Enterprise sources are simulated; the AXIOM decision path is real.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "axiom-demo-api"}


@app.get("/v1/demo/scenarios", response_model=list[ScenarioSummary])
def list_scenarios() -> list[ScenarioSummary]:
    return _scenario_summaries()


@app.post("/v1/demo/evaluate", response_model=DemoEvaluateResponse)
def evaluate_demo(request: DemoEvaluateRequest) -> DemoEvaluateResponse:
    scenario = _summary_by_id(request.scenario_id)
    action_request = copy.deepcopy(BASE_ACTION_REQUEST)
    sources = _sources_for_scenario(request.scenario_id)

    try:
        result = evaluate_action_request(
            action_request=action_request,
            sources=sources,
            policy=copy.deepcopy(BASE_POLICY),
            ledger_path="data/demo_ui_ledger.jsonl" if request.write_ledger else None,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    warrant = result["warrant"]
    verified = result["verified_evidence"]
    proof_vector = result["proof_vector"]
    decision = str(warrant.get("decision", "UNKNOWN"))
    ledger_preview = {
        "ledger_action": "APPEND",
        "warrant_id": warrant.get("warrant_id"),
        "decision": decision,
        "warrant_hash": sha256_hex(warrant),
        "audit_note": "In a production deployment this record is appended to the configured Proof Ledger.",
    }

    return DemoEvaluateResponse(
        scenario=scenario,
        raw_agent_context=_raw_context_for_scenario(request.scenario_id),
        action_request=action_request,
        simulated_sources=sources,
        policy_yaml=yaml.safe_dump(BASE_POLICY, sort_keys=False, allow_unicode=True),
        pipeline=_status_for_step(decision, verified, proof_vector),
        verified_evidence=verified,
        proof_vector=proof_vector,
        warrant=warrant,
        ledger_preview=ledger_preview,
    )


# ---------------------------------------------------------------------------
# Custom Data Injection Demo
# ---------------------------------------------------------------------------

class DemoCustomEvaluateRequest(BaseModel):
    """Custom demo payload supplied by the frontend.

    Enterprise systems are represented by source dictionaries.
    The AXIOM runtime still evaluates the request through schemas,
    source verifiers, policy kernel, warrant and ledger preview.
    """

    title: str = Field(default="CUSTOM — user-provided enterprise context")
    description: str = Field(default="User injected a custom ActionRequest, sources and optional policy.")
    raw_agent_context: list[str] = Field(default_factory=list)
    action_request: dict[str, Any]
    sources: dict[str, Any]
    policy: dict[str, Any] | None = None
    write_ledger: bool = False


def _custom_template_payload() -> dict[str, Any]:
    return {
        "title": "CUSTOM — production action from my enterprise context",
        "description": "Paste or modify this payload to test your own action, claims, source responses and policy.",
        "raw_agent_context": [
            "agent_ops_custom proposes: deploy payment-api to production now.",
            "The agent claims: change ticket CHG-1001 is approved.",
            "The agent claims: GitHub PR #42 is approved with required checks.",
            "The agent claims: CI, security scan, rollback and deployment window are valid."
        ],
        "action_request": copy.deepcopy(BASE_ACTION_REQUEST),
        "sources": copy.deepcopy(BASE_SOURCES),
        "policy": copy.deepcopy(BASE_POLICY),
        "write_ledger": False
    }


@app.get("/v1/demo/custom-template")
def custom_template() -> dict[str, Any]:
    """Return a complete editable payload for the Custom Data panel."""
    return _custom_template_payload()


@app.post("/v1/demo/evaluate-custom", response_model=DemoEvaluateResponse)
def evaluate_custom_demo(request: DemoCustomEvaluateRequest) -> DemoEvaluateResponse:
    """Evaluate a user-provided ActionRequest and source bundle."""

    policy = request.policy if request.policy is not None else copy.deepcopy(BASE_POLICY)

    try:
        result = evaluate_action_request(
            action_request=request.action_request,
            sources=request.sources,
            policy=policy,
            ledger_path="data/demo_ui_custom_ledger.jsonl" if request.write_ledger else None,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    warrant = result["warrant"]
    verified = result["verified_evidence"]
    proof_vector = result["proof_vector"]
    decision = str(warrant.get("decision", "UNKNOWN"))

    ledger_preview = {
        "ledger_action": "APPEND",
        "warrant_id": warrant.get("warrant_id"),
        "decision": decision,
        "warrant_hash": sha256_hex(warrant),
        "audit_note": "Custom demo payload evaluated through the real AXIOM runtime. In production this record is appended to the configured Proof Ledger."
    }

    scenario = ScenarioSummary(
        id="custom_user_payload",
        title=request.title,
        expected_decision=decision,
        severity="success" if decision == "ALLOW" else "danger" if decision == "BLOCK" else "warning",
        description=request.description,
    )

    return DemoEvaluateResponse(
        scenario=scenario,
        raw_agent_context=request.raw_agent_context or [request.description],
        action_request=request.action_request,
        simulated_sources=request.sources,
        policy_yaml=yaml.safe_dump(policy, sort_keys=False, allow_unicode=True),
        pipeline=_status_for_step(decision, verified, proof_vector),
        verified_evidence=verified,
        proof_vector=proof_vector,
        warrant=warrant,
        ledger_preview=ledger_preview,
    )


# ---------------------------------------------------------------------------
# Custom Data Injection Demo
# ---------------------------------------------------------------------------

class DemoCustomEvaluateRequest(BaseModel):
    """Custom demo payload supplied by the frontend.

    Enterprise systems are represented by source dictionaries.
    The AXIOM runtime still evaluates the request through schemas,
    source verifiers, policy kernel, warrant and ledger preview.
    """

    title: str = Field(default="CUSTOM — user-provided enterprise context")
    description: str = Field(default="User injected a custom ActionRequest, sources and optional policy.")
    raw_agent_context: list[str] = Field(default_factory=list)
    action_request: dict[str, Any]
    sources: dict[str, Any]
    policy: dict[str, Any] | None = None
    write_ledger: bool = False


def _custom_template_payload() -> dict[str, Any]:
    return {
        "title": "CUSTOM — production action from my enterprise context",
        "description": "Paste or modify this payload to test your own action, claims, source responses and policy.",
        "raw_agent_context": [
            "agent_ops_custom proposes: deploy payment-api to production now.",
            "The agent claims: change ticket CHG-1001 is approved.",
            "The agent claims: GitHub PR #42 is approved with required checks.",
            "The agent claims: CI, security scan, rollback and deployment window are valid."
        ],
        "action_request": copy.deepcopy(BASE_ACTION_REQUEST),
        "sources": copy.deepcopy(BASE_SOURCES),
        "policy": copy.deepcopy(BASE_POLICY),
        "write_ledger": False
    }


@app.get("/v1/demo/custom-template")
def custom_template() -> dict[str, Any]:
    """Return a complete editable payload for the Custom Data panel."""
    return _custom_template_payload()


@app.post("/v1/demo/evaluate-custom", response_model=DemoEvaluateResponse)
def evaluate_custom_demo(request: DemoCustomEvaluateRequest) -> DemoEvaluateResponse:
    """Evaluate a user-provided ActionRequest and source bundle."""

    policy = request.policy if request.policy is not None else copy.deepcopy(BASE_POLICY)

    try:
        result = evaluate_action_request(
            action_request=request.action_request,
            sources=request.sources,
            policy=policy,
            ledger_path="data/demo_ui_custom_ledger.jsonl" if request.write_ledger else None,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    warrant = result["warrant"]
    verified = result["verified_evidence"]
    proof_vector = result["proof_vector"]
    decision = str(warrant.get("decision", "UNKNOWN"))

    ledger_preview = {
        "ledger_action": "APPEND",
        "warrant_id": warrant.get("warrant_id"),
        "decision": decision,
        "warrant_hash": sha256_hex(warrant),
        "audit_note": "Custom demo payload evaluated through the real AXIOM runtime. In production this record is appended to the configured Proof Ledger."
    }

    scenario = ScenarioSummary(
        id="custom_user_payload",
        title=request.title,
        expected_decision=decision,
        severity="success" if decision == "ALLOW" else "danger" if decision == "BLOCK" else "warning",
        description=request.description,
    )

    return DemoEvaluateResponse(
        scenario=scenario,
        raw_agent_context=request.raw_agent_context or [request.description],
        action_request=request.action_request,
        simulated_sources=request.sources,
        policy_yaml=yaml.safe_dump(policy, sort_keys=False, allow_unicode=True),
        pipeline=_status_for_step(decision, verified, proof_vector),
        verified_evidence=verified,
        proof_vector=proof_vector,
        warrant=warrant,
        ledger_preview=ledger_preview,
    )


# ---------------------------------------------------------------------------
# SDK-oriented runtime routes
# ---------------------------------------------------------------------------
from axiom.sdk.api_routes import router as sdk_runtime_router

app.include_router(sdk_runtime_router)
