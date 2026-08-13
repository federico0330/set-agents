# 023-senales-de-consumo

<!-- notas:auto -->
## Estado

- fase: `PACKAGE_REVIEW` · modo: scoped · revisión 29
- spec: `docs/specs/023-senales-de-consumo/spec.md` (hash `6b9ce1f94aa2`)

## Criterios de aceptación

- AC-01
- AC-02
- AC-03
- AC-04
- AC-04a
- AC-05
- AC-06
- AC-07
- AC-08
- AC-09
- AC-10

## Paquetes

- [[features/023-senales-de-consumo/B1-registro-que-no-miente|B1-registro-que-no-miente]] — package_review · Normalizador unico de consumo: que los cuatro lanes registren de verdad, y que un dict ir…
- [[features/023-senales-de-consumo/B2-el-reporte-dice-de-donde-sale|B2-el-reporte-dice-de-donde-sale]] — planned · Dos secciones nombradas por su fuente que nunca se suman, para que no haya doble conteo
- [[features/023-senales-de-consumo/B3-ventana-y-rollup|B3-ventana-y-rollup]] — planned · Rollups en la misma transaccion que close_run, y retencion que no borra lo referenciado
- [[features/023-senales-de-consumo/B4-estimado-nunca-dato-del-proveedor|B4-estimado-nunca-dato-del-proveedor]] — planned · Que ningun numero estimado viaje sin su base, su ventana y su cobertura

## Approach y decisiones

- [2026-08-13] implementer: AC-01..03. Medido antes de implementar: 80 dispatches, 1 con numeros, 54 absent, 25 NULL. El plan decia que opencode y claude-code MIENTEN con ok+NULL; es falso, ponen absent, que…
- decisión: [[decisiones/2026-08-13 correccion-el-plan-tenia-razon-a-medias-y-el-orquestador-tambien|Correccion: el plan tenia razon sobre un camino que la base no exhibia]]

## Qué falta

- _nada pendiente_ ✅

## Presupuestos

- spawns: 1 (máx 8/paquete) · deep review máx 2 ciclos

[[00 - Proyecto|⌂ Proyecto]] · [[features/023-senales-de-consumo/grafo|grafo]] · bitácora: `/home/federico/SET-AGENTES/docs/specs/023-senales-de-consumo/bitacora.md`

_Actualizado: 2026-08-13T17:12:55+00:00_
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
