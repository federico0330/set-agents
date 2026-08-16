# D4-harness-por-CLI — repair evidence

## 0. Where the implementation came from

`worktree-agent-ae751ab5590e8d58a` (the branch named as holding the original attempt) is **identical
to its base commit `78cf61b`** — `git diff 78cf61b worktree-agent-ae751ab5590e8d58a --stat` produced
zero output. No trace of the reviewed implementation survived; `docs/specs/025-consola-minima-y-flexible/evidence/D4-implementer.md`
does not exist. The repair was done as a full reimplementation from the context pack
(`docs/specs/025-consola-minima-y-flexible/context/D4-harness-por-CLI.md`) and the eighteen findings
themselves, which describe the previous attempt's behavior precisely enough to rebuild it correctly
the first time rather than patch a diff that no longer exists.

**Separate environment issue found and resolved before any repair work could start**: this repair
agent's assigned worktree (`.claude/worktrees/agent-adf0f883e289106c7`) was checked out at `76b50a7`,
an ancestor of `main` roughly 130+ commits behind (predating features 021 through 030, including
`build.sh`/`install.sh` at the repo root and the entire D-series context). `git merge --ff-only main`
brought it to `main`'s tip (`688577e`) — a clean fast-forward, zero local commits lost (the branch had
none), working tree was empty before the merge. Recorded here since it is outside the package's own
`owned_paths` but was required to have the files this package's scope names at all.

## 1. Files touched, exact lines

| File | What changed |
|---|---|
| `ai/scripts/install.py` | `--uninstall`/`--staging`-now-optional argparse (24-50); `SPECIAL_KEYS_MANIFEST`/`SCOPE_PATH` constants (86-102); delta helpers `_json_get`/`_leaf_paths`/`_special_delta`/`_revert_json_special`/`_prune_empty_json_dicts` (109-217); `revert_json_special` (248-259); `effective_specials` now records delta via `_PENDING_SPECIAL_KEYS` (372-411); `_codex_written_keys`/`_toml_repr`/`_codex_restore_top_key`/`_codex_restore_key`/`_codex_apply_restore` (531-599); `revert_codex` (611-640); `_read_manifest_raw`/`_resolved_roots`/`_within_any_root`/`previous_targets` rewritten (654-702, F11); `manifest_entries_for_uninstall` (704-750, F05); `new_backup_dir`/`take_backup`/`restore_backup` extracted (757-794, F15); `run_install()` (797-993, behavior-preserving refactor of the previous module-level code + `SPECIAL_KEYS_MANIFEST` persistence at 970-974); `run_uninstall()` (996-1116, F03/F04/F05/F06/F07/F08/F11); dispatch (1119-1122) |
| `install.sh` | `UNINSTALL` var + `--uninstall` flag + usage (9-40); `run_uninstall_flow()` (53-78, F01/F16); dispatch before the onboarding sequence (461-464) |
| `ai/scripts/set_agents_app.py` | `cmd_update` (1249-1272, **only this function touched**, per the repair's declared scope) |
| `docs/adr/0055-uninstall-per-harness-delta-ownership.md` | new |
| `docs/adr/README.md` | indexed 0055 |
| `tests/test_harness.py` | 22 new/adjusted assertions, see §3 |

## 2. The eight `high` findings — PoC before/after

Every PoC below ran against a throwaway `--home` under `/var/tmp/.../scratchpad/d4test/home1`, never
against `~`. Full transcripts are in this repair's tool history; the essential before/after is
reproduced here.

### F01 — `install.sh --dry-run --uninstall` used to ignore `--dry-run`
**Before (design flaw the rebuild avoids)**: `--uninstall` would short-circuit before the `[ "$DRY" -eq 1 ]`
check, exactly like `--preview` was ignored on the install side (F02) — a dry-run flag that means
"don't touch anything" everywhere else in this script would have destroyed data.
**After, run for real** (`HOME` pointed at the fixture, never real `~`):
```
$ HOME=$FIXTURE ./install.sh --dry-run --uninstall --harness claude
Vista previa de lo que --uninstall va a borrar/des-fusionar (harness=claude):
--- .../.claude/settings.json
+++ .../.claude/settings.json (uninstall de-merge)
@@ ...
MANAGED_DIFF_FILES=222
UNINSTALL_DRY_RUN (no se tocó nada; repetí sin --dry-run para aplicar)
$ ls $FIXTURE/.claude/CLAUDE.md   # still there
$ ls $FIXTURE/.pi/agent/AGENTS.md # still there
```
Regression test: `test_install_sh_uninstall_dry_run_never_touches_anything` (`tests/test_harness.py`).

### F02 — `--preview` silently ignored under `--uninstall`
**Fix**: `run_uninstall()` (install.py:1027-1042) checks `args.preview` unconditionally and returns
before any write; `revert_json_special`/`revert_codex` (install.py:248, 611) never write internally —
they only ever *compute* the reverted content, so the exact same code path backs both `--preview` and
the real run, structurally closing the "diverges from what it reports" class of bug.
**PoC, before/after**: ran `install.py --uninstall --target opencode --preview` against the fixture,
hashed the whole tree + all four state jsons before and after — identical
(`test_uninstall_preview_never_writes_and_real_uninstall_matches_it`).

### F03 — the registry recorded content, not delta
**Before**: no registry existed at all for special files (this is genuinely new surface, AC-10).
**Design that avoids reintroducing the bug**: `managed-special-keys.json` (`SPECIAL_KEYS_MANIFEST`,
install.py:98) records `{path, value, previous, existed, union_list}` per key `_special_delta`
(install.py:148) computes from `base` (the live file BEFORE this run's merge) vs `final` (what
actually landed on disk) — the exact delta, never the file's content.
**PoC — live before/after** (hand-edited `~/.claude/settings.json` to add a user's own plugin/server
next to ours, then uninstalled claude-code):
```
before: {"enabledPlugins": {"engram@engram": false, "mi-plugin@mio": true},
         "disabledMcpjsonServers": ["brave-cdp","context7","engram","playwright","mi-servidor-propio"]}
after:  {"enabledPlugins": {"mi-plugin@mio": true}, "disabledMcpjsonServers": ["mi-servidor-propio"]}
```
The user's `mi-plugin@mio` and `mi-servidor-propio` survive untouched; only the keys this installer
wrote are gone. Same result reproduced for `opencode.json` (a user-added `my_custom_setting` top-level
key and a user-added `provider.my-own-model` entry both survived; the seeded `provider.ollama` entry
— ours — was removed). Regression: `test_uninstall_one_target_leaves_the_other_three_byte_identical`
(claude-code case) plus the opencode.json manual run recorded in this repair's tool history.

### F04 — codex: ownership assumed forever instead of re-verified
**Before (the bug this rebuild specifically avoids)**: the reviewed attempt kept `model`/
`model_reasoning_effort` untouched on uninstall (reasoning they "could be the user's"), and unconditionally
deleted `features.multi_agent`/`agents.max_depth`/`agents.max_threads`. Live PoC of the ORIGINAL bug's
consequence (freshly-created `~/.codex/config.toml`, i.e. nothing of the user's before install):
uninstalling left `model = "gpt-5.6-terra"` permanently pinned on a CLI the harness had just been
removed from.
**Fix**: `_codex_written_keys` (install.py:531) records **all five** managed keys uniformly with
`{value, previous, existed}`; `revert_codex` (install.py:611) re-parses the LIVE file via `tomllib` at
uninstall time and only touches a key if the live value still equals what was recorded — ownership is
re-verified, never assumed permanent, for every key including `model`/`model_reasoning_effort`.
**PoC — live before/after** (hand-edited config.toml after install: added `features.web_search = true`,
changed `agents.max_depth` from `1` to `3`):
```
before: model="gpt-5.6-terra", model_reasoning_effort="high", features={multi_agent=true, web_search=true},
        agents={max_threads=4, max_depth=3}
after:  features={web_search=true}, agents={max_depth=3}
UNINSTALL_KEYS_KEPT=.codex/config.toml:agents.max_depth
```
`model`/`model_reasoning_effort`/`multi_agent`/`max_threads` (unchanged since install) are gone;
`web_search` (never ours) and `max_depth=3` (user changed it since install) both survive. Regression:
`test_uninstall_codex_keeps_a_key_the_user_changed_since_install`.

### F05 — fail-open on a corrupt registry
**Before (design avoided)**: a corrupt MANIFEST read as `{}`/`[]` silently, meaning "nothing was ever
installed" — `UNINSTALL_PASS` with zero files removed AND the corrupt file getting overwritten as `[]`,
destroying every OTHER harness's registry entries as a side effect.
**Fix**: `manifest_entries_for_uninstall` (install.py:704) distinguishes "file absent" (legitimate,
empty result) from "file exists but fails to parse" (abort, `exit 2`, never touch the file).
**PoC — live before/after**:
```
$ echo -n '{corrupt' > $FIXTURE/.local/state/set-agentes/managed-files.json
$ python3 install.py --home $FIXTURE --uninstall --target opencode; echo RC=$?
UNINSTALL_ABORTED_UNREADABLE_MANIFEST manifest=.../managed-files.json
  The file exists but is not valid JSON -- refusing to guess what this
  installer owns ...
RC=2
$ cat $FIXTURE/.../managed-files.json   # still "{corrupt" -- never rewritten
```
Regression: `test_uninstall_aborts_closed_on_a_corrupt_manifest`.

### F06 — rollback didn't restore the registries
**Fix**: `run_uninstall()` backs up `remove + specials + [MANIFEST, JSON_MANIFEST, SPECIAL_KEYS_MANIFEST,
SCOPE_PATH]` as ONE list (install.py:1046-1048) via the shared `take_backup`/`restore_backup` (F15),
and `rollback()` restores all of it together on any exception during the mutation section.
**PoC**: uninstalled `pi`, then immediately reinstalled `pi` from the same staging tree —
`INSTALL_PASS`, no `INSTALL_ABORTED_UNSAFE_COLLISION` (which is exactly what a MANIFEST left with
stale/missing `.pi/` entries after an uninstall would trigger, per the pi collision guard at
install.py:834-852, unchanged). Regression: `test_uninstall_reinstall_round_trip_never_hits_the_collision_guard`.

### F07/F08 — scope narrowing invented instead of derived
**Before (bug this rebuild specifically avoids)**: `install-targets.json` never distinguished "no
scope file" from "explicit empty scope", and a naive uninstall reading it would either leave it wide
(F07: the bug the whole package exists to fix, reopened from the uninstall side) or invent "all four
minus the one just removed" (F08) when the file didn't exist.
**Fix**: `run_uninstall()` (install.py:1105-1110) derives the post-uninstall scope from the SURVIVING
`MANIFEST` entries' harness roots — ground truth, never merged/guessed — and always writes it, so the
last uninstall produces an explicit `[]`, never a missing file.
**PoC — live before/after**: uninstalled `codex` (last remaining target after two prior uninstalls in
the same session):
```
before install-targets.json: ["codex"]
$ python3 install.py --home $FIXTURE --uninstall --target codex
after  install-targets.json: []
after  managed-files.json entries under .codex/.claude/.pi: []  (none)
```
And the narrowing case: uninstalling `claude-code` out of a four-target install drops scope from
`["claude-code","codex","opencode","pi"]` to `["codex","opencode","pi"]`. Regression:
`test_uninstall_one_target_leaves_the_other_three_byte_identical` (asserts the narrowed scope
directly).

## 3. F11, checked as part of the same rebuild (foundational to F05/F06's safety, not counted
among the eight but PoC'd the same way)

`previous_targets()`/`manifest_entries_for_uninstall()` now resolve both the candidate and every root
(`_within_any_root`, install.py:675) before the containment check — `Path.parents` never collapses
`..`, so a lexical check would have called `.claude/../../victim.txt` "inside `.claude`" even though it
resolves two directories above `--home`.
**PoC — live before/after**:
```
$ echo "do not delete me" > $OUTSIDE_HOME/victim.txt
$ python3 -c "... manifest.append('.claude/../../victim.txt') ..."
$ python3 install.py --home $FIXTURE --uninstall --target claude-code
$ cat $OUTSIDE_HOME/victim.txt
do not delete me      # survived
```
Regression: `test_uninstall_never_deletes_outside_home_via_a_manifest_traversal_entry`.

## 4. F16 (confirmation before a destructive uninstall)

`install.sh`'s `run_uninstall_flow()` (install.sh:53) prints the `--preview` diff, then calls the
existing `confirm()` helper (unchanged, same one `pkg_install` uses) unless `--yes`. Answering "n"
cancels with rc≠0 and touches nothing — PoC'd live, `~/.claude/CLAUDE.md` still present after the
cancel. Regression: `test_install_sh_uninstall_requires_confirmation_without_yes`.

## 5. AC-09's original bug (`cmd_update`)

`set_agents_app.py:1249-1272` (only function touched in this file, as declared). `cmd_update` used to
build `[build.sh, --install]` with **no `--target`** at all; `install.py`'s own "no `--target` = all
four" default then silently re-widened a machine that had installed with `--harness claude` back to
all four trees on every "Actualizar". Now reads `_install_scope()` (pre-existing, `set_agents_app.py:886`)
and passes explicit `--target` per scoped harness; an explicit empty scope (`[]`, i.e. everything was
uninstalled) skips the reinstall entirely instead of falling through to install.py's own
no-`--target`-means-all default, which would have resurrected the same bug through the empty-list
path (`for target in []: install += [...]` producing zero `--target` flags). A machine that predates
`install-targets.json` (`None`) keeps the historical default (all four), unchanged. Regression:
`test_cmd_update_reinstalls_only_the_scoped_targets` (mocked at the `subprocess.run`/git boundary,
asserts the exact `--target` flags built).

## 6. The ten remaining findings

| Finding | Status |
|---|---|
| F09 (mcp.<id> extended by user → invalid fragment after prune) | **Not addressed.** `_revert_json_special` removes only the leaf keys it owns and prunes an emptied PARENT dict, but if the user added an extra field to an object we otherwise fully own (e.g. `mcp.engram.my_note`), the surviving fragment can be missing `type`/`command`. Documented here as a known gap; the safer of the two bad options (leave a possibly-incomplete fragment vs. silently delete the user's added field) was not resolved this pass. |
| F10 (pre-`SPECIAL_KEYS_MANIFEST` installs no-op silently on uninstall) | **Partially addressed as a side effect.** `manifest_entries_for_uninstall` still removes plain managed files for a legacy install (MANIFEST predates nothing structurally new); the SPECIAL files simply have no delta to revert (`special_entries` empty for that target) and are left untouched, with no explicit `UNINSTALL_NOTE`. Adding that note was not done this pass. |
| F11 (path traversal, lexical fence) | **Fixed**, see §3. |
| F12 (no test for `SPECIAL_KEYS_MANIFEST` cross-preservation across sequential per-CLI installs) | **Covered indirectly** by `test_uninstall_one_target_leaves_the_other_three_byte_identical`, which installs all four then uninstalls one and asserts the other two specials' delta entries are untouched — the sequential-install ordering itself (installing opencode, then claude, then codex one at a time, each pass only updating its own entry via `_PENDING_SPECIAL_KEYS.update`) was exercised manually during development (see tool history) but has no dedicated named regression test. |
| F13 (isolation test not hashing state jsons) | **Fixed** — `_state_files`/the assertions in `test_uninstall_one_target_leaves_the_other_three_byte_identical` cover `.local/state/set-agentes/*.json`, not just the trees. |
| F15 (duplicated backup/rollback) | **Fixed** — `new_backup_dir`/`take_backup`/`restore_backup` (install.py:757-794) shared by both `run_install` and `run_uninstall`. |
| F16 (confirmation) | **Fixed**, see §4. |
| F17, F18 (latent/cosmetic) | **Not investigated this pass** — the context pack itself calls these "latentes y cosméticos"; out of budget for this repair given the eight `high`s took priority as instructed. |

## 7. Mordidas (bite tests — neutralize, red, revert, paste literal)

For each of the following, the fix was commented out / reverted locally, the test re-run to confirm
red, then restored:

1. **`_within_any_root` un-resolved** (F11): reverting to plain `root in candidate.parents` made
   `test_uninstall_never_deletes_outside_home_via_a_manifest_traversal_entry` fail with the victim file
   gone — confirmed red, restored the `resolve()`-based check.
2. **`manifest_entries_for_uninstall` fail-open** (F05): reverting the `stored is None` branch to
   `return [], stored or [], []` (silently proceeding) made `test_uninstall_aborts_closed_on_a_corrupt_manifest`
   fail (`rc=0` instead of `2`, no `UNINSTALL_ABORTED_UNREADABLE_MANIFEST`) — confirmed red, restored.
3. **`revert_codex` skip-check removed** (F04): commenting out the `if live_value != entry["value"]:
   skip` branch made `test_uninstall_codex_keeps_a_key_the_user_changed_since_install` fail (`max_depth`
   became unset instead of staying `3`) — confirmed red, restored.
4. **`run_uninstall` scope derivation replaced with the F08 bug** (`scope = set(all_targets) -
   {t for t in args.target}`): made the narrowing assertion in
   `test_uninstall_one_target_leaves_the_other_three_byte_identical` fail (`install-targets.json` came
   back `["opencode","codex","pi"]` — correct by coincidence for THIS single-target case but would
   invent a wrong scope for a target that was never actually installed in the first place, which is
   exactly F08; the derived-from-MANIFEST version was restored as the only one that is correct in
   general, not just for this fixture).

## 8. Validation run

- `python3 -m unittest` (targeted, per this repair's explicit "no full suite" restriction): 22 tests,
  all passing — the 9 new D4 tests plus 13 pre-existing install/uninstall-adjacent tests
  (`test_managed_install_preserves_unrelated_and_rolls_back`,
  `test_install_py_flags_codex_model_change_distinctly`,
  `test_pi_install_collision_guard_fails_closed_in_preview_and_write_mode`,
  `test_pi_install_target_and_managed_write_set_is_bounded`,
  `test_check_drift_detects_stale_and_clean_install`,
  `test_install_prunes_orphaned_managed_files_but_keeps_user_files`,
  `test_install_prunes_tier_variant_removed_from_models_toml`,
  `test_install_sh_dry_run_plans_missing_tools`, `test_install_sh_dry_run_never_touches_network`,
  `test_install_sh_creates_set_agents_link`, `test_install_sh_yes_terminates_the_opencode_auth_loop`,
  `test_install_sh_redirects_windows_gitbash_to_ps1`,
  `test_build_sh_generate_mode_regenerates_global_and_installs_the_drift_hook`) — no regressions.
- `./build.sh --check` → `SELF_SCAFFOLD_SYNC_OK files=2`, `GLOBAL_TREE_SYNC_OK profile=go-zen
  harnesses=4`, **`BUILD_CHECK_PASS`**.
- `git diff --check` → clean (no whitespace errors).
- Full suite (`python3 -m unittest discover -s tests`) and `verify.sh` were deliberately **not** run,
  per this repair's explicit instruction (other agents share the repo).

## 9. What's left unverified / next steps if reopened

- F09 (mcp fragment left incomplete after a partial user extension) — needs a product decision on
  "delete the incomplete fragment" vs "leave it and warn" before implementing.
- F10's explicit `UNINSTALL_NOTE` for a no-op legacy uninstall.
- F12's dedicated sequential-per-CLI-install regression test (behavior verified manually, not pinned).
- AC-11 remains fully deferred, per the orchestrator's instruction; ADR-0055 records the corrected
  axis (`HOME` + per-CLI `XDG_*`) for whoever implements it, and flags opencode's actual `XDG_CONFIG_HOME`
  support as **sin verificar** (this repo's own `install.py:38-42` hardcoding is verified; opencode's
  runtime behavior is not, no source consulted this pass).
