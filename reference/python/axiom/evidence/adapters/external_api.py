from __future__ import annotations

from typing import Any

from axiom.evidence.canonical import CanonicalEvidenceEvent, canonical_events_to_proof_vector


def payload_to_events(payload: dict[str, Any] | list[dict[str, Any]]) -> list[CanonicalEvidenceEvent]:
    """Normalize an external API/webhook payload into canonical evidence events.

    Accepted payload shapes:
    - a single CanonicalEvidenceEvent object
    - a list of CanonicalEvidenceEvent objects
    - {"events": [ ... ]}
    """
    if isinstance(payload, dict) and "events" in payload:
        items = payload["events"]
    elif isinstance(payload, list):
        items = payload
    elif isinstance(payload, dict):
        items = [payload]
    else:
        raise ValueError("External evidence payload must be an object, list, or object with events.")

    if not isinstance(items, list):
        raise ValueError("events must be a list.")

    return [CanonicalEvidenceEvent.model_validate(item) for item in items]


def payload_to_proof_vector(payload: dict[str, Any] | list[dict[str, Any]]) -> dict[str, Any]:
    return canonical_events_to_proof_vector(payload_to_events(payload))
