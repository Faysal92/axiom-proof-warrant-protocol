from enum import Enum

class Decision(str, Enum):
    ALLOW = "ALLOW"
    CONDITIONAL = "CONDITIONAL"
    SUSPEND = "SUSPEND"
    REQUIRE_HUMAN_REVIEW = "REQUIRE_HUMAN_REVIEW"
    BLOCK = "BLOCK"

class DimensionState(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    MISSING = "missing"
    UNKNOWN = "unknown"

PROOF_LEVEL_ORDER = {
    "P0_UNSUPPORTED": 0,
    "P1_PLAUSIBLE": 1,
    "P2_SOURCE_BACKED": 2,
    "P3_CROSS_CHECKED": 3,
    "P4_EXECUTED": 4,
    "P5_AUDITED": 5,
}
