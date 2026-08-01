# Integration evidence — 003-trusted-routing-pi-runtime (contract 2.0.0)

Actor: integrator. Date: 2026-07-29. Package `P1R-trusted-routing` was accepted 2026-07-25 and has sat
un-integrated since then. The point of this pass is explicitly *not* to re-check the code as of acceptance
day, but as of today's working tree, after two later features (`004-adaptive-dispatch`, `005-portable-core`,
and — uncommitted, in the working tree right now — `007-quota-visibility` and `009-self-application`) touched
shared infrastructure this package depends on (`routing_core/store.py`, `set_agents_app.py`'s routing CLI
wiring). No package internals were reopened; this note records what was checked at INTEGRATION and one
unresolved process blocker found in the state file itself (§3).

## 0. Global gates (not re-run; orchestrator ran them directly)

`./ai/scripts/verify.sh` → `VERIFY_PASS` (284 tests) · `./build.sh --check` → `SELF_SCAFFOLD_SYNC_OK files=2`.
Not repeated here. As a targeted spot-check (store.py received the largest diff of any file this package
depends on), I did independently re-run just the routing suite: `python3 -m unittest tests.test_routing -v`
→ **114 tests, OK** (162s), including every AC-tagged crash/concurrency/retention/privacy/legacy/CLI test
plus the 007-added schema-6/usage tests that now sit next to them in the same file.

## 1. What changed since 2026-07-25 acceptance, and what didn't

`git log --oneline 5df0878..HEAD -- ai/scripts/routing_core/ ai/scripts/routing.py ai/scripts/set_agents_app.py`
shows three committed touches to `store.py` (004-P1 dispatch-core, 005-P1 portable-core, both additive schema
bumps this package's own AC-06/AC-07 contract anticipates — "schema, pragmas... fails closed" is the
invariant, not a frozen column count). On top of that, the **working tree carries uncommitted 007-P2/009
changes** (`git status` shows `M ai/scripts/routing_core/store.py`, `M ai/scripts/set_agents_app.py`,
`M ai/scripts/cost-report.py`, plus a large `tests/test_routing.py` addition) that bump `SCHEMA` 5→6 to add
per-dispatch usage/cost columns (`usage_input/output/cache_read/cache_write/reasoning`, `cost_micros`,
`usage_status`) and a `--usage` CLI flag on `route-terminal`.

Checked `git diff --stat` for the domain-decision modules this package's contract actually lives in:
`domain.py`, `service.py`, `catalog.py`, `gates.py`, `routing.py`, `ai/catalogs/routes.v1.toml`,
`models_config.py` — **zero diff on all of them** since 003's acceptance commit. Route eligibility, static-ID
derivation, review-identity resolution, Pi disablement, and the fact-completeness matrix are byte-identical to
what was reviewed and accepted. Only the persistence adapter (`store.py`) and the CLI composition layer
(`set_agents_app.py`) changed, and both changes are strictly additive (new nullable columns via `ALTER TABLE`,
a new optional `--usage` flag gated so it only applies to `route-terminal`).

## 2. AC-by-AC confirmation against the working tree

- **AC-01, AC-01a (facts boundary).** Unchanged code (`domain.py`/`service.py`). Live-confirmed via the
  routing suite (`test_unhashable_required_tools_degrades_not_raises`,
  `test_unverified_review_reports_tier_without_execution`, and the full downgrade-matrix block) — all pass.
- **AC-02, AC-02a (static IDs, collision safety, provider inventory).** Unchanged code. Live-confirmed:
  `test_static_ids_exclude_runtime_and_catalog_is_immutable` passes; the real `routing.db` on this machine
  carries `route_id='rt1_19b417ba8ec5fd2a'` (fits `rt1_<16hex>`).
- **AC-03, AC-03a (writer identity, review independence, run-ID shape).** Unchanged code
  (`implementation_identity`/`recent_writers` logic in `store.py` untouched by the diff — only new columns
  were appended, the identity-resolution query and its `WHERE` clause are unmodified). Live-confirmed: the one
  real dispatch on disk is `role_class='writer'`, `state='terminal_success'`, `run_id` matches `run1_[0-9a-f]{32}`.
- **AC-04 (Pi guardrails).** Unchanged code (`catalog.py`/`gates.py`). No live Pi dispatch to inspect today,
  but nothing in the diff touches Pi eligibility, and the suite's Pi-specific tests pass.
- **AC-05 (simulated explanation, CLI envelope, legacy detection).** Live-confirmed two ways:
  1. `--route-explain` with an invalid task class returned the exact schema-2 envelope
     (`{"schema_version":2,"ok":false,"command":"route-explain","data":{},"warnings":[],"reason_codes":["TASK_CLASS_INVALID"]}`)
     and left `routing.db`'s MD5 byte-identical before/after — non-mutation is proven, not merely asserted.
  2. `--routing-report --json` returned `"warnings":["LEGACY_ROUTING_STATE_PRESENT"]`, correctly detecting two
     genuine pre-003 legacy artifacts still on this machine
     (`~/.local/state/set-agentes/routing/routing.lock`, `routing-metadata.json`, both dated 2026-07-24,
     pre-dating the v2 cutover). This is the legacy detector working as specified, not a regression: warnings
     are allowed at exit 0 and do not block routing-v2, per spec's explicit-precedence rule 2.
- **AC-06 (managed root, tamper resistance, salt never emitted).** `store.py`'s symlink/ownership/mode
  checks, `_validate_existing_readonly`, and `SchemaDivergence` fail-closed path are untouched by the working
  diff except for the `_ddl_divergence` comparison now also covering the new usage columns (it compares
  against the canonical DDL built fresh from the same `_create_schema` source, so drift detection still
  self-updates rather than going stale). Live-confirmed: `meta` on disk holds `schema_version='6'`,
  `installation_hmac_salt` is a 64-char hex string, and it is **not** present anywhere in `--routing-report`'s
  JSON output.
- **AC-07, AC-07a (atomic authorization, partial write, fallback, crash matrix).** `_authorize_issued`,
  `mark_dispatched`, `mark_partial`, `consume_fallback`, `terminal`, `abandon` all keep their original
  `BEGIN IMMEDIATE` / precondition-`WHERE` / single-commit shape; the diff only appends `USAGE_COLUMNS` to the
  authorization insert's *column list* (now named, not positional — see the file's own comment on why that
  matters for exactly this reason) and appends usage-column `SET` clauses to `close_run`'s two UPDATE
  branches, without touching any state-transition guard. Live-confirmed by the suite's full crash-matrix
  block (`test_sqlite_authorization_closes_fallback_before_dispatch`,
  `test_the_ddl_comparison_sees_schema_and_the_integrity_check_sees_rows`, and the rest) — all pass.
- **AC-08 (privacy, retention).** The new usage/cost columns are token counts and a derived cost figure, not
  task body/prompt/source/credentials/PII/provider output — they do not fall into any forbidden category this
  AC lists, so their addition does not weaken it. `_compact_in` still only ever deletes from `events`;
  grepped the current file for any `DELETE`/retention statement touching `dispatches` — none exists,
  confirming 003's "dispatches are never compacted" invariant survived the 007 addition.
- **AC-09 (full compatibility/verification gate).** `./ai/scripts/verify.sh` passes at 284 tests; the routing
  suite alone passes at 114/114; no 003-owned test was weakened, skipped, or deleted — the only removed lines
  in `tests/test_routing.py`'s diff are a schema-4-specific fixture that was generalized into a version-generic
  helper reused by 007's own multi-step migration tests, not a loss of coverage.

**No AC failed. No substantive regression found.** The only drift since 2026-07-25 is additive persistence
schema and CLI surface belonging to a different, later feature (007), and it is additive by construction
(`ALTER TABLE ADD COLUMN`, nullable, checked, never touching the columns or transitions 003 owns).

## 3. Citation/line-number drift in design.md

`design.md`'s "Schema" section (`### dispatches`) enumerates the exact column list as it stood at 003's own
acceptance and does not carry any `file:line` citations into `store.py` (grepped for `store.py` and
`line \d+`/`:\d+\)` patterns — the only three hits are the module-boundary diagram, not citations into current
code). This is **cosmetic, not substantive**: design.md is explicitly scoped as "the architecture review for
... version 2.0.0" (its own opening line), a point-in-time document for what P1R needed to build, not a live
mirror of the shared `dispatches` table's current column set — later features (004's `abandoned` state, 005's
`project_key`, 007's `usage_*`/`cost_micros`) each own their own design/ADR documents for their deltas
(`ADR-0008`, `ADR-0010`). No citation in design.md points at a stale line number in `store.py`; the drift is
only that its column enumeration is now a strict subset of the live table, which is expected schema
evolution, not rot. No action needed.

## 4. Cross-package findings

None blocking. One item surfaced and explicitly **not** acted on, per the integrator's own remit:

- The routing-v2 schema has moved to version 6 with two feature's worth of unrelated columns
  (`project_key` from 005, `usage_*`/`cost_micros`/`usage_status` from 007) layered onto the table 003
  designed. This is by design (ADR-0005's "one durable store" decision, amended by 005/007's own ADRs) and is
  not a 003 regression, but it is worth naming explicitly for whoever next touches this table: 003's own
  design.md is now the least current of the three schema-owning documents.

## 5. State-file blocker — not resolved, not touched (per this role's remit)

**This is the one item that actually gates `DONE` and needs the orchestrator's attention.** The feature state
file (`ai/state/features/003-trusted-routing-pi-runtime.json`, currently uncommitted/modified in the working
tree) does **not** read `phase: PACKAGE_ACCEPTED` right now. It reads:

```
"phase": "BLOCKED", "final_state": "BLOCKED", "updated_at": "2026-07-29T16:55:25+00:00"
```

with an unresolved (no `resolved_at`) blocker entry:

```json
{"at": "2026-07-29T16:55:25+00:00", "package_id": "P1R-trusted-routing", "reason": "spawn budget exhausted"}
```

`packages[0].attempts.spawns` is `16`, exactly equal to `budgets.max_spawns_per_package` (`16`). Reading
`cmd_record_spawn` in `ai/scripts/feature-state.py`: the guard is `attempts.get("spawns", 0) >= budget` →
`block_with_reason(...)`. The package's spawn counter accumulated across its whole PACKAGE_IMPLEMENTATION →
PACKAGE_REVIEW → PACKAGE_REPAIR (×3 rounds: R1/R2/R3) → PACKAGE_ACCEPTED lifecycle and landed exactly at the
budget ceiling on acceptance day; it was never reset or re-scoped for the INTEGRATION phase. Whatever process
called `record-spawn --package-id P1R-trusted-routing` today (2026-07-29, presumably an earlier attempt to
start this integration pass, given the timestamp) tripped the same package-level counter and the state machine
auto-blocked the feature, exactly as `feature-state.py`'s guard is designed to do when a spawn budget is
exhausted with no fresh authorization on record — the same pattern as the three prior R1/R2/R3 blockers in this
feature's own history, each of which required an explicit user re-authorization to lift.

Per this role's remit, I did **not** touch this file, run any `feature-state.py` mutating command, or attempt
to work around the block. This needs the orchestrator to either authorize a fresh spawn budget scoped to
INTEGRATION (consistent with how R1/R2/R3 were each explicitly re-authorized in this feature's own history) or
otherwise resolve the block before recording the `INTEGRATION`/`DONE` transition — the state file's own phase
says `BLOCKED`, not `PACKAGE_ACCEPTED`, as of right now.

## 6. Verdict

**Code/spec verdict: ready.** All AC-01 through AC-09 hold against the current working tree (not just the
tree as of 2026-07-25 acceptance); the two later features that touched shared infrastructure (`store.py`,
`set_agents_app.py`) did so additively and without weakening any invariant 003 owns; the routing suite is
114/114 green including every AC-tagged crash/concurrency/retention/privacy/legacy/CLI probe; no substantive
regression found; the one design.md drift is cosmetic (a point-in-time schema snapshot that predates later
features' additive columns), not a stale code citation.

**Process verdict: blocked.** The state file itself currently records `phase: BLOCKED` /
`final_state: BLOCKED` with an unresolved spawn-budget blocker dated today, contradicting the assumption this
integration pass was launched under ("already `PACKAGE_ACCEPTED`, no more packages planned"). The orchestrator
must resolve that blocker (budget re-authorization, same pattern as R1/R2/R3) before the feature can actually
be recorded as `DONE` — the code is ready, the bookkeeping is not.
