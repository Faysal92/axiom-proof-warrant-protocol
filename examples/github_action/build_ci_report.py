#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def normalize_outcome(value: str | None) -> str:
    value = (value or "success").lower()
    if value in {"success", "passed", "pass", "ok"}:
        return "success"
    if value in {"failure", "failed", "fail", "error", "cancelled", "skipped"}:
        return "failure"
    return value


def check_run(name: str, outcome: str, run_id: str) -> dict:
    conclusion = normalize_outcome(outcome)
    return {
        "id": run_id,
        "name": name,
        "status": "completed",
        "conclusion": conclusion,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a GitHub check-runs-style report for AXIOM.")
    parser.add_argument("--out", required=True)
    parser.add_argument("--target", default="payment-api")
    parser.add_argument("--sha", default="unknown")
    parser.add_argument("--branch", default="main")
    parser.add_argument("--unit-status", default="success")
    parser.add_argument("--integration-status", default="success")
    parser.add_argument("--unit-run-id", default="unit-tests")
    parser.add_argument("--integration-run-id", default="integration-tests")
    args = parser.parse_args()

    report = {
        "target": args.target,
        "head_sha": args.sha,
        "branch": args.branch,
        "check_runs": [
            check_run("unit tests", args.unit_status, args.unit_run_id),
            check_run("integration tests", args.integration_status, args.integration_run_id),
        ],
    }

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"CI report written to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
