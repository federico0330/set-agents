# 010-spawn-provenance

<!-- notas:auto -->
## Estado

- fase: `PACKAGE_ACCEPTED` · modo: feature · revisión 42
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

- [2026-07-30] gate-runner: gate-runner ejecuta suite completa con timeout explícito, verify.sh y diff-check sobre el delta de tests; no cambia código.
- [2026-07-30] debugger: debugger inspecciona el proceso/test colgado y corrige sólo la causa raíz dentro de tests/test_harness.py si corresponde; luego aporta un comando reproducible.
- [2026-07-30] gate-runner: El gate-runner fue interrumpido sin un resultado válido. Un debugger aislará el test/proceso colgado y aplicará sólo el arreglo mínimo si la regresión nueva es la causa.
- [2026-07-30] delta-reviewer: delta-reviewer revisa exclusivamente el delta en tests/test_harness.py: replay antes de phase/budget y no-op byte-estable; read-only.
- [2026-07-30] integrator: El paquete está en DELTA_REVIEW; un revisor distinto verificará sólo el cambio de tests/test_harness.py contra P1-REV-001 antes de aceptar 010.
- [2026-07-30] delta-reviewer: Delta review pasó sin hallazgos nuevos. Se cerrará P1-REV-001, se registrará testing y se aceptará 010; recién entonces se marcará 005 como DONE.
- decisión: [[decisiones/2026-07-30 ac-04-supersede-dos-decisiones-previas-sobre-done-ready-y-blockers|AC-04 supersede dos decisiones previas sobre done_ready() y blockers]]

## Qué falta

- → `INTEGRATION` — all packages accepted

## Presupuestos

- spawns: 10 (máx 12/paquete) · deep review máx 2 ciclos

[[00 - Proyecto|⌂ Proyecto]] · [[features/010-spawn-provenance/grafo|grafo]] · bitácora: `/home/federico/SET-AGENTES/docs/specs/010-spawn-provenance/bitacora.md`

_Actualizado: 2026-07-30T16:15:59+00:00_
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
