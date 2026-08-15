# P4 — owned-paths-matchea-directorios — evidence

## AC -> cambio -> prueba

| AC | Cambio (`archivo:línea`) | Prueba |
| --- | --- | --- |
| AC-08 | `ai/scripts/check-owned-paths.py:25-48` (`_is_bare_directory_pattern`, `_is_directory_descendant`, `matches`) + `PROYECTO/ai/scripts/check-owned-paths.py:25-48` (copia idéntica) | `tests/test_harness.py::test_owned_paths_directory_declaration_covers_its_descendant_files` |
| AC-09 (prefijo) | mismos `:25-38` — frontera `path == directory or path.startswith(directory + "/")`, nunca `startswith(pattern)` pelado | `tests/test_harness.py::test_owned_paths_directory_declaration_never_matches_a_prefix_lookalike_or_a_true_outsider` |
| AC-09 (glob intacto) | `_is_bare_directory_pattern` excluye cualquier patrón con `* ? [ ]` | `tests/test_harness.py::test_owned_paths_directory_descendant_rule_does_not_relax_existing_glob_patterns` |
| AC-09 (precedencia read-only) | `check-owned-paths.py:122-127` sin tocar — read_only se evalúa primero y hace `continue`; la descendencia solo cambia qué matchea `matches()`, no el orden | `tests/test_harness.py::test_owned_paths_directory_descendant_never_overrides_read_only_precedence` |
| AC-08/09 (decisión `approved_exception`) | efecto de `matches()` compartido en `approved_exception:51-58` — documentado abajo | `tests/test_harness.py::test_approved_exception_directory_declaration_widens_to_cover_descendants_by_design` |

## La matriz — rojo antes, verde después, salida literal del script real

Todas las corridas usan `python3 PROYECTO/ai/scripts/check-owned-paths.py --state-file <json> --package-id PKG-01 --changed-file <file>` (el script real, sin helper inventado).

### ROJO (antes del fix — código de `matches()` sin tocar, capturado primero)

Fila 1 — declarado `tests`, cambiado `tests/test_harness.py` (exigido: pass; hoy: fail):
```json
{
  "changed_files": ["tests/test_harness.py"],
  "ok": false,
  "out_of_scope": ["tests/test_harness.py"],
  "owned_paths": ["tests"],
  "package_id": "PKG-01",
  "read_only_paths": [],
  "read_only_violations": []
}
OWNERSHIP_FAIL
exit=2
```

Fila 2 — declarado `tests/`, cambiado `tests/test_harness.py` (exigido: pass; hoy: fail):
```json
{
  "changed_files": ["tests/test_harness.py"],
  "ok": false,
  "out_of_scope": ["tests/test_harness.py"],
  "owned_paths": ["tests/"],
  "package_id": "PKG-01",
  "read_only_paths": [],
  "read_only_violations": []
}
OWNERSHIP_FAIL
exit=2
```

Fila 3 — declarado `docs/adr`, cambiado `docs/adr/0051-x.md` (exigido: pass; hoy: fail):
```json
{
  "changed_files": ["docs/adr/0051-x.md"],
  "ok": false,
  "out_of_scope": ["docs/adr/0051-x.md"],
  "owned_paths": ["docs/adr"],
  "package_id": "PKG-01",
  "read_only_paths": [],
  "read_only_violations": []
}
OWNERSHIP_FAIL
exit=2
```

Fila 4 — declarado `tests`, cambiado `tests-extra/x.py` (control negativo, ya correcto antes del fix):
```json
{
  "changed_files": ["tests-extra/x.py"],
  "ok": false,
  "out_of_scope": ["tests-extra/x.py"],
  "owned_paths": ["tests"],
  "package_id": "PKG-01",
  "read_only_paths": [],
  "read_only_violations": []
}
OWNERSHIP_FAIL
exit=2
```

Fila 5 — declarado `tests`, cambiado `outside/x.py` (control negativo, ya correcto antes del fix):
```json
{
  "changed_files": ["outside/x.py"],
  "ok": false,
  "out_of_scope": ["outside/x.py"],
  "owned_paths": ["tests"],
  "package_id": "PKG-01",
  "read_only_paths": [],
  "read_only_violations": []
}
OWNERSHIP_FAIL
exit=2
```

### VERDE (después del fix, mismas 5 filas, mismo comando literal)

Fila 1:
```json
{
  "changed_files": ["tests/test_harness.py"],
  "ok": true,
  "out_of_scope": [],
  "owned_paths": ["tests"],
  "package_id": "PKG-01",
  "read_only_paths": [],
  "read_only_violations": []
}
OWNERSHIP_PASS
exit=0
```

Fila 2:
```json
{
  "changed_files": ["tests/test_harness.py"],
  "ok": true,
  "out_of_scope": [],
  "owned_paths": ["tests/"],
  "package_id": "PKG-01",
  "read_only_paths": [],
  "read_only_violations": []
}
OWNERSHIP_PASS
exit=0
```

Fila 3:
```json
{
  "changed_files": ["docs/adr/0051-x.md"],
  "ok": true,
  "out_of_scope": [],
  "owned_paths": ["docs/adr"],
  "package_id": "PKG-01",
  "read_only_paths": [],
  "read_only_violations": []
}
OWNERSHIP_PASS
exit=0
```

Fila 4 (sigue fallando, como exige AC-09):
```json
{
  "changed_files": ["tests-extra/x.py"],
  "ok": false,
  "out_of_scope": ["tests-extra/x.py"],
  "owned_paths": ["tests"],
  "package_id": "PKG-01",
  "read_only_paths": [],
  "read_only_violations": []
}
OWNERSHIP_FAIL
exit=2
```

Fila 5 (sigue fallando, como exige AC-09):
```json
{
  "changed_files": ["outside/x.py"],
  "ok": false,
  "out_of_scope": ["outside/x.py"],
  "owned_paths": ["tests"],
  "package_id": "PKG-01",
  "read_only_paths": [],
  "read_only_violations": []
}
OWNERSHIP_FAIL
exit=2
```

### Corridas manuales adicionales (trampas 2 y 3, antes de escribir el test formal)

Precedencia read-only con directorio owned+read-only (`owned_paths: ["tests"]`, `read_only_paths: ["tests/frozen"]`, cambiado `tests/frozen/legacy.py` — debe seguir siendo `read_only_violations`, nunca pasar por descendencia):
```json
{
  "changed_files": ["tests/frozen/legacy.py"],
  "ok": false,
  "out_of_scope": [],
  "owned_paths": ["tests"],
  "package_id": "PKG-01",
  "read_only_paths": ["tests/frozen"],
  "read_only_violations": ["tests/frozen/legacy.py"]
}
OWNERSHIP_FAIL
exit=2
```

`approved_exception` sobre directorio (`approved_exceptions: [{"path": "generated", "status": "approved"}]`, cambiado `generated/sub/out.txt` — con el fix, ahora pasa; decisión documentada abajo):
```json
{
  "changed_files": ["generated/sub/out.txt"],
  "ok": true,
  "out_of_scope": [],
  "owned_paths": [],
  "package_id": "PKG-01",
  "read_only_paths": [],
  "read_only_violations": []
}
OWNERSHIP_PASS
exit=0
```

## Por cada test nuevo: neutralizar, confirmar rojo, revertir

Procedimiento real ejecutado (no narrado): se guardó una copia de `check-owned-paths.py` ya arreglado
(`/var/tmp/.../scratchpad/p4/check-owned-paths.py.fixed{,.proyecto}`), se sobrescribió
`PROYECTO/ai/scripts/check-owned-paths.py` (el que usa `CHECK_OWNED` en `tests/test_harness.py:31`) con
la versión vieja (`matches()` solo con `fnmatch` pelado, sin `_is_bare_directory_pattern` /
`_is_directory_descendant`), se corrieron los 5 tests nuevos, y se restauró la copia arreglada
verificando `cmp` en 0 antes de seguir.

Comando de neutralización + corrida (real, `-v`):
```
python3 -m unittest \
  tests.test_harness.HarnessTests.test_owned_paths_directory_declaration_covers_its_descendant_files \
  tests.test_harness.HarnessTests.test_owned_paths_directory_declaration_never_matches_a_prefix_lookalike_or_a_true_outsider \
  tests.test_harness.HarnessTests.test_owned_paths_directory_descendant_rule_does_not_relax_existing_glob_patterns \
  tests.test_harness.HarnessTests.test_owned_paths_directory_descendant_never_overrides_read_only_precedence \
  tests.test_harness.HarnessTests.test_approved_exception_directory_declaration_widens_to_cover_descendants_by_design \
  -v
```

Salida real contra el código NEUTRALIZADO (viejo):
```
test_owned_paths_directory_declaration_covers_its_descendant_files ...
  (declared='tests', changed_file='tests/test_harness.py') ... ERROR
  (declared='tests/', changed_file='tests/test_harness.py') ... ERROR
  (declared='docs/adr', changed_file='docs/adr/0051-x.md') ... ERROR
test_owned_paths_directory_declaration_never_matches_a_prefix_lookalike_or_a_true_outsider ... ok
test_owned_paths_directory_descendant_rule_does_not_relax_existing_glob_patterns ... ok
test_owned_paths_directory_descendant_never_overrides_read_only_precedence ... FAIL
test_approved_exception_directory_declaration_widens_to_cover_descendants_by_design ... ERROR

FAILED (failures=1, errors=4)
```

Detalle honesto de qué pasó con cada uno de los 5 tests nuevos, uno por uno:

1. **`test_owned_paths_directory_declaration_covers_its_descendant_files`** — ERROR en las 3
   subTest (rows 1-3), `CalledProcessError` porque `run(..., check=True)` revienta al recibir exit 2
   del script viejo (`OWNERSHIP_FAIL`) donde el test esperaba `OWNERSHIP_PASS`. Rojo genuino,
   confirmado. Restaurado el fix -> `ok` (ver corrida verde abajo).

2. **`test_owned_paths_directory_declaration_never_matches_a_prefix_lookalike_or_a_true_outsider`**
   — `ok` incluso con el código viejo. Esto es correcto y esperado: es un control negativo — el
   comportamiento que pin-ea (`tests-extra/x.py` y `outside/x.py` deben seguir en `OWNERSHIP_FAIL`)
   YA era verdadero antes del fix (fila 4/5 de la matriz, capturadas arriba como ya-rojas-correctas
   desde el principio). No es una guarda hueca: pin-ea explícitamente la trampa de prefijo que el
   context pack exige cubrir como regresión futura — si alguien más adelante cambia
   `_is_directory_descendant` a un `startswith(pattern)` pelado, este test SÍ se rompe (lo hubiera
   hecho contra cualquier implementación ingenua que use `str.startswith(pattern)` en vez del límite
   de segmento `path.startswith(directory + "/")`).

3. **`test_owned_paths_directory_descendant_rule_does_not_relax_existing_glob_patterns`** — `ok`
   incluso con el código viejo, por la misma razón: pin-ea que `src/**` sigue rechazando
   `src-legacy/app.py`, comportamiento que ya era correcto por ser puro `fnmatch`. Control de no
   regresión sobre comportamiento existente, no guarda hueca del feature nuevo — sin esta prueba,
   una implementación descuidada de la regla de directorio podría empezar a tratar `src/**` como
   directorio bare y aflojar el glob; el `assertEqual(lookalike.returncode, 2)` lo detectaría.

   **Corrección post-repair (P4-F03, delta review)**: esta afirmación resultó ser a medias. El
   reviewer independiente midió que borrando por completo la exclusión de metacaracteres
   (`_is_bare_directory_pattern` -> `return bool(pattern)`) los 5 asserts de este test seguían en
   `ok` — el control nunca discriminaba lo que decía pin-ear, porque `fnmatch`'s `*` ya cruza `/`
   (se traduce a `.*`), así que tanto el caso positivo (`src/nested/app.py`) como el negativo
   (`src-legacy/app.py`) ya pasaban/fallaban correctamente por `fnmatch` solo, sin necesidad de la
   exclusión. El repair (`docs/specs/027-controles-que-miran/evidence/P4-repair.md`) reemplaza el
   control por un caso adversarial (`config/*.json/evil/x.py` contra el patrón `config/*.json`) que
   sí discrimina: solo un `directory.startswith` sin exclusión de metacaracteres lo deja pasar. Ver
   ese archivo para la corrida roja/verde real contra el código neutralizado.

4. **`test_owned_paths_directory_descendant_never_overrides_read_only_precedence`** — **FAIL real**
   contra el código viejo: `AssertionError: 'tests/frozen/legacy.py' not found in []`. El código
   viejo sí produce `OWNERSHIP_FAIL` (exit 2) pero por el motivo incorrecto —
   `out_of_scope: ["tests/frozen/legacy.py"]` en vez de `read_only_violations`— porque sin
   descendencia tampoco matchea `read_only_paths: ["tests/frozen"]`. El test pin-ea el bucket
   correcto, no solo el exit code. Rojo genuino, confirmado.

5. **`test_approved_exception_directory_declaration_widens_to_cover_descendants_by_design`** — ERROR
   (`CalledProcessError`, exit 2) contra el código viejo: sin la regla de descendencia, la excepción
   aprobada sobre `generated` no cubre `generated/sub/out.txt`, así que cae a `out_of_scope` y el
   script sale con `OWNERSHIP_FAIL`. Rojo genuino, confirmado.

Restauración: `cp` desde el backup guardado antes de neutralizar, seguido de `cmp` entre las dos
copias del script, exit 0 (idénticas). Confirmación verde de los 5 tests, corrida real:
```
test_owned_paths_directory_declaration_covers_its_descendant_files ... ok
test_owned_paths_directory_declaration_never_matches_a_prefix_lookalike_or_a_true_outsider ... ok
test_owned_paths_directory_descendant_rule_does_not_relax_existing_glob_patterns ... ok
test_owned_paths_directory_descendant_never_overrides_read_only_precedence ... ok
test_approved_exception_directory_declaration_widens_to_cover_descendants_by_design ... ok

Ran 5 tests in 0.556s
OK
```

## Decisión sobre `approved_exception` (trampa 2) — explícita

`matches()` alimenta tres consumidores: `owned` (`check-owned-paths.py:126`), `read_only`
(`:123`) y `approved_exception` (`:56`, vía `matches(path, [pattern])` con un solo patrón). La regla
de descendencia normalizada vive DENTRO de `matches()`, así que los tres call sites la heredan por
igual — no hay forma de aplicarla solo a `owned`/`read_only` sin bifurcar la función o duplicar la
lógica de matching en un cuarto lugar.

**Decisión: se acepta, a propósito, que una `approved_exception` declarada sobre un directorio bare
ahora cubra también sus descendientes**, no solo el path exacto. Razones:

1. Una `approved_exception` ya es una excepción **revisada por un humano** (`status: "approved"`,
   campo que un humano setea explícitamente) — no es un control automático que deba ser el más
   estricto posible por defecto, como sí lo es `owned_paths`/`read_only_paths`.
2. Mantiene una sola semántica por patrón: si `"generated"` significa "el directorio `generated` y
   todo lo de abajo" para `owned_paths`, significarlo distinto según qué campo lo lea sería una
   inconsistencia silenciosa — exactamente el tipo de descubrimiento tardío que este paquete pide
   evitar.
3. Quien quiera una excepción más angosta todavía puede: declarar el archivo exacto, o un glob
   (`generated/*.json`), que la regla de descendencia deja intacto (no aplica a patrones con
   metacaracteres, confirmado por
   `test_owned_paths_directory_descendant_rule_does_not_relax_existing_glob_patterns`).
4. **(Corrección post-repair, P4-F02 — la versión original de este punto era falsa, ver
   `docs/specs/027-controles-que-miran/evidence/P4-repair.md` para la medición que la refuta)**: la
   precedencia de `read_only` en el loop principal (`check-owned-paths.py:154`,
   `if matches(path, read_only) and not approved_exception(package, path):`) SÍ es afectada por esta
   decisión — una `approved_exception` de directorio amplia también puede sacar un archivo de
   `read_only_violations`, no solo de `out_of_scope`, para cualquier descendiente del directorio
   aprobado. Medido en vivo: `read_only_paths: ["Global"]` +
   `approved_exceptions: [{"path": "Global", "status": "approved"}]` convierte
   `Global/claude-code/settings.json` de `read_only_violations` (comportamiento pre-P4) en
   `OWNERSHIP_PASS` silencioso (`out_of_scope: []`, `read_only_violations: []`). Esto es consistente
   con la razón 1-3 de arriba (una excepción humana-aprobada sigue siendo humana-aprobada
   independientemente de qué bucket habría capturado el archivo) y el orquestador la acepta como
   parte de la misma decisión de ensanchamiento — pero el texto original de este punto describía la
   dirección contraria a la medida, y quedaba sin test que la cubriera. Ambas cosas se corrigen en el
   repair: este párrafo, y
   `test_approved_exception_directory_declaration_also_cancels_read_only_violation_for_descendants`.

Test que pin-ea el efecto: `test_approved_exception_directory_declaration_widens_to_cover_descendants_by_design`
(caso `owned_paths` vacío) y, agregado en el repair,
`test_approved_exception_directory_declaration_also_cancels_read_only_violation_for_descendants`
(caso `read_only_paths` + excepción sobre el mismo directorio).

## Prueba de que las dos copias del script son idénticas

```
$ cmp ai/scripts/check-owned-paths.py PROYECTO/ai/scripts/check-owned-paths.py
$ echo $?
0
$ diff ai/scripts/check-owned-paths.py PROYECTO/ai/scripts/check-owned-paths.py
$ echo $?
0
```
(sin salida de `diff`, exit 0 en ambos — byte-idénticas.)

`./build.sh --check` real:
```
PROFILE_AUTO go-zen
SELF_SCAFFOLD_SYNC_OK files=2
GLOBAL_TREE_SYNC_OK profile=go-zen harnesses=4
BUILD_CHECK_PASS
```

## Otras validaciones locales corridas

- `python3 -m unittest tests.test_harness.HarnessTests.test_owned_paths_gate
  tests.test_harness.HarnessTests.test_owned_paths_gate_accepts_camel_case_package_schema
  tests.test_harness.HarnessTests.test_check_owned_paths_reports_global_read_only_violation_distinct_from_out_of_scope
  tests.test_harness.HarnessTests.test_owned_paths_gate_sees_untracked_new_files
  tests.test_harness.HarnessTests.test_owned_paths_gate_sees_untracked_files_with_spaces_in_their_name
  tests.test_harness.HarnessTests.test_owned_paths_gate_still_sees_ordinary_tracked_changes -v` —
  todas las pruebas preexistentes de `check-owned-paths.py` (control de no regresión sobre
  `src/**`, `shared_paths`, `read_only_paths`, `approved_exceptions` exactos, camelCase, git
  untracked/spaces, git diff tracked) siguen en `ok`. 6/6 OK.
- `git diff --check` — exit 0, sin conflictos de whitespace.
- `python3 -m unittest tests.test_harness` (módulo completo, NO `discover -s tests`) — lanzado en
  background (`heartbeat-run.py --interval 20`), en simultáneo con OTRO proceso del mismo módulo
  lanzado por otro agente en la misma máquina (`ps aux` lo confirmó mientras corría). Terminó con
  `[exited with code 0]`. La salida cruda mostrada (`tail -40`) es de fixtures no relacionados
  (`SCAFFOLD_SKIP`, `VAULT_DOCTOR_PLAN`, etc. de otros tests que imprimen a stdout durante su
  propia ejecución) porque el resumen final de `unittest` ("Ran N tests ... OK") va a stderr justo
  antes de la línea de exit del wrapper y quedó fuera de la ventana de `tail -40` visible; el dato
  que sí es 100% confiable es el exit code, capturado por el wrapper de forma independiente al
  parseo de texto: **exit 0 = módulo completo verde, sin failures/errors**, consistente con que
  ninguna de las 6 pruebas preexistentes de `check-owned-paths.py` ni las 5 nuevas rompieron nada
  del resto de la suite.

## Archivos tocados

- `ai/scripts/check-owned-paths.py` — regla de descendencia de directorios (`:25-48`).
- `PROYECTO/ai/scripts/check-owned-paths.py` — copia byte-idéntica.
- `tests/test_harness.py` — 5 tests nuevos (línea ~8727-8880): `test_owned_paths_directory_declaration_covers_its_descendant_files`, `test_owned_paths_directory_declaration_never_matches_a_prefix_lookalike_or_a_true_outsider`, `test_owned_paths_directory_descendant_rule_does_not_relax_existing_glob_patterns`, `test_owned_paths_directory_descendant_never_overrides_read_only_precedence`, `test_approved_exception_directory_declaration_widens_to_cover_descendants_by_design`.

## Sin verificar

- `./ai/scripts/verify.sh` y `python3 -m unittest discover -s tests` — explícitamente fuera de
  presupuesto por instrucción del orquestador (dos agentes más compitiendo por la máquina); el
  gate-runner los corre después, una sola vez.
- (Ya no pendiente) `python3 -m unittest tests.test_harness` completo terminó en background con
  exit code 0 — ver sección "Otras validaciones locales corridas".

## Nota del repair (delta review)

Este archivo es el registro original del implementer. El repair que cierra los hallazgos P4-F01 a
P4-F06 del review independiente vive en
`docs/specs/027-controles-que-miran/evidence/P4-repair.md` — incluye la corrección de la razón #4 de
arriba, la normalización de `..`/espaciados de declaración, el test adversarial de F03, el ADR-0052,
y la matriz de F01/F04 corrida de nuevo después del arreglo.
