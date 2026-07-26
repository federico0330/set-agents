# 002-adaptive-pi-orchestration · P1-routing-core

<!-- notas:auto -->
## Motivo

- objetivo: Schema-2 configuration, deterministic routing, proportional flows, telemetry, CLI, and native gates
- ruteo: Critical routing contract requires hosted frontier implementation → implementer (openai/gpt-5.6-sol)
- complejidad: high
- riesgo: public-configuration-contract
- riesgo: allowlisted-command-execution
- riesgo: telemetry-privacy
- riesgo: reviewer-independence
- paths: `models.toml`, `ai/scripts/models_config.py`, `ai/scripts/setup_models.py`, `ai/scripts/routing.py`, `ai/scripts/set_agents_app.py`, `tests/test_routing.py`

## Tareas

- [x] P1-T1 (completed) · focused tests, py_compile, setup_models check, CLI smoke
- [x] P1-T2 (completed) · focused tests, py_compile, setup_models check, CLI smoke
- [x] P1-T3 (completed) · focused tests, py_compile, setup_models check, CLI smoke
- [x] P1-T4 (completed) · focused tests, py_compile, setup_models check, CLI smoke
- [x] P1-T5 (completed) · focused tests, py_compile, setup_models check, CLI smoke, third repair cycle: routing tests 20/20 pass, third repair cycle: py_compile, models check, CLI smokes, diff check pass

## Hallazgos

- P1-R1-001 [high] closed — correctness
- P1-R1-002 [high] closed — correctness
- P1-R1-003 [high] closed — integration
- P1-R1-004 [medium] closed — correctness
- P1-R1-005 [high] closed — correctness
- P1-R1-006 [high] closed — security
- P1-R1-007 [medium] closed — data-integrity
- P1-R1-008 [high] closed — security
- P1-R1-009 [high] closed — data-integrity
- P1-R1-010 [high] closed — scalability
- P1-R1-011 [medium] closed — integration
- P1-R1-012 [high] closed — testing
- SEC-001 [high] closed — security
- SEC-002 [high] closed — security
- SEC-003 [high] closed — security
- SEC-004 [high] closed — security
- SEC-005 [high] closed — security
- SEC-006 [medium] closed — security
- SEC-007 [medium] closed — security
- P1-DR1-001 [high] closed — security
- P1-DR1-002 [high] closed — security
- P1-DR1-003 [high] closed — integration
- P1-DR1-004 [high] closed — correctness
- P1-DR1-005 [high] closed — security
- P1-DR1-006 [medium] closed — correctness
- P1-DR1-007 [high] closed — security
- P1-DR1-008 [high] closed — security
- P1-DR1-009 [medium] closed — integration
- P1-DR2-001 [high] open — security
- P1-DR2-002 [high] open — security
- P1-DR2-003 [high] open — security
- P1-DR2-004 [medium] closed — correctness
- P1-DR2-005 [medium] closed — integration
- P1-DR2-006 [high] closed — security
- P1-DR2-007 [high] open — security
- P1-DR2-008 [high] open — data-integrity

## Recorrido

- review: repair_required (19 hallazgos)
- review: repair_required (5 hallazgos)
- repair: P1-R1-001, P1-R1-002, P1-R1-003, P1-R1-004, P1-R1-005, P1-R1-006, P1-R1-007, P1-R1-008, P1-R1-009, P1-R1-010, P1-R1-011, P1-R1-012, SEC-001, SEC-002, SEC-003, SEC-004, SEC-005, SEC-006, SEC-007 → 6 archivos
- repair: P1-DR1-001, P1-DR1-002, P1-DR1-003, P1-DR1-004, P1-DR1-005, P1-DR1-006, P1-DR1-007, P1-DR1-008, P1-DR1-009 → 6 archivos
- delta review: repair_required
- delta review: repair_required
- gate `p1-routing-tests`: pass
- gate `p1-compile`: pass
- gate `p1-models-check`: pass
- gate `p1-cli-smoke`: pass
- gate `p1-diff-check`: pass
- gate `p1-routing-tests-r3`: pass
- gate `p1-compile-r3`: pass
- gate `p1-models-r3`: pass
- gate `p1-cli-r3`: pass
- gate `p1-diff-r3`: pass

context pack: `docs/specs/002-adaptive-pi-orchestration/context/P1-routing-core.md`

↩ [[features/002-adaptive-pi-orchestration|002-adaptive-pi-orchestration]]
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
