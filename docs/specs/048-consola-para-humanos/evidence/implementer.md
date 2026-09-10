# 048 — Evidencia de implementación

## 1. Tests nuevos, mordidos en rojo antes de darlos por verdes

Cada uno se neutralizó introduciendo a propósito el defecto que dice cubrir, se confirmó el
rojo, y se revirtió. Salidas reales de la sesión.

| Defecto inyectado | Test que se puso en rojo |
|---|---|
| `cell_width` vuelve a contar codepoints (el bug real de `tui_views.visual_len`) | `CellWidthTests::test_wide_glyphs_count_two_cells` |
| La paleta se congela en el primer uso (el bug real de `tui_views.py:37`) | `PaletteTests::test_colour_capability_is_recomputed_on_every_call`, `::test_capability_ladder_degrades_by_terminal` |
| `is_safe_label` vuelve a ser `isascii()` | `LabelRuleTests::test_accented_spanish_is_allowed_and_symbols_are_not` |
| El espacio deja de marcar en multi | `MultiSelectTests` ×3 |
| Un header de sección puede marcarse | `MultiSelectTests::test_a_section_header_can_never_be_marked` |
| "Cancelar" en el review igual aplica | `OnboardingRunTests::test_choosing_cancel_on_the_review_writes_nothing` |
| La detección imprime `0 modelos` cuando no midió | `OnboardingScreenTests::test_detection_never_invents_a_model_count` |
| El cache de hosts no valida claves ni valores | `HostCountsCacheTests::test_a_tampered_cache_never_injects_a_host_or_a_bogus_count` |
| El cache de hosts nunca expira | `HostCountsCacheTests::test_an_expired_cache_is_ignored`, `::test_a_cache_stamped_in_the_future_is_ignored` |
| Una función de pintado vuelve a probear | `ProbeDisciplineTests::test_exactly_one_function_reaches_the_probe` |

Restaurado en cada caso: `tests.test_consola_ui` vuelve a 44/44 en verde.

## 2. Tests reescritos (etiqueta/índice → clave estable)

Ninguna aserción de **comportamiento** se tocó. Lo que cambió es cómo el test llega a la rama.

| Test | Antes | Ahora |
|---|---|---|
| `test_menu_ui::test_instalar_picks_a_harness_and_passes_it_to_install_sh` | `Selected(1), Selected(0), Selected(2)` | `_pick("configurar")` + wizard; la aserción `run_tty([install.sh, "--harness", "opencode"])` es **idéntica** |
| `test_menu_ui::test_menu_items_start_with_como_esta` | `MENU_ITEMS[0] == "Como esta"` | `test_salir_is_last_and_ends_the_session_in_both_modes` + `test_engineering_surfaces_are_hidden_until_expert_mode_is_on` |
| `test_harness::test_menu_items_carry_no_emoji_and_single_space_layout` | `isascii()` sobre `MENU_ITEMS` | `is_safe_label` + `cell_width` sobre **toda** etiqueta visible, más la mitad negativa que reafirma los cinco glifos de ADR-0050 |
| `test_harness::test_menu_orders_vault_immediately_before_salir` | posición en `MORE_ITEMS` | orden de claves en ambos modos |
| `test_harness::test_menu_items_include_proponer_herramienta_between_tools_and_mcp` | índices en `MORE_ITEMS` | `keys.index("proponer") == keys.index("herramientas") + 1` |
| `test_consola_viva_hosts::test_menu_has_como_trabaja_and_vault_under_mas` | texto de etiqueta | claves (`trabajo` presente, `vault` sólo en experto) |
| `test_menu_ui::test_tui_views_rounded_box_and_cache` | `tui_views.rounded_box` | `ui.rule` + `ui.SessionCache` |

**Intactos**: los 76 de `TuiTests`, progreso/stdout, `run_tty` sin redibujo, sesión única,
enums cerrados de MCP, las cuatro cancelaciones de vault, plugins en texto humano, stdin
no-TTY, `test_render_*`, y todo `test_routing.py`.

## 3. Defectos encontrados y corregidos que no estaban en el pedido

1. **`tui_views` congelaba la paleta en import-time** (`if use_color():` a nivel de módulo).
   Sin TTY al importar, sin color para siempre en ese proceso.
2. **`visual_len` usaba `len()`**: toda caja con un glifo ancho quedaba con el borde corrido —
   y había emoji en cuatro headers, que el gate no miraba.
3. **`_home_header` probeaba en cada repintado.** `probe_host_model_counts` levanta un
   subproceso por CLI.
4. **El wizard medía dentro de la pantalla alterna**, donde la línea de progreso es invisible:
   el usuario veía una terminal en blanco ~30 s sin explicación.
5. **Los probes corrían en serie**: el costo era la SUMA de los timeouts de cada CLI sin
   loguear. Ahora corren en paralelo (mismo timeout, mismo resultado, mismo orden de salida).
   Medido: 60 s → 30,1 s.
6. **Sin cache en disco**: los 30 s se pagaban en CADA arranque. Con el cache (TTL 30 min,
   0600, validado contra el universo cerrado de `HOSTS`): 30,1 s en frío → **0,00 s** en un
   proceso nuevo. Medido en vivo.
7. **`drift_state()` tarda ~9 s y corría en silencio** entre "revisando tus CLIs: listo" y el
   primer frame. Ahora se nombra mientras pasa.
8. **Cancelar el wizard disparaba una segunda pasada completa de probes.** Ahora sólo se
   re-mide si se aplicó algo.
9. **Segunda fuente de verdad de posturas**: el header decía `autonoma/guarded/paso-a-paso`;
   `POSTURAS` define `autonoma/consultiva/todo_consultado`. Ahora todo deriva de `POSTURAS`.
10. **Los pickers de `setup_models.py` no recibían estilo**: ninguna de sus ocho llamadas a
    `run_picker` pasaba `style`, así que la pantalla Modelos era monocroma.
11. **`README.md` documentaba un menú de nueve emoji** eliminado por ADR-0050.
12. **`docs/specs/README.md` tenía las filas 045/046/047 duplicadas.**

## 4. Verificación en vivo (la app corriendo de verdad, en un pty)

- Primer arranque con `HOME` limpio: los cinco pasos, con multi-selección real (espacio
  destilda), preset, revisión que lista sólo lo marcado, y **Cancelar sin escribir nada**.
- Home en modo experto a 88 columnas: 0 líneas exceden el ancho. A 80×24 y 120×40 tampoco.
- `Otras CLIs` → `Antigravity`: estado, modelos medidos, modelo y esfuerzo elegidos.
- `NO_COLOR=1` y `TERM=dumb`: **0** secuencias de color en pantalla; el wordmark degrada a una
  línea de texto.
- `./set-agents < /dev/null` → help, `rc 2`, **0** bytes ANSI en stdout.
- `--status` y `--route-doctor --json` sin cambios.

## 5. Un fallo que ya estaba roto antes de este paquete

`verify.sh` destapó `tests/test_decide_always.py::PanelRelabelTests::test_panel_names_the_table_as_curated_fallback`. **No lo rompió este paquete**: lo rompió el trabajo de 045 que ya estaba sin commitear en el árbol al empezar la sesión.

Probado, no supuesto:

```
$ git show HEAD:ai/scripts/setup_models.py | grep -c "DEFAULTS CURADOS"   → 1
$ grep -rn "DEFAULTS CURADOS" ai/scripts/                                  → (nada)
$ git diff --stat -- tests/test_decide_always.py                           → (vacío: intacto)
```

En HEAD las tres cadenas que el test exige (`DEFAULTS CURADOS`, `ADR-0030`, `variantes @tier`)
estaban en `_panel_lines`. 045 AC-A.1 reescribió ese panel a dos líneas humanas y se llevó las
tres puestas, sin actualizar el test — que además quedó **contradiciendo** al test propio de
045, `test_consola_viva_hosts::test_panel_header_is_human_compact`, que afirma
`assertNotIn("DEFAULTS CURADOS", ...)` y `assertNotIn("ADR-", ...)` sobre la misma función.

Resuelto sin perder señal:

- **`variantes @tier` vuelve**, en `_overrides_matrix_lines` — detrás de Overrides, que es la
  pantalla que 045 designó para la matriz curada. Era información real de ingeniería y su
  desaparición fue un efecto colateral no advertido del recorte, no una decisión.
- **La etiqueta de "esto es fallback, no la decisión"** sigue afirmada, ahora sobre el texto
  que la dice en castellano (`fallback si el router no decide`).
- **`ADR-0030` no vuelve**: 045 prohíbe explícitamente ids de ADR en superficie humana.
- Se agregó la otra mitad, `test_the_first_screen_never_shows_the_curated_matrix`, para que el
  par no pueda volver a divergir en silencio.

Ambos mordidos en rojo: quitar el conteo de tiers rompe el primero; devolver la matriz al
primer panel rompe el segundo.

## 6. Hallazgo grave, ajeno a este paquete: la separación de deberes se podía saltear desde la consola

`verify.sh` dejó rojos `test_setup_models_rejects_separation_violation` y
`test_setup_models_check_rejects_opencode_separation_violation`. **No eran tests viejos: eran
correctos y estaban señalando un agujero real** abierto por el trabajo de 045 que ya estaba sin
commitear en el árbol.

### Qué pasaba

ADR-0071 sacó el gusto por área/rol del `models.toml` trackeado y lo mandó al overlay de
instancia. Al hacerlo, la escritura se salió del único camino que corría `validate()` — y
`validate()` es donde vive la separación de deberes, la primera regla del harness: *el que
escribe no aprueba*.

`setup_models.py` escribía el overlay y **retornaba 0 sin validar nada**
(`if not mutated: return 0 if (subscription_written or overlay_written) else wizard(...)`,
antes de la línea `validate(config, roles_path)`).

Reproducido en vivo, antes del arreglo:

```
$ setup-models.sh --set audit.codex=gpt-5.6-terra
OVERLAY_WRITTEN areas.audit.codex=gpt-5.6-terra
rc=0

$ python3 -c "... effective_models_config(load_config('models.toml')) ..."
audit.codex     = gpt-5.6-terra
implement.codex = gpt-5.6-terra
validate: rechaza -> separation violation: spec-challenger shares codex_model=gpt-5.6-terra with implementation
```

El auditor quedaba corriendo el modelo del implementador. `models.toml` limpio, `--check` en
verde (sólo mira el archivo de fábrica), y el config que el router lee de verdad, en violación.
La opción **"Preferir un modelo"** del wizard usa el mismo `write_models_overlay_field`, así que
la TUI tenía el mismo agujero.

### Arreglado

`setup_models.write_overlay_cell()`: arma el overlay candidato **en memoria**, corre `validate()`
sobre el config efectivo resultante, y sólo entonces escribe. Un valor ilegal nunca toca el
disco — el mismo contrato fail-closed que ADR-0071 ya declara para un valor fuera de `[catalog]`.
Lo usan las dos entradas: `--set` y el wizard.

```
$ setup-models.sh --set audit.codex=gpt-5.6-terra
MODELS_INVALID: separation violation: spec-challenger shares codex_model=gpt-5.6-terra with implementation
rc=2
(no escribió nada)

$ setup-models.sh --set audit.codex_effort=high
OVERLAY_WRITTEN areas.audit.codex_effort=high
rc=0
```

Mordido en rojo: quitar la línea de `validate()` vuelve a poner los dos tests en rojo.

## 7. Los otros cuatro rojos previos

| Test | Qué pasaba | Resolución |
|---|---|---|
| `test_setup_models_set_and_check_roundtrip` | Esperaba `MODELS_WRITTEN`; ADR-0071 hace que `--set` escriba el overlay | Actualizado al contrato de 0071: el valor aterriza en `models.local.toml`, reaplicarlo es no-op, `models.toml` queda byte-idéntico (que es el punto de 0071), `--check` sigue pasando |
| `test_sort_key_tripwire_pins_full_tuple_shape` | La llamada `candidates.sort(...)` pasó a multilínea con ADR-0073 y el regex sin `re.DOTALL` dejó de matchear — el tripwire sólo podía fallar por "call not found", nunca por un cambio real de forma | `re.DOTALL` + se pinea el décimo elemento (`effort_request_rank`) en su posición documentada por ADR-0073: después de `model_request`, antes de `billing_rank` |
| `test_adr0043_ac10_no_call_site_still_passes_the_legacy_state_dir_shaped_root` | Contaba `== 4` ocurrencias; 045 AC-A.1 borró el bloque `listado=`/`usable=` del panel Estado y se llevó el cuarto call site | Se enuncia la regla en vez de contarla: **todo** punto de entrada de probe pasa `cache_root=_probe_cache_root()`. Más fuerte: falla ante un call site nuevo con root equivocado, cosa que un `== 4` aceptaba tras un borrado compensatorio |
| `test_usage_normalize_dispatch_table_covers_all_four_runtimes` | 047 ensanchó `RUNTIMES` con `agy`/`copilot`; `NORMALIZERS` no los tiene | **Hueco real, no lo adiviné.** Nadie midió qué reporta `agy` y este módulo prohíbe inventar un mapeo. Se agregó `UNMAPPED_RUNTIMES` (ausencia nombrada, patrón que el repo ya usa en `EFFORT_NAMED_ABSENCE`) y el test pasa a exigir que **todo** runtime declarado tenga translator **o** ausencia nombrada con motivo. El hueco es latente: ningún lane de agy/copilot reporta usage todavía |

Los cinco tests reescritos se mordieron en rojo antes de darlos por verdes.

## 8. Un error mío, y su reparación

Al revertir una mordida corrí `git checkout -- ai/scripts/routing_core/usage.py`, que llevó el
archivo a HEAD y **se llevó puesto también el cambio sin commitear de 047** (`RUNTIMES` con
`agy`/`copilot`). Restaurado: HEAD y el árbol tenían las mismas 194 líneas y la única diferencia
medida antes del error era la línea 97, así que reponerla devuelve el archivo exacto. `git diff`
sobre ese archivo muestra hoy sólo esa línea más mi bloque de ausencia nombrada.

Lección aplicada: para revertir una mordida sobre un archivo con cambios sin commitear, la
reversión va por reemplazo de cadena, nunca por `git checkout --`.
