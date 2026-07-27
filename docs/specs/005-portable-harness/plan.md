# Feature 005 — implementation plan (contract 1.1.0, pre-approval)

Amended from 1.0.0 after spec-challenge (see `spec.md`'s Amendment log for the full rationale and the
old→new AC map). Three packages, strictly ordered: P1 unlocks portability with NO vault dependency (ORQ-6
split the scaffold so P1 is portable on its own); P2 makes the vault the state/context controller and picks
up the vault-link half of the scaffold; P3 is last, a UI rework of surfaces P1/P2 finalize. Full loop per
package (implementation → gates → independent review → repair → delta → acceptance), `--mode feature`
budgets, same as 004.

## P1-portable-core

| ID | Work item | Acceptance |
|---|---|---|
| T-100 | ADR-0008: `HARNESS_HOME`/`PROJECT_ROOT` doctrine, install-time-only baking, allowlist dual fix, corrected walk-up, SEC-A02 trust reframing, persisted project-id mechanism, SCHEMA 4→5 migration mechanics | AC-00 |
| T-101 | `Global/**` keeps `__SET_AGENTS_ROOT__` through generate/build (no baking there); `verify.sh` asserts zero absolute paths / placeholder presence in `Global/**` | AC-01 |
| T-102 | Extend `install.py`'s substitution write path from JSON-only (`merged_json`) to a generic byte-substitution applied to the installed `hooks/coord_policy.py` and installed `agents/orchestrator.{md,toml}` | AC-01 |
| T-103 | `install.py` validates the resolved `HARNESS_HOME` against `FORBIDDEN_SYNTAX` byte classes, refuses install with a clear error on a hit; `coord_policy.py`'s matcher gains a post-`shlex.split` argv-comparison mode so spaces in `HARNESS_HOME` still match | AC-02 |
| T-104 | `find_project_root(start)`: self-inclusive candidate list (`[start] + ancestors`), both markers evaluated per level (nearest-ancestor-wins), stops at filesystem root; `--project`/`SET_AGENTS_PROJECT` seam, explicit-over-discovered precedence | AC-03 |
| T-105 | Re-anchor `_resolve_context_pack`/`_validate_context_pack_path` to `PROJECT_ROOT`; security-auditor re-derivation of SEC-A02 including the trust-level reframing (exact read paths, byte cap, "data never instructions") | AC-04 |
| T-106 | Persisted per-project id file (written at scaffold time) as the primary `project_key` source, path-hash as fallback only; `realpath`+case normalization; fail-closed on mismatch, including "no prior runs" case | AC-05 |
| T-107 | `project_key` column on `dispatches` + SCHEMA 4→5 DDL/CHECKs; migration: live-DB backup, single-transaction (`BEGIN EXCLUSIVE`/`COMMIT`), backfill every pre-existing row (incl. non-terminal) with the harness's own `project_key`; re-derive `dispatches_review` index scope; document `metric_rollups` staying global and the backward-incompatibility consequence (pre-005 checkout + schema-5 DB ⇒ `ROUTING_UNAVAILABLE` via existing `store.py:150` check) | AC-05 |
| T-108 | `set-agents --scaffold [DIR]` (P1 portion only): `ai/state/features/` + generic-script copy (`feature-state.py`, `check-owned-paths.py`) + persistent project-id file; idempotent create-if-missing; NO vault dependency | AC-06 |
| T-109 | Harness self-scaffold: `SET-AGENTES/ai/scripts/{feature-state.py,check-owned-paths.py}` become tracked copies of the `PROYECTO/ai/scripts/` templates; drift check added inside `build.sh --check`'s empty branch, explicitly scoped apart from `check-drift.sh` and `verify.sh`'s `Global/**` diff | AC-07 |
| T-110 | Degrade-honest doctrine extended: no marker in `[start]+ancestors` ⇒ base agent; explicit non-degrade clarification for a state-dir-only (no `.git`) project; Pi lifecycle forwards one user routing cwd to decide/dispatched/terminal while preserving Pi's execution cwd | AC-08 |
| T-111 | Guest E2E hermetic test (executed by gate-runner/package-reviewer, never implementer-self-attested): fully isolated temp tree (clone, fake `$HOME`, scaffolded project); matrix = non-default clone dir name, `$HOME` without `~/.local/bin` on PATH (absolute script path invoked directly), `HARNESS_HOME` with a space, non-git scaffolded project, `verify.sh` green from the guest clone; asserts exit code + JSON envelope + concrete `project_key` per case | AC-09 |

Ownership: `ai/scripts/install.py`, `ai/scripts/generate.py`, `ai/scripts/coord_policy.py`,
`ai/scripts/set_agents_app.py` (routing zones + P1 scaffold command), `ai/scripts/set_agents_spawn.py` (Pi routing-cwd propagation), `ai/scripts/routing_core/store.py`,
`ai/scripts/bootstrap_project.py`, `ai/scripts/sync-project.sh`, `build.sh`, `ai/scripts/verify.sh`,
`Global/_canonical/agents/orchestrator.md`, `docs/adr/0008-*.md`, `tests/test_harness.py`,
`tests/test_routing.py`.

## P2-vault-mandatory

| ID | Work item | Acceptance |
|---|---|---|
| T-200 | ADR-0009: DEC-5/6/7 mechanics, backup/rollback doctrine, merge-case algorithm grounded in `evidence/vault-migration-inventory.md` | AC-10 |
| T-201 | `tools.toml`'s `[cli.obsidian]` gains `apt`/`dnf`/`zypper`/`winget`/`choco`; `platform_pm()` extended; table-driven `shutil.which`-mocked tests across all managers + "none" on ALL THREE CI runners; `windows-latest` job runs the full `unittest` suite (stops being parse-only); sudo consent contract verified byte-unchanged; macOS/Windows real GUI install documented as a manual checkpoint, never claimed as machine-verified | AC-11 |
| T-202 | Persisted vault-link intent-marker registry (topology + vault path + full repo path + linked-at), written by every `--vault-link` (hybrid or `--private`); vault status surface (T-207) refuses to act without an entry | AC-12 |
| T-203 | `notes_root()` scoped to `ai/state/`-marked directories (never arbitrary/third-party dirs); preserve `tests/test_harness.py:611-621` verbatim, replace 622-628 with its documented opposite, assertion count never shrinks; re-run P1's T-109 drift check after this template edit, before P2's own gates | AC-13 |
| T-204 | `.obsidian/{app,appearance,core-plugins}.json` managed seeds, fixed core-plugin set, no community plugins | AC-14 |
| T-205 | `app_config()["vault"]` persistence via read-merge-write for `--vault-init`/`--vault-link`; fix `menu()`'s `first_run()` raw `APP_CONFIG.write_text(...)` to use the same read-merge-write helper | AC-15 |
| T-206 | Reverse-direction migration (vault-resident → hybrid): full universe (pure move, MERGE — required by `iey-ai`, dedup, byte-conflict abort, already-symlinked repo side, vanished target repo, same-basename-different-path); copy-verify-then-delete-original backup/rollback (never a bare `shutil.move`); `--dry-run` + explicit separate confirmation; `exclude_notes_from_git()` reused for the four real `~/iey/` projects per DEC-5; registry entry records the exclusion | AC-16 |
| T-207 | New, distinct vault status/repair surface (proposed `--vault-doctor`, NOT an extension of `--doctor --harness pi`, which stays byte-unchanged): report-only by default; `--repair` requires an explicit flag AND a per-project dry-run-confirmed marker; never touches an unregistered project | AC-17 |
| T-208 | `set-agents --context [--project DIR] [--json]`: `<COMPANY>` resolution algorithm, degrade paths (no vault/no company/no proyecto file), byte caps, fixed `{hub,company,project,pending}` JSON schema, asserted to never read credential surfaces (`~/.pi/agent/auth.json` etc.) | AC-18 |
| T-209 | Orchestrator doctrine: drop the "when the directory exists" condition, unconditional `--context` at turn/feature open + `sync-notes` at phase close; allowlist `--context*` as a READ-ONLY third sanctioned channel in `coord_policy.py`/`generate.py` | AC-19 |
| T-210 | `render_notes()`: log BOTH the outer (`:1098-1099`) and inner (`:1091`) swallowed exceptions, with a destination/size-cap/rotation; cross-project isolation (project X's status check never shows project Y's failure) | AC-20 |
| T-211 | Headless degrade: no Obsidian/no manager ⇒ file vault keeps working, `--vault-doctor` reports WARNING only; a `TOOL_MANUAL`/exit-1 install attempt inside `--scaffold` never propagates as a scaffold failure; a persisted decline is a steady non-repeating WARNING | AC-21 |

Ownership: `tools.toml`, `ai/scripts/set_agents_app.py` (vault section `:946-1157` + tools `:622-709` + new
`--context`/`--vault-doctor` surfaces + `menu()`'s `first_run()`), `PROYECTO/ai/scripts/feature-state.py`,
`Global/_canonical/agents/orchestrator.md`, `docs/adr/0009-*.md`, `.github/workflows/ci.yml`,
`tests/test_harness.py`.

## P3-tui

| ID | Work item | Acceptance |
|---|---|---|
| T-300 | `ai/scripts/tui.py`: pure `(state, key) -> state` core, unit-tested without pty | AC-22 |
| T-301 | Raw-byte key decoder: ANSI arrow sequences (`\x1b[A` and `\x1bO` variants), UTF-8 multibyte, bracketed-paste immunity — unit-tested separately from the pure core | AC-23 |
| T-302 | Raw-mode reader + render loop (alternate screen, box-drawing, arrows, `/` search WITH a free-text fallback mode for pickers that support it today, ESC/Ctrl-C) reusing `use_color()`/`color()`/`bold()`/`dim()`/`_lerp()`/`_gradient_row()`/`banner()` | AC-24 |
| T-303 | Replace `menu()`/`tools_menu()`/`mcp_menu()`/`plugins_menu()`/`vault_menu()` + `setup_models.py`'s `choose()`/`wizard()`; preserve `choose()`'s free-text fallback explicitly | AC-24 |
| T-304 | Regression-lock: `test_banner_degrades_without_tty` keeps passing; non-TTY stdin pre-menu check keeps its exact exit-2 shape | AC-25 |
| T-305 | `run_tty()` exits raw mode/alternate screen before `install.sh`/`setup-models.sh`/`build.sh --install`; WIDEN the same handoff to every in-process `input()` prompt reachable from the selector (`cmd_tools_install`'s sudo confirm, `mcp_menu`'s free-text prompts) | AC-26 |
| T-306 | `finally`-block + `SIGTERM`/`SIGHUP` handlers restore terminal state on abnormal exit; test forces an exception inside the render loop | AC-27 |
| T-307 | Separate data-from-print in `cmd_plugins`/`cmd_mcp`/`cmd_tools`/`cmd_status` so the menu renders human output from the same data machine-format callers already get | AC-28 |
| T-308 | Menu debt: reorder Vault before Salir, validate `mcp_menu`'s free-text inputs, human-readable plugin display, graceful invalid-input handling, no tracebacks on `EOFError`/`KeyboardInterrupt`; update `README.md`/`INSTALACION.md` grids and stale line-number references | AC-29, AC-30 |

Ownership: `ai/scripts/tui.py` (new), `ai/scripts/set_agents_app.py` (menu functions + `cmd_*` refactor),
`ai/scripts/setup_models.py`, `README.md`, `INSTALACION.md`, `tests/test_harness.py`.

## Global

| ID | Work item | Acceptance |
|---|---|---|
| T-400 | Focused suites per package; `verify.sh` green (net assertion count never shrinks; asserts zero absolute paths / placeholder presence in `Global/**`); GateSpecs for `--scaffold`/`--context`/`--project`/`--vault-doctor`; `docs/architecture/` updated including the SCHEMA 4→5 backward-incompatibility note; `proposal.md` (new deliverable) aligned with this contract | AC-31 |

## Risks

- **`Global/**` path-leak regression (P1/T-101,T-102) — the single highest-severity finding from the
  spec-challenge.** Baking `HARNESS_HOME` at generate/build time (rather than install time) would commit a
  developer's own absolute path into tracked files and break `verify.sh` on every other machine. Mitigation:
  the placeholder-only invariant is itself a regression test (`Global/**` contains `__SET_AGENTS_ROOT__` and
  zero absolute paths), not just a design intention.
- **Real-data migration (P2/T-206).** The four `~/iey/` projects hold real user notes lost from version
  control since 2026-07-23, and `iey-ai` requires a MERGE, not a pure move (13/29 files). Mitigation:
  `--dry-run` first, copy-verify-then-delete (never a bare `shutil.move`), abort-on-any-byte-mismatch,
  explicit confirmation separate from the dry-run, privacy preserved via `exclude_notes_from_git()` per
  DEC-5, no auto-run as part of a generic doctor pass.
- **Security surface change (P1/T-105).** Moving the context-pack confinement from `ROOT` to `PROJECT_ROOT`
  requires the security-auditor to re-derive SEC-A02 against the new anchor AND its new trust level
  (third-party repo content, not the harness's own tree). Mitigation: AC-04 requires both halves explicitly;
  the package review panel for P1 MUST include `security-auditor`.
- **SQLite schema migration (P1/T-107).** SCHEMA 4→5 on a routing DB with real runs from 004's usage, plus
  a semantic backfill decision (pre-005 rows belong to the harness's own `project_key`) and a documented
  backward-incompatibility consequence for pre-005 checkouts. Mitigation: additive column + CHECK
  constraints, single-transaction migration, live-DB backup, tested against a copy before the live DB.
- **Two coexisting vault topologies without a disambiguator (P2/T-202).** `--private` surviving (DEC-6)
  means an auto-repairer cannot infer intent from directory shape alone. Mitigation: the persisted registry
  is a hard prerequisite for any repair action — no entry, no touch.
- **Test that changes sign (P2/T-203).** `test_notes_autorender_on_state_mutation_and_optin_by_dir`'s
  opt-in-by-directory assertion is REPLACED by its documented opposite (opt-in-by-`ai/state/`) — a
  spec-approved behavior change; half (a) of the test is preserved verbatim. The package's evidence file
  must name the old assertion, the new one, and the spec clause that authorizes the flip.
- **Cross-package template drift (P1/T-109 vs P2/T-203).** Both P1's self-scaffold and P2's `notes_root()`
  edit touch `PROYECTO/ai/scripts/feature-state.py`. Mitigation: P2 explicitly re-runs P1's drift check
  before its own gates (documented in T-203), so the harness's own copy never silently diverges mid-feature.
- **Guest proof requires a genuinely isolated environment (P1/T-111).** Mitigation unchanged from 1.0.0: one
  `tempfile.TemporaryDirectory()` tree for clone + `$HOME` + scaffolded project, never the developer's real
  paths; executed by a role other than the implementer (separation of duties).
- **In-process prompts under raw mode (P3/T-305).** `input()` doesn't echo correctly under raw
  mode/alternate screen — unreadable consent is not consent, and this affects MORE than the subprocess
  launches `run_tty` already covered (sudo confirmation, MCP free-text prompts). Mitigation: AC-26 widens
  the terminal-handoff contract to every in-process prompt reachable from the selector, not only
  subprocess launches.

## Execution

Feature `005-portable-harness` follows the harness's own cycle: `REQUIREMENTS → SPEC_DRAFT →
SPEC_CHALLENGE → USER_APPROVAL`, then `P1-portable-core → P2-vault-mandatory → P3-tui`, each with
implement → gates independent of the others → review panel → repair → delta-review → accept, before
`INTEGRATION`. This plan is the post-spec-challenge revision (contract 1.1.0); a delta re-challenge and
user approval are the next steps before `PACKAGE_PLANNING` opens.
