# ADR-0053 — un indicador de trabajo que nunca pisa el canal máquina

- Estado: Accepted (2026-08-16). Feature 025-consola-minima-y-flexible, paquete D2
  (`D2-trabajo-visible`). AC-04, AC-05.

## Contexto

`ai/scripts/tui.py` (830 líneas antes de este paquete: picker, raw mode, alternate screen,
bracketed paste, viewport clamp) no tenía spinner, animación ni indicador de progreso —
medido con `grep -rniE "spinner|animat" ai/scripts/*.py` → 0 resultados. Lo único que hoy le
decía al usuario que algo estaba pasando era una línea estática impresa antes de la llamada
lenta (`print(dim("· chequeando updates…"))`, `set_agents_app.py:3544`), sin animación y sin
relación con la duración real de la operación.

Medido en esta máquina (no timeouts declarados — latencia real de punta a punta):

| Comando | Latencia real medida | Comando exacto |
|---|---|---|
| `--help` | 137 ms | `time python3 ai/scripts/set_agents_app.py --help` |
| `--route-doctor --json` | 13,478 s (`real`) | `time timeout 30 python3 ai/scripts/set_agents_app.py --route-doctor --json` |
| `--doctor-all` | 10,516 s (`real`) | `time timeout 30 python3 ai/scripts/set_agents_app.py --doctor-all` |

Ambos comandos lentos superan largamente el umbral de ~300 ms que dispara AC-04; `--help`
queda debajo y no se instrumenta.

### La trampa: stdout es el canal máquina

Tres consumidores reales de stdout que un spinner mal ubicado rompe:

1. `_routing_output` (`set_agents_app.py:498-509`) imprime el JSON de `--json` en stdout y el
   texto humano en stderr — cualquier byte de progreso en stdout corrompe el contrato de
   `--json` (D1, AC-03) byte a byte.
2. `check-drift.sh:45` parsea stdout de `install.py --preview` con
   `sed -n 's/^MANAGED_DIFF_FILES=//p'` — un `\r` ahí rompe el parseo.
3. Los spawns del propio harness fuerzan `CI=1 NO_COLOR=1 TERM=dumb`
   (`opencode_spawn.py:202`, `codex_spawn.py:222`, `set_agents_spawn.py:115`,
   `routing_core/catalog.py:557,757,1120,1161`): todo lo que el harness se invoca a sí mismo
   corre ya degradado.

Y una trampa fina adicional: `use_color()` (`set_agents_app.py:944`) pregunta por
`sys.stdout.isatty()`. Reusarla para un indicador que escribe a stderr es preguntarle al
stream equivocado — `set-agents --route-doctor --json > out.json` deja stdout pipeado y
stderr todavía como TTY real.

## Decisión

### 1. `tui.supports_progress(stream)` — predicado propio, por stream, con tres gates independientes

`ai/scripts/tui.py` (nueva sección "progress / spinner", después de `suspend_terminal()`):
reusa `_is_tty(stream)` (ya existente, degrada a `False` en vez de lanzar) y agrega dos
chequeos de entorno propios — `NO_COLOR` y `TERM=dumb` — sobre el stream que el llamador
efectivamente va a usar, nunca sobre `sys.stdout`. Los tres gates (TTY / `NO_COLOR` /
`TERM=dumb`) están probados por separado (`tests/test_harness.py::TuiTests
::test_supports_progress_needs_a_real_tty_on_that_stream_and_no_degrade_env`) — un test que
sólo prueba "sin TTY" no prueba `NO_COLOR`.

### 2. `tui.with_progress(message, fn, *, stream=None, final=None)` — nunca stdout, siempre informa

Ejecuta `fn()` mientras informa sobre `stream` (default `sys.stderr`, jamás `sys.stdout`):

- **Modo vivo** (`supports_progress(stream)` True): un hilo daemon redibuja un frame de
  spinner (`|/-\`) cada 0.1 s con `\r`, exclusivamente sobre `stream`.
- **Modo degradado** (sin TTY, `NO_COLOR`, `TERM=dumb`, o cualquier stream que no sepa
  responder `isatty()`): una única línea estática, sin `\r`, sin ANSI.
- **AC-05, nunca único indicador**: al terminar `fn()` (con éxito), se escribe SIEMPRE una
  línea persistente (`final(result)` o un fallback `"<message>: listo"`) — en ambos modos.
  Si `fn()` lanza, el hilo se detiene y la línea del spinner se limpia igual (en el `finally`)
  antes de propagar la excepción, pero no se escribe línea final para un resultado que no
  existe — el propio manejo de error del llamador es lo que informa en ese caso.
- **AC-05, nunca bloquea input**: el hilo del spinner siempre se une (`join(timeout=1.0)`)
  antes de que `with_progress` retorne, así que nada puede seguir escribiendo cuando el
  llamador encadena un `input()`/`tui.suspend_terminal()` inmediatamente después
  (`tests/test_harness.py::TuiTests::test_with_progress_joins_the_spinner_thread_before_returning`,
  que compara `threading.active_count()` antes/después).

### 3. Dos puntos de integración, elegidos por medición — no todos los timeouts declarados

`cmd_route_doctor` (`set_agents_app.py:558-568`) y `cmd_doctor_all`
(`set_agents_app.py:930-940`) envuelven su llamada lenta (`route_doctor`,
`probe_listed_and_usable`) con `tui.with_progress(..., stream=sys.stderr, ...)` — las dos
únicas operaciones con latencia real medida (arriba), no las siete filas de timeouts
*declarados en el código* que el context pack de D2 lista aparte y marca explícitamente "sin
verificar". Los demás sitios (`AUTH_STATE_TIMEOUT_SECONDS`, `--version` por CLI, `git
fetch`/`git pull` del update, `install.py --preview`, liveness de providers) quedan sin
instrumentar en este paquete — quedan en "sin verificar" en la evidencia, no asumidos.

`routing_core/`, `install.py` y los `*_spawn.py` no se tocaron (fuera de `owned_paths` de este
paquete): la instrumentación vive enteramente en el llamador (`set_agents_app.py`), nunca en
el código probeado.

### 4. `--json` no cambia ni un byte

`cmd_route_doctor(human=False)` sigue imprimiendo exactamente el mismo envelope JSON por
`_routing_output` — el spinner corrió antes, sobre `stream=sys.stderr`, y ya fue unido
(`join`) para cuando ese `print(json.dumps(...))` se ejecuta. Verificado con y sin animación
real (spinner vivo vs. degradado): stdout produce bytes idénticos en ambos casos
(`tests/test_menu_ui.py::RouteDoctorProgressTests
::test_json_stdout_is_byte_identical_whether_or_not_the_spinner_animates`), y manualmente con
`script` (pty real) contra `set-agents --route-doctor --json`, TTY / `| cat` (pipe) /
`NO_COLOR=1` — las tres salidas pegadas literales en
`docs/specs/025-consola-minima-y-flexible/evidence/D2-implementer.md`.

## Alternativas rechazadas

- **Reusar `use_color()` para gatear el spinner.** Rechazado — pregunta por
  `sys.stdout.isatty()`, el stream equivocado para algo que escribe a stderr; el context pack
  lo señala explícitamente como la "trampa fina".
- **`rich`/`tqdm`.** Rechazado — sin dependencias nuevas (restricción explícita del paquete);
  stdlib solamente (`threading`, ya usado en otras partes del repo).
- **Instrumentar los siete sitios con timeout declarado del context pack.** Rechazado para
  este paquete — son timeouts *en el código*, no latencias medidas; sólo se instrumentaron los
  dos comandos con latencia real confirmada (>10 s). Instrumentar sin medir habría sido
  exactamente la "medí antes de escribir" que el paquete pide evitar violar al revés.
- **Escribir la línea final también cuando `fn()` lanza una excepción.** Rechazado — no hay
  `result` que formatear (`final(result)` necesita un resultado real), y el manejo de error de
  cada `cmd_*` ya informa por su propio camino (`except` con su propio `_routing_output`/
  mensaje); duplicar el aviso ahí habría sido una segunda fuente de verdad para el mismo
  fallo.

## Consecuencias

- `tui.py` gana `supports_progress`/`with_progress`, stdlib puro, sin nuevo estado global
  persistente (el hilo es local a cada llamada).
- `--route-doctor` y `--doctor-all` informan de forma visible durante los ~10-14 s que tardan
  realmente, en TTY (animado), en pipe (línea estática) y con `NO_COLOR`/`TERM=dumb` (línea
  estática) — nunca en silencio, nunca corrompiendo `--json`.
- Cuatro mordidas rojo→revertido→verde demostradas para D2 (dos a nivel `tui.with_progress` en
  `tests/test_harness.py`, una que tumbó dos tests a la vez por la misma causa, y una a nivel
  comando en `tests/test_menu_ui.py` contra `--route-doctor --json`), documentadas con su
  salida literal en la evidencia del paquete.
- El resto de operaciones lentas con timeout *declarado* (no medido) del context pack de D2
  quedan explícitamente sin instrumentar y sin medir en este paquete — abierto para un futuro
  paquete que las mida primero.

## Evidencia

`docs/specs/025-consola-minima-y-flexible/evidence/D2-implementer.md` — tabla AC → cambio
(`archivo:línea`) → prueba; la tabla de latencias reales medidas (comando y número); las tres
salidas TTY/pipe/`NO_COLOR` pegadas literales (vía `script`, pty real); las mordidas con su
rojo demostrado y revertido.
