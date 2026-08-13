# P2-modelo-por-instancia — evidencia del implementer

Inicio: 2026-08-13T14:28:20Z.

## AC -> cambio -> prueba

| AC | Cambio | archivo:línea | Prueba |
|---|---|---|---|
| AC-04 | `allowed` gana `"model_request"` (7 -> 8 claves, conjunto cerrado sin abrirse); `_validate_model_request` valida `"provider/model"` con el mismo vocabulario cerrado de `_validate_model_pin_entry` | `ai/scripts/set_agents_app.py:290-306` (`_validate_model_request`), `:629-630` (`allowed`), `:648-649` (parseo) | `tests/test_model_request.py::ModelRequestDescriptorValidationTests` (2), `::ModelRequestCliTests::test_unknown_key_still_rejected_after_model_request_joins_the_allowed_set`, `::test_malformed_model_request_value_is_a_parse_error_not_a_silent_degrade` |
| AC-05 | `model_request` entra en `route()` como parámetro nuevo (nunca campo de `TaskRequest`), evaluado en dos puntos, los dos DESPUÉS del bucle de exclusiones (`:321-392`, sin tocar): (1) `model_request_reason` capturado dentro del mismo bucle de exclusiones (`:320`, `:383-391`); (2) factor de sort nuevo insertado entre `TIER_ORDER` y `billing_rank` (`:435`), sin reordenar los factores preexistentes | `ai/scripts/routing_core/service.py:243-256` (firma+docstring), `:320`, `:383-391`, `:435` | `tests/test_model_request.py::ModelRequestBarrierTests` (8 tests: 5 barreras + positivo + "entra después" + OUTRANKED), `tests/test_routing.py::RoutingTests::test_sort_key_tripwire_pins_full_tuple_shape` (extendido) |
| AC-06 | `MODEL_REQUEST_APPLIED provider/model` / `MODEL_REQUEST_UNAVAILABLE requested=provider/model reason=X` — código propio, nunca degradación silenciosa; `X` es la razón de la exclusión (`model_request_reason`), `OUTRANKED` (elegible pero superado en el sort), o `NOT_IN_CATALOG` (ningún route del catálogo nombra ese `(provider, model)` — la forma observable del techo de catálogo) | `ai/scripts/routing_core/service.py:483-512` | mismos 8 tests de `ModelRequestBarrierTests` (cada uno assertea el reason_code literal) + `ModelRequestCliTests::test_valid_model_request_key_flows_end_to_end_and_names_itself_when_applied` (vía CLI real) |
| AC-07 | `model_request` viaja como argumento local de `cmd_route_decide` -> `route()`, nunca como campo de `_model_preference`/`_model_pin`; ningún call site lo pasa a `atomic_write`/`MODEL_PREFERENCE_PATH` | `ai/scripts/set_agents_app.py:649`, `:688-689` (wiring); ausencia estructural — no hay ningún `atomic_write(..., model_request...)` en el árbol | `tests/test_model_request.py::ModelRequestCliTests::test_model_request_never_writes_model_preference_toml`, `::test_model_request_does_not_bias_a_later_decide_call_without_it`; `docs/adr/0044-latencia-por-modelo-no-por-sufijo.md` (sección "Extensión P2", los tres mecanismos documentados juntos) |

## AC-04 — el conjunto cerrado gana una clave, nunca se abre

`ai/scripts/set_agents_app.py:629-630`:

```python
allowed = {"role", "task_class", "risk", "review_of_run_id", "selected_runtime", "feature_id",
           "package_id", "model_request"}
```

`_validate_model_request` (`:290-306`) reutiliza el mismo vocabulario cerrado de proveedores y la
misma regex de modelo que `_validate_model_pin_entry` (ADR-0032) ya usa para `[model_pin]` — nunca
un vocabulario nuevo. Una clave desconocida (`"bogus_key"`) sigue dando `ROUTING_INPUT_INVALID`/rc=2:

```
$ echo '{"role":"implementer","task_class":"mechanical","bogus_key":"x"}' | python3 ai/scripts/set_agents_app.py --route-decide - --json
{"command": "route-decide", "data": {}, "ok": false, "reason_codes": ["ROUTING_INPUT_INVALID"], "schema_version": 2, "warnings": []}
```
(rc=2, salida real de `tests/test_model_request.py::ModelRequestCliTests::test_unknown_key_still_rejected_after_model_request_joins_the_allowed_set`.)

Un `model_request` mal formado (sin `/`, proveedor no auditado, token de modelo inválido) es
también un fallo de PARSEO, rc=2, nunca llega al servicio a degradar en silencio
(`test_malformed_model_request_value_is_a_parse_error_not_a_silent_degrade`).

## AC-05 — el corazón: nunca antes de las exclusiones

`RoutingService.route()` (`routing_core/service.py`) recibe `model_request` como parámetro NUEVO
(`:243-244`), nunca un campo de `TaskRequest` — la misma disciplina que `review_of_run_id`, que ya
viaja como argumento separado del `route()`, no del request. Entra en el bucle de exclusiones
(`:321-392`, **sin una sola línea tocada** salvo la captura aditiva de `model_request_reason` en
`:383-391`, que sólo LEE la `reason` que el bucle ya calculó, nunca la cambia) y, recién después de
que ese bucle terminó y filtró `candidates`, en el sort key (`:435`):

```python
candidates.sort(key=lambda x: ((x[0].provider == writer.provider) if writer else False, 0 if pin and (x[0].provider, x[0].model) == pin else 1, TIER_ORDER[x[0].tier], 0 if model_request and (x[0].provider, x[0].model) == model_request else 1, billing_rank(x[0].provider, x[0].model), _bias_rank(x[0].provider, bias_preference), 1 if x[0].route_id in self._inferred_ids else 0, x[0].curated_priority, x[0].route_id))
```

Insertado entre `TIER_ORDER` y `billing_rank` — el mismo estilo de inserción que `_bias_rank`
(014-model-preference-policy) y `billing_rank` (ADR-0035) ya establecieron como precedente para este
bloque. El orden relativo de los factores preexistentes (`pin_rank`, `TIER_ORDER`, `billing_rank`,
`_bias_rank`, `is_inferred`, `curated_priority`, `route_id`) no cambia — se inserta, no se reordena
(`tests/test_routing.py::RoutingTests::test_sort_key_tripwire_pins_full_tuple_shape`, extendido con
el token nuevo y su posición, sigue en verde).

### Un test por barrera — salida literal de cada negación

Los cinco, `tests/test_model_request.py::ModelRequestBarrierTests`:

```
$ PYTHONPATH=ai/scripts python3 -m unittest tests.test_model_request -v
test_catalog_ceiling_barrier_denies_a_model_outside_the_curated_set ... ok
test_model_request_applied_when_the_requested_model_is_genuinely_eligible ... ok
test_model_request_enters_after_the_exclusion_loop_never_before_it ... ok
test_model_request_outranked_when_eligible_but_a_lower_tier_still_wins ... ok
test_review_model_conflict_barrier_denies_the_requested_model ... ok
test_review_provider_conflict_barrier_denies_the_requested_model ... ok
test_tier_insufficient_barrier_denies_the_requested_model ... ok
test_unaudited_pair_barrier_denies_the_requested_model ... ok
test_malformed_model_request_value_is_a_parse_error_not_a_silent_degrade ... ok
test_model_request_does_not_bias_a_later_decide_call_without_it ... ok
test_model_request_never_writes_model_preference_toml ... ok
test_unknown_key_still_rejected_after_model_request_joins_the_allowed_set ... ok
test_valid_model_request_key_flows_end_to_end_and_names_itself_when_applied ... ok
test_malformed_shapes_all_raise_value_error ... ok
test_valid_provider_model_string_parses ... ok

----------------------------------------------------------------------
Ran 15 tests in 10.581s

OK
```

Salida literal, capturada corriendo cada escenario directo (no vía `unittest`, mismos fixtures que
el test correspondiente):

| Barrera pedida explícitamente | Exclusión real (`route_id`, reason) | `reason_codes` de la decisión | Ganador real |
|---|---|---|---|
| `REVIEW_PROVIDER_CONFLICT` (pide `anthropic/sonnet`, mismo proveedor que el writer `anthropic/opus`) | `{'route_id': 'rt1_e625e4045035109a', 'reason': 'REVIEW_PROVIDER_CONFLICT'}` | `MODEL_REQUEST_UNAVAILABLE requested=anthropic/sonnet reason=REVIEW_PROVIDER_CONFLICT` | `opencode-zen/kimi-k2.7-code` |
| `REVIEW_MODEL_CONFLICT` (pide `opencode-zen/claude-opus-4-8`, alias real y documentado de `anthropic/opus`, el writer) | `{'route_id': 'rt1_c854e29ff783ec7d', 'reason': 'REVIEW_MODEL_CONFLICT'}` | `MODEL_REQUEST_UNAVAILABLE requested=opencode-zen/claude-opus-4-8 reason=REVIEW_MODEL_CONFLICT` | `opencode-go/kimi-k3` |
| `TIER_INSUFFICIENT` (pide `openai-codex/gpt-5.6-sol` en `fast` cuando `implementation`+`low` exige `balanced`) | `{'route_id': 'rt1_87480290f4029931', 'reason': 'TIER_INSUFFICIENT'}` | `MODEL_REQUEST_UNAVAILABLE requested=openai-codex/gpt-5.6-sol reason=TIER_INSUFFICIENT` | `opencode-zen/kimi-k2.7-code` |
| par no auditado -> `PROVIDER_UNAUTHENTICATED` (pide `opencode-zen/kimi-k2.7-code` en runtime `claude-code`, par nunca en el inventario probado) | `{'route_id': 'rt1_33a4ac62755af0c9', 'reason': 'PROVIDER_UNAUTHENTICATED'}` | `MODEL_REQUEST_UNAVAILABLE requested=opencode-zen/kimi-k2.7-code reason=PROVIDER_UNAUTHENTICATED` | `anthropic/opus` |
| techo de catálogo (pide `opencode-zen/definitely-not-a-curated-model-xyz`, contra el catálogo REAL `ai/catalogs/routes.v1.toml`+`models.toml`, no uno sintético) | (ningún route con esa identidad — nunca existió, `execution_enabled=True`) | `MODEL_REQUEST_UNAVAILABLE requested=opencode-zen/definitely-not-a-curated-model-xyz reason=NOT_IN_CATALOG` | `openai-codex/gpt-5.6-luna` |

Más un sexto (no pedido en la tarea, agregado por rigor de AC-06): `OUTRANKED` — el modelo pedido
SOBREVIVE toda exclusión (es un candidato real y elegible) pero pierde el desempate porque otro
candidato de tier más bajo ya satisface el piso (`TIER_ORDER` sigue precediendo a `model_request` en
el sort, sin tocar su precedencia) — `MODEL_REQUEST_UNAVAILABLE requested=opencode-zen/kimi-k2.7-code reason=OUTRANKED`.
"Elegible" no es lo mismo que "elegido", y el paquete lo nombra igual, nunca en silencio.

### La prueba de que entra DESPUÉS de las exclusiones (no antes)

`test_model_request_enters_after_the_exclusion_loop_never_before_it`: corre el MISMO escenario
(reviewer pidiendo `anthropic/sonnet`, que viola `REVIEW_PROVIDER_CONFLICT`) con y sin
`model_request`, y comprueba:

```python
self.assertEqual(without_request.exclusions, with_request.exclusions)   # lista de exclusiones IDÉNTICA
self.assertEqual((without_request.provider, without_request.model),
                 (with_request.provider, with_request.model))            # mismo ganador, sin bypass
self.assertFalse(any(c.startswith("MODEL_REQUEST_") for c in without_request.reason_codes))
self.assertIn("MODEL_REQUEST_UNAVAILABLE requested=anthropic/sonnet reason=REVIEW_PROVIDER_CONFLICT",
              with_request.reason_codes)
```

Todo en verde. `model_request` no cambia ni un solo elemento de `exclusions` ni el ganador — la
única diferencia observable es el marcador aditivo.

### La mordida — cada bloque neutralizado, confirmado rojo, revertido

**Mordida A** (`service.py`, quita el factor nuevo del sort key, vuelve a la tupla de 8 elementos):
rojo en el tripwire y en 4 tests más (los que dependen de que `model_request` mueva el ganador):

```
FAIL: test_sort_key_tripwire_pins_full_tuple_shape
AssertionError: 'model_request and (x[0].provider, x[0].model) == model_request' not found in '...'
FAIL: test_model_request_applied_when_the_requested_model_is_genuinely_eligible
AssertionError: Tuples differ: ('openai-codex', 'gpt-5.6-sol') != ('opencode-go', 'kimi-k3')
FAIL: test_model_request_does_not_bias_a_later_decide_call_without_it
AssertionError: 'gpt-5.6-luna' != 'haiku'
FAIL: test_valid_model_request_key_flows_end_to_end_and_names_itself_when_applied
AssertionError: Tuples differ: ('openai-codex', 'gpt-5.6-luna') != ('anthropic', 'haiku')
Ran 15 tests in 8.046s
FAILED (failures=4)
```
Restaurado con `cp` desde el backup en el scratchpad; `diff` vacío -> `RESTORED_CLEAN`; verde de
nuevo (15/15, tripwire incluido).

**Mordida B** (`service.py`, quita el bloque entero `if model_request: ... MODEL_REQUEST_APPLIED/
UNAVAILABLE`): rojo en los 5 tests de barrera + positivo + "entra después" + el CLI end-to-end (8
fallos, todos por `AssertionError: '...MODEL_REQUEST...' not found in (...)`):
```
Ran 14 tests in 8.279s
FAILED (failures=8)
```
Restaurado con `cp`; `diff` vacío; verde de nuevo.

**Mordida C** (`set_agents_app.py`, saca `"model_request"` del `allowed`): rojo en los 3 tests que
mandan la clave por CLI (ahora rc=2, `ROUTING_INPUT_INVALID`, en vez del flujo esperado):
```
FAIL: test_model_request_does_not_bias_a_later_decide_call_without_it
AssertionError: 2 != 0 : ('{"command": "route-decide", "data": {}, "ok": false, "reason_codes": ["ROUTING_INPUT_INVALID"], ...}\n', '')
FAIL: test_model_request_never_writes_model_preference_toml
AssertionError: 2 != 0 : (mismo patrón)
FAIL: test_valid_model_request_key_flows_end_to_end_and_names_itself_when_applied
AssertionError: 2 != 0 : (mismo patrón)
Ran 14 tests in 3.590s
FAILED (failures=3)
```
Restaurado con `cp`; `diff` vacío; verde de nuevo.

**Mordida D** (`set_agents_app.py`, quita la validación de proveedor/modelo dentro de
`_validate_model_request`, deja sólo el chequeo de `/`): rojo en los 2 tests que dependen
específicamente de esa validación:
```
FAIL: test_malformed_shapes_all_raise_value_error
AssertionError: ValueError not raised : not-a-real-provider/gpt-5.6-sol
FAIL: test_malformed_model_request_value_is_a_parse_error_not_a_silent_degrade
AssertionError: 0 != 2 : ('not-a-real-provider/gpt-5.6-sol', '{"...", "ok": true, "reason_codes": [..., "MODEL_REQUEST_UNAVAILABLE requested=not-a-real-provider/gpt-5.6-sol reason=NOT_IN_CATALOG"], ...}')
Ran 3 tests in 18.634s
FAILED (failures=2)
```
(Este bloqueo muestra además el defecto exacto que la validación de AC-04 evita: sin ella, un
proveedor inventado degrada a `rc=0`/`NOT_IN_CATALOG` en vez de fallar al PARSEO — la capa
equivocada.) Restaurado con `cp`; `diff` vacío; verde de nuevo.

**Mordida E** (`service.py`, colapsa la rama `OUTRANKED` a `NOT_IN_CATALOG` siempre): rojo en el
test dedicado a esa rama:
```
FAIL: test_model_request_outranked_when_eligible_but_a_lower_tier_still_wins
AssertionError: '...reason=OUTRANKED' not found in (..., '...reason=NOT_IN_CATALOG')
Ran 1 test in 0.279s
FAILED (failures=1)
```
Restaurado con `cp`; `diff` vacío; verde de nuevo.

Verde final tras las cinco mordidas y restauraciones, 16 tests (15 de `test_model_request.py` + el
tripwire extendido de `test_routing.py`):
```
Ran 16 tests in 10.581s
OK
```

## AC-06 — la negación nombra el modelo pedido y por qué, vía CLI real

```
$ echo '{"role":"implementer","task_class":"mechanical","selected_runtime":"codex","model_request":"anthropic/haiku"}' \
  | python3 ai/scripts/set_agents_app.py --route-decide - --json   # (con stubs de codex/claude/opencode)
{"...":..., "data": {..., "model": "haiku", "provider": "anthropic", "reason_codes": [
  "RUNTIME_REDIRECTED requested=codex effective=claude-code",
  "BILLING_RANK provider=anthropic rank=0",
  "MODEL_REQUEST_APPLIED anthropic/haiku"], ...}, "ok": true, ...}
```

`openai-codex/gpt-5.6-luna` es el ganador por defecto para `mechanical`+`codex` (curated_priority
10); `anthropic/haiku` es un segundo candidato `fast` genuinamente elegible (curated_priority 20) —
pedirlo por nombre voltea el ganador y lo nombra con `MODEL_REQUEST_APPLIED`.

## AC-07 — efímero: no escribe nada, no sobrevive al spawn

- `test_model_request_never_writes_model_preference_toml`: corre `--route-decide` con
  `model_request` seteado (`SET_AGENTS_STATE` apuntando a un directorio temporal) y comprueba
  `(state_dir / "model-preference.toml").exists()` es `False` después de la llamada — el archivo
  nunca se crea.
- `test_model_request_does_not_bias_a_later_decide_call_without_it`: tres llamadas consecutivas al
  mismo proceso/raíz de routing — (1) sin `model_request` -> gana `gpt-5.6-luna` (línea base); (2)
  con `model_request=anthropic/haiku` -> gana `haiku`; (3) sin `model_request` otra vez -> vuelve a
  `gpt-5.6-luna`, exactamente la línea base. Nada quedó pegado.
- Prueba estructural: `model_request` viaja como argumento local de `cmd_route_decide` ->
  `service.route(..., model_request=model_request)` (`set_agents_app.py:688-689`) — nunca entra al
  diccionario `preference`/`model_pin` que `_config_with_model_preference` arma desde
  `model-preference.toml` (`:302-316`, sin una sola línea tocada por este paquete), y ningún call
  site nuevo invoca `atomic_write`/`MODEL_PREFERENCE_PATH` con él (`grep -rn "model_request"
  ai/scripts/` no toca ninguno de los dos símbolos).
- `docs/adr/0044-latencia-por-modelo-no-por-sufijo.md`, sección "Extensión P2 — los tres mecanismos
  juntos": tabla con alcance/persistencia/ubicación de `[areas.*]` (repo, persistente),
  `--model-pin-set` (rol, persistente, ADR-0032) y `model_request` (instancia, efímero, este
  paquete).

## Gates

### `ai/scripts/heartbeat-run.py --interval 20 -- python3 -m unittest discover -s tests`

```
Ran 1080 tests in 461.769s

OK (skipped=3)
```

Base declarada en el context pack: **1065 OK / 3 skips**. Delta: **+15** (exactamente los 15 tests
nuevos de `tests/test_model_request.py`; el tripwire de `test_routing.py` es una EXTENSIÓN de un
test existente, no suma). `1065 + 15 = 1080` — coincide exacto, sin fallos, sin errores.

### `ai/scripts/heartbeat-run.py --interval 20 -- ./ai/scripts/verify.sh`

```
BUILD_CHECK_PASS
...
Ran 1080 tests in 507.855s

OK (skipped=3)
...
GLOBAL_PORTABILITY_OK
CANONICAL_PATHS_OK
FEATURE_STATE_OK
VERIFY_PASS
```

(`verify.sh` corre su propio `./build.sh --check` primero, después la suite completa de nuevo —
**1080 OK / 3 skips** otra vez, mismo delta +15 —, y termina en `VERIFY_PASS`. Confirmado en la
salida completa: `test_sort_key_tripwire_pins_full_tuple_shape` corre y pasa dentro de esta misma
corrida (`grep -n sort_key_tripwire` sobre el log completo); las 4 clases de
`PinPrecedenceTests` (ADR-0032, `test_spawn_materialization.py`) — el precedente exacto que
`model_request` extiende — también pasan sin cambios: `test_unpinned_default_ordering_is_unchanged`,
`test_role_pin_wins_across_tiers_and_reports_model_pinned`,
`test_global_star_pin_applies_and_role_pin_beats_it`,
`test_ineligible_pin_degrades_to_dynamic_with_pin_unavailable`. Salida completa recortada a los
marcadores; el archivo entero corrido queda en el log de esta sesión.)

### `./build.sh --check`

```
$ ./build.sh --check
SELF_SCAFFOLD_SYNC_OK files=2
GLOBAL_TREE_SYNC_OK profile=go-zen harnesses=4
BUILD_CHECK_PASS
```

### `git diff --check`

```
$ git diff --check; echo "exit=$?"
exit=0
```
(sin salida — limpio.)

## Estado del diff (alcance)

```
$ git status --short -- ai/scripts/ tests/ docs/adr/
 M ai/scripts/routing_core/service.py
 M ai/scripts/set_agents_app.py
 M docs/adr/README.md
 M tests/test_harness.py          <- de P1, ya aceptado, no tocado por este paquete
?? docs/adr/0044-latencia-por-modelo-no-por-sufijo.md   <- de P1, este paquete lo EXTIENDE (no lo crea)
 M tests/test_routing.py
?? tests/test_model_request.py
```

Archivos que este paquete (P2) efectivamente edita: `ai/scripts/routing_core/service.py`,
`ai/scripts/set_agents_app.py`, `docs/adr/0044-latencia-por-modelo-no-por-sufijo.md` (extensión,
sección "Extensión P2"), `docs/adr/README.md` (una línea, resumen del índice), `tests/
test_routing.py` (un test extendido), `tests/test_model_request.py` (nuevo). `tests/test_harness.py`
y la CREACIÓN de `docs/adr/0044-...md` son de P1 (ya aceptado), presentes en el árbol de trabajo sin
commit todavía — no forman parte del diff de este paquete.

## Fuera de alcance / observaciones señaladas, no tocadas

- **`routing_cli.py`'s `_decide_status`** (`ai/scripts/routing_cli.py:57-86`): el filtro que decide
  ok/exit para `--route-decide` sólo excluye los prefijos `RUNTIME_REDIRECTED`/`BILLING_RANK ` antes
  de comparar contra el conjunto cerrado `((), ("REVIEW_IDENTITY_UNVERIFIED",))` — NUNCA excluyó
  `MODEL_PINNED`/`MODEL_PIN_UNAVAILABLE` (ADR-0032, preexistente). Medido: una decisión de REVIEW
  verificada que además carga `MODEL_PINNED ...` en `reason_codes` clasifica como `ok=False`/`exit=1`
  aunque sea una decisión legítima —
  ```
  >>> _decide_status(RouteDecision('rt1_x','claude-code','anthropic','sonnet','sonnet','medium', False, ('MODEL_PINNED anthropic/sonnet',), independence_verified=True))
  (False, 1)
  ```
  Mis nuevos marcadores `MODEL_REQUEST_APPLIED`/`MODEL_REQUEST_UNAVAILABLE` heredan la MISMA
  limitación preexistente (no la crean) cuando aparecen en una decisión de review — por eso los 5
  tests de barrera de AC-05 (dos de ellos son escenarios de review) assertean directo sobre los
  campos de `RouteDecision`, nunca a través de `_decide_status`/el exit code de la CLI. `routing_cli.py`
  no está en el ALCANCE declarado del paquete (`ai/scripts/set_agents_app.py` sí, `routing_cli.py`
  no) — señalado, no tocado; un paquete futuro podría extender el mismo filtro a `MODEL_PINNED`/
  `MODEL_PIN_UNAVAILABLE`/`MODEL_REQUEST_*` de una sola vez.
- El aislamiento roto de los módulos de test (preexistente, ya registrado en 026/P1) no se tocó.
- No se tocó `models.toml` en este paquete (P1 ya fijó `[areas.coord]`; P2 no toca `[areas.*]`).
- No se tocó el orden relativo del sort key existente (`pin_rank`, `TIER_ORDER`, `billing_rank`,
  `_bias_rank`, `is_inferred`, `curated_priority`, `route_id`) — sólo se insertó una columna nueva,
  probado por el tripwire extendido.
- **Interacción pin-vs-instancia, medida, no asumida**: cuando un pin persistente (`--model-pin-set`)
  y un `model_request` efímero nombran identidades ELEGIBLES distintas, **el pin gana** (`pin_rank`
  se evalúa antes que `TIER_ORDER` en la tupla de sort; `model_request` se insertó después) —
  verificado directo:
  ```
  >>> pin={"implementer": ("openai-codex","gpt-5.6-sol")}, model_request=("opencode-go","kimi-k3")
  >>> decision.provider, decision.model, decision.reason_codes
  ('openai-codex', 'gpt-5.6-sol', ('BILLING_RANK provider=openai-codex rank=0',
   'MODEL_PINNED openai-codex/gpt-5.6-sol',
   'MODEL_REQUEST_UNAVAILABLE requested=opencode-go/kimi-k3 reason=OUTRANKED'))
  ```
  Corregido en `docs/adr/0044-...md` (mi primer borrador decía lo contrario, sin medirlo — la
  disciplina de evidencia-sobre-memoria lo cachó antes de cerrar el paquete). Esta interacción NO
  estaba entre los ACs de este paquete y no se tocó `pin_rank` para cambiarla — se documenta tal
  como se mide, no como se asumía.
