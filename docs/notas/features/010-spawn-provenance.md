# 010-spawn-provenance

<!-- notas:auto -->
## Estado

- fase: `DONE` · modo: feature · revisión 48
- estado final: **DONE**
- spec: `docs/specs/010-spawn-provenance/spec.md` (hash `e1e9da058144`)

## Criterios de aceptación

- AC-01
- AC-02
- AC-03
- AC-04
- AC-05

## Paquetes

- [[features/010-spawn-provenance/P1-spawn-provenance|P1-spawn-provenance]] — accepted · Mintear spawn_id determinístico en record-spawn, nodo spawn (sin edges) en el grafo de 00…

## Approach y decisiones

- [2026-07-30] gate-runner: El gate-runner fue interrumpido sin un resultado válido. Un debugger aislará el test/proceso colgado y aplicará sólo el arreglo mínimo si la regresión nueva es la causa.
- [2026-07-30] delta-reviewer: delta-reviewer revisa exclusivamente el delta en tests/test_harness.py: replay antes de phase/budget y no-op byte-estable; read-only.
- [2026-07-30] integrator: El paquete está en DELTA_REVIEW; un revisor distinto verificará sólo el cambio de tests/test_harness.py contra P1-REV-001 antes de aceptar 010.
- [2026-07-30] delta-reviewer: Delta review pasó sin hallazgos nuevos. Se cerrará P1-REV-001, se registrará testing y se aceptará 010; recién entonces se marcará 005 como DONE.
- [2026-08-02] integrator: INTEGRATION entry: read-only validation of P1-spawn-provenance against approved spec 010, including the ownership exception granted in HANDOFF-PASO9.
- [2026-08-02] integrator: Integration validation PASS: AC-01..AC-05 verified in tree (replay guard first, spawn nodes edge-free, ownership clean, done_ready resolved_at filter, 5/5 regression tests green).…
- decisión: [[decisiones/2026-07-30 ac-04-supersede-dos-decisiones-previas-sobre-done-ready-y-blockers|AC-04 supersede dos decisiones previas sobre done_ready() y blockers]]

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

- spawns: 11 (máx 12/paquete) · deep review máx 2 ciclos

[[00 - Proyecto|⌂ Proyecto]] · [[features/010-spawn-provenance/grafo|grafo]] · bitácora: `/home/federico/SET-AGENTES/docs/specs/010-spawn-provenance/bitacora.md`

_Actualizado: 2026-08-18T01:16:24+00:00_
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
