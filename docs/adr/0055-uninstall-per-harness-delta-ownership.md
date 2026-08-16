# ADR-0055: Uninstall per harness — delta ownership, never content ownership

Status: Accepted
Date: 2026-08-16
Supersedes: —
Superseded by: —

## Context

D4/AC-09 asked for "install in exactly one CLI"; measured live, that already worked end to end
(`install.py --target`, `build.sh --target`, `install.sh --harness`). What was missing was exposure
(the app's "Actualizar" menu item reinstalled all four trees regardless of what was actually
installed, `set_agents_app.py` `cmd_update`) and D4/AC-10, "uninstall from exactly one CLI without
touching the other three" — which did not exist in the repository at all before this package
(`grep -rn "uninstall" ai/scripts/*.py *.sh` → zero results).

A first implementation attempt was made and reviewed. The review found eight `high` findings, every
one with an executed PoC that destroyed real data in a throwaway `--home`. That implementation was
lost before being committed (the working tree that held it was cleaned before this repair pass could
recover it) and was rebuilt from the context pack and the findings themselves, not restored from a
diff. This ADR corrects a factual error the lost attempt's own reasoning rested on, and settles the
AC-11 question the original D4 context pack deferred.

## The defect the lost attempt's own reasoning rested on

Three of the four managed harness trees are **whole files** the installer owns outright (every path
in `managed-files.json`): removing them on uninstall is a straightforward file delete, already
map-checked against MANIFEST-based safety fences elsewhere in this codebase (ADR-0008 D2).

The other three files — `~/.claude/settings.json`, `~/.codex/config.toml`,
`~/.config/opencode/opencode.json` — are **merges into a file the user owns**. Before this package,
nothing recorded which *keys* a merge added or overwrote, only that the file existed. The lost
attempt's review findings (F03, F04) showed the consequence measured live:

- **F03** — an uninstall driven by "what does the overlay/merge contain" (content) instead of "what
  did THIS installer add or change" (delta) deletes user keys that happen to sit next to ours in the
  same file/list (`enabledPlugins`, `disabledMcpjsonServers`, `[features]`, `[agents]`) — sibling keys
  the user set by hand, never written by this installer, disappear anyway.
- **F04** — even a delta recording *what value we wrote* is not enough. The reviewed attempt kept
  `model`/`model_reasoning_effort` untouched on uninstall reasoning that they are "the two keys a user
  could plausibly set by hand" (the very comment `flag_codex_model_change` carries, 024/C3) — and
  deleted the three keys it judged "purely ours" instead. The result on an uninstall of a *freshly
  created* `~/.codex/config.toml` (nothing of the user's existed before this installer's first run)
  was a `model = "gpt-5.6-terra"` line left permanently pinned on a CLI the user had just uninstalled
  the harness from.

The false premise in both directions was the same: **"I know what value I wrote" was being treated as
identical to "I permanently own this key."** They are not the same claim. A key's ownership is not
fixed at write time — it is *re-verified at uninstall time* by comparing the live value against the
value this installer last recorded writing:

- if the live value still equals what we wrote, nothing has touched it since our install — safe to
  remove (delete the key if it did not exist before us; restore the prior value if it did).
- if the live value differs, the user (or some other process) changed it since — no longer ours to
  touch, uninstall must leave it exactly as found.

This is the same discipline `apply_provider_registry`/`JSON_MANIFEST` already used for opencode's
`provider.*` ids (022 PKG-4); D4 extends it to `settings.json` and `config.toml`, recording a
**delta manifest** (`managed-special-keys.json`) of `{path, value, previous, existed, union_list}`
per special file, populated at install time (`base` and the post-merge `final` value are both already
in hand at every merge call site — nothing new needed to be read to compute this) and consulted, never
assumed, at uninstall time.

## Decision

1. Uninstall targets are named explicitly, always (`--target`, one or more) — there is no "uninstall
   everything" default, mirroring but not reusing install's own "no `--target` means all four" default
   (that install-side default is unrelated existing behavior, unchanged by this package).
2. A file this installer owns whole (in `managed-files.json`) is deleted outright, scoped strictly to
   the selected target's root, with the containment check done against the **resolved** path
   (`Path.resolve()` + `is_relative_to`), never the lexical one `Path.parents` gives — a `..`-bearing
   manifest entry must not be able to escape `--home`.
3. A special (merged) file is **de-merged**, never deleted: every recorded key whose live value still
   equals what this installer last wrote is removed (if it did not exist before) or restored to its
   prior value (if it did); every other key — the user's own, or one the user has since changed — is
   left untouched, unconditionally.
4. A corrupt registry (MANIFEST, in particular) aborts the uninstall outright (`exit 2`); it is never
   treated as "nothing was ever installed" and it is never overwritten with an empty registry as a
   side effect of a run that could not read it.
5. Files and registries (MANIFEST, `managed-json-paths.json`, `managed-special-keys.json`,
   `install-targets.json`) are backed up and rolled back together, as one operation, so an uninstall
   that fails partway through leaves the machine exactly as it was, registries included.
6. `install-targets.json` (the installed-scope record) is **derived from ground truth after removal**
   — whatever the surviving MANIFEST entries say is still installed IS the scope, recomputed fresh —
   rather than merged/subtracted from a possibly-absent prior scope file. This both narrows correctly
   on every uninstall and self-heals a machine whose scope file predates this feature entirely
   (nothing to guess: the files on disk are the truth).
7. `cmd_update` (the app's "Actualizar") now reads that same scope record and reinstalls exactly what
   it lists, instead of calling `build.sh --install` with no `--target` at all (which silently
   defaulted to all four and re-widened a deliberately narrow install on every update). A machine that
   predates the scope record (`_install_scope()` returns `None`) keeps the historical default (all
   four) unchanged — never narrowed on a guess, only ever narrowed on positive evidence.

## AC-11 — "use a CLI virgin, just this once" (deferred by the orchestrator)

The D4 context pack asked for this decision to be made and recorded even though its implementation
is deferred to a later package. The two axes that exist and must not be conflated:

- the **installed tree** in `--home` (static, baked at install time — what AC-09/AC-10 manage), versus
- what a **spawned session actually reads at runtime** — the axis AC-11 needs.

A "virgin, just this once" session cannot mean deleting and re-seeding files under `--home`; that is
neither safe (a concurrent session would see the churn) nor reversible cheaply. It has to mean a
session that never *reads* the installed tree in the first place — pointed, for that one spawn, at an
isolated location.

Every one of the four CLIs resolves its config through more than `HOME` alone:

| CLI | Path baked by `install.py` | Env var(s) that actually govern it at runtime |
|---|---|---|
| claude-code | `home / ".claude"` | `HOME` (no documented override found in this repo's own sources) |
| codex | `home / ".codex"` | `HOME` (no documented override found in this repo's own sources) |
| pi | `home / ".pi/agent"` | `HOME` (no documented override found in this repo's own sources) |
| opencode | `home / ".config/opencode"` | `HOME`, **and/or `XDG_CONFIG_HOME`** — `install.py:38-42` hardcodes `home / ".config/opencode"`, unconditionally ignoring `XDG_CONFIG_HOME` even when the user has exported it |

A future AC-11 implementation naming only `HOME` as the axis to override would be incomplete for
opencode on any machine that exports `XDG_CONFIG_HOME` (a common Linux/XDG-base-dir convention): a
spawn given a scratch `HOME` but no matching `XDG_CONFIG_HOME` override would still read the real,
installed `opencode.json` through the exported variable, defeating the "virgin" guarantee silently.
The correct axis set for a future AC-11 is **`HOME` plus, per CLI, whichever of
`XDG_CONFIG_HOME`/`XDG_DATA_HOME`/`XDG_STATE_HOME` that CLI actually consults** — not `HOME` alone.

**Sin verificar**: whether opencode's own runtime actually honors `XDG_CONFIG_HOME` (this repo's
`install.py` never reads it — that half is verified, `install.py:38-42` — but whether the `opencode`
binary itself would resolve its config through it if exported is outside this repository's sources
and was not checked against opencode's own documentation this pass). AC-11's eventual implementer
must confirm this with a source (opencode's own docs/`--help`) before relying on it, per ADR-0026.

## Consequences

- `managed-special-keys.json` is a new, small, private registry (`chmod`-inherited from its parent,
  same as the other three) — one more file uninstall/install must keep consistent with the other
  three, which is exactly why all four are now backed up/rolled back/derived together (Decision 5/6).
- A user who hand-edits a value this installer also manages (e.g. changes `agents.max_depth` in
  `~/.codex/config.toml` by hand) keeps that value forever after — uninstall, and any FUTURE install,
  never claims it back once the live value has diverged from what this installer last wrote. This is
  intentional (F04's fix) and matches ADR-0008 D2's standing doctrine, not a new relaxation.
- AC-11 remains unimplemented; this ADR only fixes the axis it must eventually use.
