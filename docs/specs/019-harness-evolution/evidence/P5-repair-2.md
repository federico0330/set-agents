# P5-tools-discovery — evidencia del repair-agent, ronda 2 (delta review)

Feature 019-harness-evolution, PKG-5. El delta review de la ronda 1 confirmó cerrados 13 de 15 findings
(incluidos los cuatro bloqueantes, reproduciendo los ataques y viéndolos fallar) pero no pasó por dos
cosas: **NEW-01** (high, hallazgo nuevo) y **F-06** (medium, REABIERTO). Alcance de esta ronda: exactamente
esos dos findings, más las observaciones (`low`, no bloqueantes) que decidí reparar por ser baratas —
documentado caso por caso más abajo, incluida la que decidí NO tocar.

Orden de trabajo: NEW-01 → F-06 → OBS-1 → OBS-2 → OBS-3 → OBS-4 → OBS-5 (documentado, no reparado) →
OBS-6 (evidencia).

## Estado por finding

| Finding | Severidad | Estado |
|---|---|---|
| NEW-01 | high | reparado |
| F-06 (round 2) | medium | reparado |
| OBS-1 | low | reparado |
| OBS-2 | low | reparado |
| OBS-3 | low | reparado |
| OBS-4 | low | reparado |
| OBS-5 | low | documentado, no reparado (decisión explícita, ver abajo) |
| OBS-6 | low | reparado (evidencia completada) |

## NEW-01 (high) — el archivo que alimenta a `bash -c` no se valida nunca

**Causa real**: `cmd_tools_install` (`ai/scripts/set_agents_app.py`) resuelve la entrada mergeada por
`load_catalog()` (curado `tools.toml` + overlay `tools.local.toml`, este último untracked por
`.gitignore`) y pasa `entry["install"][method]` directo a `subprocess.run(["bash", "-c", command])`, sin
correr nunca `_validate_install_command` sobre lo que vino del overlay local. El camino de ESCRITURA
(`cmd_tools_approve`, vía `_validate_proposal`) siempre valida; el camino de LECTURA nunca lo hacía —
asimetría explotable con un `tools.local.toml` editado a mano (no pasa por `cmd_tools_approve` en
absoluto), reproducida por el delta-reviewer con un marcador real (`true & touch <marker>` corriendo con
`rc=0` bajo `--yes`, sin ninguna pregunta).

**Cambio**:

- `ai/scripts/set_agents_app.py:1258` — nueva `_is_local_only_entry(kind, name)`: distingue una entrada
  que resuelve del catálogo CURADO (`tools.toml`, reviewed, tracked, algunas legítimamente con sudo) de
  una que solo existe por el overlay local. Mirror exacto de la regla curado-gana de `load_catalog()` —
  un nombre presente en ambos es curado para todo propósito, nunca se clasifica como local solo porque
  también exista un bloque local con ese nombre (test dedicado, ver abajo).
- `ai/scripts/set_agents_app.py:1798` (`cmd_tools_install`) — justo después de resolver `entry` y antes de
  tocar `shutil.which`/`pick_method`, si `_is_local_only_entry("cli", name)` es verdadero, se vuelve a
  correr `_validate_install_command` sobre CADA comando que la entrada carga en su tabla `install` (no
  solo el que `pick_method` elegiría en esta plataforma) — la misma función que `_validate_proposal` ya
  corre en el camino de escritura, la MISMA validación, corrida una segunda vez en el otro extremo del
  ciclo de vida del archivo. Si cualquiera falla, imprime `TOOL_REJECTED {name} — ...` y devuelve `2` —
  nunca llega a `subprocess.run`, con o sin `--yes`. Las entradas del catálogo CURADO (`tools.toml`) no
  pasan por este chequeo en absoluto — `_is_local_only_entry` las excluye por diseño, así que las 9
  entradas `[cli.*]` curadas (incluidas las que usan sudo: `gh`/`docker`/`jq`) no se ven afectadas.
  (Corrección round 3: el número "20" de rondas anteriores era el conteo de COMANDOS de install —
  29 claves de la tabla `install` en todo `tools.toml` menos 9 `doc` = 20 — no de entradas; son 9
  entradas `[cli.*]`, cada una con uno o más métodos de install. Ver P5-repair-3.md.)
- `docs/adr/0038-tools-catalog-discovery.md` §6 — nuevo párrafo "NEW-01 (high, delta review round 2)"
  documentando la asimetría lectura/escritura y la reparación; §9 gana la entrada correspondiente.

**Reproducción del ataque, comando pegado, salida real (con el arreglo)**:
```
$ python3 - <<'PY'
import sys, tempfile, io
from pathlib import Path
from unittest import mock
sys.path.insert(0, "ai/scripts")
import set_agents_app as app

with tempfile.TemporaryDirectory() as td:
    root = Path(td) / "root"
    root.mkdir()
    import shutil as _sh
    _sh.copy2("tools.toml", root / "tools.toml")
    marker = Path(td) / "marker"
    (root / "tools.local.toml").write_text(
        '[cli.backdoor]\n'
        'detect = "backdoor-bin"\n'
        '[cli.backdoor.install]\n'
        f'npm = "true & touch {marker}"\n'
    )
    with mock.patch.object(app, "ROOT", root):
        buf = io.StringIO()
        with mock.patch("sys.stdout", buf):
            rc = app.cmd_tools_install("backdoor", yes=True)
        print("rc=", rc)
        print(buf.getvalue())
        print("MARKER CREATED:", marker.exists())
PY
rc= 2
TOOL_REJECTED backdoor — la entrada de tools.local.toml no pasa la validación de instalación (ADR-0038
§3): comando con caracteres no permitidos — solo se aceptan letras, números, espacios y - . / : = _ ~ @
+ , | (allowlist, ADR-0038 §3). Una entrada legítima solo llega ahí vía --tools-approve, que ya la
valida; revisá o borrá tools.local.toml.

MARKER CREATED: False
```
(antes del arreglo: `rc=0`, `TOOL_OK backdoor`, `MARKER CREATED: True` — exactamente lo que el
delta-reviewer reprodujo).

**Ambas direcciones — las 9 entradas `[cli.*]` curadas (20 comandos de install: 29 claves de la tabla
`install` en todo `tools.toml` menos 9 `doc`) siguen instalándose igual (no pasan por el chequeo nuevo)**:
```
$ python3 -m unittest discover -s tests -k "test_obsidian_catalog_has_verified_pm_identifiers_plus_doc" -k "test_tools_install_dry_run_plan_per_manager" -k "test_tools_install_falls_through_to_manual_for_apt_dnf_zypper" -k "test_scaffold_attempts_obsidian_once" -k "test_vault_doctor_warns" -v
test_obsidian_catalog_has_verified_pm_identifiers_plus_doc ... ok
test_scaffold_attempts_obsidian_once_and_never_fails_scaffold_on_decline ... ok
test_tools_install_dry_run_plan_per_manager ... ok
test_tools_install_falls_through_to_manual_for_apt_dnf_zypper ... ok
test_vault_doctor_warns_but_never_blocks_when_obsidian_is_missing ... ok
Ran 5 tests in 0.045s
OK
```
Y el E2E que instala/planea contra el catálogo curado REAL (`vercel`/`jq`/`supabase`/`gcloud`, vía el
wrapper `set-agents` real, sin mockear nada) sigue en verde — ver el bloque de regresión más abajo (se
corrió como parte de la suite completa).

**Test de regresión** (`tests/test_harness.py`):
- `test_cmd_tools_install_rejects_a_hand_edited_local_catalog_entry_with_a_disallowed_command` — la
  prueba de mordida de arriba, como test real (mockea `subprocess.run` y assertea `run.assert_not_called()`
  y `marker.exists() is False`).
- `test_cmd_tools_install_still_runs_a_locally_approved_entry_that_passes_validation` — una entrada local
  LEGÍTIMA (misma forma que `--tools-approve` escribe) sigue instalándose y llega a `subprocess.run`.
- `test_cmd_tools_install_never_extra_validates_a_curated_entry_even_when_a_local_name_collides` —
  `_is_local_only_entry("cli", "vercel")` es `False` incluso con un `tools.local.toml` que también define
  `[cli.vercel]` (mismo criterio curado-gana que `load_catalog()`).

**Verificación real**:
```
$ python3 -m unittest discover -s tests -k "test_cmd_tools_install_rejects_a_hand_edited_local_catalog_entry_with_a_disallowed_command" -k "test_cmd_tools_install_still_runs_a_locally_approved_entry_that_passes_validation" -k "test_cmd_tools_install_never_extra_validates_a_curated_entry_even_when_a_local_name_collides" -v
test_cmd_tools_install_never_extra_validates_a_curated_entry_even_when_a_local_name_collides ... ok
test_cmd_tools_install_rejects_a_hand_edited_local_catalog_entry_with_a_disallowed_command ... ok
test_cmd_tools_install_still_runs_a_locally_approved_entry_that_passes_validation ... ok
Ran 3 tests in 0.005s
OK
```

**Prueba de mordida** (neutralizar el guard en `cmd_tools_install` — `if _is_local_only_entry(...)` →
`if False and _is_local_only_entry(...)` — y re-correr):
```
$ python3 -m unittest discover -s tests -k "test_cmd_tools_install_rejects_a_hand_edited_local_catalog_entry_with_a_disallowed_command" -v
FAIL: test_cmd_tools_install_rejects_a_hand_edited_local_catalog_entry_with_a_disallowed_command
AssertionError: 1 != 2
Ran 1 test in 0.005s
FAILED (failures=1)
```
(`rc=1`, no `2`: sin el guard, la ejecución llega a `subprocess.run` — mockeado en el test, por eso no
crea el marcador real ahí, pero el `TOOL_FAIL` que sigue solo se imprime DESPUÉS de invocar
`subprocess.run`, confirmando que el ataque atraviesa hasta el proceso real sin el arreglo). Guard
restaurado inmediatamente después; test verde de nuevo (ver arriba).

## F-06 (medium, REABIERTO) — reparaste la lista de ejemplos, no el defecto

**Causa real**: la reparación de la ronda 1 validó que cada entrada del overlay local fuera un `dict`
(`isinstance(entry, dict)`) en `_load_local_catalog`, cerrando los tres casos que el finding original
enumeraba (escalar top-level, entrada escalar de sección, lista JSON). Pero una entrada que SÍ es una
tabla bien formada, y le falta `detect`/`install` (o los tiene con el tipo equivocado), sigue siendo un
`dict` — pasaba el chequeo de ronda 1 y llegaba a `_tools_data`/`cmd_tools_install` como `KeyError`, ya
que ambas indexan `entry["detect"]`/`entry["install"]` directo, sin `.get()`. El delta-reviewer lo
reprodujo con `[cli.x] note = "no detect key"` (sin `detect`) y con `detect` presente pero sin tabla
`install`.

**Cambio**:

- `ai/scripts/set_agents_app.py:1229` — nueva `_valid_local_entry_shape(entry)`: `detect` debe ser un
  string no vacío; `install` debe ser un dict no vacío de `string -> string`. Es exactamente el esquema
  uniforme que `cmd_tools_approve` siempre escribe, para TODO `kind` (`cli`/`mcp`/`skill` — ADR-0038 §7,
  `_dump_toml_catalog`), así que es seguro exigirlo para cualquier `kind` en este archivo, no solo `cli`.
- `ai/scripts/set_agents_app.py:1170` (`_load_local_catalog`) — el loop de construcción de `section` ahora
  llama `_valid_local_entry_shape(entry)` por cada entrada; si falla, imprime un `WARNING` a stderr
  (mismo patrón que F-04's warning de parse-error) y la salta — nunca llega a `load_catalog()`, así que
  ningún consumidor downstream (`_tools_data`, `cmd_tools_install`, `tools_menu`, el panel de estado en
  `:836`/`:2943`) puede verla.
- `docs/adr/0038-tools-catalog-discovery.md` §9 — el bullet de F-06 se extiende con la reparación de
  ronda 2.

**Reproducción, cubriendo la CLASE (no solo los dos casos que el reviewer pegó)** — seis formas, cada una
bien-formada como TOML pero con la forma equivocada para lo que `_tools_data`/`cmd_tools_install` indexan:

```
$ python3 -m unittest discover -s tests -k "test_load_local_catalog_degrades_entries_missing_detect_or_install_instead_of_crashing_downstream" -v
test_load_local_catalog_degrades_entries_missing_detect_or_install_instead_of_crashing_downstream ... ok
Ran 1 test in 0.023s
OK
```

Las seis sub-pruebas (`subTest`), cada una escribiendo el `tools.local.toml` real y llamando LOS DOS
call sites exactos que el reviewer ejercitó (`_tools_data()` para `--tools`, `cmd_tools_install(..., dry=True)`
para `--tools-install x --dry-run`), no solo `_load_local_catalog()`/`load_catalog()`:

| Caso | TOML |
|---|---|
| falta `detect` | `[cli.x]\nnote = "no detect key"` |
| `detect` pero sin tabla `install` | `[cli.x]\ndetect = "x-bin"` |
| `detect` con tipo equivocado | `[cli.x]\ndetect = 1\n[cli.x.install]\nnpm = "..."` |
| `install` escalar (no tabla) | `[cli.x]\ndetect = "x-bin"\ninstall = "npm install -g x"` |
| tabla `install` vacía | `[cli.x]\ndetect = "x-bin"\n[cli.x.install]` |
| valor de `install` con tipo equivocado | `[cli.x]\ndetect = "x-bin"\n[cli.x.install]\nnpm = 1` |

Cada caso: `_load_local_catalog()` descarta la entrada (`"x" not in result["cli"]`), emite `WARNING` a
stderr, y AMBOS call sites (`_tools_data()`, `cmd_tools_install("x", dry=True)`) devuelven limpio
(`TOOL_UNKNOWN x`, `rc=2`) en vez de `KeyError`.

**Test de regresión**: `test_load_local_catalog_degrades_entries_missing_detect_or_install_instead_of_crashing_downstream`.

**Prueba de mordida** (neutralizar `_valid_local_entry_shape` en el loop de `_load_local_catalog` — `if
not _valid_local_entry_shape(entry):` → `if False and not _valid_local_entry_shape(entry):` — y re-correr):
```
$ python3 -m unittest discover -s tests -k "test_load_local_catalog_degrades_entries_missing_detect_or_install_instead_of_crashing_downstream" -v
FAIL (label='detect wrong type'): AssertionError: 'x' unexpectedly found in {...}
FAIL (label='install wrong type (scalar)'): AssertionError: 'x' unexpectedly found in {...}
FAIL (label='install empty table'): AssertionError: 'x' unexpectedly found in {...}
FAIL (label='install value wrong type'): AssertionError: 'x' unexpectedly found in {...}
(+ 2 subTests más con KeyError real al llegar a _tools_data/cmd_tools_install para los casos "missing
detect"/"detect but no install table")
Ran 1 test in 0.008s
FAILED (failures=6)
```
Las 6 subpruebas van en rojo sin el arreglo (algunas por `AssertionError` porque la entrada mal formada
sobrevive el filtro, otras por el `KeyError` real que el reviewer reprodujo). Guard restaurado
inmediatamente después; test verde de nuevo (ver arriba).

## Observaciones (`low`, no bloqueaban)

### OBS-1 — `.match()` con `$` en vez de `.fullmatch()`

**Cambio**: `ai/scripts/set_agents_app.py` — `_validate_install_command` pasa de
`_ALLOWED_CMD_CHARS_RE.match(cmd)` a `_ALLOWED_CMD_CHARS_RE.fullmatch(cmd)`. `$` matchea al final del
string O justo antes de un ÚNICO salto de línea final, así que `.match()` aceptaba un comando con
exactamente un `\n` de más al final.

**Test de regresión**: `test_validate_install_command_uses_fullmatch_not_a_trailing_dollar_match`.
```
$ python3 -m unittest discover -s tests -k "test_validate_install_command_uses_fullmatch_not_a_trailing_dollar_match" -v
test_validate_install_command_uses_fullmatch_not_a_trailing_dollar_match ... ok
Ran 1 test in 0.001s
OK
```

### OBS-2 — basename de escaladores case-sensitive

**Cambio**: `ai/scripts/set_agents_app.py:_cmd_privilege_escalator` — la comparación pasa a
`basename.lower() in _PRIVILEGE_ESCALATORS` (el frozenset se mantiene todo-minúscula; solo se folding la
comparación). Irrelevante en Linux (filesystem case-sensitive), relevante en macOS/Windows por defecto.

**Test de regresión**: `test_cmd_privilege_escalator_covers_the_missing_binaries_case_insensitively`
(casos `SUDO`, `/usr/bin/SUDO`, `Doas`, ver output combinado con OBS-3 abajo).

### OBS-3 — `sudoedit`, `run0`, `please` fuera del denylist

**Cambio**: `ai/scripts/set_agents_app.py` — `_PRIVILEGE_ESCALATORS` suma `"sudoedit"`, `"run0"`,
`"please"` a los cinco ya existentes (`sudo`, `doas`, `pkexec`, `su`, `runas`).

**Test de regresión**: `test_cmd_privilege_escalator_covers_the_missing_binaries_case_insensitively`
(cubre OBS-2 y OBS-3 juntos, comparten archivo/función/causa).

**Verificación real (OBS-2 + OBS-3)**:
```
$ python3 -m unittest discover -s tests -k "test_cmd_privilege_escalator_covers_the_missing_binaries_case_insensitively" -v
test_cmd_privilege_escalator_covers_the_missing_binaries_case_insensitively ... ok
Ran 1 test in 0.002s
OK
```

### OBS-4 — `_LEGIT_PIPE_RE` acepta cualquier token que empiece con curl/wget

**Causa real**: `\b` es un boundary de PALABRA, no de "nombre de binario real" — `curl.evil -x URL | bash`
tiene un `.` justo después de `curl`, que YA es un boundary de palabra (letra → no-letra), así que el
regex viejo lo aceptaba.

**Cambio**: `ai/scripts/set_agents_app.py` — `_LEGIT_PIPE_RE` pasa de `^(?:curl|wget)\b[^|]*\|\s*(?:bash|sh)\s*$`
a `^(?:curl|wget)(?=\s)[^|]*\|\s*(?:bash|sh)\s*$` — exige un espacio real después del nombre del binario
(la única forma en que el catálogo curado lo invoca).

**Test de regresión**: `test_legit_pipe_re_requires_a_real_fetch_binary_not_just_a_name_prefix`.
```
$ python3 -m unittest discover -s tests -k "test_legit_pipe_re_requires_a_real_fetch_binary_not_just_a_name_prefix" -v
test_legit_pipe_re_requires_a_real_fetch_binary_not_just_a_name_prefix ... ok
Ran 1 test in 0.001s
OK
```

### OBS-5 — falsos positivos fail-closed por "su" en una URL o `@scope/su`

**Decisión: NO reparado, documentado explícitamente.** `os.path.basename("@scope/su")` es `"su"`, así
que `npm install -g @scope/su` (o una URL cuyo último segmento de path sea literalmente `/su`/`/sudo`)
se rechaza igual que un escalador real. Es un falso positivo por diseño del criterio de F-03 (comparar
por basename de CADA token, no por posición): rechazar de más es la dirección segura acá (aflojarlo
reabriría la clase de bug que F-03 cerró — un escalador con path resuelto que se cuela). No hay ninguna
entrada real en `tools.toml` afectada. Documentado en `docs/adr/0038-tools-catalog-discovery.md` §3
("Falsos positivos conocidos, y por qué son aceptables") y PINEADO con un test para que no derive en
silencio en ninguna dirección:

```
$ python3 -m unittest discover -s tests -k "test_cmd_privilege_escalator_documented_false_positive_on_a_scoped_package_named_su" -v
test_cmd_privilege_escalator_documented_false_positive_on_a_scoped_package_named_su ... ok
Ran 1 test in 0.002s
OK
```

### OBS-6 — evidencia sin sección para F-09; referencia colgante a un bloque inexistente

**Cambio**: `docs/specs/019-harness-evolution/evidence/P5-repair.md` — se agregó la sección `### F-09`
faltante (cambio→verificación→test, con nota explícita de que la reparación YA estaba implementada en
ronda 1; lo que faltaba era la sección dedicada) y se cerró la referencia colgante "ver bloque de gates
al final de este archivo" con el bloque de gates real (ver sección "Gates" de ESTE archivo — la ronda 2
—, referenciada desde ahí).

## Gates (ronda 2)

`git diff --check` (limpio, sobre los archivos tocados en esta ronda):
```
$ git diff --check -- ai/scripts/set_agents_app.py tests/test_harness.py docs/adr/0038-tools-catalog-discovery.md docs/specs/019-harness-evolution/evidence/P5-repair.md
$ echo "EXIT=$?"
EXIT=0
```

`git status --porcelain` — sin `tools.local.toml` ni `tools.proposals.json`:
```
$ git status --porcelain | grep -E "tools\.local\.toml|tools\.proposals\.json"
(sin salida)
```

`python3 -m unittest discover -s tests` (corrida intermedia, ANTES de agregar el test de pin de OBS-5 —
se deja pegada porque documenta el conteo exacto en un punto intermedio, útil para reconciliar el número
final de abajo):
```
$ python3 -m unittest discover -s tests
Ran 911 tests in 497.438s
OK (skipped=3)
```

`./ai/scripts/verify.sh` (corrida FINAL, con el árbol de trabajo completo — incluye el test de pin de
OBS-5 agregado después de la corrida de arriba, de ahí el +1):
```
$ ./ai/scripts/verify.sh
...
Ran 912 tests in 549.238s

OK (skipped=3)
GLOBAL_PORTABILITY_OK
CANONICAL_PATHS_OK
FEATURE_STATE_OK
VERIFY_PASS
```
Reconciliación: base declarada al inicio de esta ronda 904 OK / 3 skips; 8 tests nuevos en esta ronda (3
de NEW-01 + 1 de F-06 round 2 + 4 de las OBS reparadas/pineadas: OBS-1, OBS-2+OBS-3 combinado, OBS-4,
OBS-5) → 904 + 8 = 912, exactamente lo que reporta `verify.sh`. Ningún skip nuevo (sigue en 3), ningún
test existente bajó.

`./build.sh` / `./build.sh --check` (no toqué `Global/_canonical/` en esta ronda, pero se corrieron
igual, tal como pide la sección de Validación; sin drift):
```
$ ./build.sh
CHECK_PASS: generated and validated profile go-zen
Generated tracked artifacts for go-zen.

$ ./build.sh --check
CHECK_PASS: generated and validated profile go-zen
SELF_SCAFFOLD_SYNC_OK files=2
```

`python3 -m py_compile` (sanity de sintaxis sobre los archivos tocados):
```
$ python3 -m py_compile ai/scripts/set_agents_app.py tests/test_harness.py
$ echo "EXIT=$?"
EXIT=0
```
