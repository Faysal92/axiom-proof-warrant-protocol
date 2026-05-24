NEXT_ACTIONS = {
    "unit_tests_passed": "Run unit tests and attach the test logs.",
    "integration_tests_passed": "Run integration tests and attach the test logs.",
    "security_scan_clean": "Run a security scan and attach the scan result.",
    "rollback_available": "Provide and verify a rollback plan.",
    "human_reviewed": "Request human review and attach approval evidence.",
    "stale_evidence": "Refresh evidence and resubmit the ProofVector.",
}

def build_next_actions(missing_evidence: list[str]) -> list[str]:
    actions: list[str] = []
    for item in missing_evidence:
        key = item.split(":", 1)[0]
        actions.append(NEXT_ACTIONS.get(key, f"Provide evidence for: {item}"))
    return actions
