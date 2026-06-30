# TIPS-USO — Tu sistema multiagente (OpenCode · Claude Code · Codex)

Guía práctica para instanciar y manejar el harness. Todo el contenido fuente vive en `~/SET-AGENTES/`.
Los archivos reales instalados están en `~/.config/opencode/`, `~/.claude/` y `~/.codex/`.

---

## 1. Qué es esto (en criollo)
- **Harness**: el andamiaje verificable alrededor del modelo (agentes, permisos, skills, comandos, scripts,
  gates). No le pedís mejor al modelo: lo metés en un proceso que prueba su propio trabajo.
- **Loop**: ciclo controlado `implementar → verificar → auditar → reparar → verificar → memoria → stop`,
  con cortes duros (máx. iteraciones, mismo error repetido, decisión humana).
- **Regla de oro**: el que implementa NO aprueba. Modelos baratos implementan; modelos capaces diseñan y auditan.

## 2. Estructura de SET-AGENTES
```
SET-AGENTES/
├── AGENT.md            # regla: responder en español
├── TIPS-USO.md         # este archivo
├── manifest.tsv        # rol → modo/temp/permisos/modelo por harness (EDITÁ ACÁ los modelos)
├── build.sh            # genera e instala (./build.sh  |  ./build.sh --install)
├── Global/
│   ├── _canonical/     # FUENTE: cuerpo de cada agente/skill/command (inglés) — editá acá
│   ├── _shared/        # configs: opencode.json, CLAUDE.md, AGENTS.*.md, snippet codex
│   ├── opencode/  claude-code/  codex/   # GENERADOS por build.sh (no editar a mano)
└── PROYECTO/           # esqueleto en español para copiar a cada repo
```
> Editás en `_canonical/` y `manifest.tsv`, corrés `build.sh`, y se regenera todo para los 3 harnesses.

## 3. Cómo cambiar modelos (lo más común)

### Perfiles rápidos (Go ⇄ Zen) — dos scripts
```bash
cd ~/SET-AGENTES
./use-go-zen.sh   # plan Go para planificar/auditar + free para implementar + GPT Plus en críticos
./use-zen.sh      # TODO en Zen (cuando Go diga 'monthly usage limit reached'); GPT Plus queda de reserva
```
Cada script cambia el manifest, el modelo por defecto y reinstala todo de una. Si Go se agota → `./use-zen.sh`.
Cuando Go vuelve a tener cupo mensual → `./use-go-zen.sh`.

### Cambio fino (un rol puntual)
Abrí `manifest.tsv`. Cada fila es un rol con su modelo por harness. Cambiás el ID, guardás y:
```bash
cd ~/SET-AGENTES && ./build.sh --install
```
IDs reales (verificá con `opencode models`). OJO: `opencode/*` = **Zen** (tu plata) · `opencode-go/*` = plan **Go**
(NO usar, lo agotaste) · `openai/*` = **GPT Plus** (reserva, se agota rápido).
- **Free (Zen, $0)**: `opencode/deepseek-v4-flash-free`, `opencode/north-mini-code-free`, `opencode/nemotron-3-ultra-free`, `opencode/mimo-v2.5-free`.
- **Zen capaces**: `opencode/deepseek-v4-pro`, `opencode/glm-5.1/5.2`, `opencode/kimi-k2.6`, `opencode/qwen3.6-plus`, `opencode/claude-sonnet-4-6`, `opencode/gpt-5.5`.
- **Zen codex (crítico)**: `opencode/gpt-5.3-codex` — usado en db-auditor/security-auditor.
- **GPT Plus (reserva manual)**: `openai/gpt-5.5`. No los uso en automático para no agotarlos.

## 4. Roster de agentes (16)
| Plan/Diseño | Construir | Auditar (read-only) | Soporte |
|---|---|---|---|
| orchestrator, brainstormer, product-analyst, architect, ux-ui-designer | test-writer, implementer, refactor-specialist | auditor, security-auditor, red-team, blue-team, db-auditor, performance-auditor | debugger, memory-scribe |

Cómo se invocan:
- **OpenCode**: `@auditor revisá el diff`, o comando `/audit`. El primary por defecto es `orchestrator`.
- **Claude Code**: vía el Task tool (los agentes están en `~/.claude/agents/`).
- **Codex**: prompts `/<rol>` en `~/.codex/prompts/` (multi-agente activo).

## 5. Comandos
`/brainstorm` `/sdd-start` `/design` `/next-task` `/audit` `/verify` `/repair` `/debug`
`/review-security` `/review-db` `/review-perf` `/red-team` `/blue-team` `/save-memory` `/pr-ready`

## 6. Flujo típico (SDD + TDD + auditoría)
```
/brainstorm <idea fuzzy>          # opcional, si no está claro
/sdd-start <idea>                 # product-analyst: spec/plan/tasks/acceptance
/design                           # architect: ADR si toca arquitectura/datos/seguridad/plata
# test-writer: tests rojos para los AC
/next-task T-001                  # implementer: diff mínimo
./ai/scripts/verify.sh            # gate determinístico
/audit                            # auditor read-only
/review-db  /review-security  /review-perf   # según el dominio del cambio
/repair                           # solo findings concretos → re-verify → re-audit
/save-memory                      # solo aprendizaje durable y verificado
```
O todo el loop automático de una tarea:
```bash
./ai/scripts/loop.sh T-001 4
```

## 7. Instanciar en un repo nuevo
```bash
cp -r ~/SET-AGENTES/PROYECTO/* ~/SET-AGENTES/PROYECTO/.opencode ~/mi-repo/   # lo que necesites
cd ~/mi-repo
chmod +x ai/scripts/*.sh
$EDITOR AGENTS.md           # dominio, invariantes, stack, comandos test/lint/build
$EDITOR ai/scripts/verify.sh  # reflejar tu stack real
```
Override local: poné agentes/skills de dominio en `.opencode/{agents,skills}/` (o `.claude/`, `.codex/`).
Lo local pesa más que lo global dentro del repo.

## 8. Qué va global y qué local
- **Global**: agentes/skills/comandos genéricos, separación de deberes, política de secrets, permisos base, MCPs comunes.
- **Local (repo)**: AGENTS.md del proyecto, specs/tasks/ADRs, verify.sh real, skills de dominio, reglas de negocio del cliente, overrides de modelo.
- **NO global**: reglas de un cliente, rutas específicas, credenciales, decisiones de arquitectura de un proyecto, memoria ruidosa.

## 9. MCP (engram, context7, playwright, brave-cdp) — APAGADOS por defecto
Los 4 servidores están configurados en los 3 harnesses pero **arrancan apagados**, y la IA tiene que
**pedirte permiso** antes de encender o usar cualquiera. Detalle completo en `Global/_shared/mcp/README.md`.

**Quién puede llamar a cada uno** (los demás agentes NO):
| MCP | Agentes | Para qué |
|---|---|---|
| engram | memory-scribe (escribe), orchestrator (lee) | SOLO bugs, fixes y detalles críticos del proyecto |
| context7 | architect, implementer, debugger, test-writer | docs externas actuales/por versión |
| playwright / brave-cdp | debugger, ux-ui-designer | verificación E2E / controlar tu Brave |

> Regla: engram NO es un log de sesión. Lo de la sesión va en docs/specs/Obsidian. engram = memoria durable
> de alto valor. NUNCA secrets/PII/logs/diffs completos.

**Encender (tras pedírtelo):** OpenCode → `enabled:true` en opencode.json · Codex → descomentar bloque en
config.toml · Claude → sacar de `disabledMcpjsonServers` en settings.json + `/mcp`.
**Brave por CDP:** abrís Brave con `brave --remote-debugging-port=9222` y encendés `brave-cdp`.
**Nota:** en Claude, engram es un *plugin* (no mcp.json); queda disponible pero regido por la misma política
(solo memory-scribe, preguntar antes). Si lo querés 100% dormido en Claude: `enabledPlugins."engram@engram"=false`.

## 10. Checklist de oro (los 8 errores del TP de ticketing que el sistema CAZA)
Cargados como skills que usan los auditores:
1. **Paginar en SQL** no en memoria (`performance-scalability`).
2. **Transacción atómica** con unidad de trabajo (`db-integrity`).
3. **Concurrencia que dispara**: token de versión incrementado / UPDATE condicional atómico (`db-integrity`).
4. **409 Conflict** correcto vía middleware global, sin stack trace (`error-handling-http`).
5. **Auditar el intento FALLIDO** con su propio SaveChanges fuera del rollback (`db-integrity`).
6. **N+1 / AsNoTracking / proyección** y constantes en vez de hardcodes (`performance-scalability`).
7. **Frontend**: toast propio + refresco, sin `alert()`, errores centralizados (`frontend-error-ux`).
8. **Secrets y basura**: nada commiteado, `.gitignore` de bin/obj/*.user (`secrets-hygiene`).

## 11. Cortes del loop (cuándo para solo)
Máx. iteraciones · mismo estado de falla repetido (hash) · `HUMAN_DECISION_REQUIRED` (criterios en conflicto,
finding que cambia comportamiento, migración que arriesga plata/identidad/audit, fix que necesita secrets/prod).

## 12. Mantenimiento
- Editar un agente/skill: tocá `Global/_canonical/...`, después `./build.sh --install`.
- Backups previos a la migración: `~/SET-AGENTES/_backup-<fecha>/` (incluye lo de gentle-ai por si querés restaurar algo).
