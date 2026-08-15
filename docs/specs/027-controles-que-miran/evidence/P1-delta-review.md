# P1 delta review — P1-F01

- `package_id`: `P1-alcance-y-aislamiento`
- `verdict`: `pass`
- `closed_findings`: `P1-F01`
- `new_or_reopened_findings`: `[]`
- `requires_full_review`: `false` — la reparación sólo agrega un centinela privado, restaura
  `sys.modules` por identidad y extiende el test del helper; no cambia arquitectura, contratos públicos ni
  superficie de riesgo.

## Cierre de P1-F01

`P1-F01` puede cerrarse.

- `tests/test_harness.py:31-35` define `_SYS_MODULES_ABSENT = object()`, una identidad privada distinta de
  cualquier valor previo legítimo, incluido `None`.
- `tests/test_harness.py:318-326` obtiene el estado previo con
  `sys.modules.get(name, _SYS_MODULES_ABSENT)`, registra temporalmente el módulo y restaura en `finally`:
  elimina la clave sólo si estaba ausente; en cualquier otro caso repone el objeto exacto, incluido `None`.
- `tests/test_harness.py:8663-8723` cubre los tres estados previos. En particular,
  `tests/test_harness.py:8711-8718` exige simultáneamente que la clave siga presente y que su valor vuelva a
  ser `None`; esa combinación muerde la regresión original.

No hay alcance agregado fuera de la reparación ni regresiones relacionadas detectadas.

## Evidencia ejecutada

### Test dirigido — verde actual

```text
$ python3 -m unittest tests.test_harness.HarnessTests.test_import_helper_leaves_sys_modules_exactly_as_it_found_it
.
----------------------------------------------------------------------
Ran 1 test in 0.081s

OK
[exit 0]
```

### Restauración exacta cuando `exec_module` falla

Se parcheó en memoria `importlib.util.spec_from_file_location` con un loader que comprueba que el módulo
temporal está registrado y luego lanza `RuntimeError`. El probe ejecutó `_import()` con estado inicial
ausente, presente con `None` y presente con un objeto módulo; también comprobó que la excepción se propaga.

Comando ejecutado (cuerpo explícitamente recortado; las aserciones verificaron presencia e identidad exacta
descriptas arriba):

```text
$ python3 - <<'PY'
... HarnessTests._import(NAME) con FailingLoader.exec_module() -> RuntimeError ...
... assert NAME not in sys.modules para ausencia ...
... assert NAME in sys.modules and sys.modules[NAME] is initial para None/objeto ...
PY
absent: restored=ABSENT; exception=propagated
present_none: restored=None; exception=propagated
present_module: restored=EXACT_OBJECT; exception=propagated
EXEC_FAILURE_RESTORE_PASS
[exit 0]
```

Esto confirma el camino de excepción que deriva del `finally` en `tests/test_harness.py:320-326`.

### Mordida contra la lógica anterior, sin modificar archivos

Se cargó `tests/test_harness.py` en un módulo sólo en memoria y se reemplazaron exactamente una vez
`get(name, _SYS_MODULES_ABSENT)` por `get(name)` y `is _SYS_MODULES_ABSENT` por `is None`; luego se ejecutó el
mismo test dirigido.

```text
$ python3 - <<'PY'
... source = Path("tests/test_harness.py").read_text() ...
... assert source.count("previous = sys.modules.get(name, _SYS_MODULES_ABSENT)") == 1 ...
... reemplazo en memoria por la lógica anterior ...
... HarnessTests("test_import_helper_leaves_sys_modules_exactly_as_it_found_it") ...
PY
F
======================================================================
FAIL: test_import_helper_leaves_sys_modules_exactly_as_it_found_it
  (tests._p1_f01_in_memory_regression.HarnessTests.test_import_helper_leaves_sys_modules_exactly_as_it_found_it)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "tests/test_harness.py", line 8715, in test_import_helper_leaves_sys_modules_exactly_as_it_found_it
    self.assertIn("set_agents_app", sys.modules,
AssertionError: 'set_agents_app' not found in {...} : _import() must restore a sys.modules[name] = None entry as present, not pop it

----------------------------------------------------------------------
Ran 1 test in 0.074s

FAILED (failures=1)
IN_MEMORY_OLD_LOGIC: failures=1 errors=0
[exit 0: el probe considera éxito haber demostrado el rojo esperado]
```

Salida explícitamente recortada: `{...}` sustituye únicamente el volcado completo de `sys.modules`.

### Whitespace del diff

```text
$ git diff --check
[sin salida]
[exit 0]
```

## Evidencia todavía sin verificar

Los gates completos posteriores a la reparación de `tests.test_harness` y `tests.test_routing` siguen **sin
verificar**: `docs/specs/027-controles-que-miran/evidence/P1-gates.md:11-12` registra que ambas ejecuciones
fueron interrumpidas con exit 130, sin conteo ni resultado final. No se declaran verdes y la interrupción, por
sí sola, no demuestra un defecto nuevo atribuible al delta.

## Hallazgos

Ninguno.
