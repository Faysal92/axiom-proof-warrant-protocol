from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .evaluator import evaluate
from .evidence.adapters.external_api import payload_to_events, payload_to_proof_vector
from .ledger import append_ledger_entry
from .source_verification import evaluate_action_request


app = FastAPI(
    title="AXIOM Control Plane API",
    version="0.1.6",
    description="Minimal HTTP API for evaluating critical actions, canonical evidence events, and issuing AXIOM Execution Warrants.",
)


class EvaluateRequest(BaseModel):
    action: dict[str, Any]
    proof_vector: dict[str, Any]
    policy: dict[str, Any] | None = None
    policy_yaml: str | None = None
    write_ledger: bool = False
    ledger_path: str = "data/api_ledger.jsonl"


class EvidenceConvertRequest(BaseModel):
    evidence: dict[str, Any] | list[dict[str, Any]]


class EvidenceEvaluateRequest(BaseModel):
    action: dict[str, Any]
    evidence: dict[str, Any] | list[dict[str, Any]]
    policy: dict[str, Any] | None = None
    policy_yaml: str | None = None
    write_ledger: bool = False
    ledger_path: str = "data/api_ledger.jsonl"


class SourceVerifyEvaluateRequest(BaseModel):
    action_request: dict[str, Any]
    sources: dict[str, Any]
    policy: dict[str, Any] | None = None
    policy_yaml: str | None = None
    write_ledger: bool = False
    ledger_path: str = "data/api_source_verified_ledger.jsonl"


class SourceVerifyEvaluateResponse(BaseModel):
    verified_evidence: list[dict[str, Any]]
    proof_vector: dict[str, Any]
    warrant: dict[str, Any]
    ledger_entry: dict[str, Any] | None = None


class EvaluateResponse(BaseModel):
    warrant: dict[str, Any]
    ledger_entry: dict[str, Any] | None = None


class EvidenceConvertResponse(BaseModel):
    proof_vector: dict[str, Any]
    events_count: int


class EvidenceEvaluateResponse(BaseModel):
    proof_vector: dict[str, Any]
    warrant: dict[str, Any]
    ledger_entry: dict[str, Any] | None = None


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "axiom-control-plane"}


def _resolve_policy(policy: dict[str, Any] | None, policy_yaml: str | None) -> dict[str, Any]:
    if policy is None and policy_yaml is None:
        raise HTTPException(status_code=400, detail="Either policy or policy_yaml is required.")
    return policy if policy is not None else yaml.safe_load(policy_yaml or "")


@app.post("/v1/actions/evaluate", response_model=SourceVerifyEvaluateResponse)
def evaluate_action_with_source_verification(request: SourceVerifyEvaluateRequest) -> SourceVerifyEvaluateResponse:
    """Product-facing endpoint: verify claims at source before issuing a warrant."""
    try:
        policy = _resolve_policy(request.policy, request.policy_yaml)
        result = evaluate_action_request(
            action_request=request.action_request,
            sources=request.sources,
            policy=policy,
            ledger_path=request.ledger_path if request.write_ledger else None,
        )
        ledger_entry = None
        if request.write_ledger:
            # evaluate_action_request already appended to the ledger; the API keeps
            # the response lightweight and does not reread the ledger.
            ledger_entry = {"ledger_path": request.ledger_path}
        return SourceVerifyEvaluateResponse(
            verified_evidence=result["verified_evidence"],
            proof_vector=result["proof_vector"],
            warrant=result["warrant"],
            ledger_entry=ledger_entry,
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/v1/warrants/evaluate", response_model=EvaluateResponse)
def evaluate_warrant(request: EvaluateRequest) -> EvaluateResponse:
    try:
        policy = _resolve_policy(request.policy, request.policy_yaml)
        warrant = evaluate(action=request.action, proof_vector=request.proof_vector, policy=policy)
        ledger_entry = None

        if request.write_ledger:
            ledger_entry = append_ledger_entry(Path(request.ledger_path), warrant)

        return EvaluateResponse(warrant=warrant, ledger_entry=ledger_entry)

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/v1/evidence/convert", response_model=EvidenceConvertResponse)
def convert_evidence(request: EvidenceConvertRequest) -> EvidenceConvertResponse:
    try:
        events = payload_to_events(request.evidence)
        proof_vector = payload_to_proof_vector(request.evidence)
        return EvidenceConvertResponse(proof_vector=proof_vector, events_count=len(events))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/v1/warrants/evaluate-from-evidence", response_model=EvidenceEvaluateResponse)
def evaluate_from_evidence(request: EvidenceEvaluateRequest) -> EvidenceEvaluateResponse:
    try:
        policy = _resolve_policy(request.policy, request.policy_yaml)
        proof_vector = payload_to_proof_vector(request.evidence)
        warrant = evaluate(action=request.action, proof_vector=proof_vector, policy=policy)
        ledger_entry = None

        if request.write_ledger:
            ledger_entry = append_ledger_entry(Path(request.ledger_path), warrant)

        return EvidenceEvaluateResponse(
            proof_vector=proof_vector,
            warrant=warrant,
            ledger_entry=ledger_entry,
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
