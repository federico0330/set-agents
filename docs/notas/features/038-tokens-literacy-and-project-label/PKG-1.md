# 038-tokens-literacy-and-project-label · PKG-1

<!-- notas:auto -->
## Motivo

- objetivo: Cap always-on doctrine, code literacy, project_label, cost-report per encargo
- ruteo: single bounded public-contract package already implemented in this turn → implementer (inherit)
- complejidad: small
- paths: `Global/_shared/`, `Global/_canonical/agents/orchestrator.md`, `Global/_canonical/agents/architect.md`, `ai/scripts/set_agents_app.py`, `ai/scripts/feature-state.py`, `ai/scripts/feature_state_lib/render_notes.py`, `ai/scripts/cost-report.py`, `PROYECTO/ai/scripts/feature-state.py`, `PROYECTO/ai/scripts/feature_state_lib/render_notes.py`, `tests/test_harness.py`, `docs/adr/0069-tiered-doctrine-and-code-literacy.md`, `docs/specs/038-tokens-literacy-and-project-label/`, `TIPS-USO.md`, `docs/COMO-FUNCIONA.md`

## Tareas

- [x] project_label + hub title (completed) · unittest tests.test_harness, ./ai/scripts/verify.sh VERIFY_PASS 1377
- [x] tiered always-on + orchestrator literacy + line cap test (completed) · unittest tests.test_harness, ./ai/scripts/verify.sh VERIFY_PASS 1377
- [x] cost-report sessions per encargo (completed) · unittest tests.test_harness, ./ai/scripts/verify.sh VERIFY_PASS 1377

## Hallazgos

- PKG1-TEST-01 [low] closed — testing
- PKG1-TEST-02 [medium] closed — testing
- PKG1-TEST-03 [low] closed — testing

## Recorrido

- review: repair_required (3 hallazgos)
- verificación: 0 refutados, 3 sostenidos
- repair: PKG1-TEST-01, PKG1-TEST-02, PKG1-TEST-03 → 1 archivos
- delta review: pass
- testing: pass
- runtime QA: pass (waived)
- gate `verify`: pass
- gate `build-check`: pass
- gate `owned-paths`: pass

## Spawns

- SPAWN-001 implementer · modelo cursor/grok-4.6 · effort high
- SPAWN-002 package-reviewer · modelo openai/gpt-5.6-sol · effort high
- SPAWN-003 finding-verifier · modelo openai/gpt-5.6-sol · effort high
- SPAWN-005 delta-reviewer · modelo openai/gpt-5.6-sol · effort medium

context pack: `docs/specs/038-tokens-literacy-and-project-label/context/PKG-1.md`

↩ [[features/038-tokens-literacy-and-project-label|038-tokens-literacy-and-project-label]]
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
