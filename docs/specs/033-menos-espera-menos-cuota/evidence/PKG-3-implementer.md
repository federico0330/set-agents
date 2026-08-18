# PKG-3 implementer evidence — elegir-modelo-sin-scrollear

Package: PKG-3. Feature: 033-menos-espera-menos-cuota.
Owned: `ai/scripts/tui.py`, `ai/scripts/setup_models.py`.
Exceptions: `tests/test_harness.py`, `tests/test_models_wizard_ui.py`, `docs/specs/033-menos-espera-menos-cuota`.
Not touched: `ai/scripts/set_agents_app.py`, `LANES` / `WIZARD_ITEMS` indexes 0-4, `_viewport_slice` clamp, `tui.with_progress`, PKG-2 probe/cache (consumed `available_opencode_models` only). `tui.py` still does not import `set_agents_app`.
`strict_tdd`: false. Test owner: implementer. `pytest` was not used.

## AC → change → proof

| AC | Change (file:line) | Proof |
|---|---|---|
| AC-3.1 | Headers opt-in on `PickerState.headers` (`tui.py:139`, default empty). `_step_cursor` / `_selectable_indices` (`tui.py:161-177`) skip them; ENTER on a header is a no-op (`tui.py:187-188`). OpenCode catalog grouped as `{prefix} ({n})` in `_group_models_by_provider` (`setup_models.py:412-429`); `choose` maps `Selected.index` through rendered items (`setup_models.py:401-404`). Wizard groups only the OpenCode picker (`setup_models.py:590-594`). | `test_reduce_skips_section_headers_on_up_down_and_never_selects_them` OK. `test_default_picker_state_has_no_headers` OK. `test_choose_groups_by_provider_and_maps_selected_index_to_the_model_id` OK. `test_choose_without_grouping_keeps_a_flat_index_into_options` OK. Existing wrap/enter TuiTests OK. |
| AC-3.2 | `_position_caption` (`tui.py:787-801`): always `n de total`; with an active search query `n de coincidencias (de total)`. | `test_render_shows_position_counter_and_match_count_when_filtering` OK (`1 de 5` vs `1 de 3 (de 5)`). |
| AC-3.3 | Same caption: `▲ ` / ` ▼` when `_viewport_slice` window has rows above/below (`tui.py:799-801`). Clamp itself unchanged (`tui.py:749-757`). | `test_render_shows_scroll_arrows_when_content_is_outside_the_viewport` OK. |
| AC-3.4 | `●` on the current id (`tui.py:777-778`). `run_picker(..., current=)` starts the cursor there (`tui.py:883-896`, `:909`). Wizard passes the cell's current value (`setup_models.py:587-600`). | `test_render_marks_current_value_and_run_picker_starts_the_cursor_on_it` OK (`› ● beta`, Enter → `Selected(1)`). |
| AC-3.5 | Suffixes rendered with existing `style["dim"]` (`tui.py:675-678`, `:766`, `:781-782`). `free` when id ends in `-free`; `← {role}` from `_models_in_use` (`setup_models.py:432-464`). No new `dim()` in tui that imports `set_agents_app`. | `test_render_dims_free_and_used_by_suffixes` OK (`«free»`, `«← implementer»`). Grouping test asserts both suffixes on `choose()`. |
| AC-3.6 | CHAR in navigate enters search with that char (`tui.py:194-195`). `/` still SEARCH (`:192-193`). Esc still returns to navigate. PASTE in navigate still ignored. | `test_reduce_a_letter_in_navigate_enters_search_without_slash` OK. `test_reduce_paste_is_ignored_in_navigate_but_appended_in_search_and_freetext` OK. `/` + Esc TuiTests OK. Bite below. |
| AC-3.7 | `_render` writes `\x1b[H\x1b[J` (`tui.py:878`), not `\x1b[H\x1b[2J`. | `test_render_redraw_does_not_emit_full_screen_wipe_2j` OK. Bite below. |
| AC-3.8 | All new coverage uses `_FakeStdout` / `_FakeTTY` / mocked `run_picker`. No real TTY. `test_menu_ui.py` unchanged (`/` contract held). | Heartbeat unittest below: 116 OK including `tests.test_menu_ui`. |

## Bite evidence (cp, never git checkout/restore/stash)

Green copy: `/tmp/pkg3-bite/tui.py.green`.

### AC-3.7 wipe

Left `\x1b[2J` in `_render`, ran the byte test.

RED:

```
AssertionError: '[2J' unexpectedly found in '\x1b[H\x1b[2J› a\r\n  b\r\n1 de 2\r\n↑↓ mover · Enter elegir · Esc cancelar · / buscar\r\n'
```

`cp /tmp/pkg3-bite/tui.py.green ai/scripts/tui.py` → GREEN:

```
test_render_redraw_does_not_emit_full_screen_wipe_2j ... ok
Ran 1 test in 0.010s
OK
```

### AC-3.6 type-to-search

Restored CHAR-in-navigate to `return state`.

RED:

```
AssertionError: 'navigate' != 'search'
- navigate
+ search
```

`cp /tmp/pkg3-bite/tui.py.green ai/scripts/tui.py` → GREEN:

```
test_reduce_a_letter_in_navigate_enters_search_without_slash ... ok
Ran 1 test in 0.009s
OK
```

## Local validation (not the 20 min gate)

```
$ python3 ai/scripts/heartbeat-run.py --interval 20 -- python3 -m unittest tests.test_harness.TuiTests tests.test_menu_ui tests.test_models_wizard_ui -v
...
Ran 116 tests in 5.086s
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

Full `./ai/scripts/verify.sh` was **not** run (package gate). `_viewport_slice` was not rewritten. `with_progress` was not rewritten.

## Assumptions

- Grouping is opt-in (`group_by_provider=True`) only for OpenCode model ids; Área/Rol/Campo/Effort and the main menu stay flat lists with empty `headers`.
- Search with a non-empty query hides section headers (they are not selectable) and shows `n de coincidencias (de total)` over model rows only.
- Type-to-search applies to every picker that uses `reduce()` (CHAR in navigate). `/` and PASTE contracts are unchanged; `test_menu_ui.py` stayed green without picker edits.
- Claude/codex model pickers get `current=` / `●` but are not grouped (ids are not `provider/model` OpenCode catalog rows).

## Known risks

- A 125-model catalog still uses the existing viewport clamp; grouping adds header rows so more arrow-skips than before, which is the point.
- `choose()` mapping assumes ENTER never lands on a header; the reducer enforces that, and `choose` still refuses a header index as belt-and-suspenders.
