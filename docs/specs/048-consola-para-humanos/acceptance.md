# 048 — Criterios de aceptación

Cada criterio se mide sobre un string que el picker recibe o sobre una llamada real, nunca
sobre una captura de pantalla.

## PKG-A — sistema visual

- **AC-A.1** `ui.cell_width` mide celdas: ancho doble cuenta 2, combinantes 0, ANSI 0, y todo
  texto latino acentuado cuenta 1 por carácter.
  *Prueba*: `tests/test_consola_ui.py::CellWidthTests`.
- **AC-A.2** La capacidad de color se recalcula en cada llamada: cambiar `NO_COLOR`/`TERM`/
  `COLORTERM` **después** de importar el módulo cambia lo que pinta.
  *Prueba*: `PaletteTests::test_colour_capability_is_recomputed_on_every_call`.
- **AC-A.3** Un stream que no es TTY no recibe un solo byte ANSI de ningún pintor de `ui`.
  *Prueba*: `PaletteTests::test_a_non_tty_stream_never_receives_ansi`.
- **AC-A.4** Todo glifo del sistema visual mide exactamente una celda.
  *Prueba*: `LabelRuleTests::test_every_glyph_the_renderer_uses_is_exactly_one_cell`.
- **AC-A.5** `multi=True` es aditivo: con `multi=False` el reducer se comporta igual que antes
  (Enter → `Selected`, dígito → `Selected`, espacio → typeahead).
  *Prueba*: `MultiSelectTests::test_single_selection_is_untouched_by_the_new_field` más los 76
  tests de `test_harness.TuiTests`, sin cambiar uno.

## PKG-B — arquitectura del menú

- **AC-B.1** El home despacha por clave: pedir una acción por su `key` llega a su rama, y el
  test falla si la clave desaparece.
  *Prueba*: `tests/test_menu_ui.py::MenuDispatchTests`.
- **AC-B.2** `salir` es la última fila en ambos modos; `vault`, `mcps`, `plugins`,
  `herramientas`, `proponer` y `hosts` no existen en modo simple y sí en experto.
  *Prueba*: `test_engineering_surfaces_are_hidden_until_expert_mode_is_on`,
  `test_harness.py::test_vault_is_expert_only_and_salir_stays_last_in_both_modes`.
- **AC-B.3** Toda etiqueta visible pasa `ui.is_safe_label` y mide una celda por carácter — home
  experto, hints, harness choices, nombres de host, targets y presets del wizard, posturas. Y la
  mitad negativa: `⏻ Salir`, `🗒 Vault`, `🧰 Herramientas`, `⚙️ Modo`, `📐 Metodología` siguen
  rechazados.
  *Prueba*: `test_harness.py::test_every_visible_label_is_fixed_width_and_free_of_emoji` y
  `::test_the_label_rule_still_rejects_the_glyphs_that_motivated_it`.
- **AC-B.4** El header del home no lleva jerga: ni `ADR-`, ni `models.local.toml`, ni `drift`,
  ni `probe`, ni `listado=`, ni el SHA.
  *Prueba*: `test_home_header_reaches_the_pickers_own_frame_and_carries_no_jargon`.
- **AC-B.5** Ningún paint mide: `probe_host_model_counts` se invoca desde `measure_hosts()` y
  desde ningún constructor de pantalla.
  *Prueba*: `grep -n probe_host_model_counts ai/scripts/set_agents_app.py` devuelve sólo
  `measure_hosts`.

## PKG-C — primer arranque guiado

- **AC-C.1** Cancelar cualquiera de los pasos 1 a 4 no escribe nada: ni postura, ni metodología,
  ni una sola invocación al instalador.
  *Prueba*: `OnboardingRunTests::test_cancelling_before_the_review_writes_nothing` y
  `::test_choosing_cancel_on_the_review_writes_nothing`.
- **AC-C.2** Aplicar instala exactamente los targets marcados y guarda el preset elegido; el
  argv sigue siendo `install.sh --harness <valor>`, idéntico al de antes.
  *Prueba*: `OnboardingRunTests::test_applying_installs_exactly_the_marked_targets_and_stores_the_preset`,
  `test_menu_ui.py::test_configurar_runs_the_guided_wizard_and_installs_what_it_returns`.
- **AC-C.3** La detección lista los siete candidatos, ausentes incluidos, y **nunca inventa** un
  conteo de modelos (045 AC-A.2).
  *Prueba*: `OnboardingScreenTests::test_detection_never_invents_a_model_count`.
- **AC-C.4** Los presets sólo referencian posturas y metodologías que existen — ADR-0054 fija
  las cadenas de `POSTURAS` y el wizard las deriva, no las reescribe.
  *Prueba*: `OnboardingScreenTests::test_presets_only_reference_real_posturas_and_metodologias`.
- **AC-C.5** Un install fallido se reporta como fallido, no se cuenta como éxito.
  *Prueba*: `OnboardingScreenTests::test_summary_reports_a_failed_install_instead_of_claiming_success`.

## PKG-D — hosts accionables

- **AC-D.1** El panel Estado nombra los siete hosts por su nombre humano.
  *Prueba*: `tests/test_consola_viva_hosts.py::test_estado_lists_hosts`.
- **AC-D.2** Un pin de host va al overlay de instancia bajo `[hosts.*]`; `models.toml` no se
  toca; overlay ausente o malformado degrada a "sin pin".
  *Prueba*: `tests/test_consola_ui.py` (familia `hosts`) y `git diff -- models.toml` vacío.
- **AC-D.3** `write_host_pin` rechaza un esfuerzo fuera de `models_config.EFFORTS`.
- **AC-D.4** El menú de un host sólo ofrece modelos que el probe listó; si listó cero, lo dice
  y no ofrece elegir.

## PKG-F — la escritura del overlay vuelve a validar (hallazgo, no pedido)

Encontrado corriendo los gates: ADR-0071 sacó la escritura del overlay del único camino que
corría `validate()`, así que la separación de deberes se podía saltear desde la consola. Ver
`evidence/implementer.md` §6 y la enmienda a ADR-0071.

- **AC-F.1** `--set` sobre una celda que rompe la separación de deberes devuelve rc 2, imprime
  el motivo y **no escribe nada**.
  *Prueba*: `test_harness::test_setup_models_rejects_separation_violation`,
  `::test_setup_models_check_rejects_opencode_separation_violation`.
- **AC-F.2** El wizard ("Preferir un modelo") hace lo mismo: `RECHAZADO` con el motivo y overlay
  inexistente en disco.
  *Prueba*: `test_models_wizard_ui::OverlayWriteIsValidatedTests`.
- **AC-F.3** Una celda legal sigue aterrizando en `models.local.toml`, con `models.toml`
  byte-idéntico.
  *Prueba*: `test_setup_models_set_and_check_roundtrip`,
  `OverlayWriteIsValidatedTests::test_a_legal_cell_still_lands_in_the_instance_overlay`.
- **AC-F.4** La validación usa el `roles_path` que recibió el wizard, no una ruta fija del repo
  — una corrida apuntada con `--models` valida contra su propio roster.

## PKG-E — gates

- **AC-E.1** `python3 -m unittest tests.test_harness tests.test_routing tests.test_menu_ui
  tests.test_models_wizard_ui tests.test_models_wizard_first_paint tests.test_consola_viva_hosts
  tests.test_consola_ui` en verde, más `./build.sh --check && ./ai/scripts/verify.sh`.
- **AC-E.2** Ningún test debilitado, salteado ni borrado. Los pines de comportamiento
  (Esc/Ctrl-C → rc 0, enums cerrados de MCP, una sola `TerminalSession` por flujo encadenado,
  cancelación de vault, `run_tty` sin redibujo, progreso nunca en stdout, sin `[2J`, primer paint
  < 300 ms) siguen intactos. Los pines de etiqueta e índice se reescribieron contra claves
  estables — más fuertes, con la mordida en rojo de cada uno registrada en la evidencia.
