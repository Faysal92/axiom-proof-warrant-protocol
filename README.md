# AXIOM

**Status:** Draft v0.1.1 / RFC Candidate  
**Category:** Proof-Weighted Authorization / Proof Warrant Protocol  
**Primary Artifact:** Execution Warrant  
**Core Doctrine:** No action beyond proportional proof.

> **AXIOM is a candidate open specification and reference implementation for proof-weighted authorization of critical AI actions.**

```text
Permission is not proof.
Proof must be proportional to consequence.
No action beyond proportional proof.
```

AXIOM is not another IAM system, policy engine, sandbox, SIEM, SOAR, CI/CD tool, LLM guardrail, or runtime-governance product.

AXIOM supplies the missing object those systems should require before critical execution:

> a signed, scoped, time-bound, revocable **Execution Warrant** proving that an action is justified by evidence strong enough for its consequence.

---

## One-Line Summary

```text
AXIOM turns static permission into proof-weighted authorization.
```

Traditional systems ask:

```text
Can this agent act?
```

AXIOM asks:

```text
Has this agent proven enough to act, in this context, right now?
```

---

## Why AXIOM Exists

AI systems no longer only generate text. They now write code, open pull requests, deploy services, modify infrastructure, call APIs, query databases, revoke credentials, change firewall rules, trigger cyber response actions, and operate through autonomous or semi-autonomous agents.

Existing controls usually ask:

```text
Who is acting?
Does this actor have permission?
Does the action satisfy policy?
```

Those questions are necessary, but not sufficient.

An AI agent can be authenticated, authorized, and policy-compliant — and still act on hallucination, weak correlation, stale evidence, prompt injection, incomplete tests, misunderstood context, insufficient scope, missing rollback, or contradictory logs.

AXIOM adds the missing question:

```text
Is the available proof strong enough for the consequence of this action, here and now?
```

---

## AXIOM Doctrine

```text
1. Permission is not proof.
2. Proof must be proportional to consequence.
3. Proof is a vector, not a score.
4. No critical action without an Execution Warrant.
5. No evidence without provenance.
6. No warrant beyond context.
7. No LLM in the final authorization path.
```

---

## Strategic Thesis

AXIOM has two horizons.

### Immediate Product — Warrant Gate

The immediate product is a proof gate for critical actions.

```text
No proof, no critical execution.
```

The customer buys risk reduction, auditability, compliance evidence, control over AI agents, safe automation, and CI/CD or DevSecOps governance.

### Long-Term Asset — Proof Ledger

The Proof Ledger is the structured memory of every proof decision.

Each warrant decision becomes a proof-labeled decision:

```json
{
  "action": "deploy_production",
  "provided_proof": ["unit_tests_passed"],
  "required_proof": ["integration_tests", "security_scan", "rollback_plan"],
  "decision": "SUSPEND",
  "reason": "proof_not_proportional_to_consequence"
}
```

### Expansion — RLPF

RLPF means **Reinforcement Learning from Proof Feedback**.

```text
The Warrant is the product.
The Proof Ledger is the moat.
RLPF is the expansion.
```

Scale AI industrialized labeled data for model perception.

AXIOM industrializes proof-labeled decisions for agent autonomy.

Short version:

```text
Scale AI labels what models should recognize.
AXIOM labels what agents are justified to do.
```

---

## What Changed in v0.1.1

This build integrates the feedback from the first review cycle:

- stricter Pydantic runtime models;
- separation between `PolicyEngine` and `Evaluator`;
- explicit `Challenge Response` for missing evidence;
- distinction between **missing proof** and **failed proof**;
- numeric `risk_bound` check using `action_weight.final_weight` and `risk_policy.max_risk_score`;
- hash-chained JSONL ledger;
- HMAC-signed warrants for v0.1.1;
- clear examples for `ALLOW`, `SUSPEND`, `BLOCK`, and `REQUIRE_HUMAN_REVIEW`.

HMAC is sufficient for the local reference implementation. A future v0.2 should support JWS / Ed25519 / RSA signatures.

---

## Core Artifacts

AXIOM defines these core artifacts:

| Artifact | Role |
|---|---|
| `Action` | Proposed operation |
| `ActionWeight` | Consequence weight of the operation |
| `ProofVector` | What the available evidence supports |
| `RequirementVector` | What proof the action requires |
| `ExecutionWarrant` | Signed decision artifact |
| `ProofLedger` | Append-only memory of warrant decisions |
| `ChallengeResponse` | Machine-readable description of what proof is missing |

---

## Proof Levels

| Level | Name | Meaning |
|---|---|---|
| P0 | Unsupported | Model assertion only; no external evidence |
| P1 | Plausible | Coherent hypothesis, but unverified |
| P2 | Source-backed | Static evidence: document, diff, isolated log, single artifact |
| P3 | Cross-checked | Multiple independent sources or empirical corroboration |
| P4 | Executed | Verified through test, benchmark, query, simulation, or formal check under assumptions |
| P5 | Audited | Executed and reviewed by human, trusted authority, formal process, or third party |

Important:

```text
P4 is not universal.
Executed proof is only valid within its assumptions, scope, and test conditions.
```

---

## Deterministic Kernel

AXIOM does not authorize by scalar confidence.

It authorizes through deterministic constraints:

```text
Allowed(action) ⇔

ProofVector ⊒ RequirementVector

AND Scope(action) ⊆ Scope(ProofLicense)

AND Time(action) ⊆ ValidityWindow(ProofLicense)

AND Risk(action, context) ≤ PolicyRiskBound(action, context)

AND Contradictions(evidence) = ∅

AND Limitations(proof) ∩ CriticalRequirements(action) = ∅

AND Signature(warrant) is valid

AND Warrant is not expired

AND Warrant is not revoked
```

An LLM may assist in summarization, extraction, or missing-evidence suggestions.

An LLM must not be the final authorization authority.

---

## Decisions

| Decision | Meaning |
|---|---|
| ALLOW | Proof covers requirements and warrant is issued |
| CONDITIONAL | Execution allowed only under explicit constraints |
| SUSPEND | Missing proof can potentially be supplied |
| REQUIRE_HUMAN_REVIEW | Automated proof is insufficient for action weight |
| BLOCK | Contradiction, failed required proof, hard risk limit, invalid proof, or forged evidence |

The UX is not simply:

```text
No.
```

It is:

```text
Not yet. Here is the proof gap.
```

---

## Quick Start

```bash
cd axiom-proof-warrant-protocol-v0.1.1
pip install -r requirements.txt

PYTHONPATH=reference/python python -m axiom.cli eval \
  --action examples/deploy_payment_api.action.json \
  --proof examples/deploy_payment_api.missing_proof_vector.json \
  --policy examples/production_policy.yml \
  --out examples/output.suspend.warrant.json
```

Expected result:

```text
Decision: SUSPEND
```

Run an allowed case:

```bash
PYTHONPATH=reference/python python -m axiom.cli eval \
  --action examples/deploy_payment_api.action.json \
  --proof examples/deploy_payment_api.good_proof_vector.json \
  --policy examples/production_policy.yml \
  --out examples/output.allow.warrant.json
```

Expected result:

```text
Decision: ALLOW
```

Run a blocked case:

```bash
PYTHONPATH=reference/python python -m axiom.cli eval \
  --action examples/deploy_payment_api.action.json \
  --proof examples/deploy_payment_api.failed_security_scan.proof_vector.json \
  --policy examples/production_policy.yml \
  --out examples/output.block.warrant.json
```

Expected result:

```text
Decision: BLOCK
```

---

## Repository Structure

```text
axiom-proof-warrant-protocol-v0.1.1/
  README.md
  RFC-0001-Proof-Warrant.md
  CHANGELOG.md
  LICENSE
  ADOPTERS.md
  pyproject.toml
  requirements.txt

  schemas/
    proof_vector.schema.json
    requirement_vector.schema.json
    execution_warrant.schema.json
    ledger_entry.schema.json

  examples/
    deploy_payment_api.action.json
    deploy_payment_api.missing_proof_vector.json
    deploy_payment_api.failed_security_scan.proof_vector.json
    deploy_payment_api.good_proof_vector.json
    deploy_payment_api.human_review_missing.proof_vector.json
    production_policy.yml
    strict_risk_policy.yml

  reference/python/axiom/
    cli.py
    models.py
    policy_engine.py
    evaluator.py
    warrant.py
    crypto.py
    ledger.py
    enums.py

  tests/conformance/
    test_policy_engine.py
```

---

## Security Boundaries

AXIOM can guarantee only what is routed through its enforcement points.

AXIOM does not guarantee absolute truth, perfect security, interception of non-instrumented paths, absence of human error, honesty of all external systems, correctness of all evidence sources, quality of the base model, or impossibility of attack.

Precise claim:

```text
AXIOM does not make attacks impossible.
AXIOM makes unjustified critical actions impossible to authorize properly when execution is warrant-gated.
```

---

## Final Manifesto

AXIOM does not control by trust.

AXIOM controls by proof.

It does not ask whether an AI sounds confident.

It asks what the evidence allows the AI to claim.

It does not ask whether an actor has permission alone.

It asks whether the action is justified, scoped, reversible, risk-bounded, and auditable.

```text
No certainty beyond evidence.
No action beyond proof.
No warrant beyond context.
No action beyond proportional proof.
```

AXIOM turns static permission into proof-weighted authorization.

AXIOM is the proof-warrant protocol for critical AI actions.
