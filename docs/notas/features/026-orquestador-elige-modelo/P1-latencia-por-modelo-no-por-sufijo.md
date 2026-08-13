# 026-orquestador-elige-modelo · P1-latencia-por-modelo-no-por-sufijo

<!-- notas:auto -->
## Motivo

- objetivo: El orquestador deja de estar obligado al sufijo -fast y pasa a un modelo no-GPT de suscripcion
- complejidad: small
- paths: `models.toml`, `tests/test_harness.py`, `docs/adr`

## Tareas

- [x] Reescribir el test de -fast conservando la regla para implementer y product-analyst (AC-01) (completed) · unittest: 1065 OK / 3 skips (orquestador); verify.sh: VERIFY_PASS; build.sh --check: GLOBAL_TREE_SYNC_OK + BUILD_CHECK_PASS; mordida propia: romper implementer da rojo, restaurar da verde
- [x] [areas.coord].opencode a opencode-go/grok-4.5 y opencode/grok-4.5 (AC-02) (completed) · unittest: 1065 OK / 3 skips (orquestador); verify.sh: VERIFY_PASS; build.sh --check: GLOBAL_TREE_SYNC_OK + BUILD_CHECK_PASS; mordida propia: romper implementer da rojo, restaurar da verde
- [x] ADR-0044 con la razon y el limite de la lane codex (AC-03) (completed) · unittest: 1065 OK / 3 skips (orquestador); verify.sh: VERIFY_PASS; build.sh --check: GLOBAL_TREE_SYNC_OK + BUILD_CHECK_PASS; mordida propia: romper implementer da rojo, restaurar da verde

## Recorrido

- review: pass (0 hallazgos)
- testing: pass
- runtime QA: pass
- gate `unittest-suite`: pass
- gate `verify-sh`: pass
- gate `build-check`: pass
- gate `git-diff-check`: pass

## Spawns

- SPAWN-001 implementer · modelo anthropic/opus · effort medium · route run1_7148d21f9aa2e4ab6ed111273f9486db

context pack: `docs/specs/026-orquestador-elige-modelo/context/P1-latencia-por-modelo-no-por-sufijo.md`

↩ [[features/026-orquestador-elige-modelo|026-orquestador-elige-modelo]]
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
