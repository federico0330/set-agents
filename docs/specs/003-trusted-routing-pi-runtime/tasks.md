# P1R work items

All work belongs to one implementation package, **P1R**. P2/P3 are paused until P1R is independently accepted.

## T-001 — Trusted request/fact/catalog boundary

- **Acceptance:** AC-01, AC-01a, AC-02, AC-02a, AC-04.
- **Scope:** establish the untrusted request versus mandatory observed-facts boundary and create the internally
  built immutable catalog snapshot from the approved sources.
- **Local validation:** every fact-matrix absence/staleness/conflict; fresh disabled/unauthenticated/timeout/ambiguous
  provider probes; OpenAI-only, Claude-only, provider-outage, four-runtime fixtures; immutable row/static-ID collision;
  schema-1 and existing role/runtime/Pi-invariant regressions.
- **Ownership hint:** routing/domain and configuration/catalog integration.
- **Checkpoint:** architecture verifies that every data source actually carries its required signal; no inferred
  default is permitted for an absent fact.

## T-002 — Static route and independent review identity

- **Acceptance:** AC-02, AC-02a, AC-03, AC-03a.
- **Scope:** issue SHA-256 content-bound `rt1_<16hex>` routes and resolve `ImplementationIdentity` only from the
  persisted writer dispatch referenced by `review_of_run_id`.
- **Local validation:** same-static-content stability/change sensitivity despite dynamic eligibility; hash-injection
  collision invalidates snapshot; CSPRNG run-ID shape/no event persistence; missing/forged/non-terminal-writer
  references; role class, family exclusion, and different-authenticated-provider preference.
- **Ownership hint:** routing domain and dispatch identity contract.
- **Checkpoint:** prove provider and family jointly originate in the persisted writer dispatch, not request claims or
  caller catalog data.

## T-003 — Private SQLite dispatch lifecycle

- **Acceptance:** AC-06, AC-07, AC-07a.
- **Scope:** fixed managed root and routing-v2 SQLite record; atomic authorization, partial-write state, single-use
  fallback, terminal outcomes, and safe restart/corruption behavior.
- **Local validation:** `BEGIN IMMEDIATE` race; every pre/post-`mark_dispatched` crash boundary; POSIX versus
  Windows/unreliable-network unavailable behavior; root/final/ancestor symlink; permissions; corrupt database;
  duplicate fallback and retry suppression.
- **Ownership hint:** persistence/lifecycle module.
- **Checkpoint:** no caller path, no symlink traversal, and no automatic mutation retry after any uncertain durable
  state.

## T-004 — Observable non-mutating operations and retention

- **Acceptance:** AC-05, AC-08.
- **Scope:** simulated-only explain, stable redacted CLI envelopes/exit states, legacy warning, private event
  compaction, exact retained percentiles, and lifetime rollups.
- **Local validation:** explain byte-for-byte DB/no-file proof; exact schema-2 one-document stdout and CLI `0/1/2`;
  all five no-follow v1 paths/links remain untouched; secret/PII/traceback scans; nearest-rank overall/per-route/empty
  p50/p90 and 10,001/90-day/interrupted-compaction correctness.
- **Ownership hint:** operator CLI/reporting and metrics layer.
- **Checkpoint:** prove legacy is not read as authority and no output/stored record serializes prohibited content.

## T-005 — P1R evidence and acceptance handoff

- **Acceptance:** AC-09 and traceability for AC-01–AC-08.
- **Scope:** consolidate tests/evidence and run full required gates before independent package review.
- **Local validation:** all plan gate categories, repository compile/lint/type checks, canonical full verification,
  compatibility checks for existing runtimes and schema-1; repair
  `tests/test_harness.py::test_install_sh_dry_run_plans_missing_tools` with PATH isolated from host aliases; repair
  `test_models_config_emit_roundtrip` to prove schema-1 in-memory compatibility plus deterministic schema-2 emission
  rather than byte-equality to a schema-1 fixture.
- **Ownership hint:** integration/test evidence; review is performed by an independent read-only role.
- **Checkpoint:** no test is weakened; any failing trusted-source, crash, privacy, security, or compatibility probe
  blocks P1R and leaves P2/P3 paused.
