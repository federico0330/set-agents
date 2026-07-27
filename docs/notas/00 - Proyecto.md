# SET-AGENTES — notas

<!-- notas:auto -->
## Features

- [[features/002-adaptive-pi-orchestration|002-adaptive-pi-orchestration]] — fase `BLOCKED` · paquetes 0/1 · **BLOCKED**
- [[features/003-trusted-routing-pi-runtime|003-trusted-routing-pi-runtime]] — fase `PACKAGE_ACCEPTED` · paquetes 1/1
- [[features/004-adaptive-dispatch|004-adaptive-dispatch]] — fase `PACKAGE_ACCEPTED` · paquetes 1/1

## Qué falta

- **002-adaptive-pi-orchestration** ⛔ bloqueo: HUMAN_DECISION_REQUIRED: user-authorized third repair cycle failed final review; five high findings remain and P1 exhau…
- **002-adaptive-pi-orchestration** 5 hallazgos abiertos
- **003-trusted-routing-pi-runtime** → `INTEGRATION` — all packages accepted
- **004-adaptive-dispatch** → `INTEGRATION` — all packages accepted

## Decisiones

- [[decisiones/2026-07-26 scope-cheap-tier-and-pi-spike|Alcance 004: tier barato sin opencode/* y P3 condicionado a spike]]
- [[decisiones/2026-07-26 am2-probe-cache-fresh-selected|AM-2: cache de probes filtering-only + re-probe fresco del seleccionado (enmienda a 003/ADR-0005)]]
- [[decisiones/2026-07-26 am1-hybrid-facts|AM-1: derivacion hibrida de facts con risk raise-only (enmienda a 003)]]
- [[decisiones/2026-07-25 r3-threat-model-amendment|R3: enmienda del threat model de routing-v2]]
- [[decisiones/2026-07-24 p1r-final-delta-block|P1R remains blocked after fresh independent delta review]]
- [[decisiones/2026-07-24 p1r-r2-authorized|Second repair cycle authorized by user]]
- [[decisiones/2026-07-24 authorize-p1r-r2|User authorizes a second P1R repair cycle]]
- [[decisiones/2026-07-24 p1r-r1-delta-block|P1R blocked after the authorized R1 delta review]]

## Referencias

- `ai/state/STATUS.md` — dashboard técnico
- `docs/adr/` — decisiones formales de arquitectura

_Actualizado: 2026-07-27T10:01:27+00:00_
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
