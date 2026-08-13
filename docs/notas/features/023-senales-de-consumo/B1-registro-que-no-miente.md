# 023-senales-de-consumo · B1-registro-que-no-miente

<!-- notas:auto -->
## Motivo

- objetivo: Normalizador unico de consumo: que los cuatro lanes registren de verdad, y que un dict irreconocible se cuente como descarte
- complejidad: medium
- paths: `ai/scripts/routing_core`, `tests`, `docs/adr`

## Tareas

- [x] routing_core/usage.py con la muestra real del cable por lane en el docstring (AC-01) (completed) · unittest: 1092 OK / 3 skips (orquestador); verify.sh VERIFY_PASS; build.sh + --check GLOBAL_TREE_SYNC_OK + BUILD_CHECK_PASS
- [x] Un dict no vacio sin campos reconocidos pasa de ok a invalid (AC-02) (completed) · unittest: 1092 OK / 3 skips (orquestador); verify.sh VERIFY_PASS; build.sh + --check GLOBAL_TREE_SYNC_OK + BUILD_CHECK_PASS
- [x] Prueba por lane con columnas no-NULL, evidenciada con status_counts (AC-03) (completed) · unittest: 1092 OK / 3 skips (orquestador); verify.sh VERIFY_PASS; build.sh + --check GLOBAL_TREE_SYNC_OK + BUILD_CHECK_PASS

## Recorrido

- review: pass (0 hallazgos)
- testing: pass
- runtime QA: pass
- gate `unittest-suite`: pass
- gate `verify-sh`: pass
- gate `build-check`: pass
- gate `git-diff-check`: pass

## Spawns

- SPAWN-001 implementer · modelo anthropic/opus · effort medium · route run1_08556f77458c0e5f404b308e8d49f90b

context pack: `docs/specs/023-senales-de-consumo/context/B1-registro-que-no-miente.md`

↩ [[features/023-senales-de-consumo|023-senales-de-consumo]]
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
