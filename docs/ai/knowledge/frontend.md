# Conocimiento acumulado — Frontend y UX

> Memoria del "departamento" de frontend para ESTE proyecto. La escribe SOLO `memory-scribe`,
> consolidando las secciones `## Destilado` de los reportes de reviewers/auditores; los demás agentes
> la leen al arrancar (junto con `_global/frontend.md` si existe) y no la editan. Entradas con prefijo
> `[YYYY-MM][feature-id]`. Si el archivo supera ~120 líneas, el scribe compacta en la misma pasada:
> dedupe, generalizar, borrar lo obsoleto. Nunca secretos, tokens, PII ni valores de `.env`.

## Invariantes
- [2026-09][049-identidad-honesta-modelos] Console home is cache-first: first frame reads ModelState cache/absence with no subprocesses; Actualizar estado is the sole measurement path (ADR-0076 §UX, menu() set_agents_app.py:4002).
- [2026-09][049-identidad-honesta-modelos] Apply/restore/pin writers share one exclusive lock; only exact readback yields applied, otherwise pending_apply (PKG-C2 accepted, docs/modules/consola.md).
- [2026-09][049-identidad-honesta-modelos] Honest model identity: session/default/installed/routing are independent evidence layers; footer shows last response, selector prepares next send; plugins are read-only (ADR-0076).

## Errores conocidos y causas raíz

## Decisiones y porqués

## Candidatos a global
