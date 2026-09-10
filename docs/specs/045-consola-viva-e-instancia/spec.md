# 045 — Live console and local instance

- **Estado:** Approved (Federico, 2026-08-26) — plan "Consola viva, instancia local y hosts adaptables".
- **Modo:** feature · risk signal `public-contract` + `multi-module`.
- **Packages:** A (live home), B (instance overlay), C (postura/metodología + Cursor field), D (effort axis).
- **ADRs:** extends 0048 (overlay universe), 0063 (`cursor` field), 0026/026 AC-04 (`model_request` sibling).
  Architecture owns the new ADR; this spec does not write it.
- **Companions:** 046 (host rows this console renders), 047 (lanes that consume the effort axis).

## Problem

Three measured gaps, one theme: the console shows curated intent where the user expects live fact, and
it writes the user's taste into a git-tracked file.

1. **The home is a defaults dump.** `setup_models.py:_panel_lines` (`:231`) ends with
   `DEFAULTS CURADOS` plus one row per area (`:313-322`); its own docstring calls the area table "el
   útil core" (`:234-240`). Live signal that exists — discovered providers (`:290-312`), subscription
   age (`:220-228`) — is one line each, above ten rows of fallback the router only reaches when the
   model does not apply the decision.
2. **The wizard dirties the repo.** "Guardar" calls `models_config.emit_atomic(models_out, config)`
   (`setup_models.py:694`) on the tracked `models.toml`. ADR-0048 already fixed this for
   `[subscriptions]` — `models_config.py:295-302` names the tracked rewrite as "what used to dirty
   the tree and block `--update` forever via `tree_clean()`" — but it fixed it for exactly one section
   and states that `[areas.*]`/`[roles.*]` "stay in the tracked file by design" (`:297-298`). Every
   area/role/effort edit still lands there.
3. **Effort is one provider's field, and the orchestrator cannot ask for it.** `codex_effort` is a
   Codex-only column (`models_config.py:39` `AREA_FIELDS`, catalog check at `:640-641`); the wizard's
   field picker offers `claude|codex|codex_effort|opencode` (`setup_models.py:613`) and never `cursor`,
   although ADR-0063 already put `cursor` in `AREA_FIELDS`. `--route-decide` accepts `model_request`
   as "the ONE new key" (`set_agents_app.py:672-676`) and has no effort sibling, even though every
   decision already reports `effort` (`:763`).

Postura (`set_agents_app.py:1124-1148`) and metodología preferida (`:1182-1203`) are real state with
CLI verbs and zero menu surface: `MENU_ITEMS` (`:3789-3800`) never names them.

## Scope

### PKG-A — the live home
`menu()` (`set_agents_app.py:3803`) and the wizard header (`setup_models.py:231`, painted by
`tui.run_picker`, `tui.py:899`) lead with live state: hosts (from 046 when present), authenticated /
routable providers, and the last routing decision. The curated matrix moves behind an **Overrides**
entry. Visual system (ANSI colors, hierarchy, short transitions) lives in `tui.py`; the TUI stays
stdlib-only (DEC-4).

### PKG-B — the instance overlay
Factory taste stays in git (`models.toml`); user taste lands in `STATE_DIR`
(`set_agents_app.py:47`) as `models.local.toml`, following ADR-0048's four-function shape
(`subscriptions_overlay_path` `:305`, `load_subscriptions_overlay` `:320`,
`write_subscription_overlay` `:336`, `effective_subscriptions` `:370`). The wizard **never** writes
tracked `models.toml` for a user-taste edit. Absent overlay == no overlay == factory value.

### PKG-C — postura, metodología, Cursor
`MENU_ITEMS` gains postura and metodología (SDD / RDD=strict-TDD / off) surfaces that read and write
the existing state (`set_postura` `:1129`, `set_metodologia` `:1187`) with no `--avanzado` needed.
`cursor` becomes an editable field in Overrides, closing the `AREA_FIELDS` gap ADR-0063 opened.

### PKG-D — effort as a first-class axis
Model **and** effort are overridable for every lane, not only Codex. `--route-decide`
(`cmd_route_decide`, `set_agents_app.py:671`) accepts an ephemeral `effort_request` in its descriptor,
sibling of `model_request` in the `allowed` set (`:675-676`), validated on the same closed-set /
`ROUTING_INPUT_INVALID` rc=2 path (`:696-697`). It is a **soft preference**: it never relaxes a hard
exclusion and never silently changes a decision — an unhonored request is named in `reason_codes`.

## Non-goals

- Gentle-TUI copy, a marketplace, static SDD phase profiles, a `brew`/`curl` path parallel to
  `cmd_update`.
- Any non-stdlib TUI dependency (DEC-4).
- Reordering `WIZARD_ITEMS[0..4]` (`setup_models.py:565-566` pins those indexes) or renumbering
  `MENU_ITEMS` branches (`menu()` dispatches by index, `:3835-3879`). New entries append.
- Migrating existing tracked `[areas.*]`/`[roles.*]` values into the overlay. Factory stays factory.
- Reopening `[subscriptions]` semantics (ADR-0048/ADR-0029 tri-state stands).
- Persisting `effort_request`. It is per-decision, like `model_request`.

## Criteria

- **AC-A.1** The first screen of `./set-agents` and of the models wizard contains no `AREA`/`EFFORT`
  matrix row; the matrix is reachable only through an Overrides entry.
- **AC-A.2** The home names, per line, at least: hosts, providers, and the last routing decision —
  each either with live values or with an explicit "not measured / probe failed" phrase. No zero row
  is invented (023, 044 precedent).
- **AC-B.1** A user-taste edit (area, role, effort, cursor) writes `STATE_DIR/models.local.toml` and
  leaves `git diff --name-only -- models.toml` **empty**.
- **AC-B.2** Overlay absent, malformed, or with unknown keys → factory value, no crash (same
  degrade-to-`{}` discipline as `load_subscriptions_overlay`, `models_config.py:320-333`).
- **AC-B.3** Overlay and tracked file disagree → overlay wins per key; a curated value the overlay
  says nothing about still applies (ADR-0048's rule at `models_config.py:370-377`).
- **AC-C.1** The menu shows the current postura and the current metodología, and changing either from
  the menu is readable by the next `--posturas` / `--metodologias` run, without `--avanzado`.
- **AC-C.2** `cursor` is selectable in Overrides and its value validates against the same catalog
  path as the other fields.
- **AC-D.1** Effort is overridable for every lane in `AREA_FIELDS`, not only Codex.
- **AC-D.2** A descriptor with a valid `effort_request` routes with that effort when eligible and
  reports it; the pre-045 byte-identical decision is preserved when the key is absent.
- **AC-D.3** An invalid or unhonorable `effort_request` **names the reason** (parse failure → rc=2
  `ROUTING_INPUT_INVALID`; well-shaped but not honorable → a named reason code) and never bypasses a
  hard exclusion, never downgrades silently.
- **AC-E.1** `python3 -m unittest tests.test_harness tests.test_routing tests.test_menu_ui` and
  `./build.sh --check && ./ai/scripts/verify.sh` green. No test weakened, skipped, or deleted.

## Spec audit

Checked:

- **Absence, per requirement.** AC-B.2 defines the *absent record* outcome (missing file, malformed
  file, unknown key) and not only "present with a value" — the universe is `AREA_FIELDS`
  (`models_config.py:39`), which exists independently of what the overlay happens to contain.
  AC-A.2 defines the absent-signal outcome as a named phrase, never a fabricated zero.
- **Data source carries the signal.** `effort` is already on every decision (`set_agents_app.py:763`),
  so AC-D.2 reads a field that exists. Live provider state is already computed
  (`_estado_general_lines`, `:3721`; `probe_listed_and_usable`, `:3752`), so AC-A.2 does not require a
  new probe to be honest.
- **Fixture that would fool AC-B.1.** A tree already dirty at `models.toml` — which is the state of
  this working copy on 2026-08-26 — makes `git diff` non-empty regardless of the change, and a tree
  where the wizard writes to a temp `models_out` makes it empty regardless. The criterion is measured
  from a clean `models.toml` baseline against the **real** `models_out` path the wizard uses.
- **Fixture that would fool AC-A.1.** Asserting the matrix is absent from a *screenshot* of the
  picker passes if the matrix simply scrolled off. The criterion is on the header text the picker
  receives, which is where 035 F-03 already put it (`setup_models.py:594-600`).
- **Pairwise conflicts.** (i) Overlay vs tracked value → AC-B.3 states precedence. (ii)
  `effort_request` vs a hard exclusion → AC-D.3 gives the exclusion precedence and forces a named
  reason, so two outcomes never race. (iii) `effort_request` vs `model_request` when the requested
  model does not offer the requested effort → the model request wins and the effort request is
  reported unhonored; a single decision never carries two conflicting efforts. (iv) 045 PKG-D vs 047
  `materialize(model, effort)` → 045 defines the vocabulary, 047 consumes it and must not define a
  second one.
- **Could not verify.** Whether the effort axis becomes new `AREA_FIELDS` entries or a nested table;
  the exact token for an unhonored `effort_request`; whether the Overrides entry is a new
  `WIZARD_ITEMS` tail entry or a `MENU_ITEMS` entry; the overlay's precedence against
  `MODEL_PREFERENCE_PATH` (`set_agents_app.py:109`). All **UNVERIFIED** — architecture confirms
  against the real schema and signatures.

## Supersedes

- **ADR-0048's overlay-universe clause** (`models_config.py:295-302`): `[subscriptions]` is no longer
  the only `models.toml` section with a per-machine overlay, and `[areas.*]`/`[roles.*]` no longer
  "stay in the tracked file by design" for user taste. Tri-state subscription semantics unchanged.
- **026 AC-04's "`model_request` is the ONE new key"** (`set_agents_app.py:672-674`): `effort_request`
  becomes a second key. The closed set stays closed and an unrecognized key stays
  `ROUTING_INPUT_INVALID`/rc=2.
- **035's "area table stays, it's the useful core"** (`setup_models.py:234-240`): the matrix is no
  longer the default body of the home panel.
- Not superseded: 025 AC-02 / ADR-0050 (`--avanzado` flag hiding — postura and metodología are
  already visible flags, `set_agents_app.py:4022-4028`; this feature adds menu surface, not flags);
  ADR-0066 (extraction ceiling — `menu()` is edited in place); ADR-0029/ADR-0048 subscription
  tri-state; ADR-0063 (this closes its `cursor` gap rather than changing it).
