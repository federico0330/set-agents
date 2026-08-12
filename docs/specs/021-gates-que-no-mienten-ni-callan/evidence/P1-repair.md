# Evidencia — repair-agent, PKG-1 `P1-check-que-verifica` (021-gates-que-no-mienten-ni-callan)

Alcance recibido: **P1-F03** y **P1-F04**, los dos `low`, los dos de documentación. P1-F01 y P1-F02
ya estaban reparados por el orquestador (excepciones aprobadas) antes de este spawn — no se tocan
acá.

## Tabla finding → cambio → verificación

| Finding | Cambio | Archivo:línea | Verificación |
|---|---|---|---|
| P1-F03 | Párrafo agregado (no reescritura) en "Consecuencias" del ADR: dice explícitamente que de los tres call sites solo `install.sh:370` siguió funcionando sin tocarlo, que `setup_models.py:397,570` sí se rompían, nombra `_generate_smoke_test` y el rename `BUILD_CHECK_FAIL` → `MODELS_GENERATE_FAIL`/`BUILD_INSTALL_FAIL` | `docs/adr/0041-build-check-verifies-global.md:126-144` (bloque nuevo insertado tras la línea 128 original) | `grep -n 'smoke_test\|MODELS_GENERATE_FAIL' docs/adr/0041-build-check-verifies-global.md` → ver §1 abajo, ya no vacío |
| P1-F04 | Puntero con wikilink agregado en la zona humana ("Notas propias", fuera de `<!-- notas:auto -->`) de la nota original, aclarando que la afirmación es falsa para `setup_models.py` y linkeando a la nota de corrección | `docs/notas/decisiones/2026-08-12 check-compara-con-perfil-canonico-fijo.md:24-29` | `sync-notes` corrido después, línea sobrevive (§2 abajo) |

## 1. P1-F03 — grep antes vacío, ahora no

```
$ grep -n 'smoke_test\|MODELS_GENERATE_FAIL' docs/adr/0041-build-check-verifies-global.md
137:  paquete, agregó `_generate_smoke_test(profile)` (`ai/scripts/setup_models.py:107-121`), que llama
142:  pasaron a llamar a `_generate_smoke_test(profile)` en vez de `build.sh --check`, y el mensaje de
143:  error `BUILD_CHECK_FAIL` se separó en `MODELS_GENERATE_FAIL` (no generó) y `BUILD_INSTALL_FAIL` (no
```

El párrafo se insertó dentro de la viñeta existente sobre los tres call sites (no se borró ni
reescribió nada previo — se extendió esa misma viñeta con una oración que empieza en "De los tres,
solo `install.sh:370`..."). Confirmado `ai/scripts/setup_models.py:107-121` como rango real de
`_generate_smoke_test` (leído directamente del archivo, no asumido de la nota del orquestador).

## 2. P1-F04 — wikilink agregado en zona humana, sobrevive `sync-notes`

Contenido agregado, ya en el archivo:

```
## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._

**Rectificación 2026-08-12** (no borra lo de arriba): la frase del bloque auto "install.sh y
setup_models.py siguen funcionando sin tocarlos" es correcta para `install.sh`, pero **falsa para
`setup_models.py`** — sí se rompía (por una razón distinta al perfil: corre `--check`
inmediatamente después de escribir un `models.toml` nuevo, antes de que nada regenere `Global/`).
Detalle y arreglo en
[[decisiones/2026-08-12 correccion-setup-models-si-habia-que-tocarlo|correccion-setup-models-si-habia-que-tocarlo]].
```

Corrida real de `sync-notes` después de escribir el cambio:

```
$ python3 ai/scripts/feature-state.py sync-notes
NOTES_SYNCED n=0
{
  "notes_dir": "/home/federico/SET-AGENTES/docs/notas",
  "ok": true,
  "written": []
}
```

`n=0`/`written: []` — el motor no reescribió el archivo (mi línea está fuera del bloque
`notas:auto`, así que no la toca). Releído después de `sync-notes`: la línea del wikilink sigue ahí,
byte a byte (confirmado con `Read`, ver el archivo completo abajo era innecesario porque nada
cambió; el bloque `<!-- notas:auto -->...<!-- /notas:auto -->` original tampoco se movió).

No se tocó `install.sh` ni ningún otro archivo (`grep -c` sobre el diff confirma solo 2 archivos
modificados, ver §5).

## 3. Gates pedidos por el mandato — resultado real, sin recortar

### `./build.sh --check`

```
$ ./build.sh --check
SELF_SCAFFOLD_SYNC_OK files=2
GLOBAL_TREE_SYNC_OK profile=go-zen harnesses=4
BUILD_CHECK_PASS
rc=0
```

**PASS.** Esperado: mis dos cambios son `docs/adr/` y `docs/notas/decisiones/`, ninguno de los
cuatro árboles de `Global/`.

### `git diff --check` — limpio para MIS DOS archivos, NO limpio para el repo entero

```
$ git diff --check -- docs/adr/0041-build-check-verifies-global.md "docs/notas/decisiones/2026-08-12 check-compara-con-perfil-canonico-fijo.md"
rc=0
```

Pero `git diff --check` sin acotar (todo el árbol de trabajo) **no** está limpio:

```
$ git diff --check
docs/notas/features/021-gates-que-no-mienten-ni-callan/P1-check-que-verifica.md:20: trailing whitespace.
+- P1-F01 [medium] closed —
docs/notas/features/021-gates-que-no-mienten-ni-callan/P1-check-que-verifica.md:21: trailing whitespace.
+- P1-F02 [low] closed —
docs/notas/features/021-gates-que-no-mienten-ni-callan/P1-check-que-verifica.md:22: trailing whitespace.
+- P1-F03 [low] open —
docs/notas/features/021-gates-que-no-mienten-ni-callan/P1-check-que-verifica.md:23: trailing whitespace.
+- P1-F04 [low] open —
```

**Esto NO lo causé yo.** Ver §4.

### `./ai/scripts/verify.sh`

```
$ ./ai/scripts/verify.sh > verify_out.log 2>&1; echo "EXIT=$?"
EXIT=1
```

**FAIL.** Causa: la suite completa (`python3 -m unittest discover -s tests -v`) corrió 972 tests con
**1 failure** (no 972 OK/3 skips como la línea base del implementer):

```
Ran 972 tests in 418.312s
FAILED (failures=1, skipped=3)
```

El único failure:

```
FAIL: test_guest_copy_scaffolds_and_verifies_portably (test_harness.HarnessTests.test_guest_copy_scaffolds_and_verifies_portably)
AC-09: an installed, space-named guest routes from a non-Git project.
Traceback (most recent call last):
  File "/home/federico/SET-AGENTES/tests/test_harness.py", line 3476, in test_guest_copy_scaffolds_and_verifies_portably
    self.assertEqual(verified.returncode, 0, verified.stdout + verified.stderr)
AssertionError: 2 != 0 : SELF_SCAFFOLD_SYNC_OK files=2
GLOBAL_TREE_SYNC_OK profile=go-zen harnesses=4
BUILD_CHECK_PASS
docs/notas/features/021-gates-que-no-mienten-ni-callan/P1-check-que-verifica.md:20: trailing whitespace.
[... las mismas 4 líneas de arriba ...]
```

Este test copia el árbol de trabajo completo (incluido el WIP no comiteado) a un `guest` y corre
`verify.sh` adentro; `verify.sh` en algún punto de su cadena de gates hace el equivalente de
`git diff --check`, que ve la misma suciedad de arriba y devuelve `rc=2`, no `rc=0`.

Reproducido también aislado (mismo resultado, sin ninguna otra ejecución concurrente):

```
$ python3 -m unittest -v tests.test_harness.HarnessTests.test_guest_copy_scaffolds_and_verifies_portably
... FAIL (mismo traceback)
```

## 4. Por qué esto NO es mío — evidencia, no memoria

1. **El archivo sucio no es ninguno de los dos que edité.** Edité `docs/adr/0041-...` y
   `docs/notas/decisiones/2026-08-12 check-compara-...`; el que aparece en `git diff --check` es
   `docs/notas/features/021-gates-que-no-mienten-ni-callan/P1-check-que-verifica.md`, que nunca toqué
   (ni `Edit` ni `Write` corrieron sobre ese path en esta sesión).
2. **Mi propio `sync-notes` no lo escribió.** Lo corrí después de mis dos ediciones y devolvió
   `NOTES_SYNCED n=0` / `"written": []` — cero archivos reescritos. El contenido sucio (con el
   trailing whitespace) ya estaba en disco antes de que yo corriera ese comando.
3. **El timestamp coincide exacto con una acción previa del orquestador, no mía.** El estado de la
   feature (`ai/state/features/021-gates-que-no-mienten-ni-callan.json`, `packages[0].repairs` y
   `verifications`) registra la reparación de P1-F01/P1-F02 y la verificación de las cuatro findings
   en `2026-08-12T14:50:13+00:00` — y el `mtime` real del archivo sucio en disco es exactamente esa
   misma marca (`stat -c %Y` → `1786546213` → `2026-08-12 14:50:13 -03`... UTC-3, coincide con
   `14:50:13Z`). Eso pasó **antes** de que este spawn arrancara.
4. **Causa raíz identificada, solo lectura (no toqué el archivo)**:
   `ai/scripts/feature_state_lib/render_notes.py:198-212`. La línea 202-203:
   ```python
   label = finding.get("category") or finding.get("summary") or ""
   line = f"- {finding.get('id')} [{finding.get('severity')}] {finding.get('status', 'open')} — {_short(label)}"
   ```
   Los cuatro findings de este paquete tienen `title`/`detail`/`required` pero **no** `category` ni
   `summary` (confirmado leyendo el JSON de estado, ver arriba) → `label` queda `""` → la línea
   renderizada termina en `" — "` con espacio final. Es un bug de la plantilla de "## Hallazgos",
   dispara cada vez que se regeneran notas para findings sin esos dos campos — nada específico de
   P1-F03/P1-F04 ni de mis cambios.

## 5. Alcance efectivamente tocado — solo dos archivos

```
$ git status --short docs/adr/0041-build-check-verifies-global.md "docs/notas/decisiones/2026-08-12 check-compara-con-perfil-canonico-fijo.md"
 M docs/adr/0041-build-check-verifies-global.md
 M "docs/notas/decisiones/2026-08-12 check-compara-con-perfil-canonico-fijo.md"
```

No se tocó `build.sh`, `setup_models.py`, nada bajo `tests/`, ni `ai/state/` (ni siquiera con lectura
mutante — todas las lecturas de estado en este documento fueron con `python3 -c` de solo lectura).

## 6. Conclusión sobre los gates

- **F03 y F04: reparados y verificados con sus propias validaciones específicas** (§1, §2) — ambas
  positivas.
- **`./build.sh --check`: PASS**, sin relación con el problema de abajo.
- **`git diff --check`: limpio para mis dos archivos; NO limpio a nivel repo**, por un archivo que no
  toqué, con causa raíz identificada en código (`render_notes.py`) fuera del alcance de este repair
  (dos findings de documentación, "no toques ... el estado de la feature").
- **`./ai/scripts/verify.sh`: FAIL (rc=1)**, exclusivamente por el mismo defecto preexistente
  (1 failure de 972, `test_guest_copy_scaffolds_and_verifies_portably`, que a su vez falla por el
  mismo trailing-whitespace).

No intenté arreglar el renderer: es código (`feature_state_lib`), no es ninguno de los dos findings
asignados, y mi mandato dice explícitamente "Solo estos dos findings" y "no mutes estado de feature:
eso lo hace el orquestador". Lo dejo consignado con `archivo:línea` para que el orquestador decida
(nuevo finding / fix directo / lo que corresponda) — no es un `HUMAN_DECISION_REQUIRED` de producto,
es un defecto de código con causa raíz ya señalada.
