# AXIOM

**Status:** Draft v0.1.6 / RFC Candidate  
**Category:** Proof-of-Action Layer / Proof Warrant Protocol  
**Primary Artifact:** Execution Warrant  
**Core Doctrine:** No action beyond proportional proof.  
**Reference Kernel:** Deterministic Python implementation with Source Verifiers MVP  

> **AXIOM is a provider-agnostic Proof-of-Action Layer for critical autonomous actions.**

```text
No proof, no warrant.
No warrant, no critical action.
```

AXIOM exists because AI systems are moving from **answering** to **acting**.

When AI only answers, the main problem is correctness.  
When AI acts, the main problem is justification.

A critical autonomous action should not execute merely because an agent is authenticated, authorized, aligned, sandboxed, or running on trusted infrastructure.

It should execute only when the available proof is proportional to the consequence of the action.

---

## 0. v0.1.6 Product Architecture: Source-Verified Governance

AXIOM v0.1.6 locks the product foundation around one rule:

```text
AXIOM does not trust the agent.
AXIOM verifies at the source, governs by policy, signs the warrant, and records the decision.
```

The product architecture is intentionally hybrid:

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

The normalizer may use AI to extract intent from messy enterprise context.

The critical path does not rely on AI judgment. Source Verifiers check evidence at the source: tickets, reviews, CI runs, security scans, rollback plans, deployment windows, IAM, SIEM, cloud metadata, or business systems.

```text
The normalizer extracts intent.
Schemas structure it.
Verifiers check evidence at the source.
The policy kernel decides.
The warrant signs.
The ledger remembers.
```

### Why Source Verifiers Matter

A valid schema is not the same as a true claim.

An agent can produce a structurally valid object saying:

```json
{
  "ticket_id": "CHG-1001",
  "approval": "approved",
  "rollback_plan": "available"
}
```

Pydantic can validate the shape. It cannot prove the ticket exists, that the approval is real, that the approver is authorized, or that the rollback plan is fresh and scoped to the requested action.

AXIOM v0.1.6 introduces source verification for this reason:

```text
Pydantic structures. AXIOM verifies.
```

### Source-Verified DevOps MVP

The reference MVP demonstrates a production deployment action:

```text
agent_ops_01 wants to deploy prod.payment-api
```

AXIOM verifies these claims at source before issuing a warrant:

```text
change ticket approved
GitHub PR approved
CI checks passed
security scan clean
rollback plan available
deployment window allowed
```

Run it locally:

```bash
PYTHONPATH=reference/python python -m axiom.cli verify-action \
  --action-request examples/devops/deploy_to_production.action_request.json \
  --sources examples/devops/sources_allow.json \
  --policy examples/devops/devops_prod_policy.yml \
  --out examples/devops/output.allow.warrant.json \
  --proof-out examples/devops/output.allow.proof_vector.json \
  --verified-out examples/devops/output.allow.verified_evidence.json \
  --ledger data/devops_ledger.jsonl
```

Expected result:

```text
Decision: ALLOW
Verified claims: 6
```

Try missing rollback:

```bash
PYTHONPATH=reference/python python -m axiom.cli verify-action \
  --action-request examples/devops/deploy_to_production.action_request.json \
  --sources examples/devops/sources_missing_rollback.json \
  --policy examples/devops/devops_prod_policy.yml \
  --out examples/devops/output.suspend.warrant.json
```

Expected result:

```text
Decision: SUSPEND
Missing evidence:
- rollback_available
```

Try failed security scan:

```bash
PYTHONPATH=reference/python python -m axiom.cli verify-action \
  --action-request examples/devops/deploy_to_production.action_request.json \
  --sources examples/devops/sources_failed_security.json \
  --policy examples/devops/devops_prod_policy.yml \
  --out examples/devops/output.block.warrant.json
```

Expected result:

```text
Decision: BLOCK
Missing evidence:
- contradiction:security_scan_failure
```

The same flow is also exposed through HTTP:

```text
POST /v1/actions/evaluate
```


## 1. The Final Thesis

AXIOM is built around one simple claim:

```text
Permission is not proof.
Confidence is not proof.
A valid identity is not proof.
A safe runtime is not proof.
A clean log is not proof by itself.

Critical action requires proportional proof.
```

AXIOM turns autonomous execution into a governed, auditable, proof-based process:

```text
Evidence → Governance → Warrant → Execution → Ledger
```

A system governed by AXIOM does not ask only:

```text
Can this agent act?
```

It asks:

```text
Has this action earned the right to be executed?
```

---

## 2. Why AXIOM Exists

NVIDIA strengthens trust in the execution infrastructure.

OpenAI and Anthropic strengthen the safety of agents and their runtimes.

Traditional cybersecurity strengthens access control, identity, posture, and policy.

AXIOM adds the missing layer:

```text
Proof of Action
```

A critical autonomous action should not only be:

```text
technically possible
identity-authorized
policy-permitted
runtime-guarded
executed in an attested environment
```

It must also be:

```text
justified by proportional evidence
bound to a specific context
scoped to a specific target
fresh enough to be valid
free from blocking contradictions
recorded as an Execution Warrant
written into a Proof Ledger
```

Short version:

> **The others strengthen the capacity to act. AXIOM governs the right to act.**

---

## 3. Ecosystem Map

AXIOM does not replace the major layers of the AI and cybersecurity stack.

It gives them a common proof-of-action layer.

| Layer | Examples | What it secures | What remains missing |
|---|---|---|---|
| Infrastructure | NVIDIA, cloud, confidential computing, attestation | Execution environment | Whether a specific action is justified |
| Model/runtime | OpenAI, Anthropic, agent SDKs, guardrails, hooks, sandboxing | Agent behavior and tool use inside a runtime | Portable, provider-agnostic warrant of action |
| Cybersecurity | IAM, Zero Trust, SIEM, EDR, scanners, policy engines | Identity, posture, access, detection | Proof that an autonomous action is proportionally justified |
| AXIOM | ProofVector, RequirementVector, Execution Warrant, Proof Ledger | The act itself | The external systems still provide evidence |

AXIOM's role is not to be another model, scanner, SIEM, IAM system, or runtime.

AXIOM's role is to answer the missing question:

```text
Is this specific action sufficiently justified by proof, in this context, right now?
```

---

## 4. The Shadow Agent Sprawl Problem

Enterprises are moving from AI pilots to autonomous agents.

The problem is not only that agents may be unsafe.

The deeper problem is that agents can proliferate faster than security, platform, compliance, and audit teams can inventory, govern, and verify their actions.

This creates a new enterprise risk:

```text
I have agents, but I cannot prove they are under control
or credible in their actions.
```

AXIOM addresses this with a proof-warrant model:

```text
Every critical action must carry proof.
Every decision must produce a warrant.
Every warrant must be auditable.
Every missing proof becomes explicit.
```

AXIOM does not claim to discover every agent automatically.

AXIOM provides the protocol and reference kernel for making critical autonomous actions warrant-gated, controllable, credible, and auditable.

---

## 5. The Core Law

```text
No action beyond proportional proof.
```

This means:

```text
The more consequential the action,
the stronger, fresher, broader, and more auditable the proof must be.
```

A unit test may be enough for a local refactor.

It is not enough for a production payment deployment.

A risk score may be enough for a low-value refund.

It is not enough for a high-value wire transfer.

A single sensor may be enough for a harmless robotic movement.

It is not enough for a human-adjacent industrial action.

The action weight determines the proof required.

---

## 6. AXIOM Doctrine

AXIOM is governed by seven invariants:

```text
1. Permission is not proof.
2. Proof must be proportional to consequence.
3. Proof is a vector, not a scalar score.
4. No critical action without an Execution Warrant.
5. No evidence without provenance.
6. No warrant beyond context.
7. No LLM in the final authorization path.
```

The model may propose.

The agent may collect.

The runtime may execute.

The infrastructure may attest.

The warrant decides.

---

## 7. What AXIOM Is

AXIOM is:

```text
a Proof-of-Action Layer
a Proof Warrant Protocol
a deterministic reference kernel
a provider-agnostic evidence layer
a warrant gate for critical autonomous actions
an auditable Proof Ledger
a future dataset engine for proof-native agents
```

AXIOM is not:

```text
a scanner
a SIEM
an IAM system
a model provider
a cloud provider
an agent builder
a generic observability platform
a replacement for OpenAI, Anthropic, NVIDIA, GitHub, GitLab, or Zero Trust
```

AXIOM consumes signals from those systems.

It does not replace them.

---

## 8. Proof-of-Action Layer

AXIOM defines a new architectural category:

```text
Proof-of-Action Layer
```

A Proof-of-Action Layer sits between evidence sources and execution points.

```text
Evidence Sources
  → Canonical Evidence Events
  → Proof Router
  → ProofVector
  → AXIOM Kernel
  → Execution Warrant
  → Enforcement Point
  → Proof Ledger
```

Its purpose is to make critical action:

```text
controllable
credible
auditable
explainable
interoperable
governable
```

The minimal operating rule:

```text
No proof, no warrant.
No warrant, no critical action.
```

---

## 9. Architecture

```text
                 ┌────────────────────────────┐
                 │     Evidence Sources       │
                 │                            │
                 │ GitHub / GitLab / CI/CD    │
                 │ Semgrep / Snyk / scanners  │
                 │ SIEM / EDR / SOC           │
                 │ Business APIs              │
                 │ Human approvals            │
                 │ Local JSON / webhooks      │
                 │ Sensors / runtime events   │
                 └──────────────┬─────────────┘
                                │
                                ▼
                 ┌────────────────────────────┐
                 │ Canonical Evidence Events  │
                 │ provider-agnostic evidence │
                 └──────────────┬─────────────┘
                                │
                                ▼
                 ┌────────────────────────────┐
                 │        Proof Router        │
                 │ merges partial evidence    │
                 └──────────────┬─────────────┘
                                │
                                ▼
                 ┌────────────────────────────┐
                 │        ProofVector         │
                 │ what proof supports        │
                 └──────────────┬─────────────┘
                                │
                                ▼
                 ┌────────────────────────────┐
                 │      AXIOM Kernel          │
                 │ deterministic decision     │
                 └──────────────┬─────────────┘
                                │
                                ▼
                 ┌────────────────────────────┐
                 │    Execution Warrant       │
                 │ signed decision artifact   │
                 └──────────────┬─────────────┘
                                │
                                ▼
                 ┌────────────────────────────┐
                 │       Proof Ledger         │
                 │ audit + learning memory    │
                 └────────────────────────────┘
```

---

## 10. Core Artifacts

| Artifact | Role |
|---|---|
| `Action` | The proposed operation to execute |
| `Action Weight` | Consequence and risk weight of the action |
| `Canonical Evidence Event` | Provider-agnostic evidence input |
| `ProofVector` | What the available evidence supports |
| `RequirementVector` | What the action requires before execution |
| `Execution Warrant` | Signed, scoped, time-bound decision artifact |
| `Proof Ledger` | Append-only memory of warrant decisions |

---

## 11. Canonical Evidence Event

AXIOM v0.1.6 is evidence-first and source-verified.

GitHub, GitLab, Jenkins, Semgrep, SIEM, EDR, business systems, local JSON, webhooks, and human approvals are all evidence sources.

AXIOM evaluates only canonical proof.

Example:

```json
{
  "event_id": "ev_security_scan_001",
  "source": {
    "provider": "semgrep",
    "kind": "security_scan",
    "name": "semgrep",
    "trust_level": "high",
    "collected_at": 1779100000
  },
  "subject": {
    "action_id": "act_deploy_payment_api",
    "target": "payment-api",
    "environment": "production"
  },
  "claims": {
    "security_scan_clean": false
  },
  "evidence_refs": [
    "semgrep_report_001"
  ],
  "limitations": [],
  "contradictions": [
    {
      "type": "security_scan_failure",
      "severity": "critical",
      "summary": "Critical finding detected."
    }
  ]
}
```

The same schema can represent:

```text
CI results
security scans
human approvals
rollback plans
fraud risk checks
SOC clearance
business approvals
runtime attestations
external API responses
```

That is what makes AXIOM provider-agnostic.

---

## 12. Proof Hygiene

AXIOM follows a strict proof-hygiene rule:

```text
An evidence source may only claim what it actually observed.
```

Examples:

| Evidence source | May claim | Must not claim |
|---|---|---|
| Semgrep | `security_scan_clean` | `human_reviewed`, `rollback_available` |
| GitHub Checks / GitLab CI | `unit_tests_passed`, `integration_tests_passed` | `security_scan_clean`, `human_reviewed` |
| PR/MR review system | `human_reviewed` | `unit_tests_passed`, `rollback_available` |
| Rollback plan artifact | `rollback_available` | `security_scan_clean`, `human_reviewed` |
| Fraud risk API | `fraud_score_below_threshold` | `manager_approved` |
| Human approval system | `human_approved` | `fraud_score_below_threshold` |

AXIOM loses value if connectors invent proof.

Proof must be observed, sourced, scoped, fresh, and auditable.

---

## 13. Decision Model

AXIOM emits one of five decisions:

| Decision | Meaning |
|---|---|
| `ALLOW` | Proof covers requirements and the warrant is issued |
| `CONDITIONAL` | Execution allowed only under explicit constraints |
| `SUSPEND` | Missing proof can potentially be supplied |
| `REQUIRE_HUMAN_REVIEW` | Automated proof is insufficient for action weight |
| `BLOCK` | Contradiction, forbidden action, hard risk limit, invalid proof, or forged evidence |

The UX is not:

```text
No.
```

It is:

```text
Not yet. Here is the proof gap.
```

Suspended and blocked warrants are not waste.

They are structured learning signals.

---

## 14. Deterministic Kernel

AXIOM does not authorize by model confidence.

It authorizes through deterministic constraints:

```text
Allowed(action) ⇔

ProofVector ⊒ RequirementVector

AND Scope(action) ⊆ Scope(Proof)

AND Time(action) ⊆ ValidityWindow(Proof)

AND Risk(action, context) ≤ PolicyRiskBound(action, context)

AND Contradictions(evidence) = ∅

AND Limitations(proof) ∩ CriticalRequirements(action) = ∅

AND Signature(warrant) is valid

AND Warrant is not expired

AND Warrant is not revoked
```

An LLM may help with:

```text
claim extraction
evidence summarization
proof gap explanation
next-action suggestions
ProofVector drafting
```

An LLM must not be the final authorization authority.

```text
The model may become proof-native,
but the warrant remains external.
```

---

## 15. Action Weight

`Action Weight` is a governance parameter, not a scientific measurement.

It represents an organization's risk appetite for a class of actions.

It must be:

```text
defined
versioned
reviewed
audited
owned by security / governance leadership
```

AXIOM does not claim to discover the true risk of an action automatically.

AXIOM provides a deterministic mechanism for applying a documented risk policy to execution decisions.

---

## 16. Proof Levels

Proof levels are useful, but never sufficient alone.

They must always be combined with:

```text
scope
context
freshness
limitations
contradictions
validity window
risk bound
```

| Level | Name | Meaning |
|---|---|---|
| `P0` | Unsupported | Model assertion only; no external evidence |
| `P1` | Plausible | Coherent hypothesis, but unverified |
| `P2` | Source-backed | Static evidence: document, diff, isolated log, single artifact |
| `P3` | Cross-checked | Multiple independent sources or empirical corroboration |
| `P4` | Executed | Verified through test, benchmark, query, simulation, or formal check under assumptions |
| `P5` | Audited | Executed and reviewed by human, trusted process, formal authority, or third party |

```text
P4 is not universal.
Executed proof is only valid within its assumptions, scope, and test conditions.
```

---

## 17. Execution Warrant

An `Execution Warrant` is the central AXIOM artifact.

It records:

```text
who requested the action
what action was requested
what proof was provided
what proof was required
what proof was missing
what scope was authorized
what risk was accepted or rejected
why the action was allowed, suspended, or blocked
when the decision was made
how the warrant was signed
where the decision was recorded
```

Example:

```json
{
  "warrant_id": "wrn_000001",
  "warrant_type": "EXECUTION_WARRANT",
  "status": "SUSPENDED",
  "actor": {
    "actor_id": "ai_coding_agent_01",
    "actor_type": "ai_agent",
    "identity_verified": true
  },
  "action": {
    "action_type": "deploy_production",
    "target": "payment-api",
    "environment": "production"
  },
  "provided_proof": {
    "proof_level": "P2_SOURCE_BACKED",
    "evidence_refs": [
      "git_diff_abc123",
      "ci_unit_tests_789"
    ]
  },
  "missing_evidence": [
    "integration_tests_passed",
    "security_scan_clean",
    "rollback_available",
    "human_reviewed"
  ],
  "decision": "SUSPEND",
  "reason": "Provided proof is not proportional to the consequence of deploying payment-api to production."
}
```

---

## 18. Proof Ledger

The Proof Ledger is the append-only memory of AXIOM decisions.

In v0.1.5, the reference implementation uses a local JSONL hash chain for simplicity and transparency.

At enterprise scale, ledger design raises first-class concerns:

```text
integrity
distribution
privacy
retention
interoperability
revocation
external verification
tenant boundaries
compliance export
```

The local ledger is the reference starting point, not the final enterprise architecture.

Strategic view:

```text
The warrant is the product.
The Proof Ledger is the moat.
RLPF is the expansion.
```

The format of a warrant can be copied.

A history of real proof decisions cannot be copied.

Every `SUSPEND`, `BLOCK`, and `ALLOW` becomes structured proof feedback.

---

## 19. AXIOM and Cybersecurity

AXIOM is cybersecurity because it protects execution.

Traditional cybersecurity asks:

```text
Who is acting?
Is this identity valid?
Is the device posture acceptable?
Is the access allowed?
Is the behavior suspicious?
```

AXIOM adds:

```text
Is this action justified by proportional proof?
```

This is not a replacement for IAM, Zero Trust, EDR, SIEM, SOAR, scanners, or policy engines.

It is a missing decision artifact those systems can feed:

```text
identity signals
policy signals
scan results
logs
alerts
attestation
approvals
test results
risk scores
```

AXIOM converts those signals into:

```text
ALLOW / SUSPEND / BLOCK
Execution Warrant
Proof Ledger entry
```

Precise cyber claim:

```text
AXIOM does not make attacks impossible.
AXIOM makes unjustified critical actions impossible to authorize properly
when execution is warrant-gated.
```

---

## 20. AXIOM vs Scanners

AXIOM is not a scanner.

Scanners detect or assess risk.

AXIOM governs whether execution is justified in light of that risk.

```text
Assessment Layer → Semgrep / Snyk / Wiz / SIEM / EDR / CNAPP
Decision Layer   → AXIOM
Execution Layer  → CI/CD / agents / scripts / cloud APIs
```

Short version:

```text
Scanners detect risk.
AXIOM governs the right to act.
```

If Semgrep reports a critical finding and an agent still requests a production deployment, AXIOM can issue:

```text
BLOCK
```

If the scanner evidence is missing, AXIOM can issue:

```text
SUSPEND
```

If the evidence covers the requirement vector, AXIOM can issue:

```text
ALLOW
```

---

## 21. AXIOM and OpenAI, Anthropic, NVIDIA

AXIOM is complementary to major AI infrastructure providers.

| Actor | Strength | AXIOM adds |
|---|---|---|
| OpenAI | Agent runtime, orchestration, tools, guardrails, sandboxing, tracing | External proof-of-action warrant and ledger |
| Anthropic | Claude Code hooks, agent safety, deterministic control points, MCP ecosystem | Provider-agnostic warrant protocol beyond one runtime |
| NVIDIA | Accelerated infrastructure, guardrails, attestation, confidential computing | Decision of whether the action itself is justified |
| Traditional Cyber | Identity, posture, access, policy, detection | Portable proof that a specific autonomous action was justified |

Important distinction:

```text
MCP validates the need for open agent-tool interoperability.
Claude Code Hooks validate the need for deterministic pre-action control.
AXIOM targets the missing neutral layer:
proof of action before critical execution.
```

AXIOM does not compete with these layers.

AXIOM gives them a common warrant language.

---

## 22. Anthropic Hooks and AXIOM

Claude Code Hooks are a strong validation of AXIOM's thesis.

They show that deterministic control before tool use is necessary.

But a hook is not the same thing as a provider-agnostic warrant protocol.

```text
Claude Code Hook:
Before using a tool, run a configured control.
If the hook denies, block the tool call.

AXIOM:
Before a critical action, gather multi-source evidence.
Compare ProofVector and RequirementVector.
Check scope, freshness, limitations, contradictions, and action weight.
Emit ALLOW / SUSPEND / BLOCK.
Produce a signed Execution Warrant.
Record the decision in a Proof Ledger.
```

Best integration:

```text
Claude Code → PreToolUse Hook → AXIOM → Warrant → Allow/Block
```

But this is an integration, not a dependency.

AXIOM must remain independent of any single runtime.

```text
Hooks are enforcement points.
AXIOM is the proof-of-action protocol.
```

---

## 23. MCP, Hooks, and AXIOM

MCP and Claude Code Hooks should not be confused.

```text
MCP expands what an agent can connect to.
Hooks constrain how an agent acts.
AXIOM proves whether a critical action has earned the right to execute.
```

MCP validates the need for open agent-tool interoperability.

Hooks validate the need for deterministic action control.

AXIOM combines these market signals into a neutral Proof-of-Action Layer:

```text
not another tool protocol
not another hook system
not another model guardrail

a portable warrant format,
canonical proof schema,
and ledger for critical autonomous actions.
```

---

## 24. AXIOM and Scale AI

The comparison with Scale AI is strategic, not literal.

Scale AI helped industrialize labeled data for model learning.

AXIOM aims to industrialize proof-labeled decisions for autonomous action.

```text
Model era:
raw data → labels → training datasets

Agent era:
proposed action → required proof → warrant decision → Proof Ledger
```

Short version:

```text
The model era needed labels to learn.
The agent era will need warrants to act.
```

Even sharper:

```text
Scale AI helped enterprises turn raw data into trainable models.
AXIOM helps enterprises turn uncontrolled agents into controlled,
credible, warrant-gated systems.
```

---

## 25. AXIOM and Model Intelligence

AXIOM does not magically make a model know more facts.

It improves a different and more operational form of intelligence:

```text
Knowledge intelligence:
what the model knows.

Action intelligence:
what the model knows how to do with what it knows.

Epistemic intelligence:
what the model knows about the quality, limits, and proof status
of its own claims before acting.
```

AXIOM immediately improves action intelligence and epistemic intelligence.

A model without AXIOM may say:

```text
The patch looks correct. Deploy it.
```

A system governed by AXIOM says:

```text
The patch is plausible.
Available proof: unit tests.
Missing proof: integration tests, security scan, rollback plan, human review.
Action: production deployment.
Risk: critical.
Decision: SUSPEND.
```

That is not ignorance.

That is intelligent treatment of ignorance.

---

## 26. Black-Box and White-Box Models

AXIOM can improve both black-box and white-box agents, but differently.

### Black-box models

For black-box models, AXIOM does not change weights.

It improves behavior through:

```text
external feedback
proof gaps
challenge responses
RAG over previous warrants
tool-use constraints
few-shot proof examples
runtime decision loops
```

### White-box models

For open-weight or internal models, AXIOM can support deeper learning:

```text
fine-tuning
instruction tuning
DPO
reward modeling
RLPF
proof-native adapters
evaluation benchmarks
```

Final formula:

```text
Black-box: AXIOM changes the decision loop.
White-box: AXIOM can turn proof feedback into training data.
```

---

## 27. The AXIOM Loop

```text
Cybersecurity governs AI.
AI learns from governance.
Future agents become proof-native.
The warrant remains external.
```

A proof-native agent is not an agent that authorizes itself.

It is an agent that becomes better at anticipating the proof required before requesting execution.

```text
The model may become proof-native,
but the warrant remains external.
```

---

## 28. RLPF

RLPF means:

```text
Reinforcement Learning from Proof Feedback
```

RLHF teaches models what humans prefer.

RLPF teaches agents what proof supports.

A Proof Ledger creates training/evaluation data like:

```json
{
  "action": "deploy_production",
  "provided_proof": ["unit_tests_passed"],
  "required_proof": ["integration_tests", "security_scan", "rollback_plan"],
  "decision": "SUSPEND",
  "reason": "proof_not_proportional_to_consequence"
}
```

This is not a classic label.

It is an annotation of consequence.

---

## 29. Provider-Agnostic Evidence Layer

v0.1.5 introduces provider-agnostic evidence.

AXIOM can consume:

```text
local JSON
JSONL
external API payloads
webhooks
GitHub Actions
GitLab CI
Jenkins-like reports
Semgrep/SAST reports
manual approvals
SIEM-like clearance reports
rollback artifacts
business risk systems
```

The principle:

```text
Any evidence source
        ↓
Canonical Evidence Event
        ↓
Proof Router
        ↓
ProofVector
        ↓
AXIOM Kernel
        ↓
Execution Warrant
```

GitHub is an integration.

GitLab is an integration.

DevSecOps is a first market wedge.

AXIOM is the general Proof Warrant Protocol.

---

## 30. Current Reference Implementation: v0.1.6

v0.1.6 includes:

```text
Deterministic policy engine
Pydantic runtime models
ProofVector / RequirementVector evaluation
Action Weight policy checks
Scope checks
Freshness checks
Contradiction checks
Limitation checks
Execution Warrant generation
HMAC signature verification
JSONL hash-chain Proof Ledger
Proof Router
Canonical Evidence Event loader
Local JSON / JSONL evidence support
External API / webhook evidence support
Semgrep connector
Provider-agnostic CI adapter
Provider-agnostic human review adapter
Rollback adapter
Manual / SIEM-style adapter examples
Source Verifiers MVP
ActionEnvelope / Claim / VerifiedEvidence schemas
`verify-action` CLI
`POST /v1/actions/evaluate` API endpoint
DevOps production deployment source-verified demo
GitHub Action Warrant Gate
GitLab CI Warrant Gate example
FastAPI endpoints
CLI commands
Conformance tests
Unit tests
Integration tests
```

Packaged verification target:

```text
51 tests passing
```

---

## 31. Quick Start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

PYTHONPATH=reference/python pytest tests -q
```

Expected packaged result:

```text
51 passed
```

---

## 32. Demo 1 — General Proof-of-Action Protocol

This demo shows AXIOM outside CI/CD.

It uses a wire-transfer action and local evidence JSON.

Clean evidence:

```bash
PYTHONPATH=reference/python python -m axiom.cli evidence-eval \
  --action examples/generic/wire_transfer.action.json \
  --evidence examples/generic/wire_transfer_clean.evidence.json \
  --policy examples/generic/wire_transfer_policy.yml \
  --out examples/demo.wire_transfer.allow.warrant.json \
  --ledger data/demo_ledger.jsonl
```

Expected:

```text
Decision: ALLOW
```

High-risk evidence:

```bash
PYTHONPATH=reference/python python -m axiom.cli evidence-eval \
  --action examples/generic/wire_transfer.action.json \
  --evidence examples/generic/wire_transfer_high_risk.evidence.json \
  --policy examples/generic/wire_transfer_policy.yml \
  --out examples/demo.wire_transfer.block.warrant.json \
  --ledger data/demo_ledger.jsonl
```

Expected:

```text
Decision: BLOCK
```

Ledger verification:

```bash
PYTHONPATH=reference/python python -m axiom.cli ledger-verify \
  --ledger data/demo_ledger.jsonl
```

Expected:

```text
LEDGER VALID
```

Message:

```text
CI/CD is one use case.
AXIOM is evidence-first and provider-agnostic.
```

---

## 33. Demo 2 — DevSecOps Warrant Gate

This demo shows AXIOM as a DevSecOps Warrant Gate.

```text
CI evidence
Security scan evidence
Human review evidence
Rollback evidence
        ↓
Proof Router
        ↓
AXIOM Kernel
        ↓
Execution Warrant
        ↓
Merge/deploy allowed or blocked
```

Generate Semgrep proof:

```bash
PYTHONPATH=reference/python python -m axiom.cli semgrep-proof \
  --report examples/scanners/semgrep_failed_scan.json \
  --target payment-api \
  --environment production \
  --commit abc123 \
  --out examples/demo.semgrep.partial_proof_vector.json
```

Generate CI proof:

```bash
PYTHONPATH=reference/python python -m axiom.cli ci-proof \
  --report examples/github/check_runs_passed.json \
  --target payment-api \
  --environment production \
  --commit abc123 \
  --out examples/demo.ci.partial_proof_vector.json
```

Generate review proof:

```bash
PYTHONPATH=reference/python python -m axiom.cli review-proof \
  --report examples/github/pr_reviews_approved.json \
  --target payment-api \
  --environment production \
  --commit abc123 \
  --out examples/demo.review.partial_proof_vector.json
```

Generate rollback proof:

```bash
PYTHONPATH=reference/python python -m axiom.cli rollback-proof \
  --report examples/rollback/rollback_plan_available.json \
  --target payment-api \
  --environment production \
  --commit abc123 \
  --out examples/demo.rollback.partial_proof_vector.json
```

Merge proof:

```bash
PYTHONPATH=reference/python python -m axiom.cli merge-proof \
  --proof examples/demo.semgrep.partial_proof_vector.json \
  --proof examples/demo.ci.partial_proof_vector.json \
  --proof examples/demo.review.partial_proof_vector.json \
  --proof examples/demo.rollback.partial_proof_vector.json \
  --out examples/demo.merged_proof_vector.json
```

Evaluate:

```bash
PYTHONPATH=reference/python python -m axiom.cli eval \
  --action examples/deploy_payment_api.action.json \
  --proof examples/demo.merged_proof_vector.json \
  --policy examples/security_policy.yml \
  --out examples/demo.devsecops.warrant.json \
  --ledger data/demo_ledger.jsonl
```

With failed Semgrep evidence, expected:

```text
Decision: BLOCK
```

Message:

```text
No valid Execution Warrant → no merge.
```

---

## 34. GitHub and GitLab

AXIOM includes installable DevSecOps examples:

```text
.github/workflows/axiom-warrant-gate.yml
.gitlab-ci.yml
```

These demonstrate how CI/CD systems can act as enforcement points.

The important architecture is not GitHub or GitLab.

The important architecture is:

```text
Pipeline produces evidence.
AXIOM evaluates proof.
The gate fails if the warrant is not ALLOW.
```

---

## 35. FastAPI Control Plane

v0.1.6 includes a minimal FastAPI control plane.

Endpoints:

```text
GET  /health
POST /v1/actions/evaluate
POST /v1/warrants/evaluate
POST /v1/evidence/convert
POST /v1/warrants/evaluate-from-evidence
```

Run locally:

```bash
PYTHONPATH=reference/python uvicorn axiom.api:app --reload
```

The API is intentionally minimal.

It exists to demonstrate that AXIOM can become a control plane, not only a CLI.

---

## 36. Security Boundaries

AXIOM can guarantee only what is routed through its enforcement points.

AXIOM helps ensure:

```text
critical actions are evaluated before execution
warrants are scoped and signed
decisions are auditable
proof gaps are explicit
limitations suspend actions
contradictions block actions
ledger history is preserved
missing evidence becomes feedback
```

AXIOM does not guarantee:

```text
absolute truth
perfect security
interception of non-instrumented paths
absence of human error
honesty of every external system
correctness of every evidence source
quality of the base model
impossibility of attack
```

Precise claim:

```text
AXIOM does not make attacks impossible.
AXIOM makes unjustified critical actions impossible to authorize properly
when execution is warrant-gated.
```

---

## 37. Standard Strategy

AXIOM should not try to do everything.

AXIOM should define what every critical autonomous system should produce before acting:

```text
evidence
decision
warrant
ledger entry
```

The standard surface is:

```text
Canonical Evidence Event
ProofVector
RequirementVector
Execution Warrant
Proof Ledger Entry
```

The strategic defense is not that the JSON format is impossible to copy.

The defense is:

```text
neutrality
open source adoption
provider-agnostic adapters
community
conformance tests
Proof Ledger data moat
```

AXIOM's long-term position depends on becoming the neutral proof-of-action layer before closed ecosystems fragment the market.

---

## 38. Business Perspective

AXIOM is not best positioned as a low-ticket productivity tool.

Its strongest wedge is critical-action governance.

Potential offerings:

```text
Proof Gap & Shadow Agent Assessment
Warrant Gate Pilot
AXIOM Control Plane
Proof Ledger analytics
Compliance and audit export
Enterprise adapters
```

Value is tied to:

```text
risk reduction
auditability
production safety
agent governance
regulatory readiness
incident reconstruction
controlled autonomous execution
```

The first buyer is likely not a casual developer.

The first buyer is likely:

```text
CISO / RSSI
VP Engineering
Head of Platform
Head of DevSecOps
CTO
AI Governance lead
```

---

## 39. Roadmap

### v0.1.x — Reference Protocol

```text
stabilize schemas
improve README and RFC
release provider-agnostic evidence examples
add conformance fixtures
```

### v0.2 — Evidence Connectors

```text
GitHub live API
GitLab live API
Snyk
Semgrep
SIEM / EDR
Jira / ServiceNow approvals
Cloud IAM / policy signals
```

### v0.3 — Enforcement Points

```text
GitHub Action hardening
GitLab CI hardening
Kubernetes admission controller
API gateway plugin
agent runtime wrapper
Claude Code hook integration
OpenAI Agents SDK integration
```

### v0.4 — Control Plane

```text
central API
warrant registry
ledger verification
policy management
evidence ingestion
tenant isolation
```

### v1.0 — Enterprise Proof Fabric

```text
distributed ledger
external auditor verification
provider-neutral warrant validation
compliance export
proof analytics
RLPF dataset generation
```

---

## 40. Final Manifesto

AXIOM does not control by trust.

AXIOM controls by proof.

It does not ask whether an agent sounds confident.

It asks what the evidence allows the agent to do.

It does not ask whether an actor has permission alone.

It asks whether the action is justified, scoped, fresh, risk-bounded, reversible when needed, and auditable.

It does not turn proof into a shallow score.

It turns proof into boundaries.

It does not make agents powerful by making them more confident.

It makes them usable by forcing their actions to become provable.

```text
No certainty beyond evidence.
No action beyond proof.
No warrant beyond context.
No action beyond proportional proof.
```

AXIOM makes autonomous actions controllable, credible, and auditable.

AXIOM is the Proof-of-Action Layer for critical autonomous systems.

```text
No proof, no warrant.
No warrant, no critical action.
```
