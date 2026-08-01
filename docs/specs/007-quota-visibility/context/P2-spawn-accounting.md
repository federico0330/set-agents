# Context pack — 007-P2 `spawn-accounting`

Delimited by structure, not by a file list: the surface is **the path a token count would have to travel and
does not** — from `set_agents_spawn.py:spawn`'s return value, through the `--route-terminal` CLI edge, into
`dispatches`, and back out through `--routing-report` and `cost-report.py`. Plus the schema migration that
makes room for it, and the two records that describe the result.

## The defect, stated exactly

The harness already receives the number. `set_agents_spawn.py:spawn` returns
`("success", {"model": …, "usage": {…}})`; its only production caller, `route_and_spawn`, unpacks that
`detail` and then closes the run with `--route-terminal … --latency-ms N` **without passing it**. The object
survives only as far as a `print(json.dumps(result))` that nothing consumes. `grep usage ai/scripts/set_agents_app.py`
returns nothing.

So the harness records the route, the model and the latency of every delegation, and discards the one
dimension that is the binding constraint. The wire itself is one argument; everything that argument touches
on landing is the package.

## What the live evidence actually shows

The one recorded sample (`docs/specs/004-adaptive-dispatch/evidence/P3-implementation.md:149`) is
`{"input": 3221, "output": 6, "totalTokens": 3227, "cost": {"total": 0.003257}}`. **No cache keys, no
reasoning key.** The test double is sparser still (`{"cost": {"total": 0.001}}`), and several tests inject
`{}` outright. `spawn` itself coalesces with `usage or {}`, so an empty object is the ordinary case, not an
anomaly.

`set_agents_spawn.py` is **pi-only** — `route_and_spawn` pins `selected_runtime: "pi"` and builds
`pi_pinned_argv`. No other runtime's usage ever reaches this path; the other three lanes are scraped after the
fact from their own vendor stores by `cost-report.py`, which is a separate program. The column vocabulary is
borrowed from `cost-report.py:FIELDS` for comparability in the report, not because those lanes feed the store.

## Invariants the package must not break

- **`NULL` means "not reported"; `0` means "reported as zero".** AC-08 justifies the cache columns as making
  the "Pi reuses no cache across spawns" thesis falsifiable rather than a zero written in advance. That only
  holds if an absent dimension stays `NULL`. Coercing absent to `0` fabricates precisely the evidence the
  thesis needs, while satisfying the criterion's letter.
- **Column placement is load-bearing and fails only in a live run.** `ALTER TABLE ADD COLUMN` inserts after
  the last column definition and before the first table constraint, so the new columns must be declared in
  `_create_schema` immediately after `PROJECT_KEY_COLUMN`, in the same order as their `ALTER`s. Verified in
  both directions: that placement yields a normalized DDL byte-equal to canonical, any other does not. Every
  test that creates a database and reopens it stays green either way — this is the failure mode 007-P1 exists
  to have closed, one package earlier.
- **`store.py:_authorize_issued` writes `dispatches` positionally**, `INSERT INTO dispatches VALUES(?…)` with
  no column list. Widening the table without widening that tuple breaks every authorization. It fails loudly,
  but nothing in the contract points at it.
- **Closing the run is the invariant; the discard is recorded, never silent.** A malformed `--usage` is
  refused at the CLI, where nothing is at stake yet. An unusable one never aborts the close — it lands as
  `usage_status='invalid'` with the row written. `absent` is reserved for a usage that never existed.
- **The two edges reject different things.** Unparseable (not JSON, not an object) at the CLI; untrustworthy
  (types, signs, ranges, the `totalTokens` mismatch) in the store. A closed key whitelist like
  `cmd_route_decide`'s would contradict AC-12, which requires accepting shapes we cannot map.
- **Round-half-up is defined on the provider's text, not on its binary approximation.** Half a micro-dollar
  written as `0.0000005` is `4.999…e-7` once parsed as a float, and rounds the wrong way. `parse_float=Decimal`
  is what makes AC-12 implementable at all.
- **`_lifecycle_command` does not catch `RuntimeError`.** `feature-state.py:parse_json_object` raises
  `StateError`, a `RuntimeError` subclass; copying it would leak a traceback and break the one-JSON-line
  contract that `tests/test_routing.py` pins alongside the exit code.
- **Routing modes are total.** `--usage` must be added to `_routing_args` *and* to `modifier_misuse`. Missing
  the first makes the flag unusable; missing the second lets it ride silently alongside `--route-decide`.
- **The report's two halves have different scopes and different retention.** Percentiles come from `events`,
  which has no `project_key` and is machine-global and compacted at 90 days / 10 000 rows. Tokens come from
  `dispatches`, which is per-project and has no retention path at all. Their route key sets are not subsets of
  each other — a run closed without `--latency-ms` contributes tokens and no percentile.
- **A reporter does not import the store.** `store.py.__init__` derives home from `pwd.getpwuid` deliberately,
  so the environment cannot redirect where durable authorizations live (ADR-0005). `cost-report.py` reads the
  routing database through its own `--home` seam and recomputes the project key locally; a test pins that the
  duplicated derivation agrees with `project_key_for`.
- **The reserved-hole guard survives.** `tests/test_harness.py` ends its ADR-index test with
  `assertNotIn("0010", linked)` — the guard 009-P3 shipped so a reservation note could not be satisfied by a
  phantom row. Writing ADR-0010 makes it fail by design. It is generalized to parse the note, not deleted.

## Out of scope, recorded rather than fixed

`open_runs()` does not filter by `project_key` while `recent_writers()` does — a pre-existing cross-project
listing, not this package's business. `terminal()` still has no production callers and is not removed.
`dispatches` grows without bound; AC-17 states that as an invariant with its cost rather than adding
retention. `_canonical_ddl` is a class attribute that is never invalidated; harmless with one `SCHEMA` per
process and worth revisiting only if that stops being true. Feeding token data back into the routing decision
is an explicit non-goal of the whole feature: this makes cost visible, never decisive.
