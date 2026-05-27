# AXIOM GitHub Action Warrant Gate Example

This directory contains helper scripts used by `.github/workflows/axiom-warrant-gate.yml`.

The workflow models each evidence producer as a GitHub Actions job:

- `ci_agent` produces CI/test evidence.
- `security_agent` produces scanner evidence.
- `review_agent` produces human-review evidence.
- `rollback_agent` produces rollback evidence.
- `axiom_warrant_gate` merges partial ProofVectors and issues the final warrant.

The final job fails unless AXIOM returns `ALLOW`.

If the workflow is configured as a required status check in branch protection, then:

```text
No valid Execution Warrant → no merge.
```
