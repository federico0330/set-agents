# 024-listo-para-terceros · C2-modelstoml-neutro

<!-- notas:auto -->
## Motivo

- objetivo: models.toml deja de fijar las suscripciones de una persona y el usuario tiene overlay propio
- complejidad: medium
- paths: `models.toml`, `ai/scripts/models_config.py`, `tests`, `docs/adr`
- depende de: C1-estado-fuera-del-producto

## Tareas

- [x] [subscriptions] pasa a ausente = auto (AC-03) (completed) · unittest: 1113 OK / 3 skips (orquestador); verify.sh VERIFY_PASS; build.sh + --check BUILD_CHECK_PASS
- [x] El small model deja de exigir Zen en local, y la lane local se renombra a lo que es (AC-04) (completed) · unittest: 1113 OK / 3 skips (orquestador); verify.sh VERIFY_PASS; build.sh + --check BUILD_CHECK_PASS
- [x] Overlay de config del usuario en STATE_DIR, que desbloquea --update (AC-05) (completed) · unittest: 1113 OK / 3 skips (orquestador); verify.sh VERIFY_PASS; build.sh + --check BUILD_CHECK_PASS

## Recorrido

- review: pass (0 hallazgos)
- testing: pass
- runtime QA: pass
- gate `unittest-suite`: pass
- gate `verify-sh`: pass
- gate `build-check`: pass
- gate `git-diff-check`: pass

## Spawns

- SPAWN-001 implementer · modelo anthropic/opus · effort medium · route run1_c9272b14d418db96b5ae8a49c655d671

context pack: `docs/specs/024-listo-para-terceros/context/C2-modelstoml-neutro.md`

↩ [[features/024-listo-para-terceros|024-listo-para-terceros]]
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
