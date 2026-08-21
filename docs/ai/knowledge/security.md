# Conocimiento acumulado — Seguridad

> Memoria del "departamento" de security para ESTE proyecto. La escribe SOLO `memory-scribe`,
> consolidando las secciones `## Destilado` de los reportes de reviewers/auditores; los demás agentes
> la leen al arrancar (junto con `_global/security.md` si existe) y no la editan. Entradas con prefijo
> `[YYYY-MM][feature-id]`. Si el archivo supera ~120 líneas, el scribe compacta en la misma pasada:
> dedupe, generalizar, borrar lo obsoleto. Nunca secretos, tokens, PII ni valores de `.env`.

## Invariantes
- [2026-08][034-cuota-organica-y-writer-barato] Mixed inherit on review-ro + duty in {audit, judge} is forbidden at generate (reviewer independence). Cursor inherit is the parent model. Guards: models_config.py:644-652, generate.py:768-778. Bite: test_mixed_inherit_on_audit_reviewer_is_forbidden_at_generate.
- [2026-08][034-cuota-organica-y-writer-barato] P001 --command must not exempt a heavy role from frontier classification. Exemption is local-gate-runner role only (model.py:683-697). Bite: test_fifth_heavy_implementer_with_p001_command_is_rejected.
- [2026-08][035-panel-honesto-consola-y-tips] FULL_REVIEW_PANEL packages cannot use record-review to bypass mandatory security-auditor; REVIEW_PANEL_REQUIRED rejects all three verdicts (ADR-0065, AC-A.1).

## Errores conocidos y causas raíz
- [2026-08][034-cuota-organica-y-writer-barato] SEC-001 PKG-D: mixed inherit on audit/reviewer passed generate because family() treated inherit as a distinct slug from composer-2.5. Runtime: reviewer shared the writer.
- [2026-08][034-cuota-organica-y-writer-barato] SEC-001 PKG-C: spawn_commands_are_p001 short-circuit let a heavy implementer with a P001 --command skip FRONTIER_CAP_EXHAUSTED (quota bypass).

## Decisiones y porqués

## Candidatos a global
