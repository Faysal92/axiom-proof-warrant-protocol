# AXIOM

**Status:** Draft v0.1.2 / RFC Candidate  
**Category:** Proof-Weighted Authorization / Proof Warrant Protocol  
**Primary Artifact:** Execution Warrant  
**Core Doctrine:** No action beyond proportional proof.

> AXIOM is a proof-warrant protocol and deterministic reference kernel for critical AI actions.

```text
Permission is not proof.
Proof must be proportional to consequence.
No action beyond proportional proof.
```

AXIOM exists because AI is moving from **answering** to **acting**.

When AI only answers, the main problem is correctness.  
When AI acts, the main problem is justification.

A critical AI action should not execute merely because an agent has permission.  
It should execute only when the available proof is proportional to the consequence of the action.

---

## 1. The Cybersecurity Blind Spot

Modern cybersecurity controls access.

AXIOM controls justified execution.

Traditional security systems ask:

```text
Who is acting?
Does this actor have permission?
Does the action satisfy policy?
Does the behavior look suspicious?
```

Those questions are necessary, but not sufficient.

An AI agent can be authenticated, authorized, policy-compliant, inside the perimeter, and apparently normal — and still execute a dangerous action based on hallucinated reasoning, stale evidence, prompt injection, incomplete tests, misread context, missing rollback, false correlation, or contradictory logs.

The next cyber failure mode is not only unauthorized action.

It is:

```text
authorized action without sufficient justification
```

AXIOM adds the missing runtime question:

```text
Is this action sufficiently justified by proof, in this context, right now?
```

Short version:

```text
A stolen key should not be enough.
A valid role should not be enough.
A policy match should not be enough.
A confident agent should not be enough.
```

AXIOM requires a warrant.

---

## 2. What AXIOM Does

AXIOM turns static permission into proof-weighted authorization.

```text
Identity + Permission + Policy
→ Access

Identity + Permission + Policy + Contextual Proof + Action Weight + Scope + Time + Accountability
→ Execution Warrant
```

AXIOM does not replace IAM, Zero Trust, EDR, SIEM, SOAR, CI/CD, runtime governance, or vulnerability scanners.

AXIOM adds the missing artifact those systems should require before critical execution:

```text
Execution Warrant
```

An Execution Warrant records who requested the action, what action was requested, what proof was provided, what proof was required, what proof was missing, what scope was authorized, what risk was accepted, and why the action was allowed, suspended, or blocked.

---

## 3. Assessment Layer vs Decision Layer vs Execution Layer

AXIOM is not a scanner.

Scanners and security tools detect or assess risk. AXIOM decides whether execution is justified.

```text
Assessment Layer → Snyk / Semgrep / SonarQube / Wiz / SIEM / EDR / CNAPP
Decision Layer   → AXIOM
Execution Layer  → CI/CD / agents / scripts / cloud APIs
```

The key distinction:

```text
Scanners detect risk.
AXIOM governs the right to act.
```

A scanner may produce:

```json
{
  "tool": "semgrep",
  "scan_status": "failed",
  "critical_findings": 1,
  "report_ref": "semgrep_report_001"
}
```

AXIOM consumes that evidence inside a `ProofVector`, checks it against policy, and emits a decision:

```text
ALLOW
SUSPEND
BLOCK
REQUIRE_HUMAN_REVIEW
CONDITIONAL
```

AXIOM does not try to find every vulnerability.

AXIOM ensures that critical actions cannot be properly authorized when the required security evidence is missing, stale, contradictory, or failed.

Precise cyber claim:

```text
AXIOM does not make attacks impossible.
AXIOM makes unjustified critical actions impossible to authorize properly when execution is warrant-gated.
```


---

## Scanner Evidence Example — v0.1.2

v0.1.2 adds a concrete scanner-evidence demonstration.

The goal is to prove that AXIOM is the **Decision Layer**, not the Assessment Layer.

```text
Semgrep / Snyk / Wiz / SIEM / EDR → produce evidence
AXIOM → consumes evidence and emits a warrant decision
CI/CD / agents / cloud APIs → execute only with a valid warrant
```

Three scanner-driven outcomes are included:

| Scenario | Scanner Evidence | AXIOM Decision |
|---|---|---|
| Clean scan + required proof | `security_scan_clean: true` | `ALLOW` |
| Missing scan evidence | no `security_scan_clean` dimension | `SUSPEND` |
| Failed Semgrep scan | `security_scan_clean: false` + contradiction | `BLOCK` |

Example failed scanner evidence:

```json
{
  "tool": "semgrep",
  "scan_status": "failed",
  "critical_findings": 1,
  "high_findings": 2,
  "report_ref": "semgrep_report_001"
}
```

AXIOM does not rerun Semgrep.

AXIOM consumes the scanner result as proof and decides whether the deployment is justified.

```text
Scanners detect risk.
AXIOM governs the right to act.
```

---

## 4. The Core Idea

AXIOM is based on one rule:

```text
Action Weight ≤ Proof Coverage
```

A passing unit test is not enough for a production payment deployment.  
A valid service account is not enough to delete critical data.  
A confident agent is not enough to trigger a cyber-response action.  
A policy match is not enough if the action is based on weak or stale evidence.

AXIOM checks whether the proof is proportional to the consequence.

---

## 5. AXIOM Doctrine

AXIOM is governed by seven invariants:

```text
1. Permission is not proof.
2. Proof must be proportional to consequence.
3. Proof is a vector, not a score.
4. No critical action without an Execution Warrant.
5. No evidence without provenance.
6. No warrant beyond context.
7. No LLM in the final authorization path.
```

The model may propose.

The warrant decides.

---

## 6. Product Category

AXIOM defines a category:

```text
Proof-Weighted Authorization
```

Also expressible as:

```text
Proof-Conditioned Authorization
Proof-Bounded Control
Proof Warrant Protocol
Epistemic Zero Trust
```

| Layer | Question |
|---|---|
| Identity | Who is acting? |
| Permission | Is this actor allowed in principle? |
| Policy | Is this action compliant with rules? |
| Runtime Governance | Should this tool call or resource access proceed? |
| **AXIOM** | **Is the proof strong enough for the consequence of this action?** |

AXIOM does not compete with identity and policy systems.

AXIOM provides the proof object they should consume.

---

## 7. AXIOM Is Multidimensional

AXIOM is multidimensional, but not scattered.

It has one core:

```text
No action beyond proportional proof.
```

Every use case comes from this single rule.

AXIOM can be viewed through seven dimensions:

1. **Cybersecurity** — scanners detect risk; AXIOM governs the right to act.
2. **DevSecOps / CI/CD** — AXIOM gates merge, deploy, rollback and infrastructure changes.
3. **AI Governance** — AXIOM turns AI actions into auditable decisions.
4. **Agent Intelligence** — AXIOM transforms a model that answers well into an agent that knows when it has earned the right to act.
5. **Proof-Labeled Dataset** — every warrant decision becomes training and evaluation data.
6. **Protocol / Standard** — Execution Warrant, ProofVector, RequirementVector and Proof Ledger form a vendor-neutral language for proving before acting.
7. **Business Infrastructure** — Warrant Gate, Code Gate, Cyber Response Gate, enterprise connectors, compliance reports and Proof Ledger analytics.

Strategic formula:

```text
The Warrant is the product.
The Proof Ledger is the moat.
RLPF is the expansion.
```

Final multidimensional thesis:

```text
AXIOM is proof infrastructure for autonomous execution.
It secures actions, governs agents, produces auditable decisions,
and generates the datasets that can make future models more intelligent.
```

Where Scale AI industrialized labeled data for perception, AXIOM industrializes proof-labeled decisions for action.

---

## 8. Core Artifacts

| Artifact | Role |
|---|---|
| `Claim` | Assertion produced by a model, agent, or machine process |
| `Proof License` | Boundary of what a claim is allowed to justify |
| `Action Weight` | Consequence weight of the proposed action |
| `ProofVector` | What the available evidence actually supports |
| `RequirementVector` | What proof the action requires |
| `Execution Warrant` | Signed, scoped, time-bound decision artifact |
| `Proof Ledger` | Append-only memory of warrant decisions |

### Note on Action Weight

Action Weight is a governance parameter, not a scientific measurement.

It represents the organization’s risk appetite for a given class of actions and must be defined, versioned, reviewed, and audited by the organization’s security governance function.

AXIOM does not claim to discover the “true” risk of an action automatically. It provides a deterministic mechanism for applying a documented risk policy to execution decisions.

---

## 9. Execution Warrant Example

```json
{
  "warrant_id": "wrn_000001",
  "protocol_version": "axiom-proof-warrant-v0.1.2",
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
  "required_proof": {
    "min_proof_level": "P4_EXECUTED",
    "required_evidence": [
      "unit_tests_passed",
      "integration_tests_passed",
      "security_scan_clean",
      "rollback_plan_verified",
      "human_reviewed"
    ]
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
    "rollback_plan_verified",
    "human_reviewed"
  ],
  "decision": "SUSPEND",
  "reason": "Provided proof is not proportional to the consequence of deploying payment-api to production.",
  "challenge": {
    "resubmit_allowed": true,
    "next_actions": [
      "Run integration tests and attach the test logs.",
      "Run a security scan and attach the scan result.",
      "Provide and verify a rollback plan.",
      "Request human review and attach approval evidence."
    ]
  }
}
```

The UX is not:

```text
No.
```

It is:

```text
Not yet. Here is the proof gap.
```

---

## 10. Decisions

AXIOM emits one of five decisions.

| Decision | Meaning |
|---|---|
| `ALLOW` | Proof covers requirements and warrant is issued |
| `CONDITIONAL` | Execution allowed only under explicit constraints |
| `SUSPEND` | Missing proof can potentially be supplied |
| `REQUIRE_HUMAN_REVIEW` | Automated proof is insufficient for action weight |
| `BLOCK` | Contradiction, forbidden action, hard risk limit, invalid proof, or forged evidence |

Suspended or blocked warrants are not waste.

They are learning signals.

---

## 11. Proof Levels

Proof levels are useful, but never sufficient alone.

They must always be combined with scope, context, freshness, limitations, contradictions, validity window, and risk bound.

| Level | Name | Meaning |
|---|---|---|
| `P0` | Unsupported | Model assertion only; no external evidence |
| `P1` | Plausible | Coherent hypothesis, but unverified |
| `P2` | Source-backed | Static evidence: document, diff, isolated log, single artifact |
| `P3` | Cross-checked | Multiple independent sources or empirical corroboration |
| `P4` | Executed | Verified through test, benchmark, query, simulation, or formal check under assumptions |
| `P5` | Audited | Executed and reviewed by human, trusted authority, formal process, or third party |

```text
P4 is not universal.
Executed proof is only valid within its assumptions, scope, and test conditions.
```

---

## 12. Deterministic Kernel

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

An LLM may assist in:

```text
claim extraction
evidence summarization
missing evidence suggestion
explanation generation
proof-vector drafting
```

An LLM must not be the final authorization authority.

```text
The model may propose.
The warrant decides.
```

---

## 13. AXIOM and Model Intelligence

AXIOM does not magically make a model know more facts.

It improves a different and more operational form of intelligence.

```text
1. Knowledge intelligence
   What the model knows.

2. Action intelligence
   What the model knows how to do with what it knows.

3. Epistemic intelligence
   What the model knows about the quality, limits, and proof status of its own knowledge.
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

AXIOM transforms a model that answers well into an agent that knows when it has earned the right to act.

```text
Short term:
AXIOM teaches the system to measure its ignorance.

Long term:
AXIOM teaches the model to reduce critical ignorance through proof feedback.
```

---

## 14. Black-Box and White-Box Models

AXIOM can improve both black-box and white-box models, but differently.

### Black-box models

For black-box models, AXIOM does not change the weights.

It improves behavior through:

```text
prompting
tool feedback
challenge responses
agent memory
RAG over previous warrants
few-shot proof examples
guarded tool calls
```

Black-box formula:

```text
AXIOM does not change the weights.
AXIOM changes the decision loop.
```

### White-box models

For white-box or open-weight models, AXIOM can improve the model more deeply.

The Proof Ledger can support:

```text
fine-tuning
instruction tuning
DPO
reward modeling
RLPF
evaluation benchmarks
proof-native adapters
```

White-box formula:

```text
AXIOM can turn proof feedback into model training.
```

Final model-improvement thesis:

```text
Black-box: AXIOM improves behavior through external proof feedback.
White-box: AXIOM can improve weights through proof-labeled datasets.
```

---

## 15. The AXIOM Loop

AXIOM sits at the point where cybersecurity and AI autonomy converge.

In the short term, cybersecurity governs AI actions through the Warrant Gate.

In the long term, every blocked, suspended, or allowed warrant becomes structured proof feedback for future agents.

This creates the AXIOM loop:

```text
Cybersecurity governs AI.
AI learns from governance.
Future agents become proof-native.
```

A proof-native agent is not an agent that authorizes itself.

It is an agent that becomes better at anticipating the proof required before requesting execution.

```text
The model may become proof-native, but the warrant remains external.
```

AXIOM turns cybersecurity decisions into structured proof feedback for the next generation of AI agents.

---

## 16. Strategic Thesis

AXIOM has three horizons.

### Immediate Product: Warrant Gate

```text
No proof, no critical execution.
```

The buyer gets:

```text
risk reduction
auditability
compliance evidence
control over AI agents
safe automation
CI/CD and DevSecOps governance
```

### Long-Term Asset: Proof Ledger

Every warrant creates a proof-labeled decision:

```json
{
  "action": "deploy_production",
  "provided_proof": ["unit_tests_passed"],
  "required_proof": ["integration_tests", "security_scan", "rollback_plan"],
  "decision": "SUSPEND",
  "reason": "proof_not_proportional_to_consequence"
}
```

This is not a classic data label.

It is an annotation of consequence.

In v0.1.2, the Proof Ledger is implemented as a local JSONL hash chain for simplicity, transparency, and developer adoption.

At enterprise scale, ledger integrity, distribution, privacy, retention, interoperability, and external verification become first-class design concerns.

The local ledger is the reference starting point, not the final enterprise architecture.

### Expansion: RLPF

RLPF means:

```text
Reinforcement Learning from Proof Feedback
```

RLHF teaches models what humans prefer.  
RLPF teaches agents what proof supports.

```text
The Warrant is the product.
The Proof Ledger is the moat.
RLPF is the expansion.
```

---

## 17. The New Bottleneck

The model era was, in significant part, limited by the availability of high-quality labeled data.

The agent era will be limited by justified action.

```text
Model era:
raw data → labels → training datasets

Agent era:
proposed action → required proof → warrant decision → proof ledger
```

Scale AI industrialized labeled data for model perception.

AXIOM aims to industrialize proof-labeled decisions for agent autonomy.

```text
Scale AI helped models learn to recognize.
AXIOM helps agents learn to justify before acting.
```

In a world of autonomous agents, justification is what makes them deployable in production.


---

## What Changed in v0.1.2

v0.1.2 turns the cyber positioning into a concrete evidence-flow demo.

It adds:

- Semgrep-style scanner output examples;
- scanner-derived `ProofVector` examples;
- `security_policy.yml` for scanner-gated production deployment;
- conformance tests for clean scan, missing scan, and failed scan;
- README updates clarifying `Assessment Layer → Decision Layer → Execution Layer`;
- updated reference version metadata.

The purpose of v0.1.2 is narrow:

```text
prove that AXIOM consumes security evidence and turns it into execution decisions.
```

---

## 18. Reference Implementation Scope

v0.1.2 is deterministic and local.

Included:

```text
Action JSON input
ProofVector JSON input
Policy YAML input
Pydantic runtime models
PolicyEngine separated from Evaluator
RequirementVector generation
Action Weight risk-bound check
Coverage check
Scope check
Time check
Contradiction check
Limitation intersection
Missing proof vs failed proof distinction
Challenge Response
ALLOW / CONDITIONAL / SUSPEND / REQUIRE_HUMAN_REVIEW / BLOCK
HMAC-signed warrant
JSONL proof ledger with hash chain
verify command
ledger verify command
conformance tests
```

Excluded from v0.1.2:

```text
LLM as final decision-maker
fine-tuning
JWS / Ed25519 / RSA signatures
automatic enterprise-wide interception
dynamic deception
full cloud integration
offensive cyber actions
```

v0.1.2 law:

```text
No LLM in the final authorization path.
```

---

## 19. Quick Start

```bash
cd axiom-proof-warrant-protocol-v0.1.2
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=reference/python pytest tests/conformance
```

Expected result:

```text
6 passed
```

Run a suspended warrant example:

```bash
PYTHONPATH=reference/python python -m axiom.cli eval \
  --action examples/deploy_payment_api.action.json \
  --proof examples/deploy_payment_api.missing_proof_vector.json \
  --policy examples/production_policy.yml \
  --out examples/demo.suspend.warrant.json \
  --ledger data/demo_ledger.jsonl
```

Run an allowed warrant example:

```bash
PYTHONPATH=reference/python python -m axiom.cli eval \
  --action examples/deploy_payment_api.action.json \
  --proof examples/deploy_payment_api.good_proof_vector.json \
  --policy examples/production_policy.yml \
  --out examples/demo.allow.warrant.json \
  --ledger data/demo_ledger.jsonl
```

Run a blocked warrant example:

```bash
PYTHONPATH=reference/python python -m axiom.cli eval \
  --action examples/deploy_payment_api.action.json \
  --proof examples/deploy_payment_api.failed_security_scan.proof_vector.json \
  --policy examples/production_policy.yml \
  --out examples/demo.block.warrant.json \
  --ledger data/demo_ledger.jsonl
```

Verify the ledger:

```bash
PYTHONPATH=reference/python python -m axiom.cli ledger-verify \
  --ledger data/demo_ledger.jsonl
```

Expected result:

```text
LEDGER VALID
```



Run the v0.1.2 Semgrep failed-scan example:

```bash
PYTHONPATH=reference/python python -m axiom.cli eval \
  --action examples/deploy_payment_api.action.json \
  --proof examples/deploy_payment_api.semgrep_failed.proof_vector.json \
  --policy examples/security_policy.yml \
  --out examples/output.semgrep.block.warrant.json \
  --ledger data/demo_ledger.jsonl
```

Expected result:

```text
Decision: BLOCK
```

Run the v0.1.2 missing-scan example:

```bash
PYTHONPATH=reference/python python -m axiom.cli eval \
  --action examples/deploy_payment_api.action.json \
  --proof examples/deploy_payment_api.semgrep_missing.proof_vector.json \
  --policy examples/security_policy.yml \
  --out examples/output.semgrep.suspend.warrant.json \
  --ledger data/demo_ledger.jsonl
```

Expected result:

```text
Decision: SUSPEND
```

Run the v0.1.2 clean-scan example:

```bash
PYTHONPATH=reference/python python -m axiom.cli eval \
  --action examples/deploy_payment_api.action.json \
  --proof examples/deploy_payment_api.semgrep_clean.proof_vector.json \
  --policy examples/security_policy.yml \
  --out examples/output.semgrep.allow.warrant.json \
  --ledger data/demo_ledger.jsonl
```

Expected result:

```text
Decision: ALLOW
```

---

## 20. Roadmap

### v0.2 — Evidence Connectors

Connect AXIOM to real evidence:

```text
Git diff
JUnit
GitHub Actions
GitLab CI
Semgrep
Snyk
Terraform plan
Kubernetes events
EDR JSON
SIEM logs
```

### v0.3 — AXIOM Code Gate

Gate AI-generated code before merge and deployment:

```text
AI-generated PR checks
merge warrant
deployment warrant
permission regression gates
security-sensitive code gates
GitHub Action
GitLab CI template
```

### v0.4 — Runtime Enforcement Integrations

Make real systems warrant-gated:

```text
CI/CD plugin
Kubernetes admission controller
API gateway
SOAR connector
agent runtime wrapper
CLI wrappers
Terraform wrapper
kubectl wrapper
```

### v0.5 — Proof Fabric

Make warrants portable and verifiable across systems:

```text
portable warrants
cross-system verification
federated proof exchange
revocation registry
third-party auditors
vendor-neutral warrant validation
```

### v1.0 — Epistemic Learning Layer

Turn proof outcomes into model-improvement signals:

```text
Proof Ledger → training assets
missing evidence examples
negative overclaim examples
positive verified examples
proof pattern examples
model steering
proof-aware adapters
proof-native model evaluation
RLPF datasets
```

---

## 21. Security Boundaries

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
honesty of all external systems
correctness of all evidence sources
quality of the base model
impossibility of attack
```

Precise claim:

```text
AXIOM does not make attacks impossible.
AXIOM makes unjustified critical actions impossible to authorize properly when execution is warrant-gated.
```

---

## 22. Final Manifesto

AXIOM does not control by trust.

AXIOM controls by proof.

It does not ask whether an AI sounds confident.

It asks what the evidence allows the AI to claim.

It does not ask whether an actor has permission alone.

It asks whether the action is justified, scoped, reversible, risk-bounded, and auditable.

It does not turn proof into a score.

It turns proof into boundaries.

It does not make models powerful by making them more confident.

It makes them powerful by forcing their actions to become provable.

```text
No certainty beyond evidence.
No action beyond proof.
No warrant beyond context.
No action beyond proportional proof.
```

AXIOM turns static permission into proof-weighted authorization.

AXIOM transforms a model that answers well into an agent that knows when it has earned the right to act.

AXIOM is the proof-warrant protocol for critical AI actions.
