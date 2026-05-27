from __future__ import annotations

from copy import deepcopy
from typing import Any

from .enums import PROOF_LEVEL_ORDER


def _level_value(level: str | None) -> int:
    return PROOF_LEVEL_ORDER.get(level or "P0_UNSUPPORTED", 0)


def _weakest_proof_level(levels: list[str]) -> str:
    if not levels:
        return "P0_UNSUPPORTED"
    return min(levels, key=_level_value)


def _merge_unique(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def _dimension_status(value: Any) -> str:
    """Return a normalized status for a proof dimension.

    The Proof Router must detect conflicting claims emitted by independent
    adapters. Two adapters may both emit `security_scan_clean`; if one says
    `passed` and the other says `failed`, the router must not let the last
    writer silently win.
    """
    if value is True:
        return "passed"
    if value is False:
        return "failed"
    if value is None:
        return "missing"

    if isinstance(value, dict):
        raw = value.get("status", value.get("value", value.get("result")))
    else:
        raw = value

    status = str(raw).lower()
    if status in {"passed", "pass", "success", "ok", "true", "clean", "approved"}:
        return "passed"
    if status in {"failed", "fail", "error", "false", "dirty", "rejected"}:
        return "failed"
    if status in {"missing", "not_run", "not_available", "unknown"}:
        return status
    return "unknown"


def _dimension_conflict(dimension: str, existing: Any, incoming: Any) -> bool:
    """True when two evidence sources assert incompatible states.

    We intentionally compare normalized states, not the full dictionaries,
    because two providers can attach different metadata to the same compatible
    claim. Metadata differences are not proof conflicts. Status differences are.
    """
    return _dimension_status(existing) != _dimension_status(incoming)


def _source_ref(vector: dict[str, Any]) -> dict[str, Any]:
    source = vector.get("source") or {}
    return {
        "provider": source.get("provider"),
        "kind": source.get("kind"),
        "ref": source.get("ref"),
        "evidence_refs": vector.get("evidence_refs", []),
    }


def _dimension_conflict_contradiction(
    *,
    dimension: str,
    existing_value: Any,
    incoming_value: Any,
    existing_source: dict[str, Any] | None,
    incoming_source: dict[str, Any],
) -> dict[str, Any]:
    return {
        "type": "dimension_conflict",
        "severity": "critical",
        "dimension": dimension,
        "summary": f"Conflicting evidence for dimension '{dimension}'.",
        "existing_status": _dimension_status(existing_value),
        "incoming_status": _dimension_status(incoming_value),
        "existing_source": existing_source or {},
        "incoming_source": incoming_source,
    }


def merge_proof_vectors(*proof_vectors: dict[str, Any]) -> dict[str, Any]:
    """Merge partial ProofVectors into a consolidated ProofVector.

    Each connector should only emit the evidence it actually owns.
    The Proof Router consolidates those partial vectors before the AXIOM kernel evaluates them.

    Security property:
    if two independent sources emit the same dimension with incompatible states,
    the router records a contradiction instead of silently allowing the last
    source to overwrite the first one.
    """

    vectors = [deepcopy(v) for v in proof_vectors if v]
    if not vectors:
        raise ValueError("At least one proof vector is required.")

    levels = [v.get("meta", {}).get("proof_level", "P0_UNSUPPORTED") for v in vectors]
    freshness_values = [
        int(v.get("meta", {}).get("freshness_epoch"))
        for v in vectors
        if v.get("meta", {}).get("freshness_epoch") is not None
    ]

    merged: dict[str, Any] = {
        "meta": {
            "proof_level": _weakest_proof_level(levels),
            "source_trust": "mixed" if len(vectors) > 1 else vectors[0].get("meta", {}).get("source_trust"),
            "freshness_epoch": min(freshness_values) if freshness_values else None,
            "reproducibility": "mixed" if len(vectors) > 1 else vectors[0].get("meta", {}).get("reproducibility"),
            "independence": "multiple_sources" if len(vectors) > 1 else vectors[0].get("meta", {}).get("independence"),
        },
        "scope": {},
        "dimensions": {},
        "limitations": [],
        "contradictions": [],
        "evidence_refs": [],
    }

    security_evidence: list[dict[str, Any]] = []
    dimension_sources: dict[str, dict[str, Any]] = {}

    for vector in vectors:
        for key, value in (vector.get("scope") or {}).items():
            if key not in merged["scope"]:
                merged["scope"][key] = value
            elif merged["scope"][key] != value:
                merged["limitations"].append(
                    {
                        "type": "scope_conflict",
                        "domain": key,
                        "severity": "high",
                        "expected": merged["scope"][key],
                        "actual": value,
                    }
                )

        incoming_source = _source_ref(vector)
        for dimension, incoming_value in (vector.get("dimensions") or {}).items():
            if dimension not in merged["dimensions"]:
                merged["dimensions"][dimension] = incoming_value
                dimension_sources[dimension] = incoming_source
                continue

            existing_value = merged["dimensions"][dimension]
            if _dimension_conflict(dimension, existing_value, incoming_value):
                merged["contradictions"].append(
                    _dimension_conflict_contradiction(
                        dimension=dimension,
                        existing_value=existing_value,
                        incoming_value=incoming_value,
                        existing_source=dimension_sources.get(dimension),
                        incoming_source=incoming_source,
                    )
                )
                # Keep the original claim to avoid last-writer-wins behavior.
                continue

            # Compatible duplicate claim: keep first value, but evidence refs from
            # both sources are still accumulated below.

        merged["limitations"].extend(vector.get("limitations") or [])
        merged["contradictions"].extend(vector.get("contradictions") or [])
        merged["evidence_refs"].extend(vector.get("evidence_refs") or [])

        if vector.get("security_evidence"):
            security_evidence.append(vector["security_evidence"])

    merged["evidence_refs"] = _merge_unique(merged["evidence_refs"])

    if security_evidence:
        merged["security_evidence"] = security_evidence

    return merged
