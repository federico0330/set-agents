# Conocimiento acumulado — Arquitectura y patrones

> Memoria del "departamento" de architecture para ESTE proyecto. La escribe SOLO `memory-scribe`,
> consolidando las secciones `## Destilado` de los reportes de reviewers/auditores; los demás agentes
> la leen al arrancar (junto con `_global/architecture.md` si existe) y no la editan. Entradas con prefijo
> `[YYYY-MM][feature-id]`. Si el archivo supera ~120 líneas, el scribe compacta en la misma pasada:
> dedupe, generalizar, borrar lo obsoleto. Nunca secretos, tokens, PII ni valores de `.env`.

## Invariantes
- [2026-08][034-cuota-organica-y-writer-barato] Cursor inherit is the parent model, not a distinct family. Mixed inherit on review-ro+audit/judge shares the writer. Dual fail-closed: models_config.py:644-652 (load_roles) and generate.py:768-778 (validate_cursor_target). Bite: test_mixed_inherit_on_audit_reviewer_is_forbidden_at_generate.
- [2026-08][034-cuota-organica-y-writer-barato] Frontier cap is not MODE_BUDGETS. scoped.max_spawns_per_package stays 8 (model.py:125). Caps 4/package and 16/feature are constants beside it (model.py:133-134). Exhaustion is FRONTIER_CAP_EXHAUSTED, never raising max_spawns.
- [2026-08][034-cuota-organica-y-writer-barato] is_frontier_spawn (model.py:683-697): --model present, model not cheap default, role not local-gate-runner. commands do not exempt. Honest P001 exemption is the local-gate-runner role check only.
- [2026-08][034-cuota-organica-y-writer-barato] Cursor is not in RUNTIMES. --route-decide stays forbidden on this host. repair-agent pin stays cheap; salvage is an invocation --model override, not a heavy role pin.
- [2026-08][034-cuota-organica-y-writer-barato] cheap_consecutive_failures is a feature counter; reset only on package green-on-first (all required gates pass, salvage is None, package never struck) at PACKAGE_GATES to PACKAGE_REVIEW (model.py:700-711). A partial named-gate pass must not reset.
- [2026-08][034-cuota-organica-y-writer-barato] record-spawn --salvage requires --model before mint (SALVAGE_MODEL_REQUIRED, feature-state.py:425-432). FRONTIER_CAP_EXHAUSTED check runs before salvage mint and spawn increment (feature-state.py:440-462).
- [2026-08][034-cuota-organica-y-writer-barato] Organic init: scoped/feature without --risk-signal die RISK_SIGNAL_REQUIRED and write no JSON (cli_lifecycle.py:155-157). Bare init stays fail-closed because CLI --mode default is scoped.

## Errores conocidos y causas raíz
- [2026-08][034-cuota-organica-y-writer-barato] family() returns the raw slug inherit, so mixed [areas.audit].cursor=inherit with implementer composer-2.5 passed load_roles: inherit looked distinct. Universal-inherit died only when ALL pins were inherit. Root: at Cursor runtime inherit is the parent model (reviewer shares writer).
- [2026-08][034-cuota-organica-y-writer-barato] is_frontier_spawn short-circuited on spawn_commands_are_p001 for any role. A heavy implementer/repair-agent/package-reviewer with --command 'git diff --check' was classified non-frontier; the 5th spawn and salvage-after-cap skipped FRONTIER_CAP_EXHAUSTED. Fix: deleted that short-circuit.
- [2026-08][034-cuota-organica-y-writer-barato] cli_repair reset cheap_consecutive_failures on the first passing named gate of a still-open package. PKG-01 fail + PKG-02 pass-then-fail collapsed consecutive to 1 instead of 2.
- [2026-08][034-cuota-organica-y-writer-barato] record-spawn --salvage minted package.salvage with model empty when --model was omitted, and still spent attempts.spawns.

## Decisiones y porqués
- [2026-08][034-cuota-organica-y-writer-barato] Engram is no-goal of 034 because the Obsidian vault (docs/notas/) is already mandatory (ADR-0012 / ADR-0056). Capital Engram absent from 034 product surface. Managed MCP engram starts disabled (generate.py:640). A spawn that does not read the vault is a 005/025 defect, not a reason to copy Engram. Decision already logged as 034-engram-no-goal-obsidian; not re-logged.
- [2026-08][034-cuota-organica-y-writer-barato] 033 product (wizard/tui/lanes) was not reopened by 034.
- [2026-08][034-cuota-organica-y-writer-barato] family() keeps returning the raw slug (coord may pin inherit; the helper has no writer pin to collapse against). Mixed inherit is a generate-time duty check (review-ro + audit/judge), not a family() collapse.
- [2026-08][034-cuota-organica-y-writer-barato] Cheap code-rw BASE is free/rank-0 (opencode/deepseek-v4-flash-free / Cursor composer-2.5), not a -fast suffix. CHEAP_IMPLEMENT_MODEL matches that cell (models.toml:121-134, model.py:135). Green-on-first is derived in cost-report section 2, not a JSON field; salvage-green is not first-attempt.

## Candidatos a global
- [2026-08][034-cuota-organica-y-writer-barato] Cursor inherit is the parent chat model, not a distinct family — mixed inherit on a reviewer shares the writer. Guard at generate (duty + inherit), not by collapsing family().
- [2026-08][034-cuota-organica-y-writer-barato] Quota classifiers that exempt on command content (e.g. P001 git diff --check) are bypasses; exempt by role, not by argv.
