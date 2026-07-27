# Feature 005 — acceptance scenarios (BDD, contract 1.1.0)

Given/When/Then per AC. Regression tests are written after convergence and assert these observables.
Amended from 1.0.0 after spec-challenge (see `spec.md`'s Amendment log for the full old→new AC map).

## Flow diagram (actor → action → observable outcome)

```
GUEST                     HARNESS (any HARNESS_HOME)         PROJECT (any PROJECT_ROOT)          VAULT
  |                              |                                    |                            |
  | git clone SET-AGENTES        |                                    |                            |
  |------------------------------>                                    |                            |
  | ./install.sh                 | validates HARNESS_HOME (AC-02),    |                            |
  |------------------------------>  bakes it ONLY into INSTALLED      |                            |
  |                              |  files (AC-01) — Global/** stays   |                            |
  |                              |  __SET_AGENTS_ROOT__, untouched    |                            |
  |                              |                                    |                            |
  | set-agents --scaffold DIR    |                                    |                            |
  |------------------------------> P1: ai/state/features/, generic    |                            |
  |                              | scripts, persistent project-id     |                            |
  |                              |------------------------------------> (AC-06, AC-07)              |
  |                              | P2: docs/notas/ (if ai/state/       |                            |
  |                              | marker present, AC-13) + vault link|                            |
  |                              |------------------------------------> docs/notas/ (AC-13)          |
  |                              |------------------------------------------------------------------> symlink +
  |                              |                                    |                            |  registry entry
  |                              |                                    |                            |  (AC-12, AC-16)
  |                              |                                    |                            |
  | cd DIR ; open orchestrator   |                                    |                            |
  |------------------------------>                                    |                            |
  |                              | orchestrator runs --context        |                            |
  |                              | (allowlisted read-only, AC-19,     |                            |
  |                              |  ORQ-1)                            |                            |
  |                              |------------------------------------------------------------------> reads hub +
  |                              |<------------------------------------------------------------------ contexto.md +
  |                              |  (AC-18)                           |                            |  00 - Proyecto.md
  |                              |                                    |                            |
  | orchestrator delegates role  |                                    |                            |
  |------------------------------> --route-decide: PROJECT_ROOT-      |                            |
  |                              |  scoped context pack (AC-03,AC-04),|                            |
  |                              |  self-inclusive walk-up (AC-03)    |                            |
  |                              |------------------------------------> run_id carries project_key  |
  |                              |  (AC-05: persisted id, fail-closed |  (never crosses projects)  |
  |                              |   on mismatch)                     |                            |
  |                              |                                    |                            |
  |                              | feature-state mutation             |                            |
  |                              |------------------------------------> render_notes() writes       |
  |                              |                                    |  docs/notas/*.md; both      |
  |                              |                                    |  swallow points logged      |
  |                              |                                    |  (AC-20)                    |
  |                              |                                    |------------------------------> visible in
  |                              |                                    |                            |  Obsidian graph
  |                              |                                    |                            |
  | ./set-agents  (arrow menu)   |                                    |                            |
  |------------------------------> TUI: navigate (AC-22,AC-23),       |                            |
  |                              |  exits raw mode before EVERY       |                            |
  |                              |  in-process prompt incl. sudo      |                            |
  |                              |  confirm (AC-26), restores on      |                            |
  |                              |  abnormal exit too (AC-27);        |                            |
  |                              |  `--status` / non-TTY keeps        |                            |
  |                              |  machine format (AC-25, AC-28)     |                            |
  |                              |                                    |                            |
  | set-agents --vault-doctor    |                                    |                            |
  |------------------------------> report-only by default; --repair  |                            |
  |                              | needs dry-run-confirmed marker      |                            |
  |                              | (AC-17); never touches an          |                            |
  |                              | unregistered project (AC-12)       |                            |
```

## P1-portable-core

**AC-00 ADR-0008**
- Given P1 starts, When the first P1 code lands, Then `docs/adr/0008-two-roots-portability.md` records the
  `HARNESS_HOME`/`PROJECT_ROOT` doctrine, install-time-only baking, the allowlist dual fix, the corrected
  walk-up, the SEC-A02 trust-boundary reframing, the persistent project-id mechanism, and the SCHEMA 4→5
  migration mechanics (backup, atomicity, backfill semantics, backward-incompatibility note).

**AC-01 path baking is install-time-only**
- Given `./build.sh --output STAGING` regenerates `Global/**`, When the tracked `Global/**` tree is diffed
  against `STAGING`, Then they are byte-identical AND both contain the literal `__SET_AGENTS_ROOT__` string
  wherever the routing CLI path or `HARNESS_HOME` is referenced (JSON, `coord_policy.py`,
  `orchestrator.md`/`.toml`) — zero absolute filesystem paths in either.
- Given a real `./install.py` run for machine M with `HARNESS_HOME=/some/absolute/path`, When the installed
  `hooks/coord_policy.py` and installed `agents/orchestrator.md` are inspected, Then `__SET_AGENTS_ROOT__` is
  gone and replaced by M's real absolute path.
- Given a `verify.sh` run on a DIFFERENT machine than the one that last regenerated `Global/**`, Then it
  still passes (no machine-specific path ever entered the tracked tree).

**AC-02 allowlist matcher survives spaces, rejects hostile paths**
- Given a `HARNESS_HOME` containing a literal `;` or a backtick, When `install.py` runs, Then installation
  is REFUSED with a clear, actionable error naming the offending character — never a silent broken install.
- Given a `HARNESS_HOME` containing a space (e.g. `/Users/Jane Doe/SET-AGENTES`), When the orchestrator
  invokes `python3 "<that path>/ai/scripts/set_agents_app.py" --route-decide -`, Then `coord_policy.py`'s
  `allowed()` matches it (post-`shlex.split` argv comparison), not blocked by quoting.

**AC-03 project-root walk-up, corrected**
- Given `cwd` IS the project root itself (no `--project`, no `SET_AGENTS_PROJECT`), When
  `find_project_root` runs, Then it resolves to `cwd` itself (self-inclusive — regression-locks the
  `find_vault`-inherited "excludes self" bug).
- Given a directory tree where `$HOME/ai/state/features/` exists (unrelated to any real project) and the
  actual project's `.git` is TWO levels below `$HOME`, When resolving from inside the project, Then the
  project's own nearer `.git` wins — the stray higher-up state dir never outranks it (both markers checked
  per level, nearest-ancestor-wins).
- Given `--project DIR` AND a different `SET_AGENTS_PROJECT` AND a resolvable walk-up target all present,
  When resolving, Then `--project` wins.
- Given no marker found in `[start] + ancestors` all the way to `/`, Then resolution stops there — no crash,
  no infinite loop.

**AC-04 SEC-A02 re-derivation with trust-boundary content**
- Given a foreign or malformed `feature-state.json` inside `PROJECT_ROOT`, When
  `_validate_context_pack_path` runs, Then traversal-outside-`PROJECT_ROOT` degrades to "no pack" (crash-free,
  unconfined-join-free) — asserted by the security-auditor's re-derivation.
- Given the security-auditor's package review, Then the evidence names the exact paths `--route-decide`/
  `--context` may read under `PROJECT_ROOT`, the byte cap applied to anything surfaced to an agent from
  there, and an explicit statement that this content is data, never instructions.

**AC-05 project-scoped routing DB with a persisted identity**
- Given two different projects each authorizing a writer run, When either requests `review_of_run_id`
  independence, Then only a run sharing the SAME `project_key` satisfies it.
- Given a project directory that gets MOVED or RENAMED after scaffold, When a subsequent `--route-decide`
  runs from the new location, Then `project_key` is UNCHANGED (read from the persisted id file, not
  re-derived from the new path).
- Given no persisted id file exists (pre-005 edge case), When resolving, Then the path-hash fallback is used,
  documented as a fallback, not the primary mechanism.
- Given the SCHEMA 4→5 migration runs against the existing DB, Then a backup of the live DB file exists
  before any ALTER, the migration runs inside one transaction, every pre-existing row (including any
  non-terminal one) is backfilled with the harness's OWN persisted `project_key`, and
  `--routing-report`/`--routing-open-runs`/`--routing-recent-writers` keep working for that data afterward.
- Given a `project_key` mismatch during an independence check, Then the decision DENIES (never grants) —
  fail-closed, asserted explicitly, including the "no prior runs in this project" case (nothing to match,
  same denial).
- Given a pre-005 checkout of the harness reads a post-005 (schema-5) DB, Then it fails closed via the
  existing `schema_version != SCHEMA` check (`ROUTING_UNAVAILABLE`) — documented, not a new failure mode.

**AC-06 P1-scoped scaffold**
- Given an empty target directory, When `set-agents --scaffold DIR` runs, Then (P1 portion)
  `ai/state/features/`, the generic scripts, and a persisted project-id file all exist afterward — with NO
  dependency on vault/Obsidian machinery for this portion to succeed.
- Given the same command run twice, Then the second run is a no-op for every already-present file.

**AC-07 harness self-scaffold, scoped drift check**
- Given `SET-AGENTES/ai/scripts/feature-state.py` compared against `PROYECTO/ai/scripts/feature-state.py`,
  Then byte-identical (same for `check-owned-paths.py`).
- Given a deliberately diverged copy, When `./build.sh --check` runs, Then it fails naming the diverged
  file — and this check is verified to be DISTINCT from `check-drift.sh` (a different, installed-vs-repo
  check) and from `verify.sh`'s `Global/**` diff (a different, tracked-vs-regenerated check).
- Given P2 edits `PROYECTO/ai/scripts/feature-state.py` for AC-13, When P2's gates run, Then this drift
  check is re-run (and passes) BEFORE P2's own gates proceed.

**AC-08 degrade honest, extended, non-git case clarified**
- Given a `cwd` with neither `ai/state/features/` nor `.git` in `[start]+ancestors`, When routing is
  attempted, Then a stable unavailable outcome fires and the BASE agent spawns.
- Given a scaffolded directory that has `ai/state/features/` but NO `.git` (not yet version-controlled),
  When routing is attempted, Then it resolves normally as a valid `PROJECT_ROOT` — NOT a degrade case.
- Given Pi starts from a user-project subdirectory, When its lifecycle invokes `--route-decide`,
  `--route-dispatched`, and any normal or exception-path `--route-terminal`, Then every invocation uses the
  same explicit routing cwd, and the resulting `dispatches.project_key` is the user project's persisted id;
  Pi's own execution cwd remains unchanged.

**AC-09 the guest proof — hermetic scripted test**
- Given a role OTHER than the implementer runs the test (gate-runner/package-reviewer, never
  self-attested), inside fully isolated temp directories (clone, `$HOME`, and scaffolded project all under
  one tree sharing nothing real), When the matrix runs — (1) harness cloned under a non-`SET-AGENTES` dir
  name, (2) fake `$HOME` with no `~/.local/bin` on PATH, invoking the absolute script path directly,
  (3) `HARNESS_HOME` containing a space, (4) a scaffolded project with no `.git`, (5) `verify.sh` from the
  guest clone — Then every case reports a named observable (exit code, parsed JSON envelope, and for cases
  (1)-(4) the concrete `project_key` value matching the guest project's persisted id) and all pass.
- Given anything beyond this matrix (a real interactive terminal, a real OS-level install), Then it is a
  declared MANUAL CHECKPOINT, never presented as this AC's machine verification.

## P2-vault-mandatory

**AC-10 ADR-0009**
- Given P2 starts, Then `docs/adr/0009-mandatory-vault.md` records DEC-5/6/7, the backup/rollback doctrine,
  and the merge-case algorithm grounded in `evidence/vault-migration-inventory.md`.

**AC-11 multi-OS install, three verification tiers**
- Given `shutil.which` mocked to simulate each of pacman/apt/dnf/zypper/brew/winget/choco/none, When
  `platform_pm()`/`pick_method()` run, Then each resolves correctly and `--dry-run` prints
  `TOOL_PLAN <name> method=<m>` with zero installs — this table-driven suite runs on ALL THREE CI runners.
- Given the `windows-latest` CI job, Then it runs the full `unittest` suite (no longer parse/dry-run/compile
  only).
- Given the resolved install command starts with `sudo`, Then it is never silent, never auto-confirmed with
  `--yes`, and prints `TOOL_MANUAL`+exit 1 without a TTY — byte-identical to the pre-existing contract.
- Given a real macOS or Windows GUI install, Then it is documented and executed as a MANUAL CHECKPOINT, never
  claimed as machine-verified.

**AC-12 persisted vault-link intent marker**
- Given `--vault-link` runs in hybrid mode, Then a registry entry records topology=`hybrid`, vault path,
  full repo path, and linked-at.
- Given `--vault-link --private` runs, Then the entry records topology=`private`.
- Given the vault status surface inspects a directory with NO registry entry, Then it reports
  "unregistered" and takes no repair action.
- Given two repos share a basename at different paths, Then the registry disambiguates by full path, never
  basename.

**AC-13 notes mandatory, scoped to harness-managed projects**
- Given a directory with `ai/state/` present (harness-managed) and no `docs/notas/` yet, When any state
  mutation runs, Then `docs/notas/` is created and written into.
- Given a directory WITHOUT `ai/state/` that someone merely `cd`-ed into, When any command runs, Then no
  `docs/notas/` is created there.
- Given `tests/test_harness.py:611-621` ("mutation refreshes notes without `sync-notes`"), Then it passes
  UNCHANGED, verbatim.
- Given the replacement for 622-628 (opt-in-by-`ai/state/` instead of opt-in-by-`docs/notas/`), Then the
  test's total assertion count is greater than or equal to before — never fewer assertions.

**AC-14 managed `.obsidian/`**
- Given a freshly linked vault, Then `.obsidian/{app,appearance,core-plugins}.json` exist with the fixed
  core-plugin set and no community-plugin manifest.

**AC-15 vault config persistence, all writers**
- Given `--vault-init TARGET`, Then `app_config()["vault"]` reads back `TARGET` afterward.
- Given a FIRST RUN of the app (today's `first_run()` raw-overwrite path) after a `vault` key was already
  persisted, When first-run logic executes, Then the `vault` key SURVIVES (read-merge-write, not a raw
  overwrite) — regression-locks the `menu()`/`:1239` fix.

**AC-16 real-data migration — merge-aware, privacy-preserving, backup/rollback**
- Given one of the three "pure move" `~/iey/` projects (repo side absent), When `--dry-run` runs, Then it
  reports the exact files that would move, zero writes.
- Given `iey-ai` (repo side already holds 2 non-harness files), When `--dry-run` runs, Then it reports a
  MERGE plan: 13 files move in as new paths, the 2 pre-existing files are untouched, zero conflicts (matches
  the evidence file's `comm -12` result).
- Given a byte-identical file on both sides, Then it is skipped (dedup), not re-copied, not flagged.
- Given a byte-DIFFERING file on both sides, Then the WHOLE operation aborts with `VAULT_LINK_CONFLICT`,
  zero files moved.
- Given the repo side is ALREADY a symlink (dangling, or an outward legacy `--private` link), Then this is
  reported as a distinct case, never silently overwritten as if "absent".
- Given explicit confirmation after a clean dry-run, When migrating, Then each file is copied to its
  destination and byte-verified BEFORE the vault-side original is removed; an interruption mid-migration
  leaves both copies present; a re-run is idempotent.
- Given migration completes for the four real projects, Then `.git/info/exclude` contains `docs/notas` for
  each (via `exclude_notes_from_git()`), and the registry entry (AC-12) records the exclusion.

**AC-17 vault status/repair — new distinct surface**
- Given `set-agents --vault-doctor` (default, no `--repair`), Then it lists each registered project's state
  (healthy/real-dir-drift/dangling/unregistered) and takes NO repair action.
- Given `--vault-doctor --repair` on a project WITHOUT a dry-run-confirmed marker, Then it refuses to repair
  and reports why.
- Given `--vault-doctor --repair` on a project WITH the marker, Then it repairs via AC-16's migration.
- Given `--doctor --harness pi`, Then its envelope, schema, and exit codes are BYTE-IDENTICAL to 004's —
  this feature adds nothing to that function.

**AC-18 `--context`, fully specified**
- Given `--context --project DIR`, Then it emits `{hub, company, project, pending}`, each capped, read-only.
- Given no vault found, Then a stable `VAULT_NOT_FOUND`-shaped result returns, no crash.
- Given no company directory resolvable, Then hub-only output.
- Given no `00 - Proyecto.md`, Then that field reports absent (never fabricated).
- Given `--context`'s file reads, Then `~/.pi/agent/auth.json` and any other credential surface is never
  touched, asserted by a test enumerating what paths were opened.

**AC-19 orchestrator doctrine, unconditional, read-only allowlist**
- Given the canonical orchestrator prompt, Then the "when the directory exists" condition is gone —
  unconditional MUST for `--context` at turn/feature open and `sync-notes` at phase close.
- Given `coord_policy.py`'s allowlist, Then `--context*` matches as a THIRD sanctioned channel, documented
  as read-only (never mutating), distinct from the routing CLI's mutating-capable exception.

**AC-20 failure visibility, both swallow points**
- Given a note-render failure injected at the OUTER swallow point (`:1098-1099`), Then it is logged and
  surfaced at the next status check; state mutation still succeeds.
- Given a note-render failure injected at the INNER, per-feature swallow point (`:1091`), Then it is ALSO
  logged and surfaced (this one was unnamed in 1.0.0).
- Given a failure recorded for project Y, When a status check runs for project X, Then project X's report
  never shows project Y's failure.

**AC-21 headless degrade, precedence stated**
- Given no Obsidian binary and no recognized package manager, When any mutation or `--vault-doctor` runs,
  Then the file vault keeps working and the exit code is not made non-zero solely by the missing GUI.
- Given `cmd_tools_install` returns `TOOL_MANUAL`/exit 1 for a no-TTY/no-manager install attempt made during
  `--scaffold`, Then `--scaffold` AS A WHOLE still exits 0 (the install attempt's own exit code never
  propagates as a scaffold failure).
- Given a declined/impossible install was already recorded, When `--scaffold` runs again, Then no re-prompt
  loop occurs — a steady WARNING is reported instead.

## P3-tui

**AC-22 pure core**
- Given `tui.py`'s core function called directly with a state and a key event, Then it returns the next
  state deterministically, unit-tested with zero terminal I/O.

**AC-23 raw-byte key decoder**
- Given raw bytes `\x1b[A` and the `\x1bO` variant, Then both decode to the same logical up-arrow event.
- Given a UTF-8 multibyte sequence typed into the `/` search box, Then it decodes to the correct character(s),
  not garbled or split.
- Given a bracketed-paste sequence, Then it is never interpreted as navigation keys.

**AC-24 full menu replacement, free-text fallback preserved**
- Given the model-id picker (today `setup_models.choose()`), When the user presses `/` and types a value
  not in the listed options, Then it is accepted as free text — the fallback `choose()` supports today is
  not silently dropped by the new selector.

**AC-25 tty contracts, regression-locked**
- Given stdout redirected to non-TTY, Then zero ANSI bytes appear.
- Given stdin from `/dev/null`, Then help prints and exit is 2, never entering the menu.

**AC-26 terminal handoff for every in-process prompt**
- Given the user selects an option that shells out to `install.sh`/`setup-models.sh`/`build.sh --install`,
  Then the terminal is in normal mode at the sudo/login prompt moment, restored after.
- Given `cmd_tools_install`'s in-process sudo confirmation (`input()`) is reached from the new selector,
  Then the terminal exits raw mode/alternate screen for that prompt's duration too — not only for
  subprocess launches.
- Given `mcp_menu`'s free-text prompts reached from the new selector, Then the same terminal-handoff applies.

**AC-27 abnormal-exit terminal restoration**
- Given an exception is deliberately raised inside the render loop, Then the terminal is restored to normal
  mode via a `finally` block regardless of the exception path.
- Given a `SIGTERM` or `SIGHUP` is delivered while the TUI is in raw mode, Then a signal handler restores
  the terminal before the process exits.

**AC-28 `cmd_*` surface preserved**
- Given `set-agents --status`/`--tools`/`--mcp`/`--plugins`, Then each prints today's exact machine format,
  unchanged.

**AC-29 menu debt**
- Given the menu, Then `[9] Vault` appears before Salir; `mcp_menu`'s free-text inputs are validated;
  `plugins_menu` shows human-readable text; invalid input is never silently ignored; `EOFError`/
  `KeyboardInterrupt` exit cleanly, no traceback.

**AC-30 docs updated**
- Given `README.md`/`INSTALACION.md`, Then the numbered-grid duplication is replaced, including the
  previously-missing `[9] Vault`.

## Global

**AC-31** — `verify.sh` green (net assertion count never shrinks; asserts zero absolute paths / placeholder
presence in `Global/**`); GateSpecs cover `--scaffold`, `--context`, `--project`, `--vault-doctor`;
`docs/architecture/` documents the two-roots model, the vault topology, and the SCHEMA 4→5
backward-incompatibility consequence; `proposal.md` stays aligned with this contract.
