# 048 — Diseño

## Funciones madre (leídas antes de tocarlas)

| Entrada | Qué la hace posible | Qué cambia |
|---|---|---|
| `set_agents_app.py` `menu()` | el loop del home; abría `TerminalSession` y despachaba `if index == 0..5` | despacha por `Action.key`; mide hosts una vez antes del loop; dispara el wizard en `first_run()` |
| `set_agents_app.py` `_home_header(drift, badge)` | pintaba pulse + `metrics_grid` y **probeaba en cada repintado** | wordmark + una línea medida + sólo los avisos accionables; lee del cache, no mide |
| `set_agents_app.py` `menu_style()` | el dict de estilo de todo picker | devuelve los pintores de `ui`; `dim`→`ui.muted`, `bold`→`ui.bold` |
| `tui.py` `_reduce_navigate(state, key)` | el reducer puro del picker | rama de multi-selección aditiva: espacio togglea, Enter devuelve `Marked` |
| `tui.py` `_render_items(...)` | pinta las filas visibles | en multi, el marcador de fila es `[x]`/`[ ]` en vez del punto de "valor actual" |
| `tui.py` `run_picker(...)` | la sesión de render | acepta `multi=` y `marked=`; devuelve `Marked` además de `Selected`/`FreeText` |
| `models_config.py` `write_models_overlay_field(scope, field, value)` | escritura atómica de una celda del overlay (ADR-0071) | acepta una tercera familia, `hosts`, con campos `model`/`effort` |
| `setup_models.py` `wizard(...)` | el menú de Modelos | despacha por clave; todos sus pickers reciben estilo por primera vez |

## Flujo del primer arranque

```
menu()
  first_run()?  ──sí──> TerminalSession ──> onboarding.run(_onboarding_ops())
                                              1 detección   (host_rows, cache)
                                              2 qué configurar (picker multi)
                                              3 preset       (postura + metodología)
                                              4 revisión     ← nada escrito todavía
                                              5 aplicar      → ops["set_postura"]
                                                               ops["set_metodologia"]
                                                               ops["install"](harness) por target
  measure_hosts()  (una vez, con with_progress)
  loop: run_picker(_menu_rows(visible_actions()), header=_home_header(...))
        └─ _run_home_action(key)
```

`onboarding.run` recibe **callables**, no importa nada mutante. Es lo que mantiene cada comando
dentro de `set_agents_app.py`, donde el golden suite lo parchea (ADR-0066), y lo que hace que el
wizard se pueda testear entero sin terminal ni subprocesos.

## Por qué el paso 5 no dibuja una barra viva

`install.sh` puede pedir sudo: mientras corre es el escritor exclusivo de la terminal, y hay un
pin duro de cero `\r` entre su prompt y `CHILD_DONE` (`tests/test_menu_ui.py`). El paso imprime
una línea plana antes de entregar la terminal (`run_tty` ya envuelve en `tui.suspend_terminal()`)
y marca `✓`/`✗` recién en la pantalla de cierre. La barra de pasos avanza *entre* hijos, nunca
encima de uno que pregunta.

## Por qué el pin de host no entra en `AREA_FIELDS`

`[areas.*]`/`[roles.*]` son gusto por **duty** (qué modelo corre el implementer). Un pin de host
es gusto de **máquina** (qué modelo debe usar el binario `agy` de esta computadora). Meterlo en
`AREA_FIELDS` habría arrastrado el field picker del wizard (`OVERRIDE_FIELDS`), el validador de
catálogo (`models_config.py:640`) y la matriz de áreas, para representar algo que no es un duty.
La familia `hosts` reusa la misma maquinaria atómica de 0071 sin tocar ninguna de esas tres.

## Puntos sin verificar

- **`agy models`** se parsea con la heurística de `host_adapters._agy_probe_models` (fail-closed:
  cualquier error o "sign in" devuelve conjunto vacío). No tengo una máquina con `agy` logueado
  en esta sesión, así que el formato exacto de su salida queda `sin verificar`; el menú de host
  degrada a "no listó ningún modelo" en ese caso, que es el comportamiento correcto igual.
- **Instalar el harness en agy** no existe (`install.py --target` no lo acepta,
  `_agy_install_harness` es `NotImplementedError`). Documentado como Non-goal, no como pendiente
  silencioso.
