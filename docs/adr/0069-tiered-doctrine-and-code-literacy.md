# ADR-0069 — Doctrina por capas, alfabetismo de código, etiqueta de proyecto

- Estado: **Accepted** (2026-08-24). Feature `038-tokens-literacy-and-project-label`.
- Relaciona: ADR-0011 (turn continuity en AGENTS.md de OpenCode), ADR-0026, ADR-0068.

## Contexto

`orchestrator.md` ~900 líneas. AGENTS.md / `00-harness.mdc` (~110–130 líneas) se inyectan en **cada** sesión. Duplicar el protocolo de coordinación ahí no enseña más: infla tokens. En OpenCode, AGENTS.md **es** el coordinador cuando no hay spawn de orchestrator — no se puede vaciar Turn continuity (test y ADR-0011).

El usuario pierde noción al escalar: las devoluciones no anclan en una función real.

## Decisión

1. **Capa always-on** (`Global/_shared/AGENTS.{opencode,codex,cursor}.md`, `CLAUDE.md`, regla Cursor): invariantes (idioma, file-first, separación de deberes, evidencia, pregunta, continuidad de turno, decisión humana) + puntero ADR-0069 a `orchestrator.md` para spawn economy, plantillas de hito y alfabetismo completo. Techo de líneas pinneado por test (excepto `AGENTS.pi.md`, que sigue siendo el orquestador de pi).
2. **Capa coordinador** (`Global/_canonical/agents/orchestrator.md`): protocolo completo. **Code literacy:** al planear, flujo + pseudocódigo corto de la **función madre** (punto de entrada que hace posible el cambio, con `file:line` leído); al devolver, nombrarla; nunca inventar símbolos (ADR-0026, decir `sin verificar`).
3. **`project_label`:** string libre en `config.toml` (mismo writer que `postura`). Personaliza el título del hub. Ausente o vacío = nombre del directorio. Sin enum de actividad.
4. **Métrica por encargo:** `cost-report` lista sesiones de spawn por `feature_id`. Los campos de tokens en esos records están ausentes — la sección lo declara; Section 1 sigue siendo la medición de tokens CLI.

## Consecuencias

- Ahorro: less always-on prose; coordinar sigue costando `orchestrator.md` cuando se carga.
- OpenCode no pierde la regla de “no cortar el turno para reportar progreso”.
