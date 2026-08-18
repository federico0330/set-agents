# PKG-1 implementer evidence — una-sola-lane-opencode

Package: PKG-1. Feature: 033-menos-espera-menos-cuota.
Owned: `models.toml`, `ai/scripts/models_config.py`, `ai/scripts/setup_models.py`,
`ai/scripts/generate.py`, `build.sh`, `active-profile` (deleted; was gitignored).
Exceptions: the seven AC-1.7 test files, `ai/scripts/verify.sh`,
`tests/fixtures/models.toml` (loader shape), `tests/test_models_wizard_first_paint.py`
(wizard signature lost the lane argument).
Not touched: PKG-2 probe/cache, PKG-3 grouping, `detect_subscriptions` (still at
`models_config.py:402`), provider prefixes, `Global/` by hand, Cursor target 032,
`routing_core` (AC-1.6 chose (b) in owned paths). `feature-state.py` not called.

`strict_tdd`: false.

## AC → change → proof

| AC | Change (file:line) | Proof |
|---|---|---|
| AC-1.1 | `LANES` gone. 38 `opencode = { … }` maps → strings keeping go-zen (33 kept, 5 no-go-zen overrides dropped). Prefixes stay. | Conservation list below. `hasattr(models_config, "LANES")` is False (`test_manual_lane_scripts_and_profile_axis_are_gone`). `test_opencode_cells_reject_a_restored_lane_map` OK. |
| AC-1.2 | `active_profile()` / `auto_profile()` / `active-profile` / `build.sh --profile` / `generate.py --profile` gone. `verify.sh:30` is `./build.sh --output "$STAGING"` (no `--profile go-zen`). `detect_subscriptions` stays. | `test_generate_rejects_the_dead_profile_flag` OK. `test_manual_lane_scripts_and_profile_axis_are_gone` OK. `grep --profile build.sh` → empty. |
| AC-1.3 | Campo is exactly `["claude","codex","codex_effort","opencode"]` (`setup_models.py:613`). Panel has no `lane:`; column `OPENCODE` (`:266`, `:314`). | `test_campo_is_exactly_the_four_axes` OK. `test_panel_is_compact_overrides_collapse_to_a_count` asserts no `lane:` / no `OPENCODE[`. |
| AC-1.4 | `[session].opencode_small_model` is `"opencode/north-mini-code-free"` (`models.toml:54`). Validation `models_config.py:199-203`. openai-only's `openai/gpt-5.4-mini` dropped. | `small_model()` returns the string. Conservation below. |
| AC-1.5 | 18 `[roles.*.tiers.*.opencode]` collapsed after identity proof (command below). `local-gate-runner` kept only its go-zen string, no invented keys. | Pre-collapse: `AC-1.5 identity: PASS` (18/18 identical). `test_ac15_eighteen_tier_opencode_cells_are_the_proven_identical_strings` OK. `test_ac15_local_gate_runner_keeps_only_the_go_zen_string` OK. |
| AC-1.6 **(b)** | `fail_provider_exhausted` / `require_opencode_provider_usable` (`models_config.py:96-128`, wired in `resolve_role:582`). Names `PROVIDER_QUOTA_EXHAUSTED provider=…` and `./setup-models.sh`. 011 remains BLOCKED; no live failover assumed. | Bite RED/GREEN below. `test_ac16_exhausted_provider_fails_loudly_naming_provider_and_action` OK. |
| AC-1.7 | 6 files rewritten against the single dimension. `tests/test_auto_profile.py` **deleted**: the invariant that died is `auto_profile()` mapping probed opencode pairs → `go-zen\|zen\|openai-only` and `build.sh` writing `active-profile` only when missing. The lane axis is gone, so that mapping can no longer break. Wrappers-gone (`use-*.sh` absent) moved to `test_harness.py`. | Rewritten-test table below. No tests deleted to green the suite except that entire file. |

## Go-zen conservation list

Pre-collapse inventory (command actually run against the 3-lane `models.toml`):
`opencode = { }` maps: **38**. With go-zen: **33**. Without go-zen (drop override; resolved go-zen unchanged): **5**.

### Maps without go-zen (override dropped)

| Line (pre) | Dropped keys | Why |
|---|---|---|
| 205 `[roles.debugger]` | zen=`openai/gpt-5.4` | Never applied to go-zen; debugger still inherits `[areas.implement]` |
| 246 `[roles.image-describer]` | openai-only=`openai/gpt-5.4-mini` | Whole role table emptied and removed |
| 274 `[roles.product-analyst]` | zen=`opencode/deepseek-v4-pro`, openai-only=`openai/gpt-5.4` | `codex` override kept |
| 279 `[roles.project-bootstrapper]` | zen=`opencode/deepseek-v4-pro`, openai-only=`openai/gpt-5.4-mini` | `codex`/`codex_effort` kept |
| 300 `[roles.test-writer]` | zen=`opencode/deepseek-v4-flash-free`, openai-only=`openai/gpt-5.4-mini` | Whole role table emptied and removed |

### Other-lane values that differed from go-zen (dropped; remaining string = go-zen)

| Line (pre) | Keep (go-zen) | Dropped (≠ go-zen) |
|---|---|---|
| 97 `[areas.coord]` | `openai/gpt-5.5` | zen/openai-only `opencode/grok-4.5` |
| 103 `[areas.analysis]` | `openai/gpt-5.4-fast` | zen `openai/gpt-5.4-mini`, openai-only `openai/gpt-5.4` |
| 109 `[areas.docs]` | `openai/gpt-5.4-fast` | zen `opencode/glm-5.2`, openai-only `openai/gpt-5.5` |
| 115 `[areas.implement]` | `openai/gpt-5.6-fast` | zen `opencode/kimi-k2.7-code`, openai-only `openai/gpt-5.4` |
| 121 `[areas.gate]` | `openai/gpt-5.4-mini` | zen `opencode/deepseek-v4-flash-free` |
| 160 `[areas.release]` | `openai/gpt-5.4-mini` | zen `opencode/deepseek-v4-flash-free` |
| 166 `[areas.memory]` | `openai/gpt-5.4-mini` | zen `opencode/deepseek-v4-flash-free` |
| 243 `[roles.frontend-engineer]` | `openai/gpt-5.3-codex-spark` | openai-only `openai/gpt-5.4-mini` |
| 283 `[roles.refactor-specialist]` | `openai/gpt-5.3-codex-spark` | openai-only `openai/gpt-5.4-mini` |

23 maps had other lanes equal to go-zen (pure drop). 18 of those are the AC-1.5 tier tables.

### AC-1.4 small model

Kept go-zen: `opencode/north-mini-code-free`. Dropped openai-only: `openai/gpt-5.4-mini`. zen was already the same as go-zen.

## AC-1.5 pre-collapse identity proof

Command (run **before** collapsing `models.toml`):

```
python3 - <<'PY'  # tomllib load of models.toml; 18 [roles.*.tiers.*.opencode] maps
# … print unique values per table …
PY
```

Output (abridged; every table `unique=[one model] missing=[]`):

```
[roles.debugger.tiers.fast].opencode: unique=['openai/gpt-5.6-luna']
[roles.debugger.tiers.balanced].opencode: unique=['openai/gpt-5.6-sol']
[roles.debugger.tiers.frontier].opencode: unique=['openai/gpt-5.6-terra']
… same luna/sol/terra for delta-reviewer, finding-verifier, implementer,
  package-reviewer, security-auditor …
tier tables counted: 18
AC-1.5 identity: PASS
```

`[roles.local-gate-runner]` was **not** one of the 18 (only `"go-zen"`). Collapsed to that string; no keys invented.

## AC-1.6 choice: (b)

Owned-path loud fail. `routing_core` not touched. 011-quota-failover stays BLOCKED.

Message shape (`models_config.py:108-114`):
`PROVIDER_QUOTA_EXHAUSTED provider={provider} model={model} area={area} — reassign the area with ./setup-models.sh (Campo: opencode) or wait until that provider's quota resets`

Forbidden behaviours excluded by the test: hang, raw traceback (`assertNotIn("Traceback")`), silent substitute (`assertRaises` + orchestrator stays `openai/gpt-5.5`).

## Bite evidence (cp, never git checkout/restore/stash)

### AC-1.6 silent exhaustion

`cp ai/scripts/models_config.py /tmp/pkg1-bite/models_config.py.green`

Replaced `fail_provider_exhausted` body with `return None` (no `die`).

RED:

```
AssertionError: ModelsError not raised
FAILED (failures=1)
red_rc=1
```

`cp /tmp/pkg1-bite/models_config.py.green ai/scripts/models_config.py` → GREEN:

```
test_ac16_exhausted_provider_fails_loudly_naming_provider_and_action ... ok
Ran 1 test in 0.012s
OK
green_rc=0
```

### Restored 3-lane map (rewritten-test bite)

`cp` green copy. `_opencode_string` accepted a dict by taking `go-zen`.

RED:

```
AssertionError: ValueError not raised
FAILED (failures=1)
red3_rc=1
```

`cp` restore → GREEN:

```
test_opencode_cells_reject_a_restored_lane_map ... ok
OK
green3_rc=0
```

Production file confirmed restored (`PROVIDER_QUOTA_EXHAUSTED` and `not a lane map` present).

## Rewritten-test invariants

| File | Invariant kept |
|---|---|
| `test_auto_profile.py` | **Deleted.** Died: probe→lane mapping (`go-zen`/`zen`/`openai-only`) and `build.sh` writing missing `active-profile`. Wrappers-gone (`use-*.sh` absent) moved to `test_harness.test_manual_lane_scripts_and_profile_axis_are_gone`. |
| `test_probe_subscriptions.py` | ADR-0029 tri-state (explicit false dies; absent+detected silent; absent+undetected WARN; `detect_subscriptions` shape). Calls `load_roles`/`load_role_tiers` without a lane. |
| `test_models_wizard_ui.py` | Compact panel, tri-state pins, WIZARD_ITEMS 0-4 pinned, grouping picker, no key insertion on Esc. Added Campo=4 axes and no `lane:` / `OPENCODE`. |
| `test_decide_always.py` | Doctrine markers + panel "DEFAULTS CURADOS". `_panel_lines` no longer takes a profile. |
| `test_spawn_materialization.py` | Same panel markers; `_panel_lines` arity only. |
| `test_routing.py` | AC-06(a) collision scan now reads OpenCode **strings** (still "no area cell collides with any tiered ladder"). `resolve_role` no profile. Probe-cache tripwire count `cache_root=_probe_cache_root()` is **1** (was 2: `detect_subscriptions` + deleted `auto_profile`). |
| `test_harness.py` | Area/override merge, inactive subscription dies, emit round-trip, generate/build without `--profile`, separation `--set`, tier coherence with string cells. |

## Local validation (not the 20 min gate)

```
$ python3 ai/scripts/heartbeat-run.py --interval 20 -- python3 -m unittest tests.test_probe_subscriptions tests.test_models_wizard_ui tests.test_decide_always tests.test_spawn_materialization -v
Ran 76 tests in 11.076s
OK (skipped=1)
```

(`test_auto_profile` omitted: file deleted.)

```
$ python3 ai/scripts/heartbeat-run.py --interval 20 -- python3 -m unittest tests.test_routing tests.test_harness -v
```

First run: 3 FAIL (`cache_root=_probe_cache_root()` count 1≠2; `git diff --check` blank line at EOF on `models.toml:288`; `--set judge.opencode=openai/gpt-5.6-terra` no longer collides with implementer `openai/gpt-5.6-fast`). Repaired. Re-run of those three plus AC-1.5/1.6/axis tests:

```
Ran 11 tests in 13.474s
OK
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

Full `./ai/scripts/verify.sh` was **not** run (package gate). `Global/` not rewritten by hand.

## Assumptions

- AC-1.6(b) is a harness-side API (`exhausted_providers=` on `load_roles`/`resolve_role`). Production spawn adapters are not owned and were not wired; 011 is BLOCKED so this does not claim live failover.
- Role overrides that only named zen/openai-only were dropped rather than inventing a go-zen key.
- `tests/fixtures/models.toml` and `tests/test_models_wizard_first_paint.py` had to follow the string/signature change or the rewritten tests could not load.

## Known risks

- A machine whose live probe lacks the pinned model's subscription still gets ADR-0029 WARN-and-keep at generate time; quota exhaustion is loud only when a caller passes `exhausted_providers`.
- `gitignore` still lists `active-profile` (not owned). Harmless leftover.
