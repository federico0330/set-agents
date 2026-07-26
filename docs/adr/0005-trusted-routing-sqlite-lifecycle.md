# ADR 0005 — Trusted routing lifecycle in local SQLite

## Estado

Accepted on 2026-07-24.

Supersedes only ADR-0004's JSON/JSONL routing-journal choice and its threshold for introducing a transactional
store. ADR-0004's Pi, routing-policy, permission, rollout, and topology decisions remain accepted historical
context.

## Contexto

P1R must authorize at most one writer, make a partial-write marker sticky, consume a pre-authorized fallback at
most once, and persist one terminal outcome across process crashes and concurrent attempts. The existing
JSON/JSONL-plus-sidecar approach repeatedly failed to make decision state and telemetry crash-safe as one atomic
unit. That repeated failure crosses ADR-0004's YAGNI threshold for a durable transactional store even on one
local host.

This choice is based on SET-AGENTES lifecycle requirements, not copied from Gentle-AI. The Gentle-AI installer
uses `state.json`; SQLite in that ecosystem belongs to the separate Engram memory system. Neither is evidence
that Gentle-AI supplies a routing transaction model suitable for SET-AGENTES.

## Opciones consideradas

1. **Repair JSON/JSONL with locks, atomic renames, and sidecars.** Keeps human-readable files and minimal
   dependencies, but cannot atomically coordinate authorization, sticky flags, fallback consumption, terminal
   state, events, and compaction without rebuilding a fragile database protocol.
2. **Use Python standard-library `sqlite3` at one fixed private root.** Supplies local ACID transactions,
   uniqueness constraints, ordered percentile queries, crash recovery, and one-file schema evolution without a
   new service or package dependency.
3. **Use a remote database or routing service.** Could coordinate multiple hosts, but adds credentials, network
   availability, deployment, recovery, privacy, and operational cost that P1R does not require.

## Decisión

Choose option 2 for supported POSIX local filesystems only. The only production state root is the
harness-managed state base plus `routing-v2` (`~/.local/state/set-agentes/routing-v2`), never a request,
environment, or caller-selected path. Production routing-v2 ignores `SET_AGENTS_STATE`; tests relocate the root
only through explicit composition injection. Windows, unreliable/unknown network filesystems, absent `sqlite3`,
or missing Unix ownership/mode/locking semantics return `ROUTING_UNAVAILABLE` without mutation.

The root is private `0700`; `routing.db`, `routing.db-wal`, and `routing.db-shm` are private `0600`. Opening walks
ancestors/components with no-follow `lstat` and descriptor-relative checks, records root/DB identities, and
revalidates root, DB, WAL, and SHM identities and modes after SQLite connects and configures sidecars. Symlinks,
unsafe ownership/modes/types, detected replacement, corruption, schema mismatch, unsupported storage, and lock
failure fail closed.

Python `sqlite3` must open by pathname, so these checks prevent pre-existing links and detect replacement but
cannot guarantee safety against a malicious process with the same UID intentionally racing that pathname during
open. Such a process is outside this feature's threat model because it already controls the user's harness state;
detected identity changes and accidental or different-UID tampering remain fail-closed.

The normalized schema contains `meta`, `dispatches`, `events`, and `metric_rollups`.
`meta` stores `schema_version` and a private installation-local CSPRNG `installation_hmac_salt`, reserved for
keyed privacy identities and schema compatibility even though current events omit task/run identity. It is never
emitted, caller-supplied, or derived from the legacy salt; legacy salt is never read or migrated. `dispatches` is
never compacted and is the authoritative single-writer/review-identity/lifecycle record.

Static `route_id` binds exactly `catalog_version`, `provider`, `model`, `family`, `effort`, sorted `tiers`, sorted
`roles`, sorted `tools`, and `curated_priority`; runtime is not hashed and a runtime-only change does not change
`route_id`.
`CatalogSnapshot` separately owns the immutable compatibility mapping
`(route_id,runtime,provider,model,family,effort)`, and authorization fails closed unless its complete dispatch
identity matches that mapping. `selected_runtime` is a mandatory harness fact; missing or conflicting runtime
disables execution, and only harness dispatch composition may source it. Auth observations are keyed by the exact
`(runtime,provider)` pair and use only the closed
P1R argv mapping: Codex/OpenAI uses `codex login status`; Claude Code/Anthropic uses
`claude auth status --json`; OpenCode/OpenAI uses `opencode auth list --pure` mapped to `openai` plus
`opencode models openai --pure`; and OpenCode/Anthropic uses the same auth listing mapped to `anthropic` plus
`opencode models anthropic --pure`. Results are bounded/redacted and no credential file is read. Auth never
crosses runtime boundaries; every other pair is unavailable, and Pi remains simulation-only/non-executable until
P2 supplies its adapter.

`dispatches` stores immutable selected and optional fallback
`(route_id,runtime,provider,model,family,effort)` identities plus the actual dispatched identity with the same
complete tuple. Terminal-success review identity therefore reflects the route/runtime/effort that truly ran.
`events` contains only allowlisted, non-identifying operational fields. `metric_rollups` preserves lifetime
counters, histograms, exclusions, and fallback outcomes.

Every authorization, primary-dispatch marker, partial-write marker, fallback consumption, and terminal outcome
uses one `BEGIN IMMEDIATE` unit with matching event/rollup evidence. Authorization sets
`fallback_window_open=1`. Primary `mark_dispatched` atomically closes it before any external primary invocation.
Fallback consumption is allowed only while the row remains authorized/open, partial-write is false, no terminal
exists, and the fallback is unused; consumption closes the window and stores the actual fallback identity before
any external fallback invocation. A restart before dispatch may consume fallback only when that durable
authorized/open/non-partial/non-terminal state still holds. After `mark_dispatched`, any possible external start,
partial/consumed/terminal state, or failed terminal commit, the attempt cannot consume fallback or redispatch.

Connections use WAL, `synchronous=FULL`, foreign keys, and `busy_timeout=0`; mutation conflicts fail immediately
and are never automatically retried. Every event insertion increments all applicable lifetime/histogram,
exclusion, and fallback counters exactly once. Retention captures one UTC cutoff in one transaction, keeps the
newest 90-day population capped at 10,000, increments only `compacted_count` grouped by the exact deletion key,
deletes those exact events, and never re-increments lifetime/exclusion/fallback counters or touches dispatches.
Reports preserve exact nearest-rank retained p50/p90 for all events and each route; empty populations are null.

Legacy detection enumerates `STATE_DIR/routing` and recognizes only `routing-decisions.json`,
`routing-decisions.lock`, `routing-events.jsonl`, `routing-metadata.json`, `routing.salt`, `routing.lock`, and
strict rotated names matching `^routing-events-[0-9]+-[0-9]+\.jsonl$`. Each match is inspected with no-follow
`lstat` and is never opened, read, or mutated. A safe regular file emits `LEGACY_ROUTING_STATE_PRESENT`; a symlink
or unsafe type also emits `LEGACY_ROUTING_STATE_UNSAFE`. No legacy object is imported, trusted, rewritten,
deleted, or dual-written.

### Scale / Data / Security decisions

- **Data store:** local relational SQLite is justified now by the measured design failure of JSON/sidecars to
  provide the required atomic lifecycle. No document, key-value, graph, or vector store is needed. A remote
  relational store requires a separately approved multi-host coordination need or measured local SQLite
  throughput/locking failure against an explicit service target. Unsupported platform/filesystem combinations
  fail closed rather than falling back to JSON.
- **API Gateway:** not yet — YAGNI. Add one only if multiple remotely exposed backend services or client types
  require centralized authentication, rate limiting, routing, and observability.
- **Deploy platform:** none; this is a local installed runtime, so Vercel/PaaS, VPS/IaaS, and managed hosting are
  all out of scope. Reconsider only after an approved remote control plane, with measured runtime/connection
  requirements and named operational ownership.
- **Queue/cache/CDN/replica/shard:** not yet — YAGNI. A queue requires measured asynchronous backpressure; a cache
  requires a profiled hot read plus safe invalidation; a CDN requires a remote static surface with geographic
  latency; replicas require primary read saturation; sharding requires proven single-database capacity
  exhaustion.
- **Security:** least privilege and isolation are enforced by a fixed private root, caller/environment-independent
  production routing path, no-follow component checks, and before/after identity validation. Raw credentials,
  tokens, prompts, content, task identity, and provider output are never persisted. Corrupt, replaced, or
  ambiguous state fails closed; recovery requires an integrity-checked SQLite-consistent backup, never automatic
  recreation or replay. Same-UID malicious pathname racing is explicitly outside the local threat model.
  R3 amendment (2026-07-24): the same-UID exclusion extends to in-process code; "caller" means untrusted intent,
  not untrusted code. In-process non-forgeable permits, `statfs` filesystem classification, full
  descriptor-relative traversal, and per-authorization re-probing are approved exceptions (decision
  `r3-threat-model-amendment`); the enforceable guarantee is sealed production composition plus fail-closed
  behavior against accidents and non-UID attackers.

## Consecuencias

- Routing lifecycle and telemetry changes that must agree are one atomic local unit.
- SQLite locking provides exclusivity for concurrent local processes without claiming distributed coordination.
- Persistent routing-v2 is unavailable on Windows and unreliable/unknown network filesystems; other harness
  behavior remains unchanged.
- The schema, permissions, integrity checks, retention, and recovery path become security-critical compatibility
  contracts and require crash/concurrency/tamper tests.
- WAL sidecars are part of the private state boundary and backup procedure.
- Exact p50/p90 is available only for retained event samples; lifetime reports preserve counters and histograms,
  not invented exact percentiles after raw samples are compacted.
- Closing the fallback window before invocation may sacrifice an attempt after a crash between commit and process
  start; this deliberate availability cost prevents duplicate primary/fallback mutation.
- A corrupt or unavailable database can stop routing until an operator restores safe state. Availability is
  deliberately subordinate to preventing duplicate or forged dispatch.
- No gateway, queue, external database, remote service, or deployment is introduced.
