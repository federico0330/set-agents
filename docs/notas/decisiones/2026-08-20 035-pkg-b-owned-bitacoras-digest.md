# Excepciones: bitacoras ajenas y estado.md regenerados

<!-- notas:auto -->
- fecha: 2026-08-20 · actor: orchestrator
- alcance: [[features/035-panel-honesto-consola-y-tips|035-panel-honesto-consola-y-tips]] · [[features/035-panel-honesto-consola-y-tips/PKG-B|PKG-B]]

## Contexto

check-owned-paths vs 788eb62 listo 29 out_of_scope: docs/modules/estado.md (impacto PKG-A, sync-notes) y 28 bitacora.md de specs 002-034. Digest/sync-notes del orquestador las toca. El implementer de B no las edito. verify.sh y characterize.py ya pasaron.

## Decisión

update-package --exception docs/modules/estado.md y docs/specs/*/bitacora.md. No ensancha owned_paths. No autoriza editar otras specs.

## Consecuencias

Re-run solo owned-paths + characterize compare. verify.sh no se vuelve a pagar (25 min, VERIFY_PASS).
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
