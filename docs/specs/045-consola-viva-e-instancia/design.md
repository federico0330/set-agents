# 045 — Design handoff

> `product-analyst`, 2026-08-26. This file exists to satisfy ADR-0067 §4: a new feature declares, in
> `design.md`, which shipped clauses it steps on. **The architect owns everything below the
> supersession ledger** — module boundaries, signatures, data contracts, and the new ADR. Every HOW
> here is marked UNVERIFIED and must be confirmed against the real schema before implementation.

## Supersedes

| shipped clause | where it lives today | what 045 changes |
|---|---|---|
| ADR-0048 (024 C2) — `[subscriptions]` is the ONE `models.toml` section with a per-machine overlay; `[areas.*]`/`[roles.*]` "stay in the tracked file by design" | `ai/scripts/models_config.py:295-302` | The overlay universe widens to user taste over areas, roles, effort, and `cursor`, in `STATE_DIR/models.local.toml`. The tri-state subscription semantics (ADR-0029) are untouched. |
| 026 AC-04 — `model_request` is "the ONE new key" of the `--route-decide` descriptor | `ai/scripts/set_agents_app.py:672-676` | `effort_request` becomes a second key. The set stays closed; an unrecognized key stays `ROUTING_INPUT_INVALID`/rc=2. |
| 035 — "Area table stays (it's the useful core)" in the wizard panel | `ai/scripts/setup_models.py:234-240`, matrix at `:313-322` | The curated matrix stops being the default body of the home panel and moves behind Overrides. |

**Explicitly not superseded** (stated so nobody reads a supersession into this feature):

- **025 AC-02 / ADR-0050** — the `--avanzado` hiding policy. `--postura`/`--posturas`/`--metodologia`/
  `--metodologias` are already visible flags (`set_agents_app.py:4022-4028`); 045 adds *menu* surface,
  it does not move a flag between the visible and hidden sets.
- **ADR-0066** — the extraction ceiling of `set_agents_app.py`. `menu()` (`:3803`) is edited in place;
  nothing moves out of the monolith in this feature.
- **ADR-0063** — Cursor pins per role. 045 closes the gap that `cursor` is in `AREA_FIELDS`
  (`models_config.py:39`) but absent from the wizard's field picker (`setup_models.py:613`). The pin
  semantics and Cursor's absence from `RUNTIMES` are unchanged.
- **ADR-0029 / ADR-0048** subscription tri-state, **023 / 044** honesty rules (never invent a zero
  row), **DEC-4** stdlib-only TUI.

## Mother functions this feature enters

| entry | anchor | why it is the entry |
|---|---|---|
| `menu()` | `ai/scripts/set_agents_app.py:3803` | The only loop that paints the home and dispatches every branch by index (`:3835-3879`). |
| `MENU_ITEMS` | `ai/scripts/set_agents_app.py:3789-3800` | The order is the contract `menu()`'s indexes and `tests/test_menu_ui.py` both read. |
| `wizard()` | `ai/scripts/setup_models.py:560` | Owns `WIZARD_ITEMS` (`:567-570`, indexes 0-4 pinned at `:565-566`), the field picker (`:613`), and the save path (`:694`). |
| `_panel_lines()` | `ai/scripts/setup_models.py:231` | Builds the header the picker paints; the curated matrix is `:313-322`. |
| `run_picker()` | `ai/scripts/tui.py:899` | Where the visual system (colors, hierarchy, transitions) has to live to stay stdlib. |
| `cmd_route_decide()` | `ai/scripts/set_agents_app.py:671` | The closed `allowed` set (`:675-676`), the parse-failure path (`:696-697`), and the `effort` already on every decision (`:763`). |
| ADR-0048 overlay shape | `ai/scripts/models_config.py:305`, `:320`, `:336`, `:370` | The four-function precedent `models.local.toml` should mirror rather than reinvent. |

## UNVERIFIED — architecture must resolve before implementation

1. **Effort schema.** Does the effort axis become per-lane entries in `AREA_FIELDS`
   (`models_config.py:39`) or a nested table? `codex_effort` is referenced at `:39`, `:178`, `:610`,
   `:640-641`, `:765`, `:783`, `:843`, `:852` plus `LEGACY_MODEL_COLUMNS` (`:34`) — the migration
   surface, not just the new field, is the decision.
2. **Overlay scope and precedence.** Which sections `models.local.toml` may carry, and how it orders
   against `MODEL_PREFERENCE_PATH` (`set_agents_app.py:109`) and `subscriptions.local.toml`.
3. **Unhonored-`effort_request` token.** The reason-code name and whether it is a parse rejection or a
   post-decision reason, following the `MODEL_PIN_UNAVAILABLE` precedent (`set_agents_app.py:746-753`).
4. **Where Overrides lives.** A new tail entry in `WIZARD_ITEMS` (append-only, `:565-566`) or a new
   `MENU_ITEMS` entry (which reindexes `menu()`'s branches). These are not interchangeable.
5. **Package boundaries A/B/C/D** against `owned_paths`, and whether PKG-D must land before 047's
   `materialize(model, effort)` — this spec asserts it must; architecture confirms the ordering.
