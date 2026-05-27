# AXIOM v0.1.6 Verification Results

Generated package: `axiom-proof-warrant-protocol-v0.1.6-source-verifiers-product-foundation`

## Test command

```bash
PYTHONPATH=reference/python pytest tests/unit tests/integration tests/conformance -q
```

Observed result:

```text
60 passed
```

## Source-verified CLI demo

ALLOW:

```bash
PYTHONPATH=reference/python python -m axiom.cli verify-action \
  --action-request examples/devops/deploy_to_production.action_request.json \
  --sources examples/devops/sources_allow.json \
  --policy examples/devops/devops_prod_policy.yml \
  --out examples/devops/output.allow.warrant.json \
  --proof-out examples/devops/output.allow.proof_vector.json \
  --verified-out examples/devops/output.allow.verified_evidence.json \
  --ledger data/devops_demo_ledger.jsonl
```

Expected:

```text
Decision: ALLOW
Verified claims: 6
```

SUSPEND:

```bash
PYTHONPATH=reference/python python -m axiom.cli verify-action \
  --action-request examples/devops/deploy_to_production.action_request.json \
  --sources examples/devops/sources_missing_rollback.json \
  --policy examples/devops/devops_prod_policy.yml \
  --out examples/devops/output.suspend.warrant.json
```

Expected:

```text
Decision: SUSPEND
Missing evidence:
- rollback_available
```

BLOCK:

```bash
PYTHONPATH=reference/python python -m axiom.cli verify-action \
  --action-request examples/devops/deploy_to_production.action_request.json \
  --sources examples/devops/sources_failed_security.json \
  --policy examples/devops/devops_prod_policy.yml \
  --out examples/devops/output.block.warrant.json
```

Expected:

```text
Decision: BLOCK
Missing evidence:
- contradiction:security_scan_failure
```

## Product foundation locked

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

Core rule:

```text
Pydantic structures. AXIOM verifies.
```

Enterprise doctrine:

```text
AXIOM does not trust the agent.
AXIOM verifies at the source, governs by policy, signs the warrant, and records the decision.
```
