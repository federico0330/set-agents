# Evidencia — PKG-1 `P1-check-que-verifica` (021-gates-que-no-mienten-ni-callan)

ADR: `docs/adr/0041-build-check-verifies-global.md` (indexado en `docs/adr/README.md`).

## 0. Línea base — el defecto reproducido antes de tocar nada

Con el `build.sh` de HOY (sin editar), ensucié `Global/opencode/AGENTS.md` con `cp`/escritura directa
(nunca `git`) y corrí `./build.sh --check`:

```
$ cp Global/opencode/AGENTS.md /scratch/AGENTS.md.orig
$ echo "" >> Global/opencode/AGENTS.md
$ echo "DIRT-MARKER-FOR-BASELINE-EVIDENCE" >> Global/opencode/AGENTS.md
$ ./build.sh --check
CHECK_PASS: generated and validated profile go-zen
SELF_SCAFFOLD_SYNC_OK files=2
$ echo "rc=$?"
rc=0
```

`rc=0` con `Global/` sucio — el bug del D-1 de la spec, confirmado antes de escribir una línea de
código. Restauré con `cp` (no `git`) inmediatamente después.

## 1. Tabla AC → cambio → prueba

| AC | Cambio | Archivo:línea | Prueba |
|---|---|---|---|
| AC-01 | `--check` genera un árbol dedicado forzado a `--profile go-zen` (ignorando `$PROFILE`/`active-profile`) y lo diffea contra `Global/` con el patrón de `verify.sh:26-28` (sin `\|\| true`), fallando `rc=1` y nombrando los archivos vía `diff -ruN` | `build.sh:90-130` (bloque `check)` nuevo, líneas 107-129) | `tests/test_harness.py:141-158` `test_build_check_detects_global_drift_and_names_the_file` (rojo confirmado contra el `build.sh` de ayer, ver §3) + verificación manual §4 |
| AC-02 | La salida distingue `SELF_SCAFFOLD_SYNC_OK`/`SELF_SCAFFOLD_DRIFT` de `GLOBAL_TREE_SYNC_OK`/`GLOBAL_TREE_DRIFT`; `BUILD_CHECK_PASS` solo aparece si ambos pasan. El auto-print de `generate.py` (`CHECK_PASS: generated and validated profile X`, que se leía como veredicto sin serlo) se silencia en modo `check` porque ese STAGING genérico ya no se construye para ese modo (`build.sh:76-88`) | `build.sh:104-105,123-129` | Verificación manual §4 (salida literal, limpia y sucia) |
| AC-03 | Test que ensucia `Global/opencode/AGENTS.md` con escritura directa (equivalente de `cp`, nunca `git`) y prueba que `--check` falla nombrando el archivo; limpio antes también prueba `rc=0` | `tests/test_harness.py:141-158` | Ver §3 (rojo→verde) |
| AC-04 | `verify.sh` ya corre `--check` (`:6`) antes que la suite (`:17`) — no se tocó ningún call site. Se fijó la regla por escrito en `TIPS-USO.md` y se guardó estructuralmente (orden de `verify.sh` + texto de doctrina) | `TIPS-USO.md` (sección "Safe generation and installation") · `tests/test_harness.py:7916-7929` `test_build_check_runs_before_the_suite_whenever_both_are_cited_as_gate_evidence` | Test nuevo, verde (§5) |
| AC-05 | Contenido de decisión redactado para que el orquestador lo registre con `log-decision` (no lo corrí yo — `log-decision` tiene `--actor default=orchestrator` y mi contrato dice "no mutes estado de feature: eso lo hace el orquestador") | — | Ver §7, texto exacto a registrar |

## 2. El cambio en `build.sh`

`build.sh:76-88`: la generación genérica de `$STAGING` (la que antes SIEMPRE corría, incluso en modo
`check`, sin que `check` la usara nunca — solo comparaba los 2 archivos de self-scaffold) ahora se
salta en modo `check`, porque `check` construye su propio árbol dedicado forzado a `go-zen`
(`build.sh:114-116`) y no necesita el genérico. Esto también evita que `check` imprima dos veces
`CHECK_PASS: generated and validated profile X` (una del genérico con el perfil local, otra del
dedicado con `go-zen`) — exactamente el ruido que AC-02 pide evitar.

`build.sh:90-130`, modo `check`:
1. Compara los 2 archivos de self-scaffold (sin cambios de lógica; solo el texto de comentario).
2. `SELF_SCAFFOLD_SYNC_OK files=2` si pasa (si no, sale antes, sin cambios respecto de hoy).
3. **Nuevo**: genera `$CHECK_STAGING` con `generate.py --output ... --profile go-zen` (forzado,
   ignora `$PROFILE`/`--profile`/`active-profile`) y hace `diff -ruN "$ROOT/Global/$harness"
   "$CHECK_STAGING/$harness"` para los 4 árboles — el patrón de `verify.sh:26-28`, no el de
   `--diff` (`build.sh:99-104` sigue intacto, con su `\|\| true`, como modo "mostrame").
4. `GLOBAL_TREE_SYNC_OK profile=go-zen harnesses=4` o `GLOBAL_TREE_DRIFT profile=go-zen` (+ `exit 1`).
5. `BUILD_CHECK_PASS` solo si los dos chequeos anteriores pasaron.

`--diff`/`generate`/`install` no cambiaron de comportamiento (siguen usando el `$STAGING` genérico,
con `$PROFILE`/`active-profile`, sin tocar).

## 3. AC-03 — rojo confirmado, después verde

Rojo, contra el `build.sh` de ayer (antes de tocarlo), corrido de verdad:

```
$ python3 -m unittest -v tests.test_harness.HarnessTests.test_build_check_detects_global_drift_and_names_the_file
test_build_check_detects_global_drift_and_names_the_file (...) ... FAIL

======================================================================
FAIL: test_build_check_detects_global_drift_and_names_the_file (...)
----------------------------------------------------------------------
Traceback (most recent call last):
  File ".../tests/test_harness.py", line 154, in test_build_check_detects_global_drift_and_names_the_file
    self.assertNotEqual(dirty.returncode, 0, "build.sh --check must fail on a dirtied Global/ file")
AssertionError: 0 == 0 : build.sh --check must fail on a dirtied Global/ file

----------------------------------------------------------------------
Ran 1 test in 0.663s

FAILED (failures=1)
```

Después de implementar `build.sh`, el mismo test, verde:

```
$ python3 -m unittest -v tests.test_harness.HarnessTests.test_build_check_detects_global_drift_and_names_the_file
test_build_check_detects_global_drift_and_names_the_file (...) ... ok

----------------------------------------------------------------------
Ran 1 test in 1.216s

OK
```

El test escribe/restaura el archivo con bytes directos (`Path.read_bytes`/`write_bytes`) dentro de
un `try/finally` — nunca `git checkout`/`git restore`. Verificado después de correrlo que
`Global/opencode/AGENTS.md` quedó byte-idéntico al estado previo (incluye el WIP no comiteado que ya
tenía la sesión, ajeno a este test):

```
$ cmp /scratch/AGENTS.md.pretest Global/opencode/AGENTS.md && echo IDENTICAL
IDENTICAL
```

## 4. Verificación manual de AC-01/AC-02 (salida literal)

Limpio:

```
$ ./build.sh --check
SELF_SCAFFOLD_SYNC_OK files=2
GLOBAL_TREE_SYNC_OK profile=go-zen harnesses=4
BUILD_CHECK_PASS
$ echo rc=$?
rc=0
```

Sucio (`Global/opencode/AGENTS.md` con una línea agregada por escritura directa, después restaurado
con `cp`):

```
$ echo "DIRT-MANUAL-VERIFY" >> Global/opencode/AGENTS.md
$ ./build.sh --check
SELF_SCAFFOLD_SYNC_OK files=2
diff -ruN /home/federico/SET-AGENTES/Global/opencode/AGENTS.md /var/tmp/set-agentes-check.NbjDld/opencode/AGENTS.md
--- /home/federico/SET-AGENTES/Global/opencode/AGENTS.md	...
+++ /var/tmp/set-agentes-check.NbjDld/opencode/AGENTS.md	...
@@ -112,4 +112,3 @@
 production operation the user explicitly requested is NOT a stop — do it and record it; the stop is for
 credentials out of reach after the resolve-first attempt, production DATA touched by the harness's own
 initiative, and destructive operations.
-DIRT-MANUAL-VERIFY
GLOBAL_TREE_DRIFT profile=go-zen
$ echo rc=$?
rc=1
$ cp /scratch/AGENTS.md.pretest2 Global/opencode/AGENTS.md   # restaurado, no con git
$ cmp /scratch/AGENTS.md.pretest2 Global/opencode/AGENTS.md && echo RESTORED_OK
RESTORED_OK
```

Nombra el archivo (`AGENTS.md`, vía los headers `---`/`+++` de `diff -ruN`), distingue las dos
verificaciones, y `BUILD_CHECK_PASS` no aparece cuando hay drift.

## 5. AC-04 — test de orden, verde

```
$ python3 -m unittest -v tests.test_harness.HarnessTests.test_build_check_runs_before_the_suite_whenever_both_are_cited_as_gate_evidence
test_build_check_runs_before_the_suite_whenever_both_are_cited_as_gate_evidence (...) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.003s

OK
```

`verify.sh` no se tocó (ya tenía el orden correcto: `--check` en `:6`, la suite en `:17`). Se agregó
la regla en `TIPS-USO.md` (sección "Safe generation and installation") y un test que ancla
estructuralmente el orden (`text.index` de una línea contra la otra) más la presencia del texto de
doctrina, para que no pueda revertirse en silencio.

## 6. Los tres call sites que esperan `rc=0` — verificados corriéndolos, no asumidos

### `install.sh:370` (`"$ROOT/build.sh" --check`, bajo `set -euo pipefail`)

No se puede correr `install.sh` completo sin riesgo de tocar el HOME real. Se corrió el test
existente que sí ejecuta esa línea de verdad, contra el árbol real del repo, con HOME apuntando a un
directorio temporal (no simula nada: usa `subprocess.run(check=True)`, así que si `install.sh`
hubiera devuelto `rc != 0` el test habría lanzado `CalledProcessError` y fallado):

```
$ python3 -m unittest -v tests.test_harness.HarnessTests.test_install_sh_creates_set_agents_link
test_install_sh_creates_set_agents_link (...) ... ok

Ran 1 test in 22.569s
OK
```

Sin cambios en `install.sh`. Funciona porque `Global/` de este repo ya está en sync con `go-zen`
(verificado en §0/§4 con el árbol limpio).

### `setup_models.py:397` y `:570` (`subprocess.run([build.sh, "--check"], ...)`)

**Acá encontré un problema real, no hipotético**, y lo arreglé dentro del alcance del paquete (no
es uno de los 17 call sites protegidos de AC-04, ni relitiga la decisión del perfil fijo).

Corriendo el escenario real (mutar un modelo vía `setup_models.py`, SIN `--models`/`--output-models`
— es decir, sobre el `models.toml` real del repo, exactamente el código de producción, no un mock)
contra mi primer intento de `build.sh` (que forzaba `go-zen` para `--check` pero seguía usando
`--check` como gate post-escritura):

```
$ cp models.toml /scratch/models.toml.orig
$ python3 ai/scripts/setup_models.py --set audit.codex_effort=high --no-install --yes
SELF_SCAFFOLD_SYNC_OK files=2
diff -ruN .../Global/codex/agents/delta-reviewer.toml ...
-model_reasoning_effort = "xhigh"
+model_reasoning_effort = "high"
[... 4 archivos más de Global/codex/agents/*.toml ...]
GLOBAL_TREE_DRIFT profile=go-zen
BUILD_CHECK_FAIL rc=1 — corré ./build.sh --check para ver el detalle
MODELS_WRITTEN /home/federico/SET-AGENTES/models.toml
$ echo rc=$?
rc=1
$ cp /scratch/models.toml.orig models.toml   # restaurado con cp, no git
$ cmp /scratch/models.toml.orig models.toml && echo BYTE_IDENTICAL_RESTORED
BYTE_IDENTICAL_RESTORED
```

**Causa raíz**: `setup_models.py` escribe un `models.toml` nuevo y corre `build.sh --check`
**antes** de que nada regenere `Global/` (eso lo hace `--install`, y `--install` instala al HOME del
usuario, no toca `Global/` del repo — solo `./build.sh` a secas, sin flags, actualiza `Global/`, y
eso pasa en un commit aparte). Con `--check` respondiendo ahora "¿coincide `Global/` con una
generación fresca?" (AC-01, correcto), cualquier cambio de modelo real hace que la respuesta sea
"no" — no porque el cambio esté mal, sino porque literalmente nadie regeneró `Global/` todavía. Es
exactamente la pregunta equivocada para ese punto del flujo: `--check` ahora es un gate de
repositorio, y acá lo que se necesita es un smoke test de "¿esta config nueva genera sin explotar?",
sin comparar contra nada.

**Nota importante**: `docs/notas/decisiones/2026-08-12 check-compara-con-perfil-canonico-fijo.md`
(ya registrada por el orquestador, presumiblemente durante spec-challenge) afirma en sus
consecuencias: *"install.sh y setup_models.py siguen funcionando sin tocarlos"*. Para `install.sh`
eso es correcto (§ arriba). **Para `setup_models.py` esa afirmación no resistió la re-ejecución**:
sin tocarlo, rompía en todo cambio de modelo real. Lo dejo consignado explícitamente porque el aviso
de proceso de este paquete pide exactamente eso — no dejar pasar una afirmación de verificación que
no se sostiene.

**Arreglo, dentro del alcance del paquete** (`ai/scripts/setup_models.py`, no es uno de los 17 call
sites de la suite ni toca la decisión del perfil fijo): agregué `_generate_smoke_test(profile)`
(`ai/scripts/setup_models.py:104-118`), que llama a `build.sh --output <tmp> --profile <profile>` —
un modo que YA EXISTE en `build.sh` (`build.sh:55-60`, sin tocar) y que hace exactamente lo que el
smoke test necesita: correr `generate.py` completo (los mismos `die()` que antes atrapaba el
`--check` viejo como efecto colateral de construir su STAGING) sin comparar contra `Global/`. Los
dos call sites (`setup_models.py:589-604` no-interactivo, `setup_models.py:416-421` wizard) ahora
llaman a `_generate_smoke_test(profile)` en vez de `build.sh --check`. Los mensajes de error se
renombraron de `BUILD_CHECK_FAIL` a `MODELS_GENERATE_FAIL`/`BUILD_INSTALL_FAIL` (separé el caso
"no generó" del caso "no instaló", que antes compartían el mismo mensaje engañoso).

Verificación del mismo escenario, con el arreglo:

```
$ cp models.toml /scratch/models.toml.orig2
$ python3 ai/scripts/setup_models.py --set audit.codex_effort=high --no-install --yes
CHECK_PASS: generated and validated profile go-zen
MODELS_WRITTEN /home/federico/SET-AGENTES/models.toml
$ echo rc=$?
rc=0
$ cp /scratch/models.toml.orig2 models.toml   # restaurado con cp, no git
$ cmp /scratch/models.toml.orig2 models.toml && echo RESTORED_OK
RESTORED_OK
```

`rc=0`, comportamiento correcto restaurado.

**Cobertura de tests preexistente de esta rama**: ningún test existente ejercía estos dos call
sites de verdad — todos los tests de `setup_models.py` usan `--models`/`--output-models`
("plumbing"), que salta explícitamente todo este bloque (`if not plumbing:`), y el flujo interactivo
del wizard requiere una TTY real (`wizard()` sale con `rc=2` sin una) que ningún test de
`test_models_wizard_ui.py` cruza hasta la opción "Guardar" (todas sus secuencias de picks terminan en
"Salir sin guardar"). Verificado con `grep -n` antes de escribir esta afirmación. Por eso la
verificación de este AC fue manual y directa contra el código de producción real, restaurando con
`cp` cada vez — no hay una regresión de cobertura automática que reparar, porque no había cobertura
ahí para empezar.

## 7. AC-05 — texto para `log-decision` (no lo corrí; ver nota abajo)

No ejecuté `feature-state.py log-decision` yo mismo: el comando tiene `--actor` por default
`orchestrator`, y mi contrato de implementer dice "no mutes estado de feature: eso lo hace el
orquestador". Dejo acá el contenido exacto para que el orquestador lo registre:

```
python3 ai/scripts/feature-state.py log-decision \
  --title "Los gates de build.sh --check en 019/020 solo probaban self-scaffold, no ausencia de drift" \
  --feature-id 021-gates-que-no-mienten-ni-callan --package-id PKG-1 \
  --context "Durante 019 y 020 se registraron decenas de gates citando './build.sh --check -> CHECK_PASS + SELF_SCAFFOLD_SYNC_OK files=2' como evidencia de 'sin drift'. El build.sh de esas features (antes de ADR-0041) generaba un STAGING y solo comparaba dos archivos de self-scaffold (feature-state.py, check-owned-paths.py) entre PROYECTO/ai/scripts/ y ai/scripts/; el STAGING nunca se comparaba contra Global/. El texto CHECK_PASS que se leía lo imprimía generate.py al generar (ran without exploding), no un veredicto de drift. El delta review de 020/P2 detecto 2 lineas de drift latente en Global/* que ese gate no vio." \
  --decision "No se reabren 019 ni 020: sus gates quedan anotados, no invalidados. Lo que probaba realmente ese './build.sh --check -> CHECK_PASS' era: (1) que generate.py corrio sin excepciones para el perfil activo de esa maquina/corrida, y (2) que feature-state.py y check-owned-paths.py coincidian byte a byte entre PROYECTO/ai/scripts/ y ai/scripts/. No probaba que Global/{opencode,claude-code,codex,pi} coincidiera con lo que generate.py produce -- esa comparacion no existia. ADR-0041/PKG-1 (021) corrigio build.sh --check para que compare de verdad, con perfil fijo go-zen." \
  --consequences "Ninguna evidencia de 019/020 se invalida retroactivamente ni se reabre esa feature; queda documentado que 'CHECK_PASS' en esos gates significaba 'generate.py no exploto', nunca 'Global/ sin drift'. A partir de 021/PKG-1, un './build.sh --check -> CHECK_PASS' SI certifica ausencia de drift en Global/ (perfil go-zen)."
```

## 8. Gates

- `python3 -m unittest -v tests.test_harness.HarnessTests.test_build_check_detects_global_drift_and_names_the_file` → **OK** (rojo→verde documentado en §3).
- `python3 -m unittest -v tests.test_harness.HarnessTests.test_build_check_runs_before_the_suite_whenever_both_are_cited_as_gate_evidence` → **OK**.
- `python3 -m unittest -v tests.test_harness.HarnessTests.test_install_sh_creates_set_agents_link` → **OK** (call site real, §6).
- `python3 -m unittest -v tests.test_harness.HarnessTests.test_guest_copy_scaffolds_and_verifies_portably` → **OK** (`build.sh --install` sobre un guest copiado).
- `python3 -m unittest -v tests.test_harness.HarnessTests.test_every_adr_on_disk_has_a_row_in_the_index tests.test_harness.HarnessTests.test_the_adr_index_never_lists_a_file_that_is_not_there` → **OK** (ADR-0041 indexado).
- `python3 -m py_compile ai/scripts/*.py ai/scripts/routing_core/*.py ai/scripts/feature_state_lib/*.py PROYECTO/ai/scripts/feature_state_lib/*.py tests/*.py` → **PY_COMPILE_OK**.
- `git diff --check` → **rc=0**, sin problemas de whitespace.
- `python3 -m unittest discover -s tests -v` completo, corrida limpia (sin ediciones concurrentes, lanzada recién después de terminar todos los cambios de este paquete):
  ```
  Ran 972 tests in 724.082s
  OK (skipped=3)
  ```
  972 = 970 de línea base + los 2 tests nuevos de este paquete (§3, §5). 0 `FAIL`, 0 `ERROR`. Los 3
  skips son los preexistentes marcados `BLOCKED-by-environment` (E2E de pi real / route-decide sin
  ruta elegible en esta máquina), sin relación con este paquete.
- `./ai/scripts/verify.sh` (respeta AC-04 por construcción: `--check` en `:6`, la suite en `:17`):
  ```
  SELF_SCAFFOLD_SYNC_OK files=2
  GLOBAL_TREE_SYNC_OK profile=go-zen harnesses=4
  BUILD_CHECK_PASS
  [... suite completa, 972 tests, OK (skipped=3) ...]
  GLOBAL_PORTABILITY_OK
  CANONICAL_PATHS_OK
  FEATURE_STATE_OK
  VERIFY_PASS
  ```
  `rc=0`. Los `diff -ruN "Global/$harness" "$STAGING/$harness"` de `verify.sh:26-28` (sin `|| true`,
  bajo `set -e`) no produjeron salida para ninguno de los 4 árboles **después** de que la suite
  completa corriera y regenerara `Global/` decenas de veces — el criterio de cierre de la spec
  ("correr la suite completa y que `git diff --stat` no cambie por efecto de la propia suite") se
  cumple: `git diff --stat Global/` antes y después de esta corrida completa de `verify.sh` es
  idéntico (mismos 59 archivos del WIP preexistente de la sesión, ninguno nuevo).

## 9. Nota de proceso — una corrida contaminada, descartada explícitamente

Una primera corrida completa de la suite (en background) se lanzó antes de terminar de escribir los
tests/parches y se solapó en el tiempo con mis propias ediciones a `tests/test_harness.py` y
`ai/scripts/setup_models.py`. Terminó con `rc=1` y un solo `ERROR`:
`test_every_direct_run_picker_call_in_tuitests_pins_msvcrt_to_none` (`ast.parse` sobre el propio
`test_harness.py`, `IndentationError: unexpected indent` en un punto que no corresponde a ningún
cambio real mío). Re-corrido solo, inmediatamente, sin ediciones concurrentes:

```
$ python3 -m unittest -v tests.test_harness.TuiTests.test_every_direct_run_picker_call_in_tuitests_pins_msvcrt_to_none
... ok
Ran 1 test in 0.064s
OK
```

Confirmado como artefacto de la corrida concurrente (leyó el archivo mientras yo lo escribía), no un
hallazgo real. Lo dejo documentado en vez de omitirlo, y la corrida limpia (§8) se lanzó recién
después de terminar todas las ediciones, sin tocar nada mientras corre.
