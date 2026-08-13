# 023 — Señales de consumo

- **Estado**: aprobado por Federico como capa B del plan A→B→C (2026-08-12), y confirmado
  (2026-08-13) con el pedido de escribir e implementar las tres features restantes.
- **Decisión ya tomada, no re-litigable**: la cuota restante se **estima desde el consumo propio**,
  siempre etiquetada `ESTIMADO`, y **nunca entra al sort key**.
- **ADRs**: 0045 (un vocabulario de consumo, traducido en el borde), 0046 (estimado es estimado).

## El defecto que manda sobre todo lo demás — RE-MEDIDO, el plan se equivocaba

El plan A→B→C decía que `opencode` y `claude-code` persisten `usage_status='ok'` con todas las
columnas en NULL, o sea que **mienten**. **Medido en la base real el 2026-08-13, es falso y el
defecto es otro, más simple y más grande.**

`~/.local/state/set-agentes/routing-v2/routing.db`, tabla `dispatches`, 80 filas:

| `usage_status` | filas | detalle |
|---|---|---|
| con números reales | **1** | `usage_input=3321, usage_output=5, cost_micros=3351` |
| `absent` | 54 | claude-code 10, opencode 14, pi 30 |
| `NULL` | 25 | runs cerrados sin pasar uso |

`absent` **no es una mentira**: significa "el proveedor no reportó nada", y `_usage_row` lo
documenta así explícitamente (`store.py:140-142`). El problema real es que **nadie manda el uso
nunca**: la flag `--usage` existe (`set_agents_app.py:3641`, *"con --route-terminal: uso/costo del
spawn"*) y **la doctrina canónica no la menciona una sola vez** — `grep -rn '\-\-usage'
Global/_canonical/` da cero.

O sea: no hay un normalizador roto que arreglar sobre datos que llegan mal. **No llegan.** El
orquestador cierra los runs con `--route-terminal <id> success` y descarta el consumo que tiene a
la vista, porque nada se lo pide.

Sin esto arreglado no hay estimación posible: estarías promediando 1 dato. Por eso **B1 es
innegociablemente el primer paquete**, y ningún otro empieza hasta que haya datos por lane.

## Límite honesto, escrito y no disimulado

**Ningún proveedor expone cuota restante.** Los comandos permitidos responden autenticado sí/no y
qué modelos listan. Lo que sí se puede es medir lo propio y estimar desde ahí — que es lo que
Federico eligió. **Sin presupuesto declarado no existe "restante"**: existe "consumido en la
ventana", que es medición y no adivinanza.

## Paquetes

### PKG-1 — `registro-que-no-miente` (primero, sin excepción)

- **AC-01**: **que el uso efectivamente llegue.** La doctrina canónica del orquestador pasa a exigir
  `--usage` al cerrar un run, con el formato exacto por runtime, y `Global/_canonical/agents/
  orchestrator.md` lo dice de forma imperativa —no como opción—, siguiendo la lección de ADR-0041:
  una regla escrita como menú es una regla que alguien elige no seguir.
- **AC-02**: un normalizador único, `ai/scripts/routing_core/usage.py`, con **la muestra real del
  cable por runtime pegada en el docstring** — no un esquema inventado. La traducción vive en el
  adaptador; `_usage_row` sigue siendo el validador cerrado y **no se relaja**: `absent` sigue
  significando "el proveedor no reportó nada", que es verdad y no un defecto.
- **AC-03**: prueba por runtime de que las columnas quedan **no-NULL** cuando el uso se manda, y de
  que un dict **no vacío** sin ningún campo reconocido se cuenta como `'invalid'` en vez de pasar
  por bueno. Evidenciado con `status_counts` antes y después, no con una afirmación.

### PKG-2 — `el-reporte-dice-de-donde-sale`

**Alcance ampliado durante B1** (nota de decisión `correccion-el-plan-tenia-razon-a-medias-y-el-
orquestador-tambien`): el implementer de B1 encontró que `claude_code_spawn.py:602-605` y
`opencode_spawn.py:318-321` **ya adjuntan** `--usage` en cada dispatch, con las formas
`{"total_cost_usd", "modelUsage"}` y `{"tokens"}`, que `_usage_row` **no reconoce**. Antes del
endurecimiento de AC-02 eso producía exactamente lo que el plan describía: `usage_status='ok'` con
todo en NULL. Ahora produce `'invalid'`, que es un descarte **contado** — mejor, pero sigue sin ser
el dato.

- **AC-04a**: los adaptadores de spawn se cablean a `routing_core/usage.py`, para que la forma que
  ya mandan se **traduzca** en vez de descartarse. Prueba: un dispatch por lane que hoy da
  `'invalid'` pasa a dar columnas no-NULL, con `status_counts` antes y después.
- **AC-04**: el riesgo real **no** es la etiqueta `"pi"` de `cost-report.py:312`: es el **doble
  conteo** con los stores propios de los CLIs. Dos secciones nombradas por su fuente, que **nunca
  se suman entre sí**.
- **AC-05**: ninguna superficie puede presentar un total sin decir de qué fuente salió.

### PKG-3 — `ventana-y-rollup`

- **AC-06**: schema 8 con `usage_rollups`, escrito **en la misma transacción** que `close_run` —
  si el rollup no entra, el run tampoco.
- **AC-07**: retención de `dispatches`, que hoy crece sin límite. **Nunca** borra una fila
  referenciada por `replacement_of_run_id` ni una que un reviewer todavía pueda consultar.

### PKG-4 — `estimado-nunca-dato-del-proveedor`

- **AC-08**: ningún número estimado viaja solo. Siempre con `basis`, `provider_reported: false`, la
  ventana **nombrada por su definición** (no "última semana" sino el rango exacto) y la cobertura.
- **AC-09**: guard test al estilo de los ratchets que ya existen: una superficie que renderice un
  "restante" sin su etiqueta y su base **falla el gate**.
- **AC-10**: **sin presupuesto declarado no se muestra "restante"**. Se muestra "consumido en la
  ventana".

## No-goals

- **El consumo no entra al sort key** (`service.py:382`) ni a `reason_codes`. Es información para
  el humano, no un factor de ruteo.
- No se inventa denominador ni horario de reset.
- No se estima antes de que PKG-1 esté verde **por lane**.
- No se agrega `context_window`: es criterio de elegibilidad, no de costo — otra feature.

## Riesgos

1. **Estimar sobre datos rotos.** Mitigado por el orden: PKG-1 primero, con prueba por lane.
2. **Doble conteo con los stores de los CLIs.** Es el riesgo de PKG-2 y por eso las dos secciones
   nunca se suman.
3. **Que "estimado" se lea como dato del proveedor.** Es el riesgo de PKG-4 y por eso el guard test.

## Gates

Por paquete: suite en verde (**`pytest` no está instalado**), `./ai/scripts/verify.sh` →
`VERIFY_PASS`, `./build.sh --check` → `GLOBAL_TREE_SYNC_OK` + `BUILD_CHECK_PASS`, ACs con evidencia
`file:line`. Review independiente en otro proveedor, repair consolidado, delta review.

## Criterio de cierre

Un spawn real por lane con columnas de consumo **no-NULL**, evidenciado con `status_counts`. Y que
ninguna superficie pueda renderizar un "restante" sin su etiqueta y su base.
