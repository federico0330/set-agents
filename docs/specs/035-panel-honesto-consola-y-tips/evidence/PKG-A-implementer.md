# PKG-A implementer evidence — spawn 2/8

Feature: `035-panel-honesto-consola-y-tips` · Package: PKG-A · Writer: implementer / composer-2.5  
Tasks: T-002 through T-010 · strict-TDD ON

## Status

```json
{
  "package_id": "PKG-A",
  "status": "implemented",
  "completed_tasks": ["T-002", "T-003", "T-004", "T-005", "T-006", "T-007", "T-008", "T-009", "T-010"],
  "changed_files": [
    "ai/scripts/feature_state_lib/model.py",
    "ai/scripts/feature_state_lib/cli_review.py",
    "ai/scripts/feature_state_lib/transitions.py",
    "PROYECTO/ai/scripts/feature_state_lib/model.py",
    "PROYECTO/ai/scripts/feature_state_lib/cli_review.py",
    "PROYECTO/ai/scripts/feature_state_lib/transitions.py",
    "Global/_canonical/agents/orchestrator.md",
    "Global/*/hooks/feature_state_lib/* (regenerated)",
    "Global/*/agents/orchestrator.md (regenerated)",
    "Global/codex/agents/orchestrator.toml (regenerated)",
    "tests/test_harness.py"
  ],
  "acs_covered": ["AC-A.1", "AC-A.2", "AC-A.3", "AC-A.4", "AC-A.5", "AC-A.6", "AC-A.7", "AC-A.9"],
  "tests_run": [
    "python3 -m unittest tests.test_harness",
    "python3 -m unittest tests.test_honest_predicate tests.test_narracion_contrato",
    "./build.sh --check",
    "./ai/scripts/verify.sh"
  ],
  "tests_passed": ["all above green"],
  "tests_failed": [],
  "assumptions": [
    "ADR-0065 already Accepted; not edited",
    "package_accept_ready membership unchanged (DEC-LEGACY)",
    "record-repair --skip-delta untouched (no-goal 12)",
    "T-006: no 8th medium/high record-review site found beyond the 7 documented bite sites"
  ],
  "known_risks": [
    "AC-A.8 (spawn budget on FULL panel) not exercised in this spawn — pre-existing HUMAN_DECISION_REQUIRED path",
    "AC-A.6 historical validation relies on guard not being in read/validation paths — confirmed via verify.sh only"
  ],
  "blockers": []
}
```

## New helpers (file:line, both trees identical)

| symbol | location |
|---|---|
| `BLOCKING_SEVERITIES` | `ai/scripts/feature_state_lib/model.py:97` |
| `resolved_required_reviewers` | `ai/scripts/feature_state_lib/model.py:587-602` |
| `_roles_without_subreview` | `ai/scripts/feature_state_lib/cli_review.py:21-28` |
| `require_review_panel` | `ai/scripts/feature_state_lib/cli_review.py:31-47` |
| `require_no_blocking_findings` | `ai/scripts/feature_state_lib/cli_review.py:58-70` |
| `require_review_panel` call site | `cli_review.py:82` (after `package_review_ready`, before budget check) |
| `require_no_blocking_findings` call site | `cli_review.py:108` (pass arm, after finding merge) |
| `finalize-review-panel` literal → name | `cli_review.py:213` uses `model.BLOCKING_SEVERITIES` |

## strict-TDD evidence

Safety net before new guards: `tests/test_harness.py` golden suite (615 tests) exercising the
real `PROYECTO/ai/scripts/feature-state.py` CLI — especially the seven documented bite sites
(§ Bite rewrites below), `test_accept_package_rejects_open_findings_and_bad_actors`, and
pre-existing `record-review` / `finalize-review-panel` paths in `cli_review.py` and
`model.py:package_review_ready`.

### Guard: REVIEW_PANEL_REQUIRED (AC-A.1) — T-002, T-003

```json
{
  "task_id": "T-002/T-003",
  "test_file": "tests/test_harness.py",
  "layer": "integration",
  "safety_net": "tests/test_harness.py golden suite + cli_review.py:cmd_record_review pre-guard path + 7 bite sites",
  "red": true,
  "green": true,
  "triangulate": "6 cases: medium pass, repair_required on FULL, absent key, explicit null, empty list, blank elements, complexity unset",
  "refactor": "none needed"
}
```

### Guard: BLOCKING_FINDING_OPEN (AC-A.4) — T-004

```json
{
  "task_id": "T-004",
  "test_file": "tests/test_harness.py",
  "layer": "integration",
  "safety_net": "cli_review.py:finalize-review-panel has_open_findings (line 213) + test_accept_package_rejects_open_findings_and_bad_actors",
  "red": true,
  "green": true,
  "triangulate": "test_record_review_pass_rejects_blocking_finding; skip-delta door preserved in test_next_advisor_fires_for_skip_delta_door_with_open_finding",
  "refactor": "require_no_blocking_findings uses has_open_findings as rejection condition (PKG-A-repair F001)"
}
```

### Bite rewrites — T-005, T-006

```json
{
  "task_id": "T-005/T-006",
  "test_file": "tests/test_harness.py",
  "layer": "integration",
  "safety_net": "same golden suite; each rewritten test preserves its original assertion",
  "red": true,
  "green": true,
  "triangulate": "7 bite sites enumerated in acceptance.md § Mordida",
  "refactor": "none needed"
}
```

### Advisor comment — T-007

```json
{
  "task_id": "T-007",
  "test_file": "tests/test_harness.py",
  "layer": "integration",
  "safety_net": "test_next_advisor_fires_for_skip_delta_door_with_open_finding + transitions.py advisor branch",
  "red": false,
  "green": true,
  "triangulate": "comment names record-repair --skip-delta door; branch still reachable",
  "refactor": "none needed"
}
```

### Parity / doctrine — T-008, T-010

```json
{
  "task_id": "T-008/T-010",
  "test_file": "N/A (build.sh --check + rg verification)",
  "layer": "build",
  "safety_net": "build.sh SELF_SCAFFOLD_DRIFT cmp + generate.py copytree",
  "red": false,
  "green": true,
  "triangulate": "23-file scaffold sync; orchestrator doctrine grep clean",
  "refactor": "none needed"
}
```

**RED** (unpatched `PROYECTO/ai/scripts/feature_state_lib/*`, restored from `/tmp/pkg-a-backup/`):

```
$ python3 -m unittest tests.test_harness.HarnessTests.test_record_review_rejects_full_panel_membership \
    tests.test_harness.HarnessTests.test_record_review_pass_rejects_blocking_finding \
    tests.test_harness.HarnessTests.test_record_review_small_low_still_passes
FF.
FAIL: test_record_review_rejects_full_panel_membership
AssertionError: 0 != 2
FAIL: test_record_review_pass_rejects_blocking_finding
AssertionError: 0 != 2
Ran 3 tests in 9.761s — FAILED (failures=2)
```

**GREEN** (after guards in both trees):

```
$ python3 -m unittest tests.test_harness.HarnessTests.test_record_review_rejects_full_panel_membership \
    tests.test_harness.HarnessTests.test_record_review_repair_required_on_full_panel_also_rejected \
    tests.test_harness.HarnessTests.test_record_review_small_low_still_passes \
    tests.test_harness.HarnessTests.test_record_review_rejects_when_required_reviewers_absent \
    tests.test_harness.HarnessTests.test_record_review_rejects_when_required_reviewers_null \
    tests.test_harness.HarnessTests.test_record_review_rejects_when_complexity_unset \
    tests.test_harness.HarnessTests.test_record_review_pass_rejects_blocking_finding \
    tests.test_harness.HarnessTests.test_next_advisor_fires_for_skip_delta_door_with_open_finding
........
Ran 8 tests in 13.020s — OK
```

### Guard: BLOCKING_FINDING_OPEN (AC-A.4)

Covered in RED/GREEN above (`test_record_review_pass_rejects_blocking_finding`).

## Bite rewrites (7 sites)

| # | line (approx) | test | change |
|---|---|---|---|
| 1 | 8662 | `test_done_ready_reaches_done_after_a_real_block_and_reopen_cycle` | `full_panel_pass` |
| 2 | 10252 | `test_non_runtime_package_accepts_without_runtime_qa` | `full_panel_pass` in `drive_to_testing` |
| 3 | 12581 | `test_record_repair_commit_fail_open_when_git_cannot_answer` | `full_panel_repair_required_run` |
| 4 | 12633 | `test_record_repair_commit_accepted_when_git_verifies_it` | `full_panel_repair_required_run` |
| 5 | 13188 | `test_record_repair_commit_fail_open_in_real_shallow_clone` | `full_panel_repair_required_run` |
| 6 | split | `test_record_review_pass_rejects_blocking_finding` + `test_next_advisor_fires_for_skip_delta_door_with_open_finding` | replaces `test_next_does_not_blame_a_late_review_that_never_happened` |
| 7 | 11226 | `test_accept_package_rejects_open_findings_and_bad_actors` | legal setup via skip-delta leaving F-001 open |

## grep verification

```
$ rg -n "record-review is outside this package" ai/scripts PROYECTO/ai/scripts Global
(no matches)

$ rg -n "when multiple specialist reviewers are useful" Global/
(no matches)
```

## build.sh --check (post-regeneration)

```
SELF_SCAFFOLD_SYNC_OK files=23
GLOBAL_TREE_SYNC_OK harnesses=5
BUILD_CHECK_PASS
```

## Full suite

```
$ python3 -m unittest tests.test_harness
Ran 615 tests in 795.301s
OK (skipped=2)

$ python3 -m unittest tests.test_honest_predicate tests.test_narracion_contrato
Ran 65 tests in 1.999s
OK

$ ./ai/scripts/verify.sh
(exit 0)
```

## Remaining risks for package-reviewer

- Spawn budget collision on FULL panel (AC-A.8) is documented but not a gate in this spawn.
- `record-repair --skip-delta` door still reachable — advisor branch preserved by design (T-007).
