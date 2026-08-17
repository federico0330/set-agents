# 025-consola-minima-y-flexible

<!-- notas:auto -->
## Estado

- fase: `DONE` · modo: scoped · revisión 159
- estado final: **DONE**
- spec: `docs/specs/025-consola-minima-y-flexible/spec.md` (hash `f113d8233aa7`)

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
- AC-11
- AC-12

## Paquetes

- [[features/025-consola-minima-y-flexible/D1-superficie-humana|D1-superficie-humana]] — accepted · Menu sin emoji, 31 flags internas ocultas pero vivas, y salida humana en vez de JSON crudo
- [[features/025-consola-minima-y-flexible/D2-trabajo-visible|D2-trabajo-visible]] — accepted · Que se vea que el harness esta trabajando, sin romper pipes ni CI
- [[features/025-consola-minima-y-flexible/D3-posturas-de-autonomia|D3-posturas-de-autonomia]] — accepted · Que el usuario elija cuanta autonomia le da al harness, y que cada postura cambie algo ob…
- [[features/025-consola-minima-y-flexible/D4-harness-por-CLI|D4-harness-por-CLI]] — accepted · Instalar y desinstalar el harness por CLI, sin tocar los otros
- [[features/025-consola-minima-y-flexible/D5-vault-en-todo-spawn|D5-vault-en-todo-spawn]] — accepted · Que cada spawn de proyecto use Obsidian, verificando primero que se cumple hoy en un spaw…

## Approach y decisiones

- [2026-08-17] package-reviewer: Relanzamiento único tras policy interruption; read-only y excluye security PoCs. Solo AC-11 y coherencia docs/runtime.
- [2026-08-17] finding-verifier: F01 high AC11: verificación focal read-only de CLI/docs sin análisis de rutas ni cambios.
- [2026-08-17] repair-agent: D4-F01 upheld; repair limitado a CLI one-shot, aislamiento HOME/XDG, tests y evidencia; no tocar otros carriles.
- [2026-08-17] delta-reviewer: DELTA_REVIEW del repair bfe7b2d; revisión read-only focal de aislamiento runtime y evidencia.
- [2026-08-17] repair-agent: Spawn 8/8; F01/DR02 probados por delta, repair mínimo sin cambios de aislamiento.
- [2026-08-17] implementer: Base fija 8a9f62bb5fa7dc1ed3f4275a1261de7c88ea9208; usar la rama rescatada sólo como referencia selectiva, nunca mergear su D5 divergente.
- decisión: [[decisiones/2026-08-15 actualizar-le-repone-los-cuatro-CLIs-al-que-instalo-uno|Defecto latente: cmd_update ignora install-targets.json y reinstala los cuatro arboles]]
- decisión: [[decisiones/2026-08-15 RDD-ya-existe-en-el-repo-con-otra-acepcion|RDD no es un termino a definir: ya esta en uso instalado, con otro significado]]
- decisión: [[decisiones/2026-08-15 numeracion-de-ADRs-de-025-desempatada-a-favor-de-los-context-packs|Los numeros de ADR de la spec 025 estaban viejos y se corrigieron a favor de los context packs]]
- decisión: [[decisiones/2026-08-16 RDD-es-el-modulo-de-gentle-ai-confirmado-por-federico|RDD queda definido: es el modulo strict-TDD de gentle-ai, confirmado por Federico]]
- decisión: [[decisiones/2026-08-16 el-reporte-de-un-implementer-no-es-evidencia-de-que-el-codigo-exista|D5 nunca produjo codigo, y el orquestador lo dio por implementado durante horas]]
- decisión: [[decisiones/2026-08-16 RDD-es-receipt-driven-development-y-ahora-tiene-fuente|RDD queda cerrado con fuente: Receipt-Driven Development, verificado contra el upstream]]
- decisión: [[decisiones/2026-08-17 retoma-opencode-traspaso-2026-08-17|Retoma desde opencode con TRASPASO]]
- decisión: [[decisiones/2026-08-17 route-decide-sin-descriptor-host|route-decide sin descriptor en host OpenCode]]
- decisión: [[decisiones/2026-08-17 enmienda-documental-025-antes-de-aceptar-D1|La enmienda documental de 025 se formaliza antes de aceptar D1]]
- decisión: [[decisiones/2026-08-17 d2-segundo-ciclo-reparacion-consolidada|D2 entra al segundo y último ciclo de reparación]]
- decisión: [[decisiones/2026-08-17 d4-gate-reintento-focal|D4 relanza el gate focal por evidencia incompleta]]
- decisión: [[decisiones/2026-08-17 d4-review-reintento-sin-poc-rutas|D4 relanza revisión de producto sin PoC de rutas]]
- decisión: [[decisiones/2026-08-17 d4-segundo-repair-con-evidencia-delta|D4 usa el último repair batch con evidencia directa del delta]]
- decisión: [[decisiones/2026-08-17 d4-presupuesto-spawn-agotado-antes-delta-final|D4 agotó su presupuesto de spawns antes del delta final]]
- decisión: [[decisiones/2026-08-17 d5-relanzamiento-único-tras-watchdog|D5 relanzamiento único tras watchdog]]

## Qué falta

- _nada pendiente_ ✅

## Presupuestos

- spawns: 23 (máx 8/paquete) · deep review máx 2 ciclos

[[00 - Proyecto|⌂ Proyecto]] · [[features/025-consola-minima-y-flexible/grafo|grafo]] · bitácora: `/home/federico/SET-AGENTES/docs/specs/025-consola-minima-y-flexible/bitacora.md`

_Actualizado: 2026-08-17T19:05:19+00:00_
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
