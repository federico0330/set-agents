# MCP — política y cómo encender/apagar por harness

Servidores definidos en los 3 harnesses: **engram**, **context7**, **playwright**, **brave-cdp**.
Regla general: **arrancan APAGADOS** y la IA debe **pedirte permiso** antes de encender o usar cualquiera.
Excepción operativa: durante un runtime/E2E gate aprobado, el agente puede encender `playwright` o `brave-cdp`
mediante `ai/scripts/mcp.sh` / `ai/scripts/e2e.sh`, usarlo sólo para esa prueba observable, y apagarlo al salir.

## Quién puede llamar a cada uno (los demás agentes NO)
| MCP | Agentes habilitados | Para qué |
|---|---|---|
| engram | `memory-scribe` (escribe), `orchestrator` (lee) | SOLO documentar bugs, fixes y detalles críticos del proyecto |
| context7 | `architect`, `implementer`, `debugger`, `test-writer` | SOLO docs externas actuales/por versión cuando hay duda |
| playwright | `runtime-verifier`, `debugger`, `ux-ui-designer` | Verificación E2E con navegador propio |
| brave-cdp | `runtime-verifier`, `debugger`, `ux-ui-designer` | Controlar un Brave local con sesión/login cuando hace falta |

> Todo lo demás (estado de sesión, decisiones de trabajo) NO va a engram: va en la sesión y en
> docs/specs/Obsidian. engram es para memoria durable de alto valor, no un log.

## Encender
- **Runtime/E2E gate aprobado** — el agente ejecuta `./ai/scripts/mcp.sh browser-gate auto` o
  `./ai/scripts/e2e.sh <TASK_ID> auto`. No debe pedirte que manipules toggles.
- **Otros usos** — el agente pide permiso primero. En OpenCode puede ejecutar `./ai/scripts/mcp.sh on <server>`
  cuando el proyecto tiene el script. En Codex/Claude, si la sesión no expone el conector dinámicamente, puede
  quedar requerido reiniciar la sesión con el server habilitado.

## Apagar
El agente ejecuta `./ai/scripts/mcp.sh off playwright` y/o `./ai/scripts/mcp.sh off brave-cdp`. El wrapper
`e2e.sh` lo hace en `EXIT` aunque falle la prueba.

## Brave por CDP
Para gates que requieren una sesión real, el agente debe intentar:

```bash
./ai/scripts/mcp.sh ensure-brave-cdp
```

Eso abre o detecta un Brave/Chromium local con CDP en `127.0.0.1:9222` y habilita `brave-cdp`. Si requiere login,
el agente sólo debe pedirte que ingreses credenciales en la ventana abierta; no debe pedirte que edites toggles ni
que copies cookies/tokens.
