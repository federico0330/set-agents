# PKG-6 implementer evidence — cuotas-que-alcanzan

Package: PKG-6. Feature: 033-menos-espera-menos-cuota.
Owned: `ai/scripts/feature_state_lib`, `ai/scripts/cost-report.py`.
Exceptions: `ai/scripts/feature-state.py` (`cmd_record_spawn`, `cmd_start_review_panel`), `tests/test_harness.py` (+ four neighbor helpers that write a context-pack stub), this evidence file.
Not touched: `Global/` by hand (regenerated via `./build.sh`), `--route-decide`, `max_deep_review_cycles`, finding-verifier, PKG-1..5 product code, `verify.sh`.
`strict_tdd`: false. Runtime: Cursor. pytest does not exist.

## AC → change → proof

| AC | Change (file:line) | Proof |
|---|---|---|
| AC-6.1 | `check_transition` refuses `PACKAGE_IMPLEMENTATION` without the pack (`transitions.py:21-24` → `context_pack_errors` `model.py:509-531`). Canonical path is sibling of `approved_spec.path`: `…/context/<PKG>.md`. | `test_package_implementation_requires_a_context_pack_file` OK. Bite: remove the guard → RED `AssertionError: 0 != 2`; `cp` restore → GREEN. |
| AC-6.2 | `cmd_record_spawn` (`feature-state.py:414-418`, `--command` append `:985`): `gate-runner` whose `--command`s are all P001 (`is_p001_command` `model.py:534-557`, allowlist copied from `claude_local_gate_guard.py:43-61`) raises `StateError` naming `local-gate-runner`. Mixed commands still record. | `test_record_spawn_rejects_p001_gate_runner_naming_local_gate_runner` OK. `test_p001_allowlist_matches_the_local_gate_guard` OK. |
| AC-6.3 | `required_reviewers_for` (`model.py:483-493`): small **and** low → `SINGLE_REVIEW_PANEL`; any medium/high axis → `FULL_REVIEW_PANEL`. Unset complexity fail-safes to medium. Unset risk → `DEFAULT_PACKAGE_RISK = "low"` (`model.py:94`, `resolve_package_risk:473-480`) so the planner leaving `risk` null does not ask the human. Persisted by `persist_review_requirements` (`:496-501`) from `create-package` / `update-package --complexity` (`cli_lifecycle.py:317`, `:360`). `cmd_start_review_panel` (`feature-state.py:516-534`) enforces writers out, full panel membership, and small+low size=1. | `test_start_review_panel_size_follows_complexity_and_risk` OK. Live PKG-6 is `complexity=high` / risks include `high` → full panel on `start-review-panel`. |
| AC-6.4 | `SPAWN_BUDGET_WARN_RATIO = 0.8` (`model.py:99`). `spawn_budget_warns` (`:578-580`) is true when `used < ceiling` and `used/ceiling >= 0.8`. `record-spawn` prints `SPAWN_BUDGET_WARN {used}/{ceiling} WARN 80%` on stderr (`feature-state.py:486-490`) and sets `metadata.spawn_budget_warn`. Status cell uses `spawn_budget_label` (`render_status.py:235`). Notes/bitácora surface the same (`render_notes.py:197-198`, `render_bitacora.py:117-121`). Hard cap unchanged. | `test_record_spawn_warns_at_eighty_percent_of_the_mode_ceiling` OK. Sample (ceiling 5): 1–3 silent; 4th spawn stderr `SPAWN_BUDGET_WARN 4/5 WARN 80%`; STATUS.md cell `4/5 WARN 80%`; phase not `BLOCKED`. |
| AC-6.5 | `collect_feature_spawns` (`cost-report.py:445-479`) reads `ai/state/features/*.json` `spawns[]` (history `record-spawn` fallback if `spawns[]` empty). Wired in `main` (`:721`) next to `collect_pi`. No `--route-decide`. Tokens stay 0; sessions count. Section 2 source string updated (`:693-696`). | Live `python3 ai/scripts/cost-report.py --project /home/federico/SET-AGENTES --since 2026-08-10`: Section 2 **before** (routing.db only, Cursor): `No sessions matched.` / TOTAL 0. **After**: TOTAL **137** sessions, including `cursor/inherit implementer 7`. Fixture test `test_cost_report_section_two_ingests_feature_state_spawns` OK. |
| AC-6.6 | `NON_ACCEPTING_ACTORS` still includes `implementer` (`model.py:90`). `package_accept_ready` (`:649-652`). `start-review-panel` rejects writers (`feature-state.py:517-522`). New pin `test_shrinking_the_panel_cannot_let_implementer_self_approve_or_patch` (`test_harness.py:12696-12723`) next to the existing `repair-agent` pin (`:10221-10230`). Not weakened. | Test OK. Bite: drop `implementer` from the set → RED `'implementer' not found in {…}`; `cp` restore → GREEN. |

## Bite

`cp` to `/tmp/pkg6-bite/`, never `git checkout` / `restore` / `stash`. Mutate both `ai/scripts` and `PROYECTO/ai/scripts` (tests execute `PROYECTO/ai/scripts/feature-state.py`).

### AC-6.1 `test_package_implementation_requires_a_context_pack_file`

Removed the `PACKAGE_IMPLEMENTATION` block in `check_transition`.

RED:

```
FAIL: test_package_implementation_requires_a_context_pack_file
AssertionError: 0 != 2
Ran 1 test in 1.038s
FAILED (failures=1)
```

`cp` restore → GREEN: `Ran 1 test in 1.206s` `OK`.

### AC-6.6 `test_shrinking_the_panel_cannot_let_implementer_self_approve_or_patch`

Dropped `implementer` from `NON_ACCEPTING_ACTORS`.

RED:

```
FAIL: test_shrinking_the_panel_cannot_let_implementer_self_approve_or_patch
AssertionError: 'implementer' not found in {'refactor-specialist', 'frontend-engineer', 'repair-agent'}
Ran 1 test in 0.010s
FAILED (failures=1)
```

`cp` restore → GREEN: `Ran 1 test in 2.689s` `OK`.

## cost-report Section 2 (command as specified)

```
$ python3 ai/scripts/cost-report.py --project /home/federico/SET-AGENTES --since 2026-08-10
```

Before this package (Section 2 = `routing.db` `dispatches` only; Cursor subagents never hit `*_spawn.py`):

```
Section 2 -- harness dispatch registry
No sessions matched.
TOTAL … 0
```

After (`collect_feature_spawns` ingest). Tokens remain 0 (feature-state does not store them). Sessions:

| harness | model | agent | sessions |
|---|---|---|---|
| feature-state | cursor/inherit | implementer | 7 |
| feature-state | cursor/inherit | package-reviewer | 5 |
| feature-state | cursor/inherit | security-auditor | 5 |
| feature-state | cursor/inherit | gate-runner | 4 |
| feature-state | anthropic/opus | implementer | 14 |
| … | … | … | … |
| **TOTAL (Section 2, this section only)** | | | **137** |

`cursor/inherit implementer` is this runtime. Feature 033 is in the 137. No `--route-decide` added.

## 80% warning sample (AC-6.4)

Ceiling 5 (`--max-spawns-per-package 5`). Spawns 1–3: no `SPAWN_BUDGET_WARN` on stderr. Spawn 4 (`used/ceiling = 4/5 = 0.8`, still below the hard cap):

```
SPAWN_BUDGET_WARN 4/5 WARN 80%
```

STATUS.md Spawns cell: `4/5 WARN 80%`. Feature phase is not `BLOCKED`. Spawn 5 still records; overflow remains `validate_state` / the existing ceiling block.

## Local validation (not verify.sh)

```
$ python3 -m unittest \
    tests.test_harness.HarnessTests.test_record_spawn_mints_sequential_spawn_ids_from_the_counter \
    tests.test_harness.HarnessTests.test_accept_package_rejects_open_findings_and_bad_actors
… OK

$ python3 -m unittest (PKG-6 AC tests + the two required) -v
Ran 7 tests in 6.563s
OK
```

```
$ python3 ai/scripts/heartbeat-run.py --interval 20 -- python3 -m unittest tests.test_harness.HarnessTests
Ran 492 tests in 598.398s
OK (skipped=2)
```

```
$ python3 ai/scripts/heartbeat-run.py --interval 20 -- ./build.sh --check
SELF_SCAFFOLD_SYNC_OK files=23
GLOBAL_TREE_SYNC_OK harnesses=5
BUILD_CHECK_PASS
```

```
$ git diff --check
(exit 0, empty)
```

`./ai/scripts/verify.sh` was **not** run (package instruction).
