import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .crypto import sha256_hex

def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

def _last_hash(path: Path) -> str:
    if not path.exists():
        return "GENESIS"
    lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not lines:
        return "GENESIS"
    return json.loads(lines[-1]).get("current_hash", "GENESIS")

def append_ledger_entry(
    ledger_path: Path,
    warrant: dict,
    reason: Optional[str] = None,
) -> dict:
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    previous_hash = _last_hash(ledger_path)

    entry = {
        "entry_id": "ktx_" + warrant["warrant_id"].replace("wrn_", ""),
        "entry_type": "WARRANT_DECISION",
        "warrant_id": warrant["warrant_id"],
        "actor": warrant.get("actor", {}).get("actor_id"),
        "action": warrant.get("action", {}).get("action_type"),
        "target": warrant.get("action", {}).get("target"),
        "decision": warrant.get("decision"),
        "reason": reason or warrant.get("reason"),
        "missing_evidence": warrant.get("missing_evidence", []),
        "timestamp": utc_now(),
        "previous_hash": previous_hash,
    }
    entry["current_hash"] = sha256_hex(entry)

    with ledger_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, sort_keys=True, ensure_ascii=False) + "\n")

    return entry

def verify_ledger(ledger_path: Path) -> bool:
    if not ledger_path.exists():
        return True

    previous = "GENESIS"
    for line in ledger_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        entry = json.loads(line)
        if entry.get("previous_hash") != previous:
            return False
        current = entry.get("current_hash")
        unsigned = dict(entry)
        unsigned.pop("current_hash", None)
        if sha256_hex(unsigned) != current:
            return False
        previous = current
    return True
