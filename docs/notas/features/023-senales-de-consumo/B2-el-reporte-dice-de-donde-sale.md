# 023-senales-de-consumo · B2-el-reporte-dice-de-donde-sale

<!-- notas:auto -->
## Motivo

- objetivo: Dos secciones nombradas por su fuente que nunca se suman, para que no haya doble conteo
- complejidad: small
- paths: `ai/scripts`, `tests`, `docs/adr`
- depende de: B1-registro-que-no-miente

## Tareas

- [x] Separar el consumo propio del de los stores de los CLIs (AC-04) (completed) · unittest: 1095 OK / 3 skips (orquestador); verify.sh VERIFY_PASS; build.sh --check GLOBAL_TREE_SYNC_OK + BUILD_CHECK_PASS
- [x] Ninguna superficie muestra un total sin decir su fuente (AC-05) (completed) · unittest: 1095 OK / 3 skips (orquestador); verify.sh VERIFY_PASS; build.sh --check GLOBAL_TREE_SYNC_OK + BUILD_CHECK_PASS

## Recorrido

- review: pass (0 hallazgos)
- testing: pass
- runtime QA: pass
- gate `unittest-suite`: pass
- gate `verify-sh`: pass
- gate `build-check`: pass
- gate `git-diff-check`: pass

## Spawns

- SPAWN-001 implementer · modelo anthropic/opus · effort medium · route run1_566c34a108b5c9ca05efd67240b7e517

context pack: `docs/specs/023-senales-de-consumo/context/B2-el-reporte-dice-de-donde-sale.md`

↩ [[features/023-senales-de-consumo|023-senales-de-consumo]]
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
