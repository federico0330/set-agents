---
name: system-design-decisions
description: Design-TIME architecture decision framework — when to add (or NOT add) queues, caches, CDN, read replicas, sharding; SQL vs NoSQL and CAP/BASE/normalization; security posture (least privilege, isolation, recovery) decided day one. Load when designing a new system, module, data model, or scaling/deploy strategy — BEFORE code. Complements the audit-time skills performance-scalability and db-integrity.
license: MIT
compatibility: opencode
metadata:
  enabled_for: architect, brainstormer, product-analyst
---

# System Design Decisions

## When to use
At design time — before code — when choosing a scaling strategy, a data store, a deployment topology, or a
security posture for a new system or module. This is the DECISION companion to the audit-time skills
`performance-scalability` (query efficiency of a diff) and `db-integrity` (transactions/concurrency of a diff):
those review code that already exists; this one decides what to build in the first place.

## Golden rule (governs every section below)
Understand the problem before choosing the tool. Progressive evolution, not complexity by default —
simplicity is the competitive advantage when scaling. **Add a scaling component only when the problem it
solves is real and measurable.** The default architecture is the boring one: client → stateless server →
one database. Every deviation costs money, deploy complexity, and cognitive load, and must be justified by a
concrete trigger — or explicitly deferred (YAGNI) with the measurable threshold that would activate it.

**The one exception — security is NOT deferred (see §3).** Least privilege, isolation, and recovery are
day-one decisions: by the time the "problem" is measurable, you are already breached.

## 1. Compute & scale — decide what to add, and what to defer
Default: stateless server (state lives in the DB or an object store, never in server memory), one relational
DB, synchronous request/response. Reach for each component ONLY on its trigger:

| Component | Add WHEN (measurable trigger) | Do NOT add just because… | Cost / deploy note |
|---|---|---|---|
| Vertical scale (more CPU/RAM) | Single node saturates but traffic still fits one box | You expect growth "someday" | Cheapest first move; buys time |
| Load balancer + horizontal nodes | One node can't hold peak, or you need HA/redundancy | It "feels more scalable" | Requires stateless servers first |
| Cache (Redis/in-mem) | A hot read is measurably expensive AND tolerant of slight staleness | The query is merely "important" | You now own an invalidation strategy (TTL or write-through) — the hard part |
| CDN (CloudFront/Cloudflare) | Static assets or globally distributed users with latency pain | The app is one-region and dynamic | Great ROI for static; near-zero for personalized dynamic |
| Message queue (SQS/etc.) | Traffic spikes to absorb, or long/slow work that must not block the user | You want "microservices vibes" | Adds async complexity, retries, dead-letter, ordering concerns |
| Read replica | Read-heavy load starves the primary | Writes are the bottleneck (replicas don't help writes) | Introduces replication lag → eventual consistency on reads |
| Sharding | A single DB genuinely can't hold the data/throughput | Before replicas + caching + vertical are exhausted | Highest-cost, hardest-to-reverse move; pick the shard key deliberately |

**Load balancer vs reverse proxy — they are different roles even when one box (e.g. Nginx) does both.** A
**load balancer** distributes incoming traffic across interchangeable nodes by their availability/health (scale
and HA). A **reverse proxy** routes by the *kind* of request — path, host, or service — to the right backend
(the front door of a microservice split, TLS termination, caching). Name which job you are actually adding; "put
Nginx in front" is not a decision until you say whether it is balancing load, routing services, or both.

**The API is a contract, not just code.** A public interface is a map others build against: its shape, verbs,
status codes, and cache semantics (see `error-handling-http`) are promises. Design it for the caller's ergonomics,
and treat versioning and backward compatibility as a deliberate decision — a breaking change to a shipped contract
is an ADR-worthy event, not an edit.

**Observability is the standing exception to "defer".** You cannot operate a distributed system blind, so
design the three pillars in from the start, cheaply: structured/canonical logs with metadata (user id,
server, request id); a few health metrics (latency, availability, error rate); and a trace id that travels
the full request path. This is not premature scaling — it is the instrument panel.

## 2. Data model — choose the store from the access pattern, not fashion
Understand the access pattern (read/write ratio, consistency needs, relationship shape) BEFORE naming a
product.

- **Relational (SQL)** — the default. Pick it when you need consistency, structured/related data, and real
  transactions (users, payments, orders, anything money/identity/audit).
- **Document (Mongo-like)** — schema still in flux, self-contained aggregates, early-stage product with
  evolving shape. Pay for it with weaker cross-document consistency.
- **Key-value (Redis/DynamoDB)** — extreme read/write speed on a known key; demands precise up-front access
  modeling (you design the keys, not ad-hoc queries).
- **Graph (Neo4j)** — the value IS the relationships (social graphs, recommendations, path-finding) and you
  need native traversal algorithms.

Cross-cutting decisions to record:
- **CAP** — a distributed store gives you two of {Consistency, Availability, Partition-tolerance}. Partitions
  happen, so you are really choosing C vs A under a partition. State which, and why it fits the domain.
- **ACID vs BASE** — money/identity/audit → ACID, no exceptions. High-availability, tolerant-of-slightly-
  stale data (feeds, counts, recommendations) → BASE (Basically Available, Soft state, Eventual consistency)
  is an acceptable, deliberate trade.
- **Normalization vs denormalization** — normalize (1NF atomic values, 2NF no partial deps, 3NF no transitive
  deps) by default in relational stores to kill duplication and keep writes consistent. Denormalize only as a
  deliberate read-speed optimization (the native NoSQL style), and only when you can name the read it serves
  and own the write-time duplication cost.
- **Polyglot persistence** — combining engines (SQL for critical transactions + a KV cache or NoSQL for
  massive reads, the Netflix/Uber pattern) is legitimate, but every extra engine is operational surface: add
  one only with a written justification, not by default.

## 3. Security by design — day one, NOT deferred
This section overrides the golden rule's "defer until measurable". Decide these up front:
- **Authentication vs authorization** — two distinct pillars, both day-one. **Authentication** proves *who you
  are* (login/identity); **authorization** decides *what you may do* once identified (roles, scopes,
  object-level access). Conflating them — or checking one and not the other — is how IDOR and privilege
  escalation happen. Decide the model for both; hand the enforcement proof to the audit skills below.
- **Least privilege** — every component, credential, and token gets the minimum scope it needs, nothing more.
  (This harness already lives it: MCP servers off by default, read-only agents, capability gates.)
- **Isolation / blast-radius containment** — separate concerns and environments so one compromised vector
  does not escalate to the whole system (separate credentials per boundary, prod vs non-prod separation,
  no shared god-tokens).
- **Session & token handling** — treat a live session/cookie as a credential (session hijacking needs no
  password); short-lived, scoped, revocable tokens; never in logs or client-visible state.
- **Recovery from day one** — isolated, tested, restorable backups designed before launch (ransomware and
  disk failure are when-not-if); a written incident path (who to notify, how to revoke).
- **Verification arm** — this skill DECIDES the posture; proving it holds belongs to the audit skills. Hand
  the concrete threats to `security-review`, `red-team-playbook`, `blue-team-hardening`, and `secrets-hygiene`
  rather than re-deriving them here.

## Required output
Every design that touches scale, data model, deploy, or security must produce:
1. A **"Scale / Data / Security decisions"** section in `design.md`.
2. **One ADR per material decision** in `docs/adr/NNNN-slug.md`, using the repo format
   (`Estado / Contexto / Opciones consideradas / Decisión / Consecuencias`). Each ADR must name the
   **measurable trigger** that justified adding a component — or, for a deferral, state
   **"not yet — YAGNI"** plus the threshold that would activate it — and the cost/deploy consequence of the
   choice. A decision to keep it simple is itself an ADR-worthy decision.

Use `brainstorming` for the options / tradeoff / risk / cost / reversibility mechanics; this skill supplies
the systems criteria that feed it.

## Verification ideas
- For each added component, is there a written measurable trigger — or is it complexity by default?
- For each deferred component, is the activation threshold stated, so it is a conscious choice and not an
  oversight?
- Does the chosen store match the stated access pattern, and is the C-vs-A / ACID-vs-BASE trade explicit?
- Are the four security day-one items (least privilege, isolation, session/token, recovery) each addressed —
  not deferred?
- Could a reader six months from now see WHY each piece exists from the ADRs alone?
