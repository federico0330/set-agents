# Conocimiento acumulado — Datos e integridad

> Memoria del "departamento" de data para ESTE proyecto. La escribe SOLO `memory-scribe`,
> consolidando las secciones `## Destilado` de los reportes de reviewers/auditores; los demás agentes
> la leen al arrancar (junto con `_global/data.md` si existe) y no la editan. Entradas con prefijo
> `[YYYY-MM][feature-id]`. Si el archivo supera ~120 líneas, el scribe compacta en la misma pasada:
> dedupe, generalizar, borrar lo obsoleto. Nunca secretos, tokens, PII ni valores de `.env`.

## Invariantes
- [2026-09][049-identidad-honesta-modelos] ModelState singular CLI set-agents --model-state; OpenCode-only observation via allowlisted session list + export children; 5s/20 root sessions/1MiB stdout cap; no session_id or transcript in output (ADR-0076, model_state.py).

## Errores conocidos y causas raíz

## Decisiones y porqués

## Candidatos a global
