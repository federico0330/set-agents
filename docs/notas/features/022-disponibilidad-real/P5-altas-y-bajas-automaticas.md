# 022-disponibilidad-real · P5-altas-y-bajas-automaticas

<!-- notas:auto -->
## Motivo

- objetivo: Que activar una suscripcion alcance para usarla, y que darla de baja se note, sin tocar nada
- complejidad: medium
- paths: `ai/scripts/routing_core/catalog.py`, `ai/scripts/set_agents_app.py`, `tests`
- depende de: P4-proveedores-del-usuario

## Tareas

- [x] Verificacion empirica del CLI id: se acepta solo si el CLI contesto bien (AC-16) (completed) · unittest discover -s tests: 1065 OK / 3 skips (corrida del orquestador); verify.sh: VERIFY_PASS; build.sh --check: GLOBAL_TREE_SYNC_OK + BUILD_CHECK_PASS
- [x] La baja simetrica y automatica; el registro es memoria, no autorizacion (AC-17) (completed) · unittest discover -s tests: 1065 OK / 3 skips (corrida del orquestador); verify.sh: VERIFY_PASS; build.sh --check: GLOBAL_TREE_SYNC_OK + BUILD_CHECK_PASS
- [x] --provider-verify para modelos que ya no responden, nunca dentro de route() (AC-18) (completed) · unittest discover -s tests: 1065 OK / 3 skips (corrida del orquestador); verify.sh: VERIFY_PASS; build.sh --check: GLOBAL_TREE_SYNC_OK + BUILD_CHECK_PASS
- [x] listed_by_provider vs usable_after_ceiling en las TRES superficies (AC-19) (completed) · unittest discover -s tests: 1065 OK / 3 skips (corrida del orquestador); verify.sh: VERIFY_PASS; build.sh --check: GLOBAL_TREE_SYNC_OK + BUILD_CHECK_PASS

## Recorrido

- review: pass (0 hallazgos)
- testing: pass
- runtime QA: pass
- gate `unittest-suite`: pass
- gate `verify-sh`: pass
- gate `build-check`: pass
- gate `git-diff-check`: pass

## Spawns

- SPAWN-001 implementer · modelo anthropic/opus · effort medium · route run1_12758daeb52b60685e0f17bd7c39cd40
- SPAWN-002 package-reviewer · modelo openai-codex/gpt-5.6-terra · effort high · route dec1_7513f638ac3053cecd70fd11a0788c70

context pack: `docs/specs/022-disponibilidad-real/context/P5-altas-y-bajas-automaticas.md`

↩ [[features/022-disponibilidad-real|022-disponibilidad-real]]
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
