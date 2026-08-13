# 026-orquestador-elige-modelo · P2-modelo-por-instancia

<!-- notas:auto -->
## Motivo

- objetivo: Que el orquestador pueda pedir un modelo para un spawn puntual, sin saltear ninguna barrera
- complejidad: medium
- paths: `ai/scripts/set_agents_app.py`, `ai/scripts/routing_core`, `tests`, `docs/adr`
- depende de: P1-latencia-por-modelo-no-por-sufijo

## Tareas

- [x] Clave nueva en el conjunto cerrado del descriptor (AC-04) (completed) · unittest: 1080 OK / 3 skips (orquestador); verify.sh VERIFY_PASS; build.sh --check GLOBAL_TREE_SYNC_OK + BUILD_CHECK_PASS; barrera de independencia verificada en vivo por el orquestador
- [x] La preferencia entra DESPUES de las exclusiones, con test por barrera (AC-05) (completed) · unittest: 1080 OK / 3 skips (orquestador); verify.sh VERIFY_PASS; build.sh --check GLOBAL_TREE_SYNC_OK + BUILD_CHECK_PASS; barrera de independencia verificada en vivo por el orquestador
- [x] reason_code propio cuando el modelo pedido no es elegible (AC-06) (completed) · unittest: 1080 OK / 3 skips (orquestador); verify.sh VERIFY_PASS; build.sh --check GLOBAL_TREE_SYNC_OK + BUILD_CHECK_PASS; barrera de independencia verificada en vivo por el orquestador
- [x] Efimera: no escribe model-preference.toml ni altera el pin (AC-07) (completed) · unittest: 1080 OK / 3 skips (orquestador); verify.sh VERIFY_PASS; build.sh --check GLOBAL_TREE_SYNC_OK + BUILD_CHECK_PASS; barrera de independencia verificada en vivo por el orquestador

## Recorrido

- review: pass (0 hallazgos)
- testing: pass
- runtime QA: pass
- gate `unittest-suite`: pass
- gate `verify-sh`: pass
- gate `build-check`: pass
- gate `git-diff-check`: pass

## Spawns

- SPAWN-001 implementer · modelo anthropic/opus · effort medium · route run1_629c7c7ec716656891597f662bb47360

context pack: `docs/specs/026-orquestador-elige-modelo/context/P2-modelo-por-instancia.md`

↩ [[features/026-orquestador-elige-modelo|026-orquestador-elige-modelo]]
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
