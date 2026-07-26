# Feature 004 — implementation plan (contract 1.1.0, pre-approval)

Three packages, strictly ordered. P3 is gated by its spike (T-300). Full loop per package
(implementation → gates → independent review → repair → delta → acceptance), `--mode feature` budgets.

## P1-dispatch-core

| ID | Work item | Acceptance |
|---|---|---|
| T-100 | ADR-0006: AM-1 (hybrid facts, raise-only risk) + AM-2 (cache filtering-only + fresh-selected) mechanics | AC-00 |
| T-101 | Tiered catalog repopulation (single-tier rows, fast/balanced/frontier × both providers) + schema/effort/xhigh validation; document route_id churn vs historical telemetry | AC-01 |
| T-102 | Required-tier resolution + tier-aware filtering/ordering in `RoutingService.route`; (task_class × risk) unit matrix | AC-02 |
| T-103 | Dispatch CLI: `--route-decide` (descriptor contract incl. `review_of_run_id` + `feature_id`/`package_id`, AM-1 derivation in-process), `--route-dispatched`, `--route-terminal` (incl. authorized→`abandoned`, SCHEMA 3→4 + DDL CHECKs + operator wipe note), `--routing-open-runs`, `--routing-recent-writers`; reason/data allowlists + routing-mode set extension; exempt-set mode exclusion; concurrency doctrine | AC-03 |
| T-104 | Probe cache per ADR-0006 + fresh-selected re-probe wired into writer authorization; explain reuses cache | AC-04 |
| T-105 | Backlog N-1..N-4 + focused suite + GateSpec update | AC-05, AC-13 |

Ownership: `docs/adr/0006-*.md`, `ai/catalogs/routes.v1.toml`, `ai/scripts/routing_core/**`,
`ai/scripts/routing.py`, `ai/scripts/set_agents_app.py` (routing zones), `tests/test_routing.py`,
`ai/scripts/verify.sh` (py_compile line).

## P2-opencode-lane

| ID | Work item | Acceptance |
|---|---|---|
| T-201 | Per-role tier tables (5 declared roles), lane-aware + subscription-validated, in models.toml/models_config | AC-06 |
| T-202 | `generate.py` variant emission `<role>@<tier>` + orchestrator allowlist + validate()/verify surface + build-time variant↔catalog coherence gate + install/prune | AC-06 |
| T-203 | Orchestrator doctrine: decide→variant protocol, narration, degraded mode, reviewer run_id sourcing; coord permission surface (mutating-capable, narrated) | AC-07 |
| T-204 | Hermetic lane lifecycle test + worker-death closure doctrine/test | AC-08 |

Ownership: `models.toml`, `ai/scripts/models_config.py`, `ai/scripts/generate.py`,
`ai/scripts/install.py`, `Global/_canonical/agents/orchestrator.md`, permission/hook policy files,
`tests/test_harness.py`.

## P3-pi-lane (gated by T-300)

| ID | Work item | Acceptance |
|---|---|---|
| T-300 | SPIKE (bounded, evidence-first): pinned Pi install probe; auth-status observability; SDK per-session effort; model-ID mapping. Any NO ⇒ HUMAN_DECISION_REQUIRED | AC-09g |
| T-301 | Managed pinned Pi install + status/rollback + `--doctor --harness pi` (new specified surface) | AC-09 |
| T-302 | `pi` target in generate/install (fresh-context children, no delegation, depth 0) + surfaces | AC-10 |
| T-303 | Extension `set_agents_spawn` over the SDK; lifecycle closure incl. crash⇒failure; refusal path | AC-11 |
| T-304 | Extension-level guards (002 AC-04 doctrine at the new enforcement point) with per-guard tests; read-only children until green | AC-11g |
| T-305 | `(pi, provider)` pairs + parsers (spike argv); per-route `runtimes` allowlist validation; gated `PI_SIMULATION_ONLY` flip; rollout/rollback docs + ADR/architecture updates | AC-12, AC-13 |

Ownership: `ai/scripts/routing_core/catalog.py`, `ai/scripts/generate.py`, `ai/scripts/install.py`,
new `Global/_canonical/pi-extension/` (TypeScript), `ai/scripts/set_agents_app.py` (doctor),
`docs/adr/`, `docs/architecture/`.

## Risks

- Pi SDK/auth reality vs docs → T-300 spike is the gate; nothing else in P3 starts before it.
- Tier curation quality → telemetry via `--routing-report`; catalog edits are 1-file diffs.
- Variant/catalog divergence → build-time coherence gate (AC-06), not doctrine.
- Cache staleness → AM-2 confines the cache to candidate filtering; authorization always re-probes.
- Orphan runs → authorized→failure closure + `--routing-open-runs` + worker-death doctrine (AC-03/08).
- Variant explosion → only the 5 declared roles.
