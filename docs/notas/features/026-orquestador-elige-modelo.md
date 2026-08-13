# 026-orquestador-elige-modelo

<!-- notas:auto -->
## Estado

- fase: `DONE` · modo: scoped · revisión 59
- estado final: **DONE**
- spec: `docs/specs/026-orquestador-elige-modelo/spec.md` (hash `659eb59f9f95`)

## Criterios de aceptación

- AC-01
- AC-02
- AC-03
- AC-04
- AC-05
- AC-06
- AC-07

## Paquetes

- [[features/026-orquestador-elige-modelo/P1-latencia-por-modelo-no-por-sufijo|P1-latencia-por-modelo-no-por-sufijo]] — accepted · El orquestador deja de estar obligado al sufijo -fast y pasa a un modelo no-GPT de suscri…
- [[features/026-orquestador-elige-modelo/P2-modelo-por-instancia|P2-modelo-por-instancia]] — accepted · Que el orquestador pueda pedir un modelo para un spawn puntual, sin saltear ninguna barre…

## Approach y decisiones

- [2026-08-13] implementer: AC-01..03. El test test_repo_go_zen_routes_hot_path_to_fast_variants_and_keeps_reviewers_apart (test_harness.py:266) exige sufijo -fast para orchestrator/implementer/product-analy…
- [2026-08-13] implementer: AC-04..07, clase public-contract: cambia el contrato del descriptor de --route-decide (set_agents_app.py:605, conjunto cerrado). El riesgo central es que se convierta en bypass: l…

## Qué falta

- _nada pendiente_ ✅

## Presupuestos

- spawns: 2 (máx 8/paquete) · deep review máx 2 ciclos

[[00 - Proyecto|⌂ Proyecto]] · [[features/026-orquestador-elige-modelo/grafo|grafo]] · bitácora: `/home/federico/SET-AGENTES/docs/specs/026-orquestador-elige-modelo/bitacora.md`

_Actualizado: 2026-08-13T15:35:37+00:00_
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
