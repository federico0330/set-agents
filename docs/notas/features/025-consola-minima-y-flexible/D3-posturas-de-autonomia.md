# 025-consola-minima-y-flexible · D3-posturas-de-autonomia

<!-- notas:auto -->
## Motivo

- objetivo: Que el usuario elija cuanta autonomia le da al harness, y que cada postura cambie algo observable
- complejidad: medium
- paths: `ai/scripts`, `Global/_canonical`, `tests`, `docs/adr`
- depende de: D2-trabajo-visible

## Tareas

- [x] Tres posturas elegibles con su explicacion en pantalla (AC-06) (completed) · D3-gates-runtime-qa.md: --posturas, persistencia y tres conductas observables verdes.
- [x] Toggles de TDD estricto, SDD y RDD con su explicacion (AC-07) (completed) · D3-gates-runtime-qa.md: --metodologias y toggles de TDD/SDD/RDD verdes.
- [x] RDD definido como Receipt Driven Development, nombrando lo que el harness ya practica (AC-08) (completed) · D3-gates-runtime-qa.md: RDD referido como Receipt Driven Development y reconciliado con strict-TDD.

## Hallazgos

- D3-F01 [high] closed — testing
- D3-F02 [medium] closed — testing
- D3-F03 [medium] closed — correctness

## Recorrido

- review: repair_required (3 hallazgos)
- verificación: 0 refutados, 3 sostenidos
- verificación: 0 refutados, 1 sostenidos
- repair: D3-F01, D3-F02, D3-F03 → 8 archivos
- repair: D3-F01 → 7 archivos
- delta review: repair_required
- delta review: pass
- testing: pass
- runtime QA: pass
- gate `d3-unit-focal`: pass
- gate `d3-runtime-cli`: pass

## Spawns

- SPAWN-001 gate-runner · modelo openai-codex/gpt-5.6-luna · effort low · route MODEL_STATIC_FALLBACK
- SPAWN-002 package-reviewer · modelo openai-codex/gpt-5.6-sol · effort xhigh · route MODEL_STATIC_FALLBACK
- SPAWN-003 finding-verifier · modelo openai-codex/gpt-5.6-sol · effort xhigh · route MODEL_STATIC_FALLBACK
- SPAWN-004 repair-agent · modelo openai-codex/gpt-5.6-terra · effort medium · route MODEL_STATIC_FALLBACK
- SPAWN-005 delta-reviewer · modelo openai-codex/gpt-5.6-sol · effort xhigh · route MODEL_STATIC_FALLBACK
- SPAWN-006 finding-verifier · modelo openai-codex/gpt-5.6-sol · effort xhigh · route MODEL_STATIC_FALLBACK
- SPAWN-007 repair-agent · modelo openai-codex/gpt-5.6-terra · effort medium · route MODEL_STATIC_FALLBACK
- SPAWN-008 delta-reviewer · modelo openai-codex/gpt-5.6-sol · effort xhigh · route MODEL_STATIC_FALLBACK

context pack: `docs/specs/025-consola-minima-y-flexible/context/D3-posturas-de-autonomia.md`

↩ [[features/025-consola-minima-y-flexible|025-consola-minima-y-flexible]]
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
