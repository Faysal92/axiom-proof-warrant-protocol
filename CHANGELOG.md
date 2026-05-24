# Changelog

## v0.1.2

- Added concrete scanner-evidence examples for Semgrep-style assessment output.
- Added `security_policy.yml` for scanner-gated production deployment.
- Added `deploy_payment_api.semgrep_clean.proof_vector.json`.
- Added `deploy_payment_api.semgrep_failed.proof_vector.json`.
- Added `deploy_payment_api.semgrep_missing.proof_vector.json`.
- Added conformance tests for clean scan, failed scan, and missing scan evidence.
- Updated README with the Assessment Layer / Decision Layer / Execution Layer positioning.
- Updated reference metadata from v0.1.1 to v0.1.2.

## v0.1.1

- Added Pydantic runtime models.
- Added `PolicyEngine` separate from `Evaluator`.
- Added explicit distinction between missing proof and failed proof.
- Added numeric risk-bound evaluation.
- Added `ChallengeResponse`.
- Added examples for SUSPEND, BLOCK, ALLOW and REQUIRE_HUMAN_REVIEW.
- Added `.gitignore`.
- Kept local HMAC signatures for reference implementation.
- Kept JSONL hash-chain ledger.
