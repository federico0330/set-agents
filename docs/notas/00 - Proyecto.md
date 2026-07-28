# SET-AGENTES — notas

<!-- notas:auto -->
## Features

- [[features/002-adaptive-pi-orchestration|002-adaptive-pi-orchestration]] — fase `BLOCKED` · paquetes 0/1 · **BLOCKED**
- [[features/003-trusted-routing-pi-runtime|003-trusted-routing-pi-runtime]] — fase `PACKAGE_ACCEPTED` · paquetes 1/1
- [[features/004-adaptive-dispatch|004-adaptive-dispatch]] — fase `DONE` · paquetes 3/3 · **DONE**
- [[features/005-portable-harness|005-portable-harness]] — fase `PACKAGE_ACCEPTED` · paquetes 1/1

## Qué falta

- **002-adaptive-pi-orchestration** ⛔ bloqueo: HUMAN_DECISION_REQUIRED: user-authorized third repair cycle failed final review; five high findings remain and P1 exhau…
- **002-adaptive-pi-orchestration** 5 hallazgos abiertos
- **003-trusted-routing-pi-runtime** → `INTEGRATION` — all packages accepted
- **005-portable-harness** → `INTEGRATION` — all packages accepted

## Decisiones

- [[decisiones/2026-07-28 routing-db-schema4-unmigratable|La DB de routing local no se puede migrar de schema 4 a 5 por el path sancionado]]
- [[decisiones/2026-07-27 p1-pi-project-cwd-propagation|Pi lifecycle propagates project context by explicit cwd]]
- [[decisiones/2026-07-27 global-absolute-path-leak|Pre-existing absolute-path leak in tracked Global/ templates (out of P1 scope, tracked)]]
- [[decisiones/2026-07-27 ac09-ac10-pi-minimal-target-accepted|AC-09/AC-10 literal deviations accepted: minimal pi target + pnpm-store pin]]
- [[decisiones/2026-07-27 t300-pi-lane-feasibility-yes|T-300 spike: P3-pi-lane is FEASIBLE (all four YES)]]
- [[decisiones/2026-07-27 sec-a02-coord-run-closure-accepted|SEC-A02 accepted: coord may terminal/abandon any routing run]]
- [[decisiones/2026-07-26 scope-cheap-tier-and-pi-spike|Alcance 004: tier barato sin opencode/* y P3 condicionado a spike]]
- [[decisiones/2026-07-26 am2-probe-cache-fresh-selected|AM-2: cache de probes filtering-only + re-probe fresco del seleccionado (enmienda a 003/ADR-0005)]]

## Referencias

- `ai/state/STATUS.md` — dashboard técnico
- `docs/adr/` — decisiones formales de arquitectura

_Actualizado: 2026-07-27T17:58:36+00:00_
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
