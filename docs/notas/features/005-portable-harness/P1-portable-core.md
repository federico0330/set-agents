# 005-portable-harness · P1-portable-core

<!-- notas:auto -->
## Motivo

- objetivo: Make the 004 adaptive router reachable and correctly scoped from any project on any machine: two-roots doctrine, install-time-only path baking, allowlist matcher fix, self-inclusive project discovery, SEC-A02 re-anchoring, persisted project id + project_key (SCHEMA 4->5), P1 scaffold, harness self-scaffold, extended honest degrade, hermetic guest proof.
- complejidad: high
- riesgo: high
- paths: `ai/scripts/install.py`, `ai/scripts/generate.py`, `ai/scripts/coord_policy.py`, `ai/scripts/set_agents_app.py`, `ai/scripts/routing_core/store.py`, `ai/scripts/bootstrap_project.py`, `ai/scripts/sync-project.sh`, `build.sh`, `ai/scripts/verify.sh`, `Global/_canonical/agents/orchestrator.md`, `Global/claude-code/hooks/coord_policy.py`, `Global/claude-code/agents/orchestrator.md`, `Global/codex/agents/orchestrator.toml`, `Global/opencode/agents/orchestrator.md`, `docs/adr/0008-two-roots-portability.md`, `tests/test_harness.py`, `tests/test_routing.py`, `ai/scripts/feature-state.py`, `ai/scripts/check-owned-paths.py`, `ai/state/project.json`, `ai/state/features/005-portable-harness.json`, `ai/state/STATUS.md`, `ai/state/narrative-log.jsonl`, `docs/notas/00 - Proyecto.md`, `docs/notas/features/005-portable-harness.md`, `docs/notas/features/005-portable-harness/**`, `docs/specs/005-portable-harness/bitacora.md`

## Tareas

- [x] T-100 (completed) · Implemented and independently gated in P1 evidence.
- [x] T-101 (completed) · Implemented and independently gated in P1 evidence.
- [x] T-102 (completed) · Implemented and independently gated in P1 evidence.
- [x] T-103 (completed) · Implemented and independently gated in P1 evidence.
- [x] T-104 (completed) · Implemented and independently gated in P1 evidence.
- [x] T-105 (completed) · Implemented and independently gated in P1 evidence.
- [x] T-106 (completed) · Implemented and independently gated in P1 evidence.
- [x] T-107 (completed) · Implemented and independently gated in P1 evidence.
- [x] T-108 (completed) · Implemented and independently gated in P1 evidence.
- [x] T-109 (completed) · Implemented and independently gated in P1 evidence.
- [x] T-110 (completed) · Implemented and independently gated in P1 evidence.
- [x] T-111 (completed) · Implemented and independently gated in P1 evidence.

## Hallazgos

- P1-REV-001 [high] closed — Lifecycle run-id operations lack project-key scoping
- P1-REV-002 [high] closed — Malformed untrusted feature JSON can crash route decide
- P1-REV-003 [high] closed — Git-only project root lacks path-hash identity fallback
- P1-REV-004 [high] closed — Scaffold silently accepts differing generic scripts
- P1-REV-005 [high] closed — Pi lifecycle does not propagate user project root
- P1-REV-006 [high] closed — Guest E2E does not prove install and absolute route invocation
- P1-REV-007 [medium] closed — Schema-4 degrade lacks migration-required warning
- P1-REV-008 [medium] closed — Corrupt project identity returns input error rather than stable degrade
- P1-DLT-001 [high] closed — Pi lifecycle caller does not propagate user project root
- P1-DLT-002 [medium] closed — Guest E2E does not observe dispatch project_key

## Recorrido

- review: repair_required (8 hallazgos)
- review: pass (0 hallazgos)
- repair: P1-REV-001, P1-REV-002, P1-REV-003, P1-REV-004, P1-REV-005, P1-REV-006, P1-REV-007, P1-REV-008 → 4 archivos
- repair: P1-DLT-001, P1-DLT-002 → 8 archivos
- delta review: repair_required
- delta review: pass
- testing: pass
- testing: pass
- runtime QA: pass
- runtime QA: pass
- gate `p1-independent-gates`: pass
- gate `p1-dlt-independent-gates`: pass

context pack: `docs/specs/005-portable-harness/context/P1-portable-core.md`

↩ [[features/005-portable-harness|005-portable-harness]]
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
