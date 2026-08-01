# ADR-0010 — Spawn accounting: what a Pi spawn actually cost, persisted and not fabricated

- Estado: Accepted (2026-07-29). Feature `007-quota-visibility`, package `P2-spawn-accounting`.
- Numbered 0010, the number `docs/adr/0011-uninterrupted-delegation.md` reserved for it and documented as a
  deliberate hole — that package landed first, so the index carried the gap until this one shipped.
- Amends `docs/adr/0008-two-roots-portability.md` D8 in part (the hardcoded `from=4 to=5` migration banner;
  see D4). Does not amend the routing decision service, the operator-driven migration doctrine (ADR-0005), or
  `cost-report.py`'s own "tokens only" heading — D2 keeps that heading literally true for every lane but this
  one, and says why.
- Every `file:symbol` citation was verified against the working tree on 2026-07-29.

## Contexto

The harness already receives the exact cost of every spawn and throws it away. `set_agents_spawn.py:spawn`
returns `("success", {"model": …, "usage": {…}})`; its only production caller, `route_and_spawn`, unpacks that
`detail` and closed the run with `--route-terminal … --latency-ms N` **without passing it**. The object
survived only as far as a `print(json.dumps(result))` nothing consumed — `grep usage
ai/scripts/set_agents_app.py` returned nothing before this package.

So the harness recorded the route, the model, and the latency of every delegation, and discarded the one
dimension that is the binding constraint. With subscription plans and multi-hour sessions across several
projects, quota is what actually limits work, and it was the only per-spawn number leaving no trace.

The one live sample ever recorded
(`docs/specs/004-adaptive-dispatch/evidence/P3-implementation.md:149`) is
`{"input": 3221, "output": 6, "totalTokens": 3227, "cost": {"total": 0.003257}}` — Pi reports no cache and no
reasoning tokens at all. That absence is not a gap in this package's test fixtures; it is the ordinary shape
of the data, and it is the single fact every decision below has to survive.

## Decisión

### D1 — NULL means "not reported"; 0 means "reported as zero"; and column order is load-bearing

`SCHEMA` 5→6 adds seven nullable columns to `dispatches`: `usage_input`, `usage_output`,
`usage_cache_read`, `usage_cache_write`, `usage_reasoning` (the same vocabulary as
`cost-report.py:FIELDS`, mapped mechanically as `"usage_" + field` — no translation table to drift, pinned
by `tests/test_routing.py:test_the_usage_vocabulary_matches_cost_report`), plus `cost_micros` and
`usage_status`.

A dimension the provider did not report is stored `NULL`, never coerced to `0`. This is not a style
preference: the cache columns exist to make "Pi reuses no cache across spawns" falsifiable, and a `0` written
for a key Pi never sent **is** the zero-written-in-advance that claim would need to not exist. `_usage_row`
(`routing_core/store.py`) enforces this at the one place usage is ever converted to a row.

The seven columns are declared in `_create_schema` **immediately after `project_key`** and the 5→6 migration
step ALTERs them in that same order (`USAGE_COLUMNS`, a single ordered sequence both consumers read — there
is no second hand-maintained list to fall out of step). `ALTER TABLE ADD COLUMN` inserts after the last
column definition and before the first table constraint; any other placement makes the post-migration DDL
differ from canonical, and every test that merely creates a database and reopens it stays green regardless —
this is the exact failure mode `007-P1` exists to have closed, one package later, and it is why
`test_the_usage_columns_sit_exactly_where_alter_table_puts_them` exists as a standing guard rather than a
one-time check.

Related and previously unstated: `_authorize_issued` wrote `dispatches` with a positional
`INSERT ... VALUES(?…)` and no column list. Widening the table without widening that tuple would have broken
every authorization, loudly but without the contract naming the risk. It now writes an explicit
`_AUTHORIZED_COLUMNS` list; no future column ever touches that line again.

Rejected: defaulting the new columns to `0`. It would satisfy `NOT NULL`-style intuitions about tidy schemas
and destroy the one property (AC-08's falsifiability) the columns exist for.

### D2 — `cost_micros` is stored despite `cost-report.py`'s own "tokens only" doctrine

`cost-report.py:10` states the harness's standing position: *"tokens only — subscription plans have no
meaningful dollar-per-token, what matters is quota."* `cost_micros` is stored anyway, and is never headlined
in the report — `--routing-report` and `cost-report.py` both lead with tokens; the dollar figure rides along.

The reason is narrower than "cost is nice to have": this feature exists because the harness receives a
number and drops it. Dropping the cost figure specifically would repeat that exact defect on the one field
that is hardest to reconstruct after the fact — token counts can sometimes be inferred from context size,
a dollar total cannot be recovered once discarded. Storing it costs one column and a conversion rule; not
storing it would be the same silent loss this whole package was written to end, applied selectively to the
one figure a future accounting need is most likely to want.

Rejected: computing cost on demand from tokens at report time. There is no stable price-per-token this
harness owns or controls, and Pi's own `cost.total` is the only authoritative figure available — recomputing
it downstream would silently diverge from whatever Pi actually charged.

### D3 — The two edges reject different things, and there is no closed key whitelist

Malformed and untrustworthy are different failures, handled at different places:

- **The CLI edge** (`set_agents_app.py:parse_usage`, reached from `cmd_route_terminal`) rejects what is
  unparseable (not JSON, or JSON that is not an object) **and** what is too long to parse cheaply — a `~1MiB`
  ceiling, `_MAX_USAGE_TEXT_LEN`. `feature-state.py:parse_json_object` is deliberately not the model copied —
  it raises `StateError`, a `RuntimeError` subclass that `_lifecycle_command` does not catch, and copying it
  would leak a traceback through the one-JSON-line contract. `cmd_route_decide`'s idiom is the model instead:
  a bare `ValueError` as a control-flow signal, one flat `except` at the caller.

  Delta-review finding (N-01, this package's own repair batch): the original prose here claimed "the run is
  not yet closed here; there is nothing to protect" as if the CLI edge were free to reject anything it likes.
  That premise is exactly what `route_and_spawn` refutes: `--usage` and `--route-terminal` are the SAME call,
  so a legitimate-but-large `usage` object that this edge rejects leaves the run `dispatched` forever — the
  identical failure shape F-SEC-02/F-PR-02 closed for a different trigger. The ceiling is sized to make that
  vanishingly unlikely rather than to sit close to any real payload: the one live Pi sample this package has
  ever measured is ~90 bytes, five orders of magnitude below the cap. It is also comfortably above the ~110KB
  needed to trigger `RecursionError` by nesting, so that `except` clause is load-bearing, not shadowed dead
  code behind a tighter length check.
- **The store edge** (`routing_core/store.py:_usage_row`, reached from `close_run`) degrades what is
  parseable but not trustworthy — wrong types, negatives, out-of-range values, or a `totalTokens` that does
  not match the sum of the token fields actually present. It never raises: closing the run is the invariant,
  and the discard is recorded as `usage_status='invalid'` with every numeric column left `NULL`, never
  silent and never a partially-trusted mix of some validated fields alongside some fabricated ones.

Neither edge enforces a closed key whitelist. A whitelist at either boundary would reject shapes the harness
cannot yet map — exactly the case `usage_status='invalid'` exists to describe instead of refuse.

`usage_status='absent'` is reserved for a usage that never existed: the two failure closes that never
spawned. `spawn()` itself returns `usage or {}`, so an empty object is the ordinary case for a provider that
reported nothing, not an anomaly — `{}` is `absent`, never `invalid`. The `close_run` branch that abandons a
never-dispatched run forces `absent` regardless of what its caller passes, because a run that never
dispatched cannot semantically have consumed anything; that invariant is enforced in the store, not left to
caller discipline.

`cost.total` is parsed with `parse_float=decimal.Decimal`, which is what makes round-half-up well-defined at
all: half a micro-dollar written as `0.0000005` becomes `4.999...e-7` once it has passed through an IEEE754
float, and both `round()` and `Decimal(float)+ROUND_HALF_UP` round it to `0` where the text the provider
actually wrote rounds to `1` — measured, not assumed. `[0, 2**53)` bounds the resulting `cost_micros`, never
`cost.total` in dollars: read the other way it contradicts the invariant above it, since `2**53-1` *dollars*
converts to roughly `9.0e21` micros, which would overflow SQLite's `2**63-1` bind limit and roll the close
back — the one shape of input that would keep a run from ever closing. `_cost_micros` enforces the bound on
its own output before returning, so that failure mode cannot occur through this path.

Rejected: a shared `parse_usage`/`cmd_route_decide` key whitelist. It would contradict the store edge's job of
accepting shapes it cannot map, which is the entire reason `invalid` exists as a status rather than a
rejection.

### D4 — Migration becomes version-generic, partially superseding ADR-0008 D8

`migration_required()` now answers on `stored < SCHEMA`, never the literal `"4"` it used to compare against —
a database written by a *newer* harness answers `False` instead of being offered a downgrade, a property the
old literal comparison had for free and a naive rewrite would have lost. `migrate()` replaces the single-shot
`migrate_from_v4` with a declarative `_MIGRATION_STEPS` dict keyed by the version each step migrates *from*,
walked in one `BEGIN EXCLUSIVE` transaction with a single DDL comparison at the end. That single comparison
is a necessity, not a simplification: it runs against the canonical DDL, which after this package is schema
6, so a lone 4→5 step could no longer validate on its own — an intermediate check after 4→5 would compare a
schema-5 database against schema-6 canonical and always fail.

`ROUTING_MIGRATE_OK from=N to=M` now reports the versions actually observed, superseding the hardcoded
`from=4 to=5` that `docs/adr/0008-two-roots-portability.md` D8 pinned. Once schema 6 exists, that literal
would have been a false statement about a chain it no longer describes, not a formatting choice. ADR-0008 is
amended in place rather than silently invalidated.

Rejected: keeping the literal `from=4 to=5` banner and adding a second banner for 5→6. Two banner formats for
one operator command would be its own inconsistency, and neither would generalize to a future 6→7 step.

### D5 — Tokens are a sibling key to the existing latency percentiles, never merged into them

`--routing-report` gains a `tokens` key beside the existing `per_route` latency breakdown, never inside it.
The two have different scopes and different route-key sets, and merging them would silently claim they share
a population: latency percentiles come from `events`, which has no `project_key` and is machine-global;
tokens come from `dispatches`, grouped by `COALESCE(actual_route_id, selected_route_id)` and scoped to the
calling project. A run closed without `--latency-ms` contributes tokens and no percentile — proof, not just
prose, that neither route-key set contains the other. The scope difference is stated in the JSON itself
(`tokens.scope`), not only here.

`SUM()` over a column that is `NULL` for every row in a group returns `NULL`, never `0` — the same
NULL-means-not-reported rule from D1, generalized to the aggregate. Coercing an all-NULL sum to `0` would
fabricate exactly the evidence D1 exists to keep honest, one level up.

`report()` also gains `tokens.status_counts`, a `project_key`-scoped count of dispatch rows grouped by
`usage_status` (review finding F-PR-03/F-PR-04): the token table above already excludes every non-`'ok'` row
by construction, and excluding them silently would be the same blindness AC-11 exists to end, moved one level
up into reporting — a mass discard of `invalid`/`absent` rows must not read as "no pi activity ever happened".

### D6 — The `pi` collector attributes only when told to, and never imports the store

`cost-report.py` gains a fourth lane reading the routing database directly through its own `--home` seam,
never through `routing_core`. `store.py.__init__` derives its home from the account database
(`pwd.getpwuid`), not `$HOME`, *deliberately* (ADR-0005) — a read-only reporter importing the store would
reintroduce exactly the environment-redirection surface that derivation exists to close.

`project_key` is a truncated hash (or a persisted random value when `ai/state/project.json` exists) and is
**not invertible to a directory**. The collector attributes rows to a project only when `--project` is
given, by recomputing the key locally (`cost-report.py:_pi_project_key`, duplicating
`set_agents_app.py:project_key_for`'s public behaviour) and matching it — never by guessing. Without
`--project` the lane is reported unattributed rather than silently wrong. The duplicated derivation is a real
drift risk, so a test pins that the two independently-written functions agree on every identity path: the
persisted-identity path, the hash-fallback path, and (review finding F-SEC-04/F-PR-05) every
present-but-unusable identity — wrong schema, corrupt JSON, symlinked, or oversized — where both functions
must refuse rather than one refusing and the other silently falling back. Same precedent `009-P1` set for
`save_memory.py` against its own prompt-declared path.

A project with genuine activity, all of it older than `--since`, must not be told its own rows "exist for
other projects" (delta-review finding N-02): the zero-match warning above counts other-project rows with an
explicit `project_key!=?` exclusion, not a bare global count, so a stale `--since` window reads as "nothing in
range" rather than misdirecting the operator toward `--project`.

Coverage is bounded to spawns this harness itself dispatched through `set_agents_spawn.py`; a `pi` session
started by hand is invisible to this lane. Both `--help`/the argparse epilog and `TIPS-USO.md` state that
limit, so a reader of the report output is not left assuming broader coverage than the tool actually has.

Rejected: skipping unattributed rows entirely without `--project`. That would hide real spend behind a flag
the user has to already know to pass, which is the opposite of what a quota-visibility feature is for.

### Scale / Data / Security decisions

No threat model changes here. The comparison this package's schema work touches
(`_normalize_ddl`/`_ddl_divergence`, from `007-P1`) is unchanged; this package only widens the table it
protects. `usage`/`cost` values arrive from the same trusted Pi subprocess `set_agents_spawn.py` already
guards (`GUARD_TOOLS_READONLY`, `SEC-A01`..`SEC-A05`) — nothing here accepts usage data from a new,
less-trusted source. `dispatches` gains no retention path: `store.py:_compact_in` compacts `events` only,
and this package does not add one for `dispatches` either. That is stated as an invariant, not an oversight —
`dispatches` already grows without bound today, and this package does not make that worse, but it also does
not fix it. Revisiting it is future work, not silently assumed away.

Read cost, measured (finding-verifier, RP-01): both `report()`'s new aggregates and `cost-report.py --project`
are `SEARCH dispatches USING INDEX dispatches_review (project_key=?)`, not a full table scan — a review-panel
finding that claimed otherwise was refuted by `EXPLAIN QUERY PLAN` against a real schema-6 store.
`dispatches_review` leads on `project_key` exactly as ADR-0008 D8 designed it, so read cost is bounded by rows
*per project*, not by table size. It does **not** cover the seven usage columns, so each pruned row still
costs a row lookup. YAGNI threshold to revisit with a covering index: >5 000 `dispatches` rows for a single
`project_key`, or a measured p90 of `--routing-report` above 50 ms — the same threshold precedent
ADR-0008 D8 sets for its own index-order tradeoff. `cost-report.py` **without** `--project` is a genuine full
scan, and correctly so: a deliberately global report has no key to prune on.

## Consecuencias

- Every spawn's token usage and cost are now durable, queryable per route and per project, instead of
  existing only inside a `print()` nothing reads.
- A future accounting need for cost has a real number to read instead of nothing, at the cost of one column
  this feature does not headline anywhere in its own reporting.
- Schema 6 databases require an explicit `--routing-migrate` from schema 4 or 5, same operator-driven
  doctrine as `007-P1`/ADR-0008 — no new automatic migration path exists.
- `docs/adr/0008-two-roots-portability.md` D8's migration banner text is now historical for the 4→5 step
  specifically; the live banner format is generalized here.
- The `pi` lane in `cost-report.py` is the only one of the four that can under-report by construction
  (unattributed rows without `--project`, no coverage of hand-run `pi` sessions) — a deliberately named limit,
  not a silent one.
