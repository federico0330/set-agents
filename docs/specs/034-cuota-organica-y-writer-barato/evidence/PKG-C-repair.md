# PKG-C repair — SEC-001

Package: PKG-C. Feature: `034-cuota-organica-y-writer-barato`.
Finding-verifier `f8d02524` upheld SEC-001. One consolidated pass. No `--route-decide`. No Engram.
`MODE_BUDGETS.scoped.max_spawns_per_package == 8` byte-equal (`model.py:125`). Caps stay constants.
Tests execute the PROYECTO twin. Do not call `accept-package`.

## SEC-001 — P001 `--command` must not exempt a heavy role

**Defect.** `is_frontier_spawn` (`ai/scripts/feature_state_lib/model.py`, pre-repair)
short-circuited on `spawn_commands_are_p001` for **any** role. A heavy
implementer / repair-agent / package-reviewer with `--command 'git diff --check'`
was classified non-frontier, so the 5th spawn and salvage-after-cap skipped
`FRONTIER_CAP_EXHAUSTED`.

**Change.** Deleted `spawn_commands_are_p001` and its short-circuit. Classification
is now (`model.py:683-697`): `--model` present, model ≠ cheap default, role ≠
`local-gate-runner`. `commands` stays in the signature for additive callers but
does not exempt. Honest P001 exemption remains the `local-gate-runner` role check
(`:693-694`). Gate-runner-all-P001 rejection kept at
`feature-state.py:414-418`. Comment at `:440-443` matches the repaired contract.

Twins: `PROYECTO/ai/scripts/feature_state_lib/model.py`,
`PROYECTO/ai/scripts/feature-state.py`. `./build.sh` regenerated Global hooks.

**Test.** `test_fifth_heavy_implementer_with_p001_command_is_rejected`
(`tests/test_harness.py:1173`): four heavy implementers with `--command 'git diff --check'`
mint; the fifth dies `FRONTIER_CAP_EXHAUSTED`, `frontier_used==4`, spawn list
length 4. Second block: four heavy reviewers with the same P001 command, then
`--salvage` repair-agent + P001 command → `FRONTIER_CAP_EXHAUSTED`, salvage not
minted. Existing `test_salvage_and_heavy_reviewer_increment_frontier_p001_does_not`
(`:1100`, honest `local-gate-runner`) stays green.

### Classifier (file:line)

```
ai/scripts/feature_state_lib/model.py:683-697
def is_frontier_spawn(...):
    if not (model or "").strip(): return False
    if (role or "") == "local-gate-runner": return False
    if is_cheap_default_model(model): return False
    return True
```

No `spawn_commands_are_p001` in the function. Cap reject still
`feature-state.py:445-461` (`FRONTIER_CAP_EXHAUSTED` +
`{"scope": "frontier", "key": "used", "grain": "package"}`).

### Command output — 5th heavy+P001 dies FRONTIER_CAP_EXHAUSTED

Live classifier + CLI (PROYECTO `feature-state.py` via `HarnessTests.run_state`):

```
is_frontier_spawn(heavy, implementer, git diff --check) = True
is_frontier_spawn(heavy, local-gate-runner, git diff --check) = False
rc 0
stderr FRONTIER_CAP_EXHAUSTED
phase BLOCKED frontier_used 4 spawns 4
```

Assertion in the new test (`test_harness.py:1195`):
`self.assertIn("FRONTIER_CAP_EXHAUSTED", blocked.stderr)`.

## Gates

```
python3 -m unittest -v \
  tests.test_harness.HarnessTests.test_fifth_heavy_implementer_with_p001_command_is_rejected \
  tests.test_harness.HarnessTests.test_fifth_frontier_of_a_package_is_rejected \
  tests.test_harness.HarnessTests.test_frontier_cap_beats_salvage_and_promotion \
  tests.test_harness.HarnessTests.test_salvage_and_heavy_reviewer_increment_frontier_p001_does_not
test_fifth_heavy_implementer_with_p001_command_is_rejected ... ok
test_fifth_frontier_of_a_package_is_rejected ... ok
test_frontier_cap_beats_salvage_and_promotion ... ok
test_salvage_and_heavy_reviewer_increment_frontier_p001_does_not ... ok
Ran 4 tests in 10.924s
OK
```

```
python3 ai/scripts/heartbeat-run.py --interval 15 -- ./build.sh --check
SELF_SCAFFOLD_SYNC_OK files=23
GLOBAL_TREE_SYNC_OK harnesses=5
BUILD_CHECK_PASS
```

`git diff --check` → DIFF_CHECK_EXIT=0.

Not touched: PKG-D, AC text, `MODE_BUDGETS` values, cap constants, `--route-decide`, Engram.
Existing tests not weakened.
