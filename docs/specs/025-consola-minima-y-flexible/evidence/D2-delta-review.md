# D2-trabajo-visible — delta review de reparación

Package: `D2-trabajo-visible`
Delta revisado: `489ecff` contra `489ecff^`
Alcance: cierre de `D2-F01`/`D2-F02`, regresiones relacionadas y pruebas del delta.

VERDICT: `repair_required`.

## Insumos leídos

- Context pack: `docs/specs/025-consola-minima-y-flexible/context/D2-trabajo-visible.md`.
- Hallazgos previos: `evidence/D2-review.md`.
- Verificación adversarial: `evidence/D2-verification.md`.
- Reparación: `evidence/D2-repair.md`.
- Contrato: `spec.md`, AC-04/AC-05.

## Evidencia preliminar del delta

- `ai/scripts/tui.py:577-641`: activación demorada a 300 ms; el caller es el único escritor
  directo y el trabajo corre en un worker no-daemon que se une antes del retorno normal.
- `ai/scripts/set_agents_app.py:1371-1454,3612-3620,3750-3782`: nuevos wrappers para status,
  update/fetch/pull/install, menú inicial y Estado general.
- `tests/test_harness.py:2474-2493,12806-12837` y `tests/test_menu_ui.py:109-120`: regresiones
  focales para demora controlada y backpressure.

## Cierre de hallazgos previos

### D2-F01 — `reopened`

El delta agregó activación demorada y cubrió `--status`, Estado general, update/fetch/pull e
instaladores, pero no cerró el requisito comprobado de cubrir las demás esperas enumeradas por el
context pack. En particular, `cmd_provider_verify` sigue ejecutando `_provider_liveness` directamente
(`ai/scripts/set_agents_app.py:2755-2765`), con timeout declarado de 2 s
(`ai/scripts/set_agents_app.py:2676,2689-2713`) y sin `with_progress` en el comando ni en su dispatch.
La reproducción con una demora controlada de 350 ms confirmó silencio completo hasta terminar.

### D2-F02 — `closed`

`ai/scripts/tui.py:608-640` ya no deja un hilo de animación dueño del stream: el worker ejecuta
solamente `fn`, el caller escribe los frames, une el worker y recién después escribe la línea final.
La prueba de backpressure en `tests/test_harness.py:12806-12837` fuerza 1,1 s —más que el timeout
anterior— y la salida permanece estable después del estado final. La suite focal correspondiente
pasó. Esto cierra el defecto específico de frames tardíos, aunque el nuevo uso sobre procesos
interactivos introduce la regresión separada D2-DR01.

## New or reopened findings

### D2-F01 — una espera de liveness enumerada sigue silenciosa

- `id`: D2-F01
- `severity`: high
- `category`: correctness
- `acceptance_criterion`: AC-04
- `file`: `ai/scripts/set_agents_app.py`
- `line`: 2676, 2689-2713, 2755-2765
- `evidence`: `_provider_liveness` declara timeout de 2 s y `cmd_provider_verify` lo llama
  directamente, sin el wrapper demorado agregado por el repair. Con un liveness de 350 ms, stdout y
  stderr permanecieron vacíos durante toda la espera.
- `reproduction`: el comando Python registrado abajo terminó exit 0 con
  `elapsed=0.351s`, `silent_during_wait=True`, `stderr=''`; la única línea de stdout apareció al final.
- `required_outcome`: toda espera humana que cruce ~300 ms, incluida esta liveness ya enumerada en el
  context pack y en el finding upheld, activa progreso en stderr y deja estado persistente sin cambiar
  stdout.
- `suggested_scope`: límite de `cmd_provider_verify` en `ai/scripts/set_agents_app.py` y una prueba
  focal con demora controlada.

### D2-DR01 — el spinner pisa prompts de instaladores interactivos

- `id`: D2-DR01
- `severity`: high
- `category`: correctness
- `acceptance_criterion`: AC-05
- `file`: `ai/scripts/set_agents_app.py`
- `line`: 1452-1454, 3612-3620
- `evidence`: `run_tty` existe para un hijo foreground con TTY heredada y prompts, pero el repair
  ejecuta ese hijo dentro del worker de `with_progress`; mientras el hijo escribe/lee el terminal, el
  caller sigue emitiendo frames `\r`. La misma forma se usa para el install posterior a `cmd_update`
  cuando no se pasó `--yes`. `suspend_terminal()` restaura el modo cooked, pero no pausa esos frames.
- `reproduction`: un hijo controlado escribió `CONFIRMAR? [s/N] ` y quedó esperando 450 ms. La salida
  fue `CONFIRMAR? [s/N] \r| ejecutando instalador…\r/...`: los frames aparecieron después del prompt
  y antes de que el hijo terminara.
- `required_outcome`: antes de cualquier prompt, el indicador debe ceder ownership completo del
  terminal. No envolver con animación concurrente un instalador/wizard interactivo; limitar progreso a
  fases conocidas como no interactivas o hacer que el propio hijo informe. Agregar una prueba que
  escriba un prompt durante el trabajo y prohíba frames posteriores hasta su handoff.
- `suggested_scope`: `run_tty`, instalación post-update y tests D2 focales.

### D2-DR02 — el gate documentado como verde falla sobre el commit

- `id`: D2-DR02
- `severity`: low
- `category`: testing
- `acceptance_criterion`: gates del paquete
- `file`: `docs/specs/025-consola-minima-y-flexible/evidence/D2-repair.md`
- `line`: 3-4, 22
- `evidence`: la evidencia afirma `git diff --check` exit 0, pero
  `git diff --check 489ecff^ 489ecff` terminó exit 2 por whitespace agregado en las líneas 3-4.
- `reproduction`: comando literal y salida registrados abajo.
- `required_outcome`: corregir el delta, rerun del gate sobre el rango exacto y evidencia que coincida
  con su salida real.
- `suggested_scope`: sólo `D2-repair.md` y su evidencia de gate.

## Comandos y resultados

- `python3 ai/scripts/heartbeat-run.py --interval 20 -- python3 -m unittest
  tests.test_harness.TuiTests
  tests.test_harness.HarnessTests.test_cmd_status_human_reports_delayed_progress_and_a_persistent_final_status
  tests.test_menu_ui.MenuDispatchTests.test_estado_general_reports_delayed_progress_and_a_persistent_final_status
  tests.test_menu_ui.RouteDoctorProgressTests tests.test_menu_ui.DoctorAllProgressTests -v` → exit 0,
  `Ran 73 tests in 5.569s`, `OK`.
- Reproducción D2-F01, flujo real `cmd_provider_verify()` con sólo `_provider_liveness` demorado
  350 ms → exit 0:
  `PROVIDER_VERIFY elapsed=0.351s rc=0 silent_during_wait=True stderr=''`.
- Reproducción D2-DR01, flujo real `run_tty()` con un `subprocess.run` controlado que emite prompt y
  demora 450 ms → exit 0:
  `INTERACTIVE rc=0 frame_after_prompt=True tail='CONFIRMAR? [s/N] \\r| ejecutando instalador…...'`.
- `git diff --check 489ecff^ 489ecff` → exit 2; reportó trailing whitespace en
  `D2-repair.md:3-4`.
- `python3 ai/scripts/heartbeat-run.py --interval 20 -- python3 -m unittest discover -s tests`
  fue interrumpido por pedido del coordinador para no continuar una suite global larga → exit 130;
  no se interpreta como falla del producto. `verify.sh` y `build.sh --check` no se ejecutaron por la
  misma instrucción.

## Scope y revisión completa

- Scope creep: no se observaron cambios fuera de los cinco archivos declarados por el repair; el
  wrapper de instaladores pertenece a D2, aunque su forma actual es defectuosa.
- `requires_full_review`: `false`. El delta cambia ownership interno del progreso y amplía call sites,
  pero no modifica contratos públicos ni arquitectura fuera de la superficie D2; la revisión focal
  cubre el riesgo nuevo.

```json
{
  "package_id": "D2-trabajo-visible",
  "verdict": "repair_required",
  "closed_findings": ["D2-F02"],
  "new_or_reopened_findings": ["D2-F01", "D2-DR01", "D2-DR02"],
  "requires_full_review": false,
  "requires_full_review_reason": "El repair mantiene los contratos públicos y el riesgo nuevo queda contenido en la implementación/call sites de progreso D2."
}
```
