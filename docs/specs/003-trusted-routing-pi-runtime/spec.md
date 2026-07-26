# Trusted routing and Pi runtime recovery

## Contract

- Feature: `003-trusted-routing-pi-runtime`
- Version: `2.0.0`
- Status: **Approved**
- Approval source: user's original explicit instruction to implement the supplied P1R plan on `2026-07-24`, after
  spec-challenge corrections preserved intent.
- Approval date: `2026-07-24`
- Successor to: `002-adaptive-pi-orchestration` P1 routing work. The 002 record remains historical evidence.

## Problem

The experimental router cannot prove that a route was built from harness-observed facts, an authentic catalog, or
the identity of the writer whose work is being reviewed. Its mutable route identifiers and file-based execution
state also leave downgrade, impersonation, symlink, and crash-recovery risks. This prevents trusted Pi execution
and blocks the remaining Pi/runtime work.

## Target users

- SET-AGENTES maintainers who need a deterministic, auditable decision before dispatching work.
- Operators of the 28-role, four-runtime harness who need Pi to remain an opt-in runtime.
- Reviewers, auditors, and judges who need demonstrably independent review assignment.

## In scope

1. Replace the experimental routing implementation with a trusted routing-v2 runtime.
2. Accept a caller-provided `TaskRequest` only as intent and require harness-built `ObservedTaskFacts` for every
   route that can lead to dispatch. Caller claims never override observed role, tools, write state, risk/critical
   surface, selected runtime, authentication, or availability facts.
3. Build one immutable `CatalogSnapshot` inside the harness from the repository-owned
   `ai/catalogs/routes.v1.toml`, canonical `roles.tsv`, enabled/authenticated provider-model inventory, and
   routing metrics. No caller-supplied catalog, observed-auth map, or route identifier is authoritative.
4. Expose the public routing entry point
   `RoutingService.route(request, facts, review_of_run_id=None)`. This is a contract name and argument shape;
   implementation types and module location are **UNVERIFIED** pending architecture review.
5. Issue each static catalog route as a content-bound ID of the form `rt1_<16hex>`, derived from the SHA-256 digest
   of this exact canonical static tuple: `catalog_version`, `provider`, `model`, `family`, `effort`, sorted `tiers`,
   sorted `roles`, sorted `tools`, and `curated_priority`. Runtime is not an ID field and changing a compatible
   runtime does not change the route ID. A snapshot is invalid in full if two distinct canonical tuples have the
   same truncated ID; no route in that snapshot can dispatch.
6. Derive `ImplementationIdentity` only from a persisted writer dispatch selected by `review_of_run_id`. For a
   reviewer, auditor, or judge, the writer family is excluded and an authenticated different provider is preferred.
   Missing, non-writer, unknown, or forged review references fail closed.
7. Persist authorization and lifecycle evidence in standard-library SQLite under a single fixed, managed
   routing-v2 root. Persistent routing-v2 is supported only on POSIX local filesystems that provide Python
   `sqlite3`, reliable local locking, and Unix ownership/mode semantics. Windows and unreliable network
   filesystems return `ROUTING_UNAVAILABLE` without mutation; non-routing Windows behavior is unchanged. The root
   is not caller selectable; it and its ancestors must not traverse symlinks and must be private (`0700`
   directories, `0600` database/artifacts where applicable).
8. Maintain `meta`, `dispatches`, `events`, and `metric_rollups` as the durable routing-v2 record. `meta` contains
   an `installation_hmac_salt` generated once; it is reserved for keyed privacy identities and current/future schema
   compatibility, and is never emitted. The record
   supports authorization, partial-write recognition, one-time fallback authorization, terminal outcomes, retained
   p50/p90 metrics, and lifetime aggregate rollups without raw sensitive content.
9. Keep `--route-explain` explicitly simulated: it has no mutation capability and may explain a hypothetical route
   but never creates an authorization, dispatch, event, fallback, metric, or other mutable execution record.
10. Preserve the existing 28 roles, the three existing runtimes (OpenCode, Claude Code, Codex), schema-1
    compatibility, and the Sol/medium parent invariant. Pi remains opt-in.

## Business rules and invariants

- **Trust boundary:** `TaskRequest` is untrusted intent; `ObservedTaskFacts` and `CatalogSnapshot` are mandatory,
  harness-derived inputs for dispatch-capable routing. Missing facts is an error, not a permissive default.
- **ObservedTaskFacts completeness matrix:** facts are fresh for one route invocation (`facts_version` and
  `observed_at`) and contain every field below. A missing, stale, conflicting, or ambiguous required value disables
  execution for the feature/frontier with `execution_enabled=false` and `FACTS_INCOMPLETE`; a conflicting value
  also carries a conflict reason. Caller claims can add a more conservative constraint, but can never lower or
  replace an observed value.

  | Field(s) | Sole authoritative source | Downgrade rule |
  |---|---|---|
  | canonical role | harness dispatch role, validated against `roles.tsv` | caller role cannot replace it |
  | `operation`, `task_class` | harness classifier | caller classification cannot lower it |
  | read/write mode, `write_started` | harness tool/dispatch state | caller read-only/no-write claim cannot lower it |
  | risk, criticality, affected surfaces | harness classifier | caller claims are additive only |
  | required tools | capability/tool policy | caller omission cannot remove a tool |
  | context required, present, critical coverage | context-pack manifest | caller context claim cannot prove coverage |
  | `selected_runtime` | harness composition for this same route invocation | caller runtime cannot replace it; absent/stale/conflicting value is incomplete |
  | `facts_version`, `observed_at` | this route invocation's harness observation | absent/stale values are incomplete |
- **Catalog boundary:** catalog contents are derived only from the named repository and harness signals. A changing
  source, unknown role/model/provider, unauthenticated provider, disabled provider, or unavailable required tool
  makes the candidate ineligible with a reason code.
- **Catalog inventory and identity:** enabled providers are only those enabled by `models.toml` routing configuration.
  Authentication and exact-model evidence are keyed by `(runtime,provider)` and probed fresh per invocation, retaining
  only redacted status/exit information; credential files are never read. P1R permits exactly these pairs:
  `codex+openai-codex` through `codex login status`; `claude-code+anthropic` through `claude auth status --json`;
  `opencode+openai-codex` through `opencode auth list --pure` mapped to provider `openai` plus
  `opencode models openai --pure`; and `opencode+anthropic` through the corresponding mapped `anthropic`
  OpenCode auth/model commands. A nonzero, missing, timed-out, ambiguous probe or absent exact model makes that pair
  unavailable. Every other runtime-provider pair is unavailable in P1R. Codex authentication never proves OpenCode
  or Pi, and Claude authentication never proves OpenCode or Pi. Pi has no execution authentication adapter until
  paused P2, so it may be simulated/explained but has `execution_enabled=false`. Exact model inventory is the
  intersection of the catalog and canonical resolved role models in `models.toml`/`roles.tsv`. `CatalogSnapshot`
  holds an explicit, immutable provider-model-runtime mapping for runtime trust and audit. A static row may map only
  to audited compatible runtimes. Dispatch authorization identity is exactly
  `(route_id,runtime,provider,model,family,effort)`; any mismatch fails closed. Four-runtime fixtures cover
  OpenAI-only, Claude-only, provider outage, and all four runtimes; a Pi parent is rejected while an eligible Claude
  child remains eligible.
- **Static route identity:** a route ID binds exactly one static catalog row, not dynamic eligibility or runtime. Its
  canonical tuple contains exactly `catalog_version`, `provider`, `model`, `family`, `effort`, sorted `tiers`, sorted
  `roles`, sorted `tools`, and `curated_priority`; it is deterministic for equal tuple content and changes only when
  one of those fields changes. IDs are not caller accepted as authority. Distinct tuples with the same truncated
  `rt1_<16hex>` ID invalidate the entire snapshot, including a malicious hash-injection collision fixture.
- **Role class and run identity:** role class derives from `roles.tsv` duty/capability: writer has `code-rw`;
  reviewer/auditor has `review-ro` plus duty `audit`; judge has `review-ro` plus duty `judge`. A completed writer
  means terminal success of the actual selected or fallback route. The harness, not caller/task data, generates each
  `run_id` as `run1_` plus 32 lowercase CSPRNG hexadecimal characters. `run_id` is never task-derived,
  caller-provided, or persisted in events. Route selection is separate from the `authorize(run_id, decision)`
  boundary.
- **Review independence:** a review role can route only when `review_of_run_id` resolves to a completed/persisted
  writer dispatch and its provider and family are known. Candidates in that writer family are excluded; among the
  remaining eligible candidates, authenticated providers other than the writer provider rank ahead of same-provider
  alternatives. If none remains, fail closed.
- **Pi parent:** Pi simulation can observe an eligible GPT-5.6 Sol parent at medium effort, with `gpt-5.6` and
  `gpt-5.6-sol` resolving consistently. Pi has no P1R execution authentication adapter and therefore remains
  `execution_enabled=false` until paused P2; this does not change behavior of the other three runtimes.
- **Dispatch identity persistence:** for selected, fallback, and actual dispatch state, persistence records the
  corresponding immutable `route_id`, runtime, provider, model, family, and effort together. Identity is all-or-none:
  a record missing any member or combining members from different immutable identities fails closed;
  selected/fallback/actual effort is therefore durable and auditable.
- **One writer and one fallback:** only one writer dispatch is authorized for a run. Fallback eligibility is
  attempt-bound and durably closes before external primary invocation (`fallback_window_open=0` commits with
  `mark_dispatched`). A pre-dispatch restart may consume the one pre-authorized fallback only while durable state is
  still authorized, `fallback_window_open=1`, `partial=false`, and `terminal=false`. Any restart after
  `mark_dispatched` or external start, plus partial write, consumed fallback, terminal outcome, or
  terminal-persistence failure, prohibits fallback and automatic mutation.
- **Crash-safe lifecycle:** authorization, dispatch transition, partial-write marker, fallback consumption, and
  terminal outcome are recorded so a restart cannot silently duplicate a writer or fallback. Authorization uses
  `BEGIN IMMEDIATE`; the exact schema/transaction implementation is **UNVERIFIED** for architecture, but its
  observable exclusivity is contractual.
- **Privacy:** records contain only the minimum allowlisted routing and operational data needed for this feature;
  they never store task body, prompt, source code, paths supplied as task context, credentials, OAuth/token data,
  secrets, PII, provider output, or tracebacks. `installation_hmac_salt` is never emitted, even while current events
  omit task/run identity. Error envelopes are stable and redacted.
- **Retention:** one UTC `now` is captured per compaction transaction. Exactly the most recent 90 days are retained;
  older events are deleted, and the retained population is capped at 10,000 by the same deterministic boundary.
  Reports calculate exact nearest-rank p50/p90 for all retained events and separately for each route; an empty
  population yields `null`. Lifetime counters are incremented at insertion only. Compaction increments only
  `compacted_count`, then deletes; it never re-increments lifetime counters. Crash recovery must not miscount,
  duplicate, or resurrect an authorization.
- **Legacy safety:** the exact legacy universe under `STATE_DIR/routing` is `routing-decisions.json`,
  `routing-decisions.lock`, `routing-events.jsonl`, `routing-metadata.json`, `routing.salt`, `routing.lock`, and
  children matching strict regex `routing-events-[0-9]+-[0-9]+\.jsonl`. Detection uses `lstat` with no link
  following, opening, or reading. Any safe presence reports `LEGACY_ROUTING_STATE_PRESENT`; a symlink or unsafe
  candidate additionally reports `LEGACY_ROUTING_STATE_UNSAFE`, still without following or mutation. Legacy state is
  never imported, trusted, deleted, migrated, or read as content by this slice.
- **CLI behavior:** `--json` writes exactly one JSON document on stdout with schema version 2:
  `{schema_version:2, ok:boolean, command:string, data:object, warnings:[allowlisted], reason_codes:[allowlisted]}`.
  Warnings are allowed on exit `0`; diagnostics are redacted and go only to stderr in human mode. Exit `0` means
  success, `1` unavailable/unsafe, and `2` invalid input/config; invalid or conflicting arguments exit `2`. A failure
  never causes automatic mutation retry.

## Observable outcomes

- Equivalent trusted inputs yield the same eligible static route ID and explanation; tampering with request claims
  cannot lower the observed risk or alter catalog-backed eligibility.
- Two concurrent authorization attempts for the same run produce at most one writer authorization.
- A reviewer/auditor/judge cannot be assigned to its writer family and cannot claim a writer identity itself.
- Restarting after a partial write or a failed terminal-record attempt does not dispatch another writer/fallback.
- Operators can see redacted, machine-readable reason codes and lifecycle status without exposing sensitive task
  content or accepting legacy state as evidence.

## Explicit precedence

When more than one rule applies to the same request, the following order is authoritative:

1. Unsupported platform, unsafe storage/root, incomplete/conflicting facts, invalid/colliding catalog snapshot,
   invalid review reference, or invalid input/config fails closed.
2. Legacy-state presence or unsafe legacy links are warnings only; they do not affect routing-v2 eligibility or
   authorize any action.
3. Observed facts override conflicting caller intent; a conflict is an explicit safe/critical classification, never
   a downgrade. Additive caller constraints can only make a decision more restrictive.
4. Review-family exclusion removes candidates before provider preference and normal ranking.
5. Pi has no P1R execution adapter and remains disabled; an otherwise eligible Claude child is not disabled merely
   because its Pi parent is rejected; other runtimes remain eligible according to the trusted snapshot.
6. Durable lifecycle state after `mark_dispatched` (external start or restart, partial write, used fallback, terminal
   outcome, or terminal-persistence failure) blocks fallback/retry even if a fresh ranking would otherwise find an
   eligible route. The only exception is the explicitly authorized pre-dispatch restart state.

## First shippable slice

P1R is one cohesive implementation package. Its first shippable slice is a simulated trusted decision and durable
authorization path that proves request/fact separation, immutable catalog construction, static IDs, review identity,
and single-writer/fallback behavior. Pi lifecycle expansion and any P2/P3 work stay paused until P1R is accepted.

## Non-goals

- A gateway, remote database, queue, deployment, distributed coordination service, or hosted telemetry.
- Changing the 28-role roster, replacing the three existing runtimes, or dropping schema-1 compatibility.
- Making Pi the default runtime, changing the Sol/medium parent rule, enabling `max`, or enabling unbenchmarked
  providers.
- Importing, repairing, deleting, or rewriting legacy routing-v1 JSON.
- Persisting raw task data or offering an unredacted debug/traceback mode.
- Automatic recovery that mutates or redispatches after an authorization, partial-write, storage, or terminal-outcome
  failure.

## Assumptions and risks

| Item | Contract treatment |
|---|---|
| The named route catalog, role roster, inventory/auth signals, and metrics can be read by the harness. | **UNVERIFIED** data-source integration; architecture must prove the source carries each signal before implementation. |
| Filesystem permissions and SQLite locking are available on supported local installations. | Verify on supported OS/filesystem combinations; fail closed if the managed root cannot meet the contract. |
| A persisted dispatch can distinguish writer vs. review roles and carry provider/family identity. | **UNVERIFIED** schema mapping; architecture must prove it or introduce no dispatch path. |
| Compaction can calculate exact p50/p90 over all retained data without retaining prohibited content. | Verify with a non-sensitive production-shaped fixture, including boundary dates and 10,001 events. |
| Local tampering/corruption may occur. | Symlink/corruption/partial-write probes and redacted fail-closed envelopes are mandatory acceptance behavior. |

## Spec audit

### Detection and absence checks

| Requirement | Universe and absence behavior | Signal/source check |
|---|---|---|
| Missing/stale/conflicting observed facts | Every dispatch-capable `route` invocation; each matrix field, including `selected_runtime`, must be fresh for that invocation. An absent, stale, ambiguous, or conflicting required field disables execution with `FACTS_INCOMPLETE`; no dispatch record exists. | The named harness role/classifier/tool/context/composition sources, not request fields. **UNVERIFIED** until architecture maps all facts. |
| Unauthenticated/disabled candidates | Every provider/model declared in the internally built snapshot, not merely providers presented by a caller; absent, timed-out, unavailable, or ambiguous auth probe/inventory entry is ineligible. | `models.toml` enabled routing config plus redacted per-invocation adapter status. **UNVERIFIED** signal plumbing. |
| No independent reviewer | Every eligible candidate after writer-family exclusion; empty set fails closed. | Persisted writer dispatch selected by `review_of_run_id`. **UNVERIFIED** dispatch schema. |
| Partial-write / used fallback / terminal state | Every routing-v2 dispatch record; absent marker means only the transactionally recorded initial state, not a caller assertion. | SQLite lifecycle record. **UNVERIFIED** schema/transaction details. |
| Stale/excess events | All retained routing-v2 events in the fixed root; events older than exactly 90 days or beyond the retained cap are deleted, while corrupt/unreadable state fails closed rather than treated as empty. | SQLite events plus one transaction UTC `now`, timestamp/count. **UNVERIFIED** retention query. |
| Legacy state | The six exact named `STATE_DIR/routing` entries plus children matching `routing-events-[0-9]+-[0-9]+\.jsonl`; absence emits no warning, safe presence emits `LEGACY_ROUTING_STATE_PRESENT`, and unsafe candidates additionally emit `LEGACY_ROUTING_STATE_UNSAFE`, all without open/read/mutation. | `lstat` no-follow detector. **UNVERIFIED** historical-location confirmation. |

### Faithfulness checks

- A fixture that supplies only currently active rows would falsely prove that a missing provider is harmless. Scenarios
  require an enabled catalog entry with no observed authentication and expect exclusion.
- A fixture with synthetic writer metadata would falsely prove independent review. Scenarios require identity to come
  from an actual persisted writer dispatch referenced by ID.
- A fixture that lets a caller fill `write_started`, risk, context, or required tools would falsely prove the facts
  boundary. Scenarios remove or conflict each matrix field and require a non-executable outcome.
- A fixture that checks only valid truncated IDs would miss hash injection. Scenarios create two different canonical
  tuples with the same truncated ID and require the entire snapshot to be rejected.
- A fixture that puts runtime into the ID tuple would falsely make compatible-runtime changes appear as new routes.
  Scenarios vary only runtime and require a stable route ID plus a matching audited authorization identity.
- A fixture with a direct database path would miss ancestor-symlink attacks. Scenarios include a managed-root ancestor
  symlink and require failure before use.
- A fixture below both retention thresholds would falsely prove compaction. Scenarios cross both 10,000-record and
  90-day boundaries and verify rollups/percentiles after restart.

### Pairwise conflict pass

- Caller intent versus harness facts: facts win; conflict is never a downgrade.
- Legacy warning versus otherwise valid v2 route: report warning, keep v1 untrusted/unmodified, do not block a valid
  v2 simulation solely for its presence.
- Independent-provider preference versus family exclusion: exclusion wins; preference ranks only remaining candidates.
- Pi simulation/parent status versus execution eligibility: Pi remains execution-disabled in P1R; other trusted
  candidates can remain.
- Eligible fallback versus partial write, consumed fallback, terminal outcome, or storage failure: lifecycle block wins.
- Pre-dispatch restart versus post-`mark_dispatched` start/restart: only the former may consume fallback when durable
  state is authorized with `fallback_window_open=1`, `partial=false`, and `terminal=false`; the latter states close
  the window durably.
- Event compaction versus audit/lifecycle needs: compaction preserves required retained percentiles and lifetime
  rollups; it must never delete/alter active dispatch authorization evidence.

### What could not be verified

No architecture/schema inspection was performed for this product draft. The concrete fact-builder API, canonical
static-tuple fields, SQLite table columns/indexes, fixed root location, POSIX/network-filesystem detector,
adapter timeout policy, exact allowlist vocabulary, and existing full-verification command remain **UNVERIFIED**
implementation details. They must be validated without weakening the observable contract.
