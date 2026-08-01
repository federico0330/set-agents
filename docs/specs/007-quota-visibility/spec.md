# Feature 007 — quota-visibility, contract 1.3.0

Status: contract approved. Revised after SPEC_CHALLENGE (13 findings, 4 blocking) — see the amendment log
at the end for what 1.0.0 claimed and why each claim was wrong. Revised again as 1.2.0 before P1 was opened:
P0 is retracted and four defects in the P1 criteria are corrected — see the second amendment log. Revised
again as 1.3.0 before P2 was opened: seven rotten `file:line` citations corrected, the citation convention
changed to `file:symbol`, and three couplings the P2 criteria provoked without naming — see the third log.

**Citation convention (1.3.0).** Load-bearing references are written `file:symbol` (`store.py:close_run`), not
`file:line`. Line numbers rot every time a package touches the file: 1.2.0 already had to correct one range by
a line, and 007-P1 then shifted `store.py` by ~100 lines and invalidated four more. A symbol survives the
edit. Line numbers are still used for anonymous blocks that have no symbol, and those are the ones to
re-verify when a criterion is read.

Depends on: feature 004 (adaptive-dispatch, DONE) for the dispatch lifecycle this feature instruments, and
feature 005-P1 (portable-core, accepted) for the `project_key` scoping already in `SCHEMA 5`.

## Contexto

The question that produced this contract: *how much more does an Anthropic token cost through Pi than
through everyday Claude usage?* The qualitative half is already answered and needs no code:

- **There is no per-token surcharge.** `~/.pi/agent/auth.json` holds `anthropic → {"type": "oauth"}`: the Pi
  lane enters through the same Claude subscription, the same quota bucket. The `"You're out of extra usage"`
  error at `docs/specs/004-adaptive-dispatch/evidence/P3-implementation.md:173` proves only that the included
  quota was exhausted at that moment. The claim at `docs/notas/BUENOS-DIAS.md:161` over-reads it and is wrong
  (AC-13).
- **What is asymmetric is consumption per unit of work.** The Pi lane is a CLI subprocess per spawn
  (ADR-0007): a cold conversation, no cache carried across spawns. Measured floor, same evidence file
  (`:149`): a task whose output was 6 tokens cost **3221 input tokens**.

The quantitative half cannot be answered, and that is the defect this feature closes.
`ai/scripts/cost-report.py:5-7` collects OpenCode, Claude Code and Codex; Pi is absent.
`~/.pi/agent/sessions/` is empty because `--print` mode persists no session. And `set_agents_spawn.py:282`
**receives** the exact `usage` Pi returns while the dispatch is closed by `close_run()`
(`routing_core/store.py:400-444`), which records outcome and latency and discards it.

The harness therefore has no record of what its own delegation costs. Under USD 100 subscriptions and 4–5
hour sessions across 2–3 concurrent projects, quota is the binding constraint, and it is the one dimension
of every spawn that leaves no trace.

**Not a premise of this feature:** adaptive routing is *not* blocked. `routing.db` is absent from
`~/.local/state/set-agentes/routing-v2/` (only orphan `-wal`/`-shm` remain); with no file present the store
creates a clean schema-5 database on next use and routing works. Contract 1.0.0 asserted the opposite.

### Confirmación externa, y el hueco hermano

An outside architectural review (Perplexity, 2026-07-28) that explicitly could **not** read this repository
independently named the same gap from first principles: structured logging for an agent harness should record
*"query, agent route, model used, **tokens**, latency"*. This harness records the route, the model and the
latency, and drops the tokens. That the gap is derivable without seeing the code is a reason to close it, not
a reason to widen the contract — everything else that review proposed either already exists here or is
excluded below.

There is a **sibling gap this feature deliberately does not close**: `metric_rollups` accumulates per-model
outcome counts and *nothing outside `store.py` reads them* (verified 2026-07-28). So the harness records what
each model **cost** — after this feature — and still cannot say which model produced the better **result**.
Cost visibility without quality visibility optimises toward whatever is cheapest. Feature 008's selection
depends on both halves; this contract delivers one and names the other so it is not mistaken for done.

## Alcance explícitamente excluido

- **Comparing the anthropic lane against the openai-codex lane.** `ai/catalogs/routes.v1.toml` gives
  `openai-codex` `curated_priority = 10` and `anthropic` `20` at **every** tier, and
  `models.toml [routing].enabled_providers` is all-or-nothing, so a production `--route-decide` can never
  select `anthropic` — the one live anthropic run on record had to be forced through
  `routing._compose_for_tests`. A collector built to compare the two lanes would structurally never have an
  anthropic row. **User decision (2026-07-28): measure the lane the router actually uses and state the gap.**
  P0 briefly superseded this exclusion by making provider preference role-aware; **P0 was reverted the same
  day and the exclusion stands in full** (see the P0 retraction below). This feature adds no way to *force* a
  provider for a measurement run, and it does not change which provider the router picks; it measures whatever
  the router genuinely chose, which today is `openai-codex` at every tier.
- **Feeding token data into the routing decision.** Nothing outside `store.py` reads `metric_rollups`,
  `report()` or `lifetime_count`; selection is tier + `curated_priority` + `route_id` from the catalog. This
  feature makes cost *visible*, never *decisive*. The name is `quota-visibility`.
- **Tokens in `metric_rollups`.** Its primary key (`store.py:149`) has no `project_key`; rollups are global
  by design. Putting tokens there would leak per-project totals across projects. Explicit non-goal.
- **Recovering the schema-4 history.** The two verified backups
  (`~/.local/state/set-agentes/routing-v2/backups/routing-v4-*.db`, schema 4, 2 dispatches / 7 rollups /
  10 events each) are a probe run with no analytical value, and their `dispatches` table lacks the `N03`
  `CHECK` entirely — recovering them would need a 12-step SQLite table rebuild. **User decision
  (2026-07-28): discard.** The backups are left untouched where they are; nothing restores them.
- **Closing the trigger/view gap in schema validation.** `_validate_schema()` enumerates only
  `type='table'` and the DDL comparison covers only `type IN ('table','index')`, so a trigger or view added
  to the file is invisible and the store still opens (verified live during SPEC_CHALLENGE). Real, out of
  scope, recorded separately as `routing-ddl-validation-blind-to-triggers`.
- **Dollar figures as the headline number.** Pi returns `cost.total` in dollars, but over subscription OAuth
  that figure is notional. Tokens stay the primary unit — the doctrine `cost-report.py:10` already declares.
- **Measuring interactive Pi usage.** The collector reads the routing database, so it sees only spawns that
  went through `set_agents_spawn`. A hand-run `pi` stays invisible.

## P0 — role-affinity, retracted

P0 was added after contract 1.1.0 on user instruction (*"prefiero a sonnet 5 implementando, antes que a gpt;
gpt es más lento, por eso prefiero que audite"*), implemented as a role-scoped `curated_priority` (6 catalog
rows split into 12), and **reverted the same day**. Its three criteria AC-20, AC-21 and AC-22 are withdrawn
from this contract in 1.2.0.

Why, in one line: a fixed per-role provider preference is the *opposite* of the reformulated goal — it takes
away from the orchestrator exactly the decision the user wants it to make. The review panel also returned two
high findings (in the primary OpenCode lane an `anthropic` decision is abandoned and falls back to the static
agent, losing the dynamic tier; and nothing required the two role groups to be disjoint), and two thirds of
what P0 promised was already true without it (`models.toml [areas.implement] claude=sonnet` /
`[areas.audit] claude=opus` already governed the Claude Code lane, and `REVIEW_PROVIDER_CONFLICT` already
forced a reviewer to the provider opposite the writer's).

**The scope moved to feature 008 (`dynamic-selection`), which owns adaptive model and effort selection and
which depends on 007-P2 for the measurement half.** The full record — including the requirement to keep the
test the package-reviewer identified as the only real guardian of a split catalog — is decision
`p0-role-affinity-reverted`. The 008 contract is not edited from here; it is another feature with open
packages.

## P1 — schema-normalize

Root cause, corrected. `store.py` normalizes stored DDL with `" ".join(text.split()).lower()` in three
places (`_canonical_schema_sql():170`, `_validate_existing_readonly():187`, `migrate_from_v4():279`). That
collapses whitespace and case but **preserves SQL comments**, and `ALTER TABLE ADD COLUMN` keeps the original
`CREATE TABLE` text in `sqlite_master` — so a comment added to the canonical DDL after a database was created
permanently blocks that database's migration.

Two things follow that contract 1.0.0 got wrong:

- The real schema-4 backups diverge in **two** ways, not one: the `-- N03:` comment (`store.py:140-142`)
  **and** the table-level `CHECK(state<>'abandoned' OR …)` it documents (`store.py:143`), which commit
  `71abca1` added in the same commit that raised `SCHEMA` to 4. **`schema_version` does not identify a unique
  DDL.** Comment normalization alone does not migrate those files, and it is not supposed to.
- Therefore P1 is future-proofing plus honest diagnosis, not recovery of that database.

- **AC-01** — a single `_normalize_ddl()` is the only DDL normalizer; the three hand-rolled sites call it.
  It is proved by counting the normalizer in the source plus one behavioural test per site: patching the
  function with a call counter proves nothing, because `RoutingStore._canonical_ddl` (`store.py:161`) is a
  class attribute that is never invalidated — the patch either reads a warm memo or leaves a poisoned
  canonical behind for every later test in the process.
- **AC-02** — normalization removes `--` line comments and `/* */` block comments, and is delimiter-aware
  across all four SQLite quoting forms (`'…'`, `"…"`, `[…]`, `` `…` ``): a `--` inside any of them is content,
  not a comment. **The reason is correctness, not security** (1.1.0 said the opposite and was wrong; see the
  1.2.0 amendment log): a scanner that is not delimiter-aware corrupts *our own canonical DDL*, because
  `CHECK(run_id GLOB 'run1_[0-9a-f]*' …)` (`store.py:131`) puts a `[` inside a single-quoted literal. Letting
  it open a bracket-quoted identifier flips quote parity for the rest of the statement, so the `-- N03:` block
  at `store.py:140-142` reads as string content and **survives normalization** — silently defeating AC-03
  while every test that opens a freshly created database still passes.
- **AC-03** — a database whose stored DDL differs from canonical **only** in comments migrates and opens.
  Both paths are required: a schema-5 database created that way must open through
  `_validate_existing_readonly`, and a schema-4 one must migrate through `migrate_from_v4` and then open.
  Verified with a fixture built by creating the pre-comment DDL directly, not by hand-editing a normalized
  string.
- **AC-04** — a database whose `CHECK` constraint was altered, added or removed is still rejected with
  `ROUTING_UNAVAILABLE`. Without this the repair is indistinguishable from weakening the control.
- **AC-05** — a database that cannot be migrated because its structure genuinely differs (the real v4 case:
  a missing `CHECK`) is rejected with a **distinguishable diagnostic** naming which object diverged, not a
  bare `ROUTING_UNAVAILABLE`. The current failure is silent about its cause; that silence cost a full
  diagnosis session.
  **Reading that reconciles AC-04 and AC-05**, without which they contradict each other on the identical
  input (a removed `CHECK` is AC-04's subject *and* AC-05's named example): *bare* means *unaccompanied*, not
  *some other code*. The public reason code stays exactly `ROUTING_UNAVAILABLE` — `domain.py:9` calls it "a
  stable public reason code", `test_schema_drift_fails_closed_byte_identically` pins it on a divergence path,
  and `--routing-migrate`'s output contract is pinned by ADR-0008 D8 — and the diagnostic rides alongside it.
  Only names drawn from the canonical set (compile-time constants) may be printed; an object name that came
  from the file is counted, never echoed, because that file may have been written by an attacker.
- **AC-06** — the existing verified backup path (`store.py:243-266`: copy, `integrity_check`, row count) and
  the rollback behaviour are unchanged; migration remains all-or-nothing.
- **AC-07** — `docs/adr/0005-trusted-routing-sqlite-lifecycle.md` carries an amendment stating the real threat
  model: the DDL comparison is a **version-drift and corruption detector**, not a defence against an attacker
  who can write the database file. Anyone who can write the file can write a canonical DDL with arbitrary
  rows, and triggers/views are not covered at all. Contract 1.0.0 called it a security control; overstating
  a control is how it stops being maintained.

## P2 — spawn-accounting

- **AC-08** — `SCHEMA` 5 → 6 adds nullable integer columns to `dispatches` using the **same vocabulary as
  `cost-report.py:FIELDS`** (`input`, `output`, `cache_read`, `cache_write`, `reasoning`), plus `cost_micros`
  and `usage_status`. Recording cache columns is what makes the "Pi reuses no cache across spawns" thesis
  falsifiable rather than a zero written in advance — **which only holds if a dimension the provider did not
  report is stored as `NULL` and never coerced to `0`.** The one recorded live sample
  (`docs/specs/004-adaptive-dispatch/evidence/P3-implementation.md:149`) is
  `{"input": 3221, "output": 6, "totalTokens": 3227, "cost": {"total": 0.003257}}` — Pi reports no cache and
  no reasoning at all, so a `0` written for those keys *is* the zero-in-advance this criterion forbids, and
  would fabricate the very evidence the thesis needs. `NULL` means "not reported"; `0` means "reported as
  zero".
- **AC-09** — the new columns are declared in `_create_schema` **immediately after `project_key`** and in the
  same order as the `ALTER TABLE` statements of the 5→6 step. `ALTER TABLE ADD COLUMN` inserts each column
  after the last column definition and before the first table constraint, so any other placement makes the
  post-migration DDL differ from canonical — the same failure mode as 4→5, invisible until a live run because
  every test that creates a database and reopens it stays green. Related and unstated in 1.2.0:
  `store.py:_authorize_issued` writes `dispatches` with a **positional `INSERT ... VALUES(?…)` and no column
  list**, so widening the table without widening that tuple breaks every authorization.
- **AC-10** — `close_run()` persists the usage (`terminal()` has no production callers; the sanctioned path
  is `store.py:close_run`, reached from `set_agents_app.py:cmd_route_terminal`).
- **AC-11** — the two edges are handled differently, and deliberately:
  - At the **CLI** edge, a *malformed* `--usage` is a parse failure: `ROUTING_INPUT_INVALID`, exit 2, matching
    how `--latency-ms` is already treated (`set_agents_app.py:cmd_route_terminal`, SEC-A02). The run is not yet
    closed; there is nothing to protect. **Malformed means unparseable**: not JSON, or JSON that is not an
    object. Nothing else — a closed key whitelist like `cmd_route_decide`'s would contradict AC-12, which
    requires accepting shapes we cannot map.
  - Inside **`close_run()`**, defensively, a missing or *unusable* usage never aborts the close: the run
    closes and `usage_status` records `ok | absent | invalid`. **Unusable means parseable but not
    trustworthy**: wrong types, negatives, out of range, or AC-12's `totalTokens` mismatch. Closing the run is
    the invariant; the discard is recorded, never silent. A collector that cannot distinguish "consumed
    nothing" from "we have been dropping every reading" reintroduces the exact blindness this feature exists
    to remove.
  - `absent` is a usage that never existed: the two failure closes that never spawned. Note
    `set_agents_spawn.py:spawn` returns `usage or {}`, so an empty object is the common real case for a
    provider that reported nothing — `{}` is `absent`, not `invalid`. And `ok` with NULL cache columns is
    correct, not a degraded reading: the provider reported everything it has.
- **AC-12** — `cost.total` (a float, USD) converts to `cost_micros` by a stated rule: round-half-up to the
  nearest micro-dollar, values outside `[0, 2^53)` treated as invalid. No float is stored. If
  `totalTokens != input + output` the row is still written and `usage_status` is `invalid`: that inequality is
  the signal that Pi began reporting a dimension we do not yet map.
  Two things 1.2.0 left unstated and measured since. **Round-half-up is not implementable on the parsed
  binary float**: `0.0000005` — exactly half a micro-dollar as written — becomes `4.999…e-7` in IEEE754, so
  both `round()` and `Decimal(float)` + `ROUND_HALF_UP` yield `0` while the value the provider *wrote* rounds
  to `1`. The usage JSON is therefore parsed with `parse_float=decimal.Decimal`, which yields the exact
  decimal from the source text and makes the rule well-defined. And `[0, 2^53)` is **not** a storage bound:
  SQLite binds up to `2^63-1` (and `close_run` already catches the `OverflowError` above it). `2^53` is the
  ceiling of exact-integer JSON precision.
  **The bound applies to the stored `cost_micros`, not to `cost.total` in dollars.** Read the other way it
  contradicts AC-11: a `cost.total` of `2^53 - 1` *dollars* passes, becomes ~9.0e21 micros, exceeds SQLite's
  `2^63-1` bind limit, raises `OverflowError` — which `close_run` catches into a ROLLBACK, so **the run does
  not close**. Measured. The dollar reading of this bound is the one shape of input that turns a cost figure
  into an unclosable run.
  **And the mismatch rule is `totalTokens != the sum of every present mapped token field`**, not literally
  `input + output`. On today's payload the two are identical, because Pi reports only those two. Written
  literally it would start firing falsely the day Pi begins reporting cache tokens — which is precisely when
  AC-08's falsifiability payoff arrives, so the literal reading breaks the criterion exactly when it starts
  to matter.
- **AC-13** — `--route-terminal` accepts `--usage '<json>'`. The parsing helper is written locally rather than
  imported across scripts, and rejects non-objects. `feature-state.py:parse_json_object` is *not* the model to
  copy: it raises `StateError`, a `RuntimeError` subclass, and `set_agents_app.py:_lifecycle_command` does not
  catch `RuntimeError` — a bare copy would escape as a traceback and break the one-JSON-line contract. The
  model is `set_agents_app.py:cmd_route_decide`: a bare `ValueError` as a control-flow signal with one flat
  `except`.
- **AC-14** — `migration_required()` becomes version-generic (any stored version below `SCHEMA`, not the
  literal `"4"` in `store.py:migration_required`), the `--routing-migrate` CLI reports real `from`/`to`
  instead of the hardcoded `from=4 to=5` (`set_agents_app.py:cmd_routing_migrate`), and 4→5→6 chains. Without
  this, raising `SCHEMA` turns every existing schema-5 database into a closed failure with no
  `ROUTING_SCHEMA_MIGRATION_REQUIRED` warning.
  Two couplings 1.2.0 did not name. The post-migration DDL check compares against the **current** canonical,
  which after this package is schema 6 — so a 4→5 step alone can no longer validate, and the chain must run
  under **one** `BEGIN EXCLUSIVE` with a single comparison at the end. And `ROUTING_MIGRATE_OK from=4 to=5` is
  an output contract **pinned by ADR-0008 D8** and by a regression assertion; this criterion requires changing
  it, so ADR-0008 is amended in the same package and the assertion is rewritten over the real values. The
  justification is not convenience: once schema 6 exists, `from=4 to=5` is a false statement, not a format.
- **AC-15** — `--routing-report` reports token totals per route alongside the existing latency percentiles,
  and states the scope difference explicitly: percentiles come from `events`, which has no `project_key` and
  is machine-global; tokens come from `dispatches`, which is per-project.
- **AC-16** — `cost-report.py` gains a `pi` collector reading the routing database. Because `project_key` is
  a truncated hash (or a persisted random value when `ai/state/project.json` exists,
  `set_agents_app.py:project_key_for`) it is **not invertible to a directory**: the collector attributes rows
  only when `--project` is given, by recomputing the key, and otherwise reports the lane unattributed rather
  than guessing. Both `--help` and `TIPS-USO.md` state the coverage limit: only harness-dispatched spawns.
  The routing database path comes from `cost-report.py`'s own `--home` seam, not from the store:
  `store.py.__init__` derives home from `pwd.getpwuid` *deliberately*, so the environment cannot redirect
  where durable authorizations live (ADR-0005), and a read-only reporter must not import `routing_core` to
  ask. The key derivation is therefore duplicated, and a test pins that the two derivations agree.
- **AC-17** — token data has no retention: `store.py:_compact_in` compacts `events` only, and `dispatches` has
  no retention path anywhere in `store.py`. This is stated as an invariant so it is not later "optimized"
  away, together with its acknowledged cost: `dispatches` grows without bound, which is already true today
  and which this feature does not worsen.
- **AC-18** — `docs/adr/0010-spawn-accounting.md` records the design and the rejected alternatives.

## P3 — correct the record

- **AC-19** — `docs/notas/BUENOS-DIAS.md:161` is replaced by what was verified: same OAuth, same quota
  bucket, no surcharge; the real cost is the per-spawn input floor of the CLI lane. The `rm` remediation
  offered in that note is also withdrawn — the database it names no longer exists and routing is not blocked.
  The correction is recorded with `log-decision`, because retracting a recorded claim is a decision.

## Verificación

`./ai/scripts/verify.sh` → `VERIFY_PASS` · `./build.sh --check` → `SELF_SCAFFOLD_SYNC_OK files=2` ·
`python3 -m unittest discover -s tests -v` · `git diff --check` · ownership vs baseline. Test count rises
from 209, never falls, and no test is skipped.

Live end-to-end, split by the package that owns each line — 1.1.0 mixed P1 and P2 in one bullet:

1. **P1.** A synthetic comment-only-divergent database migrates and opens (AC-03); one whose `CHECK` was
   altered is still refused (AC-04); one whose `CHECK` is missing is refused with a diagnostic naming the
   object (AC-05), and the two real schema-4 backups on this machine are diagnosed that way without being
   modified.
2. **P2.** A schema-5 database created by the current code migrates to 6 and opens, row counts preserved
   (AC-08, AC-09, AC-14). Then a real spawn through the `openai-codex` lane, and `--routing-report` showing
   its tokens.
3. `ai/scripts/cost-report.py --project .` listing the `pi` lane beside the other three.
4. With that in place, measure a real package and report what harness delegation actually costs per spawn —
   stating plainly that the anthropic-vs-openai comparison is out of scope and why.

## Amendment log — what contract 1.0.0 got wrong

SPEC_CHALLENGE ran before any code was written and returned `revision_required`: 13 findings, 4 blocking.

| # | 1.0.0 claimed | Reality |
|---|---|---|
| F-01 | A missing comment blocks the real v4 migration | The real v4 DB also lacks the `N03` `CHECK`; `schema_version` does not identify a unique DDL. AC-03 split, AC-05 added |
| F-02 | Adaptive routing is blocked; migrate the real DB | `routing.db` does not exist; routing works on a fresh schema-5. Premise and verification step removed |
| F-03 | The Pi collector answers the anthropic-vs-Claude question | `curated_priority` makes an anthropic row impossible in production. Retracted into Alcance excluido by user decision |
| F-04 | `terminal()` is the persistence point | `terminal()` has no production callers; `close_run()` is the sanctioned path. AC-10 corrected |
| F-05 | Four token columns suffice | They erase the cache dimension that makes the thesis falsifiable, and no conversion rule was stated. AC-08, AC-12 |
| F-06 | Only 5→6 needed specifying | Raising `SCHEMA` breaks every schema-5 DB with no warning; `migration_required()` is hardcoded to `"4"`. AC-14 added |
| F-07 | 5→6 exercises the P1 repair | It does not — both sides come from the same generator. The real coupling is column placement. AC-09 |
| F-08 | Malformed usage is discarded | Silent discard rebuilds the blindness the feature removes, and contradicts `--latency-ms`. AC-11 splits the edges |
| F-09 | Literal-awareness means single quotes | Four quoting forms plus block comments, or text can be hidden from the comparator. AC-02 |
| F-10 | Exact DDL equality is a security control | It is a version-drift/corruption detector; triggers and views are invisible. AC-07; gap recorded separately |
| F-11 | — | `dispatches` has no retention (AC-17); `--routing-report` mixes scopes (AC-15); `project_key` is not invertible (AC-16) |
| F-12 | The router optimizes latency and success | Nothing outside `store.py` reads the rollups. Made an explicit non-goal |
| F-13 | — | ADR work was in the package tasks but no AC required it. AC-07, AC-18 added |

## Amendment log — 1.1.0 → 1.2.0, before P1 was opened

Written the day P1 was planned, from measurements taken against today's tree. Nothing here changes *what* is
built: AC-04 and AC-05 are both implemented in full. What changes is that the contract can now be judged.

| # | 1.1.0 said | Correction |
|---|---|---|
| A-01 | P0 `role-affinity` is a package of this feature (AC-20/21/22) | Reverted the same day for contradicting the reformulated goal; the scope moved to feature 008. Section retracted, the three AC withdrawn, the F-03 exclusion restored in full. Decision `p0-role-affinity-reverted` |
| A-02 | AC-04 demands `ROUTING_UNAVAILABLE` for a removed `CHECK`; AC-05 forbids "a bare `ROUTING_UNAVAILABLE`" for a removed `CHECK` | A direct contradiction on the identical input. Resolved in writing: the code is unchanged, the diagnostic rides alongside. Without this a reviewer fails the package against whichever AC they read second |
| A-03 | AC-02 exists so quoted text cannot be "hidden from the comparator" | A security rationale inside the package whose AC-07 retracts the security framing — and false anyway: whoever can write the file writes canonical DDL directly. The real reason is measured: a non-delimiter-aware scanner corrupts our own canonical DDL (2843 chars with `-- n03` still in, vs 2581 correct) |
| A-04 | AC-01 is "a single `_normalize_ddl()` is the only normalizer" | Not behaviourally testable as stated, and the obvious test poisons the suite through the never-invalidated `_canonical_ddl` class attribute. Method of proof written into the AC |
| A-05 | AC-06's backup path is `store.py:243-265` | The block ends at `:266`; `:265` cuts the `finally` that closes the source connection. A cited invariant range must not be silently redrawn |
| A-06 | Live evidence item 1 mixes "migrates to 6" with the P1 fixtures | 5→6 is AC-08/AC-09/AC-14, which are P2. Split by owning package |

## Amendment log — 1.2.0 → 1.3.0, before P2 was opened

Again nothing here changes *what* is built. What changes is that the criteria can be followed: 007-P1 shifted
`store.py` by roughly a hundred lines the day before P2 was planned, and four of P2's citations became
pointers to unrelated code. AC-14 said "the literal `4` at `store.py:209`", and `:209` is a `sqlite3.connect`.

| # | 1.2.0 said | Correction |
|---|---|---|
| B-01 | Seven `file:line` citations across the P2 criteria | All seven were wrong. `cost-report.py:24` → `:23` (24 is blank); `close_run` at `store.py:400-444` → `:517-561`; the `"4"` literal at `store.py:209` → `:327`; `_compact_in` at `store.py:470-478` → `:587-595`; the SEC-A02 block at `set_agents_app.py:478-482` → `:477-482`; `parse_json_object` at `feature-state.py:126` → `:128-132`. Rewritten as `file:symbol`, and the convention is stated at the top |
| B-02 | AC-08 justifies cache columns as making a thesis falsifiable | True only if an unreported dimension is stored `NULL`. Pi reports neither cache nor reasoning in the one live sample, so coercing absent to `0` fabricates exactly the evidence the thesis needs. Stated in the AC |
| B-03 | AC-12 says "round-half-up" | Not implementable on the parsed binary float — measured: half a micro-dollar rounds to 0 instead of 1. `parse_float=decimal.Decimal` added to the AC. Also: `[0, 2^53)` is a JSON-precision bound, not a storage bound; SQLite reaches `2^63-1` |
| B-04 | AC-13 points at `parse_json_object` as the reference | It raises `StateError(RuntimeError)`, which `_lifecycle_command` does not catch — copying it leaks a traceback and breaks the one-JSON-line contract. `cmd_route_decide`'s idiom named instead |
| B-05 | AC-11 says "malformed" and "unusable" without defining either | They are different edges doing different work. Defined: unparseable at the CLI, untrustworthy in the store, plus what `absent` means and why `ok` with NULL columns is not a degraded reading |
| B-06 | AC-09 is about column placement | Placement is only half. `_authorize_issued` writes `dispatches` positionally with no column list, so widening the table without widening that tuple breaks every authorization. Named in the AC |
| B-07 | AC-14 requires real `from`/`to` in the migrate banner | That string is pinned by ADR-0008 D8 and by a regression assertion. The criterion cannot be met without changing both, so the amendment and the rewritten assertion are named as package work rather than discovered mid-review. Also: the chain must run under one transaction, because the post-migration comparison is against the current canonical |
| B-08 | AC-12 bounds "values" by `[0, 2^53)` without saying which values | Read as the dollar figure it **contradicts AC-11**, measured: `2^53-1` dollars → ~9.0e21 micros → `OverflowError` at bind → ROLLBACK → the run never closes. The bound is on the stored `cost_micros` |
| B-09 | AC-12's mismatch rule is `totalTokens != input + output` | Correct today only because Pi reports nothing else. Taken literally it fires falsely the day Pi reports cache tokens — i.e. exactly when AC-08's payoff arrives. Restated as the sum of every present mapped field, which degenerates to `input + output` on today's payload |
| B-10 | — | Not a contract defect but worth recording: the round-half-up rule survives the live path intact. `set_agents_spawn._parse_events` parses Pi's stdout with plain `json.loads`, so the value is a binary float before the harness re-serialises it onto argv — but `json.dumps` emits the shortest representation that round-trips, so `0.0000005 → 5e-07 → Decimal('5E-7') → 1` micro, identical to parsing the original text. Measured. The residual is narrower than it looks: only a provider writing more significant digits than a float can hold loses anything, which is inherent to any float transport |
