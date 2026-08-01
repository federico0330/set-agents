# ADR-0012 — Mandatory vault: topology intent, merge-aware migration, honest multi-OS install

- Estado: Accepted (2026-07-29). Feature `005-portable-harness`, contract 1.1.0, package
  P2-vault-mandatory, work item T-200 / AC-10. This ADR is a BLOCKING predecessor: no P2 code lands
  before it.
- **Citation correction, registered here rather than in `spec.md`:** the approved contract's AC-10 names
  this file `docs/adr/0009-mandatory-vault.md`. When P2 actually opened (2026-07-29), ADR-0009 had already
  been claimed by `0009-finding-verification.md` (feature 006-P2, accepted 2026-07-27 — after 005's spec was
  written, before P2 was implemented). Same class of citation drift this repo has hit before (007-P1's
  `file:line`→`file:symbol` convention change, 009-P3's ADR-index guard). The number used is **0012**, the
  next free slot; `spec.md`'s AC-10 text is not edited (contract-hash integrity, same reasoning as
  `ac-19-rationale-drifted-mid-package-routing-db-recreated`).
- Amends nothing; this is the first ADR for the vault surface. Does not touch ADR-0008's two-roots doctrine
  (P1, unrelated) nor any routing ADR.
- Every file:line citation below was verified against the working tree on 2026-07-29.

## Contexto

The vault (`~/<empresa>/obsidian`, an Obsidian graph) exists today as an *optional*, write-mostly surface:
`vault_link()`/`vault_link_private()` (`ai/scripts/set_agents_app.py:1267-1354`) create a symlink once, and
nothing reads the vault back into the orchestrator's context. The real `~/iey/` data exposed why this is a
problem: on 2026-07-23 the link between the vault and all four real IEY projects was lost, and since then the
vault side (`~/iey/obsidian/Proyectos/<name>/`) and the repo side (`<repo>/docs/notas/`) have been two
independent, unlinked real directories — the vault holding 29 files that exist **nowhere else** (confirmed
absent from every target repo's git history, per `docs/specs/005-portable-harness/evidence/vault-migration-inventory.md`).

Four facts constrain this design, all verified against the working tree before anything was decided:

1. **The vault-resident (legacy `--private`) and hybrid topologies are indistinguishable by directory shape
   alone once a link is lost.** Hybrid is source-in-repo + vault-side symlink (`cmd_vault_link:1318-1353`);
   `--private` is source-in-vault + repo-side symlink (`vault_link_private:1267-1315`, invoked via
   `cmd_vault_link(..., private=True)`). A REAL directory on the vault side (today's state for all four
   `~/iey/` projects) is consistent with either "this project is `--private` and working" or "this project
   was hybrid and its link rotted" — the code cannot tell which without an external record.
2. **No existing function migrates vault-resident → hybrid.** `vault_link_private` migrates the OTHER
   direction (repo-resident → vault, `:1284-1301`, moving repo files into the vault). T-206 is new logic,
   not a parameter flip on existing logic.
3. **The four real projects need two different migration shapes.** Per the inventory: three
   (`SistemaOrganizacionCobros`, `ScrappingML`, `pymepilot`) have no `docs/notas/` in the repo — pure move.
   `iey-ai` has a real `docs/notas/` with 2 non-harness files (`README.md`,
   `analisis-puntos-de-dolor-2026-07-23.md`) and zero name collisions against the vault's 13 files — a
   byte-safe union (MERGE), not a move. An implementation that only handles "repo side absent" silently does
   the wrong thing on `iey-ai` — the project holding 13 of the 29 total files.
4. **`platform_pm()` (`:839-845`) only recognizes two families.** `darwin → brew`, and Linux limited to
   `pacman`/`apt-get`; no `dnf`, `zypper`, or any Windows manager. `tools.toml`'s `[cli.obsidian.install]`
   (`:57-63`) only has `pacman`/`brew` entries. AC-11 asks for a truthful three-tier claim across three OSes,
   not a single new code path.

## Decisión

### DEC-5 — Migration direction and privacy

The four real `~/iey/` projects move from vault-resident (legacy `--private`, all four confirmed REAL
DIRECTORIES, not symlinks) into hybrid. **`docs/notas` stays in `.git/info/exclude`** after the move —
`exclude_notes_from_git()` (`:1253-1264`) is reused unchanged — until the user opts each project into git
individually, repo by repo, on their own schedule. This is not a technical constraint; it is the user's own
decision from the 2026-07-28 session predating this package, carried forward unmodified. The persisted
registry entry (DEC-6) for these four records the exclusion flag as `true`.

### DEC-6 — Persisted intent-marker registry

A new file, `<vault>/.set-agentes-vault.json` (sibling to `00 - INICIO.md`, inside the vault root so it
travels with the vault, e.g. via Syncthing, not with any one repo), holds one entry per linked project:

```json
{"iey-ai": {"topology": "hybrid", "vault_path": "/home/federico/iey/obsidian/Proyectos/iey-ai",
            "repo_path": "/home/federico/iey/iey-ai", "linked_at": "2026-07-29T...", "notes_excluded": true}}
```

Keyed by the project's **full repo path**, never the basename — two repos sharing a basename at different
paths (e.g. a fork checked out twice) are disambiguated by this key, per the spec's explicit requirement.
Written by every `cmd_vault_link` call (both hybrid and `--private`) and by T-206's migration. Read by
`--vault-doctor` (AC-17) before ANY action: **no entry ⇒ "unregistered", reported, never guessed at, never
auto-repaired.** This is what lets `--private` survive (it is still a first-class, registered topology, not
a deprecated one) while making a lost-link project indistinguishable-by-shape problem solvable — the registry
is the external record §Contexto point 1 said the directory shape cannot provide.
**DR-003 amendment (2026-07-29):** the built implementation does not fully match this paragraph. The
per-project `--vault-doctor --project X` pass falls back to the basename convention
(`vault/Proyectos/<name>`) for a project with no registry entry, and treats the FIRST successful `--repair`
as the moment of registration — this is how the four real, never-yet-linked `~/iey/` projects get migrated at
all, so "refuses any unregistered project" is not literally true for the never-registered case. What IS
implemented and tested: a registered repo's conventional path can no longer be silently claimed by a
DIFFERENT, unregistered repo sharing its basename (005-P2's security repair, finding SEC-004). The
never-registered-vs-never-registered case remains open, with the two-step dry-run/fresh-marker confirmation
as its only safeguard, tracked as debt (decision
`vault-doctor-basename-fallback-still-collides-when-both-sides-unregistered`) for a future package that adds
a real anchor/claim step.

### DEC-7 — Three honest verification tiers, never conflated

`tools.toml`'s `[cli.obsidian]` gains `apt`, `dnf`, `zypper`, `winget`, `choco` install commands;
`platform_pm()` is extended to detect all seven package managers (`pacman`, `apt`, `dnf`, `zypper`, `brew`,
`winget`, `choco`) via `shutil.which` on their respective binaries (`apt-get`, `dnf`, `zypper`, `winget`,
`choco`), keyed by `sys.platform` first (`win32` → winget/choco only; `darwin` → brew only; else → the four
Linux managers in order). Each tier is reported as what it actually is, never blended into a single
"it works" claim:

1. **Machine-verified (CI, this package's real obligation):** table-driven tests mock `shutil.which` across
   all seven managers plus "none available", assert `pick_method`'s selection order and `cmd_tools_install
   --dry` output per manager. The `windows-latest` CI job stops being parse-only (per the existing
   `.github/workflows/ci.yml` matrix) and runs the full `unittest` suite — proving the *selection logic*
   works on real Windows Python, not proving Obsidian actually installs there.
2. **Source-verified (this ADR, not CI):** the exact package identifiers (`obsidian` for pacman/apt/dnf/
   zypper, `Obsidian.Obsidian` for winget, `obsidian` for choco) are cited against Obsidian's own published
   install docs, not invented.
   **DR-004 amendment (2026-07-29):** the apt/dnf/zypper identifiers were never actually source-verified —
   checked live against the real Debian/Ubuntu package APIs and obsidian.md's own download page during
   005-P2's security repair, there is no installable `obsidian` apt/dnf/zypper package (only .deb/AppImage/
   Flathub/snap). `tools.toml` now carries pacman/brew/winget/choco only; apt/dnf/zypper fall through to the
   manual `doc` checkpoint, pointed at the real Flatpak/Snap channels instead. `platform_pm()`'s seven-manager
   detection is unchanged (decision `tools-toml-obsidian-apt-dnf-zypper-were-fabricated`).
3. **Manual checkpoint (never claimed as machine-verified):** a real GUI install on macOS and Windows is a
   declared, separate checkpoint a human runs once. The sudo consent contract (`cmd_tools_install:885-899`)
   is verified BYTE-UNCHANGED — this package adds managers to the catalog, it does not touch the confirm-
   before-sudo path.

### Backup/rollback doctrine (closes the real-data risk)

No `shutil.move` ever runs over the sole copy of irrecoverable data. For every file in scope: **copy to the
repo destination first, byte-verify the copy against the source (size + content compare), and only then
remove the vault-side original.** An interrupted migration leaves BOTH copies present — safe over-
preservation, never a half-moved state — and a re-run is idempotent: a file already copied-and-verified is
skipped, not re-copied. This mirrors `vault_link_private`'s own existing conflict discipline
(`:1287-1295`, byte-compare before ever touching a file) applied to the reverse direction and to deletion,
which that function never needed because it never deletes an original.

### Merge-case algorithm (grounded in `evidence/vault-migration-inventory.md`)

For each registered `<vault>/Proyectos/<name>` real directory with no matching registry entry:

1. Resolve `repo_path` from the registry (if migrating an already-registered `--private` project) or from
   the vault directory name matched against a caller-supplied project root (T-206's CLI surface, first run
   over the four real projects).
2. If `repo_path` does not exist on disk: **report, never guess.** (Spec case: "target repo no longer
   exists.")
3. If `repo/docs/notas` is already a symlink: inspect its target.
   - Resolves to the vault path being migrated ⇒ already hybrid, no-op, `VAULT_LINK_SKIP`.
   - Resolves elsewhere (dangling, or an outward `--private` link) ⇒ **report, never silently overwrite.**
4. If `repo/docs/notas` does not exist (pure move — 3 of the 4 real projects): create it, copy every vault
   file into it (copy-verify-then-delete per file, per the backup/rollback doctrine above), symlink the
   vault side to it, write the registry entry.
5. If `repo/docs/notas` exists as a real directory (the `iey-ai` case, MERGE): for every vault file, compute
   its relative path under `docs/notas/`.
   - No file at that relative path in the repo ⇒ copy-verify-then-delete (union member).
   - A file exists and is byte-identical ⇒ skip (already migrated, re-run idempotence).
   - A file exists and differs ⇒ `VAULT_LINK_CONFLICT`, **abort the whole project's migration, zero files
     moved for it** (other projects in the same batch are unaffected). The evidence file confirms this rule
     has nothing to trip on today (zero collisions across all 29 files) — it exists for the general case, not
     because `iey-ai` needs it today.
   - After every vault file is resolved with no abort: symlink the vault side to the repo directory, write
     the registry entry.
6. `--dry-run` runs steps 1-5 in read-only mode (no copy, no delete, no symlink, no registry write) and
   prints the exact plan per project (pure-move / merge-N-files / conflict-on-path / already-linked /
   unregistered-target-missing). A dry-run report that differs from
   `evidence/vault-migration-inventory.md`'s prediction is new information since 2026-07-27 and a
   `HUMAN_DECISION_REQUIRED` trigger per spec, not something the implementation resolves by picking a side.
7. Real execution requires `--dry-run` to have been run first (a per-invocation confirmation, not a
   persisted flag — re-running the tool a week later re-requires a fresh dry-run) AND a separate explicit
   confirmation distinct from the dry-run itself.

## Consecuencias

- `--vault-doctor` (AC-17) becomes possible specifically because the registry now exists: report-only by
  default, `--repair` requires both an explicit flag and a per-project dry-run-confirmed marker, and it
  refuses any unregistered project — the registry is a hard prerequisite for any repair action, never
  inferred from directory shape.
- `--private` survives as a first-class topology (DEC-6), not a deprecated one; the registry is what makes
  that survivable alongside hybrid without ambiguity.
- The vault gains a second piece of durable state beyond the notes themselves (the registry file). It is
  vault-resident, not repo-resident, on purpose — it describes *links between* repos and the vault, so it
  belongs with the vault, the same reasoning `VAULT_HUB`/`00 - INICIO.md` already follows.
- `tools.toml`'s `[cli.obsidian]` block grows five install methods; no existing method (`pacman`, `brew`)
  changes. `platform_pm()`'s Linux branch grows two candidates (`dnf`, `zypper`) tried after `pacman`/`apt`,
  preserving today's order for the two already-supported managers.
- `docs/notas` privacy for the four real `~/iey/` projects is unchanged by this migration — DEC-5 explicitly
  keeps them un-versioned until the user opts in per-project, later, outside this package's scope.
- Three tiers of "multi-OS support" now exist for every future CLI tool this harness adds, not only Obsidian
  — the doctrine (never claim GUI-verified from a CI-verified fact) generalizes.

## Alternativas descartadas

- **Directory-shape heuristic instead of a registry** (e.g. "if `docs/notas` doesn't exist in the repo,
  assume vault-resident"). Rejected: this is precisely the ambiguity that caused the 2026-07-23 data loss in
  the first place — a heuristic that guesses wrong on a genuinely-still-vault-resident `--private` project
  would treat legitimate data as migratable and risk exactly the kind of silent overwrite DEC-6 exists to
  prevent.
- **`shutil.move` for the migration.** Rejected outright by the spec (SC-09) and by this ADR's own backup/
  rollback doctrine: a move that is interrupted mid-way (process killed, disk full, permission error) leaves
  data in neither location reliably. Copy-verify-then-delete is strictly slower and strictly safer; safety
  wins for irrecoverable data.
- **A single "does it install" boolean instead of three tiers.** Rejected: it already produced a false
  claim once (P1's own AC-01 discrepancy, ADR-0008's point 1) where "verified" quietly meant "verified on
  the one OS the author has". DEC-7 makes the claim's scope explicit instead of implicit.
