# ADR-0025 — Autonomía "resolver primero, registrar siempre"

- Estado: Accepted (2026-08-04). Feature 017. Primera de cinco ADRs (0025-0029) del cierre de brechas de
  producto contra la visión del dueño y la comparación con `gentle-ai`.

## Contexto

La doctrina se auto-neutralizaba: `## Turn continuity` prohíbe terminar un turno para reportar progreso,
pero la Question policy autorizaba terminar por "missing credentials/access" sin exigir ningún intento
previo. El carve-out de deploy platform (`orchestrator.md`) frenaba incluso cuando el usuario ya había
nombrado la plataforma en el pedido — la decisión que el carve-out protege ya estaba tomada. "Prod
credentials" era freno duro en 4 roles sin distinguir una operación de producción explícitamente pedida
de una decidida por el harness. Y la infraestructura de instalación de CLIs/MCPs (`tools.toml` con
vercel/gh/supabase, detección `shutil.which`, instalación multi-gestor en `set_agents_app.py`,
`--mcp-add`/`--mcp-toggle`) existía completa pero era humano-only: `coord_policy.py` no permitía
ninguna de esas invocaciones y ningún rol tenía mandato de usarlas. Resultado observado: el mismo prompt
de deploy que Claude Code resolvía en minutos, el harness lo devolvía con una lista de comandos para que
el usuario corriera a mano.

## Decisión

1. **Credenciales**: "missing credentials/access" solo autoriza preguntar DESPUÉS de intentar el flujo
   interactivo del propio CLI (`vercel login`, `gh auth login`, OAuth de navegador) y de que ese flujo
   requiera una acción física del humano. El intento y su resultado se registran.
2. **Plataforma nombrada = decisión tomada**: si el pedido nombra la plataforma de deploy, el red-flag de
   arquitectura no pregunta — registra con `log-decision` y sigue; el ADR formal se escribe después. El
   carve-out queda solo para plataforma NO decidida.
3. **Prod pedido vs credencial inconseguible**: una operación de producción que el usuario pidió
   explícitamente no frena (se registra); frenan las credenciales genuinamente inconseguibles, los datos
   de producción tocados por decisión propia del harness, y lo destructivo.
4. **Auto-instalación**: `set_agents_app.py --tools`, `--tools-install <name> --yes` y
   `--mcp-add/--mcp-toggle` entran al allowlist del orquestador (`coord_policy.py`) mediante un
   argv-walker estricto (patrón `_transition_blocks_integration`), nunca regex laxo — el comentario de
   `coord_policy.py` sobre `--tools-install` nace de un hallazgo real de escritura de archivos. Sudo
   nunca: si el método de instalación elegido requiere sudo, se entrega el comando exacto al humano
   (única excepción legítima de "correlo vos"). Mandato nuevo en `orchestrator.md`/`implementer.md`: CLI
   del catálogo ausente → instalarlo y registrar con `log-decision`.
5. **MCP discipline**: la excepción operativa del browser-gate (encender→usar→apagar sin preguntar,
   registrando) se extiende a todo el catálogo `Global/_shared/mcp/` (context7, engram, playwright,
   brave-cdp). Se pregunta únicamente por credenciales de MCPs de terceros (p.ej. SUPABASE_ACCESS_TOKEN).
   `mcp.sh` gana soporte claude-code además de OpenCode.

## Rejected alternatives

- **Preguntar la primera vez por herramienta**: agrega un fin de turno por CLI nuevo sin ganancia de
  seguridad real — el catálogo `tools.toml` ya es un closed set curado.
- **Permitir sudo con `--yes`**: cruzaría la línea de blast-radius del sistema del usuario; el harness
  instala en espacio de usuario o delega.
- **Un rol nuevo `ops-runner`**: superficie duplicada; el orquestador ya puede invocar los verbos seguros
  vía wrapper y el implementer ya tiene la capability para el resto.

## Consecuencias

- El freno queda donde protege de verdad: sudo, secretos inconseguibles, destructivo, datos de prod no
  pedidos. Todo lo demás se resuelve y se registra — trazable en `docs/notas/decisiones/`.
- Cada allow nuevo de `coord_policy` lleva test negativo propio; la superficie sigue deny-by-default.
