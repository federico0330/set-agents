# 004-adaptive-dispatch · P1-dispatch-core

<!-- notas:auto -->
## Motivo

- objetivo: Tiered catalog, risk-aware selection, dispatch CLI, probe cache (AM-1/AM-2)
- ruteo: Security-critical trust boundary work on the routing core itself; in-session Claude implementer per user instruction, i… → implementer (claude-fable-in-session)
- complejidad: high
- riesgo: SCHEMA 4 bump invalidates schema-3 DBs (operator wipe doctrine)
- riesgo: cache staleness confined to candidate filtering (AM-2)
- riesgo: catalog_version 2 changes all route_ids (telemetry churn documented)
- paths: `docs/adr/0006-adaptive-dispatch-cache-and-facts.md`, `ai/catalogs/routes.v1.toml`, `ai/scripts/routing_core/**`, `ai/scripts/routing.py`, `ai/scripts/verify.sh`, `tests/test_routing.py`, `docs/specs/004-adaptive-dispatch/context/P1-dispatch-core.md`, `docs/specs/004-adaptive-dispatch/evidence/P1-*`, `docs/architecture/overview.md`

## Tareas

- [x] T-100 (completed) · ADR-0006 written; AM-1/AM-2 mechanics fully specified (table per field, cache key/root/TTL/atomicity, fresh-selected authority)
- [x] T-101 (completed) · catalog v2 6 rows single-tier; build_snapshot validates version/tier/effort/xhigh/optional runtimes; suite 19/19
- [x] T-102 (completed) · required_tier pure fn + TIER_INSUFFICIENT exclusion + tier-first ordering; suite 19/19 (matrix test lands in T-105)
- [x] T-103 (completed) · CLI decide/dispatched/terminal/open-runs/recent-writers live-verified: writer fast-tier authorized run1_817c..., dispatched, terminal success, report counters, repeat-terminal exit1; --yes conflict exit2; SCHEMA 4 abandoned state
- [x] T-104 (completed) · probe cache cold 28.9s/warm 0.0s; decide warm 0.25s; fresh-selected reprobe 13.5s verified; opencode non-TTY hang fixed (CI/TERM env); codex stderr parse; cmd dedupe
- [x] T-105 (completed) · N-1..N-4 closed; suite 19->29 tests OK 3.1s (tier matrix, hermetic probe-cache stubs, fresh-selected gating, abandoned lifecycle, CLI mode/modifier exclusion); verify.sh VERIFY_PASS; harness regressions 2/2; setup_models PASS

## Hallazgos

- PKG-N01 [high] closed — correctness
- PKG-N02 [medium] closed — data-integrity
- PKG-N03 [medium] closed — data-integrity
- PKG-N04 [medium] closed — testing
- PKG-N05 [medium] closed — correctness
- PKG-N06 [medium] closed — correctness
- PKG-N07 [medium] closed — correctness
- PKG-N08 [low] closed — testing
- PKG-N09 [low] closed — integration
- PKG-N10 [low] closed — scalability
- PKG-N11 [low] closed — correctness
- SEC-A01 [high] closed — security
- SEC-A02 [medium] closed — security
- SEC-A03 [medium] closed — security

## Recorrido

- review: repair_required (14 hallazgos)
- repair: PKG-N01, PKG-N02, PKG-N03, PKG-N04, PKG-N05, PKG-N06, PKG-N07, PKG-N08, PKG-N09, PKG-N10, PKG-N11, SEC-A01, SEC-A02, SEC-A03 → 11 archivos
- delta review: pass
- testing: pass
- runtime QA: pass
- gate `p1-package-gates`: pass
- gate `r1-post-repair-verification`: pass

context pack: `docs/specs/004-adaptive-dispatch/context/P1-dispatch-core.md`

↩ [[features/004-adaptive-dispatch|004-adaptive-dispatch]]
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
