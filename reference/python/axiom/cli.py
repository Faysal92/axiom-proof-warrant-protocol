from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml

from .connectors.semgrep import semgrep_to_partial_proof_vector, write_proof_vector
from .connectors.github_checks import github_checks_to_partial_proof_vector
from .connectors.github_reviews import github_reviews_to_partial_proof_vector
from .connectors.rollback import rollback_to_partial_proof_vector
from .crypto import verify_signature
from .evaluator import evaluate
from .ledger import append_ledger_entry, verify_ledger
from .proof_router import merge_proof_vectors
from .evidence.canonical import load_canonical_evidence, canonical_events_to_proof_vector
from .evidence.adapters import ci_checks as generic_ci_checks
from .evidence.adapters import human_review as generic_human_review
from .source_verification import evaluate_action_request


def load_json(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_yaml(path: str | Path) -> dict:
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))


def cmd_eval(args: argparse.Namespace) -> int:
    action = load_json(args.action)
    proof = load_json(args.proof)
    policy = load_yaml(args.policy)

    warrant = evaluate(action=action, proof_vector=proof, policy=policy)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(warrant, indent=2, ensure_ascii=False), encoding="utf-8")

    if args.ledger:
        append_ledger_entry(Path(args.ledger), warrant)

    print(f"Decision: {warrant['decision']}")
    print(f"Reason: {warrant['reason']}")

    if warrant["missing_evidence"]:
        print("Missing evidence:")
        for item in warrant["missing_evidence"]:
            print(f"- {item}")

    challenge = warrant.get("challenge", {})
    if challenge.get("next_actions"):
        print("Next actions:")
        for item in challenge["next_actions"]:
            print(f"- {item}")

    print(f"Warrant written to: {out_path}")
    return 0


def cmd_verify(args: argparse.Namespace) -> int:
    warrant = load_json(args.warrant)
    ok = verify_signature(warrant)
    print("VALID" if ok else "INVALID")
    return 0 if ok else 1


def cmd_ledger_verify(args: argparse.Namespace) -> int:
    ok = verify_ledger(Path(args.ledger))
    print("LEDGER VALID" if ok else "LEDGER INVALID")
    return 0 if ok else 1


def cmd_semgrep_proof(args: argparse.Namespace) -> int:
    proof_vector = semgrep_to_partial_proof_vector(
        args.report,
        target=args.target,
        environment=args.environment,
        commit=args.commit,
        branch=args.branch,
        service=args.service,
    )
    write_proof_vector(proof_vector, args.out)
    print(f"Partial Semgrep ProofVector written to: {args.out}")
    print(f"security_scan_clean: {proof_vector['dimensions']['security_scan_clean']['status']}")
    return 0


def cmd_github_checks_proof(args: argparse.Namespace) -> int:
    proof_vector = github_checks_to_partial_proof_vector(
        args.report,
        target=args.target,
        environment=args.environment,
        commit=args.commit,
        branch=args.branch,
        service=args.service,
    )
    write_proof_vector(proof_vector, args.out)
    print(f"Partial GitHub Checks ProofVector written to: {args.out}")
    for key, value in proof_vector.get("dimensions", {}).items():
        print(f"{key}: {value.get('status') if isinstance(value, dict) else value}")
    return 0


def cmd_github_reviews_proof(args: argparse.Namespace) -> int:
    proof_vector = github_reviews_to_partial_proof_vector(
        args.report,
        target=args.target,
        environment=args.environment,
        commit=args.commit,
        branch=args.branch,
        service=args.service,
    )
    write_proof_vector(proof_vector, args.out)
    print(f"Partial GitHub Reviews ProofVector written to: {args.out}")
    review = proof_vector["dimensions"]["human_reviewed"]
    print(f"human_reviewed: {review['status']}")
    return 0




def cmd_ci_proof(args: argparse.Namespace) -> int:
    """Provider-agnostic CI proof command.

    Supports GitHub Actions, GitLab Pipelines, Jenkins-style JSON, or any
    compatible report shape. The adapter emits only CI-owned proof dimensions.
    """
    proof_vector = generic_ci_checks.from_report(
        args.report,
        target=args.target,
        environment=args.environment,
        commit=args.commit,
        branch=args.branch,
        service=args.service,
    )
    write_proof_vector(proof_vector, args.out)
    print(f"Partial CI ProofVector written to: {args.out}")
    for key, value in proof_vector.get("dimensions", {}).items():
        print(f"{key}: {value.get('status') if isinstance(value, dict) else value}")
    return 0


def cmd_review_proof(args: argparse.Namespace) -> int:
    """Provider-agnostic human review proof command.

    Supports GitHub PR reviews, GitLab MR approvals, and compatible approval
    JSON. The adapter emits only the human_reviewed proof dimension.
    """
    proof_vector = generic_human_review.from_report(
        args.report,
        target=args.target,
        environment=args.environment,
        commit=args.commit,
        branch=args.branch,
        service=args.service,
    )
    write_proof_vector(proof_vector, args.out)
    print(f"Partial Review ProofVector written to: {args.out}")
    review = proof_vector["dimensions"].get("human_reviewed", {})
    print(f"human_reviewed: {review.get('status') if isinstance(review, dict) else review}")
    return 0


def cmd_rollback_proof(args: argparse.Namespace) -> int:
    proof_vector = rollback_to_partial_proof_vector(
        args.report,
        target=args.target,
        environment=args.environment,
        commit=args.commit,
        branch=args.branch,
        service=args.service,
    )
    write_proof_vector(proof_vector, args.out)
    print(f"Partial Rollback ProofVector written to: {args.out}")
    rollback = proof_vector["dimensions"]["rollback_available"]
    print(f"rollback_available: {rollback['status']}")
    return 0


def cmd_merge_proof(args: argparse.Namespace) -> int:
    vectors = [load_json(path) for path in args.proof]
    merged = merge_proof_vectors(*vectors)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(merged, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"Merged ProofVector written to: {out_path}")
    return 0



def cmd_evidence_proof(args: argparse.Namespace) -> int:
    events = load_canonical_evidence(args.evidence)
    proof_vector = canonical_events_to_proof_vector(events)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(proof_vector, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"Canonical Evidence ProofVector written to: {out_path}")
    print(f"events: {len(events)}")
    print(f"dimensions: {', '.join(sorted(proof_vector.get('dimensions', {}).keys()))}")
    return 0


def cmd_evidence_eval(args: argparse.Namespace) -> int:
    action = load_json(args.action)
    events = load_canonical_evidence(args.evidence)
    proof_vector = canonical_events_to_proof_vector(events)
    policy = load_yaml(args.policy)

    warrant = evaluate(action=action, proof_vector=proof_vector, policy=policy)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(warrant, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    if args.proof_out:
        proof_out = Path(args.proof_out)
        proof_out.parent.mkdir(parents=True, exist_ok=True)
        proof_out.write_text(json.dumps(proof_vector, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    if args.ledger:
        append_ledger_entry(Path(args.ledger), warrant)

    print(f"Decision: {warrant['decision']}")
    print(f"Reason: {warrant['reason']}")
    if warrant.get("missing_evidence"):
        print("Missing evidence:")
        for item in warrant["missing_evidence"]:
            print(f"- {item}")
    print(f"Warrant written to: {out_path}")
    return 0


def cmd_verify_action(args: argparse.Namespace) -> int:
    """Evaluate an ActionEnvelope by verifying agent claims at their sources first."""
    action_request = load_json(args.action_request)
    sources = load_json(args.sources)
    policy = load_yaml(args.policy)

    result = evaluate_action_request(
        action_request=action_request,
        sources=sources,
        policy=policy,
        ledger_path=args.ledger,
    )

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result["warrant"], indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    if args.proof_out:
        proof_path = Path(args.proof_out)
        proof_path.parent.mkdir(parents=True, exist_ok=True)
        proof_path.write_text(json.dumps(result["proof_vector"], indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    if args.verified_out:
        verified_path = Path(args.verified_out)
        verified_path.parent.mkdir(parents=True, exist_ok=True)
        verified_path.write_text(json.dumps(result["verified_evidence"], indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    warrant = result["warrant"]
    print(f"Decision: {warrant['decision']}")
    print(f"Reason: {warrant['reason']}")
    if warrant.get("missing_evidence"):
        print("Missing evidence:")
        for item in warrant["missing_evidence"]:
            print(f"- {item}")
    print(f"Verified claims: {len(result['verified_evidence'])}")
    print(f"Warrant written to: {out_path}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="axiom", description="AXIOM Proof Warrant Protocol reference CLI")
    sub = parser.add_subparsers(required=True)

    p_eval = sub.add_parser("eval", help="Evaluate an action and emit an Execution Warrant")
    p_eval.add_argument("--action", required=True)
    p_eval.add_argument("--proof", required=True)
    p_eval.add_argument("--policy", required=True)
    p_eval.add_argument("--out", required=True)
    p_eval.add_argument("--ledger", default="data/ledger.jsonl")
    p_eval.set_defaults(func=cmd_eval)

    p_verify = sub.add_parser("verify", help="Verify a warrant signature")
    p_verify.add_argument("--warrant", required=True)
    p_verify.set_defaults(func=cmd_verify)

    p_ledger = sub.add_parser("ledger-verify", help="Verify JSONL ledger hash chain")
    p_ledger.add_argument("--ledger", default="data/ledger.jsonl")
    p_ledger.set_defaults(func=cmd_ledger_verify)

    p_semgrep = sub.add_parser("semgrep-proof", help="Convert a Semgrep JSON report into a partial AXIOM ProofVector")
    p_semgrep.add_argument("--report", required=True)
    p_semgrep.add_argument("--out", required=True)
    p_semgrep.add_argument("--target", default="payment-api")
    p_semgrep.add_argument("--environment", default="production")
    p_semgrep.add_argument("--commit", default="unknown")
    p_semgrep.add_argument("--branch", default="main")
    p_semgrep.add_argument("--service", default=None)
    p_semgrep.set_defaults(func=cmd_semgrep_proof)

    p_checks = sub.add_parser("github-checks-proof", help="Convert GitHub check runs into a partial AXIOM ProofVector")
    p_checks.add_argument("--report", required=True)
    p_checks.add_argument("--out", required=True)
    p_checks.add_argument("--target", default="payment-api")
    p_checks.add_argument("--environment", default="production")
    p_checks.add_argument("--commit", default=None)
    p_checks.add_argument("--branch", default=None)
    p_checks.add_argument("--service", default=None)
    p_checks.set_defaults(func=cmd_github_checks_proof)

    p_reviews = sub.add_parser("github-reviews-proof", help="Convert GitHub PR reviews into a partial AXIOM ProofVector")
    p_reviews.add_argument("--report", required=True)
    p_reviews.add_argument("--out", required=True)
    p_reviews.add_argument("--target", default="payment-api")
    p_reviews.add_argument("--environment", default="production")
    p_reviews.add_argument("--commit", default=None)
    p_reviews.add_argument("--branch", default=None)
    p_reviews.add_argument("--service", default=None)
    p_reviews.set_defaults(func=cmd_github_reviews_proof)

    p_rollback = sub.add_parser("rollback-proof", help="Convert a rollback plan artifact into a partial AXIOM ProofVector")
    p_rollback.add_argument("--report", required=True)
    p_rollback.add_argument("--out", required=True)
    p_rollback.add_argument("--target", default="payment-api")
    p_rollback.add_argument("--environment", default="production")
    p_rollback.add_argument("--commit", default=None)
    p_rollback.add_argument("--branch", default=None)
    p_rollback.add_argument("--service", default=None)
    p_rollback.set_defaults(func=cmd_rollback_proof)


    p_ci = sub.add_parser("ci-proof", help="Convert provider-agnostic CI output into a partial AXIOM ProofVector")
    p_ci.add_argument("--report", required=True)
    p_ci.add_argument("--out", required=True)
    p_ci.add_argument("--target", default="payment-api")
    p_ci.add_argument("--environment", default="production")
    p_ci.add_argument("--commit", default=None)
    p_ci.add_argument("--branch", default=None)
    p_ci.add_argument("--service", default=None)
    p_ci.set_defaults(func=cmd_ci_proof)

    p_review = sub.add_parser("review-proof", help="Convert provider-agnostic human review output into a partial AXIOM ProofVector")
    p_review.add_argument("--report", required=True)
    p_review.add_argument("--out", required=True)
    p_review.add_argument("--target", default="payment-api")
    p_review.add_argument("--environment", default="production")
    p_review.add_argument("--commit", default=None)
    p_review.add_argument("--branch", default=None)
    p_review.add_argument("--service", default=None)
    p_review.set_defaults(func=cmd_review_proof)

    p_merge = sub.add_parser("merge-proof", help="Merge partial ProofVectors into one consolidated ProofVector")
    p_merge.add_argument("--proof", action="append", required=True, help="Path to a partial ProofVector. Can be repeated.")
    p_merge.add_argument("--out", required=True)
    p_merge.set_defaults(func=cmd_merge_proof)

    p_evidence = sub.add_parser("evidence-proof", help="Convert provider-agnostic canonical evidence JSON/JSONL into an AXIOM ProofVector")
    p_evidence.add_argument("--evidence", required=True, help="Path to a Canonical Evidence Event object, events array, or JSONL file")
    p_evidence.add_argument("--out", required=True)
    p_evidence.set_defaults(func=cmd_evidence_proof)

    p_evidence_eval = sub.add_parser("evidence-eval", help="Evaluate an action directly from canonical evidence JSON/JSONL")
    p_evidence_eval.add_argument("--action", required=True)
    p_evidence_eval.add_argument("--evidence", required=True)
    p_evidence_eval.add_argument("--policy", required=True)
    p_evidence_eval.add_argument("--out", required=True)
    p_evidence_eval.add_argument("--proof-out", default=None)
    p_evidence_eval.add_argument("--ledger", default="data/ledger.jsonl")
    p_evidence_eval.set_defaults(func=cmd_evidence_eval)


    p_verify_action = sub.add_parser(
        "verify-action",
        help="Verify agent claims at source, build a ProofVector, and emit an Execution Warrant",
    )
    p_verify_action.add_argument("--action-request", required=True)
    p_verify_action.add_argument("--sources", required=True, help="Local source bundle used by MVP source verifiers")
    p_verify_action.add_argument("--policy", required=True)
    p_verify_action.add_argument("--out", required=True)
    p_verify_action.add_argument("--proof-out", default=None)
    p_verify_action.add_argument("--verified-out", default=None)
    p_verify_action.add_argument("--ledger", default="data/source_verified_ledger.jsonl")
    p_verify_action.set_defaults(func=cmd_verify_action)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
