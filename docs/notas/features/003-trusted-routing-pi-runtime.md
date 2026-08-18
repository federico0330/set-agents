# 003-trusted-routing-pi-runtime

<!-- notas:auto -->
## Estado

- fase: `DONE` · modo: feature · revisión 80
- estado final: **DONE**
- spec: `docs/specs/003-trusted-routing-pi-runtime/spec.md` (hash `433771847056`)

## Criterios de aceptación

- AC-01
- AC-01a
- AC-02
- AC-02a
- AC-03
- AC-03a
- AC-04
- AC-05
- AC-06
- AC-07
- AC-07a
- AC-08
- AC-09

## Paquetes

- [[features/003-trusted-routing-pi-runtime/P1R-trusted-routing|P1R-trusted-routing]] — accepted · Trusted routing-v2: immutable catalog, trusted facts, private SQLite lifecycle, and simul…

## Approach y decisiones

- ruteo P1R-trusted-routing: Hosted implementation required for security-critical trust boundaries, SQLite atomic lifecycle, crash/concurrency behav…
- [2026-07-24] delta-reviewer: Final delta verdict=repair_required: FD-001 critical, FD-002..FD-009 high, FD-010 medium. Gates pass but counterexamples remain; no scope creep/full review required.
- [2026-07-25] orchestrator: User-authorized fresh budget for R3: max_spawns_per_package 13->16 (repair-agent, gate-runner, delta-reviewer). Direct state edit because the harness exposes no budget command; tr…
- [2026-07-25] repair-agent: PACKAGE_REPAIR R3, spawn 14/16 (Claude Fable in-session): FD-003 per-pair probe parsers with graceful degradation; FD-005 canonical DDL equality; FD-002 conservative risk max; FD-…
- [2026-07-25] gate-runner: DELTA_REVIEW R3 gate-runner read-only, spawn 15/16: focused suite, named regressions, setup_models, py_compile, all GateSpecs incl. new v2:routing-unit, verify.sh >=120s window, C…
- [2026-07-25] delta-reviewer: DELTA_REVIEW R3 delta-reviewer read-only, spawn 16/16 (last of authorized budget): decide resolved|open per FD-001..FD-010 against the R3-amended contract (decision r3-threat-mode…
- [2026-07-25] orchestrator: R3 complete within authorized budget (spawns 14-16, cycle 3/3): FD-001..FD-010 closed (6 resolved, 4 resolved-by-approved-exception per r3-threat-model-amendment); r3-final-verifi…
- decisión: [[decisiones/2026-07-24 p1r-third-architecture-attempt|Excepción autorizada: tercer intento de arquitectura P1R]]
- decisión: [[decisiones/2026-07-24 approve-p1r-contract-2|Aprobar contrato P1R 2.0]]
- decisión: [[decisiones/2026-07-24 p1r-r1-delta-block|P1R blocked after the authorized R1 delta review]]
- decisión: [[decisiones/2026-07-24 authorize-p1r-r2|User authorizes a second P1R repair cycle]]
- decisión: [[decisiones/2026-07-24 p1r-r2-authorized|Second repair cycle authorized by user]]
- decisión: [[decisiones/2026-07-24 p1r-final-delta-block|P1R remains blocked after fresh independent delta review]]
- decisión: [[decisiones/2026-07-25 r3-threat-model-amendment|R3: enmienda del threat model de routing-v2]]
- decisión: [[decisiones/2026-07-29 record-spawn-budget-does-not-exempt-integration-bookkeeping|record-spawn cuenta la narracion de INTEGRATION contra el presupuesto de implementacion de un paquete ya aceptado]]
- decisión: [[decisiones/2026-07-29 done-ready-does-not-filter-resolved-blockers|done_ready trata cualquier blocker historico como abierto para siempre, incluso ya resuelto]]

## Convenciones

| Eje | Origen | Stance | Umbral | Siguiente | Revisit |
|---|---|---|---|---|---|
| data-store | - | - | - | - | - |
| api-gateway | - | - | - | - | - |
| deploy-platform | - | - | - | - | - |
| audience | - | - | - | - | - |
| embeddings | - | - | - | - | - |
| realtime | - | - | - | - | - |
| mobile | - | - | - | - | - |
| auth | - | - | - | - | - |
| cost | - | - | - | - | - |
| legal | - | - | - | - | - |

## Qué falta

- _nada pendiente_ ✅

## Presupuestos

- spawns: 16 (máx 16/paquete) · deep review máx 3 ciclos

[[00 - Proyecto|⌂ Proyecto]] · [[features/003-trusted-routing-pi-runtime/grafo|grafo]] · bitácora: `/home/federico/SET-AGENTES/docs/specs/003-trusted-routing-pi-runtime/bitacora.md`

_Actualizado: 2026-07-29T17:13:45+00:00_
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
