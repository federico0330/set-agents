# 008-dynamic-selection · P1-uninterrupted-delegation

<!-- notas:auto -->
## Motivo

- objetivo: Que una sesion larga se camine sola: el orquestador no termina un turno para reportar avance, relanza una vez a un subagente muerto por cuota sin preguntar, y sigue trabajando en modo degradado con un solo proveedor dejando constancia del costo
- complejidad: medium
- riesgo: Toca doctrina ya testeada: REVIEWER_INDEPENDENCE_UNAVAILABLE como HARD DENIAL (test_harness.py:1246) y el bloque de cie…
- riesgo: build.sh --check NO detecta que Global/ quedo desactualizado tras editar _canonical/; solo verify.sh:22-27 lo agarra.
- paths: `Global/_canonical/agents/orchestrator.md`, `Global/_shared/AGENTS.opencode.md`, `Global/_shared/CLAUDE.md`, `Global/_shared/AGENTS.codex.md`, `Global/opencode/*`, `Global/claude-code/*`, `Global/codex/*`, `docs/adr/0011-uninterrupted-delegation.md`, `docs/adr/README.md`, `docs/specs/008-dynamic-selection/*`, `ai/state/features/008-dynamic-selection.json`, `ai/state/STATUS.md`, `ai/state/narrative-log.jsonl`, `ai/state/decisions-log.jsonl`, `docs/notas/*`

## Tareas

- [x] Doctrina de continuidad del turno en orchestrator.md (AC-01, AC-02, AC-03) (completed) · test_turn_continuity_doctrine_reaches_all_three_harnesses falla sobre el arbol previo y pasa despues, test_orchestrator_narration_reaches_all_three_harnesses sigue verde: el bloque de cierre no se toco
- [x] Operacion degradada de un solo proveedor y su constancia en el paquete (AC-04..AC-08) (completed) · assertIn de clean context, pi lane, update-package --exception y every provider is exhausted en los tres runtimes, test_orchestrator_doctrine_branches_on_route_decide_reason_taxonomy sigue verde: la denegacion dura del carril Pi no se contradice
- [x] Propagar la doctrina a los tres globales de Global/_shared, incluida la seccion Human decision faltante en OpenCode (AC-08) (completed) · test_shared_doctrine_covers_turn_continuity pasa sobre los tres archivos, test_shared_doctrine_covers_narration y test_shared_doctrine_covers_living_docs siguen verdes
- [x] Regenerar Global/ y agregar el test de tres runtimes (AC-09) (completed) · ./build.sh regenerado; verify.sh:22-27 diff -ruN sin diferencias, GLOBAL_PORTABILITY_OK
- [x] ADR-0011 con el trade-off de independencia y el diferimiento del carril Pi (AC-10) (completed) · docs/adr/0011-uninterrupted-delegation.md con D1..D6, umbral de reversion explicito y fila agregada en docs/adr/README.md, 0010 no se usa: esta reservado por 007-P2

## Hallazgos

- F-01 [critical] closed — correctness
- F-02 [high] closed — correctness
- F-03 [high] closed — correctness
- F-04 [medium] closed — correctness
- F-08 [low] closed — documentation
- F-09 [low] closed — documentation
- F-05 [medium] closed — correctness
- F-06 [medium] closed — correctness
- F-07 [low] closed — correctness
- F-10 [low] closed — documentation
- F-11 [low] closed — documentation
- D-01 [medium] closed — documentation
- D-02 [low] closed — documentation

## Recorrido

- review: repair_required (11 hallazgos)
- verificación: 0 refutados, 6 sostenidos
- verificación: 0 refutados, 2 sostenidos
- repair: F-01, F-02, F-03, F-04, F-05, F-06, F-07, F-08, F-09, F-10, F-11 → 8 archivos
- repair: D-01, D-02 → 2 archivos
- delta review: repair_required
- delta review: pass
- testing: pass
- testing: pass
- runtime QA: pass (waived)
- runtime QA: pass (waived)
- gate `verify.sh`: pass
- gate `build-check`: pass
- gate `ownership`: pass

↩ [[features/008-dynamic-selection|008-dynamic-selection]]
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
