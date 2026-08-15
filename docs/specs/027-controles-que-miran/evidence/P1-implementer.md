# P1-alcance-y-aislamiento — evidencia del implementer

Iniciado 2026-08-14T12:56:01Z. HEAD al empezar: `c0a2a4125485588cadab5fcc2ae5e7143d735515`.

## Tabla AC → cambio → prueba

| AC | Cambio | Prueba |
|---|---|---|
| AC-01 | `ai/scripts/check-owned-paths.py:40-82` (y su copia idéntica `PROYECTO/ai/scripts/check-owned-paths.py:40-82`): `changed_files_from_git` suma `git status --porcelain -z --untracked-files=all` (los `??`) a lo que ya daba `git diff --name-only <baseline> --`, en vez de reemplazarlo. | `tests/test_harness.py:8506` `test_owned_paths_gate_sees_untracked_new_files`; `tests/test_harness.py:8540` `test_owned_paths_gate_sees_untracked_files_with_spaces_in_their_name`; `tests/test_harness.py:8575` `test_owned_paths_gate_still_sees_ordinary_tracked_changes` (complemento: no se pierde lo que `git diff` ya veía). |
| AC-02 | `tests/__init__.py:3-17`: una sola inserción, `sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "ai/scripts"))`, corre antes de cualquier submódulo de `tests`. Además, `tests/test_harness.py:269-303` (`HarnessTests._import`, un solo helper, ~200 llamadores): guarda `sys.modules.get(name)` antes de la llamada y lo restaura exacto en un `finally` (presente o ausente), en vez de sólo registrar y dejarlo — un segundo Y un tercer bug de aislamiento encontrados al construir y validar el fix (secciones 2.4 y 2.5). Ningún otro `test_*.py` tocado. | Corridas en vivo, aisladas, de `python3 -m unittest tests.test_harness` y `tests.test_routing`, más la suite completa (`discover`) — sección 2 más abajo. |
| AC-03 | `tests/test_harness.py:8604` `test_module_isolation_gate_fails_if_the_sys_path_fix_regresses` (subproceso real de `python3 -m unittest tests.test_harness.HarnessTests.test_models_config_resolves_area_and_role_override`, afirma exit 0 y ausencia de `ModuleNotFoundError`); `tests/test_harness.py:8624` `test_module_isolation_gate_fails_if_the_set_agents_app_registration_regresses` (mismo patrón, contra `test_app_config_writers_never_clobber_each_other`, afirma ausencia de `KeyError`); `tests/test_harness.py:8648` `test_import_helper_leaves_sys_modules_exactly_as_it_found_it` (directo, en proceso: pin del invariante guardar/restaurar). | Mordida en rojo/verde documentada en sección 3. |

(Los números de línea son los del archivo final, después de todas las pasadas de edición — el bug
de comillas de AC-01 se encontró al construir el fix, sección 1.3; el segundo bug de aislamiento
de AC-02/03 se encontró al validar el primero contra `tests.test_harness` aislado, sección 2.4; el
tercero — contaminación cruzada entre archivos de test — se encontró recién al correr la suite
completa `discover`, sección 2.5.)

## 1. AC-01 — el chequeo ve los archivos nuevos

### 1.1 Estado del control ANTES de tocar el script (la trampa)

Comando corrido tal cual, sobre el estado real y sucio del repo (trabajo concurrente de otros
agentes en el mismo árbol compartido, ninguno de este paquete):

```
$ python3 ai/scripts/check-owned-paths.py --state-file ai/state/features/027-controles-que-miran.json --package-id P1-alcance-y-aislamiento --baseline HEAD
{
  "changed_files": [
    "README.md",
    "docs/notas/00 - Proyecto.md",
    "docs/notas/features/025-consola-minima-y-flexible.md",
    "docs/notas/features/025-consola-minima-y-flexible/D1-superficie-humana.md",
    "docs/notas/features/025-consola-minima-y-flexible/grafo.md"
  ],
  "ok": false,
  "out_of_scope": [
    "docs/notas/features/025-consola-minima-y-flexible.md",
    "docs/notas/features/025-consola-minima-y-flexible/D1-superficie-humana.md",
    "docs/notas/features/025-consola-minima-y-flexible/grafo.md"
  ],
  "owned_paths": ["ai/scripts/check-owned-paths.py", "tests", "docs/adr"],
  "package_id": "P1-alcance-y-aislamiento",
  "read_only_paths": [],
  "read_only_violations": []
}
OWNERSHIP_FAIL
```

**Ya fallaba ANTES de mi cambio** — pero no por el bug de AC-01. `README.md` y
`docs/notas/00 - Proyecto.md` están cubiertos por `approved_exceptions` propias del paquete (no
aparecen en `out_of_scope`). Lo que rompe el veredicto son tres notas del paquete
**025-consola-minima-y-flexible** (otra feature, edición concurrente en el mismo working tree)
tracked+modificadas, que `git diff --name-only HEAD --` ya veía sin necesitar mi fix. Ruido
legítimo de la sesión compartida — no toco esos archivos, no relajo la regla para taparlo.

### 1.2 El chequeo viendo (o no) un archivo nuevo, antes y después

Reproducción exacta del probe del context pack (`ai/scripts/_probe_new_file.py`, `touch`, sin
`git add`), contra el mismo estado/paquete real de arriba:

```
ORIGINAL (HEAD, antes del fix): ve _probe_new_file.py? False | out_of_scope incluye probe? False | out_of_scope count=5  | verdict_exit=2
FIXED    (con el cambio):       ve _probe_new_file.py? True  | out_of_scope incluye probe? True  | out_of_scope count=16 | verdict_exit=2
```

El veredicto (`OWNERSHIP_FAIL`, exit 2) no cambia — ya fallaba por el ruido de 1.1 — pero el
`out_of_scope` pasa de 5 a 16 entradas: la diferencia son archivos sin trackear (el propio probe,
la evidencia/contexto/notas en progreso de este mismo paquete, y las de 025) que antes eran
invisibles y ahora se ven, exactamente como pide AC-01. `ai/scripts/_probe_new_file.py` se borró
inmediatamente después de la prueba — no queda en el árbol.

### 1.3 El bug de comillas que apareció al construir el fix (no estaba pedido, se encontró solo)

`git status --porcelain` (sin `-z`) hace quoting estilo C de cualquier ruta con un espacio —
medido en vivo en este mismo repo:

```
$ git status --porcelain -- "docs/notas/00 - Proyecto.md"
 M "docs/notas/00 - Proyecto.md"
$ git diff --name-only HEAD -- "docs/notas/00 - Proyecto.md"
docs/notas/00 - Proyecto.md
```

`git diff --name-only` nunca cotiza esa misma ruta. Un primer borrador del fix parseaba
`--porcelain` línea por línea (sin `-z`) y le habría pasado la ruta con comillas literales a
`matches()` — rota, no matcheable contra ningún patrón real. Se cambió a
`git status --porcelain -z --untracked-files=all` (NUL-separado, sin quoting nunca, por
`git-status(1)`) antes de que el fix se diera por terminado.

**Mordido en rojo/verde** (`cp`/`cp`, nunca `git checkout`):

1. Con el fix ya escrito, se sobreescribió temporalmente `ai/scripts/check-owned-paths.py` y su
   copia con una versión que usa `--porcelain` sin `-z` (parseo por línea, sin NUL).
2. Corrida sola de `tests.test_harness.HarnessTests.test_owned_paths_gate_sees_untracked_files_with_spaces_in_their_name`:

```
FAIL: test_owned_paths_gate_sees_untracked_files_with_spaces_in_their_name
AssertionError: 'danger with spaces.py' not found in ['"danger with spaces.py"', 'feature.json'] : the path must come through unquoted, not '"danger with spaces.py"'
Ran 1 test in 0.129s
FAILED (failures=1)
```

3. Se restauró (`cp`) la versión con `-z`. Misma corrida:

```
test_owned_paths_gate_sees_untracked_files_with_spaces_in_their_name ... ok
Ran 1 test in 0.996s
OK
```

## 2. AC-02 — los módulos de test pasan aislados

### 2.1 Causa raíz (un solo punto, no docenas)

`ai/scripts/models_config.py:28` hace `import provider_registry` (sibling, bare). Sólo resuelve si
`ai/scripts/` ya está en `sys.path`. `tests/test_harness.py` nunca inserta ese path — cerca de 200
llamados a `self._import("models_config")` dependían enteramente de que ALGÚN otro `test_*.py`
(alfabéticamente anterior bajo `discover`, p. ej. `test_autonomy_policy.py`) ya hubiera hecho
`sys.path.insert(0, ".../ai/scripts")` como efecto colateral de su propio import. Corriendo
`tests.test_harness` solo, ese efecto colateral nunca ocurre:

```
ModuleNotFoundError: No module named 'provider_registry'
  at ai/scripts/models_config.py:28, via tests/test_harness.py:273 (_import -> exec_module)
```

### 2.2 El fix — una línea, en el único choke point real

`tests/__init__.py` (paquete, no un módulo de test más): Python garantiza que corre antes que
CUALQUIER submódulo de `tests`, sin importar cuál cargue `unittest` primero. Se le agregó:

```python
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "ai/scripts"))
```

Ningún otro archivo de test tocado — los ~18 `sys.path.insert` ya existentes en otros
`test_*.py` quedan como estaban (redundantes ahora, no rotos; tocarlos habría sido la "solución de
cien" que el context pack pidió evitar). Se descartó `conftest.py` (mecanismo de `pytest`, que
**no está instalado** en este entorno) y `sitecustomize.py` (parchea cualquier `python3` de la
máquina, alcance mucho mayor que el problema).

### 2.3 Conteo de los dos módulos corriendo aislados (con el fix)

```
$ python3 -m unittest tests.test_routing
Ran 320 tests in 315.602s
OK
```

```
$ python3 -m unittest tests.test_harness
Ran 464 tests in 1216.239s
OK (skipped=2)
```

(Corrida FINAL, con los tres fixes de aislamiento puestos — 2.4 y 2.5 incluidos — y sin tocar
ningún archivo bajo prueba mientras corría. Dos corridas previas se descartaron como evidencia:
una con 463 tests, contaminada por ediciones concurrentes al propio `tests/test_harness.py`
mientras corría en background — `IndentationError` espurio bajo `inspect.getsource`/`linecache` en
un test de lint no relacionado; y una limpia de 463 tests que sí valía pero quedó obsoleta al
sumar el sexto test nuevo en 2.5.)

### 2.4 Segundo bug de aislamiento, encontrado al validar el primero (no estaba en el context pack)

Con el fix de `tests/__init__.py` puesto, una primera corrida completa y aislada de
`tests.test_harness` (background, sin tocar nada mientras corría) **no dio 0 errores** — dio
~119, todos con la misma forma nueva:

```
File "ai/scripts/set_agents_app.py", line 32, in <module>
    sys.modules.setdefault("set_agents_app", sys.modules[__name__])
KeyError: 'set_agents_app'
```

`set_agents_app.py:32` asume que `sys.modules[__name__]` ya existe — cierto para un `import
set_agents_app` real (Python registra el módulo ANTES de correr su cuerpo, para que un
self-lookup así funcione), falso para `HarnessTests._import()` (`tests/test_harness.py:268`,
~200 llamadores vía `self._import("set_agents_app")` o indirectamente vía `_context_fixture`),
que hacía `module_from_spec` + `exec_module` sin registrar nada antes. Bajo `discover` quedaba
invisible por el mismo mecanismo que AC-02: algún otro módulo de test hacía un `import
set_agents_app` real primero, como efecto colateral, y ese registro quedaba cacheado para el
resto del proceso. Este archivo ya tenía el patrón correcto en otra clase
(`TuiTests._import`, más abajo en el mismo archivo, cargando `tui.py`) — se aplicó el mismo
patrón (`sys.modules[name] = module` antes de `exec_module`, con `pop` en el `except`) al único
call site de `HarnessTests._import`, no a los ~200 llamadores.

**Mordido en rojo/verde**: se sobreescribió (`cp`) `tests/test_harness.py` con una versión sin el
registro (`HarnessTests._import` vuelto a `module_from_spec` + `exec_module` directo):

```
FAIL: test_module_isolation_gate_fails_if_the_set_agents_app_registration_regresses
AssertionError: 1 != 0 : E
ERROR: test_app_config_writers_never_clobber_each_other
KeyError: 'set_agents_app'
Ran 1 test in 0.039s
FAILED (errors=1)
```

Se restauró (`cp`) la versión con el registro. Misma corrida:

```
test_module_isolation_gate_fails_if_the_set_agents_app_registration_regresses ... ok
Ran 1 test in 0.634s
OK
```

`tests/test_harness.py:8624` gana un segundo test de regresión,
`test_module_isolation_gate_fails_if_the_set_agents_app_registration_regresses`, con la misma
forma que el de AC-02 (subproceso real contra un método target conocido). Ver su propia
mordida en rojo/verde en la sección 3.

### 2.5 Tercer bug — el mismo fix rompió `tests.test_routing` bajo la suite completa

`tests.test_harness` y `tests.test_routing` aislados (2.3) ya daban los dos verdes con el fix de
2.4 puesto. Pero **`python3 -m unittest discover -s tests`** (la suite completa, los dos archivos
en el mismo proceso) dio **3 fallas nuevas**, todas en `tests/test_routing.py`, ninguna en
`tests/test_harness.py`:

```
FAIL: test_resolve_context_pack_opens_only_the_named_file (test_routing.RoutingTests...)
AssertionError: Tuples differ: (False, 'only-me', None) != (False, 'only-me', 'P1')

FAIL: test_resolve_context_pack_phase_freshness_and_default_resolution (test_routing.RoutingTests...)
AssertionError: Tuples differ: (False, 'blocked-feat', None) != (False, 'blocked-feat', 'P1')

FAIL: test_validate_context_pack_path_rejects_unsafe_values (test_routing.RoutingTests...)
AssertionError: PosixPath('/home/federico/SET-AGENTES/docs/pack.md') != PosixPath('/var/tmp/tmpslzlxm6a/docs/pack.md')
Ran 1122 tests in 1195.953s
FAILED (failures=3, skipped=3)
```

Causa: el fix de 2.4 (`sys.modules[name] = module` antes de `exec_module`, dejado puesto al
volver) copiaba el patrón de `TuiTests._import`, que asume que nada más en el proceso depende de
que `sys.modules["tui"]` quede estable. `set_agents_app` no es ese caso: `routing_cli.py` hace
`import set_agents_app` de forma **perezosa, dentro del cuerpo** de
`_resolve_context_pack`/`_validate_context_pack_path` (el propio docstring del módulo lo explica),
resuelto contra `sys.modules` en el momento de la LLAMADA, no del import. Dejar el módulo
recién-`exec`eado de `HarnessTests._import` puesto en `sys.modules["set_agents_app"]` significaba
que el `import set_agents_app` de nivel superior de `tests/test_routing.py` — y cualquier
self-import perezoso posterior de `routing_cli.py` — resolvían contra ESE módulo obsoleto (armado
bajo el entorno que tuviera mockeado el último test de `HarnessTests` que llamó a `_import`) en vez
de uno canónico, una vez que ambos archivos comparten proceso bajo `discover`.

**Reproducido en un solo proceso, sin esperar la suite completa** (mismo bug, más rápido):

```
$ python3 -m unittest tests.test_harness.HarnessTests.test_app_config_writers_never_clobber_each_other tests.test_routing.RoutingTests.test_resolve_context_pack_opens_only_the_named_file tests.test_routing.RoutingTests.test_resolve_context_pack_phase_freshness_and_default_resolution tests.test_routing.RoutingTests.test_validate_context_pack_path_rejects_unsafe_values -v
test_app_config_writers_never_clobber_each_other ... ok
test_resolve_context_pack_opens_only_the_named_file ... ok
test_resolve_context_pack_phase_freshness_and_default_resolution ... ok
test_validate_context_pack_path_rejects_unsafe_values ... ok
Ran 4 tests in 0.013s
OK
```

(Este literal ya es DESPUÉS del fix final; el rojo de la versión "registrar y dejar puesto" está
en la mordida de abajo — el mismo comando con esos cuatro tests, con el fix de 2.4 tal cual, daba
las 3 fallas de arriba en 0.02s.)

**El fix**: `HarnessTests._import` deja de "registrar y dejar puesto" (el patrón de `TuiTests`) y
pasa a "guardar y restaurar exacto": guarda `sys.modules.get(name)` ANTES de la llamada (puede ser
`None`) y lo restaura en un `finally` — ausente si estaba ausente, el valor exacto de antes si
había uno — sin importar si `exec_module` tuvo éxito o no. `tests/test_harness.py:269-303`.

**Mordido en rojo/verde** (`cp`/`cp`):

1. Se sobreescribió `tests/test_harness.py` con la versión "registrar y dejar puesto" (la que
   rompe `test_routing.py`).
2. Corrida de los cuatro tests de arriba juntos:

```
test_app_config_writers_never_clobber_each_other ... ok
test_resolve_context_pack_opens_only_the_named_file ... FAIL
test_resolve_context_pack_phase_freshness_and_default_resolution ... FAIL
test_validate_context_pack_path_rejects_unsafe_values ... FAIL
Ran 4 tests in 0.022s
FAILED (failures=3)
```

3. Se restauró (`cp`) la versión "guardar y restaurar". Misma corrida: las cuatro `ok` (literal
   pegado arriba).

**Guarda de regresión directa, en proceso** (no subproceso, más rápida y no depende de que exista
otro archivo de test para detectar la fuga): `test_import_helper_leaves_sys_modules_exactly_as_it_found_it`
(`tests/test_harness.py:8648`) siembra un módulo sentinela en `sys.modules["set_agents_app"]`,
llama a `self._import("set_agents_app")`, y afirma que el sentinela — no el módulo propio de
`_import` — es lo que queda; repite con el nombre ausente y afirma que sigue ausente.

```
$ python3 -m unittest tests.test_harness.HarnessTests.test_import_helper_leaves_sys_modules_exactly_as_it_found_it -v
```

Rojo (con `HarnessTests._import` vuelto a "registrar y dejar puesto"):

```
FAIL: test_import_helper_leaves_sys_modules_exactly_as_it_found_it
AssertionError: <module 'set_agents_app' from '.../ai/scripts/set_agents_app.py'> is not <module 'set_agents_app'> : _import() must restore a pre-existing sys.modules entry, not leave its own copy
Ran 1 test in 0.060s
FAILED (failures=1)
```

Verde (con el fix restaurado):

```
test_import_helper_leaves_sys_modules_exactly_as_it_found_it ... ok
Ran 1 test in 0.072s
OK
```

## 3. AC-03 — guarda de regresión, mordida en rojo/verde

`tests/test_harness.py:8604` `test_module_isolation_gate_fails_if_the_sys_path_fix_regresses`
corre, en subproceso real, el mismo comando de la familia con la que se mide AC-02
(`python3 -m unittest tests.test_harness.HarnessTests.test_models_config_resolves_area_and_role_override`)
contra un método ya sabido dependiente del fix, y afirma exit 0 sin `ModuleNotFoundError` en
stderr.

**Mordido**: se reemplazó (`cp`) `tests/__init__.py` por su contenido original de HEAD (sin la
inserción de `sys.path`), se corrió el test nuevo solo:

```
FAIL: test_module_isolation_gate_fails_if_the_sys_path_fix_regresses
AssertionError: 1 != 0 : E
ERROR: test_models_config_resolves_area_and_role_override
ModuleNotFoundError: No module named 'provider_registry'
Ran 1 test in 0.310s
FAILED (failures=1)
```

Se restauró (`cp`) `tests/__init__.py` con el fix. Misma corrida:

```
test_module_isolation_gate_fails_if_the_sys_path_fix_regresses ... ok
Ran 1 test in 0.290s
OK
```

`tests/test_harness.py:8624` `test_module_isolation_gate_fails_if_the_set_agents_app_registration_regresses`
corre, en subproceso real, el mismo comando de la familia con la que se mide AC-02
(`python3 -m unittest tests.test_harness.HarnessTests.test_app_config_writers_never_clobber_each_other`)
contra un método ya sabido dependiente del segundo fix (`HarnessTests._import` registrando
`sys.modules[name]` antes de `exec_module`), y afirma exit 0 sin `KeyError` en stderr.

**Mordido**: se reemplazó (`cp`) `tests/test_harness.py` por una versión donde `HarnessTests._import`
volvió a su forma sin registrar el módulo, se corrió el test nuevo solo:

```
FAIL: test_module_isolation_gate_fails_if_the_set_agents_app_registration_regresses
AssertionError: 1 != 0 : E
ERROR: test_app_config_writers_never_clobber_each_other
KeyError: 'set_agents_app'
Ran 1 test in 0.039s
FAILED (errors=1)
```

Se restauró (`cp`) `tests/test_harness.py` con el fix. Misma corrida:

```
test_module_isolation_gate_fails_if_the_set_agents_app_registration_regresses ... ok
Ran 1 test in 0.634s
OK
```

Un tercer test, `test_import_helper_leaves_sys_modules_exactly_as_it_found_it`
(`tests/test_harness.py:8648`), pin directo del invariante guardar/restaurar que el fix de la
sección 2.5 introdujo — su propia mordida en rojo/verde está documentada ahí mismo (2.5), no
repetida acá.

## 4. Hallazgo fuera de alcance (se reporta, no se toca) — RIESGO para el propio gate de este paquete

`owned_paths: ["tests"]` (declarado así en el propio estado de este paquete) NO matchea
`tests/test_harness.py` vía `fnmatch` (`fnmatch.fnmatch("tests/test_harness.py", "tests")` da
`False`) — un patrón de directorio "pelado" nunca matchea archivos adentro, hace falta `tests/**`
o `tests/*`. Confirmado que es **preexistente**: corrida del script ORIGINAL (antes de cualquier
cambio de este paquete) contra el mismo estado ya daba `tests/test_harness.py` en `out_of_scope`.
No es AC-01 (visibilidad), es semántica de matching — distinto, y ninguna AC de este paquete lo
pide.

**Mismo problema con `docs/adr`** — confirmado igual:
`fnmatch.fnmatch("docs/adr/0051-owned-paths-sees-untracked-files-and-test-isolation.md", "docs/adr")`
da `False`, y también `docs/adr/README.md` contra `"docs/adr"`.

Esto **no es hipotético para este mismo paquete**: `owned_paths` de P1 es exactamente
`["ai/scripts/check-owned-paths.py", "tests", "docs/adr"]` — bare, sin `/**`. Cuando el
orquestador corra el gate real de PACKAGE_GATES para P1 (`check-owned-paths.py --baseline
<baseline>`, sin `--changed-file`, como hace siempre), **`tests/test_harness.py`,
`docs/adr/0051-*.md` y `docs/adr/README.md` — el propio entregable de este paquete — van a
aparecer en `out_of_scope`**, no por nada mal hecho acá sino por esta semántica de matching
preexistente actuando sobre la propia declaración de `owned_paths` de P1/P2/P3 de esta feature
(las tres comparten el mismo patrón "pelado"). No se toca `matches()` — tocar el control
compartido por fuera de lo que pide AC-01/02/03 es exactamente la trampa que este mismo paquete
fue armado para no pisar, y podría mover el veredicto de otros paquetes en vuelo. Se señala acá
para que el orquestador decida: declarar `owned_paths` como `tests/**`/`docs/adr/**` (edición de
estado/límites del paquete, fuera de mi alcance como implementer) o waivearlo con
`approved_exceptions`, antes de correr PACKAGE_GATES sobre P1.

## 5. Gates

Todos corridos en vivo, en este orden, sobre el estado final (los tres fixes de aislamiento y los
seis tests nuevos ya puestos, nada pendiente). `tests.test_routing` standalone no se re-corrió
después de 2.4/2.5 porque nada de esos dos fixes lo toca cuando corre solo (sólo importa
`tests/__init__.py`, sin cambios desde la corrida de la sección 2.3) — su corrida completa SÍ está
cubierta, con el estado final, dentro de `discover` más abajo:

```
$ python3 -m unittest tests.test_harness
Ran 464 tests in 1216.239s
OK (skipped=2)

$ python3 -m unittest tests.test_routing
Ran 320 tests in 315.602s
OK

$ python3 -m unittest discover -s tests
Ran 1123 tests in 1089.706s
OK (skipped=3)

$ ./ai/scripts/verify.sh
SELF_SCAFFOLD_SYNC_OK files=2
GLOBAL_TREE_SYNC_OK profile=go-zen harnesses=4
BUILD_CHECK_PASS
...
Ran 1123 tests in 1044.500s
OK (skipped=3)
VERIFY_PASS

$ ./build.sh --check
SELF_SCAFFOLD_SYNC_OK files=2
GLOBAL_TREE_SYNC_OK profile=go-zen harnesses=4
BUILD_CHECK_PASS

$ git diff --check
EXIT=0
```

Base declarada por el context pack: **1117 OK / 3 skips**. Final: **1123 OK / 3 skips** — la
diferencia (+6) son exactamente los seis tests nuevos de este paquete (3 de AC-01, 3 de AC-03),
cero regresiones, cero tests debilitados o saltados para pasar.

`python3 -m py_compile` sobre los cuatro archivos tocados (`ai/scripts/check-owned-paths.py`,
`PROYECTO/ai/scripts/check-owned-paths.py`, `tests/__init__.py`, `tests/test_harness.py`):
`COMPILE_OK`. Las dos copias de `check-owned-paths.py` siguen siendo byte-idénticas (`diff` vacío),
confirmado antes y después de cada edición.
