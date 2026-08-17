# D2-trabajo-visible — reparación consolidada

Package: `D2-trabajo-visible`
Estado: `repaired` (un único batch)
Findings: `D2-F01`, `D2-F02`

## Trazabilidad

| Finding | Cambio mínimo | Regresión | Verificación |
|---|---|---|---|
| D2-F01 | `ai/scripts/tui.py:574-640` retrasa la activación a 300 ms y mantiene la línea final; `ai/scripts/set_agents_app.py:1371-1374,1386-1454,3612-3620,3750-3751,3778-3781` lo aplica a `--status` humano, Estado general, update/fetch/pull/install y los instaladores. | `tests/test_harness.py:2474-2497`, `tests/test_menu_ui.py:109-120`; las rutas se demoran 350 ms y exigen progreso en stderr más estado persistente. | focal verde, gates pendientes abajo. |
| D2-F02 | `ai/scripts/tui.py:608-640`: el worker sólo ejecuta `fn`; el hilo llamador es el único escritor del stream. No hay `join(timeout)` de un escritor ni puede quedar un frame tardío. | `tests/test_harness.py:12804-12837` bloquea el primer frame por 1.1 s (más que el timeout anterior) y prueba que la salida permanece estable después del final. | focal verde, gates pendientes abajo. |

## Mordidas rojo/verde

1. **D2-F01 rojo.** Se reemplazó temporalmente el wrapper de `cmd_status(human=True)` por `_status_data(rows=human)`; `python3 ai/scripts/heartbeat-run.py --interval 20 -- python3 -m unittest tests.test_harness.HarnessTests.test_cmd_status_human_reports_delayed_progress_and_a_persistent_final_status -v` terminó **exit 1**: faltó `· relevando estado…` en stderr tras las demoras de 350 ms. Se restauró el wrapper; el mismo comando terminó **exit 0**.
2. **D2-F02 rojo.** Se introdujo temporalmente un writer diferido después de la línea final; `python3 ai/scripts/heartbeat-run.py --interval 20 -- python3 -m unittest tests.test_harness.TuiTests.test_with_progress_backpressured_frame_cannot_write_after_the_final_status -v` terminó **exit 1** con `late` agregado tras `consultando: listo`. Se retiró la mutación; el mismo comando terminó **exit 0**.

## Comandos ejecutados

- `python3 ai/scripts/heartbeat-run.py --interval 20 -- python3 -m unittest tests.test_harness.TuiTests tests.test_harness.HarnessTests.test_cmd_status_human_reports_delayed_progress_and_a_persistent_final_status tests.test_menu_ui.MenuDispatchTests.test_estado_general_reports_delayed_progress_and_a_persistent_final_status tests.test_menu_ui.RouteDoctorProgressTests tests.test_menu_ui.DoctorAllProgressTests -v` → **exit 0**, 73 tests.
- `git diff --check` → **exit 0**.

## Pendiente de este checkpoint

Ejecutar suite completa, `verify.sh`, `build.sh --check`, registrar resultados y commitear el batch. No hay findings restantes ni blocker conocido.
