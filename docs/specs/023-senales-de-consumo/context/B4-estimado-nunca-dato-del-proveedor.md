# Context pack — B4-estimado-nunca-dato-del-proveedor

Spec: `docs/specs/023-senales-de-consumo/spec.md`, **AC-08, AC-09, AC-10**. Último paquete de 023.
Depende de **B3**, cuya migración dejó la base en **schema 9**.

## Lo que ya existe y tenés que consumir, no rehacer

`usage_rollups` (schema 9) trae, por ventana e identidad, **la suma y el conteo de reportados** de
cada métrica:

```
window_start, project_key, route_key, runtime, provider, model, family, outcome, usage_status,
run_count,
usage_input_sum,       usage_input_reported_count,
usage_output_sum,      usage_output_reported_count,
usage_cache_read_sum,  usage_cache_read_reported_count,
usage_cache_write_sum, usage_cache_write_reported_count,
usage_reasoning_sum,   usage_reasoning_reported_count,
cost_micros_sum,       cost_micros_reported_count
```

**El par suma/conteo es exactamente lo que necesitás para la cobertura.** Si `run_count` es 40 y
`usage_input_reported_count` es 12, tu cobertura es 12/40 y **eso hay que decirlo**, no promediar
sobre 40 como si los 28 restantes fueran cero.

## La decisión de Federico, no re-litigable

La cuota restante se **estima desde el consumo propio**, siempre etiquetada `ESTIMADO`, y **nunca
entra al sort key**. Es información para el humano, no un factor de ruteo.

## El límite honesto que hay que escribir, no disimular

**Ningún proveedor expone cuota restante.** Los comandos permitidos responden autenticado sí/no y
qué modelos listan.

De ahí sale AC-10, que es la regla más importante del paquete: **sin presupuesto declarado no existe
"restante"**. Existe "consumido en la ventana", que es medición. Un "te quedan X" sin denominador es
inventado, y el harness no inventa.

## TAREA

**AC-08** — Ningún número estimado viaja solo. Siempre con:

- `basis` — de qué salió el cálculo
- `provider_reported: false` — explícito, no ausente
- la ventana **nombrada por su definición**: no "última semana" sino el rango exacto
- la **cobertura**: cuántos de los runs de la ventana reportaron de verdad

**AC-09** — Guard test: una superficie que renderice un "restante" **sin** su etiqueta y su base
**falla el gate**. Es lo único que impide que la etiqueta se pierda en el próximo cambio.

Hay precedente cerca: el candado de DDL que B3 tuvo que agregar
(`test_canonical_ddl_is_pinned_to_schema`, `tests/test_routing.py:1424`) existe porque su ausencia
dejó el ruteo caído. Copiá esa idea: **un test que impida el error, no un comentario que lo pida**.

**AC-10** — Sin presupuesto declarado, no se muestra "restante". Se muestra "consumido en la
ventana".

## La trampa de este paquete

Es el más fácil de convertir en adivinanza con cara de dato. Un promedio sobre una cobertura de
12/40 presentado como "consumo diario" es **falso**, y suena razonable.

**Ante la duda, mostrá la medición cruda y su cobertura**, no una proyección. Una estimación
honesta que dice "12 de 40 runs reportaron" es más útil que un número redondo que oculta que 28 no
dijeron nada.

## Restricciones

- **ADR-0046** (`ls docs/adr/` para confirmar que está libre, indexalo en `docs/adr/README.md`):
  estimado es estimado.
- **No toques el sort key** (`service.py`) ni `reason_codes`. El consumo no rutea.
- **No inventes denominador ni horario de reset.**
- **No toques `_usage_row`** ni los normalizadores de B1/B2, ni el esquema de B3.
- **No uses `git checkout`, `git restore` ni `git stash`.** Para morder y restaurar: `cp` y `cp`.
- **No toques la base real del usuario** (`~/.local/state/set-agentes/routing-v2/routing.db`, hoy en
  schema 9 con 85 dispatches y 34 rollups) ni nada bajo `~`. Fixtures.

## Validación

`python3 -m unittest discover -s tests` (**`pytest` NO está instalado**; base **1102 OK / 3 skips**)
· `./ai/scripts/verify.sh` → `VERIFY_PASS` · `./build.sh --check` → `GLOBAL_TREE_SYNC_OK` +
`BUILD_CHECK_PASS` · `git diff --check` limpio.

**Corré los comandos largos así:** `ai/scripts/heartbeat-run.py --interval 20 -- <comando>`
(ADR-0041). La suite tarda ~10 min.

## Evidencia

`docs/specs/023-senales-de-consumo/evidence/B4-implementer.md`, escrito **en el primer minuto**:
tabla AC → cambio (`archivo:línea`) → prueba; la **salida literal** de la superficie mostrando la
etiqueta, la base, la ventana con su definición y la cobertura; la prueba de que sin presupuesto
declarado **no** aparece ningún "restante"; el guard test con su mordida en las dos direcciones; y
los gates.

**Por cada test nuevo: neutralizá el cambio, confirmá el rojo, revertí, pegá la prueba.** En este
proyecto ya aparecieron **cinco** guardas que decían cubrir algo que no miraban. No escribas la
sexta.

**Cada bloque literal, o marcado como recortado.** Si no lo corriste, "sin verificar".

## Fuera de alcance

El sort key · `context_window` (es elegibilidad, no costo) · inventar denominador u horario de reset
· el aislamiento roto de los módulos de test (preexistente, registrado) · features 024 y 025.
