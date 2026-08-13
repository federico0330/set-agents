# 022-disponibilidad-real · P2-techo-catalogo-tri-estado

<!-- notas:auto -->
## Motivo

- objetivo: Que [catalog] deje de ser requisito de configuracion, sin abrir la puerta a que entre cualquier cosa
- complejidad: medium
- paths: `ai/scripts/routing_core/catalog.py`, `models.toml`, `tests/test_routing.py`
- depende de: P1-registro-de-proveedores

## Tareas

- [x] resolve_ceiling tri-estado acotado a zen y go, consumido por los tres sitios (AC-04) (completed) · unittest discover -s tests: 990 OK / 3 skips (corrida del orquestador); verify.sh: VERIFY_PASS; build.sh --check: GLOBAL_TREE_SYNC_OK + BUILD_CHECK_PASS; git diff --check limpio
- [x] Las cuatro capas que impiden que entre cualquier cosa, cada una con su test (AC-05) (completed) · unittest discover -s tests: 990 OK / 3 skips (corrida del orquestador); verify.sh: VERIFY_PASS; build.sh --check: GLOBAL_TREE_SYNC_OK + BUILD_CHECK_PASS; git diff --check limpio
- [x] CATALOG_CEILING_REQUIRED nombrado en vez del generico (AC-06) (completed) · unittest discover -s tests: 990 OK / 3 skips (corrida del orquestador); verify.sh: VERIFY_PASS; build.sh --check: GLOBAL_TREE_SYNC_OK + BUILD_CHECK_PASS; git diff --check limpio

## Recorrido

- review: pass (0 hallazgos)
- testing: pass
- runtime QA: pass
- gate `unittest-suite`: pass
- gate `verify-sh`: pass
- gate `build-check`: pass
- gate `git-diff-check`: pass

## Spawns

- SPAWN-001 implementer · modelo anthropic/opus · effort medium · route run1_d8520988c6deaa8594f6fca8c700890f
- SPAWN-002 package-reviewer · modelo openai-codex/gpt-5.6-terra · effort high · route dec1_0cbd3fc5548c9fa21a03ea3316d3a9a0

context pack: `docs/specs/022-disponibilidad-real/context/P2-techo-catalogo-tri-estado.md`

↩ [[features/022-disponibilidad-real|022-disponibilidad-real]]
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
