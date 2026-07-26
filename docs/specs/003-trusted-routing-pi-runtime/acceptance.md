# Acceptance scenarios — trusted routing-v2

Contract: [spec.md](spec.md) version `2.0.0`.

## Scenario flow

```text
Operator / harness
  │ supplies TaskRequest + harness observes mandatory facts
  ▼
Trusted router ── builds immutable CatalogSnapshot ──► simulated explanation (never dispatches)
  │
  ├─ invalid/untrusted/legacy/corrupt state ──────────► redacted envelope + reason code, no mutation
  │
  └─ eligible route ──► durable single-writer authorization ──► dispatch lifecycle
                        │                                      │
                        │                                      ├─ partial write / terminal failure → no retry
                        │                                      └─ pre-write outage → one recorded fallback at most
                        ▼
                independent review from persisted writer identity
```

## BDD scenarios

### AC-01 — Trusted intent, facts, and catalog

**Given** a caller submits a `TaskRequest` and the harness independently builds complete `ObservedTaskFacts` and a
`CatalogSnapshot` from `ai/catalogs/routes.v1.toml`, `roles.tsv`, enabled/authenticated model inventory, and metrics  
**When** `RoutingService.route(request, facts, review_of_run_id=None)` evaluates a dispatch-capable request  
**Then** it uses the harness-built facts and snapshot only, returns an explainable eligible route or a redacted
fail-closed outcome, and accepts no caller catalog/auth/route-ID assertion as authority.

**Given** a caller claims lower risk, fewer tools, read-only work, or a different role than the harness observes  
**When** routing evaluates the conflict  
**Then** observed facts prevail, the request cannot be downgraded, and any unsafe ambiguity is explicit in the
reason codes.

**Given** facts are omitted, malformed, or unavailable for a dispatch-capable request  
**When** routing is requested  
**Then** it returns a stable redacted error, creates no authorization/dispatch/fallback record, and exits `2` for
invalid input/config or `1` for a diagnosed unavailable trusted source.

**Faithfulness:** the fixture includes an enabled provider absent from observed authentication inventory; it must be
excluded rather than silently treated as authenticated.

#### AC-01a — Per-field fact downgrade matrix

| Observed fact | Given | When | Then |
|---|---|---|---|
| canonical role | harness dispatch role is absent, not in `roles.tsv`, stale, ambiguous, or conflicts with caller role | a dispatch-capable route is requested | execution is disabled with `FACTS_INCOMPLETE` (and conflict reason where applicable); no authorization exists |
| `operation` / `task_class` | the harness classifier is absent, stale, ambiguous, or caller requests a lower class | the route is evaluated | caller classification cannot lower it; execution is disabled if the harness fact is not complete |
| read/write mode / `write_started` | harness tool/dispatch state is absent, stale, ambiguous, or caller says read-only/no write | the route is evaluated | no downgrade occurs; execution is disabled if state is incomplete |
| risk / criticality / affected surfaces | harness classifier is absent, stale, ambiguous, or caller claims less risk/surfaces | the route is evaluated | caller values are only additive; execution is disabled if observed values are incomplete |
| required tools | capability/tool policy is absent, stale, ambiguous, or caller omits a tool | the route is evaluated | the omission cannot remove the tool; execution is disabled if policy fact is incomplete |
| context required/present/critical coverage | context-pack manifest is absent, stale, ambiguous, or caller claims coverage | the route is evaluated | caller cannot prove coverage; execution is disabled if manifest facts are incomplete |
| `selected_runtime` | harness composition for this invocation is absent, stale, ambiguous, or conflicts with caller runtime | the route is evaluated | feature/frontier execution is disabled with `execution_enabled=false` and `FACTS_INCOMPLETE`; no authorization exists |
| `facts_version` / `observed_at` | either field is absent, not fresh for this invocation, or ambiguous | the route is evaluated | execution is disabled with `FACTS_INCOMPLETE`; no route is authorized |

**Faithfulness:** each row is exercised independently against production-shaped harness sources; a fixture that fills
all fields from the request would falsely pass and is rejected.

### AC-02 — Immutable content-bound routes and eligibility

**Given** equal canonical static catalog tuples containing exactly `catalog_version`, `provider`, `model`, `family`,
`effort`, sorted `tiers`, sorted `roles`, sorted `tools`, and `curated_priority`  
**When** routing runs twice, regardless of whether dynamic eligibility is currently true or false  
**Then** that row has the same static `rt1_<16hex>` ID derived from SHA-256 of those fields only; a currently eligible
decision explains its eligibility/ranking reason codes without redefining the ID.

**Given** any route-ID tuple field changes  
**When** routing runs against the changed snapshot  
**Then** the prior route ID/content binding is not accepted for dispatch and the new decision is independently
reproducible from the new snapshot.

**Given** a caller presents a previously seen route ID, a fabricated catalog row, an unknown role/model/provider,
an unauthenticated/disabled provider, or a candidate missing required tools/context  
**When** routing evaluates it  
**Then** only candidates from the internally built immutable snapshot are considered and each invalid candidate is
excluded with a reason code.

**Faithfulness:** mutate a route after its ID is produced and use a catalog containing both valid and invalid rows;
the test must prove binding and exclusion, not merely ID formatting.

#### AC-02a — Provider inventory, runtime rows, and collision safety

**Given** enabled providers come only from `models.toml` routing configuration and authentication/model evidence is
freshly probed per `(runtime,provider)` invocation  
**When** the pair is `codex+openai-codex`, `claude-code+anthropic`, `opencode+openai-codex`, or
`opencode+anthropic`  
**Then** P1R uses respectively `codex login status`; `claude auth status --json`; `opencode auth list --pure` mapped
to `openai` plus `opencode models openai --pure`; or mapped `anthropic` OpenCode auth/model equivalents. Only
redacted status/exit is retained and no credential file is read.

**Given** a permitted `(runtime,provider)` pair has a nonzero, missing, timed-out, ambiguous auth/model probe or an
absent exact model  
**When** that pair is evaluated  
**Then** the pair is unavailable.

**Given** any runtime-provider pair other than the four P1R pairs, or authentication evidence from Codex/Claude for
OpenCode or Pi  
**When** P1R evaluates execution eligibility  
**Then** the pair is unavailable; one runtime's authentication never proves another runtime's pair.

**Given** Pi is selected in P1R  
**When** routing evaluates execution and simulation  
**Then** Pi may be explained in simulation but has no execution auth adapter, remains `execution_enabled=false`, and
cannot be authorized until paused P2 work.

**Given** the immutable `CatalogSnapshot` uses the intersection of catalog models and canonical resolved role models
in `models.toml`/`roles.tsv`, plus an explicit immutable provider-model-runtime mapping for audited compatibility  
**When** the inventory is evaluated with OpenAI-only, Claude-only, provider-outage, and four-runtime fixtures  
**Then** only matching authenticated rows and audited compatible runtimes are eligible; a rejected Pi parent does
not reject an eligible Claude child.

**Given** two distinct canonical static tuples produce the same truncated `rt1_<16hex>` ID, including a hash-injection
fixture  
**When** the snapshot is built  
**Then** the complete snapshot is invalid, no row is eligible, and no dispatch can be authorized.

**Given** a static row has the same catalog tuple while dynamic authentication or tool/context eligibility changes  
**When** it is evaluated on two invocations  
**Then** its static route ID remains bound to that row and dynamic eligibility does not redefine the ID.

**Given** the same static row maps to two audited compatible runtimes  
**When** only its runtime changes  
**Then** the route ID remains unchanged, while authorization uses exactly
`(route_id,runtime,provider,model,family,effort)`; any value that does not match that immutable mapping fails closed.

### AC-03 — Writer identity and independent review

**Given** a completed persisted writer dispatch whose provider and family are recorded  
**When** a reviewer, auditor, or judge calls routing with that dispatch's `review_of_run_id`  
**Then** `ImplementationIdentity` is derived from that persisted dispatch alone, every candidate in the writer's
family is excluded, and an eligible authenticated provider different from the writer provider is preferred.

**Given** the review reference is absent, unknown, forged, belongs to a non-writer dispatch, or lacks trustworthy
provider/family identity  
**When** a reviewer, auditor, or judge is routed  
**Then** routing fails closed with a stable reason code and no review dispatch is authorized.

**Given** all candidates are in the writer family or no independent candidate is authenticated  
**When** review routing runs  
**Then** it fails closed rather than reusing the writer family.

**Faithfulness:** use a real persisted writer record in the fixture and verify that caller-supplied provider/family
values cannot change the result.

#### AC-03a — Role class, completed writer, and run boundary

**Given** `roles.tsv` declares capability/duty values  
**When** routing classifies a role  
**Then** writer means capability `code-rw`; reviewer/auditor means `review-ro` with duty `audit`; judge means
`review-ro` with duty `judge`; a caller cannot choose another class.

**Given** a review refers to a writer run  
**When** the persisted writer did not terminally succeed on the actual selected or fallback route  
**Then** it is not a completed writer and review routing fails closed without authorization.

**Given** a dispatch is selected, a fallback is pre-authorized, or an actual route is used  
**When** routing persists the dispatch lifecycle  
**Then** it persists each selected/fallback/actual immutable identity with route ID, runtime, provider, model, family,
and effort together; an incomplete or mixed identity fails closed, including missing selected/fallback/actual effort.

**Given** the harness begins a run  
**When** it generates a run ID before authorization  
**Then** it is `run1_` plus exactly 32 lowercase CSPRNG hexadecimal characters, never task-derived or
caller-provided, and no event persists that run ID; route selection completes before the separate
`authorize(run_id, decision)` boundary.

### AC-04 — Pi and compatibility guardrails

**Given** the trusted snapshot observes `gpt-5.6` or `gpt-5.6-sol` as an eligible Sol parent at medium effort and
Pi is explicitly selected  
**When** a Pi route is evaluated  
**Then** both approved aliases resolve consistently and Pi may be explained in simulation, but P1R execution remains
`execution_enabled=false` because Pi has no execution authentication adapter until paused P2.

**Given** Pi is selected but no eligible Sol/medium parent is observed  
**When** routing runs  
**Then** Pi execution remains disabled with a redacted explanation while eligible OpenCode, Claude Code, and Codex
routes keep their existing behavior.

**Given** valid schema-1 configuration and the canonical 28-role roster  
**When** routing-v2 is evaluated  
**Then** schema-1 compatibility, all 28 roles, and the three existing runtimes remain effective; Pi is not made the
default.

### AC-05 — Simulated explanation and CLI result contract

**Given** an operator invokes `--route-explain` with a valid supported task class  
**When** the command evaluates a simulated route  
**Then** it emits a versioned stable redacted envelope and explanation but creates no SQLite authorization,
dispatch, event, fallback, or metric mutation and never dispatches work.

**Given** an operator requests JSON output  
**When** route explanation or routing status/reporting returns  
**Then** stdout is exactly one JSON document and exactly matches
`{schema_version:2, ok:boolean, command:string, data:object, warnings:[allowlisted], reason_codes:[allowlisted]}`.

**Given** the command succeeds (warnings allowed), encounters a diagnosed unsafe/unavailable state, or receives
invalid/conflicting input/config  
**When** the operator invokes route explanation or routing status/reporting  
**Then** it exits `0`, `1`, or `2` respectively; diagnostics are redacted stderr only in human mode, and output
contains no traceback, prompt, source, credential, secret, PII, or raw task-context path.

**Given** any exact legacy candidate under `STATE_DIR/routing`: `routing-decisions.json`, `routing-decisions.lock`,
`routing-events.jsonl`, `routing-metadata.json`, `routing.salt`, `routing.lock`, or a child matching strict regex
`routing-events-[0-9]+-[0-9]+\.jsonl` is present, including an unsafe symlink  
**When** a routing-v2 status/reporting command runs  
**Then** `lstat` detects it without following, opening, or reading it; any safe presence returns
`LEGACY_ROUTING_STATE_PRESENT`, a symlink/unsafe candidate additionally returns `LEGACY_ROUTING_STATE_UNSAFE`, its
bytes remain unchanged, and it is neither imported nor routing authority.

**Given** an explain invocation has completed  
**When** the routing database and every routing-v2 file are compared byte-for-byte with their pre-invocation state  
**Then** they are unchanged, proving explanation had no mutation capability rather than merely no expected mutation.

### AC-06 — Managed SQLite root and tamper resistance

**Given** the host is Windows or a filesystem without reliable POSIX-local locking/ownership/mode semantics  
**When** persistent routing-v2 is requested  
**Then** it returns `ROUTING_UNAVAILABLE` with no mutation; existing non-routing Windows surfaces keep their
existing behavior.

**Given** routing-v2 persistence is initialized on a supported local installation  
**When** it creates or opens its durable state  
**Then** it uses standard `sqlite3` at the fixed harness-managed root, never accepts a caller-controlled path, has
private `0700` directories and `0600` database/artifact permissions where applicable, and makes `meta`,
`dispatches`, `events`, and `metric_rollups` available for the required lifecycle/reporting outcomes.

**Given** routing-v2 initializes `meta` for an installation  
**When** it is reopened or an operator requests any status, report, explain, or JSON envelope  
**Then** `installation_hmac_salt` was generated once and retained for keyed privacy identities/current-or-future
schema compatibility, but is never emitted; this remains true while current events omit task/run identity.

**Given** any managed-root component or ancestor is a symlink, permissions are unsafe, the database is corrupt, or
the storage root cannot be safely opened  
**When** routing or reporting needs persistent state  
**Then** it fails closed before using that location, returns a stable redacted envelope, emits no traceback, and
performs no automatic mutation retry.

**Faithfulness:** test an ancestor symlink and a corrupt database, not only a final-file symlink or an empty
directory.

### AC-07 — Atomic authorization, partial writes, and fallback

**Given** two concurrent routing attempts target the same writer run  
**When** they authorize dispatch  
**Then** transactionally exclusive `BEGIN IMMEDIATE` authorization records at most one writer dispatch; the other
attempt observes the durable state and does not dispatch.

**Given** an authorized writer fails strictly before `mark_dispatched` and has an eligible pre-authorized fallback  
**When** fallback authorization is requested  
**Then** exactly one fallback is recorded and may dispatch once; a second attempt cannot consume it again.

**Given** a restart occurs before `mark_dispatched` and durable state remains authorized,
`fallback_window_open=1`, `partial=false`, and `terminal=false`  
**When** fallback authorization is requested  
**Then** it may consume the single pre-authorized fallback.

**Given** `mark_dispatched` commits before the primary external invocation with `fallback_window_open=0`  
**When** the primary is dispatched, starts, restarts, partially writes, or its terminal outcome cannot be persisted  
**Then** fallback is unavailable and no automatic retry or mutation occurs.

**Given** a partial-write marker, consumed fallback, terminal outcome, failed authorization persistence, or failed
terminal-outcome persistence  
**When** restart or retry logic runs  
**Then** no automatic retry, redispatch, or new fallback is performed; the observable result is a safe checkpoint or
redacted terminal/unsafe outcome.

**Faithfulness:** interrupt the process between authorization, partial-write, fallback, and terminal transitions,
then reopen the database to prove no duplicate dispatch is authorized.

#### AC-07a — Crash matrix

| Crash/failure boundary | Observable result after restart |
|---|---|
| pre-`mark_dispatched` restart | one fallback may be consumed only when state is authorized, `fallback_window_open=1`, `partial=false`, and `terminal=false` |
| after `mark_dispatched` commit, before external invocation | fallback window is closed; no fallback or redispatch |
| after external invocation/start | no fallback or redispatch |
| after partial-write marker | no fallback or redispatch |
| after terminal result but terminal persistence fails | no fallback or redispatch; safe terminal/unsafe result |
| after fallback consumption or terminal persistence | no second fallback and no new writer |

### AC-08 — Event retention, metrics, and privacy

**Given** routing-v2 records lifecycle events containing secret-like text, prompt text, source-like content,
credentials, PII-like values, and task-context paths in the surrounding request  
**When** it persists events or emits reports/errors  
**Then** stored and emitted fields remain allowlisted routing/operational data only and expose none of those raw
values, no OAuth/token content, provider output, or traceback.

**Given** retained events exceed 10,000 records or span more than 90 days  
**When** compaction runs, including after an interrupted prior compaction  
**Then** it captures UTC now once for the transaction, deletes events older than exactly 90 days, reports exact
nearest-rank p50/p90 for all retained events and per route (or `null` for an empty population), increments only
`compacted_count` before delete, preserves insertion-time lifetime counters, and never duplicates, miscounts, or
resurrects a live authorization.

**Faithfulness:** use 10,001 events and boundary timestamps on both sides of 90 days, then simulate interruption
and reopen; a small in-memory fixture is insufficient.

### AC-09 — Full compatibility and verification gate

**Given** P1R implementation is complete  
**When** its focused routing-v2 tests, concurrency/crash/security/privacy/legacy probes, schema-1 compatibility
checks, existing-runtime regression tests, static compile/lint checks, and the repository's canonical full
verification command run  
**Then** all required gates pass without weakening prior tests, changing the role roster, changing the three existing
runtimes, or enabling Pi by default.

**And** P2/P3 implementation work remains paused until P1R receives independent package acceptance.

## Traceability

| Acceptance criteria | P1R work item | Planned proof |
|---|---|---|
| AC-01, AC-01a, AC-02, AC-02a, AC-04 | T-001 | fact-matrix, provider-inventory, collision, static-ID, compatibility fixtures |
| AC-03, AC-03a | T-002 | persisted terminal-writer, role-class, run-boundary, and independent-review probes |
| AC-06, AC-07, AC-07a | T-003 | platform/path/symlink, concurrency, and complete crash-matrix tests |
| AC-05, AC-08 | T-004 | exact CLI/envelope, explain immutability, legacy, privacy, retention/reporting tests |
| AC-09 and all criteria | T-005 | focused suite plus canonical full verification |
