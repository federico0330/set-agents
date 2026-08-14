# 024-listo-para-terceros · C1-estado-fuera-del-producto

<!-- notas:auto -->
## Motivo

- objetivo: Que el estado de Federico deje de viajar en el clon, sin mover el path
- complejidad: medium
- paths: `ai/state.seed`, `.gitignore`, `ai/scripts/check-feature-state.py`, `docs/historia`, `tests`, `docs/adr`

## Tareas

- [x] git mv ai/state a docs/historia y sembrar desde ai/state.seed, manteniendo el path (AC-01) (completed) · unittest: 1110 OK / 3 skips (orquestador); verify.sh VERIFY_PASS con FEATURE_STATE_OK; build.sh --check BUILD_CHECK_PASS
- [x] check-feature-state.py cambia la pregunta a 'desde mi baseline', sin apagar el degradado (AC-02) (completed) · unittest: 1110 OK / 3 skips (orquestador); verify.sh VERIFY_PASS con FEATURE_STATE_OK; build.sh --check BUILD_CHECK_PASS

## Recorrido

- review: pass (0 hallazgos)
- testing: pass
- runtime QA: pass
- gate `unittest-suite`: pass
- gate `verify-sh`: pass
- gate `build-check`: pass
- gate `git-diff-check`: pass

## Spawns

- SPAWN-001 implementer · modelo anthropic/opus · effort medium · route run1_b75accf4527aa0d01ef8cc005380f8ce

context pack: `docs/specs/024-listo-para-terceros/context/C1-estado-fuera-del-producto.md`

↩ [[features/024-listo-para-terceros|024-listo-para-terceros]]
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
