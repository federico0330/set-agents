# ADR-0031 — Observabilidad por spawn: la decisión de routing es auditable, no solo tomada

- **Status**: Accepted
- **Date**: 2026-08-05
- **Relates to**: ADR-0030 (decide siempre), ADR-0010 (spawn accounting), ADR-0014 (spawn
  provenance), ADR-0027 (milestone narration).

## Context

ADR-0030 establishes one routing decision per spawn for all 28 roles and states that a `simulate`
envelope is "still a decision, still recorded". In practice three gaps made that claim unfulfillable:

1. `cmd_route_decide` composes the service with `store=None` for every `simulate` decision
   (`ai/scripts/set_agents_app.py`), so the ~22 non-writer/non-verified-review roles' decisions
   existed only in the CLI envelope — gone the moment the orchestrator's turn ended.
2. `record-spawn` (`ai/scripts/feature-state.py`) had no structured fields for the decision; the
   doctrine's only vehicle was prose inside the free-text `--tech` register. Nothing validated it,
   nothing could query it.
3. There was no join key between the routing store's `run_id` and feature-state's `SPAWN-NNN`, so
   even for durable writer runs "which model ran SPAWN-007" had no answer from state.

## Decision

1. **Structured decision fields on `record-spawn`.** Optional `--model`, `--provider`, `--effort`
   and `--route-id` land on the spawn entry AND the event metadata only when provided. Old state
   files and old callers are byte-identical. `--route-id` carries the decision's `run_id`
   (writer/verified-review durable runs) or its `decision_id` (everything else) — the join contract
   is `spawn.route_id ∈ {run_id, decision_id}`.
2. **Append-only decisions log, simulate included.** Every `--route-decide` appends one JSONL line
   to `decisions-v1.jsonl` next to `routing.db` (same fixed production root as `RoutingStore`, same
   `SET_AGENTS_ROUTING_TEST_ROOT` test seam), minting a per-decision `dec1_<32hex>` `decision_id`
   that also travels in the envelope. The append is CLI-layer, best-effort by contract (an `OSError`
   can never break the one-JSON-line envelope or the exit code) and rotates one generation past
   1 MB. The name deliberately avoids the legacy `routing-decisions.json` set in `routing.py`.
3. **Read-only query surfaces.** `set-agents --routing-decisions [--limit N]` returns the log tail
   filtered to the resolved project (missing log = legitimate empty list, exit 0).
   `feature-state.py spawns [<feature_id>|--state-file …] [--package-id …]` lists each spawn with
   its decision fields; it never mutates state. Renderers surface the fields where they exist:
   bitácora headers gain `· modelo <provider>/<model> · effort <e>`, the per-package living note
   gains a `## Spawns` section, and the execution graph appends `[model]` to spawn node labels.
4. **Doctrine.** After `--route-decide`, the orchestrator passes the decision into `record-spawn`
   structured, never only as prose (all five orchestrator copies, regenerated from
   `Global/_canonical` by `build.sh`).

## Non-goals

- No `routing.db` schema change: the SQLite schema stays at its pinned version; the sidecar log is
  not the store and authorizes nothing.
- `simulate` semantics are untouched: still `store=None`, still no `--route-dispatched`/
  `--route-terminal`, still never presented as an authorized run. This ADR adds the audit trail
  ADR-0030 promised, not enforcement.
- The log is observability, never a gate input or a routing fact source.

## Consequences

- "¿Qué modelo corrió SPAWN-NNN?" is answerable from state: `feature-state.py spawns` joins the
  spawn record to the decision through `route_id`, and `--routing-decisions` shows the full
  decision (reason codes included) for simulate roles that previously left zero trace.
- Every agent-authored field that lands in a generated document goes through `_short`
  (marker-neutralization), same as the existing registers.
- Legacy states, packages and callers render byte-identical; the fields are additive everywhere.

## Verification

`tests/test_routing_decisions.py` (decision log + `--routing-decisions`), the record-spawn cluster
in `tests/test_harness.py` (structured fields, `spawns` subcommand, renderers), and the doctrine
markers in `tests/test_decide_always.py`.
