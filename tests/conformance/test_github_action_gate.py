from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
PYTHON = sys.executable


def run_script(*args: str) -> None:
    result = subprocess.run(
        [PYTHON, *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout


def test_github_action_workflow_defines_agent_jobs_and_gate():
    workflow = ROOT / ".github" / "workflows" / "axiom-warrant-gate.yml"
    assert workflow.exists()

    data = yaml.load(workflow.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
    jobs = data["jobs"]

    assert "ci_agent" in jobs
    assert "security_agent" in jobs
    assert "review_agent" in jobs
    assert "rollback_agent" in jobs
    assert "axiom_warrant_gate" in jobs

    gate = jobs["axiom_warrant_gate"]
    assert set(gate["needs"]) == {"ci_agent", "security_agent", "review_agent", "rollback_agent"}

    workflow_text = workflow.read_text(encoding="utf-8")
    assert "No valid Execution Warrant → no merge." in workflow_text
    assert "AXIOM_DECISION" in workflow_text


def test_github_action_ci_report_builder_can_emit_failed_integration(tmp_path: Path):
    out = tmp_path / "ci_report.json"
    run_script(
        "examples/github_action/build_ci_report.py",
        "--out", str(out),
        "--sha", "abc123",
        "--branch", "feature/demo",
        "--unit-status", "success",
        "--integration-status", "failure",
    )

    report = json.loads(out.read_text(encoding="utf-8"))
    checks = {item["name"]: item["conclusion"] for item in report["check_runs"]}
    assert checks["unit tests"] == "success"
    assert checks["integration tests"] == "failure"


def test_github_action_review_report_builder_can_emit_missing_review(tmp_path: Path):
    out = tmp_path / "pr_reviews.json"
    run_script(
        "examples/github_action/build_review_report.py",
        "--out", str(out),
        "--sha", "abc123",
        "--branch", "feature/demo",
        "--pr-number", "42",
        "--scenario", "require_human_review",
    )

    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["pr_number"] == "42"
    assert report["reviews"] == []


def test_github_action_rollback_report_builder_can_emit_missing_rollback(tmp_path: Path):
    out = tmp_path / "rollback_plan.json"
    run_script(
        "examples/github_action/build_rollback_report.py",
        "--out", str(out),
        "--sha", "abc123",
        "--branch", "feature/demo",
        "--scenario", "rollback_missing",
    )

    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["available"] is False
    assert report["verified"] is False
