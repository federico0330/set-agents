# P3-repair-2 — Ronda 2 (última) — repair-agent

Paquete: 022-disponibilidad-real / P3-liveness-real. Ciclos de review consumidos: 1/2. Alcance de esta
ronda: `ai/scripts/routing_core/catalog.py` + `tests/test_routing.py`.

## Estado

COMPLETO.

## P3-F03 (critical) — el arreglo

`ai/scripts/routing_core/catalog.py`, función `pi_auth_provider_keys()` (definición en línea 348,
`_PAIR_COMMANDS` referenciado en línea ~170 arriba en el archivo, ya existente).

Antes del fix, la última línea de la función era:

```python
return frozenset(key for key in doc if isinstance(key, str))
```

Esto cumplía la mitad de lo que el docstring prometía ("provider NAMES only") — filtraba por tipo de
clave (`str`) pero NUNCA validaba (a) que el proveedor fuera uno de los auditados en `_PAIR_COMMANDS`
para el runtime `pi`, ni (b) que el valor asociado tuviera forma de objeto de credencial. Cualquier
clave string en el JSON de nivel superior — inventada o real pero con valor basura — sobrevivía.

Después del fix (línea final de la función):

```python
audited = {provider for runtime, provider in _PAIR_COMMANDS if runtime == "pi"}
return frozenset(key for key, value in doc.items()
                  if isinstance(key, str) and key in audited and isinstance(value, dict))
```

`audited` es exactamente `{"openai-codex", "anthropic"}` — los dos únicos proveedores que
`_PAIR_COMMANDS` audita para el runtime `pi` (líneas 175-176), que son también los dos únicos
proveedores que el único call site real (`_probe_pairs`, `catalog.py:803`,
`if provider not in pi_auth_provider_keys(): continue`, dentro de la rama `else: # pi`) puede llegar a
preguntar. No hay redefinición de conjunto: se reutiliza la misma tabla `_PAIR_COMMANDS` que ya es la
fuente única de verdad de pares runtime/provider auditados en todo el archivo (ver
`resolve_discovered_providers`, línea 1017, mismo patrón `{provider for _, provider in _PAIR_COMMANDS}`
para su propio caso de uso más amplio).

Por qué cierra P3-F03: el docstring de la función siempre prometió "provider NAMES only" pero la
implementación previa devolvía cualquier clave string sin más — un proveedor inventado, o un
proveedor auditado con valor no-objeto (`[]`, `null`, string, int), pasaba igual. Ahora una entrada
sólo sobrevive si es simultáneamente (a) un proveedor que `pi` audita y (b) tiene forma de objeto de
credencial — exactamente la garantía que el docstring y la firma (`_pi_auth_signature`, que hashea
este mismo keyset) siempre asumieron que existía.

## Los dos casos del hallazgo, reproducidos

### Antes del fix (usando la lógica previa, aislada en un script para no tocar el repo dos veces)

```
ANTES openai-codex_empty_list: doc={'openai-codex': []} -> keyset=frozenset({'openai-codex'}) firma_vacia=False
ANTES invented_provider_object: doc={'proveedor-inventado': {'apiKey': 'x'}} -> keyset=frozenset({'proveedor-inventado'}) firma_vacia=False
```

Coincide byte a byte con lo reproducido por el orquestador.

### Después del fix (código actual del repo, `cat.pi_auth_provider_keys()` real, HOME de fixture)

```
DESPUES openai-codex_empty_list: doc={'openai-codex': []} -> keyset=frozenset() firma_vacia=True
DESPUES invented_provider_object: doc={'proveedor-inventado': {'apiKey': 'x'}} -> keyset=frozenset() firma_vacia=True
```

Los dos casos dan ahora conjunto y firma vacíos, como exige el hallazgo.

## Cuatro formas más de romper el `auth.json` de pi (más allá de las dos del hallazgo)

Todas corridas contra el código actual, todas dan vacío:

```
DESPUES audited_provider_string_value: doc={'anthropic': 'sk-not-an-object'} -> keyset=frozenset() firma_vacia=True
DESPUES audited_provider_null_value: doc={'openai-codex': None} -> keyset=frozenset() firma_vacia=True
DESPUES audited_provider_int_value: doc={'anthropic': 12345} -> keyset=frozenset() firma_vacia=True
DESPUES nested_list_of_objects: doc={'openai-codex': [{'apiKey': 'x'}]} -> keyset=frozenset() firma_vacia=True
```

Bonus, un quinto caso — proveedor real de `_PAIR_COMMANDS` pero NO auditado para `pi` (es un proveedor
opencode), con valor bien formado (objeto):

```
DESPUES unaudited_opencode_provider_object: doc={'opencode-zen': {'apiKey': 'x'}} -> keyset=frozenset() firma_vacia=True
```

Y un caso mixto (para probar que el filtrado es por-clave, no todo-o-nada): un archivo con una entrada
válida y dos inválidas conserva SOLO la válida:

```
DESPUES mixed_valid_and_invalid: doc={'anthropic': {'apiKey': 'ok'}, 'proveedor-inventado': {'apiKey': 'x'}, 'openai-codex': []} -> keyset=frozenset({'anthropic'}) firma_vacia=False
```

## Efecto colateral: `auth.json` legítimo sin cambios

Con los dos proveedores auditados por `pi`, ambos con valor objeto (la forma real que pi escribe):

```
DESPUES legitimo_ambos_auditados: -> keyset=frozenset({'anthropic', 'openai-codex'}) (esperado frozenset({'openai-codex','anthropic'}))
```

Coincide exactamente. Además, los tests preexistentes que ejercitan el keyset legítimo y el gate real de
`_probe_pairs`/`_pi_auth_signature` (que consumen `pi_auth_provider_keys()` sin mockearla, o la mockean
para aislar el resto de la cadena) siguen en verde sin modificación — ver sección "Gates" y la mordida
más abajo. En particular:

- `test_pi_auth_provider_keys_reads_names_only_and_fails_closed` (línea 321, preexistente, sin tocar):
  usa `{"anthropic":{"apiKey":"sk-should-never-be-read"},"openai-codex":{"apiKey":"also-secret"}}` como
  caso legítimo y sigue esperando `frozenset({"anthropic","openai-codex"})` — pasa igual.
- `test_adr0043_ac09_credential_signatures_fail_closed_on_symlink_and_corrupt_or_foreign_shaped_json`
  (codex/claude-code, no toca pi) — no afectado por este cambio, sigue en verde (ver barrida abajo, no
  necesitó modificación).
- `_probe_pairs` (`catalog.py:803`) sigue llamando `pi_auth_provider_keys()` directamente, sin cambios
  de firma ni de contrato — el gate real de autenticación no se tocó, sólo se corrigió el conjunto que
  ese gate consulta.

## La barrida

### Funciones que leen archivos de credenciales bajo `~` (grep sobre `Path.home()`, `.pi/`, `.codex/`,
`.claude/`, `auth.json`, `credentials.json` en `catalog.py`)

| Función | Archivo que lee | Estado antes de esta ronda | Acción |
|---|---|---|---|
| `pi_auth_provider_keys()` (catalog.py:348) | `~/.pi/agent/auth.json` | **P3-F03: no filtraba por proveedor auditado ni por forma de valor** | **Arreglado** (ver arriba) |
| `_read_credential_json()` (catalog.py:414) | genérico (recibe `Path`) — helper compartido por las dos firmas de abajo | Ya validaba `lstat` (no symlink), archivo regular, uid propio, JSON válido, `dict` top-level. Deliberadamente NO valida campos anidados (eso es responsabilidad del caller, por diseño — así lo documenta su propio docstring) | Sin cambios — ya correcto, el reparto de responsabilidad ya estaba bien |
| `_codex_auth_signature()` (catalog.py:431) | `~/.codex/auth.json` | Ya valida `tokens` es `dict` y `tokens.account_id` es `str` antes de hashear (repair P3-SEC-001, ronda anterior) | Sin cambios — ya correcto, confirmado con el test existente (ver abajo) |
| `_claude_code_auth_signature()` (catalog.py:468) | `~/.claude/.credentials.json` | Ya valida `claudeAiOauth` es `dict` y sus tres campos (`scopes` lista, `subscriptionType`/`rateLimitTier` string) antes de hashear (repair P3-SEC-001, ronda anterior) | Sin cambios — ya correcto |
| `_pi_auth_signature()` (catalog.py:505) | depende de `pi_auth_provider_keys()`, ningún acceso a archivo propio | Ya fail-closed a `""` si el keyset viene vacío (repair P3-SEC-002, ronda anterior) — ahora hereda automáticamente el filtrado más estricto de `pi_auth_provider_keys()` sin cambio de código propio | Sin cambios — se beneficia gratis del fix de arriba |
| `_live_opencode_auth_signature()` (catalog.py:532) | ninguno directo — subprocess `opencode auth list --pure`, texto parseado por `_parse_opencode_auth` | Ya fail-closed (`OSError`/`TimeoutExpired`/returncode!=0/`RoutingError` -> `""`) | Sin cambios — no lee archivo bajo `~`, fuera del patrón de este hallazgo |
| `_parse_claude_auth()` (catalog.py:289) | ninguno directo — parsea stdout de `claude auth status --json` | Ya valida `isinstance(doc, dict) and doc.get("loggedIn") is True`; una excepción de `json.loads` la captura el caller (`_probe_pairs`, `except (..., ValueError, ...)`) | Sin cambios — no lee archivo, ya fail-closed en la forma que importa |
| `_parse_opencode_auth()` / `_parse_pi_models()` / `_parse_codex_login()` | ninguno directo — parsean texto/stdout de subprocess | Cada uno ya falla cerrado ante forma inesperada (`RoutingError` en los dos primeros, `bool()` de línea vacía en el tercero) | Sin cambios — no leen archivos de credenciales bajo `~` |
| `_read_probe_cache()` (catalog.py:599) y el lector de caché embebido en `route_doctor` (catalog.py:~1108) | `<cache_root>/probe-cache.json` — caché propio del proceso de ruteo, NO un archivo de credenciales de terceros | Ya validan `lstat`/regular/uid/modo 0o600, `dict` top-level, `pairs` es `dict`, cada `(runtime, provider)` está en `_PAIR_COMMANDS`, cada lista de modelos son todos `str` | Sin cambios — fuera del alcance de "credenciales" (es el caché interno, no un `auth.json`/`credentials.json` de una CLI de terceros), pero revisado igual y ya es sólido |

Búsqueda hecha fuera de `catalog.py` (sólo para descartar otro lector de credenciales de terceros, sin
tocar nada fuera de alcance): `grep -rn "Path.home()\|\.pi/agent\|\.codex/auth\|\.claude/\.credentials\|auth\.json\|credentials\.json" ai/scripts --include="*.py"`.
Único hallazgo relevante: `ai/scripts/set_agents_app.py:1080`, función `auth_state()`, rama `claude` —
```python
credentials = Path.home() / ".claude/.credentials.json"
return "ok" if credentials.exists() and credentials.stat().st_size > 0 else "needed"
```
Esto NUNCA abre ni parsea el archivo como JSON (sólo `.exists()`/`.stat().st_size`), así que no hay
forma/tipo que validar — no es una guarda floja (no promete validar forma que luego no valida), es un
heurístico de presencia para el status humano de `set-agents --status`, ya documentado como tal en el
comentario adyacente ("no stable status command; same heuristic install.sh uses"). Fuera de alcance
(no es `catalog.py`) y no amerita anotarse como hallazgo aparte porque no hay brecha entre lo que dice
hacer y lo que hace.

### Tests que afirman cubrir "foreign shape"/"corrupt"/"malformed" para credenciales (grep sobre
docstrings/nombres en `tests/test_routing.py`, filtrado a los relacionados con pi/codex/claude-code)

| Test | Qué decía cubrir | Qué cubría de verdad antes de esta ronda | Acción |
|---|---|---|---|
| `test_pi_auth_provider_keys_reads_names_only_and_fails_closed` (línea 321) | "Missing file, foreign JSON shape, and corrupt JSON all fail closed to empty" (comentario línea 328) | Sólo probaba forma ajena como **lista top-level** (`["not","a","dict"]`) — ya rechazada por el `isinstance(doc, dict)` anterior al bucle. Nunca probó un objeto top-level con clave no auditada o con valor no-objeto — exactamente el hueco de P3-F03. Es el mismo test que la ronda 1 de repair ya había señalado como insuficiente (ver tabla del enunciado, fila 4) sin cerrarlo del todo. | **Se agregó un test nuevo dedicado** (no se debilitó el existente, que sigue intacto y sigue en verde): `test_pi_auth_provider_keys_rejects_unaudited_and_non_object_entries` (después de la línea 351), con 6 formas de romper el archivo + 1 caso mixto + 1 caso de control legítimo |
| `test_adr0043_ac09_credential_signatures_fail_closed_on_symlink_and_corrupt_or_foreign_shaped_json` (línea 4140, codex/claude-code) | "a symlink is never followed, and corrupt/foreign-shaped JSON never raises" | Ya cubre objetos inválidos de verdad (objeto vacío, campo con tipo incorrecto, objeto parcialmente poblado) para AMBOS codex y claude-code — no sólo listas. Es el test que P3-SEC-001 (ronda anterior) ya corrigió correctamente. No miente: su alcance (codex/claude-code) nunca incluyó pi, y no lo pretende. | Sin cambios — ya cubre lo que dice cubrir, para los dos runtimes que le corresponden |
| `test_adr0043_ac07_pi_auth_signature_folds_provider_keys_and_the_pinned_version` / `test_adr0043_p3sec002_repair_pi_auth_signature_never_participates_in_the_real_authentication_decision` (líneas 4002/4023) | Cubren `_pi_auth_signature`/el gate real, mockeando `pi_auth_provider_keys` directamente | No ejercitan el archivo real, así que no podían ni prometían cubrir P3-F03 — mockean la función bajo prueba, no su lectura de disco | Sin cambios — alcance correcto, no aplica |

Ninguna guarda floja encontrada fuera de `catalog.py`/`tests/test_routing.py` dentro del ámbito de
credenciales de terceros (pi/codex/claude/opencode). No hay nada que anotar para el orquestador en esta
categoría.

## La mordida del test tocado, en las dos direcciones

Test nuevo: `test_pi_auth_provider_keys_rejects_unaudited_and_non_object_entries`.

Rojo, corrido contra el archivo real del repo con la línea del fix revertida temporalmente in-place
(vía `cp` de respaldo/restauración; jamás `git checkout`/`restore`/`stash`, tal como exige el
enunciado — se restauró el archivo arreglado apenas terminó esta corrida):

```
FAIL: test_pi_auth_provider_keys_rejects_unaudited_and_non_object_entries (tests.test_routing.RoutingTests.test_pi_auth_provider_keys_rejects_unaudited_and_non_object_entries)
AssertionError: Items in the first set but not the second:
'openai-codex' : expected empty keyset for {'openai-codex': []}
Ran 1 test in 0.005s
FAILED (failures=1)
```

Verde (código actual, con el fix aplicado):

```
test_pi_auth_provider_keys_rejects_unaudited_and_non_object_entries (tests.test_routing.RoutingTests.test_pi_auth_provider_keys_rejects_unaudited_and_non_object_entries)
P3-F03 repair (022 PKG-3 repair round 2): the docstring above has always ... ok
test_pi_auth_provider_keys_reads_names_only_and_fails_closed (tests.test_routing.RoutingTests.test_pi_auth_provider_keys_reads_names_only_and_fails_closed) ... ok

Ran 2 tests in 0.008s

OK
```

Adicional (sin tocar, prueba de no-regresión de la cadena que depende de `pi_auth_provider_keys`):

```
test_adr0043_ac07_pi_auth_signature_folds_provider_keys_and_the_pinned_version ... ok
test_adr0043_p3sec002_repair_pi_auth_signature_never_participates_in_the_real_authentication_decision ... ok

Ran 2 tests in 0.006s

OK
```

## Gates

Los cuatro corrieron completos, en este orden, después de aplicado el fix + el test nuevo:

### `ai/scripts/heartbeat-run.py --interval 20 -- python3 -m unittest discover -s tests`

```
Ran 1008 tests in 684.056s

OK (skipped=3)
```

1008 = 1007 base + 1 test nuevo (`test_pi_auth_provider_keys_rejects_unaudited_and_non_object_entries`).
Mismos 3 skips que la base. Cero regresiones.

### `ai/scripts/heartbeat-run.py --interval 20 -- ./ai/scripts/verify.sh`

```
Ran 1008 tests in 718.402s

OK (skipped=3)
GLOBAL_PORTABILITY_OK
CANONICAL_PATHS_OK
FEATURE_STATE_OK
VERIFY_PASS
```

(`verify.sh` corre su propio `BUILD_CHECK_PASS`/`GLOBAL_TREE_SYNC_OK` al principio, ya vistos arriba, y
la suite completa de nuevo internamente antes de sus chequeos propios — el veredicto final es
`VERIFY_PASS`.)

### `./build.sh --check`

```
SELF_SCAFFOLD_SYNC_OK files=2
GLOBAL_TREE_SYNC_OK profile=go-zen harnesses=4
BUILD_CHECK_PASS
```

### `git diff --check`

Sin salida, exit code 0 (sin errores de whitespace).

## Qué no pude verificar

Nada quedó sin verificar dentro del alcance (`catalog.py` + `tests/test_routing.py`): los dos casos del
hallazgo, las cuatro (en realidad seis) formas adicionales de romper el archivo, el caso legítimo de
no-regresión, la mordida en las dos direcciones y los cuatro gates corrieron todos, con salida literal
pegada arriba.

Un dato que quedó fuera de mi alcance explícito y que el propio enunciado reserva para el orquestador:
la captura A/B del efecto colateral a nivel de todo el paquete (más allá de la prueba puntual de
no-regresión que sí corrí acá, aislada a `pi_auth_provider_keys`/`_pi_auth_signature`/`_probe_pairs`).
