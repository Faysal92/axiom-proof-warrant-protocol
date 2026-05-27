# AXIOM React + FastAPI Demo Deployment

This package is deployment-ready for:

```text
axiom.stack-moderne.fr -> React demo UI + FastAPI AXIOM backend
```

## What is real in this demo

- FastAPI backend
- AXIOM source-verification pipeline
- Pydantic schemas
- Policy kernel
- Execution Warrant generation
- Ledger preview

## What is simulated

- Jira
- GitHub reviews
- CI/CD checks
- Security scan
- Rollback plan
- Deployment window

The demo message is:

> Enterprise systems are simulated. The AXIOM decision engine is real.

## 1. DNS

Create this DNS record:

```text
Type: A
Name: axiom
Value: 51.158.123.130
```

Test:

```bash
nslookup axiom.stack-moderne.fr
```

## 2. Server install

On the server:

```bash
cd /opt/axiom-demo
bash deploy/scripts/install_server.sh
```

If the server reports `System restart required`, reboot:

```bash
reboot
```

## 3. Deploy

From the project root:

```bash
cd /opt/axiom-demo
bash deploy/scripts/deploy.sh axiom.stack-moderne.fr
```

When DNS points to the server, enable HTTPS:

```bash
ENABLE_HTTPS=1 bash deploy/scripts/deploy.sh axiom.stack-moderne.fr
```

## 4. Health checks

```bash
bash deploy/scripts/healthcheck.sh
```

Expected:

```text
FastAPI health: {"status":"ok","service":"axiom-demo-api"}
frontend ok
```

## 5. Local Docker commands

```bash
docker compose up -d --build
docker compose logs -f
docker compose down
```

## 6. Public URL

```text
https://axiom.stack-moderne.fr
```

## Security notes for the public demo

- Do not add real Jira/GitHub/AWS secrets.
- Do not expose endpoints that execute real infrastructure actions.
- Keep enterprise sources simulated for the public demo.
- Use real connectors only inside paid/private POCs.
