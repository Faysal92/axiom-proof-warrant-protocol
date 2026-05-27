# AXIOM v0.1.6 — Source Verifiers MVP

AXIOM v0.1.6 locks the product foundation around source-verified proof.

## Product doctrine

```text
AXIOM does not trust the agent.
AXIOM verifies at the source, governs by policy, signs the warrant, and records the decision.
```

## New architecture

```text
Raw Enterprise Context
        ↓
Normalizer
        ↓
Pydantic Schemas
        ↓
Source Verifiers
        ↓
Policy Kernel
        ↓
Execution Warrant
        ↓
Proof Ledger
```

## New code

- `reference/python/axiom/schemas.py`
- `reference/python/axiom/source_verification.py`
- `reference/python/axiom/verifiers/base.py`
- `reference/python/axiom/verifiers/jira.py`
- `reference/python/axiom/verifiers/github.py`
- `reference/python/axiom/verifiers/cicd.py`
- `reference/python/axiom/verifiers/rollback.py`
- `reference/python/axiom/verifiers/deployment_window.py`

## New CLI

```bash
python -m axiom.cli verify-action \
  --action-request examples/devops/deploy_to_production.action_request.json \
  --sources examples/devops/sources_allow.json \
  --policy examples/devops/devops_prod_policy.yml \
  --out examples/devops/output.allow.warrant.json \
  --proof-out examples/devops/output.allow.proof_vector.json \
  --verified-out examples/devops/output.allow.verified_evidence.json
```

## New API

```text
POST /v1/actions/evaluate
```

This endpoint verifies action claims at source, builds a ProofVector, applies policy, and returns an Execution Warrant.

## New examples

- `examples/devops/deploy_to_production.action_request.json`
- `examples/devops/devops_prod_policy.yml`
- `examples/devops/sources_allow.json`
- `examples/devops/sources_missing_rollback.json`
- `examples/devops/sources_failed_security.json`
- `examples/devops/sources_unapproved_ticket.json`

## New tests

- Unit tests for Source Verifiers
- Integration tests for source-verified ALLOW / SUSPEND / BLOCK flows
- Conformance tests for CLI and API

## Verification

```text
60 passed
```

## Non-negotiable rule

```text
Pydantic structures. AXIOM verifies.
```
