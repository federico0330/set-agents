# 032-cursor-como-runtime

<!-- notas:auto -->
## Estado

- fase: `PACKAGE_IMPLEMENTATION` · modo: scoped · revisión 14
- spec: `docs/specs/032-cursor-como-runtime/spec.md` (hash `180fc0a3e1fa`)

## Criterios de aceptación

- AC-01
- AC-02
- AC-03
- AC-04
- AC-05
- AC-06
- AC-07

## Paquetes

- [[features/032-cursor-como-runtime/C1|C1]] — planned · Target cursor en el build y en el instalador: agentes, skills, doctrina y managed-files, …
- [[features/032-cursor-como-runtime/C2|C2]] — planned · Proyeccion por proyecto: .cursor/rules con alwaysApply y .cursor/commands, mas documentac…

## Approach y decisiones

- [2026-08-18] orchestrator: La doctrina dice que quien implementa no aprueba su propio trabajo, y esta sesion corre bajo una instruccion de entorno que prohibe invocar otros agentes. Por eso los dos paquetes…
- [2026-08-18] orchestrator: El generador armaba artefactos para cuatro runtimes y Cursor no era uno, asi que abrir un proyecto ahi dejaba al agente sin roles ni doctrina. Ahora emite un quinto arbol donde ca…
- decisión: [[decisiones/2026-08-18 cursor-entra-como-runtime-anfitrion-nunca-como-lane-de-ruteo|Cursor entra como runtime anfitrion, nunca como lane de ruteo]]
- decisión: [[decisiones/2026-08-18 en-cursor-no-se-instalan-hooks-de-evento-en-esta-version|En Cursor no se instalan hooks de evento en esta version]]

## Convenciones

| Eje | Origen | Stance | Umbral | Siguiente | Revisit |
|---|---|---|---|---|---|
| data-store | n/a | no database: the artifacts are files on disk under ~/.cursor and the project tree |  |  |  |
| api-gateway | n/a | no network surface: build, install and bootstrap are local processes |  |  |  |
| deploy-platform | n/a | no deploy: distribution is git clone plus ./build.sh --install on the developer machine |  |  |  |
| audience | request | Federico as a single developer using Cursor on his own machine, after the other three runtimes ran out of quota |  |  |  |
| embeddings | n/a | no embeddings or vector search anywhere in this feature |  |  |  |
| realtime | n/a | no realtime: generation and install are one-shot batch commands |  |  |  |
| mobile | n/a | no mobile surface: Cursor is a desktop IDE |  |  |  |
| auth | n/a | no authentication: the feature writes files under the user's own HOME |  |  |  |
| cost | request | explicit anti-cost decision: no model id is pinned, every subagent inherits the session model so the harness never routes a paid model behind the user's back |  |  |  |
| legal | n/a | no legal surface: internal developer tooling, public repo, no third-party data |  |  |  |

## Qué falta

- → sigue la implementación local del paquete
- 1 tarea pendientes en C2

## Presupuestos

- spawns: 0 (máx 8/paquete) · deep review máx 2 ciclos

[[00 - Proyecto|⌂ Proyecto]] · [[features/032-cursor-como-runtime/grafo|grafo]] · bitácora: `/home/federico/SET-AGENTES/docs/specs/032-cursor-como-runtime/bitacora.md`

_Actualizado: 2026-08-18T14:18:10+00:00_
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
