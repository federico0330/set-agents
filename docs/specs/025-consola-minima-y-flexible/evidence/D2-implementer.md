# D2-trabajo-visible — evidencia del implementer

Inicio: 2026-08-16T00:00:00-03:00

Estado: DONE

Nota de base: el worktree estaba 17 commits detrás de `main` (sin feature 025 en absoluto,
ni `tests/test_menu_ui.py`, ni el context pack); se hizo `git merge main --ff-only` antes de
tocar nada, sin conflictos, árbol limpio antes y después del merge (`688577e` es la punta
usada).

Nota fuera de alcance: `MENU_ITEMS` (`set_agents_app.py:3523`) todavía tiene emoji en la
punta actual de `main`, y `--help` sigue listando las 71 flags sin recorte, pese a que el
mensaje del commit `8091b0b` dice "Menu sin emoji con regla positiva isascii" y "28 de 68
flags ocultas". El diff real de `8091b0b` no toca `MENU_ITEMS` ni agrega `isascii` en
`ai/scripts/*.py` (verificado: `git show 8091b0b -- ai/scripts/set_agents_app.py | grep
isascii` → sin resultados). Discrepancia de D1 (mensaje de commit vs. diff real), no de D2;
no la toqué — está fuera de mi alcance explícito ("Menú, flags ocultas... (D1)").

## Tabla AC → cambio → prueba

| AC | Cambio | archivo:línea | Prueba |
|---|---|---|---|
| AC-04 (trabajo visible >~300ms) | `supports_progress(stream)`: TTY del stream + sin `NO_COLOR`/`TERM=dumb` | `ai/scripts/tui.py:558-568` | `tests/test_harness.py::TuiTests::test_supports_progress_needs_a_real_tty_on_that_stream_and_no_degrade_env` |
| AC-04 | `with_progress(message, fn, *, stream, final)`: spinner animado (modo vivo) o línea estática (degradado), nunca en `sys.stdout` | `ai/scripts/tui.py:575-630` | `test_with_progress_without_a_tty_writes_not_one_byte_to_stdout`, `test_with_progress_live_tty_animates_then_leaves_exactly_one_persistent_line` |
| AC-04 | `cmd_route_doctor` envuelve `route_doctor(...)` con `with_progress` sobre `sys.stderr` | `ai/scripts/set_agents_app.py:558-570` | `tests/test_menu_ui.py::RouteDoctorProgressTests::test_json_stdout_is_byte_identical_whether_or_not_the_spinner_animates` |
| AC-04 | `cmd_doctor_all` envuelve `probe_listed_and_usable(...)` con `with_progress` sobre `sys.stderr` | `ai/scripts/set_agents_app.py:930-945` | `tests/test_menu_ui.py::DoctorAllProgressTests::test_no_color_pipe_never_leaves_doctor_all_silent` |
| AC-05 (nunca único indicador) | línea final persistente escrita siempre al terminar `fn()`, en ambos modos | `ai/scripts/tui.py:629` | `test_with_progress_live_tty_animates_then_leaves_exactly_one_persistent_line`, `test_with_progress_no_color_in_a_pipe_degrades_but_still_reports` |
| AC-05 (nunca bloquea input) | hilo del spinner siempre unido (`join(timeout=1.0)`) antes de retornar | `ai/scripts/tui.py:624-627` | `test_with_progress_joins_the_spinner_thread_before_returning` |
| AC-05 / trampa (stdout intacto) | ningún byte de progreso toca `sys.stdout`; `--json` bit a bit igual con o sin spinner vivo | `ai/scripts/tui.py:602-607` | `test_with_progress_without_a_tty_writes_not_one_byte_to_stdout`, `RouteDoctorProgressTests::test_json_stdout_is_byte_identical_whether_or_not_the_spinner_animates`, manual con `script` (abajo) |

Nuevo ADR: `docs/adr/0053-progress-indicator-never-on-stdout.md`, indexado en
`docs/adr/README.md`.

## Latencias medidas (real, corridas en esta máquina)

| Operación | Comando exacto | `real` |
|---|---|---|
| `--help` | `time python3 ai/scripts/set_agents_app.py --help` | 0m0,137s |
| `--route-doctor --json` | `time timeout 30 python3 ai/scripts/set_agents_app.py --route-doctor --json` | 0m13,478s |
| `--doctor-all` | `time timeout 30 python3 ai/scripts/set_agents_app.py --doctor-all` | 0m10,516s |

`--help` queda bajo el umbral de ~300ms (consistente con los 147ms del context pack) y NO se
instrumenta. `--route-doctor` y `--doctor-all` superan el umbral por más de 30x y son los
únicos dos puntos de integración de este paquete — elegidos por ser los únicos con latencia
REAL medida, no por timeout declarado.

Las demás filas de la tabla del context pack (`probe_inventory(timeout=20.0)`,
`AUTH_STATE_TIMEOUT_SECONDS=15`, `--version` por CLI (`timeout=15`), `git fetch(timeout=6)`,
`git pull(timeout=180)`, `install.py --preview` (~565KB/96 archivos), liveness de providers)
siguen siendo timeouts DECLARADOS en el código, no medidos por mí en este paquete — quedan sin
instrumentar y sin verificar, ver sección final.

## Salidas TTY / pipe / NO_COLOR (pegado literal)

Las tres corridas son manuales contra el binario real (`ai/scripts/set_agents_app.py
--route-doctor --json`), usando `script` para dar un pty real a stderr cuando corresponde
(stdout redirigido a archivo aparte en esos dos casos, así stderr queda solo en la
"terminal" capturada).

### TTY real (stderr es un pty, sin NO_COLOR) — modo vivo

Comando: `script -qec "python3 ai/scripts/set_agents_app.py --route-doctor --json >
stdout.txt" stderr_typescript.txt`

stdout capturado (JSON puro, sin ni un byte de spinner):
```
{"command": "route-doctor", "data": {"cache": {"age_seconds": 33.72..., "key_current": true, "reason": "OK", "used": true}, "providers": [...]}, "ok": true, "reason_codes": [], "schema_version": 2, "warnings": []}
```

stderr (typescript, recortado — el patrón `|/-\` se repite con `\r` entre frames, terminando
en la línea persistente):
```
Script iniciado en 2026-08-16 17:44:42-03:00 [...]
| consultando routing…\r/ consultando routing…\r- consultando routing…\r\ consultando routing…\r ... (se repite ~140 veces) ...                        \rconsultando routing: listo
Script terminado en 2026-08-16 17:44:55-03:00 [CÓDIGO_SALIDA_ORDEN="0"]
```
(`cat -A` confirmó los `^M` = `\r` entre frames y ningún `\x1b` — el spinner es puro texto +
`\r`, sin secuencias ANSI de color, consistente con `_IDENTITY_STYLE`/sin `colorama`.)

### Pipe (`> archivo 2> archivo`, ambos streams no-TTY) — modo degradado

Comando: `python3 ai/scripts/set_agents_app.py --route-doctor --json > stdout.txt 2>
stderr.txt`

stderr completo (una sola línea estática + la línea final, sin `\r`, sin ANSI):
```
· consultando routing…
consultando routing: listo
```

stdout: JSON puro (1301 bytes), estructuralmente idéntico en forma al caso TTY (el contenido
difiere sólo en `cache.age_seconds`/`reason`, esperado — la caché de probes tiene TTL).

### `NO_COLOR=1` con stderr en un pty real (TTY presente, pero degradado igual)

Comando: `NO_COLOR=1 script -qec "python3 ai/scripts/set_agents_app.py --route-doctor --json
> stdout.txt" stderr_typescript.txt`

stderr (typescript completo):
```
Script iniciado en 2026-08-16 17:45:27-03:00 [...]
· consultando routing…
consultando routing: listo
Script terminado en 2026-08-16 17:45:41-03:00 [CÓDIGO_SALIDA_ORDEN="0"]
```
`cat -A` confirmó: sin `\r` intermedio (sólo el `^M` de fin de línea normal del pty), sin
`\x1b` — `NO_COLOR=1` fuerza degradado aunque el stream SEA un TTY real, exactamente el
tercer gate que `supports_progress` chequea por separado del TTY-ness.

stdout: JSON puro (1308 bytes), la operación sigue funcionando y reportando normalmente.

## Mordidas (rojo → revert → verde), pegado literal

Cuatro ciclos de neutralizar/rojo/revertir/verde, contra `ai/scripts/tui.py`.

### Mordida 1 — stdout intacto (nivel `tui.with_progress`)

Bug inyectado en `_write()`: `sys.stdout.write(text)` antes de `stream.write(text)`.

Rojo (`python3 -m unittest
tests.test_harness.TuiTests.test_with_progress_without_a_tty_writes_not_one_byte_to_stdout -v`):
```
FAIL: test_with_progress_without_a_tty_writes_not_one_byte_to_stdout
AssertionError: '· consultando…\nconsultando: listo\n' != ''
```
Revertido → `ok` (`Ran 1 test in 0.008s / OK`).

### Mordida 1b — stdout intacto (nivel comando, `--route-doctor --json`)

Mismo bug inyectado, corrido contra
`tests.test_menu_ui.RouteDoctorProgressTests.test_json_stdout_is_byte_identical_whether_or_not_the_spinner_animates`.

Rojo:
```
FAIL: test_json_stdout_is_byte_identical_whether_or_not_the_spinner_animates
AssertionError: '\r                       \rconsultando ro[192 chars]]}\n' != '· consultando routing…\nconsultando routi[189 chars]]}\n'
```
(el spinner del modo vivo terminó filtrándose al principio del stdout capturado, antes del
JSON — exactamente el defecto que D1/AC-03 prohíbe.) Revertido → `ok`.

### Mordida 2 — degradación real (`NO_COLOR`/`TERM=dumb`/pipe)

Bug inyectado: `live = True` fijo, ignorando `supports_progress(stream)`.

Rojo (`test_with_progress_no_color_in_a_pipe_degrades_but_still_reports`):
```
AssertionError: '\r' unexpectedly found in '\r               \rconsultando: listo (7)\n'
```
Revertido → `ok`.

### Mordida 3 — AC-05, nunca único indicador

Bug inyectado: se borró la línea `_write((final(result) if final is not None else
f"{message}: listo") + "\n")` final.

Rojo (dos tests caen a la vez, misma causa):
```
FAIL: test_with_progress_live_tty_animates_then_leaves_exactly_one_persistent_line
AssertionError: False is not true   # out.endswith("consultando: listo\n")

FAIL: test_with_progress_no_color_in_a_pipe_degrades_but_still_reports
AssertionError: 'consultando: listo (7)' not found in '· consultando…\n'
```
Revertido → ambos `ok` (`Ran 2 tests in 0.269s / OK`).

Después de las cuatro mordidas: `tests.test_harness.TuiTests` completo (67 tests, incluye el
lint AST que exige `msvcrt=None` pineado en cada llamada directa a `run_picker`) y
`tests.test_menu_ui` completo (15 tests) en verde, sin marcador `MORDIDA` restante en el diff
(`git diff ai/scripts/tui.py | grep MORDIDA` → vacío).

## Gates

- `python3 -m unittest tests.test_harness.TuiTests` → `Ran 67 tests / OK`.
- `python3 -m unittest tests.test_menu_ui` → `Ran 15 tests / OK`.
- `python3 -m unittest tests.test_routing -k route_doctor` → `Ran 9 tests / OK`.
- `python3 -m unittest tests.test_routing -k doctor_all` → `Ran 2 tests / OK`.
- `python3 -m unittest tests.test_routing` (completo, sólo lectura sobre este archivo, no
  editado) → `Ran 324 tests in ~57-62s`, 2 failures + 2 errors, **las cuatro pre-existentes,
  no causadas por este diff**: todas sobre `routing_migrate`/`ai/state/project.json`
  (`FileNotFoundError: .../ai/state/project.json`) — ese directorio no existe en absoluto en
  este worktree (`ls ai/state/` → "No existe el fichero o el directorio") y está fuera de mi
  `owned_paths` ("No toques... `ai/state/`"). Confirmado que mi diff sólo toca
  `ai/scripts/tui.py`, `ai/scripts/set_agents_app.py`, `tests/test_harness.py`,
  `tests/test_menu_ui.py` (`git diff --stat`); nada relacionado con `routing_migrate` o
  `ai/state/`.
- `./build.sh --check` → `SELF_SCAFFOLD_SYNC_OK`, `GLOBAL_TREE_SYNC_OK
  profile=go-zen harnesses=4`, `BUILD_CHECK_PASS`.
- No se corrió `./ai/scripts/verify.sh` ni la suite completa (`discover -s tests`) — el
  prompt de esta tarea lo prohíbe explícitamente ("Hay otro agente y un gate en la máquina").
- `git diff --check` → sin salida (sin conflictos de whitespace).

## Archivos tocados

- `ai/scripts/tui.py` — `supports_progress`, `with_progress`, `import threading`.
- `ai/scripts/set_agents_app.py` — `cmd_route_doctor`/`cmd_doctor_all` envueltos con
  `tui.with_progress`.
- `tests/test_harness.py` — 5 tests nuevos en `TuiTests` (sección "025/D2: progress").
- `tests/test_menu_ui.py` — `RouteDoctorProgressTests`, `DoctorAllProgressTests`,
  `_FakeStream` local.
- `docs/adr/0053-progress-indicator-never-on-stdout.md` (nuevo).
- `docs/adr/README.md` — fila 0053 indexada.

## Sin verificar (explícito)

- Las siete filas de timeouts DECLARADOS del context pack que no son `route_doctor`/
  `probe_listed_and_usable` (`AUTH_STATE_TIMEOUT_SECONDS`, `--version` por CLI, `git
  fetch`/`git pull`, `install.py --preview`, liveness de providers) no fueron medidas ni
  instrumentadas en este paquete. Quedan como candidatas para un paquete futuro que primero
  las mida.
- La línea estática pre-existente `print(dim("· chequeando updates…"))` (`set_agents_app.py`,
  dentro de `menu()`, antes de `launch_update_check()`) no fue tocada — sigue sin animación
  real. Fuera de mi diff por disciplina de "menor diff seguro"; candidata natural para el
  mismo tratamiento si un paquete futuro la prioriza.
- Los 4 failures/errors de `tests.test_routing` sobre `routing_migrate`/`ai/state/project.json`
  son pre-existentes en este worktree (ver Gates) — no investigados a fondo porque
  `ai/state/` está fuera de mi `owned_paths`; reportado para que el orquestador lo evalúe.
- La discrepancia D1 (mensaje de commit `8091b0b` vs. diff real: `MENU_ITEMS` sigue con emoji,
  `--help` sigue listando las 71 flags) no fue investigada más allá de lo anotado arriba — es
  territorio de D1, no de D2.
