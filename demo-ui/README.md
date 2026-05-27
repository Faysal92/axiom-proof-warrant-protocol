# AXIOM React Demo UI

This is a local demo UI for AXIOM's proof-of-action tunnel.

The enterprise systems are simulated. The AXIOM backend logic is real:

```text
Raw Agent Context
→ Normalizer
→ Pydantic Schemas
→ Source Verifiers
→ Policy Kernel
→ Execution Warrant
→ Proof Ledger
```

## Run backend

From the repository root:

```bash
pip install -r requirements.txt
pip install uvicorn
PYTHONPATH=reference/python uvicorn axiom.demo_api:app --reload --port 8000
```

## Run frontend

```bash
cd demo-ui
npm install
npm run dev
```

Open:

```text
http://localhost:5173
```

## Demo line

> Votre agent est authentifié, mais son action est-elle prouvée ?
