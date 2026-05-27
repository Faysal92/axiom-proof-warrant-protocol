from __future__ import annotations

import pytest
from pydantic import ValidationError

from axiom.evidence.canonical import CanonicalEvidenceEvent, canonical_event_to_partial_proof_vector


def test_canonical_event_bool_claims_are_normalized_to_statuses():
    event = CanonicalEvidenceEvent.model_validate(
        {
            "event_id": "ev_unit_001",
            "source": {"provider": "risk_api", "kind": "risk_assessment", "collected_at": 1779100000},
            "subject": {"target": "wire_transfer", "environment": "production"},
            "claims": {"fraud_score_below_threshold": False, "beneficiary_verified": True},
            "evidence_refs": ["risk_report:123"],
        }
    )

    proof = canonical_event_to_partial_proof_vector(event)

    assert proof["dimensions"]["fraud_score_below_threshold"]["status"] == "failed"
    assert proof["dimensions"]["beneficiary_verified"]["status"] == "passed"
    assert proof["meta"]["freshness_epoch"] == 1779100000
    assert proof["scope"]["target"] == "wire_transfer"


def test_canonical_event_requires_event_id():
    with pytest.raises(ValidationError):
        CanonicalEvidenceEvent.model_validate(
            {
                "source": {"provider": "risk_api", "kind": "risk_assessment"},
                "claims": {"fraud_score_below_threshold": True},
            }
        )
