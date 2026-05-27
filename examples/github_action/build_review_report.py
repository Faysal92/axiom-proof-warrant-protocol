#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import urllib.request
from pathlib import Path


def github_api_get_reviews(repo: str, pr_number: str, token: str) -> list[dict]:
    url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}/reviews"
    request = urllib.request.Request(url)
    request.add_header("Accept", "application/vnd.github+json")
    request.add_header("Authorization", f"Bearer {token}")
    request.add_header("X-GitHub-Api-Version", "2022-11-28")
    with urllib.request.urlopen(request, timeout=20) as response:  # noqa: S310 - explicit GitHub API endpoint
        payload = response.read().decode("utf-8")
    reviews = json.loads(payload)
    if not isinstance(reviews, list):
        return []
    return reviews


def synthetic_reviews(scenario: str, pr_number: str) -> list[dict]:
    if scenario == "require_human_review":
        return []
    return [
        {
            "id": "review-axiom-demo-1",
            "state": "APPROVED",
            "user": "axiom-review-agent@example.com",
            "submitted_at": "2026-05-24T17:30:00Z",
        }
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a GitHub PR reviews-style report for AXIOM.")
    parser.add_argument("--out", required=True)
    parser.add_argument("--target", default="payment-api")
    parser.add_argument("--sha", default="unknown")
    parser.add_argument("--branch", default="main")
    parser.add_argument("--pr-number", default="0")
    parser.add_argument("--scenario", default="allow")
    parser.add_argument("--live", action="store_true", help="Fetch live PR reviews from GitHub API using GITHUB_TOKEN.")
    args = parser.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    repo = os.environ.get("GITHUB_REPOSITORY")

    reviews: list[dict]
    if args.live and token and repo and args.pr_number not in {"", "0", "None", "null"}:
        reviews = github_api_get_reviews(repo, args.pr_number, token)
    else:
        reviews = synthetic_reviews(args.scenario, args.pr_number)

    report = {
        "target": args.target,
        "head_sha": args.sha,
        "branch": args.branch,
        "pr_number": args.pr_number,
        "reviews": reviews,
    }

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"PR review report written to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
