# RFC-0001 — AXIOM Proof Warrant Protocol

**Status:** Draft v0.1.1 / RFC Candidate  
**Category:** Proof-Weighted Authorization  
**Primary Artifact:** Execution Warrant

## Abstract

AXIOM defines a proof-warrant protocol for critical AI actions.

Existing identity, permission, policy, sandbox, and runtime-governance systems ask:

```text
May this actor perform this action?
```

AXIOM asks:

```text
Has this actor provided enough contextual proof for the consequence of this action?
```

Core doctrine:

```text
Permission is not proof.
Proof must be proportional to consequence.
No action beyond proportional proof.
```

## Determinism Requirement

LLMs may assist in summarization, extraction, and missing-evidence suggestion.

LLMs must not be the final authorization authority.

The final evaluator must be deterministic, auditable, and reproducible.

## v0.1.1 Reference Rules

The reference implementation checks:

- proof level coverage;
- mandatory evidence dimensions;
- scope match;
- evidence staleness;
- contradictions;
- failed mandatory proof;
- risk bound;
- human-review requirements;
- HMAC signature validity;
- hash-chained ledger integrity.

## Warrant Challenge Response

A `SUSPEND` warrant should not merely deny execution. It should return a structured challenge:

```json
{
  "decision": "SUSPEND",
  "challenge": {
    "resubmit_allowed": true,
    "missing_evidence": ["integration_tests_passed"],
    "next_actions": ["Run integration tests and resubmit the ProofVector"]
  }
}
```

This enables proof-native agents to gather missing evidence and resubmit.
