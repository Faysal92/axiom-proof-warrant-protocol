from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml

from .crypto import verify_signature
from .evaluator import evaluate
from .ledger import append_ledger_entry, verify_ledger


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

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
