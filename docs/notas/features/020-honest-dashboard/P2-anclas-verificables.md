# 020-honest-dashboard · P2-anclas-verificables

<!-- notas:auto -->
## Motivo

- objetivo: Que una referencia file:line en docs/modules/ que ya no apunta a lo que dice sea un fallo detectable por comando
- complejidad: medium
- paths: `ai/scripts/feature_state_lib/check_anchors.py`, `ai/scripts/feature_state_lib/cli_modules.py`, `ai/scripts/feature-state.py`, `docs/modules`, `tests/test_module_docs.py`
- depende de: P1-digest-no-esconde

## Tareas

- [x] Gramatica de anclas: forma completa y abreviada :N, basename acotado a los paths del modulo (AC-06) (completed) · check-anchors rc=0 sobre los cinco modulos; rc=1 con ancla fuera de rango, con razon precisa. Suite 968 (base 943, +25). Verificado en vivo por el orquestador.
- [x] Comando check-anchors read-only, rc distinto de cero si hay anclas rotas (AC-07) (completed) · check-anchors rc=0 sobre los cinco modulos; rc=1 con ancla fuera de rango, con razon precisa. Suite 968 (base 943, +25). Verificado en vivo por el orquestador.
- [x] Verificacion semantica acotada a simbolo en backticks adyacente (AC-08) (completed) · check-anchors rc=0 sobre los cinco modulos; rc=1 con ancla fuera de rango, con razon precisa. Suite 968 (base 943, +25). Verificado en vivo por el orquestador.
- [x] Enganche en sync-notes con contrato never-raises (AC-09) (completed) · check-anchors rc=0 sobre los cinco modulos; rc=1 con ancla fuera de rango, con razon precisa. Suite 968 (base 943, +25). Verificado en vivo por el orquestador.
- [x] Corregir las anclas rotas de hoy, rc=0 sobre los cinco modulos (AC-10) (completed) · check-anchors rc=0 sobre los cinco modulos; rc=1 con ancla fuera de rango, con razon precisa. Suite 968 (base 943, +25). Verificado en vivo por el orquestador.
- [x] Tests que prueban el defecto: linea fuera de rango y simbolo movido (AC-11) (completed) · check-anchors rc=0 sobre los cinco modulos; rc=1 con ancla fuera de rango, con razon precisa. Suite 968 (base 943, +25). Verificado en vivo por el orquestador.

## Hallazgos

- F-01 [medium] closed
- F-02 [medium] closed
- F-03 [low] closed
- F-04 [low] open
- F-05 [medium] closed

## Recorrido

- review: repair_required (4 hallazgos)
- verificación: 0 refutados, 2 sostenidos
- verificación: 0 refutados, 1 sostenidos
- repair: F-01 → 3 archivos
- repair: F-02 → 3 archivos
- repair: F-03 → 3 archivos
- repair: F-05 → 3 archivos
- delta review: repair_required
- delta review: pass
- testing: pass
- runtime QA: pass
- gate `verify`: pass
- gate `build-check`: pass
- gate `diff-check`: pass

## Spawns

- SPAWN-001 implementer · modelo openai-codex/gpt-5.6-sol · effort medium · route run1_c5214efc4b0d73beea87d3e922b6ec85
- SPAWN-002 implementer · modelo openai-codex/gpt-5.6-sol · effort medium · route run1_05f7b094421e38137485dcbf27349065

context pack: `docs/specs/020-honest-dashboard/context/P2-anclas-verificables.md`

↩ [[features/020-honest-dashboard|020-honest-dashboard]]
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
