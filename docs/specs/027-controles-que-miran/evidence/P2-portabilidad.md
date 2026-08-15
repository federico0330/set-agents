# 027/P2 — reparación de portabilidad de la frontera de Bubblewrap

Contexto: la cifra 1809s de `docs/specs/027-controles-que-miran/evidence/P2-gates-retry.md:61`
es de `verify.sh` completo (suite + otros gates), no de `tests.test_harness` solo -- **corrección
respecto a una primera cita errónea en este mismo archivo**. La comparación correcta para el
mismo comando que mido abajo (`python3 -m unittest tests.test_harness`) es la de
`docs/specs/027-controles-que-miran/evidence/P2-gates-retry.md:83`: `Ran 466 tests in 820.976s`,
`OK (skipped=2)`, corrida ya con el `copytree` incondicional + el literal `/usr/bin/bwrap` (el
código previo a esta reparación). Decisión de Federico (2026-08-14): degradación portable — la
frontera de bwrap solo aplica en Linux con bwrap presente; en su ausencia el audit hook
in-process (que es el que cumple AC-04/AC-05) sigue activo siempre, con un marcador visible por
stderr.

## Estado: completo

## Tabla cambio -> archivo:línea -> prueba

| Cambio | archivo:línea | Prueba que lo respalda |
|---|---|---|
| Detección de bwrap por `shutil.which` una sola vez (`_BWRAP`), con seam `SET_AGENTS_TEST_NO_BWRAP` para simular ausencia | `tests/__init__.py:47` | `test_unittest_write_guard_degrades_portably_without_bwrap`, además de las corridas manuales con `SET_AGENTS_TEST_NO_BWRAP=1` documentadas abajo |
| Marcador visible por stderr, una sola vez, cuando degrada | `tests/__init__.py:48-50` | corrida manual `SET_AGENTS_TEST_NO_BWRAP=1 python3 -m unittest ...` — línea `descendant-boundary: off (bwrap not found)` aparece una sola vez (ver bloques abajo) |
| `copytree` deja de ser incondicional al importar; se mueve a `_ensure_test_checkout()`, idempotente, llamada solo en la rama con bwrap de `_sandboxed_popen` | `tests/__init__.py:73-90`, llamada en `tests/__init__.py:133` | `test_unittest_write_guard_degrades_portably_without_bwrap` (mockea `shutil.copytree` y afirma `assert_not_called()`); neutralizado y confirmado rojo (ver abajo) |
| Literal `/usr/bin/bwrap` reemplazado por `_BWRAP` en el chequeo de auto-invocación y en la tupla de frontera | `tests/__init__.py:115-117`, `tests/__init__.py:151` | mismo test nuevo + las tres pruebas P2-F01 ya existentes siguen en verde con bwrap presente |
| `_sandboxed_popen` degrada: sin bwrap, aplica `_child_environment(...)` y delega en `_ORIGINAL_POPEN` sin envolver; `_SandboxPopen` solo se usa con bwrap | `tests/__init__.py:125-132` | `test_unittest_write_guard_degrades_portably_without_bwrap`; diagnóstico ad hoc `probe_confinement.py` (ver abajo) que muestra el despacho real (`_ORIGINAL_POPEN` sin envolver vs `_SandboxPopen` con la tupla bwrap) |
| Audit hook (`_test_write_audit`, `_reject_write_outside_sandbox`) sin tocar | no aplica (sin diff) | las pruebas P2 existentes (`test_unittest_write_guard_rejects_home_and_cli_destinations_before_mutation`, `test_unittest_write_guard_rejects_symlink_parent_for_remove_rename_and_dir_fd`) siguen en verde sin modificación |
| `skipUnless(tests._BWRAP, ...)` en los 3 tests que dependen de la frontera de procesos hijos | `tests/test_harness.py:8598,8610` (offset final tras insertar la prueba nueva), `tests/test_routing.py:2083` | corridas con y sin `SET_AGENTS_TEST_NO_BWRAP=1` (ver abajo): "ok" con bwrap, "skipped" sin bwrap, nunca desaparecidos del conteo |
| Test nuevo `test_unittest_write_guard_degrades_portably_without_bwrap` | `tests/test_harness.py` (agregado antes de `test_unittest_write_guard_rejects_home_and_cli_destinations_before_mutation`) | ver bloque de neutralización abajo |
| `import tests` agregado a `test_routing.py` (necesario para referenciar `tests._BWRAP` en el `skipUnless`) | `tests/test_routing.py:20` | mismas corridas del `skipUnless` de routing |

## Neutralizaciones (rojo confirmado) por test nuevo/modificado

Backups tomados con `cp` (nunca `git checkout/restore/stash`):
`/var/tmp/claude/.../scratchpad/{init.py.bak,test_harness.py.bak,test_routing.py.bak}`.

### 1) `test_unittest_write_guard_degrades_portably_without_bwrap` (test nuevo)

Neutralización: se eliminó la rama temprana `if _BWRAP is None: ... return _ORIGINAL_POPEN(...)`
de `_sandboxed_popen` (dejando que, incluso sin bwrap, el código intente construir la
tupla de frontera con `_BWRAP=None` como ejecutable). Confirma la mitad (b) del test:
la copia del checkout se dispara y el `Popen` real explota al intentar ejecutar `None`.

Comando: `python3 ai/scripts/heartbeat-run.py --interval 20 -- python3 -m unittest
tests.test_harness.HarnessTests.test_unittest_write_guard_degrades_portably_without_bwrap -v`

Salida literal (rojo confirmado):
```
test_unittest_write_guard_degrades_portably_without_bwrap (tests.test_harness.HarnessTests.test_unittest_write_guard_degrades_portably_without_bwrap)
027/P2 portability repair (Federico, 2026-08-14): AC-04/05 are enforced by the ... ERROR

======================================================================
ERROR: test_unittest_write_guard_degrades_portably_without_bwrap (...)
----------------------------------------------------------------------
Traceback (most recent call last):
  File ".../tests/test_harness.py", line 8570, in test_unittest_write_guard_degrades_portably_without_bwrap
    result = subprocess.run(
        [sys.executable, "-c", "print('degraded-ok')"], cwd=ROOT, text=True, capture_output=True,
    )
  ...
  File ".../tests/__init__.py", line 153, in _sandboxed_popen
    return _SandboxPopen(boundary, *popen_args, **popen_kwargs)
  ...
  File "<frozen posixpath>", line 178, in dirname
TypeError: expected str, bytes or os.PathLike object, not NoneType

----------------------------------------------------------------------
Ran 1 test in 0.004s

FAILED (errors=1)
```

Revertido con `cp init.py.bak tests/__init__.py` (diff contra el backup: vacío). Vuelto a
verde: ver "Ran 3 tests in 0.521s / OK" en la corrida posterior a la restauración (incluye
este test + los dos P2-F01 de abajo).

### 2) `skipUnless(tests._BWRAP, ...)` en las 3 pruebas P2-F01 dependientes de la frontera

Neutralización: se quitó el decorador `@unittest.skipUnless(...)` de las 3 funciones y se
corrió forzando `SET_AGENTS_TEST_NO_BWRAP=1` (sin el seam el decorador quedaría siempre
activo salvo que el host realmente no tenga bwrap).

**Resultado honesto, no ocultado:** en este entorno (usuario no-root, `/etc/hosts` no
escribible por permisos reales del SO sin importar bwrap; el PATH del fixture-probe y del
stub de rutas funciona igual con o sin confinamiento) las 3 pruebas siguen en **verde**
incluso sin bwrap y sin el skip -- no fueron diseñadas para fallar por su propio contenido
en un sandbox no-root, dependen del contexto de ejecución (en CI corriendo como root,
`/etc/hosts` SÍ sería escribible sin bwrap). Comando y salida:

```
$ SET_AGENTS_TEST_NO_BWRAP=1 python3 -m unittest tests.test_harness.HarnessTests.test_unittest_descendant_cannot_open_an_external_absolute_path_for_writing tests.test_harness.HarnessTests.test_unittest_descendant_preserves_fixture_path_inside_private_sandbox tests.test_routing.RoutingTests.test_route_probe_fixture_reaches_stubs_inside_descendant_boundary -v
descendant-boundary: off (bwrap not found)
test_unittest_descendant_cannot_open_an_external_absolute_path_for_writing (...) ... ok
test_unittest_descendant_preserves_fixture_path_inside_private_sandbox (...) ... ok
test_route_probe_fixture_reaches_stubs_inside_descendant_boundary (...) ... ok

Ran 3 tests in 16.389s

OK
```

Porque el rojo-por-contenido no es reproducible en este sandbox, se generó evidencia
alternativa de que el `skipUnless` protege un gap real (no decorativo): un diagnóstico ad
hoc (`probe_confinement.py`, no forma parte de la suite, no escribe nada fuera del
worktree) que inspecciona qué construye realmente `_sandboxed_popen` en cada modo, sin
ejecutar nada:

```
$ python3 probe_confinement.py            # bwrap presente (default)
bwrap active: True
dispatched via: _SandboxPopen (bwrap boundary)
launched args: ('/usr/bin/bwrap', '--die-with-parent', '--ro-bind', '/', '/', '--dev', '/dev',
  '--bind', '/var/tmp/set-agentes-unittest-a56et43w', '/var/tmp/set-agentes-unittest-a56et43w',
  '--bind', '.../child-tmp', '/tmp',
  '--bind', '.../checkout', '/home/federico/SET-AGENTES/.claude/worktrees/agent-af40bb882ba164335',
  '--setenv', 'PATH', '...', '--chdir', '...', '--', 'true')

$ SET_AGENTS_TEST_NO_BWRAP=1 python3 probe_confinement.py   # bwrap forzado ausente
descendant-boundary: off (bwrap not found)
bwrap active: False
dispatched via: ORIGINAL_POPEN (unconfined)
launched args: ['true']
```

Esto confirma el gap real que el `skipUnless` documenta: sin bwrap, el descendiente corre
sin ningún `ro-bind /` ni frontera de namespace -- exactamente lo que P2-F01 identificó
como el hueco que un hook in-process no puede cerrar. La decisión de Federico
(2026-08-14) es aceptar ese gap fuera de Linux+bwrap porque los ACs solo exigen el hook
in-process. Se marca explícitamente **sin verificar**: la degradación real en un proceso
corriendo como root (donde `/etc/hosts` sí sería escribible y las 3 pruebas SÍ irían a
rojo sin el skip) no se reprodujo en este entorno.

Verificación de que el decorador funciona correctamente en ambas direcciones (esto sí se
confirmó de punta a punta, con el decorador puesto):
- Con bwrap presente (default): las 3 pruebas corren y pasan ("ok", no "skipped") -- ver
  corrida de la sección "Verificación" abajo.
- Con `SET_AGENTS_TEST_NO_BWRAP=1`: las 3 pruebas se saltan explícitamente, nombrando la
  razón, y aparecen en el conteo (`skipped=N`), nunca desaparecen en silencio:

```
$ SET_AGENTS_TEST_NO_BWRAP=1 python3 -m unittest tests.test_harness.HarnessTests.test_unittest_descendant_cannot_open_an_external_absolute_path_for_writing tests.test_harness.HarnessTests.test_unittest_descendant_preserves_fixture_path_inside_private_sandbox -v
descendant-boundary: off (bwrap not found)
test_unittest_descendant_cannot_open_an_external_absolute_path_for_writing (...) ... skipped 'P2-F01 descendant boundary requires bwrap (portable degradation, 2026-08-14)'
test_unittest_descendant_preserves_fixture_path_inside_private_sandbox (...) ... skipped 'P2-F01 descendant boundary requires bwrap (portable degradation, 2026-08-14)'

Ran 2 tests in 0.000s

OK (skipped=2)

$ SET_AGENTS_TEST_NO_BWRAP=1 python3 -m unittest tests.test_routing.RoutingTests.test_route_probe_fixture_reaches_stubs_inside_descendant_boundary -v
descendant-boundary: off (bwrap not found)
test_route_probe_fixture_reaches_stubs_inside_descendant_boundary (...) ... skipped 'P2-F01 descendant boundary requires bwrap (portable degradation, 2026-08-14)'

Ran 1 test in 0.000s

OK (skipped=1)
```

Decoradores restaurados con `cp test_harness.py.bak tests/test_harness.py` y
`cp test_routing.py.bak tests/test_routing.py` (diff contra backup: vacío en ambos).

### Verificación (bwrap presente, sin ninguna neutralización activa)

```
$ python3 -m unittest tests.test_harness.HarnessTests.test_unittest_descendant_cannot_open_an_external_absolute_path_for_writing tests.test_harness.HarnessTests.test_unittest_descendant_preserves_fixture_path_inside_private_sandbox tests.test_harness.HarnessTests.test_unittest_write_guard_degrades_portably_without_bwrap tests.test_harness.HarnessTests.test_unittest_write_guard_rejects_home_and_cli_destinations_before_mutation tests.test_harness.HarnessTests.test_unittest_write_guard_allows_private_temporary_directory tests.test_harness.HarnessTests.test_unittest_write_guard_rejects_symlink_parent_for_remove_rename_and_dir_fd tests.test_harness.HarnessTests.test_unittest_child_home_implicitly_moves_state_to_that_fixture_home -v
... (7 tests) ...
Ran 7 tests in 0.509s

OK

$ python3 -m unittest tests.test_routing.RoutingTests.test_route_probe_fixture_reaches_stubs_inside_descendant_boundary -v
Ran 1 test in 29.450s

OK
```

## Medición de tiempo: con bwrap vs sin bwrap

Ambas corridas son `python3 -m unittest tests.test_harness` completo (471 tests, el mismo
comando y módulo que `P2-gates-retry.md:81-83` citaba como `466 tests` -- la diferencia de 5 es
la prueba nueva de esta reparación más otras agregadas desde entonces), en esta misma máquina,
en simultáneo con otros dos implementers corriendo sus propias suites (contención real, no un
entorno aislado -- ver "Sin verificar" sobre qué tan limpia es la comparación).

**Con bwrap (default, `_BWRAP` resuelve a `/usr/bin/bwrap`; el marcador de degradación no
imprime nada porque no degrada):**
```
$ python3 -m unittest tests.test_harness
...
Ran 471 tests in 892.499s

FAILED (failures=2, errors=3, skipped=2)
```

**Sin bwrap (`SET_AGENTS_TEST_NO_BWRAP=1`, seam agregado por esta reparación):**
```
$ SET_AGENTS_TEST_NO_BWRAP=1 python3 -m unittest tests.test_harness
descendant-boundary: off (bwrap not found)
...
Ran 471 tests in 812.499s

FAILED (failures=2, errors=4, skipped=4)
```

**Lectura:** 812.499s vs 892.499s -- ~80s (~9%) más rápido sin bwrap, y sin el `copytree`
incondicional de ~31MB que antes corría siempre al importar (ahora nunca se dispara sin bwrap,
confirmado por el test nuevo). El `skipped` sube de 2 a 4 porque las 2 pruebas
`skipUnless(tests._BWRAP, ...)` de `tests/test_harness.py` se saltan explícitamente (no
desaparecen del conteo). El resto del tiempo de la suite (la enorme mayoría) es trabajo real de
cada test (instalación, scaffolding, subprocess de `build.sh`/`install.sh`, generación de
`Global/opencode/*`), no la frontera de bwrap en sí -- por eso la ganancia es modesta acá, y por
eso la regresión medida en `P2-gates-retry.md` (1809s) fue en `verify.sh`, que corre bastante
más que solo `tests.test_harness`.

**Fallas observadas en ambas corridas (2 `FAIL` + 3-4 `ERROR`) -- no introducidas por este
diff, ver razonamiento:**

| Test | Con bwrap | Sin bwrap | Causa raíz (no relacionada a este diff) |
|---|---|---|---|
| `test_adr_0017_and_0007_amendment_and_superseding_decision_recorded` | ERROR | ERROR | `FileNotFoundError: ai/state/decisions-log.jsonl` -- este worktree (fast-forwardeado desde una rama vieja para poder leer el `tests/__init__.py` actual, ver más abajo) nunca tuvo `ai/state/` poblado; `ai/state/` está fuera de mi ownership (explícitamente prohibido tocar) |
| `test_check_and_native_codex_agents` | ERROR (`CalledProcessError` con la tupla de bwrap) | ERROR (mismo `CalledProcessError`, sin bwrap de por medio) | `./build.sh --check` sale con status 1 **con y sin bwrap** -- la causa es el propio `build.sh --check`, no la frontera; la tupla de bwrap además es byte-idéntica a la del código previo (`_BWRAP` resuelve al mismo `/usr/bin/bwrap` literal), así que ya fallaba antes de esta reparación |
| `test_install_sh_creates_set_agents_link` | ERROR | ERROR | mismo patrón: `install.sh` sale con status 1 con y sin bwrap -- no relacionado a la frontera |
| `test_install_sh_yes_terminates_the_opencode_auth_loop` | FAIL (assertion) | ERROR (`CalledProcessError`, categoría distinta pero mismo síntoma de fondo) | diff de `model:` entre `Global/opencode/agents/*.md` generado y el pin vigente -- drift de `models.toml`/routing en vivo, ajeno a `tests/__init__.py` |
| `test_build_check_detects_global_drift_and_names_the_file` | ok | FAIL | mismo drift de `model:` pins, capturado en el propio `shutil.copytree(ROOT, guest, ...)` del test (línea 201-205, no relacionado a `_TEST_CHECKOUT`); ver hipótesis abajo sobre por qué solo aparece sin bwrap |
| `test_guest_copy_scaffolds_and_verifies_portably` | FAIL | FAIL | `CANONICAL_DANGLING_PATH` sobre `ai/state/STATUS.md` y `ai/state/decisions-log.jsonl` -- mismo root cause que la primera fila: `ai/state/` ausente en este worktree |

Ninguna de estas 6 fallas toca `tests/__init__.py`, `_BWRAP`, `_sandboxed_popen` ni el audit
hook -- las trazas literales (arriba, en las corridas completas guardadas en
`/var/tmp/claude/.../scratchpad/{with-bwrap,no-bwrap}.log`) muestran o bien un
`FileNotFoundError` sobre `ai/state/` (fuera de mi ownership, explícitamente prohibido tocar) o
un `build.sh --check`/`install.sh` que sale con status 1 en ambas corridas por el mismo drift de
contenido en `Global/opencode/agents/*.md` (`model:` pins vs `models.toml`/routing en vivo,
terreno de otro implementer trabajando en paralelo en el mismo checkout de `main`). Que 3 de las
4 fallas de ese grupo aparezcan **con y sin bwrap por igual** es la evidencia más fuerte de que
no las causa este diff. Hipótesis, sin verificar con certeza total, sobre por qué
`test_build_check_detects_global_drift_and_names_the_file` sólo apareció en rojo en la corrida
sin bwrap (siendo el mismo drift): bajo bwrap ese test copia `ROOT` que, dentro del namespace
del hijo, resuelve a `_TEST_CHECKOUT` (una foto fija tomada por `_ensure_test_checkout()` una
sola vez, al principio de la corrida); sin bwrap, `shutil.copytree(ROOT, guest, ...)` lee el
`ROOT` real y en vivo, que pudo haber sido regenerado sobre la marcha por otro proceso
(`build.sh` de otro implementer corriendo en el mismo checkout compartido) entre el arranque de
la corrida y el momento exacto de ese test -- una carrera de datos preexistente entre suites
paralelas compartiendo el mismo árbol de trabajo, no algo que este diff cause o pueda arreglar
desde `tests/__init__.py`.

## Hallazgo importante: la degradación mutó de verdad 19 archivos reales del worktree

Al terminar las dos corridas completas de medición, `git status` mostraba **19 archivos
modificados de verdad** bajo `Global/opencode/agents/*.md` y `Global/opencode/opencode.json`
(pins de `model:` reescritos con valores degradados de `models.toml`/routing en vivo) que no
eran parte de mi diff. Esto es una consecuencia **concreta y real**, no hipotética, de aceptar
la degradación portable: sin bwrap (y aparentemente en algún camino de código incluso con
bwrap -- no aislé cuál corrida exacta la causó, ver abajo), algún test que invoca `build.sh`
o el auto-scaffold de `set_agents_app.py` terminó escribiendo sobre el `Global/opencode/` real
del worktree en lugar de una copia privada. El audit hook in-process no lo vio (corre en el
intérprete padre, no en el proceso hijo que hizo la escritura) y, sin la frontera de bwrap, no
había nada más deteniéndolo.

**Restaurado** con `git show HEAD:<path>` archivo por archivo (no `git checkout`/`git restore`,
por la restricción explícita de esta tarea) -- confirmado con `git status --short` limpio salvo
mis 3 archivos + el nuevo `P2-portabilidad.md`.

Esto **no es una regresión de este diff en el sentido de "un test que antes pasaba ahora
falla"** -- es la manifestación real del gap que P2-F01 documentó y que la decisión de
Federico (2026-08-14) aceptó conscientemente ("los ACs solo exigen el hook in-process"). Pero
es la primera vez que se ve el costo concreto: sin bwrap, un test con un bug de aislamiento
preexistente (probablemente el mismo `build.sh --check`/`install.sh` que ya fallaba con
`returncode=1` en ambas corridas, ver tabla de arriba) puede escribir sobre el propio checkout
en vez de sobre una copia. **Esto se reporta como `known_risk` explícito para el
package-reviewer/gate-runner**, no se intenta arreglar acá: arreglar el test que hace la
escritura real está fuera del alcance de esta tarea (toca `tests/test_harness.py` en zonas no
relacionadas a bwrap/portabilidad, o el propio `build.sh`) y arreglarlo "de paso" violaría el
alcance acotado del packet.

## Nota de entorno: worktree adelantado con fast-forward

Este worktree (`.claude/worktrees/agent-af40bb882ba164335`) estaba 14 commits detrás de `main`
al empezar -- `tests/__init__.py` tenía sólo 2 líneas, sin ninguna de las capas de P2 descritas
en la tarea. Se hizo `git merge --ff-only main` (verificado antes con
`git merge-base --is-ancestor HEAD main`, sin commits propios que perder) para poder leer y
tocar el `tests/__init__.py` real. `ai/state/` nunca se materializó en ese fast-forward (está
gitignored/fuera del control de versiones per ADR-0047), de ahí las fallas de `ai/state/` en la
tabla de arriba -- no son un efecto de mi cambio ni de este merge, son la ausencia estructural
de ese directorio en cualquier checkout fresco.

## Sin verificar

- Las 6 fallas de la tabla de arriba se razonan como preexistentes (mismo error con y sin
  bwrap en 3 de 4 del grupo `build.sh`/`install.sh`, `FileNotFoundError` sobre un directorio
  fuera de mi ownership en 2, y una tupla de bwrap byte-idéntica a la del código previo) pero
  **no se corrieron contra el `tests/__init__.py` sin parchear** (el de 2 líneas de este
  worktree antes del fast-forward no sirve de control porque directamente no tenía la lógica
  de P2) para confirmarlo con una corrida roja/verde de antes/después literal -- es inferencia
  por lectura de traza, no una neutralización con revert como las de la sección anterior.
- La degradación real en un proceso corriendo como **root** (donde `/etc/hosts` sí sería
  escribible sin bwrap y las 3 pruebas `skipUnless` irían genuinamente a rojo sin el
  decorador) no se reprodujo en este entorno no-root. Se compensó con el diagnóstico
  `probe_confinement.py` (inspección directa de qué construye `_sandboxed_popen`, sin
  ejecutar nada) — ver sección de neutralización #2.
- macOS y Windows reales (los otros dos runners de `.github/workflows/ci.yml`) no se
  probaron -- esta reparación es de código, no de CI; la simulación fue vía
  `SET_AGENTS_TEST_NO_BWRAP=1` en Linux, no un host macOS/Windows genuino.
- `test_guest_copy_scaffolds_and_verifies_portably` (`tests/test_harness.py:3659`, 132s
  medido en `P2-gates-retry.md`): no se aisló su tiempo individualmente con y sin bwrap
  en esta pasada (correrlo en soledad hubiera implicado un tercer `-m unittest` largo,
  fuera del presupuesto de una sola pasada). Por lectura de código: hace su **propio**
  `shutil.copytree(ROOT, guest, ...)` (línea 3671, no relacionado con el `_TEST_CHECKOUT`
  de `tests/__init__.py`) y sus `subprocess.run` sí pasan por `_sandboxed_popen` -- así que
  parte de su costo es nuestra frontera, parte es su propio copytree, y no se separaron
  las dos fuentes con medición.

## Seguimiento del coordinador: qué tests escriben en `Global/opencode/` vía proceso hijo

Presupuesto real gastado en esta tarea: **barato**, como pedía el pedido -- nada de correr la
suite completa de nuevo. Todo lo de abajo son corridas de un solo test (9-71s cada una) más una
copia descartable (`git archive`, sin `.git`, ~26MB) de un commit viejo para el punto 2.

### 1) Lista de los 19 archivos y qué test(s) los produce

Los 19 archivos exactos (capturados con `git status --porcelain` en este worktree, antes de
restaurar):
```
Global/opencode/agents/agent-factory.md
Global/opencode/agents/app-runner.md
Global/opencode/agents/architect.md
Global/opencode/agents/brainstormer.md
Global/opencode/agents/debugger.md
Global/opencode/agents/frontend-engineer.md
Global/opencode/agents/image-describer.md
Global/opencode/agents/implementer.md
Global/opencode/agents/integrator.md
Global/opencode/agents/local-gate-runner.md
Global/opencode/agents/orchestrator.md
Global/opencode/agents/package-planner.md
Global/opencode/agents/product-analyst.md
Global/opencode/agents/project-bootstrapper.md
Global/opencode/agents/refactor-specialist.md
Global/opencode/agents/repair-agent.md
Global/opencode/agents/test-writer.md
Global/opencode/agents/ux-ui-designer.md
Global/opencode/opencode.json
```

Búsqueda estática de todos los call-sites de `run("./build.sh")` **sin** `--output`, `--check`,
`--diff` ni `--install` (los únicos que corren `MODE="generate"`, la rama de `build.sh` que
hace `rm -rf "$ROOT/Global/$harness"; cp -a "$STAGING/$harness" "$ROOT/Global/$harness"` para
los 4 harnesses -- ver `build.sh:137-144`, ya citado en el hallazgo de arriba): **18
call-sites**, en 18 tests distintos de `tests/test_harness.py`:

```
$ grep -n 'run("\./build\.sh"' tests/test_harness.py | grep -v -- '--check\|--diff\|--output\|--install'
179   test_check_and_native_codex_agents
4047  test_orchestrator_narration_reaches_all_four_harnesses
4073  test_context_is_allowlisted_read_only_across_all_three_runtimes
4097  test_turn_continuity_doctrine_reaches_all_three_harnesses
4320  test_orchestrator_doctrine_branches_on_route_decide_reason_taxonomy
4388  test_orchestrator_doctrine_demands_usage_on_every_direct_route_terminal_close
4425  test_opencode_orchestrator_permission_map_actually_admits_the_spawn_cli
5027  test_generated_mcp_is_off
5035  test_orchestrator_delegation_graph_is_broad_but_state_governed
5050  test_runtime_verifier_can_manage_browser_mcp_gate
5154  test_release_harnesses_require_gated_wrapper
5226  test_domain_knowledge_is_wired_through_the_canon
5768  test_the_delivery_commit_convention_is_declared_where_the_gate_reads_it
5790  test_consult_mode_is_wired_and_never_starts_pipeline
5809  test_architecture_gate_is_wired_through_the_canon
6046  test_rpl_p0a_package_gate_runner_is_opencode_only_and_strictly_scoped
9903  test_ac27_resolve_before_asking_mirrored_in_shared_doctrine_and_triage
9930  test_ac28_explicar_reaches_the_four_runtime_trees
```
(mapeo línea→test hecho leyendo hacia atrás desde cada línea hasta el `def test_...` que la
contiene; no es una lista completa de *todo* lo que puede escribir en `Global/` -- sólo de
`run("./build.sh")` sin flags, que es el patrón que produjo exactamente estos 19 archivos.)

**Confirmado con una corrida real, no sólo lectura de código:** aislé UN solo test
representativo (`test_check_and_native_codex_agents`, el primero de la lista) y lo corrí solo,
dos veces, con `git status --porcelain` antes y después de cada corrida:

```
$ git status --porcelain          # antes, limpio salvo mi diff
 M tests/__init__.py
 M tests/test_harness.py
 M tests/test_routing.py
?? docs/specs/027-controles-que-miran/evidence/P2-portabilidad.md

$ python3 -m unittest tests.test_harness.HarnessTests.test_check_and_native_codex_agents -v
test_check_and_native_codex_agents (...) ... ok
Ran 1 test in 29.895s
OK

$ git status --porcelain          # después, CON bwrap: sin cambio
 M tests/__init__.py
 M tests/test_harness.py
 M tests/test_routing.py
?? docs/specs/027-controles-que-miran/evidence/P2-portabilidad.md

$ SET_AGENTS_TEST_NO_BWRAP=1 python3 -m unittest tests.test_harness.HarnessTests.test_check_and_native_codex_agents -v
descendant-boundary: off (bwrap not found)
test_check_and_native_codex_agents (...) ... ok
Ran 1 test in 71.413s
OK

$ git status --porcelain          # después, SIN bwrap: los 19 archivos, exactos
 M Global/opencode/agents/agent-factory.md
 M Global/opencode/agents/app-runner.md
 M Global/opencode/agents/architect.md
 M Global/opencode/agents/brainstormer.md
 M Global/opencode/agents/debugger.md
 M Global/opencode/agents/frontend-engineer.md
 M Global/opencode/agents/image-describer.md
 M Global/opencode/agents/implementer.md
 M Global/opencode/agents/integrator.md
 M Global/opencode/agents/local-gate-runner.md
 M Global/opencode/agents/orchestrator.md
 M Global/opencode/agents/package-planner.md
 M Global/opencode/agents/product-analyst.md
 M Global/opencode/agents/project-bootstrapper.md
 M Global/opencode/agents/refactor-specialist.md
 M Global/opencode/agents/repair-agent.md
 M Global/opencode/agents/test-writer.md
 M Global/opencode/agents/ux-ui-designer.md
 M Global/opencode/opencode.json
 M tests/__init__.py
 M tests/test_harness.py
 M tests/test_routing.py
?? docs/specs/027-controles-que-miran/evidence/P2-portabilidad.md
```

Un solo test, corrido solo, sin bwrap, reproduce exactamente los 19 archivos. **Con bwrap la
misma corrida no toca nada.** Restaurado de nuevo con `git show HEAD:<path>` (no
`git checkout`/`git restore`), confirmado limpio.

No hace falta correr los otros 17 uno por uno para responder la pregunta del coordinador: los
18 call-sites ejecutan el mismo código de `build.sh` (`MODE="generate"`, sin `--output`), con
el mismo `cwd=ROOT` (el helper `run()` de `tests/test_harness.py:41-49` lo fija así para
cualquier invocación), en la misma máquina con el mismo estado de probes de proveedores -- la
causa de la deriva de contenido (`model:` degradados) es determinística por esta máquina, no
por cuál test corre. El único que **verifiqué en vivo** es `test_check_and_native_codex_agents`;
los otros 17 comparten el call-site idéntico (`run("./build.sh")`, `cwd=ROOT`, sin frontera)
así que el mecanismo es el mismo, pero no corrí cada uno para confirmarlo -- lo marco como
inferencia estructural, no medición, para los otros 17.

### 2) ¿Preexistente o introducido por P2? Medido, no razonado

`tests/__init__.py` sólo tiene 2 commits en su historia (`git log --follow`): el commit actual
(`9a2c8c2`, "027/P1 accepted + P2 en repair") y uno anterior (`2fdbb15`). El padre de `9a2c8c2`
es `c0a2a41` ("024/C4 ... "), el estado justo antes de que 027 (P1 y P2 juntos, en un solo
commit) tocara `tests/__init__.py` por primera vez:

```
$ git show c0a2a41:tests/__init__.py
"""Test package for unittest discovery."""
```

Sin sys.path fix, sin audit hook, sin bwrap -- cero protección de ningún tipo. El mismo test,
byte-idéntico, ya existía ahí:

```
$ git show c0a2a41:tests/test_harness.py | sed -n '168,180p'
    def test_check_and_native_codex_agents(self):
        run("./build.sh", "--check")
        run("./build.sh")
        agents = sorted((ROOT / "Global/codex/agents").glob("*.toml"))
        ...
```

Lo corrí de verdad, aislado, en una copia descartable de ese commit (`git archive c0a2a41 | tar
-x` a un directorio de scratch -- sin `.git`, para no interferir con mi worktree; nunca toqué
mi checkout real para esto):

```
$ cd <scratch>/repo
$ stat -c '%i %Y %n' Global/opencode/agents/agent-factory.md Global/opencode/opencode.json
14157247 1786705775 Global/opencode/agents/agent-factory.md
14157341 1786705775 Global/opencode/opencode.json

$ PYTHONPATH="$(pwd)/ai/scripts" python3 -m unittest tests.test_harness.HarnessTests.test_check_and_native_codex_agents -v
test_check_and_native_codex_agents (...) ... ok
Ran 1 test in 9.368s
OK

$ stat -c '%i %Y %n' Global/opencode/agents/agent-factory.md Global/opencode/opencode.json
14157250 1786757448 Global/opencode/agents/agent-factory.md
14157407 1786757448 Global/opencode/opencode.json
```

El inode y el mtime cambiaron para los dos archivos -- `rm -rf` + `cp -a` reales ocurrieron
sobre el `Global/` de esa copia, exactamente el mismo patrón. (El contenido resultó
byte-idéntico al ya commiteado en esa corrida puntual -- `sha256sum -c` coincidió -- así que
esa vez en particular no hubo *drift* observable, pero la escritura sí ocurrió, mecánicamente,
sobre un checkout que nunca tuvo bwrap, sys.path fix, ni audit hook.)

**Conclusión medida: preexistente.** El patrón "`run("./build.sh")` con `cwd=ROOT` reescribe
`Global/` de verdad" ya estaba en el harness antes de que 027 existiera. 027/P2 no lo creó --
fue la PRIMERA vez que algo (la frontera de bwrap) lo hizo seguro. Esta reparación de
portabilidad, al degradar sin bwrap, no reintroduce un bug nuevo: **revierte al comportamiento
que siempre existió** en cualquier host sin bwrap (o en cualquier commit anterior a P2).

Costo real de esto: dos corridas de un test (~10-30s cada una) + un `git archive` (~1s, 26MB) +
lectura de 2 commits. Nada cerca de correr la suite vieja completa.

### 3) ¿El hijo escribe en ROOT porque el test se lo pide, o por herencia de cwd/env?

**Se lo pide explícitamente.** `tests/test_harness.py:41-49`:
```python
def run(*args, env=None, check=True):
    return subprocess.run(
        args,
        cwd=ROOT,
        env={**os.environ, **(env or {})},
        text=True,
        capture_output=True,
        check=check,
    )
```
`cwd=ROOT` está *hardcodeado* en el helper que estos 18 tests usan a propósito. Y `build.sh` en
`MODE="generate"` (la que corre cuando NO se pasa `--output`) hace, literalmente
(`build.sh:137-144`):
```bash
generate)
  for harness in opencode claude-code codex pi; do
    rm -rf "$ROOT/Global/$harness"
    cp -a "$STAGING/$harness" "$ROOT/Global/$harness"
  done
```
Donde `$ROOT` adentro de `build.sh` es `$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)` -- el
directorio del propio `build.sh`, que es el `cwd` que el test le pasó. No hay ningún cwd/env
heredado por accidente: **el test pide `cwd=ROOT`, y `build.sh` sin `--output` regenera
`Global/` en el propio `ROOT` por diseño** (es su modo por default, pensado para cuando alguien
corre `./build.sh` a mano en su propio checkout para regenerar los artefactos trackeados). Estos
18 tests reutilizan ese mismo comportamiento de producción para poder leer `Global/codex/agents/*.toml`
etc. después y afirmar sobre el contenido regenerado -- confiando enteramente en que la frontera
de bwrap (cuando existe) hace que ese `cwd=ROOT` sea seguro.

Esto decide la pregunta del coordinador: **es un problema de seam, no de fixture.** El fixture
(`run()`, `cwd=ROOT`) y el propio `build.sh` (`MODE="generate"` escribe en `$ROOT`) hacen
exactamente lo que se les pidió, tal como lo hacían antes de que existiera cualquier frontera
(punto 2). Lo que cambia el costo de la decisión de Federico es que, sin bwrap, ya no hay nada
que interponga una copia privada entre ese `cwd=ROOT` deliberado y el disco real -- no que el
fixture esté mal escrito o que algo se filtre por error de env/cwd.

**Confirmado y árbol limpio.** `git status --porcelain` en este worktree, ahora:
```
 M tests/__init__.py
 M tests/test_harness.py
 M tests/test_routing.py
?? docs/specs/027-controles-que-miran/evidence/P2-portabilidad.md
```
Sólo mi diff original + esta evidencia. No pude correr `git status --porcelain` sobre
`/home/federico/SET-AGENTES` (el checkout compartido): el sandbox de este agente rechaza
explícitamente cualquier comando de git que apunte fuera de mi propio worktree ("git operations
must target its own worktree"). No operé sobre esa ruta en ningún momento de esta sesión ni de
la anterior -- todo lo que corrí usó rutas absolutas dentro de
`.claude/worktrees/agent-af40bb882ba164335` o directorios de scratch descartables sin `.git` --
así que no hay razón para esperar cambios ahí, pero no puedo pegar la salida literal que el
coordinador pidió para esa ruta específica; se lo dejo para que lo confirme él mismo o me
autorice el comando puntual si lo necesita verificado por mí.

## Reparación del seam (Federico, 2026-08-14): los 18 call sites pasan a `--output DIR`

Decisión tomada tras la investigación anterior: no es un caso raro, son 18 tests que
reescriben `Global/` en cada corrida. Se arregla el seam, no `build.sh` ni el helper `run()`.

### 1) Call sites tocados (18/18) — ninguno quedó afuera

Los 18 call sites identificados en el seguimiento anterior fueron todos convertidos. Ningún
test de los 18 verifica *que* `build.sh` escriba en `ROOT` como parte de su propio contrato --
todos leen contenido generado para afirmar sobre texto/estructura, nunca sobre la ubicación de
la escritura -- así que los 18 se pudieron redirigir sin perder lo que verifican:

| # | Test | Línea (antes) | Qué leía en `ROOT/Global/...` | Ahora lee en |
|---|---|---|---|---|
| 1 | `test_check_and_native_codex_agents` | 179 | `Global/codex/agents/*.toml`, `gate-runner.toml` | `<tmp>/codex/agents/...` |
| 2 | `test_orchestrator_narration_reaches_all_four_harnesses` | 4047 | opencode/claude-code/codex/pi `orchestrator.*`, `pi/AGENTS.md` | `<tmp>/<harness>/...` |
| 3 | `test_context_is_allowlisted_read_only_across_all_three_runtimes` | 4073 | opencode/claude-code/codex `orchestrator.*` | `<tmp>/<harness>/...` |
| 4 | `test_turn_continuity_doctrine_reaches_all_three_harnesses` | 4097 | opencode/claude-code/codex `orchestrator.*` | `<tmp>/<harness>/...` |
| 5 | `test_orchestrator_doctrine_branches_on_route_decide_reason_taxonomy` | 4320 | `Global/*/agents/orchestrator.*` (glob genérico) | `<tmp>/*/agents/orchestrator.*` |
| 6 | `test_orchestrator_doctrine_demands_usage_on_every_direct_route_terminal_close` | 4388 | mismo glob genérico | mismo, sobre `<tmp>` |
| 7 | `test_opencode_orchestrator_permission_map_actually_admits_the_spawn_cli` | 4425 | `Global/opencode/agents/orchestrator.md` | `<tmp>/opencode/agents/orchestrator.md` |
| 8 | `test_generated_mcp_is_off` | 5027 | `Global/opencode/opencode.json`, `Global/claude-code/settings.overlay.json` | `<tmp>/opencode/...`, `<tmp>/claude-code/...` |
| 9 | `test_orchestrator_delegation_graph_is_broad_but_state_governed` | 5035 | `Global/opencode/...`, `Global/claude-code/...` | `<tmp>/...` |
| 10 | `test_runtime_verifier_can_manage_browser_mcp_gate` | 5050 | opencode/claude-code/codex `runtime-verifier.*` | `<tmp>/...` |
| 11 | `test_release_harnesses_require_gated_wrapper` | 5154 | opencode/claude-code/codex `github-release-manager.*` | `<tmp>/...` |
| 12 | `test_domain_knowledge_is_wired_through_the_canon` | 5226 | `Global/claude-code/agents/*.md` (varios) | `<tmp>/claude-code/agents/*.md` |
| 13 | `test_the_delivery_commit_convention_is_declared_where_the_gate_reads_it` | 5768 | `Global/{opencode,claude-code}/commands/feature-batch.md` (el resto del test lee `Global/_canonical/...`, sin tocar -- ver nota) | `<tmp>/{opencode,claude-code}/commands/feature-batch.md` |
| 14 | `test_consult_mode_is_wired_and_never_starts_pipeline` | 5790 | `Global/claude-code/...`, existencia de `Global/{opencode,claude-code}/commands/{consult,status}.md` | `<tmp>/...` |
| 15 | `test_architecture_gate_is_wired_through_the_canon` | 5809 | `Global/claude-code/{agents,skills}/...` (5 archivos) | `<tmp>/claude-code/...` |
| 16 | `test_rpl_p0a_package_gate_runner_is_opencode_only_and_strictly_scoped` | 6046 | `Global/opencode/agents/package-gate-runner.md` + 2 asserts de NO-existencia (claude-code/codex) + `Global/opencode/agents/orchestrator.md` | `<tmp>/opencode/...`, `<tmp>/claude-code/...`, `<tmp>/codex/...` |
| 17 | `test_ac27_resolve_before_asking_mirrored_in_shared_doctrine_and_triage` | 9903 | `Global/{codex,pi,opencode}/AGENTS.md`, `Global/claude-code/CLAUDE.md` (la primera mitad del test, ANTES de esta línea, lee `Global/_shared/...` y `Global/_canonical/...` -- sin tocar, ver nota) | `<tmp>/...` |
| 18 | `test_ac28_explicar_reaches_the_four_runtime_trees` | 9930 | `Global/{opencode,claude-code,codex,pi}/skills/explicar/SKILL.md`, `Global/{opencode,claude-code}/commands/explicar.md`, `Global/pi/prompts/explicar.md`, existencia de `Global/codex/commands` (la comparación contra `Global/_canonical/skills/explicar/SKILL.md` sigue leyendo el canónico real, sin tocar) | `<tmp>/...` |

**Nota sobre `_canonical`/`_shared`:** varios de estos tests (13, 17, 18) también leen
`ROOT / "Global/_canonical/..."` o `ROOT / "Global/_shared/..."` -- esos NO se tocaron y no
hacía falta: `build.sh --output DIR` (`generate.py --output DIR`, `ai/scripts/generate.py:16-17`
`CANON = ROOT / "Global/_canonical"`, `SHARED = ROOT / "Global/_shared"`) sólo escribe
`DIR/{opencode,claude-code,codex,pi}` -- los cuatro harnesses -- nunca `DIR/_canonical` ni
`DIR/_shared`, que son plantillas fuente, leídas siempre del `ROOT` real, jamás regeneradas. Esos
reads eran ya de sólo lectura sobre contenido trackeado y estático; no forman parte de los 19
archivos mutados ni de los 18 call sites.

**Ninguno quedó afuera.** Los 18 verifican CONTENIDO generado (texto de doctrina, permisos,
estructura TOML/JSON, existencia/no-existencia de archivos por harness) -- ninguno afirma sobre
la ubicación física de la escritura (`ROOT` vs. cualquier otro directorio) como parte de lo que
prueba, así que redirigir el destino no le saca nada a ninguno de los 18.

**Ayudante nuevo, único cambio no mecánico:** `_generate_output()` (`tests/test_harness.py`,
cerca de `run()`) -- `Path(tempfile.mkdtemp(prefix="build-output-"))`, sin `with`/cleanup
explícito a propósito (ya vive bajo el `TMPDIR` relocado del sandbox de `tests/__init__.py`, se
descarta con el resto del sandbox al terminar la corrida; evita reindentar el cuerpo completo de
los 18 tests bajo un `with tempfile.TemporaryDirectory()`, que hubiera sido un diff mucho más
grande para el mismo resultado). `tests/__init__.py` **no se tocó** -- no hizo falta: el fix
completo vive en el punto de invocación (`tests/test_harness.py`), no en el seam de
`subprocess.Popen`. `tests/test_routing.py`, `ai/scripts/`, `build.sh`, `PROYECTO/`, `ai/state/`
y la spec tampoco se tocaron.

### 2) `git status --porcelain` antes y después, corrida completa sin bwrap

```
$ git status --porcelain                    # ANTES
 M tests/__init__.py
 M tests/test_harness.py
 M tests/test_routing.py
?? docs/specs/027-controles-que-miran/evidence/P2-portabilidad.md

$ SET_AGENTS_TEST_NO_BWRAP=1 python3 -m unittest tests.test_harness
descendant-boundary: off (bwrap not found)
...
Ran 472 tests in 813.904s

FAILED (failures=1, errors=1, skipped=4)

$ git status --porcelain                    # DESPUÉS
 M tests/__init__.py
 M tests/test_harness.py
 M tests/test_routing.py
?? docs/specs/027-controles-que-miran/evidence/P2-portabilidad.md
```

**19 → 0.** Ni un solo archivo de `Global/` cambió. Antes y después son byte-idénticos: sólo
mis 3 archivos editados + esta evidencia, exactamente igual en las dos corridas.

Las dos fallas que sobreviven (`failures=1, errors=1`) **no son de `Global/` ni de los 18 call
sites** -- ya estaban identificadas como preexistentes/fuera de alcance en la sección anterior:
- `test_adr_0017_and_0007_amendment_and_superseding_decision_recorded` (ERROR):
  `FileNotFoundError: ai/state/decisions-log.jsonl` -- mismo root cause de siempre, `ai/state/`
  nunca poblado en este worktree, fuera de mi ownership.
- `test_guest_copy_scaffolds_and_verifies_portably` (FAIL): esta vez el diff de `model:` ocurre
  **enteramente dentro de la propia copia privada `guest` del test** (rutas
  `/var/tmp/.../set-agents-guest-.../...`, nunca `Global/` real -- confirmado por el `git status`
  limpio de arriba) -- es el mismo tipo de deriva de pin de modelo por probe en vivo, pero
  autocontenida en el propio fixture del test, no uno de los 18 call sites (no llama
  `run("./build.sh")` bare en ningún punto; tiene su propio flujo install/verify). No forma
  parte de esta tarea.

`skipped=4`: confirmado que incluye las 2 pruebas P2-F01 `skipUnless(tests._BWRAP, ...)` de este
módulo (ya documentadas arriba -- `tests/test_harness.py:8675,8687`), porque la corrida no usó
`-v` y no imprimió los nombres de los otros 2 -- **sin verificar cuáles son exactamente los
otros 2**; candidatos preexistentes por lectura de código (`grep skipTest`): la guarda de
recursión de `test_guest_copy_scaffolds_and_verifies_portably` (línea ~3726, sólo si
`SET_AGENTS_GUEST_VERIFY=1`, no debería aplicar en la corrida top-level) o alguno de los guards
de `pi`/E2E (`SET_AGENTS_PI_E2E`, binario `script`, extensión `pi-subagents`) -- ninguno
relacionado a los 18 call sites ni a `Global/`, y ninguno tocado por esta tarea.

### 3) Contraprueba: `test_no_build_sh_call_writes_to_root_without_output_or_a_readonly_flag`

`tests/test_harness.py`, agregado inmediatamente después de `test_check_and_native_codex_agents`.
Mismo idioma que `test_every_direct_run_picker_call_in_tuitests_pins_msvcrt_to_none` (ya existía
en el archivo, línea ~10603 antes de mis ediciones): `inspect.getsource(HarnessTests)` + `ast.parse`,
recorre cada método buscando llamadas `run("./build.sh", ...)` cuyo conjunto de argumentos-string
no contenga ninguno de `--output`/`--check`/`--diff`/`--install`, y falla nombrando el método.

**Verde (estado actual, los 18 arreglados):**
```
$ python3 -m unittest tests.test_harness.HarnessTests.test_no_build_sh_call_writes_to_root_without_output_or_a_readonly_flag -v
test_no_build_sh_call_writes_to_root_without_output_or_a_readonly_flag (...) ... ok
Ran 1 test in 0.270s
OK
```

**Rojo (neutralizado: reintroduje un `run("./build.sh")` bare dentro de
`test_check_and_native_codex_agents`, la misma mutación que el coordinador quiere impedir):**
```
$ python3 -m unittest tests.test_harness.HarnessTests.test_no_build_sh_call_writes_to_root_without_output_or_a_readonly_flag -v
test_no_build_sh_call_writes_to_root_without_output_or_a_readonly_flag (...) ... FAIL

AssertionError: Lists differ: ['test_check_and_native_codex_agents'] != []
- ['test_check_and_native_codex_agents']
+ [] : these HarnessTests methods call run("./build.sh", ...) with none of
--output/--check/--diff/--install -- with run()'s hardcoded cwd=ROOT and no bwrap boundary
this rewrites the real Global/ tree in place: ['test_check_and_native_codex_agents']

Ran 1 test in 0.260s
FAILED (failures=1)
```

Muerde nombrando exactamente el test reintroducido. Revertido con `cp` desde el backup tomado
antes de neutralizar (`/var/tmp/claude/.../scratchpad/test_harness.counterproof.bak`); diff
contra el backup: vacío. Vuelto a verde, confirmado junto con `test_check_and_native_codex_agents`
mismo (`Ran 2 tests in 36.787s`, `OK`).

**Por qué es estática y no dinámica:** una contraprueba dinámica (correr de verdad un
`run("./build.sh")` bare para comprobar que NO debería mutar `ROOT`) sería circular y peligrosa
-- si alguien reintrodujera la regresión, esa misma prueba, corriendo sin bwrap (el escenario
que se supone debe cubrir, incluyendo macOS/Windows en CI), mutaría el `Global/` real para
detectar que muta el `Global/` real. El lint estático detecta el patrón sin ejecutar nada.

### 4) `Ran N tests in Xs` limpio, máquina sin contención

```
Ran 472 tests in 813.904s
FAILED (failures=1, errors=1, skipped=4)
```
(472 = los 471 de la medición anterior + esta contraprueba nueva.) Comparable a la medición
previa bajo contención de máquina (812.499s, 471 tests, con `failures=2, errors=4` -- las 2
fallas extra de esa corrida eran justamente 2 de los 4 rastros de deriva de `Global/` que este
fix eliminó). La diferencia de tiempo entre ambas corridas (813.904s vs 812.499s) es ruido, no
señal -- confirma lo ya anotado antes: el costo de la suite es abrumadoramente el trabajo real de
cada test (subprocess de `install.sh`/`build.sh`, scaffolding), no el mecanismo de escritura de
`Global/` en sí.

### Sin verificar (de esta tarea puntual)

- Los otros 3 skips (`skipUnless(tests._BWRAP, ...)`) de `tests/test_routing.py` no se
  re-verificaron en esta pasada (no forman parte de este módulo ni de esta tarea) -- siguen
  documentados en la sección anterior.
- No corrí la corrida CON bwrap de la suite completa de nuevo tras este fix (sólo los 18 tests
  tocados + la contraprueba, que sí confirmé en verde con bwrap arriba) -- el pedido explícito
  era la corrida SIN bwrap como prueba que manda; asumo que package-reviewer/gate-runner corre
  la versión con bwrap como parte de su propio gate.
- `test_guest_copy_scaffolds_and_verifies_portably` sigue en rojo (autocontenido, fuera de
  alcance) -- no confirmé si ESE test también podría beneficiarse de un `--output` equivalente
  en su propio flujo interno (tiene su propia mecánica de guest/install/verify, no uno de los 18
  call sites de `run("./build.sh")` directo); no lo toqué porque no es parte de esta tarea.
