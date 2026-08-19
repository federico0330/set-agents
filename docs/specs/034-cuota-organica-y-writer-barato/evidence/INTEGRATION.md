# 034 integration — four accepted packages compose (2026-08-19)

Feature `034-cuota-organica-y-writer-barato`. Phase `INTEGRATION`. Spec hash
`539a4ff6b58b9ca67df9342dddcc79783660dcac73ce987a5da58ce136bd9721`
(`sha256sum docs/specs/034-cuota-organica-y-writer-barato/spec.md`).
Runtime: Cursor. No `--route-decide`. No Engram MCP. `MODE_BUDGETS` not inflated.
Packages were not reopened.

## Package table

| ID | Status | What landed | Module impacts |
|---|---|---|---|
| PKG-A | accepted | Organic init guard: 1–3 files without a named risk signal stay quick-fix (`implement → gate → log-quickfix`). `init --mode scoped\|feature` without `--risk-signal` dies `RISK_SIGNAL_REQUIRED` and writes no JSON. CLI `--mode` default stays `scoped` so a bare `init` fails closed. | `estado`, `generacion-arboles` |
| PKG-B | accepted | Cheap `code-rw` BASE (`opencode/deepseek-v4-flash-free` / Cursor `composer-2.5`). One salvage per package (`record-spawn --salvage` requires `--model`). Consecutive cheap misses are a feature counter; green-on-first is a package close. | `routing`, `estado`, `generacion-arboles` (integrator recorded the missing detect candidate) |
| PKG-C | accepted | Frontier cap **4/package, 16/feature** as constants **outside** `MODE_BUDGETS`. `cost-report` section 2: derived `% green-on-first-attempt` + `frontier_used/cap`. P001 honest exemption is `local-gate-runner` only. | `estado`, `narracion-notas` |
| PKG-D | accepted | Cursor per-role `model:` pins from `models.toml` `cursor=`. `inherit` on `review-ro` + `audit`/`judge` dies at `load_roles` and `validate_cursor_target`. `repair-agent` stays on the cheap pin. | `generacion-arboles` (already present; detect named only this) |

## Cross-package invariants (file:line)

| Invariant | Holds | Source |
|---|---|---|
| Organic init guard | `scoped`/`feature` require a closed-list `--risk-signal`; missing token → `RISK_SIGNAL_REQUIRED` | `ai/scripts/feature_state_lib/cli_lifecycle.py:155-157`; tokens `ai/scripts/feature_state_lib/model.py:139-147`; doctrine `Global/_canonical/skills/request-triage/SKILL.md:121-125` |
| Cheap `code-rw` default | `[areas.implement]` BASE is free/rank-0, not `-fast`. `CHEAP_IMPLEMENT_MODEL` matches that cell. | `models.toml:121-134`; `ai/scripts/feature_state_lib/model.py:135` |
| One salvage | `--salvage` without `--model` dies before mint; second salvage → `SALVAGE_ALREADY_USED` / `HUMAN_DECISION_REQUIRED`; salvage-red after first salvage blocks | `ai/scripts/feature-state.py:425-438`; `ai/scripts/feature_state_lib/cli_repair.py:51-55` |
| Frontier 4/16 **outside** `MODE_BUDGETS` | Constants, never JSON. Check runs before mint. Cheap / `local-gate-runner` / absent `--model` do not increment. | `ai/scripts/feature_state_lib/model.py:133-134`; `is_frontier_spawn` `:683-697`; `ai/scripts/feature-state.py:440-462` |
| **`MODE_BUDGETS.scoped.max_spawns_per_package` stays 8** | Byte-equal scoped row. Frontier is a different counter. | `ai/scripts/feature_state_lib/model.py:123-128` — scoped line **`:125`**: `"max_spawns_per_package": 8` |
| Cursor per-role pins | Frontmatter `model: {cursor_model}` from `models.toml`. Shipped: implementer/repair-agent `composer-2.5`; package-reviewer/adversarial-judge `gpt-5.6-sol`. | `ai/scripts/generate.py:570-585`; `models.toml:134` / `:162` / `:180`; `Global/cursor/agents/implementer.md:4`, `repair-agent.md:4`, `package-reviewer.md:4` |
| `inherit` on review-ro + audit/judge dies | Dual guard: `load_roles` and `validate_cursor_target`. `REVIEW_DUTIES = {audit, judge}`. | `ai/scripts/models_config.py:38`; `ai/scripts/models_config.py:644-652`; `ai/scripts/generate.py:770-778` |
| Green-on-first metric | Derived in `cost-report` section 2; not a JSON field; salvage-green is not first-attempt. | `ai/scripts/cost-report.py:532-591` |

The four packages compose: A’s init guard does not touch B’s cheap BASE; B’s salvage spends C’s frontier cupo when the override is heavy; C does not raise `max_spawns`; D’s pins keep repair cheap and refuse mixed inherit. Precedence (DEC-PRECEDENCE-CEILING) is C’s cap check before B’s salvage mint (`feature-state.py:440-462` before spawn increment `:463`).

## module-impact-detect

Commands (read-only; exit 0, `"ok": true` each):

```
python3 ai/scripts/feature-state.py module-impact-detect 034-cuota-organica-y-writer-barato --package-id PKG-A
python3 ai/scripts/feature-state.py module-impact-detect 034-cuota-organica-y-writer-barato --package-id PKG-B
python3 ai/scripts/feature-state.py module-impact-detect 034-cuota-organica-y-writer-barato --package-id PKG-C
python3 ai/scripts/feature-state.py module-impact-detect 034-cuota-organica-y-writer-barato --package-id PKG-D
```

| Package | Detect candidates | Already recorded | Action |
|---|---|---|---|
| PKG-A | `estado`, `generacion-arboles` | both | none |
| PKG-B | `estado`, `generacion-arboles` | had `routing` + `estado`; **missing** `generacion-arboles` | recorded `generacion-arboles` (`record-module-impact` → `"ok": true`, `"changed": true`). `routing` left in place (product impact on cheap writer; `models.toml` is unmatched by globs). |
| PKG-C | `estado`, `narracion-notas` | both | none (`cost-report.py` unmatched, advisory) |
| PKG-D | `generacion-arboles` | `generacion-arboles` | none |

`docs/architecture/overview.md` § “Mode selection and writer quota (034)” and the `## Últimos cambios estructurales` entries on `estado`, `generacion-arboles`, `routing`, `narracion-notas` match the diff. Sembrada prose still describes the code; not rewritten.

## AC-X.3 Engram

Command: `rg Engram` over `ai/scripts/generate.py`, `ai/scripts/models_config.py`, `ai/scripts/feature-state.py`, `ai/scripts/feature_state_lib`, `models.toml`, `tests/test_harness.py`.

**Capital `Engram`: 0 hits** in that product set. Mentions in spec/no-goal docs are expected.

Lowercase `engram` (pre-existing managed-catalog disable/tests, **not** in the 034 `git diff` of those files):

- `ai/scripts/generate.py:640` — `enabledPlugins: {"engram@engram": False}` (starts disabled)
- `ai/scripts/models_config.py:82` — `MANAGED_MCP` catalog tuple
- `tests/test_harness.py` — asserts overlay stays off / PATH resolution

`git diff -- ai/scripts/generate.py ai/scripts/models_config.py ai/scripts/feature-state.py ai/scripts/feature_state_lib models.toml tests/test_harness.py | rg -i engram` → empty. **No new Engram MCP/code.** AC-X.3 holds.

## Global gates

### Mandated command (did not print `VERIFY_PASS`)

```
python3 ai/scripts/heartbeat-run.py --interval 30 -- bash ai/scripts/verify.sh
```

- Heartbeat wrapper: yes (`--interval 30`). Not piped through `tail`.
- Early: `SELF_SCAFFOLD_SYNC_OK files=23` · `GLOBAL_TREE_SYNC_OK harnesses=5` · `BUILD_CHECK_PASS`
- Reporter: `ran 1363 tests in 14m42s  fail=2  error=0  skip=4`
- Failures (both stale OpenCode-family collisions against the **old** `-fast` writer):
  1. `FAIL test_harness.HarnessTests.test_invalid_separation_graph_is_rejected` — `AssertionError: 0 != 2` (`tests/test_harness.py:6243` at fail time)
  2. `FAIL test_harness.HarnessTests.test_setup_models_check_rejects_opencode_separation_violation` — `AssertionError: 0 != 2` (`:1698` at fail time)
- Skips (pre-existing, not 034): AC-10 Zen/Go credentials; two Pi E2E env gates; `route-decide` `NO_ELIGIBLE_ROUTE` / `ROUTING_UNCONFIGURED`
- Process: **exit_code 1**, elapsed **906036 ms**. `VERIFY_PASS` was **not** printed (`set -e` stopped `verify.sh` after unittest).

Cause: PKG-B moved `[areas.implement].opencode` to `opencode/deepseek-v4-flash-free`. Putting `judge.opencode=openai/gpt-5.6-fast` no longer shares a family with implementation (`models_config.family` / `_OPENCODE_FAMILY_SUFFIX`), so `generate.py` correctly returned 0. The bite was stale, not a dead guard. Codex collision in the same test (`audit` on `gpt-5.6-terra`) still fired.

### Integrator adapter (did not reopen A–D; bite kept)

Retargeted both collisions to `opencode/deepseek-v4-flash-free` in `tests/test_harness.py`. Guard unchanged.

```
python3 -m unittest \
  tests.test_harness.HarnessTests.test_invalid_separation_graph_is_rejected \
  tests.test_harness.HarnessTests.test_setup_models_check_rejects_opencode_separation_violation
```

→ `Ran 2 tests in 11.537s` **OK** (exit 0).

### `verify.sh` tail after unittest (the mandated run never reached these)

`py_compile` `PY_COMPILE_EXIT=0` · `git diff --check` `GIT_DIFF_CHECK_EXIT=0` · `BUILD_OUTPUT_EXIT=0` · tree `diff -ruN Global/{opencode,claude-code,codex,pi,cursor}` `TREE_DIFF_EXIT=0` · `GLOBAL_PORTABILITY_OK` · `CANONICAL_PATHS_OK` · `FEATURE_STATE_OK`.

Standalone `git diff --check` before and after the adapter: exit 0.

**`VERIFY_PASS` was never emitted by the mandated `heartbeat-run.py -- verify.sh` invocation.** Full suite was not re-run after the two-line retarget (one integration pass). Orchestrator should re-run that same heartbeat command for a clean `VERIFY_PASS` before `DONE`.

## Residuals

1. **Clean `VERIFY_PASS` line** — mandated heartbeat command exited 1; adapter + focused tests + verify tail are green; full 1363-test process not repeated.
2. **Unmatched detect paths** (advisory): `tests/test_harness.py` (all packages), `models.toml` (B, D), `ai/scripts/cost-report.py` (C). Not new modules; product impacts already recorded where the globs hit.
3. **Probe WARNs** during generate (`WARN degraded … subscription not detected`) — existing degrade-not-die; live routing excludes `PROVIDER_UNAUTHENTICATED`.
4. **Installed Cursor tree vs repo** — `Global/cursor/AGENTS.md` in-repo pins per role; a session that still sees “No model is pinned” is install lag, not this feature’s source.

No Engram MCP. `MODE_BUDGETS.scoped.max_spawns_per_package` still 8. Packages A–D not reopened.
