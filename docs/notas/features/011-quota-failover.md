# 011-quota-failover

<!-- notas:auto -->
## Estado

- fase: `BLOCKED` · modo: feature · revisión 7
- estado final: **BLOCKED**
- spec: `docs/specs/011-quota-failover/spec.md` (hash `280c60a041c4`)

## Criterios de aceptación

- AC-01
- AC-02
- AC-03
- AC-04
- AC-05
- AC-06

## Paquetes

- [[features/011-quota-failover/P1-quota-failover|P1-quota-failover]] — package_gates · Atomically classify the exact settled Anthropic/Pi quota exhaustion, preserve its failed …

## Approach y decisiones

- ruteo P1-quota-failover: atomic routing lifecycle and accounting require high-capability implementation
- [2026-07-30] implementer: Implementación acotada de esquema, transacción BEGIN IMMEDIATE, integración Pi y pruebas deterministas para AC-01..AC-06.
- [2026-07-30] implementer: Nueva instancia implementa exclusivamente los pendientes documentados: tests deterministas AC-01..05 y runner/evidencia AC-06.
- [2026-07-30] implementer: Instancia focalizada para runner credencial-gated AC-06 y evidencia, sin expandir el núcleo de routing.
- [2026-07-30] implementer: Core schema-7, transición atómica, adaptador Pi, pruebas AC-01..05 y runner AC-06 documentados; cinco pruebas focalizadas PASS.
- [2026-07-30] runtime-verifier: AC-06 requiere precondición externa verificable. Runner validado devuelve BLOCKED/HUMAN_DECISION_REQUIRED antes de abrir DB o invocar Pi; feature state quedó BLOCKED.
- [2026-07-30] -: verify.sh (suite completa, 473 tests) -> FAILED (failures=2): test_routing_migrate_uses_harness_identity_and_test_store espera 'to=6' y el schema real ya es 7; test_the_usage_colu…
- decisión: [[decisiones/2026-07-30 ac-06-espera-agotamiento-real-decidido-con-el-usuario|El usuario elige esperar un agotamiento real de cuota en vez de forzarlo o relajar AC-06]]

## Qué falta

- → corresponde tu decisión (ver Blocker)
- ⛔ bloqueo: HUMAN_DECISION_REQUIRED: AC-06 exige una suscripción Anthropic controlada y genuinamente agotada junto a un proveedor a…
- 5 tareas pendientes en P1-quota-failover

## Presupuestos

- spawns: 3 (máx 12/paquete) · deep review máx 2 ciclos

[[00 - Proyecto|⌂ Proyecto]] · [[features/011-quota-failover/grafo|grafo]] · bitácora: `/home/federico/SET-AGENTES/docs/specs/011-quota-failover/bitacora.md`

_Actualizado: 2026-07-30T17:04:39+00:00_
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
