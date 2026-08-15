# P4 — owned-paths-matchea-directorios — repair evidence

Repair pass closing the 5 findings from the independent delta review of P4
(`docs/specs/027-controles-que-miran/context/P4-owned-paths-matchea-directorios.md`, AC-08/AC-09).
P4-F05 and P4-F07 are out of scope for this pass (owned by the orchestrator).

## Hallazgo -> cambio -> verificación

| Hallazgo | Cambio (`archivo:línea`) | Verificación |
| --- | --- | --- |
| P4-F01 (medium, path traversal) | `ai/scripts/check-owned-paths.py:32-45` (`_normalize_slashes`, `_canonical_path`) + `:73-74` (`matches` uses `_canonical_path`) + copia idéntica `PROYECTO/ai/scripts/check-owned-paths.py` | `tests/test_harness.py::test_owned_paths_directory_descendant_rejects_path_traversal_through_the_boundary` — matriz F01 re-corrida abajo |
| P4-F02 (medium, razón falsa) | (a) `docs/specs/027-controles-que-miran/evidence/P4-implementer.md` — reason #4 corregida in situ, marcada como corrección post-repair, no reescrita en silencio. (b) `check-owned-paths.py` sin cambio de comportamiento adicional (el efecto ya era el medido; se documenta y se testea) | `tests/test_harness.py::test_approved_exception_directory_declaration_also_cancels_read_only_violation_for_descendants` — corrida abajo |
| P4-F03 (low, guarda hueca) | `tests/test_harness.py::test_owned_paths_directory_descendant_rule_does_not_relax_existing_glob_patterns` — caso adversarial agregado (`config/*.json` / `config/*.json/evil/x.py`) | rojo/verde real contra `_is_bare_directory_pattern` neutralizado, abajo |
| P4-F04 (low, asimetría de grafías) | `ai/scripts/check-owned-paths.py:48-58` (`_canonical_declaration`) + `:67` (`_is_directory_descendant` usa `_canonical_declaration`) + copia idéntica en `PROYECTO/` | `tests/test_harness.py::test_owned_paths_directory_declaration_normalizes_leading_slash_dot_slash_double_slash_and_backslash_spellings` — matriz F04 re-corrida abajo |
| P4-F06 (low, decisión sin ADR) | `docs/adr/0052-owned-paths-directory-descendant-semantics.md` (nuevo) + `docs/adr/README.md` (indexado) | ver sección ADR abajo |

F01 y F04 comparten la misma normalización (`posixpath.normpath` tras `\` → `/`), aplicada al lado del
path cambiado (`_canonical_path`, F01) y al lado de la declaración (`_canonical_declaration`, F04 —
además de `lstrip("/")` sobre la declaración, no sobre el path, ver el ADR para la razón).

## Matriz F01 completa, corrida de nuevo después del arreglo

`owned_paths: ["tests"]`, comando real `python3 ai/scripts/check-owned-paths.py --state-file <json>
--package-id PKG-01 --changed-file <file>`:

```
tests/../ai/scripts/pwn.py 2
tests/../../etc/passwd 2
tests/real.py 0
tests-extra/x.py 2
```

Contra `HEAD` (antes de este package, código sin `_is_directory_descendant`), el orquestador había
medido: `tests/../ai/scripts/pwn.py` rc=2, `tests/../../etc/passwd` rc=2, `tests/real.py` rc=2 (FAIL —
el defecto que el package arregla), `tests-extra/x.py` rc=2. Contra el P4 sin reparar (medido en el
hallazgo): `tests/../ai/scripts/pwn.py` rc=0, `tests/../../etc/passwd` rc=0 (la regresión),
`tests/real.py` rc=0 (correcto, es el arreglo), `tests-extra/x.py` rc=2 (correcto, la trampa
aguantó). Después de este repair: las dos primeras filas vuelven a `2` (rc=2, `OWNERSHIP_FAIL`),
`tests/real.py` sigue en `0` (`OWNERSHIP_PASS`, el arreglo original de P4-F01 no se rompió) y
`tests-extra/x.py` sigue en `2` (la trampa de prefijo sigue aguantando).

## Matriz F04, después del arreglo

`python3 ai/scripts/check-owned-paths.py --state-file <json> --package-id PKG-01 --changed-file
<file>`, un patrón distinto por fila en `owned_paths`:

```
/tests tests/x.py 0
./tests tests/x.py 0
docs//adr docs/adr/x.md 0
tests// tests/x.py 0
tests\sub tests/sub/x.py 0
```

Las cinco son `0` (`OWNERSHIP_PASS`). Antes del repair, según midió el orquestador: `/tests` -> FAIL,
`./tests` -> FAIL, `docs//adr` -> FAIL, `tests//` -> PASS (ya correcto), `tests\sub` -> FAIL. Las
cuatro que fallaban ahora pasan; la que ya pasaba (`tests//`) sigue pasando.

## Efecto F02, medido antes y después (sin cambio — se corrige el registro, no el comportamiento)

`read_only_paths: ["Global"]`, `approved_exceptions: [{"path": "Global", "status": "approved"}]`,
cambiado `Global/claude-code/settings.json`:

```
0
{
  "changed_files": [
    "Global/claude-code/settings.json"
  ],
  "ok": true,
  "out_of_scope": [],
  "owned_paths": [],
  "package_id": "PKG-01",
  "read_only_paths": [
    "Global"
  ],
  "read_only_violations": []
}
OWNERSHIP_PASS
```

Idéntico antes y después de este repair (el hallazgo es sobre el REGISTRO de la decisión, no sobre el
comportamiento — el orquestador ya aceptó este ensanchamiento). Lo que cambia: la reason #4 en
`P4-implementer.md` ahora describe esta salida en vez de su opuesto, y
`test_approved_exception_directory_declaration_also_cancels_read_only_violation_for_descendants` la
fija con un assert nombrado.

## Efecto F03, medido antes y después

`owned_paths: ["src/**", "config/*.json"]`, cambiado `config/*.json/evil/x.py` (caso adversarial
agregado al test):

Después del fix (código real, sin neutralizar):
```
2
{
  "changed_files": [
    "config/*.json/evil/x.py"
  ],
  "ok": false,
  "out_of_scope": [
    "config/*.json/evil/x.py"
  ],
  "owned_paths": [
    "config/*.json"
  ],
  "package_id": "PKG-01",
  "read_only_paths": [],
  "read_only_violations": []
}
OWNERSHIP_FAIL
```

## Por cada test nuevo o modificado: neutralizar, confirmar rojo, revertir

Procedimiento real (no narrado), un hallazgo a la vez. Se copió el script ya arreglado a
`/var/tmp/.../scratchpad/p4/backup/check-owned-paths.py.fixed` antes de empezar; cada neutralización
edita SOLO `PROYECTO/ai/scripts/check-owned-paths.py` (el que usa `CHECK_OWNED` en
`tests/test_harness.py:31`), corre el test dirigido, y se restaura con `cp` desde el backup,
confirmando `cmp` en 0 contra `ai/scripts/check-owned-paths.py` antes de seguir al siguiente hallazgo.

### F01 — `test_owned_paths_directory_descendant_rejects_path_traversal_through_the_boundary`

Neutralización: `matches()` vuelve a `normalized = path.replace("\\", "/")` (sin `_canonical_path`,
sin `posixpath.normpath`).

Salida real (`-v`):
```
======================================================================
FAIL: test_owned_paths_directory_descendant_rejects_path_traversal_through_the_boundary (tests.test_harness.HarnessTests.test_owned_paths_directory_descendant_rejects_path_traversal_through_the_boundary) (changed_file='tests/../ai/scripts/pwn.py')
AssertionError: 0 != 2 : {..., "ok": true, "out_of_scope": [], "owned_paths": ["tests"], ...}
OWNERSHIP_PASS

======================================================================
FAIL: ... (changed_file='tests/../../etc/passwd')
AssertionError: 0 != 2 : {..., "ok": true, "out_of_scope": [], "owned_paths": ["tests"], ...}
OWNERSHIP_PASS

----------------------------------------------------------------------
Ran 1 test in 0.249s

FAILED (failures=2)
```
Rojo genuino en las 2 filas de traversal (las otras 2 subTest, `tests/real.py` y `tests-extra/x.py`,
no dependen de esta normalización y no fallaron). Restaurado (`cp` + `cmp` exit 0) -> `ok`.

### F04 — `test_owned_paths_directory_declaration_normalizes_leading_slash_dot_slash_double_slash_and_backslash_spellings`

Neutralización: `_is_directory_descendant` vuelve a `directory = pattern.rstrip("/")` (sin
`_canonical_declaration`).

Salida real (`-v`, resumen): 4 de las 5 subTest (`/tests`, `./tests`, `docs//adr`, `tests\sub`)
terminan en `ERROR` (`CalledProcessError`, exit 2 donde se esperaba `OWNERSHIP_PASS`); la quinta
(`tests//`) sigue en `ok` porque ya pasaba antes del repair (`pattern.rstrip("/")` ya le quitaba la
barra doble sobrante). `FAILED (errors=4)`. Restaurado (`cp` + `cmp` exit 0) -> `ok`.

### F03 — caso adversarial en `test_owned_paths_directory_descendant_rule_does_not_relax_existing_glob_patterns`

Neutralización: `_is_bare_directory_pattern` vuelve a `return bool(pattern)` (se borra la exclusión de
metacaracteres por completo — la misma neutralización que el reviewer usó para encontrar el
hallazgo).

Salida real:
```
======================================================================
FAIL: test_owned_paths_directory_descendant_rule_does_not_relax_existing_glob_patterns (...)
AssertionError: 0 != 2 : {
  "changed_files": ["config/*.json/evil/x.py"],
  "ok": true,
  "out_of_scope": [],
  "owned_paths": ["src/**", "config/*.json"],
  "package_id": "PKG-01",
  "read_only_paths": [],
  "read_only_violations": []
}
OWNERSHIP_PASS

----------------------------------------------------------------------
Ran 1 test in 0.188s

FAILED (failures=1)
```
Rojo genuino — confirma que este caso, a diferencia del `src/**`/`src-legacy` original, sí discrimina
la exclusión de metacaracteres. Restaurado (`cp` + `cmp` exit 0) -> `ok`.

### F02 — `test_approved_exception_directory_declaration_also_cancels_read_only_violation_for_descendants`

Neutralización: el loop principal vuelve a `if matches(path, read_only):` (se borra el
`and not approved_exception(package, path)` — simula una versión donde la excepción nunca cancela
`read_only`, la lectura que la reason #4 original afirmaba, incorrectamente, que ya era el
comportamiento real).

Salida real:
```
======================================================================
ERROR: test_approved_exception_directory_declaration_also_cancels_read_only_violation_for_descendants (...)
subprocess.CalledProcessError: ... returned non-zero exit status 2.

----------------------------------------------------------------------
Ran 1 test in 0.063s

FAILED (errors=1)
```
Rojo genuino (`run(..., check=True)` revienta al recibir exit 2 donde el test pide `OWNERSHIP_PASS`).
Restaurado (`cp` + `cmp` exit 0) -> `ok`.

### Confirmación verde final, las 4 pruebas juntas

```
test_owned_paths_directory_descendant_rejects_path_traversal_through_the_boundary ... ok
test_owned_paths_directory_declaration_normalizes_leading_slash_dot_slash_double_slash_and_backslash_spellings ... ok
test_owned_paths_directory_descendant_rule_does_not_relax_existing_glob_patterns ... ok
test_approved_exception_directory_declaration_also_cancels_read_only_violation_for_descendants ... ok

----------------------------------------------------------------------
Ran 4 tests in ...
OK
```
(corrida real de las 14 pruebas de owned-paths juntas — preexistentes + P4 originales + repair — más
abajo, `OK`, 14/14.)

## Corrida completa: las 14 pruebas de `check-owned-paths.py`

```
test_owned_paths_gate ... ok
test_owned_paths_gate_accepts_camel_case_package_schema ... ok
test_check_owned_paths_reports_global_read_only_violation_distinct_from_out_of_scope ... ok
test_owned_paths_gate_sees_untracked_new_files ... ok
test_owned_paths_gate_sees_untracked_files_with_spaces_in_their_name ... ok
test_owned_paths_gate_still_sees_ordinary_tracked_changes ... ok
test_owned_paths_directory_declaration_covers_its_descendant_files ... ok
test_owned_paths_directory_declaration_never_matches_a_prefix_lookalike_or_a_true_outsider ... ok
test_owned_paths_directory_descendant_rejects_path_traversal_through_the_boundary ... ok
test_owned_paths_directory_declaration_normalizes_leading_slash_dot_slash_double_slash_and_backslash_spellings ... ok
test_owned_paths_directory_descendant_rule_does_not_relax_existing_glob_patterns ... ok
test_owned_paths_directory_descendant_never_overrides_read_only_precedence ... ok
test_approved_exception_directory_declaration_widens_to_cover_descendants_by_design ... ok
test_approved_exception_directory_declaration_also_cancels_read_only_violation_for_descendants ... ok

----------------------------------------------------------------------
Ran 14 tests in 2.023s

OK
```

## Prueba de que las dos copias del script siguen idénticas

```
$ cmp ai/scripts/check-owned-paths.py PROYECTO/ai/scripts/check-owned-paths.py
$ echo $?
0
```
(sin salida, exit 0 — byte-idénticas, confirmado después de cada restauración durante los 4 red-bites
de arriba y al final.)

## `./build.sh --check`

```
PROFILE_AUTO go-zen
SELF_SCAFFOLD_SYNC_OK files=2
GLOBAL_TREE_SYNC_OK profile=go-zen harnesses=4
BUILD_CHECK_PASS
```

## ADR

`docs/adr/0052-owned-paths-directory-descendant-semantics.md` — fija la semántica de descendencia de
directorio canonicalizada, el efecto por consumidor (`owned_paths`, `read_only_paths`,
`approved_exceptions`), y la decisión sobre `approved_exception` con la razón #4 ya corregida.
Indexado en `docs/adr/README.md`. Número tomado con `ls docs/adr/` (0050 no existe en este árbol —
probablemente en uso por un package concurrente; se usó 0052, el siguiente libre después de 0051).

## Archivos tocados

- `ai/scripts/check-owned-paths.py` — `_normalize_slashes`, `_canonical_path`, `_canonical_declaration`
  (nuevas), `matches`/`_is_directory_descendant` las usan (P4-F01, P4-F04).
- `PROYECTO/ai/scripts/check-owned-paths.py` — copia byte-idéntica.
- `tests/test_harness.py` — 2 tests nuevos
  (`test_owned_paths_directory_descendant_rejects_path_traversal_through_the_boundary`,
  `test_owned_paths_directory_declaration_normalizes_leading_slash_dot_slash_double_slash_and_backslash_spellings`,
  `test_approved_exception_directory_declaration_also_cancels_read_only_violation_for_descendants` — 3
  nuevos) + 1 modificado
  (`test_owned_paths_directory_descendant_rule_does_not_relax_existing_glob_patterns`, caso
  adversarial agregado).
- `docs/specs/027-controles-que-miran/evidence/P4-implementer.md` — reason #4 corregida in situ
  (marcada como corrección post-repair), nota al pie apuntando a este archivo.
- `docs/adr/0052-owned-paths-directory-descendant-semantics.md` — nuevo.
- `docs/adr/README.md` — fila 0052 agregada.

## Sin verificar

- `./ai/scripts/verify.sh` y `python3 -m unittest discover -s tests` — explícitamente fuera de
  presupuesto (gate-runner independiente los corre sobre el árbol integrado).
- `python3 -m unittest tests.test_harness` (módulo completo) — lanzado en background
  (`heartbeat-run.py --interval 20`), seguía corriendo (confirmado por `ps aux`, PID real del
  subproceso `python3 -m unittest tests.test_harness`) al cierre de este pase de repair. **Sin
  verificar su resultado final** — no se esperó a que terminara para no exceder el presupuesto de un
  solo pase consolidado. La evidencia que SÍ cierra este repair (14/14 pruebas dirigidas de
  `check-owned-paths.py`, las 4 corridas de neutralizar/rojo/revertir, `git diff --check`,
  `./build.sh --check`) fue corrida completa y en primer plano, no en background.
