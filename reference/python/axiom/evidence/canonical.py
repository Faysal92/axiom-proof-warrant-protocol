from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from axiom.proof_router import merge_proof_vectors


def source_block(
    *,
    provider: str,
    kind: str,
    ref: str,
    collected_at: int | None = None,
) -> dict[str, Any]:
    """Build a canonical source block for provider-specific evidence adapters."""
    return {
        "provider": provider,
        "kind": kind,
        "ref": ref,
        "collected_at": int(collected_at if collected_at is not None else time.time()),
    }


def partial_proof_vector(
    *,
    source: dict[str, Any],
    claims: dict[str, Any],
    evidence_refs: list[str],
    scope: dict[str, Any] | None = None,
    limitations: list[dict[str, Any]] | None = None,
    contradictions: list[dict[str, Any]] | None = None,
    proof_level: str = "P4_EXECUTED",
    source_trust: str = "high",
    freshness_epoch: int | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a canonical PartialProofVector.

    Provider-specific adapters should use this when they translate external
    systems such as GitHub, GitLab, Jenkins, Semgrep, SIEM, EDR, or manual
    approvals into AXIOM proof.

    Adapter law:
    an adapter may only emit claims it can prove from its own source.
    """
    collected_at = int(source.get("collected_at") or int(time.time()))
    vector: dict[str, Any] = {
        "source": source,
        "meta": {
            "proof_level": proof_level,
            "source_trust": source_trust,
            "freshness_epoch": int(freshness_epoch if freshness_epoch is not None else collected_at),
            "reproducibility": "reproducible",
            "independence": "single_source",
        },
        "scope": scope or {},
        "dimensions": claims,
        "limitations": limitations or [],
        "contradictions": contradictions or [],
        "evidence_refs": evidence_refs,
    }
    if extra:
        vector.update(extra)
    return vector


class AXIOMEvidenceModel(BaseModel):
    model_config = ConfigDict(extra="allow")


class EvidenceSource(AXIOMEvidenceModel):
    provider: str = "unknown"
    kind: str = "unknown"
    name: str | None = None
    trust_level: str = "medium"
    collected_at: int | None = None


class EvidenceSubject(AXIOMEvidenceModel):
    action_id: str | None = None
    target: str = "unknown-target"
    environment: str = "unknown"
    commit: str | None = None
    branch: str | None = None
    service: str | None = None


class CanonicalEvidenceEvent(AXIOMEvidenceModel):
    """Provider-agnostic evidence event.

    This is the canonical input layer for AXIOM.

    GitHub, GitLab, local JSON files, external APIs, SIEMs, scanners, business
    systems, and sensors should all be normalized into this structure before the
    AXIOM kernel evaluates anything.

    Proof hygiene rule:
    an evidence event may only claim what its source actually observed.
    """

    event_id: str
    source: EvidenceSource
    subject: EvidenceSubject = Field(default_factory=EvidenceSubject)
    claims: dict[str, Any] = Field(default_factory=dict)
    evidence_refs: list[str] = Field(default_factory=list)
    limitations: list[dict[str, Any]] = Field(default_factory=list)
    contradictions: list[dict[str, Any]] = Field(default_factory=list)
    meta: dict[str, Any] = Field(default_factory=dict)


def _status_from_value(value: Any) -> str:
    if value is True:
        return "passed"
    if value is False:
        return "failed"
    if value is None:
        return "missing"
    if isinstance(value, str):
        lowered = value.lower()
        if lowered in {"passed", "pass", "success", "ok", "true", "clean", "approved"}:
            return "passed"
        if lowered in {"failed", "fail", "error", "false", "dirty", "rejected"}:
            return "failed"
        if lowered in {"missing", "not_run", "not_available", "unknown"}:
            return lowered
    return "unknown"


def _dimension_from_claim(name: str, value: Any, event: CanonicalEvidenceEvent) -> dict[str, Any]:
    base = {
        "source_provider": event.source.provider,
        "source_kind": event.source.kind,
        "source_name": event.source.name,
        "event_id": event.event_id,
    }

    if isinstance(value, dict):
        result = dict(value)
        result.setdefault("status", _status_from_value(result.get("status", result.get("value"))))
        result.update({k: v for k, v in base.items() if k not in result})
        return result

    return {
        "status": _status_from_value(value),
        "value": value,
        **base,
    }


def _scope_from_subject(subject: EvidenceSubject) -> dict[str, Any]:
    scope = {
        "target": subject.target,
        "environment": subject.environment,
    }
    if subject.commit is not None:
        scope["commit"] = subject.commit
    if subject.branch is not None:
        scope["branch"] = subject.branch
    if subject.service is not None:
        scope["service"] = subject.service
    if subject.action_id is not None:
        scope["action_id"] = subject.action_id
    return scope


def canonical_event_to_partial_proof_vector(event: CanonicalEvidenceEvent | dict[str, Any]) -> dict[str, Any]:
    ev = event if isinstance(event, CanonicalEvidenceEvent) else CanonicalEvidenceEvent.model_validate(event)

    freshness = ev.source.collected_at or ev.meta.get("freshness_epoch") or int(time.time())
    proof_level = ev.meta.get("proof_level", "P4_EXECUTED")
    source_trust = ev.source.trust_level or ev.meta.get("source_trust", "medium")

    evidence_refs = list(ev.evidence_refs)
    if ev.event_id not in evidence_refs:
        evidence_refs.append(ev.event_id)

    return {
        "meta": {
            "proof_level": proof_level,
            "source_trust": source_trust,
            "freshness_epoch": int(freshness),
            "reproducibility": ev.meta.get("reproducibility", "source_dependent"),
            "independence": ev.meta.get("independence", "single_source"),
        },
        "scope": _scope_from_subject(ev.subject),
        "dimensions": {
            name: _dimension_from_claim(name, value, ev)
            for name, value in ev.claims.items()
        },
        "limitations": list(ev.limitations),
        "contradictions": list(ev.contradictions),
        "evidence_refs": evidence_refs,
        "canonical_evidence": {
            "event_id": ev.event_id,
            "provider": ev.source.provider,
            "kind": ev.source.kind,
            "name": ev.source.name,
            "trust_level": ev.source.trust_level,
        },
    }


def canonical_events_to_proof_vector(events: list[CanonicalEvidenceEvent | dict[str, Any]]) -> dict[str, Any]:
    partials = [canonical_event_to_partial_proof_vector(event) for event in events]
    if not partials:
        raise ValueError("At least one canonical evidence event is required.")
    return merge_proof_vectors(*partials)


def _parse_json_or_jsonl(path: Path) -> Any:
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        raise ValueError(f"Evidence file is empty: {path}")

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        events = []
        for lineno, line in enumerate(text.splitlines(), start=1):
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSONL at {path}:{lineno}: {exc}") from exc
        return events


def load_canonical_evidence(path: str | Path) -> list[CanonicalEvidenceEvent]:
    raw = _parse_json_or_jsonl(Path(path))

    if isinstance(raw, dict) and "events" in raw:
        items = raw["events"]
    elif isinstance(raw, list):
        items = raw
    elif isinstance(raw, dict):
        items = [raw]
    else:
        raise ValueError("Canonical evidence must be an object, a list, or an object with an events array.")

    if not isinstance(items, list):
        raise ValueError("events must be a list.")

    return [CanonicalEvidenceEvent.model_validate(item) for item in items]


def write_proof_vector(proof_vector: dict[str, Any], out_path: str | Path) -> None:
    path = Path(out_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(proof_vector, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
