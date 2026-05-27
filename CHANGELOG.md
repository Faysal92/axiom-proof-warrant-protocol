# Changelog

## v0.1.6 — Source Verifiers MVP

- Added source-verified product architecture: Raw Context → Normalizer → Pydantic Schemas → Source Verifiers → Policy Kernel → Execution Warrant → Proof Ledger.
- Added `ActionEnvelope`, `Claim`, `Evidence`, `VerifiedEvidence`, `RiskProfile`, and `SourceBundle` schemas.
- Added deterministic Source Verifiers for Jira tickets, GitHub PRs, CI runs, security scans, rollback plans, and deployment windows.
- Added `verify-action` CLI to verify claims at source and emit a signed Execution Warrant.
- Added `POST /v1/actions/evaluate` API endpoint.
- Added DevOps production deployment MVP examples.
- Added unit, integration, CLI, and API tests.
- Verified: `60 passed`.


## v0.1.5 — Provider-Agnostic Evidence Layer

- Added Canonical Evidence Event schema and runtime model.
- Added local JSON / JSONL canonical evidence adapter.
- Added external API / webhook payload adapter.
- Added provider-agnostic evidence adapters for CI checks, human review, rollback, Semgrep/SAST, and manual evidence.
- Added GitLab CI example workflow (`.gitlab-ci.yml`) to prove AXIOM is not GitHub-only.
- Added GitLab pipeline / merge request examples and manual SIEM evidence examples.
- Added CLI commands `evidence-proof`, `evidence-eval`, `ci-proof`, and `review-proof`.
- Added FastAPI endpoints `/v1/evidence/convert` and `/v1/warrants/evaluate-from-evidence`.
- Added non-code wire-transfer examples to prove AXIOM is not DevSecOps-only.
- Added conformance tests for provider-agnostic evidence and multi-provider flows.
- Preserved proof hygiene: evidence sources may only claim what they actually observed.
- Test suite: `51 passed`.

## v0.1.4 — GitHub Action Warrant Gate

- Added a real GitHub Actions warrant gate workflow.
- Added CI, review, rollback report builder scripts for pipeline evidence.
- Added multi-job evidence flow: CI, Security, Review, Rollback, AXIOM Warrant Gate.
- The final GitHub check fails unless AXIOM returns `ALLOW`.
- Preserved proof hygiene: each evidence source emits only proof it owns.

## v0.1.3 — Pipeline Evidence Connectors

- Added GitHub Checks connector for unit and integration test evidence.
- Added GitHub PR Reviews connector for human review evidence.
- Added Rollback connector for rollback availability evidence.
- Added async multi-agent demonstration using asyncio tasks.
- Reinforced proof hygiene: connectors emit only evidence they own.

## v0.1.2 — Semgrep Evidence Connector, Proof Hygiene, and Control Plane API

- Added clean Semgrep connector that emits only scanner-owned evidence.
- Added Proof Router for merging partial ProofVectors.
- Added FastAPI `POST /v1/warrants/evaluate`.
- Added CLI commands `semgrep-proof` and `merge-proof`.
- Added Semgrep scan examples and partial/merged ProofVectors.
- Added tests for proof hygiene, dynamic freshness, CLI subprocess `PYTHONPATH`, API evaluation, and Semgrep-driven decisions.
- Updated requirements for FastAPI/uvicorn/httpx.
- Test suite: `16 passed`.

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
