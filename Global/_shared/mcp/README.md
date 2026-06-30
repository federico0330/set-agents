# MCP — política y cómo encender/apagar por harness

Servidores definidos en los 3 harnesses: **engram**, **context7**, **playwright**, **brave-cdp**.
Regla: **arrancan APAGADOS** y la IA debe **pedirte permiso** antes de encender o usar cualquiera.

## Quién puede llamar a cada uno (los demás agentes NO)
| MCP | Agentes habilitados | Para qué |
|---|---|---|
| engram | `memory-scribe` (escribe), `orchestrator` (lee) | SOLO documentar bugs, fixes y detalles críticos del proyecto |
| context7 | `architect`, `implementer`, `debugger`, `test-writer` | SOLO docs externas actuales/por versión cuando hay duda |
| playwright | `debugger`, `ux-ui-designer` | Verificación E2E con navegador propio |
| brave-cdp | `debugger`, `ux-ui-designer` | Controlar un Brave que abrís vos |

> Todo lo demás (estado de sesión, decisiones de trabajo) NO va a engram: va en la sesión y en
> docs/specs/Obsidian. engram es para memoria durable de alto valor, no un log.

## Encender (después de que la IA te lo pida y vos digas que sí)
- **OpenCode** — en `~/.config/opencode/opencode.json`, poné `"enabled": true` en el server.
- **Codex** — descomentá el bloque `[mcp_servers.x]` en `~/.codex/config.toml`.
- **Claude Code** — sacá el nombre de `disabledMcpjsonServers` en `~/.claude/settings.json`, luego `/mcp`.

## Apagar
Revertí lo anterior (enabled:false / comentar / volver a disabledMcpjsonServers).

## Brave por CDP (navegador que abrís vos)
1. Cerrá Brave. 2. Abrilo con debugging: `brave --remote-debugging-port=9222`
3. Encendé `brave-cdp` (paso de arriba). La IA controla esa instancia, no abre una nueva.
