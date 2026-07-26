# P1R implementation plan

## Status and boundary

This is the pre-approval plan for feature `003-trusted-routing-pi-runtime`, contract `2.0.0`. It is one cohesive
implementation package named **P1R**. P2 and P3 remain paused until independent P1R package acceptance. No
gateway, remote database, queue, deployment, or external service is introduced.

## Sequence and dependencies

1. Establish the complete observed-facts matrix and immutable catalog construction before any dispatch path.
2. Bind static routes and review identity to persisted trusted data before candidate selection is exposed.
3. Add fixed-root SQLite lifecycle storage before enabling writer/fallback execution.
4. Add non-mutating explanation, reporting, legacy detection, redaction, retention, and metric rollups over the
same lifecycle record.
5. Run the complete compatibility, concurrency, crash, security, privacy, legacy, and repository verification
evidence set; only then route the package for independent review.

## Cohesive work items (P1R only)

| ID | Work item | Depends on | Acceptance | Local validation | Risk checkpoint |
|---|---|---|---|---|---|
| T-001 | Replace experimental inputs with complete per-field harness `ObservedTaskFacts`; internally build immutable runtime-bearing `CatalogSnapshot` from routes catalog, roles roster, `models.toml` enabled/auth/model intersection, and metrics; preserve schema-1, 28 roles, 3 existing runtimes, Sol/medium, and Pi opt-in. | Approved contract | AC-01, AC-01a, AC-02, AC-02a, AC-04 | field-matrix downgrade, fresh-probe/four-runtime, static-ID/collision, schema compatibility fixtures | Prove every named source signal and that missing/stale/conflicting facts disable execution. |
| T-002 | Implement static `rt1_<16hex>` row binding (not dynamic eligibility), CSPRNG run IDs, separate authorization boundary, and persisted-writer `ImplementationIdentity`; enforce role class and family exclusion/different-provider preference. | T-001 | AC-02, AC-02a, AC-03, AC-03a | collision/tamper, role-class/run-ID, forged-reference, provider/family independence probes | Confirm identity comes only from a terminally successful persisted selected/fallback writer. |
| T-003 | Create fixed private SQLite routing-v2 storage on supported POSIX local filesystems and the atomic lifecycle for `BEGIN IMMEDIATE`, authorization, `mark_dispatched` fallback closure, partial writes, terminal outcomes, restart and corruption handling. | T-001, T-002 | AC-06, AC-07, AC-07a | platform/path/permission/symlink, concurrent authorization, full crash matrix, duplicate-fallback tests | Unsupported Windows/network filesystems return unavailable without mutation; no post-dispatch fallback. |
| T-004 | Add capability-less simulated `--route-explain`, exact schema-2 JSON envelope/exit mapping, no-follow legacy detection, and 90-day/10k compaction with nearest-rank retained metrics and insertion-time lifetime rollups. | T-003 | AC-05, AC-08 | byte-for-byte explain proof; CLI 0/1/2; legacy links untouched; per-route/empty percentile and interrupted-compaction tests | Verify allowlists, no legacy content read, and no compaction counter miscount. |
| T-005 | Integrate and freeze P1R evidence: focused suite, schema/runtime regressions, concurrency/crash/security/privacy/legacy tests, the two hermetic repair regressions below, compile/lint, and canonical full verification; prepare independent package review. | T-001–T-004 | AC-09 and all prior ACs | exact approved gate commands and saved evidence | Any failed full gate, unverified trusted source, or behavior conflict routes to repair/challenge; P2/P3 stay paused. |

## Required gates

The implementation must define the exact repository commands during package planning without substituting weaker
checks. Required evidence categories are:

1. Focused routing-v2 unit/integration tests covering all ACs.
2. Deterministic catalog, route-ID, schema-1, 28-role, 3-runtime, Sol/medium, and Pi-opt-in regression checks.
3. Concurrency, crash/restart, corrupt-store, permission, caller-path, final-file and ancestor-symlink probes.
4. Review-identity, fallback single-use, partial-write, simulated-explain/no-mutation, CLI exit `0/1/2`, redaction,
   legacy-state, and 10,000/90-day retention/rollup probes.
5. Static compile/lint/type checks used by the repository and its canonical full verification command.
6. Independent package review against this contract; package acceptance is required before P2/P3 resume.
7. `tests/test_harness.py::test_install_sh_dry_run_plans_missing_tools` with `PATH` isolated from host aliases.
8. `test_models_config_emit_roundtrip`, proving schema-1 in-memory compatibility and deterministic schema-2
   emission rather than byte equality to a schema-1 fixture.

## Human decision triggers

- The actual catalog/inventory/metrics sources cannot prove the signals this contract reads.
- A compatibility decision would change any of the 28 roles, existing runtime behavior, schema-1 behavior, or the
  Sol/medium and Pi opt-in invariants.
- A proposed recovery path would retry mutation after partial write, failed durable authorization, or uncertain
  terminal outcome.
- A finding would require importing/mutating legacy state, retaining prohibited data, or adding an out-of-scope
  remote/deployed component.

## Risks

- Local filesystem/SQLite differences can make permissions or locking unsafe; fail closed and test supported
  environments.
- Existing persisted dispatch data may not contain the required trusted identity; verify before permitting review
  dispatch.
- Retention logic can corrupt counts on interruption; use restart probes at every lifecycle boundary.
- The old implementation's state can be present in user installations; it must remain non-authoritative and
  untouched.
