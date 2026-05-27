from __future__ import annotations
import json, sys, os
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "reference" / "python"))

from axiom.evidence.adapters import semgrep, ci_checks, human_review, rollback, manual
from axiom.evaluator import evaluate
from axiom.proof_router import merge_proof_vectors


def load_json(p): return json.loads(Path(p).read_text(encoding="utf-8"))
def load_yaml(p): return yaml.safe_load(Path(p).read_text(encoding="utf-8"))
def examples(n): return ROOT / "examples" / n
def providers(n): return ROOT / "examples" / "providers" / n

SCOPE = dict(target="payment-api", environment="production", service="payments", branch="main")


# --- Adapter hygiene ---

def test_semgrep_adapter_has_source_block():
    pv = semgrep.from_report(examples("scanners/semgrep_clean_scan.json"), now_epoch=1779100000, **SCOPE)
    assert pv["source"]["provider"] == "semgrep"
    assert pv["source"]["kind"] == "sast_scan"
    assert "security_scan_clean" in pv["dimensions"]
    assert "human_reviewed" not in pv["dimensions"]


def test_ci_checks_adapter_detects_github():
    pv = ci_checks.from_report(examples("github/check_runs_passed.json"), now_epoch=1779100000, **SCOPE)
    assert pv["source"]["provider"] == "github_actions"
    assert "unit_tests_passed" in pv["dimensions"]
    assert "security_scan_clean" not in pv["dimensions"]


def test_ci_checks_adapter_detects_gitlab():
    pv = ci_checks.from_report(providers("gitlab/pipeline_passed.json"), now_epoch=1779100000, **SCOPE)
    assert pv["source"]["provider"] == "gitlab"
    assert "unit_tests_passed" in pv["dimensions"]
    assert "integration_tests_passed" in pv["dimensions"]


def test_human_review_adapter_detects_github():
    pv = human_review.from_report(examples("github/pr_reviews_approved.json"), now_epoch=1779100000, **SCOPE)
    assert pv["source"]["provider"] == "github"
    assert pv["dimensions"]["human_reviewed"]["status"] == "passed"
    assert "security_scan_clean" not in pv["dimensions"]


def test_human_review_adapter_detects_gitlab():
    pv = human_review.from_report(providers("gitlab/mr_approved.json"), now_epoch=1779100000, **SCOPE)
    assert pv["source"]["provider"] == "gitlab"
    assert pv["dimensions"]["human_reviewed"]["status"] == "passed"


def test_manual_adapter_emits_siem_claims():
    pv = manual.from_report(providers("manual/siem_clearance.json"), now_epoch=1779100000, **SCOPE)
    assert pv["source"]["provider"] == "siem"
    assert "security_scan_clean" in pv["dimensions"]
    assert pv["dimensions"]["security_scan_clean"]["status"] == "passed"


def test_manual_adapter_requires_claims():
    import tempfile, pytest
    with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as f:
        json.dump({"provider": "test", "no_claims_here": True}, f)
        path = f.name
    with pytest.raises(ValueError, match="claims"):
        manual.from_report(path)


# --- Full pipeline: GitHub ---

def test_github_pipeline_allow():
    ci  = ci_checks.from_report(examples("github/check_runs_passed.json"), now_epoch=1779100000, **SCOPE)
    rev = human_review.from_report(examples("github/pr_reviews_approved.json"), now_epoch=1779100000, **SCOPE)
    rb  = rollback.from_report(examples("rollback/rollback_plan_available.json"), now_epoch=1779100000, **SCOPE)
    sec = semgrep.from_report(examples("scanners/semgrep_clean_scan.json"), now_epoch=1779100000, commit="abc123", **SCOPE)
    merged = merge_proof_vectors(ci, rev, rb, sec)
    action = load_json(examples("deploy_payment_api.action.json"))
    policy = load_yaml(examples("security_policy.yml"))
    warrant = evaluate(action=action, proof_vector=merged, policy=policy, now_epoch=1779100001)
    assert warrant["decision"] == "ALLOW"


# --- Full pipeline: GitLab ---

def test_gitlab_pipeline_allow():
    ci  = ci_checks.from_report(providers("gitlab/pipeline_passed.json"), now_epoch=1779100000, **SCOPE)
    rev = human_review.from_report(providers("gitlab/mr_approved.json"), now_epoch=1779100000, **SCOPE)
    rb  = rollback.from_report(examples("rollback/rollback_plan_available.json"), now_epoch=1779100000, **SCOPE)
    sec = semgrep.from_report(examples("scanners/semgrep_clean_scan.json"), now_epoch=1779100000, commit="sha456", **SCOPE)
    merged = merge_proof_vectors(ci, rev, rb, sec)
    action = load_json(examples("deploy_payment_api.action.json"))
    policy = load_yaml(examples("security_policy.yml"))
    warrant = evaluate(action=action, proof_vector=merged, policy=policy, now_epoch=1779100001)
    assert warrant["decision"] == "ALLOW"


# --- Manual / SIEM ---

def test_manual_siem_replaces_semgrep():
    ci  = ci_checks.from_report(examples("github/check_runs_passed.json"), now_epoch=1779100000, **SCOPE)
    rev = human_review.from_report(examples("github/pr_reviews_approved.json"), now_epoch=1779100000, **SCOPE)
    rb  = rollback.from_report(examples("rollback/rollback_plan_available.json"), now_epoch=1779100000, **SCOPE)
    sec = manual.from_report(providers("manual/siem_clearance.json"), now_epoch=1779100000, **SCOPE)
    merged = merge_proof_vectors(ci, rev, rb, sec)
    action = load_json(examples("deploy_payment_api.action.json"))
    policy = load_yaml(examples("security_policy.yml"))
    warrant = evaluate(action=action, proof_vector=merged, policy=policy, now_epoch=1779100001)
    assert warrant["decision"] == "ALLOW"


# --- CLI ---

def test_cli_ci_proof_command(tmp_path):
    import subprocess
    out = tmp_path / "ci.pv.json"
    result = subprocess.run(
        [sys.executable, "-m", "axiom.cli", "ci-proof",
         "--report", str(examples("github/check_runs_passed.json")),
         "--out", str(out), "--target", "payment-api", "--environment", "production"],
        cwd=str(ROOT), capture_output=True, text=True,
        env={**os.environ, "PYTHONPATH": str(ROOT / "reference" / "python")},
    )
    assert result.returncode == 0, result.stderr
    pv = json.loads(out.read_text())
    assert "unit_tests_passed" in pv["dimensions"]
    assert pv["source"]["kind"] == "ci_checks"
