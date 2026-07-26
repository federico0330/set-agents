# Feature 004 — adaptive-dispatch, contract 1.1.0

Status: SPEC_DRAFT v2 (post spec-challenge rework; pending re-challenge delta and user approval).
Depends on: feature 003 P1R (trusted routing-v2) ACCEPTED. Consumes 003's contract with TWO explicit,
user-approved amendments (below). Inherits the R3-amended threat model (in-process/same-UID adversary out of
scope; "caller" = untrusted intent) and the still-accepted ADR-0004 invariants (routing owned by
SET-AGENTES; Pi supplies a provider runtime; deterministic catalog-bound selection; no remote router).

## Goal

Every orchestrator delegation can consume a routing decision — task descriptor in, `(model, effort,
runtime, tier)` out of the curated catalog — and writer dispatches complete the durable lifecycle
(`authorize → mark_dispatched → terminal`) that P1R built. Two consumption lanes: named tier variants on
OpenCode (works today), and per-spawn model selection on Pi via an extension over its SDK (P3, gated by a
feasibility spike).

## Approved contract amendments to 003 (user decisions 2026-07-26)

- **AM-1 (hybrid fact derivation).** The fact matrix splits per field: mechanically derived fields come
  from harness sources (role → roles.tsv roster; read_write + required_tools → the role's
  capability/duty; criticality → `task_class ∈ CRITICAL`; context flags → existence and freshness of the
  package context-pack file recorded in feature state; selected_runtime → composition), while the
  orchestrator descriptor supplies `task_class` and MAY ONLY RAISE the derived risk (base risk derives
  from task_class: CRITICAL ⇒ high, incident ⇒ high, else low; descriptor risk below the derived base is
  ignored, never honored). This is a bounded relaxation of 003's "caller classification cannot lower it"
  — recorded via log-decision and referenced by ADR-0006.
- **AM-2 (probe cache + fresh-selected).** Pair probes may be cached (TTL 300s) ONLY for candidate
  filtering; before any writer authorization the SELECTED pair (and fallback pair, if different) is
  re-probed fresh. A stale cache can therefore only affect which candidates are considered, never
  authorize against an unverified pair. Requires ADR-0006 (cache key, root, atomicity) BEFORE P1
  implementation. This amends 003's "probed fresh per invocation" and ADR-0005's cache deferral.

## Non-goals

- No model-based or remote router. Selection stays pure and catalog-bound.
- No Claude Code / Codex dynamic lanes (their static roles.tsv bindings stay). The daily driver for the
  adaptive lanes is OpenCode (P2) and Pi (P3).
- No `opencode/*` (Zen/Go) providers in the routed catalog in THIS feature — cheap tier uses already
  audited providers only (gpt-5.4-mini / gpt-5.6-luna / haiku). Adding a third audited provider is a
  follow-up feature (user decision B5).
- No benchmark-driven auto-tuning (telemetry report + manual curation only).
- No automatic migration of routing DBs, ever: the schema-2 DB created during 003 AND any schema-3 DB are
  invalidated by this feature's bump to SCHEMA=4 (new `abandoned` lifecycle state); the operator deletes
  `~/.local/state/set-agentes/routing-v2` once, documented in the rollout notes. Fail-closed, no repair.
- Roles outside `code-rw` and `review-ro/audit|judge` classes (docs-rw, factory-rw, memory-rw, gate-ro,
  run-ro, release, coord-ro) keep their static models: they are NOT routed in this feature.

## Tier model (closes B4)

- Closed ordered vocabulary, reusing 002's approved names: `fast < balanced < frontier`.
- Each catalog route row declares EXACTLY ONE tier (schema: `tier = "fast"`, replacing the `tiers` list;
  `build_snapshot` rejects unknown values or lists). Static-ID binding encodes the tier as a ONE-ELEMENT
  group in the existing canonical tuple shape — the 003 ID contract's encoding is unchanged, no further
  amendment. `catalog_version` bumps to 2 (row schema changed); `build_snapshot` validates and hashes 2.
- Required-tier resolution (pure function over validated facts): `task_class ∈ CRITICAL` or combined risk
  `high` ⇒ `frontier`; `task_class ∈ {mechanical, documentation, inspection}` AND risk `low` ⇒ `fast`;
  otherwise ⇒ `balanced`.
- Selection order replaces the flat priority sort: candidates are filtered to tier ≥ required, then sorted
  by (lowest tier first, curated_priority, route_id). 003's precedence is otherwise unchanged: hard
  exclusions (identity/auth/role/tools/context) filter BEFORE tier ordering; reviewer family exclusion and
  different-provider preference keep their 003 semantics on the surviving candidates.
- Consequence (documented, accepted): repopulating the catalog changes all `route_id`s; historical
  telemetry keys remain in `--routing-report` as dead route IDs — expected, not a defect. Effort values in
  catalog rows must belong to `[catalog].codex_effort` (openai-codex) or be `medium` (anthropic), and
  `xhigh` rows are rejected while `[routing].xhigh_benchmarked = false` (002 invariant, now validated).

## Packages

- **P1-dispatch-core** — ADR-0006 + tiered catalog + tier-aware selection + dispatch CLI + probe cache.
- **P2-opencode-lane** — generated tier variants + orchestrator doctrine consuming decisions.
- **P3-pi-lane** — GATED by spike T-300; managed Pi + spawn extension + pi pairs + child guards.

## Acceptance criteria

### P1-dispatch-core

- **AC-00 (ADR-0006 first).** Before any P1 code: ADR-0006 records AM-1/AM-2 mechanics — cache file
  location under the ROUTING store root (never `SET_AGENTS_STATE`/env-derived paths), invalidation key =
  (uid, digest of models.toml `[catalog]`+`[routing]`, pair), TTL 300s, atomic tmp+rename 0600 writes,
  corrupt/foreign cache ignored fail-closed, fresh-selected re-probe before writer authorization.
- **AC-01 (tiered catalog).** `routes.v1.toml` repopulated: ≥3 rows per enabled provider spanning all
  three tiers, models ∈ models.toml catalog lists, per-role compatibility, single-tier schema, effort/
  xhigh validation per the Tier model section. Roster coverage and collision validation keep passing.
- **AC-02 (tier-aware selection).** Required-tier resolution implemented exactly as specified, unit matrix
  covering every (task_class, risk) pair; candidate filtering/ordering per the Tier model section. A
  fast-tier route WINS (asserted, not "may win") when required tier is fast and a fast row is eligible.
  P1R's 19 behaviors regression-protected.
- **AC-03 (dispatch CLI).** New modes on the schema-2 envelope, exits 0/1/2, stable reason codes, never
  tracebacks:
  - `--route-decide <file|->`: descriptor JSON in (`role`, `task_class`, optional `risk` (raise-only),
    optional `review_of_run_id`, optional `selected_runtime`, optional `feature_id`/`package_id` —
    defaulting to the active feature/package in the state dir — from which AM-1 derives the context flags
    via that package's context-pack existence and freshness; no resolvable package ⇒ context flags false,
    conservative); facts built per AM-1 inside the CLI process. Writer classes get `run_id` (durable
    authorization, fresh-selected probe per AM-2). Review classes: with a valid `review_of_run_id` → full
    003 independence semantics; without one → a NON-executable decision that still reports tier/model with
    reason `REVIEW_IDENTITY_UNVERIFIED` — and a non-executable decision NEVER drives a routed spawn
    (doctrine, AC-07). Other role classes → non-executable decision with tier/model.
  - `--route-dispatched <run_id>`; `--route-terminal <run_id> <success|failure> [--latency-ms N]`;
    `--route-terminal <run_id> failure` from state `authorized` transitions to the NEW terminal state
    `abandoned` (never a review identity, fallback window closed, no actual identity) — this requires
    `SCHEMA` 3→4 with matching DDL CHECKs (see Non-goals for the operator wipe); `--routing-open-runs`
    lists run_id/state/age of non-terminal rows and `--routing-recent-writers` lists recent
    terminal-success writer run_ids (both redacted envelopes; new reason codes — incl.
    `REVIEW_IDENTITY_UNVERIFIED` — and new data payloads enter the closed allowlists and the reason→exit
    table; new mode flags join the routing-mode set so total mode exclusion holds).
  - Mode exclusion keeps 003's generic rule with a declared exempt set per routing mode (documented in
    the CLI contract): `--json` globally; `--fresh-probes` with decide; `--latency-ms` with terminal.
  - `--route-decide` for writers IS a mutating command and is documented/permissioned as such (never
    labeled read-only); concurrency doctrine: SQLITE busy ⇒ `ROUTING_UNAVAILABLE` exit 1, no auto-retry
    (003 rule), orchestrator retries by spawning a fresh decide.
- **AC-04 (probe cache).** Per AM-2/ADR-0006. Hermetic assertions: warm cache ⇒ zero probe subprocesses
  (PATH sentinel); wall-time <1s is a NON-gating budget measured as median-of-5 informational check;
  fresh-selected re-probe always runs for writer authorization (asserted via sentinel counting); cache
  bytes contain only pair→models (asserted); TTL/key invalidation and corrupt-cache cases covered.
  `--route-explain` reuses the cache (N-3 closed for explain).
- **AC-05 (backlog N-1..N-4).** Unhashable `required_tools` member ⇒ `FACTS_INCOMPLETE`;
  `_compose_for_tests` requires an explicit root (production store unreachable from the seam);
  `verify.sh` py_compile covers `routing_core/*.py`.

### P2-opencode-lane

- **AC-06 (tier variants, single source of truth).** models.toml gains per-role tier tables ONLY for:
  security-auditor, package-reviewer, delta-reviewer, implementer, debugger. Tables are lane-aware
  (go-zen/zen/local) and subscription-validated like every other role model. The tier table IS the
  declaration of the OpenCode-lane row per (role, tier). `generate.py` emits `<role>@<tier>` OpenCode
  variants (same canonical prompt/permissions/steps, tier model), ADDITIVE and OpenCode-only: the base
  agent keeps being emitted for every harness and every cross-reference. Variant↔catalog coherence is a
  build-time gate defined as a PURE OFFLINE PROJECTION (no live probes): each declared (role, tier) model
  must equal the model of exactly one catalog row with that tier that is opencode-compatible and
  role-compatible under a full-inventory assumption; zero or ambiguous matches fail the build.
  `generate.validate()` and `verify.sh`'s managed-diff surface are extended to the variant set; roles
  without tier tables generate exactly as today.
- **AC-07 (orchestrator doctrine).** Canonical orchestrator prompt gains the protocol: on spawn of a
  tiered role, run `--route-decide` and spawn the variant whose MODEL EQUALS the decided model (matching
  by model, not merely tier — the durable identity never lies). If the decision is executable but no
  variant matches the decided model (e.g. auth outage flipped the provider), the orchestrator closes the
  run (`--route-terminal <id> failure`, abandoned) and enters degraded mode. Degraded mode (renamed from
  "fallback" to avoid clashing with 003's durable fallback): router unavailable or model-mismatch ⇒ spawn
  the BASE static agent and narrate the degradation. Reviewers are routed ONLY with a verified
  `review_of_run_id` (recovered via `--routing-recent-writers` if context was compacted); an unverified
  reviewer decision never selects a variant — the base reviewer agent runs instead. Spawn narration
  includes decision route_id/run_id. Permission surface: coord's allowlist gains the routing CLI as an
  explicitly MUTATING-capable exception, narrated on use.
- **AC-08 (lane lifecycle).** Hermetic test drives decide(writer)→dispatched→terminal via the CLI against
  a temp root, counters visible in `--routing-report`; abandoned-run closure via
  `--route-terminal <id> failure` from `authorized` is exercised; worker-death doctrine documented (the
  orchestrator closes the run as failure with the stable reason on spawn loss).

### P3-pi-lane (gated)

- **AC-09g (spike gate T-300).** Before any other P3 work, a bounded spike answers with recorded evidence:
  (1) does pinned Pi expose an auth/status observation with closed argv, exit code, and no credential
  content read? (2) does the SDK accept per-session effort (or an equivalent) alongside model? (3) exact
  model-ID mapping catalog↔SDK. Any NO ⇒ HUMAN_DECISION_REQUIRED with the evidence; P3 does not proceed
  as specified without an explicit user decision.
- **AC-09 (managed Pi).** Exact-version, integrity-pinned install under a SET-AGENTES-owned dir with
  status/rollback. New CLI surface `--doctor --harness pi` is SPECIFIED as part of this package (schema-2
  envelope, exits 0/1/2, redacted output, no credential contents); `--harness` choices extended.
- **AC-10 (pi role artifacts).** `generate.py`/`install.py` gain a `pi` target: role artifacts
  semantically equivalent to the other harnesses; children fresh-context, minimum tools, no delegation
  tool, depth 0. `generate.validate()`/verify surface extended for the target.
- **AC-11 (spawn extension).** Pi extension `set_agents_spawn({role, task, context_pack})`: calls
  `--route-decide`, launches the child via the SDK with the decided model (and effort per AC-09g), closes
  the lifecycle (`--route-dispatched` before child start, `--route-terminal` with outcome, failure on
  child crash). `execution_enabled=false` ⇒ no session, refusal reason as tool result.
- **AC-11g (child guards).** The 002 AC-04 hard-deny doctrine applies AT THE EXTENSION (the new
  enforcement point): protected-path checks, argv/cwd/env normalization for any tool the child gets,
  versioned gate IDs, no delegation. Each guard has a test that proves the blocked behavior. Until
  AC-11g passes, pi children in this lane are read-only-tools only.
- **AC-12 (pi pairs + per-route runtime compatibility).** The probe table gains `(pi, provider)` entries
  (argv from the spike). Because identities derive per provider, runtime compatibility becomes
  declarable PER ROUTE via an OPTIONAL `runtimes` allowlist key. This deliberately reintroduces a field
  the SEC-006 repair removed, preserving the three things that repair protected: (i) the row schema stays
  closed — key sets become "required + allowlisted-optional", anything else `CATALOG_INVALID`; (ii)
  `runtimes` NEVER enters the canonical static-ID tuple (003/ADR-0005: runtime is not an ID field); (iii)
  two rows differing only in `runtimes` collapse to the same canonical tuple and stay `CATALOG_INVALID`
  (duplicate). Values outside the audited pair table ⇒ `CATALOG_INVALID`. `PI_SIMULATION_ONLY` flips only
  inside this package, gated by its tests; before the flip, pi-runtime requests keep failing closed
  (today as `RUNTIME_UNAVAILABLE` — regression-locked as fail-closed, not as a specific reason string).

### Global

- **AC-13 (evidence + docs).** Focused suites per package; `verify.sh` green (net never shrinks);
  GateSpecs cover the new CLI modes; docs/architecture documents per-lane on/off switches; proposal.md
  kept aligned with this contract (runtimes affected, <1s condition, benchmark non-goal).

## Trust and safety boundaries

- Facts derivation per AM-1; descriptor risk is raise-only; enums closed; 003's conservative combination
  applies. The orchestrator never fabricates facts objects — only the descriptor.
- Cache per AM-2: filtering-only authority; writer authorization always re-probes the selected pair.
- The dispatch CLI can close any run_id (same-UID audit-trail authorship is shared) — documented
  consequence of the R3 threat model, not a new surface.
- Pi children under AC-11g guards; extension is the enforcement point.

## Human decision triggers

Global rules, plus: any need to weaken a 003 invariant beyond AM-1/AM-2; AC-09g spike returning NO on any
question; any lane requiring a third provider before its audited pair exists.
