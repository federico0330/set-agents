# 008-dynamic-selection

<!-- notas:auto -->
## Estado

- fase: `DONE` · modo: feature · revisión 37
- estado final: **DONE**
- spec: `docs/specs/008-dynamic-selection/spec.md` (hash `d16765edd399`)

## Criterios de aceptación

- AC-01
- AC-02
- AC-03
- AC-04
- AC-05
- AC-06
- AC-07
- AC-08
- AC-09
- AC-10

## Paquetes

- [[features/008-dynamic-selection/P1-uninterrupted-delegation|P1-uninterrupted-delegation]] — accepted · Que una sesion larga se camine sola: el orquestador no termina un turno para reportar ava…

## Approach y decisiones

- [2026-07-30] -: product-analyst entregó AC-11..AC-20 en docs/specs/008-dynamic-selection/spec.md (1.0.0->1.1.0), verificado contra catalog.py/domain.py/service.py y una corrida real de 'opencode …
- [2026-07-30] -: product-analyst entregó contract 1.2.0 resolviendo los 3 bloqueantes + 4 highs + 6 mediums + 6 lows del primer challenge. Mando al mismo spec-challenger (contexto ya cargado) a un…
- [2026-07-30] -: product-analyst reescribió AC-17/AC-18 quirúrgicamente (contract 1.3.0): family pasa a ser curada con regla de colisión para ids compartidos entre providers, subscription/metered …
- [2026-08-02] integrator: INTEGRATION entry: read-only validation of P1-uninterrupted-delegation against approved spec 008; P3 budget-aware-selection stays blocked on 011 and is out of scope.
- [2026-08-02] integrator: Integration validation PASS: AC-01..AC-10 verified in current tree (doctrine in 3 shared runtimes, build.sh --check CHECK_PASS SELF_SCAFFOLD_SYNC_OK, ADR-0011 linked, no conflict …
- [2026-08-02] orchestrator: 008 DONE: transition PACKAGE_ACCEPTED->INTEGRATION->DONE with global gate feature-008-integration pass (verify.sh 558 OK, build check). P3 budget-aware-selection remains deferred …
- decisión: [[decisiones/2026-07-28 008-state-reinit-con-perdida-de-historia|Re-init forzado del estado de 008, con la historia descartada preservada como evidencia]]
- decisión: [[decisiones/2026-07-30 opencode-zen-go-billing-model-distinto-no-mismo-pool|OpenCode Go es suscripción mensual, OpenCode Zen es pago por uso (API key) — no comparten pool y no son el mismo tipo de proveedor]]
- decisión: [[decisiones/2026-07-30 family-se-normaliza-no-se-captura-del-vendor-para-ids-compartidos|Para modelos compartidos entre lanes de OpenCode, family se normaliza (colisiona), no se copia del vendor]]
- decisión: [[decisiones/2026-07-30 p2-discovered-inventory-pasa-a-ser-su-propia-feature-012|P2-discovered-inventory se separa de 008 y pasa a ser la feature 012, mismo patrón que 010/006]]

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

- spawns: 6 (máx 12/paquete) · deep review máx 2 ciclos

[[00 - Proyecto|⌂ Proyecto]] · [[features/008-dynamic-selection/grafo|grafo]] · bitácora: `/home/federico/SET-AGENTES/docs/specs/008-dynamic-selection/bitacora.md`

_Actualizado: 2026-08-02T14:53:39+00:00_
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
