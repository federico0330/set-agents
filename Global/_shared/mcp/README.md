# MCP — política y cómo encender/apagar por harness

Servidores definidos en los 3 harnesses: **engram**, **context7**, **playwright**, **brave-cdp**.
Regla general (ADR-0025): **arrancan APAGADOS**, y para el catálogo gestionado el agente los
**enciende→usa→apaga solo, sin pedir permiso**, registrándolo en la narración/log — la vieja excepción del
browser-gate ahora es la regla para todo el catálogo. Lo único que sigue requiriendo pedirte algo son las
credenciales de MCPs de terceros (p.ej. `SUPABASE_ACCESS_TOKEN`) o un conector ausente de la sesión que
exija reiniciarla.

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
- **Runtime/E2E gate** — el agente ejecuta `./ai/scripts/mcp.sh browser-gate auto` o
  `./ai/scripts/e2e.sh <TASK_ID> auto`. No debe pedirte que manipules toggles.
- **Cualquier otro uso del catálogo** — el agente habilitado ejecuta `./ai/scripts/mcp.sh on <server>`
  (OpenCode o Claude Code; el script detecta el harness), lo usa para esa tarea y lo apaga al salir,
  registrándolo. En Codex, si la sesión no expone el conector dinámicamente, puede quedar requerido
  reiniciar la sesión con el server habilitado.

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
