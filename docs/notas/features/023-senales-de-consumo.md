# 023-senales-de-consumo

<!-- notas:auto -->
## Estado

- fase: `DONE` · modo: scoped · revisión 134
- estado final: **DONE**
- spec: `docs/specs/023-senales-de-consumo/spec.md` (hash `47997907be45`)

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

- [[features/023-senales-de-consumo/B1-registro-que-no-miente|B1-registro-que-no-miente]] — accepted · Normalizador unico de consumo: que los cuatro lanes registren de verdad, y que un dict ir…
- [[features/023-senales-de-consumo/B2-el-reporte-dice-de-donde-sale|B2-el-reporte-dice-de-donde-sale]] — accepted · Dos secciones nombradas por su fuente que nunca se suman, para que no haya doble conteo
- [[features/023-senales-de-consumo/B3-ventana-y-rollup|B3-ventana-y-rollup]] — accepted · Rollups en la misma transaccion que close_run, y retencion que no borra lo referenciado
- [[features/023-senales-de-consumo/B4-estimado-nunca-dato-del-proveedor|B4-estimado-nunca-dato-del-proveedor]] — accepted · Que ningun numero estimado viaje sin su base, su ventana y su cobertura

## Approach y decisiones

- [2026-08-13] implementer: AC-06/07, clase migration. Medido: schema_version=7, dispatches 82 filas sin retencion, events 200 con retencion ya implementada (indices events_retention y events_route_retention…
- [2026-08-13] implementer: Relanzada de run1_0f2ddb58 que murio por session limit sin dejar codigo. Ahora codex/openai-codex/gpt-5.6-terra. OJO para el review posterior: el writer pasa a ser codex, asi que …
- [2026-08-13] package-reviewer: Writer fue codex/openai-codex/gpt-5.6-terra (run1_af1780fa, relanzado tras el limite de sesion de anthropic). Reviewer claude-code/anthropic/opus, dec1_97e06bb0, independence_veri…
- [2026-08-13] repair-agent: B3-F01 critical: close_exhausted no escribe rollup y la guarda EXISTS(rollup con esta clave) deja que un agregado ajeno 'pruebe' la fila, que se borra. B3-F02 critical: la guarda …
- [2026-08-14] delta-reviewer: Reparador claude-code/anthropic/opus (run1_26d316ee). Delta reviewer en codex, proveedor distinto. El orquestador ya verifico los seis en el codigo y ademas encontro y cerro un hu…
- [2026-08-14] implementer: AC-08/09/10, ultimo paquete de 023. usage_rollups (schema 9) ya trae suma Y conteo de reportados por metrica, que es la cobertura. Ningun proveedor expone cuota restante: sin pres…
- decisión: [[decisiones/2026-08-13 correccion-el-plan-tenia-razon-a-medias-y-el-orquestador-tambien|Correccion: el plan tenia razon sobre un camino que la base no exhibia]]
- decisión: [[decisiones/2026-08-13 relanzo-b3-en-otro-proveedor-por-limite-de-sesion|B3 se relanza en otro proveedor por limite de sesion, no por fallar la tarea]]

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

- spawns: 8 (máx 8/paquete) · deep review máx 2 ciclos

[[00 - Proyecto|⌂ Proyecto]] · [[features/023-senales-de-consumo/grafo|grafo]] · bitácora: `/home/federico/SET-AGENTES/docs/specs/023-senales-de-consumo/bitacora.md`

_Actualizado: 2026-08-14T05:10:03+00:00_
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
