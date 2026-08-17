# D2-trabajo-visible — verificación adversarial de hallazgos

Árbol verificado: `211df01`. Alcance read-only: D2-F01 y D2-F02 contra AC-04/AC-05.

## Veredicto

| ID | Veredicto | Evidencia |
|---|---|---|
| D2-F01 | `upheld` | `with_progress` sólo tiene dos llamadores (`set_agents_app.py:604,981`). `cmd_status(human=True)` y “Estado general” recorren operaciones externas sin el indicador (`set_agents_app.py:1326-1345,1371-1378,3681-3684,3771-3774`). Ambas demoras controladas reprodujeron silencio o ausencia de progreso/final persistente por encima de ~300 ms. |
| D2-F02 | `upheld` | `thread.join(timeout=1.0)` retorna sin comprobar `thread.is_alive()` (`tui.py:621-630`). Con un write del spinner bloqueado más de un segundo, `with_progress` retornó con el hilo vivo y ese hilo escribió después de la línea final. |

```json
{
  "package_id": "D2-trabajo-visible",
  "verdicts": [
    {
      "id": "D2-F01",
      "verdict": "upheld",
      "reason": "Las dos rutas humanas citadas son alcanzables y las reproducciones confirmaron esperas superiores a 300 ms sin progreso conforme a AC-04."
    },
    {
      "id": "D2-F02",
      "verdict": "upheld",
      "reason": "La reproducción confirmó que el join acotado puede devolver el control con el escritor de animación todavía vivo y capaz de escribir después del estado final."
    }
  ],
  "observations": []
}
```

## D2-F01 — upheld

No se pudo refutar:

- El contrato aprobado exige progreso para **todo** lo que tarde más de ~300 ms
  (`spec.md:48-52`); no sanciona una allowlist de operaciones medidas una vez.
- En el árbol exacto, `with_progress` sólo se llama desde `cmd_route_doctor` y
  `cmd_doctor_all` (`ai/scripts/set_agents_app.py:604,981`; confirmado con
  `rg -n "with_progress" tests ai/scripts`).
- `cmd_status(human=True)` ejecuta `version_of` y `auth_state` para cada CLI antes de su
  primer `print` (`ai/scripts/set_agents_app.py:1326-1345,1371-1378`).
- El primer ítem del menú imprime sólo el inicio estático y después ejecuta tanto
  `_status_data(rows=True)` como `probe_listed_and_usable` sin `with_progress`
  (`ai/scripts/set_agents_app.py:3681-3684,3771-3774`).
- Los restantes límites externos citados por el finding tampoco están envueltos: fetch/pull
  e instalación (`ai/scripts/set_agents_app.py:1397,1415,1446-1447,1452,1466`) y liveness
  (`ai/scripts/set_agents_app.py:2752`). Esto es evidencia de lectura; la reproducción focal
  suficiente para sostener el finding fue `--status`/menú.

Reproducción 1, demora controlada de 350 ms en cada `version_of`, sobre el flujo real
`cmd_status(human=True)` (el mock reemplaza sólo dependencias y captura stdout):

```text
$ python3 -c 'import io,sys,time; from unittest import mock; sys.path.insert(0,"ai/scripts"); import set_agents_app as app; out=io.StringIO(); seen=[]; slow=lambda _cli:(seen.append((out.getvalue()=="",time.monotonic())),time.sleep(0.35),seen.append((out.getvalue()=="",time.monotonic())),"1.0")[-1]; patches=(mock.patch.object(app,"short_sha",return_value="abc"),mock.patch.object(app,"drift_state",return_value="ok"),mock.patch.object(app,"rev_count",return_value=0),mock.patch.object(app,"auto_update_enabled",return_value=True),mock.patch.object(app.shutil,"which",return_value="/bin/fake"),mock.patch.object(app,"version_of",side_effect=slow),mock.patch.object(app,"auth_state",return_value="ok"),mock.patch.object(sys,"stdout",out)); [p.start() for p in patches]; start=time.monotonic(); rc=app.cmd_status(human=True); elapsed=time.monotonic()-start; [p.stop() for p in reversed(patches)]; print("STATUS_HUMAN elapsed=%.3fs rc=%d silent_all_slow_checks=%s first_output=%r"%(elapsed,rc,all(flag for flag,_ in seen),out.getvalue().splitlines()[0]))'
STATUS_HUMAN elapsed=1.051s rc=0 silent_all_slow_checks=True first_output='APP_STATUS sha=abc drift=ok update=0 auto_update=on'
```

Reproducción 2, flujo real `menu()` seleccionando “Estado general”; se demoró únicamente
`probe_listed_and_usable` 350 ms y se aislaron las demás dependencias para no escribir estado:

```text
$ python3 -c 'import io,sys,time; from unittest import mock; sys.path.insert(0,"ai/scripts"); import set_agents_app as app; import routing_core.catalog as catalog; out=io.StringIO(); slow=lambda *a,**k:(time.sleep(0.35),({},{}))[1]; data={"rows":[],"drift":"ok","sha":"abc","behind":0,"auto_update":True}; patches=(mock.patch.object(app,"first_run",return_value=False),mock.patch.object(app,"banner"),mock.patch.object(app,"launch_update_check",return_value="al día"),mock.patch.object(app,"drift_state",return_value="ok"),mock.patch.object(app,"short_sha",return_value="abc"),mock.patch.object(app,"auto_update_enabled",return_value=True),mock.patch.object(app,"_status_data",return_value=data),mock.patch.object(app,"_pi_lane_state",return_value="no"),mock.patch.object(app,"_install_scope",return_value=None),mock.patch.object(app,"_tools_data",return_value=[]),mock.patch.object(app.models_config,"load_config",return_value={}),mock.patch.object(catalog,"prune_legacy_probe_cache",return_value=False),mock.patch.object(catalog,"probe_listed_and_usable",side_effect=slow),mock.patch.object(app.tui,"run_picker",side_effect=[app.tui.Selected(0),None,None]),mock.patch.object(sys,"stdout",out)); [p.start() for p in patches]; start=time.monotonic(); rc=app.menu(); elapsed=time.monotonic()-start; [p.stop() for p in reversed(patches)]; text=out.getvalue(); print("MENU_ESTADO elapsed=%.3fs rc=%d cr=%d ansi=%d start_status=%s final_status=%s"%(elapsed,rc,text.count("\r"),text.count("\x1b"),"· relevando estado…" in text,"relevando estado: listo" in text))'
MENU_ESTADO elapsed=0.351s rc=0 cr=0 ansi=0 start_status=True final_status=False
```

Resultado: el camino reproduce. La línea estática de inicio no es el spinner/progreso exigido
por AC-04 y tampoco existe una línea final persistente, exigida por AC-05.

## D2-F02 — upheld

No se pudo refutar:

- El docstring promete que nada puede seguir escribiendo al retorno
  (`ai/scripts/tui.py:593-596`), pero la implementación sólo hace
  `thread.join(timeout=1.0)` y continúa sin verificar terminación
  (`ai/scripts/tui.py:621-630`). El camino es alcanzable: `_write` ejecuta
  `stream.write`/`flush` dentro del hilo y no puede cancelar una llamada ya bloqueada
  (`ai/scripts/tui.py:602-617`).
- La prueba existente usa `_FakeStdout`/`StringIO` no bloqueante y sólo compara el conteo
  global de hilos (`tests/test_harness.py:12774-12783`). Ejecutada literalmente, pasa, pero
  no recorre el timeout:

```text
$ python3 -m unittest tests.test_harness.TuiTests.test_with_progress_joins_the_spinner_thread_before_returning -v
test_with_progress_joins_the_spinner_thread_before_returning (tests.test_harness.TuiTests.test_with_progress_joins_the_spinner_thread_before_returning) ... ok
Ran 1 test in 0.155s
OK
```

Reproducción con un stream TTY cuyo `write` del hilo de spinner queda bloqueado más de un
segundo:

```bash
$ env -u NO_COLOR TERM=xterm python3 -c '
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
JOIN_TIMEOUT elapsed=1.101s result=ok spinner_alive_after_return=True final_before_release=True
JOIN_TIMEOUT late_frame_after_final=True
```

Resultado: `with_progress` retornó mientras el escritor seguía vivo; al liberarlo, escribió
después de la línea final. Esto contradice AC-05 (`spec.md:52`) y confirma exactamente el
riesgo de pisar un prompt inmediato.

## Destilado (dominio: architecture)

- Un umbral de UX expresado como “todo lo que tarde más de ~300 ms” es dinámico por ejecución; una allowlist histórica de dos llamadores no satisface el contrato.
- Un `join(timeout=...)` no establece ownership exclusivo del stream al retorno: hay que comprobar la terminación real del escritor antes del handoff al input.
- Una prueba con `StringIO` no bloqueante no cubre backpressure ni demuestra que un hilo de render no pueda escribir tarde.
