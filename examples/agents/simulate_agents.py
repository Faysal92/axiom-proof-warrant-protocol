from __future__ import annotations

import asyncio
import json
from pathlib import Path
import sys

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "reference" / "python"))

from axiom.connectors.github_checks import github_checks_to_partial_proof_vector
from axiom.connectors.github_reviews import github_reviews_to_partial_proof_vector
from axiom.connectors.rollback import rollback_to_partial_proof_vector
from axiom.connectors.semgrep import semgrep_to_partial_proof_vector
from axiom.evaluator import evaluate
from axiom.proof_router import merge_proof_vectors


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


async def security_agent(report: Path) -> dict:
    await asyncio.sleep(0.05)
    return semgrep_to_partial_proof_vector(
        report,
        target="payment-api",
        environment="production",
        commit="abc123",
        branch="main",
        service="payments",
    )


async def ci_agent(report: Path) -> dict:
    await asyncio.sleep(0.05)
    return github_checks_to_partial_proof_vector(
        report,
        target="payment-api",
        environment="production",
        service="payments",
    )


async def review_agent(report: Path) -> dict:
    await asyncio.sleep(0.05)
    return github_reviews_to_partial_proof_vector(
        report,
        target="payment-api",
        environment="production",
        service="payments",
    )


async def rollback_agent(report: Path) -> dict:
    await asyncio.sleep(0.05)
    return rollback_to_partial_proof_vector(
        report,
        target="payment-api",
        environment="production",
        service="payments",
    )


async def run_agent_scenario(name: str, *, semgrep_report: str, checks_report: str, reviews_report: str, rollback_report: str) -> dict:
    print(f"\n=== {name} ===")

    partials = await asyncio.gather(
        security_agent(ROOT / semgrep_report),
        ci_agent(ROOT / checks_report),
        review_agent(ROOT / reviews_report),
        rollback_agent(ROOT / rollback_report),
    )

    proof_vector = merge_proof_vectors(*partials)
    action = load_json(ROOT / "examples" / "deploy_payment_api.action.json")
    policy = load_yaml(ROOT / "examples" / "security_policy.yml")
    warrant = evaluate(action=action, proof_vector=proof_vector, policy=policy)

    print(f"Decision: {warrant['decision']}")
    print(f"Reason: {warrant['reason']}")
    if warrant.get("missing_evidence"):
        print("Missing evidence:")
        for item in warrant["missing_evidence"]:
            print(f"- {item}")
    return warrant


async def main() -> None:
    await run_agent_scenario(
        "Alice / clean pipeline / expected ALLOW",
        semgrep_report="examples/scanners/semgrep_clean_scan.json",
        checks_report="examples/github/check_runs_passed.json",
        reviews_report="examples/github/pr_reviews_approved.json",
        rollback_report="examples/rollback/rollback_plan_available.json",
    )
    await run_agent_scenario(
        "Bob / failed security scan / expected BLOCK",
        semgrep_report="examples/scanners/semgrep_failed_scan.json",
        checks_report="examples/github/check_runs_passed.json",
        reviews_report="examples/github/pr_reviews_approved.json",
        rollback_report="examples/rollback/rollback_plan_available.json",
    )
    await run_agent_scenario(
        "Charlie / missing human review / expected REQUIRE_HUMAN_REVIEW",
        semgrep_report="examples/scanners/semgrep_clean_scan.json",
        checks_report="examples/github/check_runs_passed.json",
        reviews_report="examples/github/pr_reviews_missing.json",
        rollback_report="examples/rollback/rollback_plan_available.json",
    )


if __name__ == "__main__":
    asyncio.run(main())
