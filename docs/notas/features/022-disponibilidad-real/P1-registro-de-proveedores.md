# 022-disponibilidad-real · P1-registro-de-proveedores

<!-- notas:auto -->
## Motivo

- objetivo: Un unico registro del que se derivan las seis tablas de proveedores que hoy estan en lockstep manual
- complejidad: medium
- paths: `ai/scripts/routing_core/catalog.py`, `ai/scripts/models_config.py`, `ai/scripts/set_agents_app.py`, `tests/test_routing.py`, `docs/adr`

## Tareas

- [x] PROVIDERS registry del que se derivan las seis tablas, incluida _MODEL_PREFERENCE_PROVIDERS (AC-01) (completed) · unittest discover -s tests: 981 OK / 3 skips (corrida del orquestador); verify.sh: VERIFY_PASS; build.sh --check: GLOBAL_TREE_SYNC_OK + BUILD_CHECK_PASS; git diff --check limpio
- [x] Arreglar el test que compara un literal contra otro literal en vez de contra la fuente (AC-01) (completed) · unittest discover -s tests: 981 OK / 3 skips (corrida del orquestador); verify.sh: VERIFY_PASS; build.sh --check: GLOBAL_TREE_SYNC_OK + BUILD_CHECK_PASS; git diff --check limpio
- [x] Test de caracterizacion byte-identico: este paquete no cambia comportamiento (AC-02) (completed) · unittest discover -s tests: 981 OK / 3 skips (corrida del orquestador); verify.sh: VERIFY_PASS; build.sh --check: GLOBAL_TREE_SYNC_OK + BUILD_CHECK_PASS; git diff --check limpio
- [x] ADR-0042 corrigiendo la afirmacion de ADR-0034:124-126 con la medicion (AC-03) (completed) · unittest discover -s tests: 981 OK / 3 skips (corrida del orquestador); verify.sh: VERIFY_PASS; build.sh --check: GLOBAL_TREE_SYNC_OK + BUILD_CHECK_PASS; git diff --check limpio

## Hallazgos

- P1-F01 [critical] closed
- P1-F02 [high] closed

## Recorrido

- review: repair_required (2 hallazgos)
- verificación: 0 refutados, 2 sostenidos
- repair: P1-F01, P1-F02 → 1 archivos
- delta review: pass
- testing: pass
- runtime QA: pass
- gate `unittest-suite`: pass
- gate `verify-sh`: pass
- gate `build-check`: pass
- gate `git-diff-check`: pass

## Spawns

- SPAWN-001 implementer · modelo anthropic/opus · effort medium · route run1_370bfc8a921ec1d0b3007c22e063908a
- SPAWN-002 package-reviewer · modelo openai-codex/gpt-5.6-terra · effort high · route dec1_4ac1490e0de390cde859378cf5ec0c4d
- SPAWN-003 repair-agent · modelo anthropic/opus · effort medium · route run1_ff614065d37db6f73429ef94f1053673
- SPAWN-004 delta-reviewer · modelo openai-codex/gpt-5.6-terra · effort high · route dec1_c4cd7f80460411b7d4270983cfcdf7ea

context pack: `docs/specs/022-disponibilidad-real/context/P1-registro-de-proveedores.md`

↩ [[features/022-disponibilidad-real|022-disponibilidad-real]]
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
