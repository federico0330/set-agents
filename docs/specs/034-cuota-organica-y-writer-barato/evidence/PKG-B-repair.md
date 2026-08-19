# PKG-B repair — F-B01, F-B02

Package: PKG-B. Feature: `034-cuota-organica-y-writer-barato`.
Finding-verifier `c3f84049` upheld both. One consolidated pass. No `--route-decide`. No Engram.
`billing_rank` and `MODE_BUDGETS` untouched. `repair-agent` pin stays cheap
(`Global/opencode/agents/repair-agent.md:4` `opencode/deepseek-v4-flash-free`;
Cursor `inherit`). Tests execute the PROYECTO twin.

## F-B01 high AC-B.6 — reset only on package green-on-first

**Defect.** `cli_repair.py` reset `cheap_consecutive_failures` on the first
passing *named* gate of a still-open package. PKG-01 fail + PKG-02 pass-then-fail
collapsed to consecutive=1 instead of 2.

**Change.** Removed the per-gate pass reset (`ai/scripts/feature_state_lib/cli_repair.py:56-64`).
Fail still latches +1 once; salvage-red still does not increment (`:51-55` returns
`HUMAN_DECISION_REQUIRED` before the increment). Reset now lives at PACKAGE_GATES
completion (`cli_lifecycle.py:279-283` → `PACKAGE_GATES` to `PACKAGE_REVIEW`) via
`model.reset_consecutive_if_package_green_on_first` (`model.py:700-711`): all
recorded required gates pass, `salvage is None`, package never struck.

Twins: `PROYECTO/ai/scripts/feature_state_lib/{cli_repair,cli_lifecycle,model}.py`.
`./build.sh` regenerated Global hooks.

**Tests.** `test_partial_gate_pass_does_not_reset_consecutive` (`test_harness.py:969`):
PKG-01 fail; PKG-02 `package verify` pass (consecutive stays 1); `package lint` fail
→ consecutive==2; PKG-03 `writer_rung=='balanced'`.
`test_package_green_on_first_resets_consecutive` (`:995`): PKG-01 fail; PKG-02 all
required gates pass, salvage None, transition PACKAGE_REVIEW → consecutive==0.

```
test_cheap_red_plus_salvage_red_counts_one_consecutive ... ok
test_two_cheap_misses_promote_next_package_off_fast ... ok
test_partial_gate_pass_does_not_reset_consecutive ... ok
test_package_green_on_first_resets_consecutive ... ok
```

## F-B02 medium AC-B.4 — --salvage requires --model before mint

**Defect.** `record-spawn --salvage` minted `package.salvage` with `model=""` when
`--model` was omitted, and still spent `attempts.spawns`.

**Change.** `ai/scripts/feature-state.py:425-432` (PROYECTO twin identical): if
`--salvage` and `--model` is missing/blank, print `SALVAGE_MODEL_REQUIRED` and
raise `StateError` **before** the spawn increment (`:440`) and before writing
`package.salvage`. Second-salvage check (`:433-439`) unchanged. No heavy pin of
`repair-agent`.

**Test.** `test_salvage_without_model_does_not_mint_salvage` (`test_harness.py:1019`):
omitted `--model` → rc 2, `SALVAGE_MODEL_REQUIRED`, `package.salvage is None`,
spawn count unchanged. `test_second_salvage_is_rejected` still ok.

```
test_second_salvage_is_rejected ... ok
test_salvage_without_model_does_not_mint_salvage ... ok
```

## Gates

```
python3 -m unittest -v \
  tests.test_harness.HarnessTests.test_cheap_red_plus_salvage_red_counts_one_consecutive \
  tests.test_harness.HarnessTests.test_second_salvage_is_rejected \
  tests.test_harness.HarnessTests.test_two_cheap_misses_promote_next_package_off_fast \
  tests.test_harness.HarnessTests.test_partial_gate_pass_does_not_reset_consecutive \
  tests.test_harness.HarnessTests.test_package_green_on_first_resets_consecutive \
  tests.test_harness.HarnessTests.test_salvage_without_model_does_not_mint_salvage
Ran 6 tests in 11.943s
OK
```

```
python3 ai/scripts/heartbeat-run.py --interval 15 -- ./build.sh --check
SELF_SCAFFOLD_SYNC_OK files=23
GLOBAL_TREE_SYNC_OK harnesses=5
BUILD_CHECK_PASS
```

`git diff --check` → exit 0.

Not touched: PKG-C frontier cap, PKG-D Cursor pins, AC text, `billing_rank`, `MODE_BUDGETS`.
