from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import Any

from axiom.schemas import Claim, SourceBundle, VerifiedEvidence


PASSED = "passed"
FAILED = "failed"
MISSING = "missing"
EXPIRED = "expired"
UNKNOWN = "unknown"


class SourceVerifier(ABC):
    """Base class for deterministic source verifiers.

    Verifier law:
    A verifier may only emit VerifiedEvidence for facts it checked at the source.
    It must never convert an agent claim into proof without source validation.
    """

    provider: str = "unknown"
    source_kind: str = "unknown"
    supported_claim_types: set[str] = set()

    def can_handle(self, claim: Claim) -> bool:
        return claim.type in self.supported_claim_types

    @abstractmethod
    def verify(self, claim: Claim, sources: SourceBundle, *, action_scope: dict[str, Any]) -> VerifiedEvidence:
        raise NotImplementedError

    def result(
        self,
        claim: Claim,
        *,
        status: str,
        ref: str | None = None,
        reason: str,
        details: dict[str, Any] | None = None,
    ) -> VerifiedEvidence:
        checked_at = int(time.time())
        evidence_ref = f"{self.provider}:{self.source_kind}:{ref or claim.ref}"
        return VerifiedEvidence(
            claim_id=claim.claim_id,
            claim_type=claim.type,
            dimension=claim.dimension,
            status=status,  # type: ignore[arg-type]
            source_provider=self.provider,
            source_kind=self.source_kind,
            ref=ref or claim.ref,
            checked_at=checked_at,
            evidence_ref=evidence_ref,
            reason=reason,
            details=details or {},
        )


def find_by_id(items: list[dict[str, Any]], key: str, value: str) -> dict[str, Any] | None:
    for item in items or []:
        if str(item.get(key)) == str(value):
            return item
    return None


def is_fresh(epoch: int | None, max_age_hours: int | None, *, now: int | None = None) -> bool:
    if epoch is None or max_age_hours is None:
        return True
    now_epoch = int(now if now is not None else time.time())
    return (now_epoch - int(epoch)) <= int(max_age_hours) * 3600


def scope_matches(*, claim: Claim, item: dict[str, Any], action_scope: dict[str, Any]) -> bool:
    expected_target = claim.target or action_scope.get("target")
    expected_environment = claim.environment or action_scope.get("environment")

    item_target = item.get("target") or item.get("service") or item.get("resource")
    item_environment = item.get("environment")

    if expected_target and item_target and str(item_target) != str(expected_target):
        return False
    if expected_environment and item_environment and str(item_environment) != str(expected_environment):
        return False
    return True
