# Feature 005 — portable-harness, contract 1.1.0

Status: SPEC_DRAFT v2 (post spec-challenge rework; pending re-challenge delta and user approval).
Depends on: feature 004 (adaptive-dispatch) DONE — P1-dispatch-core, P2-opencode-lane, P3-pi-lane all
ACCEPTED (`ai/state/features/004-adaptive-dispatch.json`, phase `DONE`). Inherits every 004 invariant
unchanged: the routing brain (task descriptor in, `(model, effort, runtime, tier)` out of the curated
catalog), the tier model, AM-1/AM-2 fact derivation and probe-cache doctrine, the `abandoned` lifecycle
state (SCHEMA=4), and the R3 threat model (in-process/same-UID adversary out of scope) carried from 003.
This feature does not touch WHAT gets routed or WHY — it touches WHERE the harness, the router, and the
project state live, and how a human drives the console app. No routing decision, tier, or catalog semantic
changes.

## Amendment log (1.0.0 → 1.1.0)

The independent, read-only spec-challenger reviewed contract 1.0.0 and returned `revision_required`: 15 HIGH
findings (SC-01..SC-16) and 14 MEDIUM findings (SC-17..SC-29, SC-27 being the missing `proposal.md`
deliverable rather than a content gap). The challenger explicitly endorsed the spec audit's structure
(named absence universes, the pairwise-conflict pass, tagged UNVERIFIED items) — every finding is a GAP
inside that framework, not an absence of the framework, so the audit's shape is preserved and extended, not
replaced.

Three user decisions were taken (DEC-5, DEC-6, DEC-7 — contract, not re-litigated) and six decisions were
taken by the orchestrator, acting within its delegated authority over non-product HOW-adjacent choices that
block an AC from being executable (ORQ-1..ORQ-6). Both sets are recorded below alongside every SC finding's
resolution. Net effect: AC-01/AC-04/AC-06 from 1.0.0 are split (path-baking mechanics separated from the
allowlist-matcher fix; the SEC-A02 re-derivation gains an explicit trust-boundary section; the unified
scaffold is split across P1/P2 per ORQ-6); AC-07 (P1.0.0) is rewritten as a hermetic scripted test (was a
prose end-to-end description); AC-13/AC-14 (P1.0.0 vault migration/doctor) are rewritten around the intent
marker (DEC-6) and the real evidence inventory (below); a NEW distinct vault status/repair surface replaces
any reuse of `--doctor --harness pi`; two NEW P3 ACs are added (raw-byte key decoding, abnormal-exit
terminal restoration). The full old→new AC map is in the table at the end of this section. `proposal.md`
is added as a new deliverable (SC-27).

**User decisions (contract):**

- **DEC-5 (migration privacy — amends DEC-1).** The four `~/iey/` projects are recovered into their repos
  but NOT versioned yet: `.git/info/exclude`'s `docs/notas` line is KEPT after migration (reusing the
  existing `exclude_notes_from_git()` function at `set_agents_app.py:1042-1053`, today only called from
  `vault_link_private`). DEC-1's promise changes from "versioned in the project's own git" to "versionable —
  on by default for NEW projects, deferred with a local git exclusion for the four migrated projects until
  the user confirms, per project, that it should be tracked." Closes the privacy half of SC-09; the other
  half (backup/rollback before any `shutil.move` over unrecoverable data) is specified in AC-16.
- **DEC-6 (`--private` survives).** The `--private` mode stays a supported, explicit mode. Hard consequence:
  because two opposite topologies (hybrid and private) now coexist, an auto-repairer CANNOT tell "hybrid
  with a lost link" from "private, deliberately" without positive evidence. A PERSISTED PER-PROJECT INTENT
  MARKER (topology chosen + origin repo, recorded at link time) is required, and the repairer NEVER acts on
  a directory that lacks one. Closes SC-10 and supplies the vault-dir → repo mapping SC-08 found missing.
- **DEC-7 (OS matrix — three honest verification tiers).** Linux/macOS/Windows support is a promise, but
  "verified" is defined at three levels so the claim is never inflated: (a) MACHINE-VERIFIED ON ALL THREE
  CI RUNNERS — table-driven tests of `platform_pm()`/`pick_method()` with `shutil.which` mocked across
  pacman/apt/dnf/zypper/brew/winget/choco and the "no manager" case; `--dry-run` plan assertions
  (`TOOL_PLAN <name> method=<m>`) per manager, zero installs; the `windows-latest` CI job stops being
  parse-only and runs the full `unittest` suite (a real widening of `.github/workflows/ci.yml`, delivered by
  this feature); (b) SOURCE-VERIFIED — exact package identifiers (`winget`, `choco`, official `.deb`, `dnf`,
  `zypper`) cited against Obsidian's own documentation, in the ADR; (c) MANUAL CHECKPOINT, DECLARED AS SUCH
  — a real end-to-end GUI install on macOS and Windows is a human checkpoint, never a machine-verified AC.
  Closes SC-20.

**Orchestrator decisions (delegated, taken as given):**

- **ORQ-1 (closes SC-06).** `python3 <HARNESS_HOME>/ai/scripts/set_agents_app.py --context*` is allowlisted
  as READ-ONLY in `coord_policy.py`'s `SAFE` list and in `generate.py`'s emitted lines — a THIRD sanctioned
  channel, distinct from the state CLI and the routing CLI. Unlike `--route-decide` (mutating-capable,
  authorizes durable runs), `--context` never writes anything — it is allowlisted as read-only specifically
  because AC-19 (orchestrator MUST read context) is unexecutable without it.
- **ORQ-2 (closes SC-16).** `project_key` is NOT path-hash-only. A stable per-project id is PERSISTED (a
  small file under `ai/state/`, written once at scaffold time) that survives moving/renaming the project
  directory; the resolved-path hash is a FALLBACK used only when no id file exists. Normalization: `realpath`
  resolution, case-normalized on case-insensitive filesystems. Fail-CLOSED, explicit: a `project_key`
  mismatch means reviewer independence is DENIED, never granted. The "no prior runs in this project" case
  resolves to "independence trivially unsatisfiable" (no writer run exists to match against), same denial
  shape, not a special case.
- **ORQ-3 (closes SC-11, SC-12).** `notes_root()` creates `docs/notas/` ONLY when the directory is a
  harness-managed project — marker: `ai/state/` exists — NEVER in an arbitrary directory or a third party's
  repo someone merely `cd`-ed into. The opt-in test shifts from "does `docs/notas/` exist" to "does
  `ai/state/` exist". `tests/test_harness.py:611-621` (half (a): "a state mutation refreshes notes without
  calling `sync-notes`") is PRESERVED VERBATIM; half (b) (622-628, the opt-in-by-directory assertion) is
  replaced by its documented opposite, named against its authorizing spec clause in the package's evidence,
  and the test's total assertion count never shrinks.
- **ORQ-4 (closes SC-07, half of SC-14).** The new vault status surface (AC-17) is REPORT-ONLY by default.
  Repair requires BOTH (i) an explicit flag and (ii) a per-project "dry-run seen and confirmed" marker (from
  DEC-6's intent-marker mechanism). It never repairs during a generic or headless run, and it never touches
  unrecoverable data by default.
- **ORQ-5 (closes SC-13).** The 004 envelope `--doctor --harness pi` (`cmd_doctor`, `set_agents_app.py:
  359-368`, pinned to schema-2 by 004's AC-09, `DOCTOR_HARNESS_UNSUPPORTED` for any other/absent harness) is
  UNTOUCHED — a new non-goal states this explicitly. Vault status/repair lives on a DISTINCT, separately
  named surface (AC-17), never on `--doctor --harness <anything>`.
- **ORQ-6 (closes the other half of SC-14).** AC-04 (1.0.0) is split: the `ai/state/features/` + generic-
  script-copy + persistent project-id piece stays in P1 (AC-06 in 1.1.0); the vault-link call moves to P2
  (part of AC-16/AC-12). `T-107`'s erroneous `AC-13` co-assignment (`plan.md:20` in 1.0.0) is removed. The
  plan gains an explicit obligation: P2, after editing `PROYECTO/ai/scripts/feature-state.py` for AC-13/
  ORQ-3, MUST re-run P1's AC-07 drift check before its own gates — otherwise P1's self-scaffold drift check
  breaks silently during P2.

**Evidence used, not re-derived:** `docs/specs/005-portable-harness/evidence/vault-migration-inventory.md`
(gathered read-only by the orchestrator, 2026-07-27) closes the "Could not verify" line the 1.0.0 spec audit
left open. Measured facts: all four `~/iey/` vault entries are REAL DIRECTORIES (legacy `--private`
topology), all four target repos exist, 29 files total, zero name collisions, and `iey-ai` is the ONE case
where the repo side is NOT absent — it already holds `docs/notas/` with 2 non-harness-generated files
(`analisis-puntos-de-dolor-2026-07-23.md`, `README.md`), so the migration for that project is a MERGE of 13
vault files into an existing directory, not a pure move — 13 of the 29 files (45%) are in the one case a
pure-move-only implementation would handle incorrectly. AC-16 requires the merge case explicitly.

**Old (1.0.0) → new (1.1.0) AC map:**

| 1.0.0 | 1.1.0 | What changed |
|---|---|---|
| AC-00 | AC-00 | + project-id persistence, SEC-A02 trust reframing, SQLite migration mechanics recorded in ADR-0008 |
| AC-01 | AC-01 + AC-02 | split: install-time-only placeholder mechanics (AC-01) vs allowlist-matcher fix for spaces/metacharacters (AC-02) |
| AC-02 | AC-03 + AC-04 | split: walk-up algorithm fix (self-inclusive, both-markers-per-level) (AC-03) vs SEC-A02 trust-boundary content (AC-04) |
| AC-03 | AC-05 | + persistent project id (ORQ-2), SQLite migration mechanics (backup/atomicity/backfill semantics) |
| AC-04 | AC-06 | scope reduced to P1 only (ORQ-6); vault link removed |
| AC-05 | AC-07 | + explicit scope vs `check-drift.sh`/`verify.sh` (SC-28), + P2 re-sync obligation |
| AC-06 | AC-08 | + non-git-but-scaffolded case clarified |
| AC-07 | AC-09 | rewritten as a hermetic scripted test with named observables + environment matrix + named executor (SC-15) |
| AC-08 | AC-10 | + DEC-5/6/7 content, backup/rollback doctrine, merge-case algorithm |
| AC-09 | AC-11 | + DEC-7 three-tier verification model |
| — | AC-12 | NEW: persisted vault-link intent marker/registry (DEC-6) |
| AC-10 | AC-13 | scoped to `ai/state/`-marked projects (ORQ-3), test-preservation detail added |
| AC-11 | AC-14 | unchanged in substance |
| AC-12 | AC-15 | + ALL config writers must read-merge-write (SC-26, fixes `menu()`'s `first_run()`) |
| AC-13 | AC-16 | + DEC-5 privacy, backup/rollback, expanded universe (symlinks, missing repo, name collisions), MERGE case required |
| AC-14 | AC-17 | moved OFF `--doctor`; new distinct surface, report-only default + repair gate (ORQ-4/ORQ-5) |
| AC-15 | AC-18 | + `<COMPANY>` resolution, degrade cases, byte caps, `--json` schema, credential-surface non-goal |
| AC-16 | AC-19 | + ORQ-1 read-only allowlist requirement |
| AC-17 | AC-20 | + inner swallow point named, log destination/caps/cross-project isolation |
| AC-18 | AC-21 | + attempts-once/never-blocks/decline-persistence precedence |
| AC-19 | AC-22 | unchanged in substance |
| — | AC-23 | NEW: raw-byte key decoder tests |
| AC-20 | AC-24 | + free-text fallback preservation (SC-22) |
| AC-21 | AC-25 | unchanged in substance |
| AC-22 | AC-26 | scope widened to ALL in-process prompts, not only `run_tty` subprocesses (SC-21) |
| — | AC-27 | NEW: abnormal-exit terminal restoration |
| AC-23 | AC-28 | unchanged in substance |
| AC-24 | AC-29 | unchanged in substance |
| AC-25 | AC-30 | unchanged in substance |
| AC-26 | AC-31 | + SQLite backward-incompatibility doc requirement, + non-goals cross-references |
| — | (proposal.md) | NEW deliverable (SC-27) |

## Goal

Three closed gaps, all rooted in one assumption the harness currently hardcodes: **"the project" and "the
harness" are the same directory.**

1. **Portability.** Any git repo, on any machine, with the harness cloned at any path, gets the same
   adaptive routing that today only works standing inside `~/SET-AGENTES`. A guest clones, installs,
   scaffolds their own repo, and the orchestrator's `--route-decide` works from that repo's `cwd` — with
   per-project scoping so reviewer independence and rollups never cross between two projects sharing one
   router.
2. **Vault mandatory.** Obsidian stops being opt-in and write-only. It becomes the state/context
   controller: auto-scaffolded from minute zero (for harness-managed projects only), auto-installed with
   explicit sudo consent, auto-linked (hybrid: source in the repo, symlink from the vault, with `--private`
   surviving as an explicit alternative), and — the biggest gap — actually READ by the orchestrator without
   being asked, with a documented, non-blocking degrade when the OS has no supported package manager or the
   user declines the GUI install.
3. **TUI.** The numbered menu becomes an arrow-key selector, stdlib-only, with the existing CLI machine
   surface (`cmd_*`, `--json`, exit codes) byte-for-byte unchanged for scripted callers.

## Two-roots doctrine (closes B1–B7, and SC-01..SC-05)

- **`HARNESS_HOME`** — the absolute path of the cloned harness, resolved once, at INSTALL TIME, and baked
  ONLY into the per-machine INSTALLED artifacts under `$HOME` — never into the git-tracked `Global/**` tree.
  **This is the SC-01 fix, and it changes the mechanism from 1.0.0**: `verify.sh` (lines 9-16) regenerates
  `Global/**` into a temp staging dir with `./build.sh --output` and requires the TRACKED tree to be
  byte-identical (`diff -ruN "Global/$harness" "$STAGING/$harness"`); `generate.py:429` copies
  `coord_policy.py` VERBATIM into the tracked `Global/claude-code/hooks/coord_policy.py`, and the canonical
  orchestrator source (`Global/_canonical/agents/orchestrator.md`) is compiled by `generate.py` into
  `Global/{opencode,claude-code}/agents/orchestrator.md` and `Global/codex/agents/orchestrator.toml` — ALL
  tracked. If path-baking happened at `generate`/`build` time (as 1.0.0 implied), the committed `Global/**`
  files would carry the BUILDER's own absolute path, breaking `verify.sh` on every other machine (the
  regenerated copy there would bake a DIFFERENT path and never match the tracked one). Corrected doctrine:
  - `Global/**` (git-tracked) ALWAYS keeps the literal placeholder `__SET_AGENTS_ROOT__` — in JSON, in
    `coord_policy.py`, and in the compiled `orchestrator.md`/`orchestrator.toml` files alike. Regression:
    `Global/**` contains `__SET_AGENTS_ROOT__` and CONTAINS ZERO ABSOLUTE FILESYSTEM PATHS, checked by
    `verify.sh` after every build.
  - The substitution happens EXCLUSIVELY in `install.py`'s write path, at real-install time, against the
    REAL `HARNESS_HOME` of the machine being installed onto. `install.py:69-72`'s `merged_json` already
    does this for the two JSON install targets (`opencode.json`, the Claude settings overlay) via
    `json.dumps(str(REPO_ROOT))[1:-1]`, escaped for quotes/backslashes, regression-locked at
    `tests/test_harness.py:1637`. This feature EXTENDS the same install-time substitution to the two
    NEW non-JSON consumers: the installed `hooks/coord_policy.py` (plain Python text) and the installed
    `agents/orchestrator.md`/`.toml` files (plain text) — a generic "replace `__SET_AGENTS_ROOT__` in this
    installed file's bytes" step, not a JSON-specific one.
- **The coord allowlist match itself needs a second fix, independent of the baking mechanism (closes
  SC-02).** `coord_policy.py:34`'s `SAFE` pattern and `generate.py:210-212`'s emitted allow-lines match the
  RAW invocation string via `re.fullmatch` (`coord_policy.py:63`). Two real failure modes, verified:
  (1) `FORBIDDEN_SYNTAX` (`:37`, banning `; | || && \` $(` etc.) and the SAFE pattern's literal structure
  both operate on the raw string with no shell-quote awareness — a `HARNESS_HOME` containing a SPACE (the
  ordinary case on macOS `/Users/Name/...` and Windows `C:\Users\Name\...`/WSL-mounted paths) forces the real
  shell invocation to quote the path, and the SAFE regex (built by substituting the escaped root into a
  fixed template) will not match a QUOTED path token the way it matches an unquoted one, verified with
  `shlex.split` producing a single quoted-content token that a naive `re.escape`-based literal comparison
  does not anticipate; (2) a `HARNESS_HOME` containing any `FORBIDDEN_SYNTAX` byte (`;|&$(`` ` ``)`) hard-
  breaks the allowlist regardless of quoting. BOTH are addressed, not one: (a) `install.py` VALIDATES the
  resolved `HARNESS_HOME` at install time and REFUSES to proceed with a clear, actionable error if it
  contains any `FORBIDDEN_SYNTAX` byte class (these are pathological, rare directory names — refusing is
  correct, not a portability gap); (b) for the common, legitimate space case, `coord_policy.py`'s matcher
  gains a SECOND mode: after `shlex.split(command)` succeeds, compare the parsed argv
  (`argv[0] in {"python3","python"}`, `argv[1] == <the exact baked absolute script path>`, `argv[2]`
  matching `--rout(e|ing)-\S+`/`--context\S*`) as STRINGS, never as a regex over the raw command — quoting
  becomes irrelevant once the comparison happens post-parse. AC-09's guest-proof matrix includes a
  path-with-a-space case specifically to regression-lock this.
- **`PROJECT_ROOT`** — discovered per invocation. The walk-up algorithm has two fixes versus 1.0.0's
  "clone `find_vault`'s ancestor walk" framing:
  - (closes SC-03) `find_vault`'s existing walk (`set_agents_app.py:1022`: `Path(project).resolve().parents`)
    EXCLUDES the starting directory itself (`.parents` never yields the path it was called on) — verified.
    Standing AT the project root (the ordinary case) would therefore not find it. `find_project_root`'s
    candidate list is `[start] + list(start.resolve().parents)` — the starting directory is candidate #1,
    ancestors follow.
  - (closes SC-04) Resolution is **nearest-ancestor-wins, with BOTH markers (`ai/state/features/`, `.git`)
    evaluated AT EACH LEVEL before moving to the next** — never "scan every ancestor for marker 1, then
    rescan every ancestor for marker 2". The wrong reading would let a stray `ai/state/features/` planted
    higher up (e.g. accidentally at `$HOME`) outrank the real repo's own nearer `.git`. The walk stops at
    the filesystem root (`/`) with no match ⇒ `PROJECT_ROOT` unresolved (AC-08). Precedence for overrides,
    most to least specific: an explicit `--project DIR` flag, then `SET_AGENTS_PROJECT` (new test seam,
    mirroring `SET_AGENTS_ROOT`/`SET_AGENTS_STATE`/`SET_AGENTS_ROUTING_TEST_ROOT` at
    `set_agents_app.py:28,33-34`), then the walk-up.
  - **A discovered or overridden `PROJECT_ROOT` is a CONFINEMENT BOUNDARY, never a GRANT OF TRUST.**
    Finding a `.git` or an `ai/state/features/` two levels up says only "read/write operations stay inside
    this directory" — it says nothing about the directory's content being safe to act on unquestioningly.
    This framing feeds directly into the SEC-A02 re-derivation below.
- **SEC-A02 re-derivation carries a TRUST-LEVEL change, not only a path change (closes SC-05).**
  `_resolve_context_pack`/`_validate_context_pack_path` (`set_agents_app.py:185-205`, `:140-155`) re-anchor
  from `ROOT` (the harness, today) to `PROJECT_ROOT`. Traversal-outside-`PROJECT_ROOT` still degrades to "no
  pack" (never a crash, never an unconfined join) — that half of the guarantee is preserved. But post-move,
  `PROJECT_ROOT` and everything under `ai/state/features/*.json` there is the CONTENT OF A THIRD-PARTY REPO
  the harness has never audited (unlike `ROOT`, which is the harness's own trusted tree). The trust
  boundaries section below states explicitly: which exact paths `--context`/`--route-decide` may read under
  `PROJECT_ROOT`, a byte cap on anything read from there and surfaced to an agent, and that this content is
  DATA to be reasoned about, never instructions the orchestrator follows.
- **Routing store root is UNCHANGED and stays out of scope.** ADR-0005 fixed `RoutingStore`'s root at
  `~/.local/state/set-agentes/routing-v2` deliberately immune to environment redirection
  (`routing_core/store.py:23-29`). This feature does NOT touch that root — it adds a `project_key` COLUMN
  inside the existing DB (AC-05), a query-scoping change, never a storage-location change.
- **The allowlisted invocation surface stays literal-path-based, never `set-agents`-based.** The global
  wrapper `./set-agents` (symlinked at `~/.local/bin/set-agents` by `install.sh:277-289`) already exists and
  resolves its own symlink portably — but neither `coord_policy.py` nor `generate.py` ever allowlists the
  literal string `set-agents` (verified: zero matches). This feature does not change that.
- **Scaffold, split across packages (closes B7, ORQ-6).** `bootstrap_project.py` and `sync-project.sh` stay
  two separate scripts — verified: NEITHER creates `ai/state/features/`, and `PROYECTO/` (the template
  project) itself has no `ai/state/` directory. `set-agents --scaffold [DIR]` composes, IN P1: creation of
  `ai/state/features/`, the generic-script copy (`feature-state.py`, `check-owned-paths.py`, matching
  `sync-project.sh:14`'s list) and the persistent project-id file (AC-05/ORQ-2). The vault-link step moves
  to P2 (part of AC-16), since P1 must not depend on vault machinery to be portable on its own.
- **The harness scaffolds itself (closes B5, SC-28).** `feature-state.py`/`check-owned-paths.py` exist ONLY
  under `PROYECTO/ai/scripts/`; `set_agents_app.py` is the mirror-image gap. `ai/scripts/{feature-state.py,
  check-owned-paths.py}` become tracked copies of the templates, with a NEW, THIRD kind of drift check —
  explicitly distinct from `check-drift.sh` (installed-vs-repo drift, a post-commit hook) and from
  `verify.sh`'s `Global/**` diff (SC-01's regenerate-vs-tracked check): this one compares
  `PROYECTO/ai/scripts/{feature-state.py,check-owned-paths.py}` against
  `SET-AGENTES/ai/scripts/{same}` byte-for-byte, added inside `build.sh --check`'s currently-empty branch
  (`build.sh:58-59`, verified as a no-op today). Cross-package obligation (ORQ-6): P2 edits
  `PROYECTO/ai/scripts/feature-state.py` for ORQ-3/AC-13; P2's gates MUST re-run this drift check (i.e.
  re-sync the harness's own copy) before P2 can pass, or P1's check silently starts failing during P2.
- **Degrade stays honest, extended.** No `PROJECT_ROOT` resolvable ⇒ base agents, same shape as 004's
  `ROUTING_UNAVAILABLE` degrade, new trigger, never a fallback to `HARNESS_HOME`-as-project. A directory
  with `ai/state/features/` but NO `.git` (a scaffolded, not-yet-git-initialized project) IS a valid
  `PROJECT_ROOT` (the state-dir marker alone suffices, `.git` is the fallback marker, not a joint
  requirement) — this is explicitly NOT the degrade case; the degrade fires only when NEITHER marker exists
  in any ancestor (or self).

## Vault topology and intent (closes B... vault gaps, DEC-5/6/7, SC-06..SC-16, SC-20, SC-25, SC-26)

- **Two coexisting topologies, disambiguated by a persisted marker (DEC-6, closes SC-08/SC-10).** Hybrid
  (source in repo, symlink from vault — the new default) and `--private` (source in vault, symlink from
  repo — surviving, unchanged in its own mechanics) cannot be told apart by directory shape alone once a
  link is lost, which is exactly the state the real `~/iey/` data was found in. A per-project registry
  entry — written at link time, read before ANY auto-repair action — records: topology chosen, vault path,
  repo path, linked-at timestamp. The auto-repairer (AC-17) refuses to touch any project lacking this
  marker; it reports "unregistered" instead of guessing.
- **`notes_root()` scope (ORQ-3, closes SC-11/SC-12).** Mandatory notes apply ONLY to harness-managed
  projects (marker: `ai/state/` exists) — never to an arbitrary directory or a third-party repo someone
  merely changed into. `tests/test_harness.py:611-621` (the "mutation refreshes notes without calling
  `sync-notes`" half) is preserved verbatim; the opt-in-by-directory half (622-628) is replaced by its
  documented opposite (opt-in-by-`ai/state/`-marker), and the test's total assertion count never shrinks.
- **Migration direction and privacy (DEC-1 as amended by DEC-5, closes SC-09 privacy half).** The four real
  `~/iey/` projects move from vault-resident (legacy `--private`, confirmed by the evidence file: all four
  are REAL DIRECTORIES, not symlinks) into hybrid — but `docs/notas` stays in `.git/info/exclude` after the
  move (reusing `exclude_notes_from_git()`, `set_agents_app.py:1042-1053`) until the user opts each project
  into git individually. The persisted intent marker for these four is written with the exclusion flag set.
- **Backup/rollback (closes SC-09's other half).** No `shutil.move` runs over the only copy of irrecoverable
  data. The migration copies files into the repo destination FIRST, verifies each copy (size/byte compare
  against source), and only removes the vault-side original file AFTER its copy is verified — never a bare
  move-then-hope. A migration interrupted mid-way leaves BOTH copies present (safe over-preservation) rather
  than a half-moved state; a subsequent re-run is idempotent (already-copied-and-verified files are skipped).
- **Expanded migration universe (closes SC-08's remaining states).** Beyond "real directory in vault, repo
  side absent" (the pure-move case): (a) the repo's `docs/notas` is ALREADY a symlink — either DANGLING (a
  lost hybrid link) or an OUTWARD link from the legacy `--private` mode (`vault_link_private`'s own pattern
  at `set_agents_app.py:1057-1069`) — both are DIFFERENT from "absent" and must not be silently overwritten;
  (b) the target repo no longer exists at the recorded path — reported, never guessed at; (c) two repos
  share the same basename at different paths — the registry entry (keyed by the FULL origin path, not the
  basename) disambiguates, never a name-based match.
- **The MERGE case is required, not optional (grounded in the evidence file, closes the part of SC-09/SC-08
  the pure-move framing missed).** `iey-ai`'s repo already holds `docs/notas/` with 2 non-harness files;
  the vault side holds 13 harness-generated notes with ZERO name collisions against those 2 (confirmed:
  `comm -12` on the sorted file lists is empty). The migration for this project is a byte-safe UNION: the
  13 vault files move in as new files, the 2 pre-existing files are untouched, and the byte-compare-and-
  abort rule (`VAULT_LINK_CONFLICT`, reused from `vault_link_private`'s existing pattern) still applies to
  any path that DOES collide (none do today, but the rule must not assume "repo side present" means
  "conflict" — presence without a matching path is not a conflict). This is 13 of the 29 total files: an
  implementation that only handles "repo side absent" is wrong for the project holding almost half the data.
- **Vault status/repair is a NEW, DISTINCT surface, `--doctor --harness pi` is untouched (ORQ-5, closes
  SC-13).** 004's `cmd_doctor` (`set_agents_app.py:359-368`) is pinned to `harness == "pi"` with a schema-2
  envelope and `DOCTOR_HARNESS_UNSUPPORTED` for anything else — this feature adds ZERO branches to that
  function. Vault status/repair gets its own flag (proposed name: `--vault-doctor`, UNVERIFIED against
  final CLI naming conventions — see spec audit). Report-only by default (ORQ-4): repair requires an
  explicit flag AND the per-project dry-run-confirmed marker; never repairs in a generic or headless pass;
  never touches an unregistered project (see the intent-marker point above).
- **Read-side (`--context`) is load-bearing and gets a full sub-spec (closes SC-18).** Since AC-19 makes
  reading it an unconditional orchestrator MUST, its degrade paths are not optional detail: `<COMPANY>` is
  resolved as the immediate child directory of the vault root under which the project's `Proyectos/<name>`
  symlink target lives (i.e. the company directory that CONTAINS the linked project, per `cmd_vault_init`'s
  own layout at `set_agents_app.py:991-1015`); no vault found ⇒ `--context` reports a stable
  `VAULT_NOT_FOUND`-shaped result and the orchestrator proceeds without vault context (never a crash, never
  a block); no company directory resolvable ⇒ hub-only output; no `00 - Proyecto.md` ⇒ that section is
  reported absent, not fabricated. Output is capped (a documented byte ceiling per section) and never reads
  outside the resolved vault/project pair — in particular, `--context` NEVER reads credential surfaces such
  as `~/.pi/agent/auth.json` or any harness/CLI auth store (closes SC-29c). `--json`'s key schema is fixed:
  `{hub, company, project, pending}`, each either a string (file contents, capped) or `null` (absent,
  reported, not omitted).
- **All config writers use read-merge-write (closes SC-26).** `set_auto_update` (`set_agents_app.py:
  461-469`) already reads `app_config()`, merges, and writes back — the pattern AC-12/AC-15 reuse for the
  `vault` key. But `menu()`'s `first_run()` branch does `APP_CONFIG.write_text("auto_update = true\n")`
  (`:1239`) — a RAW FULL OVERWRITE that would silently clobber a `vault` key persisted by a prior run. This
  feature fixes `first_run()` to use the same read-merge-write helper as every other config writer, closing
  the one remaining raw-write path.
- **Failure visibility covers BOTH swallow points (closes SC-25).** `render_notes()`
  (`PROYECTO/ai/scripts/feature-state.py:1047-1099`) has an INNER `except Exception: continue` per feature
  (`:1091`, previously unnamed) in addition to the OUTER `except Exception: pass` (`:1098-1099`, already
  named in 1.0.0). Both are logged (destination, size cap, and rotation are specified in AC-20) without
  changing the "never raises" invariant; a `--doctor`/`--vault-doctor` run against project X must never
  surface a render failure that happened in project Y — failures are recorded per-project, not globally.
- **Attempts-once / never-blocks precedence (closes SC-19).** The vault install attempt inside
  `set-agents --scaffold` happens ONCE per invocation that needs it. A no-TTY/no-manager outcome makes
  `cmd_tools_install` itself return `TOOL_MANUAL`/exit 1 for THAT call, but this NEVER propagates as a
  failure of `--scaffold` as a whole — scaffolding succeeds regardless of whether Obsidian ends up installed.
  A persisted decline (or impossible-to-install outcome) is reported as a steady WARNING on subsequent runs,
  never re-prompted in a loop, and is explicitly NOT the forbidden opt-out from the non-goals — the file
  vault keeps working either way.

## Non-goals

- No change to 004's routing brain: catalog semantics, tier resolution, AM-1/AM-2 mechanics, or reason codes
  are untouched.
- No automatic migration, import, or repair of ANY OTHER routing database (a different user's, a different
  machine's, or a pre-schema-4 DB on this machine). 004's operator-wipe doctrine for schema-2/3 DBs stays
  fail-closed with no repair; the `project_key` migration (AC-05) is additive to THIS user's existing
  schema-4 DB on THIS machine only.
- No community Obsidian plugins. Only core plugins ship, managed as data in `.obsidian/*.json`.
- No mouse or scroll support in the TUI. Arrow keys, `/` to search (with an explicit free-text fallback
  where 1.0.0 already supports one, see AC-24), Enter/Esc/Ctrl-C is the full input surface.
- No new runtime/harness lane. Portability applies to the lanes 004 already routes.
- No remote or cloud vault sync. The vault stays a local directory plus a local symlink.
- No opt-out flag that makes the vault optional again. The headless degrade is a fallback, never a toggle.
- No change to any existing SQLite column beyond the additive `project_key`; `metric_rollups` stays global,
  documented as intentional.
- No Windows-native (non-WSL) interactive raw-mode guarantee beyond `msvcrt` best-effort; the manual
  checkpoint (DEC-7c) is the only claim made about a real Windows GUI install.
- No third-party TUI library — DEC-4 is a hard constraint.
- **Removing `--private` mode (closes SC-29a).** DEC-6 keeps it as a fully supported, explicit alternative
  to the hybrid default; this feature only adds the intent marker that lets automation tell the two apart.
- **Touching `--doctor --harness pi`'s envelope, schema, or exit-code semantics (closes SC-29b, ORQ-5).**
  That surface is 004's, pinned to schema-2, and this feature adds a completely separate flag for vault
  status instead of extending it.
- **`--context` reading anything outside the resolved vault/project pair, and in particular any credential
  surface** (`~/.pi/agent/auth.json`, harness/CLI auth stores, `.env` files) (closes SC-29c).

## Packages

- **P1-portable-core** — two-roots doctrine, install-time-only path baking, allowlist-matcher fix, project
  scoping with a persistent project id, `project_key` schema migration, P1-scoped scaffold, harness
  self-scaffold, the guest portability proof.
- **P2-vault-mandatory** — the intent-marker registry, multi-OS Obsidian install (three verification
  tiers), mandatory notes scoped to harness-managed projects, managed `.obsidian/`, vault config
  persistence (all writers read-merge-write), real-data migration (merge-aware, privacy-preserving,
  backup/rollback), a new distinct vault status/repair surface, the read-side (`--context` + orchestrator
  doctrine), failure visibility, headless degrade.
- **P3-tui** — stdlib arrow-key selector replacing every numbered menu, raw-byte key decoding, abnormal-exit
  terminal restoration, cmd_* machine surface preserved.

## Acceptance criteria

### P1-portable-core

- **AC-00 (ADR-0008 first).** Before any P1 code: `docs/adr/0008-two-roots-portability.md` records the
  `HARNESS_HOME`/`PROJECT_ROOT` doctrine, that path-baking is INSTALL-TIME ONLY (never generate/build-time),
  the allowlist-matcher dual fix (install-time HARNESS_HOME validation + post-shlex-split argv comparison),
  the walk-up fix (self-inclusive, both-markers-per-level), the SEC-A02 trust-boundary reframing, the
  persistent project-id mechanism (ORQ-2), and the SCHEMA 4→5 migration mechanics (backup, transaction
  atomicity, non-terminal-row handling, backfill semantics, backward-incompatibility documentation).
- **AC-01 (path baking is install-time-only).** `Global/**` (git-tracked) contains the literal placeholder
  `__SET_AGENTS_ROOT__` — in JSON, in the installed `coord_policy.py`'s source location, and in the compiled
  `orchestrator.md`/`.toml` — and ZERO absolute filesystem paths; `verify.sh` asserts this after every
  build. The substitution into a real, machine-specific `HARNESS_HOME` happens exclusively inside
  `install.py`'s write path, extended from JSON-only (`merged_json`) to a generic byte-substitution applied
  to the installed `hooks/coord_policy.py` and the installed `agents/orchestrator.{md,toml}` files too.
- **AC-02 (allowlist matcher survives spaces and rejects hostile paths).** `install.py` validates the
  resolved `HARNESS_HOME` and REFUSES installation with a clear error if it contains any `FORBIDDEN_SYNTAX`
  byte class (`;|&$(`` ` ``)`) recognized by `coord_policy.py:37`. Independently, `coord_policy.py`'s
  matcher gains a post-`shlex.split` argv-comparison mode so a `HARNESS_HOME` containing a SPACE (the
  ordinary macOS/Windows case) still matches — quoting in the raw command string no longer defeats the
  allowlist. Both fixes ship together; neither alone closes the finding.
- **AC-03 (project-root walk-up, corrected).** `find_project_root(start)`'s candidate list is `[start]` THEN
  `start`'s ancestors (self-inclusive, closing the `find_vault`-inherited bug where `.parents` excludes the
  starting directory); at EACH level, BOTH markers (`ai/state/features/`, `.git`) are checked before moving
  to the next level (nearest-ancestor-wins across both markers, never marker-by-marker across all levels);
  the walk stops at the filesystem root with no silent fallback. Override precedence: `--project` >
  `SET_AGENTS_PROJECT` > walk-up (explicit always wins over discovered).
- **AC-04 (SEC-A02 re-derivation with trust-boundary content).** `_resolve_context_pack`/
  `_validate_context_pack_path` anchor to `PROJECT_ROOT`. The security-auditor's re-derivation covers BOTH
  halves: traversal-outside-`PROJECT_ROOT` still degrades to "no pack" (preserved), AND the new trust-level
  framing is documented — `PROJECT_ROOT`'s content is third-party, unaudited data; the exact paths
  `--route-decide`/`--context` may read under it, a byte cap on anything surfaced to an agent from there, and
  an explicit statement that this content is never treated as instructions.
- **AC-05 (project-scoped routing DB with a real project identity).** A persisted per-project id (a small
  file under `ai/state/`, written once by the P1 scaffold step, ORQ-2) is the primary `project_key` source;
  the resolved-`PROJECT_ROOT` path hash is a FALLBACK used only when no id file exists. Normalization:
  `realpath`, case-normalized on case-insensitive filesystems. `dispatches` gains the `project_key` column;
  `SCHEMA` bumps 4→5 with matching DDL/CHECKs. Migration mechanics: a full backup of the live DB file before
  any ALTER; the migration runs inside a single transaction (mirroring `_create_schema`'s own
  `BEGIN EXCLUSIVE`/`COMMIT` pattern) so no writer can be mid-write during it; every pre-existing row —
  including any in a non-terminal state at migration time — is backfilled with the project_key belonging to
  THE HARNESS ITSELF (`SET-AGENTES`'s own persisted id), since every row in this DB predates project scoping
  and was, by definition of the bug this feature fixes, generated by invocations running inside the harness
  repo. `dispatches_review`'s index is re-derived to include `project_key`; a mismatch DENIES independence,
  never grants it (fail-closed, ORQ-2); a project with no prior runs simply has nothing to match against
  (same denial shape). Backward incompatibility is documented in ADR-0008: a pre-005 checkout reading a
  schema-5 DB fails closed via `store.py:150`'s existing `schema_version != SCHEMA` check
  (`ROUTING_UNAVAILABLE`) — consistent with, not a new instance of, the existing fail-closed doctrine.
- **AC-06 (P1-scoped scaffold).** `set-agents --scaffold [DIR]` (P1 portion) creates `ai/state/features/`,
  copies the generic scripts (`feature-state.py`, `check-owned-paths.py`, matching `sync-project.sh:14`'s
  list), and writes the persistent project-id file (AC-05). Idempotent, create-if-missing. The vault-link
  step is NOT part of this AC (moved to P2, AC-16/AC-12, per ORQ-6) — P1 is portable without any vault
  dependency.
- **AC-07 (harness self-scaffold, scoped drift check).** `SET-AGENTES/ai/scripts/{feature-state.py,
  check-owned-paths.py}` are tracked copies of `PROYECTO/ai/scripts/{same}`; `build.sh --check`'s
  currently-empty branch (`:58-59`) gains a drift check comparing them byte-for-byte. This is explicitly a
  THIRD, DISTINCT kind of drift from `check-drift.sh` (installed-vs-repo, a post-commit hook) and from
  `verify.sh`'s `Global/**` diff (AC-01's regenerate-vs-tracked check) — never conflated with either. P2
  MUST re-run this check after touching the `feature-state.py` template for ORQ-3 (AC-13), before P2's own
  gates, or P1's check starts failing silently mid-P2.
- **AC-08 (degrade honest, extended, with the non-git case clarified).** No `ai/state/features/` AND no
  `.git` in `[start] + ancestors` ⇒ stable non-executable/unavailable outcome, base static agent, never a
  crash, never a fallback treating `HARNESS_HOME` as the project. A scaffolded-but-not-yet-`git init`-ed
  directory (has `ai/state/features/`, no `.git`) IS a valid `PROJECT_ROOT` — the state-dir marker alone
  suffices; this is explicitly NOT a degrade case, so AC-09's "project that is not a git repo" scenario has
  a stated, non-degraded outcome.
- **AC-09 (the guest proof — hermetic scripted test, not a prose end-to-end description).** A test executed
  by a role OTHER than the implementer at gate time (`gate-runner`/`package-reviewer`, never
  self-attested by the implementer — separation of duties) drives, inside temp directories end-to-end
  (clone target, fake `$HOME`, and the scaffolded project ALL under one isolated tree, sharing nothing with
  the developer's real `~/SET-AGENTES` or real routing DB), a real `--route-decide` invocation and asserts
  named observables: exit code, the parsed JSON envelope, and the CONCRETE `project_key` value matching the
  guest project's persisted id. The environment matrix covered: (1) the harness cloned under a directory
  name OTHER than `SET-AGENTES`; (2) a fake `$HOME` whose PATH does NOT include `~/.local/bin` — the test
  invokes the ABSOLUTE `set_agents_app.py` path directly (per the two-roots doctrine), never the `set-agents`
  wrapper, so PATH is irrelevant by design; (3) `HARNESS_HOME` containing a space (regression-locks AC-02);
  (4) a scaffolded project with NO `.git` (regression-locks AC-08's clarification — routing must still work,
  not degrade); (5) `verify.sh` running green from the guest clone (regression-locks AC-01). Anything beyond
  this matrix (a real interactive terminal session, a real OS-level fresh install) is a declared, separate
  MANUAL CHECKPOINT, never disguised as this AC.

### P2-vault-mandatory

- **AC-10 (ADR-0009 first).** Before any P2 code: `docs/adr/0009-mandatory-vault.md` records DEC-5
  (migration privacy, `exclude_notes_from_git()` reuse), DEC-6 (the intent-marker mechanism and `--private`
  survival), DEC-7 (the three OS-verification tiers), the backup/rollback doctrine (copy-verify-then-delete,
  never bare `shutil.move` over irrecoverable data), and the merge-case algorithm grounded in
  `evidence/vault-migration-inventory.md`.
- **AC-11 (multi-OS install, three-tier verification per DEC-7).** `tools.toml`'s `[cli.obsidian]` gains
  `apt`/`dnf`/`zypper`/`winget`/`choco`; `platform_pm()` extended accordingly. Machine-verified: table-driven
  tests with `shutil.which` mocked across all seven managers plus "none", `--dry-run` plan assertions
  per manager, and the `windows-latest` CI job runs the full `unittest` suite (no longer parse-only).
  Source-verified: exact package identifiers cited against Obsidian's own docs in the ADR. Manual checkpoint,
  declared as such: a real GUI install on macOS and Windows — never conflated with the machine-verified tier.
  The sudo consent contract (`:674-688`) is verified UNCHANGED byte-for-byte.
- **AC-12 (persisted vault-link intent marker).** Every `--vault-link` (hybrid or `--private`) writes a
  registry entry (topology, vault path, full origin repo path, linked-at) that the vault status surface
  (AC-17) reads before acting. No entry ⇒ "unregistered", reported, never auto-repaired. Two repos with the
  same basename at different paths are disambiguated by the full origin path, never the basename alone.
- **AC-13 (notes mandatory, scoped to harness-managed projects).** `notes_root()` creates `docs/notas/` when
  `ai/state/` exists (harness-managed marker) — never for an arbitrary or third-party directory. The half of
  `tests/test_harness.py:611-621` asserting "a mutation refreshes notes without calling `sync-notes`" is
  PRESERVED VERBATIM; the opt-in-by-directory half (622-628) is replaced by its documented opposite
  (opt-in-by-`ai/state/`), named against this clause in the package's evidence, with the test's total
  assertion count never shrinking.
- **AC-14 (managed `.obsidian/`).** Unchanged in substance from 1.0.0: `app.json`, `appearance.json`,
  `core-plugins.json` seeded with a fixed core-plugin set (graph, backlinks, outline, search, tags), no
  community plugin manager.
- **AC-15 (vault config persistence, ALL writers).** `app_config()["vault"]` is persisted by `--vault-init`/
  `--vault-link` via read-merge-write (the `set_auto_update` pattern, `:461-469`). Additionally, `menu()`'s
  `first_run()` (`:1239`, today a raw `APP_CONFIG.write_text("auto_update = true\n")`) is fixed to use the
  SAME read-merge-write helper — closing the one remaining raw-overwrite path that would otherwise clobber
  a previously persisted `vault` key.
- **AC-16 (real-data migration — merge-aware, privacy-preserving, with backup/rollback).** The reverse-
  direction move (vault-resident → hybrid) is new logic (no existing function moves this direction). It
  handles the FULL universe: pure move (repo side absent), MERGE (repo side present with non-colliding
  files — required by the `iey-ai` case, 13/29 files), byte-identical dedup (skip), byte-differing conflict
  (`VAULT_LINK_CONFLICT`, abort, zero files moved), an already-symlinked repo side (dangling or legacy
  `--private` outward link — reported, never silently overwritten), a vanished target repo (reported), and
  same-basename-different-path repos (disambiguated by the registry's full path, AC-12). Backup/rollback:
  each file is copied to its destination and byte-verified BEFORE the vault-side original is removed — an
  interrupted migration leaves both copies present, never a half-moved state; re-runs are idempotent.
  Privacy (DEC-5): `.git/info/exclude`'s `docs/notas` line is written/kept via `exclude_notes_from_git()`
  for the four real `~/iey/` projects, and the registry entry (AC-12) records the exclusion. Requires
  `--dry-run` first and an explicit, separate confirmation before touching real data.
- **AC-17 (vault status/repair — a NEW, DISTINCT surface).** A new flag (proposed `--vault-doctor`,
  UNVERIFIED naming) — NEVER an extension of `--doctor --harness pi`, which stays byte-unchanged (ORQ-5).
  Report-only by default: lists each registered project's topology/health (healthy symlink, real-dir drift,
  dangling symlink, unregistered). Repair requires BOTH an explicit `--repair` flag AND a per-project
  dry-run-confirmed marker (ORQ-4); never repairs in a generic/headless run; never touches an unregistered
  project; a dangling symlink is reported, never auto-deleted.
- **AC-18 (`--context`, fully specified).** `set-agents --context [--project DIR] [--json]` is read-only.
  `<COMPANY>` resolves as the immediate child of the vault root containing the project's `Proyectos/<name>`
  link target. Degrade paths: no vault ⇒ stable `VAULT_NOT_FOUND`-shaped result, orchestrator proceeds
  without vault context; no company dir ⇒ hub-only; no `00 - Proyecto.md` ⇒ reported absent, not fabricated.
  Output is byte-capped per section. `--json` schema: `{hub, company, project, pending}`, each a capped
  string or `null`. NEVER reads outside the resolved vault/project pair; NEVER reads credential surfaces
  (`~/.pi/agent/auth.json` or any harness/CLI auth store).
- **AC-19 (orchestrator doctrine, unconditional, with the read-only allowlist).** The living-documentation
  obligation drops its "when the directory exists" condition — unconditional MUST to run `--context` at
  turn/feature open, `sync-notes` at phase close. `--context*` is allowlisted as READ-ONLY in
  `coord_policy.py`/`generate.py` (ORQ-1) — a third sanctioned channel, distinct from the mutating-capable
  state and routing CLIs, justified precisely because `--context` never writes anything.
- **AC-20 (failure visibility, both swallow points).** `render_notes()`'s OUTER `except Exception: pass`
  (`:1098-1099`) AND its INNER per-feature `except Exception: continue` (`:1091`) are both logged (a
  documented log destination, size cap, rotation) without changing the never-raises invariant. Cross-project
  isolation: a `--vault-doctor` (or state-mutation) run against project X never surfaces a render failure
  that occurred in project Y.
- **AC-21 (headless degrade, precedence stated).** No Obsidian binary / no recognized package manager (or a
  declined install) ⇒ the file vault keeps working; `--vault-doctor` reports a WARNING, never a blocking
  exit solely for the missing GUI. The install attempt inside `--scaffold` happens once; a `TOOL_MANUAL`/
  exit-1 outcome from `cmd_tools_install` for THAT call never propagates as a `--scaffold` failure; a
  persisted decline is a steady, non-repeating WARNING state on subsequent runs, and is explicitly NOT the
  forbidden opt-out — the file vault still functions regardless.

### P3-tui

- **AC-22 (pure core).** `ai/scripts/tui.py` exposes a pure `(state, key) -> state` core, unit-testable
  without a pty — closing the ZERO existing coverage on the five menu functions.
- **AC-23 (raw-byte key decoder, tested separately from the pure core).** A decoder from raw terminal bytes
  to logical key events is unit-tested against: arrow-key ANSI sequences (`\x1b[A` and the `\x1bO` variant
  some terminals emit), UTF-8 multibyte input (for the `/` search box), and bracketed-paste sequences (must
  not be interpreted as navigation keys). This is separated from AC-22 because byte decoding, not state
  transition, is the classic source of TUI bugs.
- **AC-24 (full menu replacement, free-text fallback preserved).** `menu()`, `tools_menu()`, `mcp_menu()`,
  `plugins_menu()`, `vault_menu()`, and `setup_models.py`'s `choose()`/`wizard()` are replaced. `choose()`
  (`setup_models.py:136-146`) today supports FREE-TEXT input for a model id outside the listed options — the
  new selector preserves this as an explicit `/`-triggered free-text entry mode for the same picker; it is
  not silently dropped.
- **AC-25 (tty contracts, regression-locked).** Zero ANSI without a TTY
  (`test_banner_degrades_without_tty`); non-TTY stdin never enters the menu (`main()`'s pre-menu check keeps
  its exact exit-2-with-help shape).
- **AC-26 (terminal handoff for EVERY in-process prompt, not only `run_tty` subprocesses).** `run_tty()`
  exits raw mode/alternate screen before launching `install.sh`/`setup-models.sh`/`build.sh --install`
  (unchanged from 1.0.0) — but this AC is widened: `cmd_tools_install`'s in-process sudo confirmation
  (`input()` at `:674-688`, reachable from `tools_menu`), `mcp_menu`'s free-text `input()` prompts, and any
  other in-process confirmation reachable from the new selector ALSO exit raw mode/alternate screen for
  their duration — `input()` under raw mode does not echo, and unreadable consent is not consent.
- **AC-27 (abnormal-exit terminal restoration).** Terminal state restoration is wrapped in a `finally` block
  PLUS `SIGTERM`/`SIGHUP` handlers, not only `EOFError`/`KeyboardInterrupt`. A test forces an exception
  inside the render loop and asserts the terminal is restored to normal mode regardless.
- **AC-28 (`cmd_*` surface preserved).** `cmd_plugins`/`cmd_mcp`/`cmd_tools`/`cmd_status` keep emitting
  today's exact machine format for scripted/`--json` callers, refactored to separate data from print.
- **AC-29 (menu debt).** `[9] Vault` reordered before Salir; `mcp_menu`'s free-text inputs validated;
  `plugins_menu` shows human-readable text, never raw machine output; invalid input never silently ignored;
  `EOFError`/`KeyboardInterrupt` exit cleanly, no traceback.
- **AC-30 (docs updated).** `README.md`/`INSTALACION.md`'s numbered grids replaced with the new selector's
  description, including the previously-missing `[9] Vault`.

### Global

- **AC-31 (evidence + docs).** Focused suites per package; `verify.sh` green (net assertion count never
  shrinks, and now also asserts zero absolute paths / presence of the placeholder in `Global/**` per AC-01);
  GateSpecs cover `--scaffold`, `--context`, `--project`, `--vault-doctor`; `docs/architecture/` documents
  the two-roots model and the vault topology (including the backward-incompatibility consequence of SCHEMA
  4→5 on pre-005 checkouts); `proposal.md` (new deliverable) stays aligned with this contract.

## Trust and safety boundaries

- SEC-A02 (context-pack confinement) is RE-DERIVED with an explicit trust-level statement: `PROJECT_ROOT`
  content is third-party, unaudited data — read paths, a byte cap, and "never instructions" are documented,
  not merely "still confined" (AC-04).
- ADR-0005 (routing DB root fixed, immune to environment) is UNCHANGED: `project_key` is a query-scoping
  column inside the existing fixed-root DB.
- The sudo consent contract (`:674-688`) is UNCHANGED, verified byte-identical (AC-11).
- Secrets discipline: nothing this feature adds may log token/credential contents; `--context` explicitly
  never reads credential surfaces (AC-18); `--vault-doctor`/`--context` output stays redacted.
- Reviewer independence (`dispatches_review`) filters by `project_key`, fail-CLOSED on any mismatch (AC-05,
  ORQ-2); `metric_rollups` staying global is a documented exception for telemetry quality only.
- The coord allowlist gains a THIRD sanctioned channel (`--context*`, read-only, ORQ-1) alongside the state
  CLI and the routing CLI (both mutating-capable) — the read/write distinction between the three is
  documented explicitly, never blurred.
- `--doctor --harness pi`'s envelope, schema, and exit-code semantics are UNTOUCHED (ORQ-5); vault
  status/repair lives on its own surface.
- Regression tests are never weakened to pass: AC-13's test-sign flip preserves half (a) verbatim, replaces
  half (b) with a documented opposite, and the assertion count never shrinks.
- The migration (AC-16) never runs a destructive `shutil.move` over the only copy of data without a
  verified copy existing first.

## Human decision triggers

Global rules, plus: any request to weaken the sudo consent contract; any request to add a third-party TUI
dependency; a SQLite migration (AC-05) that would need to touch an in-flight/concurrently-open DB; any
conflict discovered during the real `~/iey/` notes migration (AC-16) that the dry-run does not resolve
cleanly; a security-auditor finding that SEC-A02 cannot be preserved under the `PROJECT_ROOT` anchor and its
trust-level reframing as specified; discovery, at implementation time, of a fifth real vault topology state
not covered by AC-16's universe.

## Spec audit

Checked (extended from 1.0.0 per the challenger's findings; the audit's own structure — universe-naming,
pairwise pass, UNVERIFIED tagging — is preserved, per the challenger's own endorsement):

- **Absence/detection requirements, universe named:**
  - AC-08 ("no project detectable"): universe = `[start] + ancestors` of the invoking `cwd` (self-inclusive,
    fixed from 1.0.0's `find_vault`-inherited exclusion, SC-03); absence = neither marker in any level.
    Outcome: stable unavailable outcome, base agent. A state-dir-only project (no `.git` yet) is explicitly
    NOT absence.
  - AC-17 (vault status drift): universe = every entry in the AC-12 registry (NOT every `<vault>/Proyectos/*`
    directory, and NOT every repo on disk — only what has a positive registry entry). States: healthy
    symlink (no-op); real directory (repaired via AC-16, hybrid only — `--private`'s real-directory shape is
    its DESIGNED state, disambiguated by the registry's topology field, never "repaired"); dangling symlink
    (reported); unregistered (reported, never touched).
  - AC-20 (render_notes failure visibility): universe = every mutating `feature-state.py` invocation, BOTH
    swallow points (outer AND inner, SC-25). Absence of an expected note ⇒ surfaced at the next status
    check, scoped per-project (a doctor run in project X never sees project Y's failures).
  - AC-16 (migration conflict/merge detection): universe = every file under each of the four known real
    `<vault>/Proyectos/<name>/` directories PLUS whatever already exists under the corresponding repo's
    `docs/notas/` (confirmed non-empty for `iey-ai` specifically — the data source, the evidence file's
    direct `find`/`comm` reproduction, carries exactly the signal needed: presence, absence, and byte-level
    identity/difference for every file on both sides).
- **Pairwise conflict pass:**
  - AC-06 (P1 scaffold: state dir + scripts + project id) vs AC-16 (P2 vault link): explicitly split by
    ORQ-6 so P1 has no vault dependency; the unified user-facing `--scaffold` command still composes both in
    sequence, order documented (P1 pieces before the P2 vault-link call) so a partial failure in the vault
    step never leaves `ai/state/features/` half-created.
  - AC-07 (P1 harness self-scaffold drift check) vs AC-13 (P2 edits the same template file for ORQ-3):
    explicit cross-package obligation — P2 re-runs P1's drift check before its own gates (ORQ-6).
  - AC-11 (attempt Obsidian install, one confirmation) vs AC-21 (headless degrade): precedence stated —
    attempt once, a decline/impossibility is a steady non-repeating WARNING, never retried in a loop, never
    propagated as a `--scaffold` failure.
  - AC-16 (explicit migration command) vs AC-17 (status surface's read side): both read the SAME registry
    (AC-12) and converge to the same end-state; AC-17 never independently repairs what AC-16 already
    migrated (idempotent, same no-op check).
  - AC-03 (`--project`/`SET_AGENTS_PROJECT`/walk-up precedence) — explicit: `--project` > env > walk-up.
  - AC-05 (project-scoped reviewer independence) vs `metric_rollups` (global): identity/independence checks
    read ONLY `dispatches`/`dispatches_review`, never `metric_rollups`.
  - AC-12 (intent marker, hybrid vs `--private`) vs AC-17 (auto-repair): the marker's topology field is the
    single source of truth for "is a real directory here a bug or the design" — AC-17 never infers topology
    from directory shape alone, only from the marker.
  - ORQ-1's read-only `--context*` allowlist vs the routing CLI's mutating-capable allowlist: documented as
    two DIFFERENT trust levels in the same coord policy file, never merged into one exception.
- **UNVERIFIED (HOW-level, tagged for architecture/package-planner):**
  - Exact new CLI flag/env names (`--project`, `--scaffold`, `--context`, `--vault-doctor`, `--repair`,
    `SET_AGENTS_PROJECT`) — proposed by analogy to existing flags, not verified against a naming convention
    document because none exists; architecture confirms or renames.
  - Exact `project_key` id-file format/location under `ai/state/`, and the exact hash algorithm for the
    path-hash fallback — UNVERIFIED.
  - Exact registry (AC-12) file format/location (proposed: alongside the project-id file under `ai/state/`,
    or vault-side — UNVERIFIED, architecture decides which side is authoritative when the two disagree).
  - Exact `.obsidian/*.json` core-plugin id list and exact `winget`/`choco` package identifiers for Obsidian
    — UNVERIFIED, confirmed against real package names at implementation time (DEC-7's source-verified tier).
  - The `(state, key) -> state` type shape for `tui.py`'s pure core, and the raw-byte key-decoder's exact
    event vocabulary — UNVERIFIED, package-planner defines the concrete structure.
  - Whether `check-owned-paths.py` needs to learn about the harness's OWN scaffolded `ai/state/` (AC-07) —
    UNVERIFIED, flagged to architecture.
  - Exact log destination/rotation policy for AC-20's now-visible render failures — UNVERIFIED, proposed
    under `ai/state/` per project, architecture confirms.

Could not verify beyond the evidence file: whether any filesystem state has changed in `~/iey/` between the
evidence gathering (2026-07-27) and implementation time — the evidence file itself states the implementer
MUST re-verify at execution time. Everything else the 1.0.0 audit could not verify is now closed by
`evidence/vault-migration-inventory.md`.
