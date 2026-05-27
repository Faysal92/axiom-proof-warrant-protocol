from __future__ import annotations

from pathlib import Path
from typing import Any

from axiom.evidence.canonical import (
    CanonicalEvidenceEvent,
    canonical_events_to_proof_vector,
    load_canonical_evidence,
)


def local_json_to_events(path: str | Path) -> list[CanonicalEvidenceEvent]:
    """Load canonical evidence events from local JSON or JSONL."""
    return load_canonical_evidence(path)


def local_json_to_proof_vector(path: str | Path) -> dict[str, Any]:
    """Convert local canonical evidence JSON/JSONL into an AXIOM ProofVector."""
    return canonical_events_to_proof_vector(local_json_to_events(path))
