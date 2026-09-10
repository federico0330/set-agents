# ADR-0073 — `effort_request`: preferencia blanda efímera, hermana de `model_request`

- Estado: **Accepted** (2026-08-26). Feature `045-consola-viva-e-instancia`, PKG-D (AC-D.1, AC-D.2,
  AC-D.3).
- **Enmienda ADR-0044 P2 / 026 AC-04**: `model_request` deja de ser "the ONE new key" del descriptor de
  `--route-decide` (`ai/scripts/set_agents_app.py:672-676`). `effort_request` es la segunda. El conjunto
  sigue cerrado y una clave no reconocida sigue siendo `ROUTING_INPUT_INVALID`/rc=2.
- **Depende de ADR-0071** para la persistencia del lado curado (`models.local.toml`), y **es consumido
  por** `047-lanes-agy-fx-copilot`: `materialize(model, effort)` habla este vocabulario y no define un
  segundo (047 audit (i)).
- No supersede ADR-0030 (`MODEL_STATIC_FALLBACK` sigue siendo el registro de materialización), ni
  ADR-0032 (el pin persistente conserva su posición en el sort key), ni ADR-0035 (`billing_rank` no se
  mueve de su lugar relativo).

## Contexto

Medido, 2026-08-26:

1. **El effort ya viaja en toda decisión y en toda identidad.** `set_agents_app.py:763` lo registra en
   el log de decisiones; `StaticRoute.effort` forma parte del binding canónico y del digest de
   `route_id` (`routing_core/domain.py:127-132`, `:195-196`); la tupla inmutable de identidad es
   `(route_id, runtime, provider, model, family, effort)` (`domain.py:208`, `:213`, `store.py:83`) y el
   esquema de `dispatches` la persiste en tres juegos de columnas (`store.py:455-466`).
2. **El orquestador no puede pedirlo.** `cmd_route_decide` acepta `model_request` como única clave nueva
   (`:675-676`) y no tiene hermana de effort, aunque el effort ya esté en cada sobre.
3. **El vocabulario ya existe y ya es cerrado, en tres lugares que coinciden.**
   `_CODEX_EFFORT_LEVELS = {low, medium, high, xhigh}` (`codex_spawn.py:82`),
   `_OPENCODE_VARIANT_LEVELS` idéntico (`opencode_spawn.py:105`) y
   `[catalog].codex_effort = ["high","low","medium","xhigh"]` (`models.toml:11`), que es lo que
   `build_snapshot` valida para `openai-codex` (`catalog.py:962`, `:1008`). Además: `anthropic` está
   **pinneado a `medium`** por el validador de catálogo (`catalog.py:1009`), las rutas sintetizadas
   nacen `medium` (`inference.py:114`), y `_PI_THINKING_LEVELS` (`set_agents_spawn.py:266`) es un
   **superconjunto** (`off`, `minimal`, `max`) que ninguna fila de catálogo puede llevar.
4. **`codex_effort` es una columna de un solo proveedor con un solo consumidor curado.**
   `AREA_FIELDS` la lista (`models_config.py:39`), `resolve_role` la resuelve (`:610`), `load_roles` la
   valida contra el catálogo (`:640-641`), y el **único** consumidor curado que existe es
   `generate.py:551`, que emite `model_reasoning_effort = <codex_effort>` en
   `~/.codex/agents/<role>.toml`. El picker de campos del wizard ofrece
   `claude|codex|codex_effort|opencode` (`setup_models.py:613`).

## Decisión

### 1. `effort_request`: clave nueva del descriptor, validada en parse

Entra al `allowed` de `cmd_route_decide` (`:675-676`). Ausente → `None` → decisión **byte-idéntica** a
la pre-045 (AC-D.2). Presente → validada contra el vocabulario cerrado de §2 por el mismo camino que
`_validate_model_request` (`:291-309`): `ValueError` plano, capturado por el `except (OSError,
ValueError)` existente (`:696-697`), que responde `ROUTING_INPUT_INVALID`/rc=2. Es la misma disciplina
fail-closed **en tiempo de parse** que `risk`/`selected_runtime` (F01): un effort malformado nunca llega
al service para degradar en un reason code distinto.

### 2. Vocabulario cerrado, una sola fuente

`models_config.EFFORTS = ("low", "medium", "high", "xhigh")`. No es invención: es el conjunto que
`_CODEX_EFFORT_LEVELS`, `_OPENCODE_VARIANT_LEVELS` y `[catalog].codex_effort` ya comparten. `load_config`
gana un guardián — `set(config["catalog"]["codex_effort"]) <= set(EFFORTS)` — para que la constante y el
catálogo trackeado no puedan divergir; la lección de ADR-0042 es que las copias sincronizadas a mano se
desincronizan, y acá ya hay tres.

Los niveles extra de pi (`off`, `minimal`, `max`) **quedan afuera** y siguen siendo vocabulario del CLI
`pi`: ninguna fila de catálogo puede llevarlos (`catalog.py:1008-1009`), así que aceptarlos como
`effort_request` sería pedir algo imposible de honrar por construcción. El mapeo pi-side no cambia
(`set_agents_spawn.py:328`).

### 3. Preferencia blanda: una columna más del sort key, después de `model_request_rank`

`effort_request_rank` se inserta en el sort key de `service.py:457` **inmediatamente después de**
`model_request_rank` y **antes de** `billing_rank`. Tupla final:

```
(same_provider_as_writer, pin_rank, TIER_ORDER, model_request_rank,
 effort_request_rank, billing_rank, _bias_rank, is_inferred, curated_priority, route_id)
```

Dos posiciones, dos razones escritas:

- **Después de `TIER_ORDER`**, como el `model_request` de 026 y a diferencia del pin persistente: un
  pedido efímero por instancia nunca le gana a la política de menor-tier-suficiente. Sólo rompe empates
  entre candidatos ya empatados en tier.
- **Después de `model_request_rank`**: el audit de 045 (iii) ya decidió que cuando el modelo pedido no
  ofrece el effort pedido, gana el modelo. Ponerlo estrictamente después hace ese resultado
  **estructural**, no un desempate que dependa del orden de llegada.

Todo candidato que esta columna compara ya sobrevivió el loop completo de exclusiones duras
(`service.py:343-...`: identidad/auth, `PROVIDER_EXHAUSTED`, `PROVIDER_UNAUTHENTICATED`,
`ROLE_INCOMPATIBLE`, `TOOLS_MISSING`, `CONTEXT_MISSING`, independencia de reviewer, piso de tier). Por
lo tanto no puede relajar ninguna, ni siquiera rankeando primero (AC-D.3).

### 4. El effort vive en la identidad de la ruta: se **selecciona**, nunca se muta

Esta es la consecuencia más importante del ADR y la razón por la que "preferencia blanda" no es un
eufemismo. `effort` está dentro del digest de `route_id` (`domain.py:127-132`, `:195-196`) y dentro de
la tupla de identidad inmutable que `authorize()` persiste (`domain.py:208`, `store.py:83`, `:455-466`).
Entonces:

- `effort_request` **elige entre rutas existentes** que ya llevan ese effort.
- **Nunca** cambia el `effort` de una ruta, nunca acuña una identidad que ninguna fila de catálogo
  respalde, y nunca altera lo que `authorize()` graba.

Cualquier otra forma rompería `identity_allowed`/`authorize` y el esquema congelado de `dispatches`.

### 5. Reason codes: dos, aditivos, y el "no honrado" siempre se nombra

Misma disciplina que `MODEL_PINNED`/`MODEL_PIN_UNAVAILABLE` (ADR-0032, `service.py:507-509`) y
`MODEL_REQUEST_APPLIED`/`MODEL_REQUEST_UNAVAILABLE` (026, `:528-540`): aditivos, nunca reemplazan ni
reordenan un code existente, nunca cambian `success`/`runtime`/`identity`/`fallback`.

- `EFFORT_REQUEST_APPLIED <effort>` cuando el effort de la ruta seleccionada es el pedido.
- `EFFORT_REQUEST_UNAVAILABLE requested=<effort> reason=<why>` en cualquier otro caso, con `why`
  resuelto en el mismo orden de prioridad de tres que ya usa `model_request`:
  1. la **primera barrera dura** que golpeó, en ese mismo loop, una ruta que llevaba ese effort
     (`TIER_INSUFFICIENT`, `PROVIDER_UNAUTHENTICATED`, `REVIEW_FAMILY_CONFLICT`, …), capturada como
     `model_request_reason` lo captura hoy (`:342`, `:409-413`) — nunca re-corriendo nada del loop;
  2. `OUTRANKED` cuando una ruta con ese effort sobrevivió todas las exclusiones (era elegible de
     verdad) pero otra ganó el sort — elegible no es lo mismo que elegida;
  3. `NOT_IN_CATALOG` cuando ninguna ruta lleva ese effort.

Nunca un degrade silencioso: eso es exactamente la trampa que AC-D.3 existe para cerrar.

### 6. Efímero: no se escribe en ningún archivo

Ni en `model-preference.toml` ni en el overlay de ADR-0071. Igual que `model_request` (026 AC-07): la
efimeridad vive en que el caller nunca llama `atomic_write` para este valor, y en que `route()` lo recibe
como **parámetro por llamada**, nunca como campo de `TaskRequest` — así todo sitio de construcción de
`TaskRequest` y todo caller existente de `route()` queda byte-idéntico (`service.py:265-279`).
`cmd_route_decide` es el único caller de producción que lo provee, directo del descriptor.

### 7. El eje curado (lado `models.toml`): qué se agrega y qué **no**, con la medición

045 AC-D.1 pide que el effort sea **ofrecido** para toda lane de `AREA_FIELDS`. Lo medido sobre los
consumidores curados:

| lane | parámetro de effort medido | consumidor curado |
|---|---|---|
| `codex` | `-c model_reasoning_effort=<e>` (`codex_spawn.py:215-216`) | **sí** — `generate.py:551` |
| `opencode` | `--variant <e>` (`opencode_spawn.py:240`) | **no** — el frontmatter de agente OpenCode lleva sólo `model:` (`generate.py:514-517`, `:602-604`) |
| `claude` | **ninguno** — `claude_code_spawn.py:436-439` no tiene flag de effort, y `catalog.py:1009` pinnea `anthropic` a `medium` | no aplica |
| `cursor` | **ninguno** — el frontmatter es `model:` (ADR-0063) | no aplica |

Decisión: **`AREA_FIELDS` no gana ningún campo nuevo en este ADR.** La matriz de Overrides muestra una
fila EFFORT para las cuatro lanes (con eso AC-D.1 se cumple en su letra: "effort is offered for every
lane"); `codex_effort` es la única celda que **acepta** un valor, y las otras tres renderizan una
ausencia nombrada (`sin parámetro de effort medido`) en lugar de aceptar un valor que nada lee — la
misma regla de honestidad 023/044 que AC-A.2 ya impone sobre este panel.

Reserva de nombre, para que el crecimiento no cueste esquema: cuando el parámetro de effort de una lane
**se mida** (el lugar donde eso pasa para una lane nueva es el contrato de adapters de 047), su campo se
llama `<lane>_effort` — `codex_effort` ya tiene esa forma —, entra a `AREA_FIELDS`, y **no** necesita
cambio en el overlay: ADR-0071 §4 ya admite cualquier miembro de `AREA_FIELDS`. Un campo se agrega
**junto con** su consumidor medido, nunca antes.

Esto es un **estrechamiento explícito** del pedido original ("effort editable por área/rol para todas
las lanes"). Se registra como tal, con la medición: escribir tres campos que nadie lee sería una API
fabricada (ADR-0026).

### 8. La persistencia del override de effort va al overlay

Editar `codex_effort` desde el wizard escribe `STATE_DIR/models.local.toml` (ADR-0071), nunca el archivo
trackeado — el effort es uno de los cuatro campos que 045 AC-B.1 enumera (área, rol, effort, `cursor`).

## Alternativas rechazadas

- **`effort_request` como filtro duro.** Dejaría que un pedido efímero anule un piso de tier o una
  exclusión de independencia: exactamente la línea que el comentario del pin (ADR-0032,
  `service.py:437-457`) y el de `billing_rank` (ADR-0035) nombran como la que nunca se mueve.
- **`effort_request_rank` antes de `TIER_ORDER`**, como el pin persistente. Rechazado: un pedido efímero
  por instancia no puede ganar "cruzando tiers"; 026 ya decidió esa posición para `model_request`.
- **Mutar el effort de la ruta decidida para honrar el pedido.** `effort` está en el digest de `route_id`
  y en la identidad congelada de `dispatches`: acuñaría una identidad sin fila de catálogo detrás y
  rompería `identity_allowed`/`authorize`.
- **Persistirlo como tercera tabla `[effort_pin]` en `model-preference.toml`.** No-goal explícito de 045
  ("Persisting `effort_request`") y un segundo decision-maker; si algún día se quiere una preferencia
  durable de effort, la celda curada (`<lane>_effort`) es donde ya corresponde.
- **Un vocabulario de effort por lane (los siete niveles de pi como efforts ruteables).** Ninguna fila de
  catálogo puede llevarlos (`catalog.py:1008-1009`): serían pedibles y nunca honrables por construcción.
- **Degradar en silencio cuando el effort pedido no es elegible.** AC-D.3 lo prohíbe explícitamente.
- **Renombrar `codex_effort` a un `effort` lane-neutral.** 8+ call sites (`models_config.py:39`, `:178`,
  `:610`, `:640-641`, `:765`, `:783`, `:843`, `:852`) más `LEGACY_MODEL_COLUMNS` (`:34`) más
  `[catalog].codex_effort`, que es entrada real del validador (`catalog.py:962`, `:1008`), a cambio de
  cero ganancia medida. `<lane>_effort` crece por adición.
- **Agregar `opencode_effort` / `claude_effort` / `cursor_effort` ahora.** No tienen consumidor curado
  medido; dos de las lanes no tienen parámetro de effort en absoluto. Serían tres campos decorativos.

## Consecuencias

- Un descriptor sin `effort_request` produce una decisión byte-idéntica a la pre-045 (AC-D.2); con uno
  válido y elegible, rutea con ese effort y lo reporta.
- Un `effort_request` fuera del conjunto cerrado sale rc=2 `ROUTING_INPUT_INVALID` por el mismo camino de
  parse que todo otro campo malformado; uno bien formado pero no honrable deja la exclusión intacta y
  **nombra** la razón (AC-D.3).
- `047 materialize(model, effort)` tiene un vocabulario único del cual tirar, y no puede inventar un
  segundo (047 audit (i)). Las tres lanes que ya materializan effort — codex
  (`-c model_reasoning_effort`), opencode (`--variant`), pi (`--thinking`) — no cambian.
- AC-D.1 queda cumplido con una fila por lane y tres ausencias nombradas. El eje realmente
  lane-agnóstico es el de **routing** (`effort` por decisión + `effort_request`), no cuatro columnas
  nuevas en `models.toml`.
- El esquema congelado de `dispatches` y el digest de `route_id` no se tocan.

## Evidencia

`ai/scripts/set_agents_app.py:291-309`, `:672-676`, `:690`, `:696-697`, `:735`, `:763`.
`ai/scripts/routing_core/service.py:265-279`, `:342`, `:343-379`, `:409-413`, `:437-457`, `:503-540`.
`ai/scripts/routing_core/domain.py:127-132`, `:189`, `:195-196`, `:208`, `:213`.
`ai/scripts/routing_core/store.py:83`, `:455-466`.
`ai/scripts/routing_core/catalog.py:962`, `:1008-1009`. `ai/scripts/routing_core/inference.py:110-120`.
`ai/scripts/codex_spawn.py:30-33`, `:82`, `:215-216`. `ai/scripts/opencode_spawn.py:39-43`, `:105`,
`:240`. `ai/scripts/set_agents_spawn.py:262-266`, `:328`.
`ai/scripts/claude_code_spawn.py:436-439`, `:523-525`.
`ai/scripts/models_config.py:34`, `:39`, `:610`, `:640-641`. `ai/scripts/generate.py:514-517`, `:551`,
`:602-604`. `ai/scripts/setup_models.py:613`, `:623-624`. `models.toml:11`.
Contratos: `docs/specs/045-consola-viva-e-instancia/{spec,design,acceptance}.md`,
`docs/specs/047-lanes-agy-fx-copilot/spec.md`.

## Destilado (dominio: architecture)

- `effort` es parte del digest de `route_id` y de la identidad congelada de `dispatches`
  (`domain.py:127-132`, `store.py:83`): cualquier pedido de effort **selecciona** entre rutas
  existentes; mutarlo acuñaría una identidad sin catálogo detrás.
- El vocabulario cerrado `{low, medium, high, xhigh}` ya existía triplicado
  (`codex_spawn.py:82`, `opencode_spawn.py:105`, `[catalog].codex_effort`) y `anthropic` está pinneado a
  `medium` por el validador (`catalog.py:1009`): el techo de lo que un pedido de effort puede lograr es
  el catálogo, no el pedido.
- Una columna nueva en un sort key es una decisión de **posición**: antes de `TIER_ORDER` es un filtro
  disfrazado; después de `model_request_rank` es lo que hace estructural la precedencia modelo > effort.
