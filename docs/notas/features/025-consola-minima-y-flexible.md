# 025-consola-minima-y-flexible

<!-- notas:auto -->
## Estado

- fase: `PACKAGE_IMPLEMENTATION` · modo: scoped · revisión 16
- spec: `docs/specs/025-consola-minima-y-flexible/spec.md` (hash `1ff81af48729`)

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

- [[features/025-consola-minima-y-flexible/D1-superficie-humana|D1-superficie-humana]] — package_implementation · Menu sin emoji, 31 flags internas ocultas pero vivas, y salida humana en vez de JSON crudo
- [[features/025-consola-minima-y-flexible/D2-trabajo-visible|D2-trabajo-visible]] — planned · Que se vea que el harness esta trabajando, sin romper pipes ni CI
- [[features/025-consola-minima-y-flexible/D3-posturas-de-autonomia|D3-posturas-de-autonomia]] — planned · Que el usuario elija cuanta autonomia le da al harness, y que cada postura cambie algo ob…
- [[features/025-consola-minima-y-flexible/D4-harness-por-CLI|D4-harness-por-CLI]] — planned · Instalar y desinstalar el harness por CLI, sin tocar los otros
- [[features/025-consola-minima-y-flexible/D5-vault-en-todo-spawn|D5-vault-en-todo-spawn]] — planned · Que cada spawn de proyecto use Obsidian, verificando primero que se cumple hoy en un spaw…

## Approach y decisiones

- [2026-08-14] implementer: AC-01..03. Medido: MENU_ITEMS son 10 items con emoji (set_agents_app.py:3523-3534), y dos de ellos ya llevan DOS espacios en vez de uno porque sus glifos miden distinto -la prueba…
- decisión: [[decisiones/2026-08-15 actualizar-le-repone-los-cuatro-CLIs-al-que-instalo-uno|Defecto latente: cmd_update ignora install-targets.json y reinstala los cuatro arboles]]
- decisión: [[decisiones/2026-08-15 RDD-ya-existe-en-el-repo-con-otra-acepcion|RDD no es un termino a definir: ya esta en uso instalado, con otro significado]]
- decisión: [[decisiones/2026-08-15 numeracion-de-ADRs-de-025-desempatada-a-favor-de-los-context-packs|Los numeros de ADR de la spec 025 estaban viejos y se corrigieron a favor de los context packs]]
- decisión: [[decisiones/2026-08-16 RDD-es-el-modulo-de-gentle-ai-confirmado-por-federico|RDD queda definido: es el modulo strict-TDD de gentle-ai, confirmado por Federico]]

## Qué falta

- → sigue la implementación local del paquete
- 3 tareas pendientes en D1-superficie-humana

## Presupuestos

- spawns: 1 (máx 8/paquete) · deep review máx 2 ciclos

[[00 - Proyecto|⌂ Proyecto]] · [[features/025-consola-minima-y-flexible/grafo|grafo]] · bitácora: `/home/federico/SET-AGENTES/docs/specs/025-consola-minima-y-flexible/bitacora.md`

_Actualizado: 2026-08-14T11:11:13+00:00_
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
