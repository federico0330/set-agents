# 006-execution-graph

<!-- notas:auto -->
## Estado

- fase: `PACKAGE_ACCEPTED` · modo: feature · revisión 51
- spec: `docs/specs/006-execution-graph/spec.md` (hash `8772b09bcb1b`)

## Criterios de aceptación

- AC-20
- AC-21
- AC-22
- AC-23
- AC-24
- AC-25
- AC-26
- AC-27
- AC-28
- AC-29

## Paquetes

- [[features/006-execution-graph/P3-graph-view|P3-graph-view]] — accepted · Grafo de ejecución navegable: nodos/aristas derivados en lectura del estado existente, se…

## Approach y decisiones

- [2026-07-30] delta-reviewer: delta-reviewer, foco adversarial en los 2 fixes de seguridad críticos (escaping mermaid) y en PR-01 (atribución de actor)
- [2026-07-30] repair-agent: repair-agent, cuarta ronda, 5 findings (1 ya resuelto sin código, 4 chicos)
- [2026-07-30] delta-reviewer: delta-reviewer, foco en D-03 (re-validación) y D-04 (degradación whole-repo)
- [2026-07-30] spec-challenger: Enmienda del contrato 1.2.0->1.3.0 con AC-30..AC-36 ya aplicada al spec; instanciando spec-challenger antes de create-package.
- [2026-08-02] integrator: INTEGRATION entry: read-only validation of P3-graph-view (ACs 20-29) against approved spec 006, cross-package deps and vault artifacts; produces integration verdict for global gat…
- [2026-08-02] integrator: Integration validation PASS: AC-20..AC-29 verified in tree (graph subcommand, mermaid oracle 0 violations, skeleton exit 0, grafo.md 8/8 clean, WAIVED retired, twin byte-identical…
- decisión: [[decisiones/2026-07-28 feature-006-delivered-outside-state-machine|La feature 006 se entrego sin archivo de estado (violacion file-first, detectada despues)]]
- decisión: [[decisiones/2026-07-30 p3-graph-view-abre-el-tracking-de-la-feature-006-sin-backfillear-p1-p2|P3-graph-view abre el tracking de la feature 006 sin backfillear P1/P2]]
- decisión: [[decisiones/2026-07-30 graph-whole-repo-cross-level-id-collision-fails-closed|Colisión de id cross-nivel en modo whole-repo del grafo queda fail-closed, no resuelta]]
- decisión: [[decisiones/2026-07-30 graph-d04-degradation-edge-cases-deferred|3 hallazgos low derivados de la ronda 4 de repair quedan como deuda, no reparados]]
- decisión: [[decisiones/2026-07-30 006-evidencia-de-consistencia-whole-repo-registrada-fase-se-queda-en-package-accepted|006 evidencia de consistencia whole-repo registrada, fase se queda en PACKAGE_ACCEPTED]]

## Qué falta

- → `INTEGRATION` — all packages accepted

## Presupuestos

- spawns: 9 (máx 12/paquete) · deep review máx 2 ciclos

[[00 - Proyecto|⌂ Proyecto]] · [[features/006-execution-graph/grafo|grafo]] · bitácora: `/home/federico/SET-AGENTS/docs/specs/006-execution-graph/bitacora.md`

_Actualizado: 2026-08-02T14:44:35+00:00_
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
