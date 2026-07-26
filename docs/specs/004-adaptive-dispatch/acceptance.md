# Feature 004 — acceptance scenarios (BDD, contract 1.1.0)

Given/When/Then per AC. Regression tests are written after convergence and assert these observables.

## P1-dispatch-core

**AC-00 ADR-0006**
- Given P1 starts, When the first P1 code lands, Then ADR-0006 exists and records AM-1/AM-2 mechanics
  (cache root under the routing store root, invalidation key, TTL, atomic 0600 writes, fresh-selected).

**AC-01 tiered catalog**
- Given the shipped catalog, When built with production config, Then every enabled provider has rows in
  `fast`, `balanced` and `frontier`; every model ∈ models.toml lists; single `tier` string per row
  (a `tiers` list or unknown value ⇒ `CATALOG_INVALID`); an `xhigh` effort row ⇒ `CATALOG_INVALID` while
  `xhigh_benchmarked=false`; roster coverage/collision checks still pass.

**AC-02 tier-aware selection**
- Given facts with `task_class=security` (or combined risk high), When routing, Then the selected route's
  tier is `frontier`, or the decision is `NO_ELIGIBLE_ROUTE` with the tier shortfall visible in exclusions.
- Given `task_class=mechanical, risk=low` and an eligible fast row, When routing, Then the fast row WINS
  over eligible balanced/frontier rows regardless of curated_priority across tiers.
- Given any (task_class, risk) pair, When resolving required tier, Then the pure function returns the
  documented value (full matrix unit-tested).
- Given descriptor risk lower than the derived base (e.g. `security` + `risk=low`), When deciding, Then
  the derived base governs (raise-only asserted).
- Given the P1R suite, When run, Then all 19 prior behaviors pass unchanged.

**AC-03 dispatch CLI**
- Given a writer descriptor, When `--route-decide -`, Then exit 0, one-line schema-2 envelope with
  `run_id` + decided identity + tier; repeating the call mints a NEW run_id.
- Given a reviewer descriptor WITHOUT `review_of_run_id`, When deciding, Then non-executable decision with
  tier/model and reason `REVIEW_IDENTITY_UNVERIFIED`, exit 0, no DB row.
- Given a reviewer descriptor WITH a valid terminal-success writer run_id, When deciding, Then 003
  independence semantics apply (family exclusion asserted).
- Given a docs-rw role, When deciding, Then non-executable decision with tier/model (no run_id).
- Given `authorized` state, When `--route-terminal <id> failure`, Then exit 0 and the row lands in the new
  terminal state `abandoned` (SCHEMA=4; never a review identity; fallback window closed); When
  `--route-terminal <id> success` from `authorized`, Then exit 1 stable reason (never a traceback).
- Given a schema-3 (or schema-2) DB on disk, When any routing operation runs, Then `ROUTING_UNAVAILABLE`
  fail-closed byte-identical (operator wipe doctrine, no migration).
- Given open runs, When `--routing-open-runs`, Then a redacted envelope lists run_id/state/age; Given
  terminal-success writers, When `--routing-recent-writers`, Then their run_ids are listed (redacted).
- Given `--route-decide` combined with any non-exempt non-default argument, Then exit 2
  `ROUTING_INPUT_INVALID`; the exempt sets (`--json`; `--fresh-probes` for decide; `--latency-ms` for
  terminal) are accepted.
- Given a concurrent holder of the DB write lock, When deciding a writer, Then exit 1
  `ROUTING_UNAVAILABLE`, no auto-retry, consistent DB afterwards.

**AC-04 probe cache**
- Given a warm valid cache, When `--route-decide` for a READ-ONLY class, Then zero probe subprocesses
  (PATH sentinel).
- Given a warm valid cache, When `--route-decide` authorizes a WRITER, Then exactly the selected (and
  differing fallback) pair probes run fresh (sentinel count), and a failed fresh probe makes the pair
  unavailable (no stale authorization).
- Given a cache older than TTL, or a models.toml digest change, or `--fresh-probes`, When deciding, Then
  all probes run and the cache is atomically rewritten 0600 with pair→models content only (bytes asserted).
- Given a corrupt or foreign cache file, When deciding, Then it is ignored fail-closed (fresh probes).
- Wall-time: median-of-5 warm decides <1s reported as a NON-gating informational check.

**AC-05 backlog**
- Given `required_tools` containing an unhashable member, When routing, Then `FACTS_INCOMPLETE`.
- Given `_compose_for_tests` without an explicit root, When called, Then it raises.
- Given `verify.sh`, When run, Then py_compile covers `ai/scripts/routing_core/*.py`.

## P2-opencode-lane

**AC-06 tier variants**
- Given tier tables for the five declared roles, When `./build.sh --check`, Then staging contains
  `<role>@fast/@balanced/@frontier` variants (same prompt body/permissions/steps, tier model), the
  orchestrator task-allowlist includes them, `generate.validate()` passes with the extended surface, and
  roles without tables emit exactly one agent.
- Given a tier-table model with zero or ambiguous matches under the pure offline projection (catalog rows
  of that tier, opencode-compatible, role-compatible, full-inventory assumption), When building, Then the
  build FAILS (coherence gate; no live probes involved).
- Given the five roles, When generated for Claude Code/Codex and for OpenCode commands referencing base
  names, Then the base agents are still emitted unchanged (variants are additive, OpenCode-only).
- Given lane/subscription resolution, When generating for each profile, Then variant models pass the same
  subscription validation as every other role model.

**AC-07 doctrine**
- Given the canonical orchestrator prompt, When inspected, Then it contains: decide→spawn protocol
  matching by DECIDED MODEL (not tier), model-mismatch ⇒ close run as abandoned + degraded mode with the
  BASE agent, router-unavailable ⇒ degraded mode with the base agent, decision id in spawn narration,
  reviewers routed only with verified `review_of_run_id` (sourced from state or
  `--routing-recent-writers`), and the routing CLI documented as mutating-capable in coord's permission
  surface.

**AC-08 lane lifecycle**
- Given a temp routing root, When decide(writer)→dispatched→terminal via CLI, Then exits 0 and
  `--routing-report` shows the route's counters.
- Given a spawn that died without terminal, When the orchestrator applies the worker-death doctrine, Then
  `--route-terminal <id> failure` closes it and the report reflects the failure.

## P3-pi-lane (gated)

**AC-09g spike** — Given T-300 completes, Then evidence records YES/NO for: probeable auth-status without
credential reads; per-session effort; model-ID mapping. Any NO ⇒ HUMAN_DECISION_REQUIRED recorded.

**AC-09 managed Pi** — Given install, Then exact pinned version under the managed dir; doctor envelope
0/1/2 redacted; rollback restores prior state.

**AC-10 pi artifacts** — Given the pi target build, Then per-role artifacts semantically equal to canonical
(spot-check test), no delegation tool, validate/verify surfaces extended.

**AC-11 spawn extension** — Given a decided executable route, When `set_agents_spawn`, Then the child
session uses the decided model (and effort per spike), lifecycle closes including crash⇒failure; Given a
non-executable decision, Then no session and the refusal is the tool result.

**AC-11g guards** — Given each 002 AC-04 guard class (protected path write, argv/cwd/env manipulation,
delegation attempt), When attempted by/through a pi child, Then it is blocked at the extension and a test
proves it. Until green, pi children get read-only tools.

**AC-12 pi pairs** — Given the spike argv, When probing with stubs, Then `(pi, provider)` yields models
intersected with models.toml; broken/absent pi affects only those pairs. Given per-route `runtimes`
allowlists, When building, Then values outside the audited pair table ⇒ `CATALOG_INVALID`; pi-runtime
requests fail closed until the gated flip, asserted as fail-closed (not tied to a specific reason string).

## Global

**AC-13** — verify.sh green (net never shrinks); GateSpecs cover new CLI modes; per-lane on/off switches
documented; proposal.md aligned with the contract.
