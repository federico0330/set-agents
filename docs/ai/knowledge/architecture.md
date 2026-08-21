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
- [2026-08][035-panel-honesto-consola-y-tips] record-review is the legitimate single-reviewer door (SINGLE_REVIEW_PANEL / small+low). FULL_REVIEW_PANEL rejects pass, repair_required, and blocked with REVIEW_PANEL_REQUIRED; correct path is start-review-panel → record-subreview × role → finalize-review-panel (cli_review.py:21-63, model.py:95-96).
- [2026-08][035-panel-honesto-consola-y-tips] Extraction ceiling for set_agents_app.py is HarnessTests._import finally restoring sys.modules (tests/test_harness.py:792-796), not missing registration. After _import returns, sys.modules["set_agents_app"] is not the test object; moved functions lose __globals__ identity with patch.object targets; re-export does not fix (ADR-0066).
- [2026-08][035-panel-honesto-consola-y-tips] PKG-B path (b): zero commands moved from set_agents_app.py; durable outputs are the 16-row command→dependency residue matrix and three-channel CLI characterization under evidence/PKG-B-characterization/ (ADR-0066, PKG-B Destilado).
- [2026-08][035-panel-honesto-consola-y-tips] Three-channel CLI characterization must run outside the golden suite: tests/__init__.py audit hook and Popen replacement measure the CLI under a modified runtime, not production CLI (ADR-0066 §5).
- [2026-08][035-panel-honesto-consola-y-tips] MODE_BUDGETS["scoped"]["max_spawns_per_package"] stays 8 at model.py:126; hitting spawn ceiling for mandatory FULL panel is HUMAN_DECISION_REQUIRED, not raising the constant (ADR-0065 rejected option, AC-A.8).
- [2026-08][035-panel-honesto-consola-y-tips] record-review membership/findings guards raise StateError before attempts.deep_review_cycles increment — rejection never consumes a review cycle or blocks the feature via block_with_reason (ADR-0065 decision 6, cli_review.py:46).

## Errores conocidos y causas raíz
- [2026-08][034-cuota-organica-y-writer-barato] family() returns the raw slug inherit, so mixed [areas.audit].cursor=inherit with implementer composer-2.5 passed load_roles: inherit looked distinct. Universal-inherit died only when ALL pins were inherit. Root: at Cursor runtime inherit is the parent model (reviewer shares writer).
- [2026-08][034-cuota-organica-y-writer-barato] is_frontier_spawn short-circuited on spawn_commands_are_p001 for any role. A heavy implementer/repair-agent/package-reviewer with --command 'git diff --check' was classified non-frontier; the 5th spawn and salvage-after-cap skipped FRONTIER_CAP_EXHAUSTED. Fix: deleted that short-circuit.
- [2026-08][034-cuota-organica-y-writer-barato] cli_repair reset cheap_consecutive_failures on the first passing named gate of a still-open package. PKG-01 fail + PKG-02 pass-then-fail collapsed consecutive to 1 instead of 2.
- [2026-08][034-cuota-organica-y-writer-barato] record-spawn --salvage minted package.salvage with model empty when --model was omitted, and still spent attempts.spawns.
- [2026-08][035-panel-honesto-consola-y-tips] Stale docstrings (vault_ops.py, routing_cli.py, project_identity.py) claimed _import() loads without sys.modules registration; the real ceiling is finally restoring sys.modules after exec (ADR-0066).
- [2026-08][035-panel-honesto-consola-y-tips] PKG-B characterization ROOT=parents[4] pointed at wrong directory; baseline and after both failed with the same missing-file error, producing a false-green three-channel compare. Fix: parents[5] plus _require_cli() abort (PKG-B-repair F001).
- [2026-08][035-panel-honesto-consola-y-tips] POSIX RoutingStore ignores HOME; hermetic routing characterization requires SET_AGENTS_ROUTING_TEST_ROOT in child env allowlist, not HOME override (PKG-B-repair F002, set_agents_app.py:68-73).
- [2026-08][035-panel-honesto-consola-y-tips] Child characterization must use _build_child_env() allowlist (PATH, HOME, TMPDIR, LANG/LC_ALL, TERM, GIT_TERMINAL_PROMPT, SET_AGENTS_STATE, SET_AGENTS_ROUTING_TEST_ROOT), not os.environ.copy() (PKG-B-repair F006).

## Decisiones y porqués
- [2026-08][034-cuota-organica-y-writer-barato] Engram is no-goal of 034 because the Obsidian vault (docs/notas/) is already mandatory (ADR-0012 / ADR-0056). Capital Engram absent from 034 product surface. Managed MCP engram starts disabled (generate.py:640). A spawn that does not read the vault is a 005/025 defect, not a reason to copy Engram. Decision already logged as 034-engram-no-goal-obsidian; not re-logged.
- [2026-08][034-cuota-organica-y-writer-barato] 033 product (wizard/tui/lanes) was not reopened by 034.
- [2026-08][034-cuota-organica-y-writer-barato] family() keeps returning the raw slug (coord may pin inherit; the helper has no writer pin to collapse against). Mixed inherit is a generate-time duty check (review-ro + audit/judge), not a family() collapse.
- [2026-08][034-cuota-organica-y-writer-barato] Cheap code-rw BASE is free/rank-0 (opencode/deepseek-v4-flash-free / Cursor composer-2.5), not a -fast suffix. CHEAP_IMPLEMENT_MODEL matches that cell (models.toml:121-134, model.py:135). Green-on-first is derived in cost-report section 2, not a JSON field; salvage-green is not first-attempt.
- [2026-08][035-panel-honesto-consola-y-tips] required_reviewers absence resolves panel from complexity+risk (resolve_package_risk → required_reviewers_for); complexity absent defaults to medium → FULL panel fail-safe preserved (ADR-0065 DEC-ABSENCE, model.py:548-575).
- [2026-08][035-panel-honesto-consola-y-tips] BLOCKING_FINDING_OPEN blocks record-review --verdict pass only on SINGLE panel, same has_open_findings predicate as finalize-review-panel (critical/high/medium), including --finding on the same call (ADR-0065 decision 3, cli_review.py:158-160).
- [2026-08][035-panel-honesto-consola-y-tips] PKG-B closes extraction at path (b): fixing _import helper or rewriting twelve patch sites requires a separate slice with tests/test_harness.py in owned_paths (ADR-0066 point 6).
- [2026-08][035-panel-honesto-consola-y-tips] Membership guard lives only in record-review/finalize-review-panel writers, not package_accept_ready — avoids re-judging historical DONE packages (ADR-0065 DEC-LEGACY, AC-A.6).

## Candidatos a global
- [2026-08][034-cuota-organica-y-writer-barato] Cursor inherit is the parent chat model, not a distinct family — mixed inherit on a reviewer shares the writer. Guard at generate (duty + inherit), not by collapsing family().
- [2026-08][034-cuota-organica-y-writer-barato] Quota classifiers that exempt on command content (e.g. P001 git diff --check) are bypasses; exempt by role, not by argv.
