import hashlib
import hmac
import json
from typing import Any

DEFAULT_DEV_SECRET = "axiom-dev-secret-change-me"

def canonical_json(data: Any) -> bytes:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")

def sha256_hex(data: Any) -> str:
    if isinstance(data, bytes):
        payload = data
    else:
        payload = canonical_json(data)
    return "sha256:" + hashlib.sha256(payload).hexdigest()

def sign_payload(payload: dict, secret: str = DEFAULT_DEV_SECRET) -> dict:
    unsigned = dict(payload)
    unsigned.pop("signature", None)
    digest = hmac.new(secret.encode("utf-8"), canonical_json(unsigned), hashlib.sha256).hexdigest()
    return {
        "algorithm": "HMAC-SHA256",
        "key_id": "dev",
        "value": digest,
    }

def verify_signature(payload: dict, secret: str = DEFAULT_DEV_SECRET) -> bool:
    signature = payload.get("signature") or {}
    expected = sign_payload(payload, secret=secret)
    return hmac.compare_digest(signature.get("value", ""), expected["value"])
