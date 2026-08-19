# PKG-A implementer evidence — ruteo-organico-enforceable

Package: PKG-A. Feature: 034-cuota-organica-y-writer-barato.
Spec hash `539a4ff6b58b9ca67df9342dddcc79783660dcac73ce987a5da58ce136bd9721`. ADR-0064.
`strict_tdd`: true. Runtime: Cursor. pytest does not exist. No `--route-decide`.

Owned: `Global/_canonical/skills/request-triage/SKILL.md`,
`Global/_canonical/agents/orchestrator.md`, `ai/scripts/feature-state.py`,
`ai/scripts/feature_state_lib/cli_lifecycle.py`, `ai/scripts/feature_state_lib/model.py`,
`tests/test_harness.py`.

Generated (need `--exception`): `Global/{opencode,claude-code,codex,pi,cursor}/` mirrors from
`./build.sh` (skills + orchestrator + `hooks/feature_state_lib`).
Self-scaffold twins: `PROYECTO/ai/scripts/feature-state.py`,
`PROYECTO/ai/scripts/feature_state_lib/{cli_lifecycle,model}.py` (tests execute the
PROYECTO copy). Neighbor init helpers: `tests/test_{integration_hook,living_scope,module_docs,rdd_schema,repair_ceiling}.py`
(added `--risk-signal user-asked-full-pipeline` so existing `init` fixtures still open
scoped/feature). This evidence file.

Not touched: `MODE_BUDGETS` values, `log-quickfix` flags `:1198-1205`, ADR-0020 read-side
table (`orchestrator.md:24-41`, number 3), 033, Engram, `models.toml`, `generate.py` source
(only invoked to emit mirrors). `--mode` default remains `scoped` (`feature-state.py:881`).

## AC → change → proof

| AC | Change (file:line) | Proof |
|---|---|---|
| AC-A.1 | Skill default 1–3 = quick-fix; table no longer says `` `scoped` (default) `` (`request-triage/SKILL.md:120-132`). Orchestrator write-side names `RISK_SIGNAL_REQUIRED` (`orchestrator.md:83-89`). Tokens `:73-76` + `user-asked-full-pipeline`. ADR-0020 table intact `:24-41`. | `test_organic_routing_doctrine_unifies_default_and_risk_signal` OK |
| AC-A.2 | Bite: `init --mode scoped` without `--risk-signal` on a 1-file copy fixture dies `RISK_SIGNAL_REQUIRED`, no state file (`cli_lifecycle.py:154-157`). No-init + `log-quickfix` is the happy path. `init --mode quick-fix` does not paint the assertion red. | `test_init_scoped_without_risk_signal_rejects_a_small_copy_change` (`test_harness.py:4989`). Bite below. |
| AC-A.3 | `--risk-signal` on `init` (`feature-state.py:882`). `scoped`/`feature` require a token from `RISK_SIGNAL_TOKENS` (`model.py:132-140`, `valid_risk_signal:254-256`). Unknown → `RISK_SIGNAL_INVALID` (`cli_lifecycle.py:158-161`). Persisted `data["risk_signal"]` (`:166-167`), additive `.get()`, no backfill. | `test_init_feature_without_risk_signal_is_rejected` OK. `test_init_unknown_risk_signal_is_invalid` OK. `test_init_scoped_with_named_signal_persists_it` OK. `test_init_incident_does_not_require_risk_signal` OK. |
| AC-A.4 | `log-quickfix` flags unchanged (`feature-state.py:1198-1205`): `--summary` required, `--result` required, `--file` append, `--gate`. | Existing `test_log_quickfix_appends_and_renders` OK. New pin `test_log_quickfix_cli_flags_remain_mandatory` OK. |
| AC-A.5 | Doctrine: gate red in quick-fix → retry or escalate with named signal; salvage does not apply; context pack (033 AC-6.1) does not apply (`request-triage/SKILL.md:99-102`, `orchestrator.md:119-123`). `log-quickfix --result blocked` writes no feature JSON. | `test_quickfix_blocked_does_not_require_context_pack_or_salvage` OK |
| AC-A.6 | `--mode` default stays `scoped` (`feature-state.py:881`). Bare `init` → `RISK_SIGNAL_REQUIRED`. Absence of init is success. | `test_init_mode_default_stays_scoped_so_bare_init_fails` OK. Bite happy-path has no feature JSON. |

## TDD (ADR-0022)

Safety net (before any production edit):

```
python3 -m unittest tests.test_harness.HarnessTests.test_log_quickfix_appends_and_renders
Ran 1 test in 1.101s
OK
```

### RED — bite written first, current `cmd_init` accepts scoped without flag

```
python3 -m unittest tests.test_harness.HarnessTests.test_init_scoped_without_risk_signal_rejects_a_small_copy_change
FAIL: AssertionError: 0 == 0   # assertNotEqual(refused.returncode, 0)
Ran 1 test in 0.768s
FAILED (failures=1)
```

Dirty modules saved with `cp` (never git checkout/restore/stash):
`/tmp/pkg-a-tdd/{cli_lifecycle,model,feature-state}.py.dirty`

### GREEN — minimum guard then triangulation

`cmd_init` raises `RISK_SIGNAL_REQUIRED` before `atomic_write` when `--mode` ∈ {scoped, feature}
and `--risk-signal` is absent. `--risk-signal` argparse added. Tokens + persist after
triangulation tests went RED (`RISK_SIGNAL_INVALID` not found; `KeyError: 'risk_signal'`).

```
python3 -m unittest … (12 PKG-A + related tests)
............
Ran 12 tests in 3.797s
OK
```

### Mordida (cp, not git)

```
cp /tmp/pkg-a-tdd/cli_lifecycle.py.dirty ai/scripts/feature_state_lib/cli_lifecycle.py
cp … PROYECTO/ai/scripts/feature_state_lib/cli_lifecycle.py
python3 -m unittest …test_init_scoped_without_risk_signal_rejects_a_small_copy_change
FAIL: AssertionError: 0 == 0   # dirty init accepted, returncode 0
BITE_EXIT=1
cp /tmp/pkg-a-tdd/cli_lifecycle.py.green …  # restore
python3 -m unittest …test_init_scoped_without_risk_signal_rejects_a_small_copy_change
  tests.test_harness.HarnessTests.test_log_quickfix_appends_and_renders
..
Ran 2 tests in 1.317s
OK
```

## Local validation (commands actually run)

```
python3 -m unittest tests.test_harness.HarnessTests.test_log_quickfix_appends_and_renders
OK  (safety net 1.101s; post-GREEN with bite 1.317s)

python3 -m unittest tests.test_harness.HarnessTests.test_init_scoped_without_risk_signal_rejects_a_small_copy_change
OK  (GREEN 1.301s with log-quickfix; post-mordida restore 1.317s)

python3 -m unittest tests.test_living_scope tests.test_repair_ceiling tests.test_rdd_schema \
  tests.test_module_docs tests.test_integration_hook
Ran 70 tests in 41.543s
OK

./build.sh --check
SELF_SCAFFOLD_SYNC_OK files=23
GLOBAL_TREE_SYNC_OK harnesses=5
BUILD_CHECK_PASS

git diff --check
(exit 0, no whitespace errors)
```

`pytest` does not exist.

## Notes for the orchestrator

- `owned_paths` do not include `Global/opencode` (or the other four harness trees).
  `./build.sh --check` required regenerating them from `_canonical`. Please
  `--exception` the generated trees, the three `PROYECTO/ai/scripts/` twins, the
  five neighbor test files, and this evidence file.
- `risk_signal` is written only when a token is present (not a `None` key on
  `base_state`). Readers use `.get()`. Existing feature JSON is not backfilled.
- Package is **not** approved. No reviewers called.
