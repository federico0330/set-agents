# P1-registro-de-proveedores — evidencia del implementer

Estado: COMPLETO (ver gates al final).

## Diseño — dónde vive `PROVIDERS`, con la medición

Medición ANTES de escribir código (`grep -rn`, limpio):

```
$ grep -rn "models_config" ai/scripts/routing_core/*.py
ai/scripts/routing_core/catalog.py:203:    # added two more in models_config.py) — this key map is site (2) of 5 that must move
ai/scripts/routing_core/catalog.py:206:    # models_config.load_config's optional-key validation loop for the same two TOML
ai/scripts/routing_core/catalog.py:207:    # keys; (5) models_config.emit's preservation loop for the same two keys (without
ai/scripts/routing_core/catalog.py:211:    # models_config.py sites is read here (fine) but never survives a re-emit (data
ai/scripts/routing_core/catalog.py:698:    as-is (already validated against `DISCOVERABLE_PROVIDERS` at models_config load time);
ai/scripts/routing_core/service.py:121:        # models_config.py already uses for a value that is never itself serialized back
ai/scripts/routing_core/service.py:136:        # a config that skips models_config validation (e.g. a bare {} in a unit test),
```
Solo comentarios; ningún `import`. `catalog.py` no importa `models_config` hoy.

```
$ grep -n "^import\|^from" ai/scripts/models_config.py
import csv / json / re / sys / tomllib / os / tempfile
from pathlib import Path
```
Ningún import de `routing_core` a nivel de módulo (confirmado antes de mi cambio).
`detect_subscriptions` (`:250-267` original) y `auto_profile` (`:269-286` original) hacen
`from routing_core.catalog import probe_inventory` **adentro del cuerpo de la función**, con
docstring explícito: *"Lazy import (no routing_core dependency at module load)"*.

```
$ cat ai/scripts/routing_core/__init__.py
"""Trusted routing-v2 domain and adapters.  The package has no CLI imports."""
from .domain import (...)
from .service import RoutingService
from .store import RoutingStore
```
`routing_core/__init__.py` importa `.service` y `.store` **incondicionalmente**. `service.py`
importa `from .catalog import build_snapshot, ...`. `store.py` importa `sqlite3`, `pwd`,
`secrets`, etc. Consecuencia medida: **cualquier** import de un submódulo de `routing_core`
(`from routing_core.X import Y`, sin importar cuál `X`) ejecuta primero ese `__init__.py`, que
carga `sqlite3`/`subprocess`/toda la maquinaria de `service.py`+`store.py` — el costo exacto que
el docstring de `models_config.py:250-251` existe para evitar en el import a nivel de módulo.

**Conclusión, argumentada, no estética:** `PROVIDERS` no puede vivir dentro de `routing_core`
(pagaría ese costo en cada `import models_config`) ni dentro de `models_config.py` (invertiría
la dirección de dependencia que `routing_core/__init__.py` declara — "no CLI imports" — porque
`models_config.py` es un módulo de aplicación: lee `models.toml` de disco, hace `die()`). Vive en
un módulo nuevo, neutro, fuera de ambos: `ai/scripts/provider_registry.py`, con cero imports
propios más allá de `dataclasses` de la librería estándar. Desarrollo completo de la decisión:
`docs/adr/0042-provider-registry-single-source.md`.

## Los siete símbolos y su derivación

| # | Símbolo | Ubicación (post-cambio) | Deriva de |
|---|---|---|---|
| 1 | `_OPENCODE_PROVIDER_KEYS` | `routing_core/catalog.py:129` | `{p: spec.opencode_auth_key for p, spec in PROVIDERS.items()}` |
| 2 | `_OPENCODE_CLI_IDS` | `catalog.py:137` | `{p: spec.opencode_cli_id for p, spec in PROVIDERS.items()}` |
| 3 | `_PAIR_COMMANDS` | `catalog.py:165-172` | sin cambio de código — su mitad `opencode` ya derivaba de `_OPENCODE_CLI_IDS` desde 012/F-05, y ese ahora deriva transitivamente de `PROVIDERS` |
| 4 | `PROVIDER_BILLING_KIND` | `catalog.py:184` | `{p: spec.billing_kind for p, spec in PROVIDERS.items()}` |
| 5 | key map de `_configured_models` (ahora `_CATALOG_KEYS`, módulo-nivel) | `catalog.py:218` | `{p: spec.catalog_key for p, spec in PROVIDERS.items()}` |
| 6 | `DISCOVERABLE_PROVIDERS` | `models_config.py:55` | `set(provider_registry.PROVIDERS)` |
| 7 | `_MODEL_PREFERENCE_PROVIDERS` | `set_agents_app.py:106` | `tuple(provider_registry.PROVIDERS)` |

Fuente única: `ai/scripts/provider_registry.py` — `PROVIDERS: dict[str, ProviderSpec]`, cuatro
campos por proveedor (`opencode_auth_key`, `opencode_cli_id`, `billing_kind`, `catalog_key`),
orden de inserción `("openai-codex", "anthropic", "opencode-zen", "opencode-go")` — el orden es
el contrato que hace determinística la tupla #7 (nunca derivada de `DISCOVERABLE_PROVIDERS`, que
es un `set` sin orden).

## Conteo "seis" vs "siete", resuelto

La spec (`spec.md` PKG-1) narra "de seis entradas en lockstep manual a una fila" pero el context
pack mide y nombra **siete** símbolos. Resuelto así (y así quedó en ADR-0042):

- **Seis** son duplicados verdaderamente **manuales** — antes de este paquete, nada los ligaba
  entre sí salvo la disciplina humana: `_OPENCODE_PROVIDER_KEYS`, `_OPENCODE_CLI_IDS`,
  `PROVIDER_BILLING_KIND`, la key map de `_configured_models`, `DISCOVERABLE_PROVIDERS`,
  `_MODEL_PREFERENCE_PROVIDERS`.
- El **séptimo**, `_PAIR_COMMANDS`, ya NO era un duplicado manual antes de este paquete: su
  mitad `opencode` deriva de `_OPENCODE_CLI_IDS` desde el repair F-05 de la feature 012
  (`catalog.py`, comprehension, no literal). Sigue siendo uno de los siete símbolos medidos
  porque también codifica identidad de proveedor (sus dos pares no-opencode) y porque, ahora,
  depende TRANSITIVAMENTE de `PROVIDERS` a través de `_OPENCODE_CLI_IDS` — pero no sumaba un
  duplicado nuevo que este paquete tuviera que eliminar.

"Seis" cuenta lo que había que dejar de duplicar a mano; "siete" cuenta todos los símbolos
medidos que ya no pueden divergir entre sí después de este paquete.

## Tabla AC → cambio → prueba

| AC | Cambio | archivo:línea | Prueba |
|---|---|---|---|
| AC-01 | `PROVIDERS: dict[str, ProviderSpec]`, módulo nuevo | `ai/scripts/provider_registry.py:1-70` | `test_adr0042_ac01_ac02_all_seven_provider_tables_are_byte_identical_to_the_pre_refactor_literals` (`tests/test_routing.py:4010`) |
| AC-01 | `_OPENCODE_PROVIDER_KEYS`/`_OPENCODE_CLI_IDS` derivadas | `catalog.py:129,137` | mismo test arriba + `test_ac02_ac03_credential_and_cli_id_maps_are_independently_addressable` (`:3127`, sin editar) |
| AC-01 | `PROVIDER_BILLING_KIND` derivada | `catalog.py:184` | mismo test arriba + `test_ac08_subscription_metered_map_is_provider_keyed_not_a_row_field` (`:3257`, sin editar) |
| AC-01 | `_CATALOG_KEYS` nueva (antes literal inline en `_configured_models`) | `catalog.py:211-218,236` | `test_adr0042_ac01_ac02_...` (`:4010`) |
| AC-01 | `DISCOVERABLE_PROVIDERS` derivada | `models_config.py:55` | mismo test arriba + `test_adr0034_ac10_discoverable_providers_lockstep_guard` (`:3192`, sin editar) |
| AC-01 | `_MODEL_PREFERENCE_PROVIDERS` derivada | `set_agents_app.py:106` | mismo test arriba + `test_adr0034_ac09_write_cli_validates_pins_against_the_effective_set_not_just_the_constant` (`:3958` post-inserción, sin editar) |
| AC-01b | guarda real: `_MODEL_PREFERENCE_PROVIDERS` contra la fuente (`_PAIR_COMMANDS` y `provider_registry.PROVIDERS`), nunca contra un literal en otro test | — | `test_adr0042_ac01b_model_preference_providers_is_guarded_against_the_real_source` (`tests/test_routing.py:4042`) |
| AC-02 | caracterización byte-idéntica de los siete símbolos | — | `test_adr0042_ac01_ac02_all_seven_provider_tables_are_byte_identical_to_the_pre_refactor_literals` (`:4010`) |
| AC-02 | tests preexistentes sin editar siguen verdes | — | ver sección siguiente |
| AC-03 | ADR-0042 primero, corrige `ADR-0034:124-126` con la medición, sin editar ADR-0034 | `docs/adr/0042-provider-registry-single-source.md` (sección "Decisión", punto 7), indexado en `docs/adr/README.md` | lectura directa del ADR (no hay test automatizado para prosa de ADR) |

## Prueba de que los tests preexistentes pasan SIN editarlos

```
$ python3 -m unittest tests.test_routing.RoutingTests.test_adr0034_ac10_discoverable_providers_lockstep_guard tests.test_routing.RoutingTests.test_ac02_ac03_credential_and_cli_id_maps_are_independently_addressable tests.test_routing.RoutingTests.test_ac08_subscription_metered_map_is_provider_keyed_not_a_row_field tests.test_routing.RoutingTests.test_adr0034_ac09_write_cli_validates_pins_against_the_effective_set_not_just_the_constant -v
test_adr0034_ac10_discoverable_providers_lockstep_guard ... ok
test_ac02_ac03_credential_and_cli_id_maps_are_independently_addressable ... ok
test_ac08_subscription_metered_map_is_provider_keyed_not_a_row_field ... ok
test_adr0034_ac09_write_cli_validates_pins_against_the_effective_set_not_just_the_constant ... ok

----------------------------------------------------------------------
Ran 4 tests in 0.010s

OK
```
`git diff tests/test_routing.py` (pegado más abajo) prueba que estas cuatro funciones no fueron
tocadas: el único cambio en ese archivo es el `import provider_registry` nuevo y el bloque de dos
funciones nuevas insertado entre `test_adr0034_m1_github_copilot_never_gets_an_audited_pair_even_
authenticated` y el comentario `# --------------------------------------------- 014-model-
preference-policy`.

## Por cada test nuevo: neutralizar, confirmar rojo, revertir

### `test_adr0042_ac01_ac02_all_seven_provider_tables_are_byte_identical_to_the_pre_refactor_literals`

Mutación: `provider_registry.py`, `opencode-go`'s `billing_kind` de `"subscription"` a
`"metered"` (vía script Python, no `git`).

```
$ python3 -m unittest tests.test_routing.RoutingTests.test_adr0042_ac01_ac02_all_seven_provider_tables_are_byte_identical_to_the_pre_refactor_literals -v
...
AssertionError: {'ope[51 chars]ion', 'opencode-zen': 'metered', 'opencode-go': 'metered'} != {'ope[51 chars]ion', 'opencode-go': 'subscription', 'opencode-zen': 'metered'}
  {'anthropic': 'subscription',
   'openai-codex': 'subscription',
-  'opencode-go': 'metered',
+  'opencode-go': 'subscription',
   'opencode-zen': 'metered'}
----------------------------------------------------------------------
Ran 1 test in 0.004s
FAILED (failures=1)
```

Revert (`cp` desde el backup tomado antes de mutar, `diff` confirma identidad):

```
$ cp "$SCRATCH/backup/provider_registry.py.orig" ai/scripts/provider_registry.py
$ diff "$SCRATCH/backup/provider_registry.py.orig" ai/scripts/provider_registry.py && echo "REVERT_OK identical"
REVERT_OK identical
$ python3 -m unittest tests.test_routing.RoutingTests.test_adr0042_ac01_ac02_all_seven_provider_tables_are_byte_identical_to_the_pre_refactor_literals -v
... ok
Ran 1 test in 0.002s
OK
```

### `test_adr0042_ac01b_model_preference_providers_is_guarded_against_the_real_source`

Dos mutaciones independientes de `set_agents_app.py` (una por cada cross-check del test),
cada una revertida con `cp` desde el backup antes de la siguiente.

**Mutación 1** — reproduce el defecto real que este paquete cierra: un `_MODEL_PREFERENCE_
PROVIDERS` hardcodeado, ahora con un proveedor menos (`opencode-go` faltante):

```
_MODEL_PREFERENCE_PROVIDERS = ("openai-codex", "anthropic", "opencode-zen")  # TEMP
```
```
$ python3 -m unittest tests.test_routing.RoutingTests.test_adr0042_ac01b_model_preference_providers_is_guarded_against_the_real_source -v
FAIL
AssertionError: Items in the second set but not the first: 'opencode-go'
Ran 1 test in 0.004s
FAILED (failures=1)
```
(el cross-check 1, contra `_PAIR_COMMANDS`, ya detecta esto — nunca llega a evaluar el cross-check 2)

**Mutación 2** (tras revertir la 1) — mismo *set* de cuatro proveedores, orden distinto (prueba
que el cross-check 1, por sets, NO alcanza solo — hace falta el cross-check 2, por tupla):

```
_MODEL_PREFERENCE_PROVIDERS = ("anthropic", "openai-codex", "opencode-zen", "opencode-go")  # TEMP
```
```
$ python3 -m unittest tests.test_routing.RoutingTests.test_adr0042_ac01b_model_preference_providers_is_guarded_against_the_real_source -v
FAIL
AssertionError: Tuples differ: ('anthropic', 'openai-codex', 'opencode-zen', 'opencode-go') != ('openai-codex', 'anthropic', 'opencode-zen', 'opencode-go')
Ran 1 test in 0.005s
FAILED (failures=1)
```

Revert final y verde:

```
$ cp "$SCRATCH/backup/set_agents_app.py.orig" ai/scripts/set_agents_app.py
$ diff "$SCRATCH/backup/set_agents_app.py.orig" ai/scripts/set_agents_app.py && echo "REVERT_OK identical"
REVERT_OK identical
$ python3 -m unittest tests.test_routing.RoutingTests.test_adr0042_ac01b_model_preference_providers_is_guarded_against_the_real_source tests.test_routing.RoutingTests.test_adr0042_ac01_ac02_all_seven_provider_tables_are_byte_identical_to_the_pre_refactor_literals -v
... ok
... ok
Ran 2 tests in 0.004s
OK
```

Nota: el backup `set_agents_app.py.orig` usado para el revert de la Mutación 2 es el mismo
tomado ANTES de la Mutación 1 (archivo intacto de mi propio cambio de implementación, sin
ninguna de las dos mutaciones de prueba) — verificado con `diff` contra el estado real tras cada
revert, no asumido.

## Un defecto real que este mismo ejercicio encontró (y por qué el gate completo importa)

La primera redacción de mi corrección al comentario de `set_agents_app.py:92-104` (el no-goal de
AC-06) escribió el símbolo `PROVIDER_BILLING_KIND` **en texto libre, dos veces**, para explicar
por qué seguía sin usarse. Eso rompió `test_ac06_no_provider_billing_kind_reference_in_new_code`
(`tests/test_routing.py:4817-4820`, doctrina de 014-model-preference-policy, sin relación
aparente con este paquete) — un `assertNotIn("PROVIDER_BILLING_KIND", ...)` literal sobre el
archivo completo, que no distingue código de comentario. Lo encontró la corrida completa de
`tests.test_routing` (258 tests, ver abajo), no ninguna corrida dirigida mía. Corregido
reescribiendo el comentario para nombrar la tabla por perífrasis ("the catalog module's own
billing-kind classification table"), como ya hacía el comentario ORIGINAL antes de mi edición —
nunca por símbolo literal. Re-verificado:

```
$ grep -n "PROVIDER_BILLING_KIND" ai/scripts/set_agents_app.py
(sin salida)
$ python3 -m unittest tests.test_routing.RoutingTests.test_ac06_no_provider_billing_kind_reference_in_new_code -v
... ok
Ran 1 test in 0.003s
OK
```

## Gates

### `python3 -m unittest tests.test_routing -v` (módulo completo, corrida directa, PRE-fix)

Esta corrida es la que encontró el defecto real de arriba (`PROVIDER_BILLING_KIND` en
comentario) — corrió ANTES del arreglo, con el archivo de prueba nuevo ya en su lugar:

```
Ran 258 tests in 152.674s
FAILED (failures=1)
FAIL: test_ac06_no_provider_billing_kind_reference_in_new_code
```

No volví a correr el módulo completo (258 tests, ~2.5 min) una segunda vez tras el arreglo —
sería redundante con el gate 1 de abajo, que corre `tests/test_routing.py` íntegro como parte
de `discover`. Lo que sí corrí, dirigido, post-fix: el test que había fallado
(`test_ac06_no_provider_billing_kind_reference_in_new_code`, verde, pegado arriba) y los seis
tests nuevos/afectados de esta sección (también verdes, pegados arriba). El veredicto real de
"todo `test_routing.py` en verde, con el arreglo puesto" es el que da el gate 1.

### Gate 1 — `heartbeat-run.py -- python3 -m unittest discover -s tests`

Corrida completa, con el arreglo de `test_ac06_no_provider_billing_kind_reference_in_new_code`
ya puesto (backgrounded vía `run_in_background`, seguida con `tail -f --pid=<heartbeat-run pid>`
para no perder salida — nunca `| tail -N` sin `-f`, ADR-0041):

```
$ ai/scripts/heartbeat-run.py --interval 20 -- python3 -m unittest discover -s tests
[... heartbeats cada 20s mientras corre, ~515s totales ...]
----------------------------------------------------------------------
Ran 981 tests in 515.551s

OK (skipped=3)
```
Los 3 `skipped` son los gates credencial-gated ya documentados en la suite (p.ej.
`test_ac10_p2_local_live_parity_gate`, exento por diseño, spec de 012) — no relacionados con
este paquete.

### Gate 2 — `heartbeat-run.py -- ./ai/scripts/verify.sh`

```
$ ai/scripts/heartbeat-run.py --interval 20 -- ./ai/scripts/verify.sh
SELF_SCAFFOLD_SYNC_OK files=2
GLOBAL_TREE_SYNC_OK profile=go-zen harnesses=4
BUILD_CHECK_PASS
[... suite completa, 981 tests, 455.124s ...]
Ran 981 tests in 455.124s

OK (skipped=3)
VERIFY_PASS
```

### Gate 3 — `./build.sh --check` (re-corrido al final, tras los gates 1/2)

```
$ ./build.sh --check
SELF_SCAFFOLD_SYNC_OK files=2
GLOBAL_TREE_SYNC_OK profile=go-zen harnesses=4
BUILD_CHECK_PASS
```

### Gate 4 — `git diff --check` (re-corrido al final)

```
$ git diff --check
(sin salida, exit 0)
```

## Fuera de alcance, no tocado

`catalog.py`'s techo `[catalog]` tri-estado (P2), `_probe_pairs`, el sort key de `service.py:382`,
Copilot, `providers.toml`/`--provider-*` (P4), altas/bajas automáticas (P5). Ningún refactor
oportunista de `catalog.py` más allá de las cuatro tablas nombradas en AC-01.

## Supuestos sin verificar

Ninguno — todo lo afirmado arriba corrió en esta sesión y quedó pegado.
