#!/usr/bin/env bash
set -euo pipefail

echo "Docker containers:"
docker compose ps

echo "FastAPI health:"
curl -fsS http://127.0.0.1:8001/health && echo

echo "Frontend health:"
curl -fsS http://127.0.0.1:8081/ >/dev/null && echo "frontend ok"

echo "Demo API scenarios:"
curl -fsS http://127.0.0.1:8001/v1/demo/scenarios | head -c 500 && echo
