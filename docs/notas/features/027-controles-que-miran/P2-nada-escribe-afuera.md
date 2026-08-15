# 027-controles-que-miran · P2-nada-escribe-afuera

<!-- notas:auto -->
## Motivo

- objetivo: Que ningun test pueda escribir fuera de un directorio temporal
- complejidad: medium
- paths: `tests`, `ai/scripts`, `docs/adr`
- depende de: P1-alcance-y-aislamiento

## Tareas

- [x] Guarda que falla si un test escribe fuera de tmp, nombrando el archivo (AC-04) (completed) · Guardia focal PASS; tests.test_harness completo: 466 tests OK (2 skips), evidencia P2-gates-retry.md.
- [x] Probada en las dos direcciones: tmp pasa, HOME falla (AC-05) (completed) · Temp/home/config destination matrix PASS; fixture drift sandbox PASS; build check PASS; evidencia P2-postrepair-gates.md.

## Hallazgos

- P2-F01 [high] closed — correctness
- P2-F02 [high] closed — security
- P2-F03 [medium] closed — testing
- P2-F04 [high] closed — correctness
- P2-F05 [medium] closed — testing
- P2-F06 [medium] closed — testing
- P2-F07 [medium] closed — security
- P2-F08 [low] closed — security
- P2-F09 [low] closed — testing
- P2-F10 [low] closed — test-coverage

## Recorrido

- review: repair_required (3 hallazgos)
- verificación: 0 refutados, 3 sostenidos
- verificación: 0 refutados, 7 sostenidos
- repair: P2-F01, P2-F02, P2-F03 → 5 archivos
- repair: P2-F04, P2-F05, P2-F06, P2-F07, P2-F08, P2-F09, P2-F10 → 4 archivos
- delta review: repair_required
- delta review: pass
- testing: pass
- runtime QA: pass
- gate `unittest-harness`: pass
- gate `unittest-harness-long`: pass
- gate `verify-sh`: pass
- gate `unittest-suite`: pass
- gate `build-check`: pass
- gate `git-diff-check`: pass
- gate `verify-sh-final`: pass
- gate `ownership`: pass

## Spawns

- SPAWN-001 package-planner · modelo openai/gpt-5.6-terra · effort high
- SPAWN-002 implementer · modelo openai-codex/gpt-5.6-terra · effort medium
- SPAWN-003 gate-runner · modelo openai-codex/gpt-5.6-luna · effort low
- SPAWN-004 local-gate-runner · modelo openai-codex/gpt-5.6-luna · effort low
- SPAWN-005 gate-runner · modelo openai-codex/gpt-5.6-terra · effort medium
- SPAWN-006 repair-agent · modelo openai-codex/gpt-5.6-terra · effort medium
- SPAWN-007 gate-runner · modelo openai-codex/gpt-5.6-luna · effort low
- SPAWN-008 package-reviewer · modelo openai-codex/gpt-5.6-sol · effort xhigh

context pack: `docs/specs/027-controles-que-miran/context/P2-nada-escribe-afuera.md`

↩ [[features/027-controles-que-miran|027-controles-que-miran]]
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
