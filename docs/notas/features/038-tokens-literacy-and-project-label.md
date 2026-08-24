# 038-tokens-literacy-and-project-label

<!-- notas:auto -->
## Estado

- fase: `DONE` · modo: scoped · revisión 30
- estado final: **DONE**
- spec: `docs/specs/038-tokens-literacy-and-project-label/spec.md` (hash `a69e5f8c1a91`)

## Criterios de aceptación

- AC-01
- AC-02
- AC-03
- AC-04
- AC-05

## Paquetes

- [[features/038-tokens-literacy-and-project-label/PKG-1|PKG-1]] — accepted · Cap always-on doctrine, code literacy, project_label, cost-report per encargo

## Approach y decisiones

- ruteo PKG-1: single bounded public-contract package already implemented in this turn
- [2026-08-24] implementer: PKG-1: sanitize_project_label + write_app_config; merge_note hub H1; always-on capped with ADR-0069 pointer; orchestrator/architect Code literacy; collect_engagements/render_engag…
- [2026-08-24] package-reviewer: Read-only package-reviewer vs AC-01..05, ADR-0069, working-tree diff vs HEAD. Writer was cursor/grok-4.6; reviewer uses gpt-5.6-sol (different family). Record degradation if pin d…
- [2026-08-24] finding-verifier: finding-verifier vs PKG1-TEST-01/02/03. Medium finding PKG1-TEST-02 is the one that requires a verdict. Writer grok-4.6, reviewer gpt-5.6-sol; verifier should be a different pass …
- [2026-08-24] repair-agent: PKG1-TEST-01/02/03: extended test_project_label_renames_hub_title (empty --project-label), test_always_on_doctrine (phrases including cursor), test_orchestrator_code_literacy (arc…
- [2026-08-24] delta-reviewer: DELTA_REVIEW: tests/test_harness.py only. Confirm empty project_label, cursor phrase pins, architect flow+pseudocode+file:line. Do not re-review 036/037. Writer grok-4.6; delta us…
- [2026-08-24] orchestrator: 038 DONE. PKG-1 accepted after package-reviewer repair_required (3 test gaps), finding-verifier upheld all three (independence degraded: same GPT family as reviewer), repair in te…

## Convenciones

| Eje | Origen | Stance | Umbral | Siguiente | Revisit |
|---|---|---|---|---|---|
| data-store | n/a | no new store: config.toml and feature JSON already exist | - | - | - |
| api-gateway | n/a | no HTTP surface; local CLI and markdown doctrine | - | - | - |
| deploy-platform | n/a | install via ./build.sh --install on the developer machine | - | - | - |
| audience | notas | harness operators reading chat, hub notes, and cost-report | - | - | - |
| embeddings | n/a | no embeddings | - | - | - |
| realtime | n/a | no realtime | - | - | - |
| mobile | n/a | no mobile surface | - | - | - |
| auth | n/a | no new auth | - | - | - |
| cost | n/a | reduce always-on tokens; measure sessions per encargo without inventing token totals | - | - | - |
| legal | n/a | no PII; project_label is a free display string | - | - | - |

## Qué falta

- _nada pendiente_ ✅

## Presupuestos

- spawns: 5 (máx 8/paquete) · deep review máx 2 ciclos

[[00 - Proyecto|⌂ Proyecto]] · [[features/038-tokens-literacy-and-project-label/grafo|grafo]] · bitácora: `/home/federico/SET-AGENTES/docs/specs/038-tokens-literacy-and-project-label/bitacora.md`

_Actualizado: 2026-08-24T15:49:14+00:00_
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
