# AXIOM v0.1.2 Patch Notes

v0.1.2 turns the cybersecurity positioning into a concrete evidence-flow demo.

## Goal

Prove that AXIOM is the Decision Layer between security assessment tools and execution systems.

```text
Assessment Layer → Semgrep / Snyk / Wiz / SIEM / EDR
Decision Layer   → AXIOM
Execution Layer  → CI/CD / agents / scripts / cloud APIs
```

## Added

- Semgrep-style scanner output examples under `examples/scanners/`.
- Scanner-derived ProofVectors:
  - `deploy_payment_api.semgrep_clean.proof_vector.json`
  - `deploy_payment_api.semgrep_failed.proof_vector.json`
  - `deploy_payment_api.semgrep_missing.proof_vector.json`
- `examples/security_policy.yml`.
- Conformance tests for scanner evidence outcomes.
- README updates for v0.1.2.

## Expected Outcomes

| Scenario | Decision |
|---|---|
| Semgrep clean + required proof | `ALLOW` |
| Semgrep missing | `SUSPEND` |
| Semgrep failed / critical finding | `BLOCK` |

## Principle

```text
Scanners detect risk.
AXIOM governs the right to act.
```
