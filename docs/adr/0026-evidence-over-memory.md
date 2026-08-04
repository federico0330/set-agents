# ADR-0026 — Evidencia sobre memoria: fuentes obligatorias y plantilla de spawn-prompt

- Estado: Accepted (2026-08-04). Feature 017. Segunda de cinco (0025-0029).

## Contexto

La exigencia de evidencia era fuerte en review (`finding-verifier`, `package-reviewer`,
`security-auditor`, `adversarial-judge` — schemas con `file:line` + evidencia obligatoria) pero ausente
exactamente donde más se responde "de memoria": `brainstormer.md` no tenía ni una regla de evidencia, el
modo consult no exigía citas, ningún subagente del lane Claude Code tenía WebSearch/WebFetch
(`generate.py::claude_tools`), y context7 arrancaba apagado detrás de un pedido de permiso — en la
práctica, se salteaba. Tampoco existía plantilla de spawn-prompt: el orquestador (el "PO" del harness)
tenía solo una enumeración en prosa de qué debe contener un spawn message.

## Decisión

1. **Regla transversal** en la doctrina compartida (`Global/_shared/CLAUDE.md` + AGENTS.*): ninguna
   afirmación técnica sin fuente — `file:line` del repo, salida de comando ejecutado, o doc actual
   (context7/WebFetch) con URL. Sin fuente disponible, se dice explícitamente "sin verificar". Aplica a
   todos los modos, consult incluido.
2. **WebSearch/WebFetch** para los roles de análisis (architect, brainstormer, package-reviewer,
   security-auditor, debugger, product-analyst) en el lane Claude Code, y `webfetch: allow` para los
   mismos en OpenCode.
3. **`brainstormer`** gana reglas de evidencia: leer el repo antes de opinar; claims de
   librerías/precios/límites con doc actual; opciones con costo real citado.
4. **Consult** entrega una tabla claims→evidencia; el claim sin fuente se marca, no se disimula.
5. **Skill `spawn-prompt`**: formato fijo de spawn message (contexto / tarea / evidencia exigida /
   formato de salida / fuera de alcance / presupuesto), referenciada como obligatoria desde
   `orchestrator.md`. Complementa el context pack de `package-planner`, no lo reemplaza.

## Rejected alternatives

- **Habilitar WebSearch a todos los roles**: los roles mecánicos (gate-runner, local-gate-runner) no
  analizan; ampliar su superficie no compra nada y contradice least-privilege.
- **Hacer de context7 un MCP siempre-encendido**: contradice el modelo enciende-usa-apaga de ADR-0025.5;
  con la excepción operativa ya no hace falta.

## Consecuencias

- Un `/consult` deja de poder responder enteramente de memoria sin declararlo.
- El costo de tokens sube marginalmente en análisis (búsquedas) y baja en re-trabajo por respuestas
  erradas — el balance es el que pide la visión de producto.
