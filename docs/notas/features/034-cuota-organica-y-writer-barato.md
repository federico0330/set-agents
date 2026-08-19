# 034-cuota-organica-y-writer-barato

<!-- notas:auto -->
## Estado

- fase: `DONE` · modo: feature · revisión 159
- estado final: **DONE**
- spec: `docs/specs/034-cuota-organica-y-writer-barato/spec.md` (hash `539a4ff6b58b`)

## Criterios de aceptación

- AC-A.1
- AC-A.2
- AC-A.3
- AC-A.4
- AC-A.5
- AC-A.6
- AC-B.1
- AC-B.2
- AC-B.3
- AC-B.4
- AC-B.5
- AC-B.6
- AC-B.7
- AC-C.1
- AC-C.2
- AC-C.3
- AC-C.4
- AC-C.5
- AC-C.6
- AC-D.1
- AC-D.2
- AC-D.3
- AC-D.4
- AC-D.5
- AC-D.6

## Paquetes

- [[features/034-cuota-organica-y-writer-barato/PKG-A|PKG-A]] — accepted · Ruteo organico enforceable: init scoped/feature exige --risk-signal; 1-3 sin senal no ent…
- [[features/034-cuota-organica-y-writer-barato/PKG-B|PKG-B]] — accepted · Escritor barato/free que cumple tools; un salvage pesado por paquete; test -fast reescrit…
- [[features/034-cuota-organica-y-writer-barato/PKG-C|PKG-C]] — accepted · Techo frontier 4/16 distinto de max_spawns; percent green-on-first-attempt en cost-report…
- [[features/034-cuota-organica-y-writer-barato/PKG-D|PKG-D]] — accepted · Pins Cursor por rol desde models.toml; generate.py deja de forzar inherit; 032 AC-06 supe…

## Approach y decisiones

- ruteo PKG-A: cursor-host native subagent; no --route-decide (032); inherit
- ruteo PKG-B: cursor-host native subagent; no --route-decide (032); inherit
- ruteo PKG-C: cursor-host native subagent; no --route-decide (032); inherit
- ruteo PKG-D: cursor-host native subagent; no --route-decide (032); inherit
- [2026-08-19] delta-reviewer: delta-reviewer inherit. Focus generate.py:768-778 models_config.py:644-652 test_mixed_inherit_on_audit_reviewer_is_forbidden_at_generate. Same-model degradation. No --route-decide…
- [2026-08-19] orchestrator: The last package pins Cursor frontmatter per role and rejects inherit on reviewers because inherit is the parent model, not a second family. Repair added that guard; delta re-ran …
- [2026-08-19] integrator: integrator inherit. All packages accepted. Write docs/specs/034-cuota-organica-y-writer-barato/evidence/INTEGRATION.md. Run verify.sh via heartbeat-run. module-impact-detect PKG-D…
- [2026-08-19] gate-runner: gate-runner inherit. heartbeat-run verify.sh after two separation bites retargeted to cheap BASE. Not P001. No --route-decide. No Engram.
- [2026-08-19] adversarial-judge: adversarial-judge inherit. Evidence docs/specs/034-cuota-organica-y-writer-barato/evidence/. VERIFY_PASS 1363/13m46s. Same-model degradation. No --route-decide. No Engram.
- [2026-08-19] orchestrator: Feature 034 is DONE. Four accepted packages, JUDGE_PASS, verify.sh 1363 tests green. Engram stays a no-goal because the vault is already mandatory. Cursor inherit on a reviewer di…
- decisión: [[decisiones/2026-08-19 034-slice-cuota-plus-organic|034 slice: cuota + ruteo orgánico; Engram no entra]]
- decisión: [[decisiones/2026-08-19 034-engram-no-goal-obsidian|Engram no-goal: el vault Obsidian ya es el contexto]]
- decisión: [[decisiones/2026-08-19 034-pkg-a-owned-path-exceptions|Excepciones de ownership PKG-A: docs vivos, spec 034 y suciedad 033]]
- decisión: [[decisiones/2026-08-19 034-pkg-b-owned-path-exceptions|Excepciones de ownership PKG-B: lifecycle, espejos y docs vivos]]
- decisión: [[decisiones/2026-08-19 034-pkg-b-triage-skill-preexisting|PKG-B waiver del skill de triage que ya cambio el lote anterior]]
- decisión: [[decisiones/2026-08-19 034-pkg-c-owned-path-exceptions|Excepciones PKG-C: suciedad de A/B, espejos y docs]]
- decisión: [[decisiones/2026-08-19 034-pkg-d-owned-path-exceptions|Excepciones PKG-D: arboles emitidos y suciedad A/B/C]]
- decisión: [[decisiones/2026-08-19 034-skip-test-writer-bites-already-landed|No spawn test-writer: cada AC ya tiene mordida]]
- decisión: [[decisiones/2026-08-19 034-memory-scribe-sin-record-spawn|memory-scribe al cierre sin gastar el techo 12]]

## Convenciones

| Eje | Origen | Stance | Umbral | Siguiente | Revisit |
|---|---|---|---|---|---|
| data-store | adr | JSON de feature-state existente (ADR-0047); no hay store nuevo ni vector |  |  |  |
| api-gateway | n/a | sin API publica; harness local |  |  |  |
| deploy-platform | adr | git clone mas ./build.sh --install en la maquina del desarrollador |  |  |  |
| audience | notas | Federico operando el harness en Cursor y OpenCode/Claude/Codex |  |  |  |
| embeddings | n/a | sin embeddings; contexto es vault Obsidian markdown |  |  |  |
| realtime | n/a | sin realtime; comandos batch y spawns |  |  |  |
| mobile | n/a | sin superficie mobile |  |  |  |
| auth | n/a | sin sistema de auth nuevo |  |  |  |
| cost | notas | cuota de modelos es el eje del slice: escritor barato, techo frontier 4/16 |  |  |  |
| legal | n/a | herramienta interna; sin datos de terceros ni ToS nuevo |  |  |  |

## Qué falta

- _nada pendiente_ ✅

## Presupuestos

- spawns: 34 (máx 12/paquete) · deep review máx 2 ciclos

[[00 - Proyecto|⌂ Proyecto]] · [[features/034-cuota-organica-y-writer-barato/grafo|grafo]] · bitácora: `/home/federico/SET-AGENTES/docs/specs/034-cuota-organica-y-writer-barato/bitacora.md`

_Actualizado: 2026-08-19T18:29:58+00:00_
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
