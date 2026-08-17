# D2 gates/runtime QA — AC-04/AC-05

Fecha: 2026-08-16. Árbol integrado verificado: `211df01`.

## VERDICT

PASS para AC-04/AC-05 en el diff integrado de D2. Los dos tasks de state pueden marcarse
`completed`: indicador visible durante operaciones largas, degradación estática sin TTY/pipe o
`NO_COLOR`, stdout JSON preservado y línea final persistente sin bloqueo de input.

## TASK_VALIDATIONS

- `ai/scripts/tui.py:558-630`: `supports_progress` exige TTY y rechaza `NO_COLOR`/`TERM=dumb`;
  `with_progress` anima sólo en modo vivo, escribe progreso en el stream recibido y siempre deja
  una línea final.
- `ai/scripts/set_agents_app.py:558-570` y `:930-945`: `--route-doctor` y `--doctor-all`
  envuelven el trabajo medible con `with_progress` sobre stderr.
- `tests/test_harness.py::TuiTests`: tests de TTY/no-TTY, NO_COLOR, stdout intacto, línea final
  y join del hilo.
- `tests/test_menu_ui.py`: stdout JSON byte-stable y doctor-all no silencioso en degradación.

## GATES

| Comando | Exit | Observación |
|---|---:|---|
| `python3 ai/scripts/heartbeat-run.py --interval 20 -- python3 -m unittest tests.test_harness.TuiTests` | 0 | 67 tests, OK |
| `python3 ai/scripts/heartbeat-run.py --interval 20 -- python3 -m unittest tests.test_menu_ui` | 0 | 15 tests, OK |
| `python3 ai/scripts/heartbeat-run.py --interval 20 -- python3 -m unittest tests.test_routing -k route_doctor` | 0 | 9 tests, OK |

Gates concretos a registrar: los tres comandos anteriores y la QA runtime de abajo; no se
recomienda usar la suite completa como gate D2 porque la evidencia del implementer documenta
fallos preexistentes de `routing_migrate` por `ai/state/project.json` ausente.

## RUNTIME_QA

Comando (exit 0):
`python3 ai/scripts/heartbeat-run.py --interval 20 -- bash -c 'python3 ai/scripts/set_agents_app.py --route-doctor --json >/tmp/d2-inner.stdout 2>/tmp/d2-inner.stderr; ...'`.

- Separación real de streams: `/tmp/d2-inner.stdout` = 1306 bytes y comienza con JSON
  (`{"command": "route-doctor"...`); `/tmp/d2-inner.stderr` = 53 bytes:
  `· consultando routing…` y `consultando routing: listo`. No hay progreso en stdout.
- El wrapper heartbeat reemite stderr del proceso hijo en su propia salida; por eso la medición
  de stdout se hizo dentro del shell hijo, directamente sobre los archivos redirigidos.
- Pipe y `NO_COLOR=1` se ejecutaron con heartbeat, exit 0; la degradación observada es texto
  estático (sin `\r`/ANSI) y conserva JSON. En el caso `NO_COLOR`, `/tmp/d2-nocolor.stdout`
  fue 1353 bytes por la reemisión del heartbeat; la separación interna confirma el contrato.

## STATE_ACTIONS

Marcar ambos tasks de D2 (`trabajo visible` y `runtime QA/gates`) como `completed`, sujeto a que
el coordinador registre los gates y esta evidencia. No cambiar state JSON desde este agente.

## FILES_CHANGED

- `docs/specs/025-consola-minima-y-flexible/evidence/D2-gates-runtime-qa.md` (esta evidencia).
- Sin cambios de código, tests, configuración ni state.

