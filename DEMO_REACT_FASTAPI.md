# AXIOM FastAPI + React Demo

This demo is built on the principle:

```text
Real core, simulated arteries.
```

The backend runs real AXIOM logic: source verification, deterministic policy evaluation, signed warrant generation, and ledger preview.

The enterprise systems are simulated: Jira, GitHub, CI/CD, Semgrep, rollback plan and deployment window.

## Architecture

```text
React Demo UI
    ↓
FastAPI axiom.demo_api
    ↓
Mock Source Bundles
    ↓
AXIOM Source Verifiers
    ↓
Policy Kernel
    ↓
Execution Warrant
    ↓
Proof Ledger Preview
```

## Run

```bash
pip install -r requirements.txt
pip install uvicorn
PYTHONPATH=reference/python uvicorn axiom.demo_api:app --reload --port 8000
```

```bash
cd demo-ui
npm install
npm run dev
```

Open:

```text
http://localhost:5173
```

## Scenarios

- `ALLOW`: all required evidence is verified at source.
- `SUSPEND`: rollback proof is missing.
- `BLOCK`: security scan contains a critical finding.
- `SUSPEND`: change ticket is not approved.

## Demo disclaimer

Use this sentence during the demo:

> In this demo, enterprise systems are simulated to keep the setup fast. The AXIOM core is real: it normalizes the action, verifies evidence at the source, applies policy, generates a signed warrant, and prepares the ledger record.


## Docker deployment

See `DEPLOY_AXIOM_DEMO.md`.
