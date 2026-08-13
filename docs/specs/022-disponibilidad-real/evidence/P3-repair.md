# P3-liveness-real — evidencia del repair (P3-SEC-001 / P3-SEC-002)

Estado: **COMPLETO**

Alcance tocado: `ai/scripts/routing_core/catalog.py`, `tests/test_routing.py`. Ningún tercer
archivo. Nunca se corrió `logout`, nunca se forzó un refresh, nunca se escribió en
`~/.claude`, `~/.codex`, `~/.pi` ni `~/.local/share/opencode` reales — todo con `HOME` de
fixture vía `tempfile.TemporaryDirectory()` / `mock.patch.object(cat.Path, "home", ...)`.
Ningún valor de credencial fue pegado en este documento, solo nombres de campo y hashes
sha256 (que nunca son material de credencial).

## Reproducción, ANTES del fix (fixture `HOME`)

Fixture: `.codex/auth.json` = `{}` (0600, uid propio), `.claude/.credentials.json` =
`{"claudeAiOauth":{}}` (0600, uid propio), sin `.pi/agent/auth.json` (directorio ausente).
Script: `/var/tmp/.../scratchpad/repro.py` (`mock.patch.object(cat.Path, "home", ...)`,
nunca toca el `HOME` real).

```
$ python3 /var/tmp/.../scratchpad/repro.py
P3-SEC-001 codex  {}                     -> firma vacia? False  (repr='145b4b380a01a1ae1d0794d94756f54fd5ff23e872e99b3cb7c01cd28819e7fb')
P3-SEC-001 claude {'claudeAiOauth':{}}   -> firma vacia? False  (repr='305a9233bef80292fc22e98621b3ee339a3eacbd8a8e39a996d2b9b437b5db68')
P3-SEC-002 pi     (archivo AUSENTE)      -> firma vacia? False  (repr='1dc52220fe44d06e20b12bd191e73ea2f2b94a701fe2315d401441e95a8dbbba')  keys=frozenset()
```

Los tres reproducen exactamente lo reportado por el orquestador: ninguna firma vacía pese a
que las tres condiciones (JSON de forma inválida, archivo ausente) exigen fail-closed (AC-09).

## DESPUÉS del fix — mismo script, mismo fixture, sin tocarlo

```
$ python3 /var/tmp/.../scratchpad/repro.py
P3-SEC-001 codex  {}                     -> firma vacia? True  (repr='')
P3-SEC-001 claude {'claudeAiOauth':{}}   -> firma vacia? True  (repr='')
P3-SEC-002 pi     (archivo AUSENTE)      -> firma vacia? True  (repr='')  keys=frozenset()
```

Los tres, vacíos.

## Por hallazgo: qué cambié y por qué cierra

### P3-F01 (critical) — validar forma y tipos antes de hashear

**`ai/scripts/routing_core/catalog.py:444-465`** (`_codex_auth_signature`): antes,
`tokens.get("account_id")` se leía con `isinstance(tokens, dict)` como única guarda, y si
`tokens` faltaba o `account_id` no era `str`, el código igual seguía y hasheaba
`"account_id=|api_key_present=False"` — un hash válido, no vacío. Ahora: `tokens` debe ser
`dict` (si no, `return ""`) y `tokens.get("account_id")` debe ser `str` (si no, `return
""`) — la validación de forma/tipo corre **antes** de construir `material` y hashear.

**`ai/scripts/routing_core/catalog.py:481-502`** (`_claude_code_auth_signature`): antes,
`oauth.get(field)` para cada uno de los tres campos se pasaba directo a `str(...)` — un campo
ausente producía el string literal `"None"`, que igual se hasheaba. Ahora: `scopes` debe ser
`list`, `subscriptionType`/`rateLimitTier` deben ser `str` — si cualquiera falla el chequeo de
tipo, `return ""` antes de tocar `hashlib`.

Por qué cierra: en ambos casos, el hash ya no puede construirse a partir de valores
placeholder (`""`, `"None"`, `False`) que resultan de un `.get()` sobre un campo ausente —
la ausencia o el tipo incorrecto de un campo REQUERIDO corta el camino antes del `return
hashlib.sha256(...)`, así que el ÚNICO camino que produce una firma no vacía es uno donde
todos los campos leídos existen y tienen el tipo esperado.

**El test que decía cubrir esto** (`tests/test_routing.py`,
`test_adr0043_ac09_credential_signatures_fail_closed_on_symlink_and_corrupt_or_foreign_shaped_json`)
quedó extendido (mismo nombre, docstring corregido) con los casos que antes no
ejercitaba: objeto vacío (`{}` / `{"claudeAiOauth": {}}` — la forma exacta reproducida
arriba), campo de tipo erróneo (`tokens` una lista, `account_id` un int, `scopes` un
string), y objeto parcialmente poblado (`tokens: {}` sin `account_id`, `claudeAiOauth`
sin `rateLimitTier`) — para codex y claude-code. Cierra un control de contorno: al final
del test, una forma completamente válida sigue produciendo una firma no vacía
(`assertTrue`), para probar que la nueva validación rechaza formas malas, no todo.

### P3-F02 (high) — uid en `pi_auth_provider_keys`, fail-closed real en `_pi_auth_signature`

**`ai/scripts/routing_core/catalog.py:361-363`** (`pi_auth_provider_keys`): agregada
`st.st_uid != os.getuid()` al chequeo existente de symlink/regular-file — la misma
disciplina que `_read_credential_json` ya tenía. Antes, un `~/.pi/agent/auth.json` de otro
uid en la misma máquina se leía igual y sus claves se plegaban tanto en `_pi_auth_signature`
(cache) como en el gate real de decisión (`_probe_pairs`, `catalog.py:803`,
`if provider not in pi_auth_provider_keys(): continue`) — este fix cierra las dos
superficies con un solo cambio, porque ambas llaman a la misma función.

**`ai/scripts/routing_core/catalog.py:521-528`** (`_pi_auth_signature`): antes,
`",".join(sorted(pi_auth_provider_keys()))` con un conjunto vacío producía `""` (nombres) que
IGUAL se hasheaba junto con `PI_PINNED_VERSION`, dando un hash fijo no vacío para "pi sin
credenciales válidas". Ahora: si `pi_auth_provider_keys()` devuelve un conjunto vacío,
`_pi_auth_signature()` devuelve `""` directamente, sin llegar a `hashlib.sha256`.

**Verificación de que la firma vacía sólo produce cache miss, nunca una decisión distinta**
(pedido explícito de la consigna): `_pi_auth_signature()` tiene un único consumidor,
`_cache_key` (`catalog.py:~535`, compone la clave de la caché de probes). La decisión REAL de
si un par `(pi, provider)` está autenticado vive en `_probe_pairs`
(`catalog.py:803`, `if provider not in pi_auth_provider_keys(): continue`), que llama a
`pi_auth_provider_keys()` DIRECTAMENTE — nunca a `_pi_auth_signature()`. Agregué un test
dedicado, `test_adr0043_p3sec002_repair_pi_auth_signature_never_participates_in_the_real_authentication_decision`,
que fuerza `_pi_auth_signature` a devolver un string fijo no vacío (la forma exacta que
producía el bug pre-repair incluso con el conjunto de claves vacío) y confirma que el par
`("pi", "openai-codex")` sigue AUSENTE de `probe_inventory(..., pairs=[...])` cuando
`pi_auth_provider_keys()` está vacío, y PRESENTE cuando no lo está — en ambos casos
IGNORANDO por completo lo que devuelve `_pi_auth_signature`. Mordí este mismo test (abajo,
mordida #5): rompí la separación estructural haciendo que la rama `pi` de `_probe_pairs`
consultara `_pi_auth_signature()` en vez de `pi_auth_provider_keys()`, y el test detectó la
regresión en rojo — confirma que el test realmente protege la propiedad, no que pasa en
verde vacuamente.

## Dos formas más de romper la forma (control adicional pedido por la consigna)

Con el fix aplicado, además de los tres casos originales:

```
$ python3 /var/tmp/.../scratchpad/repro_extra.py
A) codex tokens=list (wrong type) / claude rateLimitTier missing (partial) codex_empty=True  claude_empty=True
B) codex account_id=int (wrong type) / claude scopes=str (wrong type)  codex_empty=True  claude_empty=True
C) codex tokens={} (account_id absent) / claude scopes missing (partial) codex_empty=True  claude_empty=True
CONTROL) fully valid shape (must be codex_empty=False claude_empty=False) codex_empty=False claude_empty=False
```

Caso A: `tokens` de tipo lista (no dict) para codex; `rateLimitTier` ausente para claude —
ambos vacíos. Caso B: `account_id` un int (no str) para codex; `scopes` un string (no list)
para claude — ambos vacíos. Caso C: `tokens={}` (clave `account_id` ausente del todo) para
codex; `scopes` ausente para claude — ambos vacíos. El control confirma que una forma
íntegramente válida sigue produciendo una firma real (no vacía) — la validación nueva no
sobre-dispara.

## Mordidas — cada test tocado o agregado, en las dos direcciones

Metodología: `cp` de `catalog.py`/`test_routing.py` a `/var/tmp/.../scratchpad/bites/*.orig`
ANTES de la primera mordida; mutación in-place vía script Python (nunca `git
checkout`/`stash`); corrida del test específico para confirmar ROJO; `cp` de vuelta desde el
backup para restaurar; corrida de nuevo para confirmar VERDE. Cada restauración se verificó
con `diff` byte-a-byte contra el `.orig` (`RESTORED_IDENTICAL` en las cinco).

| # | Mordida | Test que debía fallar | Resultado |
|---|---|---|---|
| 1 | `_codex_auth_signature` revertida a la forma sin validar (`tokens.get()` con default `None`→`""`, sigue hasheando) | `test_adr0043_ac09_credential_signatures_fail_closed_on_symlink_and_corrupt_or_foreign_shaped_json` | ROJO confirmado: `AssertionError: '145b4b38...' != ''` (línea `self.assertEqual(cat._codex_auth_signature(), "")` sobre `{}`) |
| 2 | `_claude_code_auth_signature` revertida a `str(oauth.get(field))` sin chequeo de tipo | mismo test | ROJO confirmado: `AssertionError: '305a9233...' != ''` (sobre `{"claudeAiOauth": {}}`) |
| 3 | `pi_auth_provider_keys` sin el chequeo `st.st_uid != os.getuid()` | `test_pi_auth_provider_keys_reads_names_only_and_fails_closed` | ROJO confirmado: `AssertionError: Items in the first set but not the second: 'anthropic'` (el mock de uid ajeno dejó de fallar cerrado) |
| 4 | `_pi_auth_signature` revertida a hashear siempre (sin el `if not keys: return ""`) | `test_adr0043_ac07_pi_auth_signature_folds_provider_keys_and_the_pinned_version` | ROJO confirmado: `AssertionError: '1dc52220...' != ''` (línea `self.assertEqual(without, "")`) |
| 5 | `_probe_pairs`, rama `pi`, gateada por `_pi_auth_signature()` en vez de `pi_auth_provider_keys()` | `test_adr0043_p3sec002_repair_pi_auth_signature_never_participates_in_the_real_authentication_decision` | ROJO confirmado: `AssertionError: ('pi', 'openai-codex') unexpectedly found in {...}` |

Las cinco, restauradas y re-confirmadas en verde (`OK`, individualmente) después de cada
mordida. `diff` contra `catalog.py.orig` fue `RESTORED_IDENTICAL` las cinco veces (nunca se
apilaron mutaciones).

## Gates

```
$ ai/scripts/heartbeat-run.py --interval 20 -- python3 -m unittest discover -s tests
...
----------------------------------------------------------------------
Ran 1007 tests in 435.596s

OK (skipped=3)
```

Base declarada por el orquestador: 1006 OK / 3 skips. Con el test nuevo de este repair
(`test_adr0043_p3sec002_repair_pi_auth_signature_never_participates_in_the_real_authentication_decision`):
1007 OK / 3 skips (mismos tres skips de siempre) — sin fallos.

```
$ ai/scripts/heartbeat-run.py --interval 20 -- ./ai/scripts/verify.sh
SELF_SCAFFOLD_SYNC_OK files=2
GLOBAL_TREE_SYNC_OK profile=go-zen harnesses=4
BUILD_CHECK_PASS
...
Ran 1007 tests in 520.661s

OK (skipped=3)
...
GLOBAL_PORTABILITY_OK
CANONICAL_PATHS_OK
FEATURE_STATE_OK
VERIFY_PASS
```

```
$ ./build.sh --check
SELF_SCAFFOLD_SYNC_OK files=2
GLOBAL_TREE_SYNC_OK profile=go-zen harnesses=4
BUILD_CHECK_PASS
```

```
$ git diff --check
(sin salida — limpio)
```

Los cuatro gates: `PASS`.

## Tamaño del diff de este pase (transparencia, no un chequeo formal)

Este repair no tiene un `candidate_identity.changed_lines` congelado visible desde este
delegado (esa congelación es responsabilidad del orquestador vía `record-repair`/ADR-0023),
así que no puedo calcular `budget_lines` yo mismo — lo marco explícitamente "sin verificar"
en vez de asumir un número. Medición directa aislando SOLO mis cambios (diff línea a línea
contra el texto exacto de cada función antes de tocarla, guardado en
`/var/tmp/.../scratchpad/pre_repair/`): `catalog.py` ~36 líneas agregadas / ~26 quitadas en
las cuatro funciones tocadas (mayormente docstrings que documentan el porqué del fix, no solo
el código); `tests/test_routing.py`, cuatro tests extendidos + uno nuevo. Ambos archivos
permanecen dentro del alcance declarado (`catalog.py`, `tests/test_routing.py`), sin tercer
archivo.

## Lo que no pude verificar

- El `budget_lines` formal de ADR-0023 para este ciclo de repair — no tengo visibilidad del
  `candidate_identity.changed_lines` congelado del paquete desde este rol delegado. Sin
  verificar, explícitamente.
