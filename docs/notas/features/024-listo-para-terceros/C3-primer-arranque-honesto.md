# 024-listo-para-terceros · C3-primer-arranque-honesto

<!-- notas:auto -->
## Motivo

- objetivo: Que el primer arranque de un tercero diga que hacer en vez de morir mudo
- complejidad: medium
- paths: `install.sh`, `ai/scripts/install.py`, `ai/scripts/routing_core`, `tests`, `docs/adr`
- depende de: C2-modelstoml-neutro

## Tareas

- [x] El loop infinito de install.sh con --yes (AC-06) (completed) · unittest: 1116 OK / 3 skips (orquestador); verify.sh VERIFY_PASS; build.sh --check BUILD_CHECK_PASS; config de codex del usuario intacto
- [x] ROUTING_UNCONFIGURED aditivo cuando todo fue PROVIDER_UNAUTHENTICATED (AC-07) (completed) · unittest: 1116 OK / 3 skips (orquestador); verify.sh VERIFY_PASS; build.sh --check BUILD_CHECK_PASS; config de codex del usuario intacto
- [x] Dejar de reescribir los globales del usuario sin diff ni consentimiento (AC-08) (completed) · unittest: 1116 OK / 3 skips (orquestador); verify.sh VERIFY_PASS; build.sh --check BUILD_CHECK_PASS; config de codex del usuario intacto

## Recorrido

- gate `unittest-suite`: pass
- gate `verify-sh`: pass
- gate `build-check`: pass
- gate `git-diff-check`: pass

## Spawns

- SPAWN-001 implementer · modelo anthropic/opus · effort medium · route run1_8f2259ea8e3cee55ff1059f6f2a5b1c0

context pack: `docs/specs/024-listo-para-terceros/context/C3-primer-arranque-honesto.md`

↩ [[features/024-listo-para-terceros|024-listo-para-terceros]]
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
