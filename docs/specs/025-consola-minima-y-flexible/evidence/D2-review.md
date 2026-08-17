# D2-trabajo-visible — revisión independiente

Commit integrado revisado: `211df01` (el cambio D2 ingresó en su ancestro `bec3dcf`).

Alcance: AC-04/AC-05, diff D2, evidencia del implementer y gates/runtime QA. Revisión
read-only del producto; este archivo es la única escritura autorizada.

VERDICT: repair_required

## Findings

### D2-F01 — AC-04 cubre dos comandos pero deja otras esperas humanas sin progreso

- `id`: D2-F01
- `severity`: high
- `category`: correctness
- `acceptance_criterion`: AC-04
- `file`: `ai/scripts/set_agents_app.py`
- `line`: 981, 1326-1345, 1371-1373, 3681-3684, 3771-3773
- `evidence`: D2 agregó `with_progress` sólo alrededor de `cmd_doctor_all` (981-984; el
  otro sitio está en `cmd_route_doctor`, 604-608). Sin embargo, `--status` humano ejecuta
  hasta seis subprocess probes antes de su primer `print` (1326-1345, 1371-1373), y el
  primer ítem del menú vuelve a ejecutar `probe_listed_and_usable` sin `with_progress`
  (3681-3684). En ese menú sólo queda la línea estática `· relevando estado…` (3771), sin
  animación/progreso ni estado final. La propia evidencia del implementer deja explícitamente
  sin medir ni instrumentar `AUTH_STATE_TIMEOUT_SECONDS`, `--version`, fetch/pull, preview y
  liveness, aunque AC-04 dice "todo lo que tarde más de ~300 ms".
- `reproduction`: (1) con `probe_listed_and_usable` demorado 350 ms, el flujo real de menú
  tardó 0.351 s, produjo `cr=0`, mostró sólo `start_status=True` y nunca una terminación
  (`final_status=False`); (2) con cada `version_of` demorado 350 ms, `cmd_status(human=True)`
  tardó 1.052 s y `silent_all_slow_checks=True`: no escribió un byte durante ninguno de los
  tres waits. Comandos y salidas literales en “Comandos independientes”.
- `required_outcome`: toda operación humana que supere ~300 ms debe activar progreso sobre
  stderr después del umbral y terminar con estado persistente; stdout máquina debe permanecer
  intacto. Como mínimo deben cubrirse `--status` humano, el probe de `Estado general`,
  fetch/pull/instalación y los restantes puntos enumerados por el context pack, midiéndolos o
  usando activación demorada para que una llamada normalmente rápida también informe si se
  enlentece.
- `suggested_scope`: `ai/scripts/tui.py`, llamadores humanos de `ai/scripts/set_agents_app.py`
  y tests de regresión focales en `tests/test_harness.py`/`tests/test_menu_ui.py`.
- `reparación propuesta`: convertir `with_progress` en un indicador de activación demorada
  (~300 ms) y aplicarlo en el límite común de las operaciones externas, no en una allowlist de
  dos comandos medida una sola vez. Agregar pruebas de demora controlada para `--status`,
  `Estado general`, update/install/preview y liveness.

### D2-F02 — el timeout de `join` permite que el spinner sobreviva al retorno y pise el input

- `id`: D2-F02
- `severity`: medium
- `category`: correctness
- `acceptance_criterion`: AC-05
- `file`: `ai/scripts/tui.py`
- `line`: 593-596, 621-630
- `evidence`: el docstring afirma que nada puede seguir escribiendo al retornar, pero el código
  hace `thread.join(timeout=1.0)` (626) y no comprueba `thread.is_alive()` antes de limpiar,
  escribir la línea final y retornar (627-630). Si el write/flush del stream se demora más de
  un segundo, el hilo daemon sigue vivo; al destrabarse escribe un frame después de la línea
  final y puede competir con el prompt inmediato. La prueba existente
  `tests/test_harness.py:12774-12783` sólo usa un `StringIO` no bloqueante y cuenta todos los
  threads globales, por lo que nunca recorre el timeout que contradice el invariante. La
  evidencia del implementer y el ADR-0053 sobreafirman “siempre unido” basándose en esa prueba.
- `reproduction`: un stream TTY controlado bloqueó sólo el write del hilo de spinner durante
  más de 1 s. `with_progress` retornó en 1.101 s con `spinner_alive_after_return=True`; tras
  liberar el write, `late_frame_after_final=True`. Comando y salida literal abajo.
- `required_outcome`: `with_progress` no puede retornar mientras exista un escritor de
  animación capaz de tocar el stream; tampoco puede resolverlo con un join sin límite que
  congele el input. Debe haber ownership/cancelación comprobable del escritor y una prueba que
  fuerce backpressure más allá del timeout.
- `suggested_scope`: `ai/scripts/tui.py` y los tests D2 de `tests/test_harness.py`.
- `reparación propuesta`: rediseñar el handoff para que el hilo de progreso tenga terminación
  garantizada antes del retorno (por ejemplo, trabajo en worker y render/cancelación controlada
  por el caller, con un canal de resultado), y agregar un fake stream cuyo write se bloquee para
  demostrar que ningún frame puede aparecer después de la línea final/prompt.

## Comandos independientes

- `python3 ai/scripts/heartbeat-run.py --interval 20 -- python3 -m unittest
  tests.test_harness.TuiTests tests.test_menu_ui.RouteDoctorProgressTests
  tests.test_menu_ui.DoctorAllProgressTests -v` → exit 0, `Ran 70 tests in 0.603s`, `OK`.
- TTY real, estado aislado en `/tmp`:
  `python3 ai/scripts/heartbeat-run.py --interval 20 -- script -qec 'env -u NO_COLOR
  SET_AGENTS_STATE=/tmp/d2-review-state
  SET_AGENTS_ROUTING_TEST_ROOT=/tmp/d2-review-routing TERM=xterm python3
  ai/scripts/set_agents_app.py --route-doctor --json > /tmp/d2-review-tty.stdout'
  /tmp/d2-review-tty.typescript` → exit 0; stdout 1261 bytes, JSON válido, 0 `\r`,
  0 ANSI; stderr TTY 125 `\r`, 0 ANSI y línea final presente.
- Pipe real, mismo estado aislado: `... set_agents_app.py --route-doctor --json >
  /tmp/d2-review-pipe.stdout 2> /tmp/d2-review-pipe.stderr` → exit 0; stdout 1261 bytes,
  JSON válido, 0 `\r`/ANSI; stderr exacto `· consultando routing…\nconsultando routing:
  listo\n`, 0 `\r`/ANSI.
- `NO_COLOR=1` con stderr TTY real: mismo comando bajo `script`, stdout redirigido → exit
  0; JSON válido, 0 bytes de progreso en stdout, 0 ANSI y 0 frames animados en stderr;
  línea final presente.
- Reproducción D2-F01 (mock sólo de la demora externa, flujo `menu()` real):
  `python3 -c '<patch de probe_listed_and_usable con sleep(0.35); app.menu()>'` →
  `MENU_ESTADO elapsed=0.351s rc=0 cr=0 ansi=0 start_status=True final_status=False`.
- Segunda reproducción D2-F01 (flujo `cmd_status(human=True)` real, sólo `version_of`
  demorado): `python3 -c '<version_of con sleep(0.35); app.cmd_status(human=True)>'` →
  `STATUS_HUMAN elapsed=1.052s rc=0 silent_all_slow_checks=True
  first_output='APP_STATUS sha=abc drift=ok update=0 auto_update=on'`.
- Reproducción D2-F02: `env -u NO_COLOR TERM=xterm python3 -c '<BlockingSpinnerStream;
  tui.with_progress(...)>'` → `JOIN_TIMEOUT elapsed=1.101s result=ok
  spinner_alive_after_return=True final_before_release=True`; después de liberar el writer:
  `JOIN_TIMEOUT late_frame_after_final=True`.
- `cmp -s /tmp/d2-review-tty.stdout /tmp/d2-review-pipe.stdout` y contra
  `/tmp/d2-review-nocolor.stdout` → ambos exit 0: stdout fue byte-idéntico entre TTY, pipe y
  `NO_COLOR=1`.
- `env -u NO_COLOR TERM=dumb python3 -c '<TTY StringIO; tui.with_progress(...)>'` →
  `TERM_DUMB cr=0 ansi=0 text='· x…\nx: listo\n'`.
- `git diff --check bec3dcf^ bec3dcf -- <archivos D2>` → exit 0.

### Reproducciones exactas de findings

D2-F01 (`cmd_status(human=True)` no emite nada durante tres esperas de 350 ms):

```bash
python3 -c 'import io,sys,time; from unittest import mock; sys.path.insert(0,"ai/scripts"); import set_agents_app as app; out=io.StringIO(); seen=[]; slow=lambda _cli:(seen.append((out.getvalue()=="",time.monotonic())),time.sleep(0.35),seen.append((out.getvalue()=="",time.monotonic())),"1.0")[-1]; patches=(mock.patch.object(app,"short_sha",return_value="abc"),mock.patch.object(app,"drift_state",return_value="ok"),mock.patch.object(app,"rev_count",return_value=0),mock.patch.object(app,"auto_update_enabled",return_value=True),mock.patch.object(app.shutil,"which",return_value="/bin/fake"),mock.patch.object(app,"version_of",side_effect=slow),mock.patch.object(app,"auth_state",return_value="ok"),mock.patch.object(sys,"stdout",out)); [p.start() for p in patches]; start=time.monotonic(); rc=app.cmd_status(human=True); elapsed=time.monotonic()-start; [p.stop() for p in reversed(patches)]; print("STATUS_HUMAN elapsed=%.3fs rc=%d silent_all_slow_checks=%s first_output=%r"%(elapsed,rc,all(flag for flag,_ in seen),out.getvalue().splitlines()[0]))'
```

Resultado: `STATUS_HUMAN elapsed=1.052s rc=0 silent_all_slow_checks=True
first_output='APP_STATUS sha=abc drift=ok update=0 auto_update=on'`.

D2-F02 (backpressure del writer supera el `join(timeout=1.0)`):

```bash
env -u NO_COLOR TERM=xterm python3 -c '
import io, sys, threading, time
sys.path.insert(0, "ai/scripts")
import tui
class BlockingSpinnerStream(io.StringIO):
    def __init__(self):
        super().__init__(); self.entered=threading.Event(); self.release=threading.Event()
    def isatty(self): return True
    def write(self, text):
        if threading.current_thread() is not threading.main_thread() and "consultando" in text:
            self.entered.set(); self.release.wait(5)
        return super().write(text)
stream=BlockingSpinnerStream(); before=set(threading.enumerate()); start=time.monotonic()
result=tui.with_progress("consultando", lambda: (stream.entered.wait(1), "ok")[1], stream=stream)
elapsed=time.monotonic()-start
survivors=[t for t in threading.enumerate() if t not in before and t.is_alive()]
returned_text=stream.getvalue()
print("JOIN_TIMEOUT elapsed=%.3fs result=%s spinner_alive_after_return=%s final_before_release=%s" % (elapsed,result,bool(survivors),returned_text.endswith("consultando: listo\n")))
stream.release.set()
for t in survivors: t.join(1)
print("JOIN_TIMEOUT late_frame_after_final=%s" % (not stream.getvalue().endswith("consultando: listo\n")))
'
```

Resultado: `JOIN_TIMEOUT elapsed=1.101s result=ok spinner_alive_after_return=True
final_before_release=True`; luego `JOIN_TIMEOUT late_frame_after_final=True`.

## Destilado (dominio: data / algorithms)

- Un umbral de latencia es una propiedad dinámica de cada ejecución: elegir sólo los sitios
  históricamente lentos deja ciegas las mismas llamadas cuando una dependencia normalmente
  rápida se demora.
- Un `join(timeout=...)` no prueba terminación: si el writer sigue vivo, puede alterar el stream
  después del handoff al prompt.
