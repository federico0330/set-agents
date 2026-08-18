# PKG-2 implementer evidence — el-menu-no-congela

Package: PKG-2. Feature: 033-menos-espera-menos-cuota.
Owned: `ai/scripts/setup_models.py`, `ai/scripts/models_config.py`.
Exceptions: `tests/test_models_wizard_ui.py`, `tests/test_probe_subscriptions.py`, `tests/test_models_wizard_first_paint.py`.
Not touched: `ai/scripts/tui.py`, `ai/scripts/set_agents_app.py`, lanes/`LANES` (PKG-1), picker grouping (PKG-3).
`detect_subscriptions` still exists (`models_config.py:378-393`).

## AC → change → proof

| AC | Change (file:line) | Proof |
|---|---|---|
| AC-2.1 | `wizard()` first frame is `_load_subscription_panel_state()` + `run_picker` (`setup_models.py:447-473`). No `detect_subscriptions` before the first paint. | `test_first_paint_does_not_call_detect_subscriptions` OK. `test_disk_cache_age_is_on_the_first_frame` OK. AC-2.5 bite below. |
| AC-2.2 | Live probe: `tui.with_progress("midiendo suscripciones", …)` (`setup_models.py:431-433`). Catalog: `tui.with_progress("listando modelos", …)` (`setup_models.py:354`). Reuses `tui.py:577`, not rewritten. | `test_refresh_key_probes_via_with_progress_and_redraws` OK (`midiendo suscripciones`, `listando modelos`). Harness `TuiTests` with_progress pins OK. |
| AC-2.3 | TTL `10 * 60` / `60 * 60` (`models_config.py:402-403`). Cache `wizard-live-cache.json` (names + ids only). Age: `suscripciones: hace {n} min` (`setup_models.py:212-213`). Refresh item last: `REFRESH_ITEM` (`setup_models.py:203`, `WIZARD_ITEMS` `:443-446`, handler `:658-662`). Indexes 0-4 unchanged. | `test_wizard_cache_ttl_starts_at_10_and_60_minutes` OK. `test_panel_shows_subscription_age` OK. `test_refresh_is_appended_indexes_0_4_stay_pinned` OK. |
| AC-2.4 | Mute `except Exception` before the loop is gone. Named degrade in `_measure_subscriptions` (`setup_models.py:402-415`) → `SUBSCRIPTION_PROBE_FAILED` (`:202`) = `suscripciones: no se pudo medir — mostrando pins`. Wizard stays usable. | `test_refresh_degrades_named_when_probe_raises_and_stays_usable` OK (rc=0, pins still in header). `test_panel_degrades_named_when_probe_failed` OK. |
| AC-2.5 | `tests/test_models_wizard_first_paint.py`: freeze probe 5 s, first `run_picker` < 300 ms. | `test_frozen_probe_does_not_delay_first_frame_past_300ms` OK (0.030 s after restore). Bite below. |

## TTL and refresh

- Subscriptions TTL: **600 s** (`models_config.py:402`).
- Catalog TTL: **3600 s** (`models_config.py:403`).
- Refresh action (appended, not a tui.py keybinding): **"Refrescar suscripciones y catálogo"** (`setup_models.py:203`), `WIZARD_ITEMS` index 8 / option `"9"` (`:658-662`).
- Degradation copy (exact): **"suscripciones: no se pudo medir — mostrando pins"** (`setup_models.py:202`).

Cache payload: `subscriptions.names` (or `error`) and `catalog.ids` plus `at`. Regex-gated; `OPENAI_API_KEY=secret` is rejected (`test_wizard_cache_rejects_non_id_payloads`). Path: `$SET_AGENTS_STATE/wizard-live-cache.json` (else `STATE_DIR`).

## Local validation (not the 20 min gate)

```
$ python3 -m unittest tests.test_models_wizard_ui tests.test_probe_subscriptions tests.test_models_wizard_first_paint tests.test_harness.TuiTests.test_with_progress_without_a_tty_writes_not_one_byte_to_stdout tests.test_harness.TuiTests.test_with_progress_no_color_in_a_pipe_degrades_but_still_reports tests.test_harness.HarnessTests.test_wizard_drop_subscription_hint_references_menu_labels_not_stale_numbers -v
...
Ran 36 tests in 3.078s
OK
```

```
$ python3 ai/scripts/heartbeat-run.py --interval 20 -- ./build.sh --check
SELF_SCAFFOLD_SYNC_OK files=23
GLOBAL_TREE_SYNC_OK profile=go-zen harnesses=5
BUILD_CHECK_PASS
```

```
$ git diff --check
(exit 0, empty)
```

Full `./ai/scripts/verify.sh` was **not** run (package gate). `tui.with_progress` was not rewritten.

## Bite evidence (AC-2.5)

`cp` to `/tmp/pkg2-bite/setup_models.py.green`, never `git checkout`/`restore`/`stash`.

Inserted a synchronous `detect_subscriptions(config)` immediately before the first `_load_subscription_panel_state()` / `run_picker` (the historical freeze site).

RED:

```
AssertionError: 5.0286065169930225 not less than 0.3 : first frame took 5.029s; probe must not run first
```

`cp /tmp/pkg2-bite/setup_models.py.green ai/scripts/setup_models.py` → GREEN:

```
test_frozen_probe_does_not_delay_first_frame_past_300ms ... ok
Ran 1 test in 0.030s
OK
```

## Assumptions

- Live subscription/catalog probe runs when the operator picks **Refrescar suscripciones y catálogo** (and catalog also on the model picker if the 60 min cache misses). It does **not** auto-probe on the second menu loop: that would move the 13 s freeze one keystroke later and would hit `test_harness.HarnessTests.test_wizard_drop_subscription_hint_references_menu_labels_not_stale_numbers` (indexes 0-4, no mock on `detect_subscriptions`). First paint is always disk; in-place refresh is the new last item.
- Wizard `_panel_lines` passes `live_discovered=None` so the first frame never calls `_resolve_live_discovered` / `probe_inventory`. Direct unit tests that omit the kwarg keep the historical live path.
- `detect_subscriptions` is unchanged for `load_roles` / `load_role_tiers`.

## Known risks

- An operator who never hits refresh sees pins + optional stale cache age until they do. Age is visible (`hace N min`).
- Catalog ids that fail `provider/model` sanitization are not persisted (live list still returned to the picker).
