"""Fixed profile constants for HCE SVR-P1A1-DISCOVERY/v1 — not caller-overridable."""

from __future__ import annotations

PROFILE = "SVR-P1A1-DISCOVERY/v1"
FEATURE_ID = "sync-vps-runtime"
PARENT_PACKAGE_ID = "SVR-P1A1-DISCOVERY"
CHILD_A_PACKAGE_ID = "SVR-P1A1A-TS-RESOLVER"
CHILD_B_PACKAGE_ID = "SVR-P1A1B-STRUCTURAL-DISCOVERY"
SCHEMA = "set-agentes.convergence-exception/v1"

PATH_RESOLVER = "scripts/sync-vps/typescript-dispatch-resolver.ts"
PATH_RESOLVER_TEST = "scripts/sync-vps/__tests__/typescript-dispatch-resolver.test.ts"
PATH_DISCOVERY = "scripts/sync-vps/source-discovery.ts"
PATH_DISCOVERY_TEST = "scripts/sync-vps/__tests__/source-discovery.test.ts"

FOUR_PATH_UNION = [
    PATH_RESOLVER,
    PATH_RESOLVER_TEST,
    PATH_DISCOVERY,
    PATH_DISCOVERY_TEST,
]

PROFILE_SOURCE_ROOT = "scripts/sync-vps"

FINDING_MAP = [
    {"child_package_id": CHILD_A_PACKAGE_ID, "finding_ids": ["SVR-P1A1-002", "SVR-P1A1-003", "SVR-P1A1-004", "SVR-P1A1-006"]},
    {"child_package_id": CHILD_B_PACKAGE_ID, "finding_ids": ["SVR-P1A1-001", "SVR-P1A1-005", "SVR-P1A1-007", "SVR-P1A1-008", "SVR-P1A1-009", "SVR-P1A1-010"]},
]

OWNERSHIP_SNAPSHOT = [
    {"child_package_id": CHILD_A_PACKAGE_ID, "owned_paths": [PATH_RESOLVER, PATH_RESOLVER_TEST]},
    {"child_package_id": CHILD_B_PACKAGE_ID, "owned_paths": [PATH_DISCOVERY, PATH_DISCOVERY_TEST]},
]

ALL_FINDING_IDS = sorted(
    fid for entry in FINDING_MAP for fid in entry["finding_ids"]
)

CIRCULAR_TASK = (
    "Converge accepted TypeScript resolver and structural discovery children "
    "with full final panel and all ten original finding closures"
)

ORIGINAL_CHANGED_LINES = 336
BUDGET_LINES = 168
CAP_SOURCE = "complexity:high"

HCE_COMMANDS = frozenset({
    "prepare-convergence",
    "reenter-convergence",
    "authorize-convergence",
    "inspect-convergence",
    "consume-convergence",
    "verify-convergence-outcome",
})
