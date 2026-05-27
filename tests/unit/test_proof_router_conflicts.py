from __future__ import annotations

from axiom.proof_router import merge_proof_vectors


def partial(*, provider: str, dimension: str, status: str, proof_level: str = "P4_EXECUTED", ref: str | None = None) -> dict:
    ref = ref or f"{provider}:ref"
    return {
        "source": {"provider": provider, "kind": "unit_test", "ref": ref},
        "meta": {
            "proof_level": proof_level,
            "source_trust": "high",
            "freshness_epoch": 1779100000,
            "reproducibility": "reproducible",
            "independence": "single_source",
        },
        "scope": {"target": "payment-api", "environment": "production"},
        "dimensions": {dimension: {"status": status, "source_provider": provider}},
        "limitations": [],
        "contradictions": [],
        "evidence_refs": [ref],
    }


def test_router_detects_conflicting_duplicate_dimensions():
    clean = partial(provider="semgrep", dimension="security_scan_clean", status="passed", ref="semgrep:clean")
    failed = partial(provider="snyk", dimension="security_scan_clean", status="failed", ref="snyk:failed")

    merged = merge_proof_vectors(clean, failed)

    assert merged["dimensions"]["security_scan_clean"]["status"] == "passed"
    assert merged["contradictions"]
    contradiction = merged["contradictions"][0]
    assert contradiction["type"] == "dimension_conflict"
    assert contradiction["dimension"] == "security_scan_clean"
    assert contradiction["existing_status"] == "passed"
    assert contradiction["incoming_status"] == "failed"
    assert contradiction["existing_source"]["provider"] == "semgrep"
    assert contradiction["incoming_source"]["provider"] == "snyk"


def test_router_does_not_flag_compatible_duplicate_dimensions():
    semgrep = partial(provider="semgrep", dimension="security_scan_clean", status="passed", ref="semgrep:clean")
    snyk = partial(provider="snyk", dimension="security_scan_clean", status="passed", ref="snyk:clean")

    merged = merge_proof_vectors(semgrep, snyk)

    assert merged["contradictions"] == []
    assert merged["dimensions"]["security_scan_clean"]["status"] == "passed"
    assert merged["evidence_refs"] == ["semgrep:clean", "snyk:clean"]


def test_router_uses_weakest_proof_level_when_merging():
    p2 = partial(provider="doc", dimension="human_reviewed", status="passed", proof_level="P2_SOURCE_BACKED")
    p4 = partial(provider="ci", dimension="unit_tests_passed", status="passed", proof_level="P4_EXECUTED")

    merged = merge_proof_vectors(p4, p2)

    assert merged["meta"]["proof_level"] == "P2_SOURCE_BACKED"
    assert merged["meta"]["independence"] == "multiple_sources"


def test_router_scope_conflict_becomes_limitation_not_overwrite():
    production = partial(provider="ci", dimension="unit_tests_passed", status="passed")
    staging = partial(provider="review", dimension="human_reviewed", status="passed")
    staging["scope"]["environment"] = "staging"

    merged = merge_proof_vectors(production, staging)

    assert merged["scope"]["environment"] == "production"
    assert any(limitation["type"] == "scope_conflict" for limitation in merged["limitations"])
