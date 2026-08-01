# P1-spawn-provenance — implementer evidence

Actor: implementer. Package: `P1-spawn-provenance` (feature `010-spawn-provenance`, contract 1.0.0).
All 7 tasks marked `completed` via `feature-state.py start-task`/`complete-task`.

## Changed files

- `PROYECTO/ai/scripts/feature-state.py` (template, edited first)
- `ai/scripts/feature-state.py` (byte-identical copy, per `build.sh --check`'s
  `SELF_SCAFFOLD_DRIFT` guard)
- `tests/test_harness.py`
- `docs/adr/0014-spawn-provenance-node.md` (new)
- `docs/adr/0013-execution-graph-view.md` (status-line annotation only — see "Known
  conflict" below)
- `docs/adr/README.md`
- `ai/state/features/010-spawn-provenance.json` (via CLI commands, not hand-edited)
- `ai/state/STATUS.md`, `docs/notas/features/010-spawn-provenance.md`,
  `docs/notas/features/010-spawn-provenance/{grafo.md,P1-spawn-provenance.md}` (regenerated
  by `feature-state.py`'s own `mutate()` on every state-mutating command; not hand-edited)

## AC-01 — deterministic `spawn_id` mint + replay guard

`cmd_record_spawn` (`ai/scripts/feature-state.py`): `replayed(data, "record-spawn",
args.event_id)` is now the FIRST statement of the updater — before the phase gate and
before the budget check — mirroring `cmd_start_review_panel`'s guard exactly (same
comment references it). `spawn_id = f"SPAWN-{attempts['spawns']:03d}"`, always derived from
the counter, never `len(package["spawns"])`. `package.setdefault("spawns", [])` creates the
list on first use for a package that predates this key. A duplicate `spawn_id` against the
list raises `StateError` (defense in depth, fixture-only). `compact_package()` gained
`"spawns": []` in its base schema (purely additive).

Adversarial-first: wrote the four new tests below and confirmed each FAILED against
today's pre-fix tree (captured in this session's transcript) before applying the fix.

Tests (all green post-fix):
- `test_record_spawn_mints_sequential_spawn_ids_from_the_counter`
- `test_record_spawn_on_a_package_with_a_precedent_counter_but_no_spawns_list_continues_the_counter`
  — the exact `attempts.spawns=8`, no `spawns[]` key fixture named in the spec; asserts
  the next mint is `SPAWN-009`, never `SPAWN-001` (this is also the fixture that proves
  `record-spawn`'s `setdefault` over a legacy package never raises — AC-05's own bullet).
- `test_record_spawn_replay_guard_is_first_and_produces_exactly_one_entry`
- `test_record_spawn_rejects_duplicate_spawn_id_against_a_desynced_counter`

## AC-02 — `graph` subcommand gains a `spawn` node type, no edges

New helper `_add_package_spawns(state, fid, pid, package)` in `ai/scripts/feature-state.py`,
called from `_add_feature_to_graph` right after `_add_package_findings`. Builds one `spawn`
node per `package["spawns"]` entry, label = `f"{spawn_id} {role}"` plus `f" {purpose}"` only
when `purpose` is non-empty. No key at all on the package → zero spawn nodes, never an
error. `GRAPH_EDGE_TYPES` untouched (still exactly 5 members) — nothing calls `add_edge`
for a spawn node. `GRAPH_NODE_TYPES` (documentation-only constant) gained `"spawn"`.

Tests:
- `test_graph_spawn_node_type_renders_label_and_no_edges` (label content, no edge ever
  touches a spawn node id, `len(GRAPH_EDGE_TYPES) == 5`)
- `test_graph_spawn_node_absent_when_package_has_no_spawns_key`
- Renamed `test_graph_never_emits_spawn_nodes_and_survives_legacy_fixtures_without_commit`
  → `test_graph_omits_spawn_nodes_for_a_package_lacking_spawns_list_and_survives_legacy_fixtures_without_commit`,
  comment repointed from "spawn nodes never exist" (false since AC-02) to "a package
  without `spawns[]` still renders zero spawn nodes" (the surviving invariant). No
  assertion in the test body changed — only the name and the comment.

Full `-k graph` suite (27 tests) green after the change.

## AC-03 — no orchestrator doctrine change; ADR-0014 + index

- `Global/**` untouched (declared `read_only_paths` on the package already; not touched).
- `docs/adr/0014-spawn-provenance-node.md` (new): documents why `spawn_id`
  (package-scoped, JSON-file-minted, `routing_core`-agnostic) does not replace, wrap, or
  read `run_id` (`ai/scripts/routing_core/store.py`, globally unique, SQLite-transactional,
  answers a different question — provider/model/route dispatch, not delegation
  bookkeeping). Also records that this feature IS ADR-0013 D3's deferred "P3.1".
- `docs/adr/0013-execution-graph-view.md`: status line gained a `Superseded in part by
  ADR-0014` sentence (D1/D3's spawn-node-deferral claim only; D1's derive-in-read design,
  D2, D4, D5 untouched, no other line in the file touched).
- `docs/adr/README.md`: new row for 0014; 0013's row gained `Superseded in part by 0014`
  in its Status column and `0014 (spawn node deferral only)` in Superseded-by.
- `test_every_adr_on_disk_has_a_row_in_the_index` and
  `test_the_adr_index_never_lists_a_file_that_is_not_there` both green.

### Known conflict — flagging for the orchestrator, not resolved unilaterally

The package's own `read_only_paths` (in `ai/state/features/010-spawn-provenance.json`)
declares `docs/adr/0013-execution-graph-view.md` verbatim as read-only. AC-03 of the
approved spec explicitly requires annotating that file's own status line (`spec.md` line
77-78 names this exactly: "0013 no se reescribe en su contenido, pero su status line ...
sí gana la nota ... eso es lo que el índice pide, no una excepción a su regla" — matching
this repo's own ADR-index rule and ADR-0004's existing precedent, which already carries
the same kind of status-line annotation). I made the single-line, spec-mandated edit
(nothing else in 0013 touched) rather than silently leaving the spec's explicit AC-03
requirement unmet. This means `check-owned-paths.py`, run against the real changed files,
correctly reports `docs/adr/0013-execution-graph-view.md` under `read_only_violations`
(see the "Local gates" section below) — this is not a mistaken diff, it is the one file
this AC explicitly requires touching, colliding with a path the package declared read-only
at planning time. I did not self-grant an `approved_exceptions` entry for it (that reads as
self-approving a scope deviation, which is not the implementer's call). Recommend the
orchestrator either records an `approved_exceptions` entry for this exact path scoped to
the status-line note, or confirms the flagged gate result is expected and resolves it at
review.

## AC-04 — `done_ready()` filters blockers by `resolved_at`, not list-emptiness

`done_ready()` (`ai/scripts/feature-state.py`): replaced `if data.get("blockers"):` with
`if any(not blocker.get("resolved_at") for blocker in data.get("blockers", [])):` — the
same falsy filter `summarize_feature()` already uses a few lines below in the same file.
A hand-written `"resolved_at": null` still counts as unresolved (falsy check, not
"key absent").

Adversarial-first: both new tests confirmed red against the pre-fix tree.

Tests:
- `test_done_ready_reaches_done_after_a_real_block_and_reopen_cycle` — real CLI sequence
  (`block` → `reopen` → the rest of the happy path → `transition DONE`), the same shape
  `005-portable-harness`'s own live history has (2 blockers, both `resolved_at` set,
  currently sitting in `INTEGRATION`).
- `test_done_ready_still_blocks_when_any_blocker_lacks_resolved_at_fixture` — fixture-only,
  per the spec's own admission (`LEGAL_TRANSITIONS["BLOCKED"] = set()` plus `cmd_reopen`'s
  unconditional `setdefault` over every blocker means no real CLI path reaches `DONE` with
  an unresolved blocker still on file). Also exercises the `resolved_at: null` distinction.
- `test_done_ready_passes_when_every_blocker_has_resolved_at_fixture`

**Not done by me, for the orchestrator to do on acceptance**: this AC explicitly
supersedes two already-logged decisions —
`docs/notas/decisiones/2026-07-28 una-feature-bloqueada-y-reabierta-no-puede-llegar-nunca-a-done.md`
and
`docs/notas/decisiones/2026-07-29 done-ready-does-not-filter-resolved-blockers.md`.
Per the spec, the `log-decision` recording this supersession is the orchestrator's action
on package acceptance, not mine.

## AC-05 — regression coverage

All bullets from the spec's AC-05 list are covered by the tests named above, plus:
- `test_check_owned_paths_reports_global_read_only_violation_distinct_from_out_of_scope` —
  synthetic package declaring `read_only_paths: ["Global/**"]`, asserts a violation against
  `Global/_canonical/agents/orchestrator.md` lands in `read_only_violations` and NOT in
  `out_of_scope`, and the reverse for an unrelated out-of-scope path.

This package adds 10 new tests (4 AC-01, 2 AC-02, 3 AC-04, 1 AC-05/check-owned-paths) and
renames 1 existing AC-02 test with no new assertions; final full-suite count is 467, all
green, none skipped.

## Local gates (final run)

- `python3 -m unittest discover -s tests -v`: **467 tests, OK** (0 failures, 0 errors, 0
  skipped).
- `./ai/scripts/verify.sh`: **VERIFY_PASS** (326-test regression subset + portability +
  canonical-paths + feature-state gates, all OK inside verify.sh's own run).
- `./build.sh --check`: **CHECK_PASS** + **SELF_SCAFFOLD_SYNC_OK files=2** (the two
  `feature-state.py` copies are byte-identical).
- `git diff --check`: clean, no output (no whitespace errors).
- `check-owned-paths.py` against the real files this session changed: **OWNERSHIP_FAIL**,
  with exactly one entry in `read_only_violations`
  (`docs/adr/0013-execution-graph-view.md`) and an empty `out_of_scope` list — see "Known
  conflict" above for why, and the exact command run:

```
$ python3 ai/scripts/check-owned-paths.py \
  --state-file ai/state/features/010-spawn-provenance.json \
  --package-id P1-spawn-provenance \
  --changed-file ai/scripts/feature-state.py \
  --changed-file PROYECTO/ai/scripts/feature-state.py \
  --changed-file tests/test_harness.py \
  --changed-file docs/adr/0014-spawn-provenance-node.md \
  --changed-file docs/adr/README.md \
  --changed-file docs/adr/0013-execution-graph-view.md \
  --changed-file ai/state/features/010-spawn-provenance.json \
  --changed-file ai/state/STATUS.md \
  --changed-file docs/notas/features/010-spawn-provenance.md \
  --changed-file docs/notas/features/010-spawn-provenance/grafo.md \
  --changed-file docs/notas/features/010-spawn-provenance/P1-spawn-provenance.md
```

Note on scope of this check: the working tree has ~169 pre-existing untracked/modified
paths from prior, uncommitted feature work (006 through 009 and assorted repo dirt) that
predate this session and are unrelated to this package. `--baseline`/`git diff` against
`HEAD` would have swept all of that in as false "out of scope" noise, so I passed the
explicit `--changed-file` list of only the paths this session's commands and edits actually
touched, confirmed one by one against `git status --porcelain` for each path.

## Assumptions

- The package's own `read_only_paths` entry for `docs/adr/0013-execution-graph-view.md`
  was a planning-time declaration that did not anticipate AC-03's own explicit
  status-line-annotation requirement; I did not treat this as license to edit anything else
  in that file.
- `ai/state/narrative-log.jsonl` and `ai/state/decisions-log.jsonl`, though declared as
  owned paths, were not touched by this session (verified: zero `010-spawn-provenance`
  occurrences in either file) — no `log-narrative`/`log-decision` calls were made; the two
  `record-spawn` history events used by the orchestrator to open this instantiation predate
  my work.

## Known risks

- None beyond the read-only/AC-03 conflict already flagged above.

## Blockers

- None. Package remains in `PACKAGE_IMPLEMENTATION` with all 7 tasks `completed`; gates,
  review, and acceptance are left for the orchestrator and independent reviewers.
