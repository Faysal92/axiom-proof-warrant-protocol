#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a rollback plan report for AXIOM.")
    parser.add_argument("--out", required=True)
    parser.add_argument("--target", default="payment-api")
    parser.add_argument("--environment", default="production")
    parser.add_argument("--sha", default="unknown")
    parser.add_argument("--branch", default="main")
    parser.add_argument("--scenario", default="allow")
    args = parser.parse_args()

    available = args.scenario != "rollback_missing"
    report = {
        "target": args.target,
        "environment": args.environment,
        "commit": args.sha,
        "branch": args.branch,
        "available": available,
        "verified": available,
        "strategy": "blue_green_previous_version" if available else "none",
        "plan_ref": f"rollback_plan:{args.target}:{args.sha}",
    }

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Rollback report written to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
