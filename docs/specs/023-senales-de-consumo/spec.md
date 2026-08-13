# 023 — Señales de consumo

- **Estado**: aprobado por Federico como capa B del plan A→B→C (2026-08-12), y confirmado
  (2026-08-13) con el pedido de escribir e implementar las tres features restantes.
- **Decisión ya tomada, no re-litigable**: la cuota restante se **estima desde el consumo propio**,
  siempre etiquetada `ESTIMADO`, y **nunca entra al sort key**.
- **ADRs**: 0045 (un vocabulario de consumo, traducido en el borde), 0046 (estimado es estimado).

## El defecto que manda sobre todo lo demás

**El registro de consumo está roto en 2 de 4 lanes.** `opencode` y `claude-code` mandan formas que
`_usage_row` no reconoce, y el resultado no es un error: se persiste `usage_status='ok'` con **todas
las columnas en NULL**. O sea entran a los reportes como sesiones de cero tokens.

Sin esto arreglado no hay estimación posible: estarías promediando ceros fantasma. Por eso **B1 es
innegociablemente el primer paquete**, y ningún otro empieza hasta que esté verde por lane.

## Límite honesto, escrito y no disimulado

**Ningún proveedor expone cuota restante.** Los comandos permitidos responden autenticado sí/no y
qué modelos listan. Lo que sí se puede es medir lo propio y estimar desde ahí — que es lo que
Federico eligió. **Sin presupuesto declarado no existe "restante"**: existe "consumido en la
ventana", que es medición y no adivinanza.

## Paquetes

### PKG-1 — `registro-que-no-miente` (primero, sin excepción)

- **AC-01**: un normalizador único, `ai/scripts/routing_core/usage.py`, con **la muestra real del
  cable por lane pegada en el docstring** — no un esquema inventado. La traducción vive en el
  adaptador de cada lane; `_usage_row` sigue siendo el validador cerrado.
- **AC-02**: el fix de tres líneas que convierte un fantasma en un descarte contado: un dict **no
  vacío** sin ningún campo reconocido pasa de `'ok'` a `'invalid'`. Hoy miente en silencio.
- **AC-03**: prueba por lane, con un spawn real de cada uno, de que las columnas de consumo quedan
  **no-NULL**. Evidenciado con `status_counts`, no con una afirmación.

### PKG-2 — `el-reporte-dice-de-donde-sale`

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
