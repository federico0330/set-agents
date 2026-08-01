# 005-portable-harness · P3-tui

<!-- notas:auto -->
## Motivo

- objetivo: Reemplazar los menús numerados por un selector de flechas stdlib-only, con core puro testeable, decoder de teclas crudo, y handoff de terminal seguro para cada prompt in-process
- complejidad: medium
- paths: `ai/scripts/tui.py`, `README.md`, `INSTALACION.md`

## Tareas

- [x] Core puro PickerState/KeyEvent/reduce() en tui.py, testeable sin pty (AC-22) (completed) · python3 -m unittest tests.test_harness.TuiTests -v -k test_reduce -> 14 tests passed, cero I/O/termios importado en el módulo probado
- [x] Key decoder de bytes crudos a eventos lógicos, flechas/UTF-8/bracketed-paste (AC-23) (completed) · python3 -m unittest tests.test_harness.TuiTests -v -k test_decode_keys -> 12 tests passed (arrow variants, utf8 split, paste immunity, unknown CSI, empty=EOF)
- [x] TerminalSession: raw mode/alt screen con restauración en finally + SIGTERM/SIGHUP (AC-27) (completed) · python3 -m unittest tests.test_harness.TuiTests -v -k test_terminal_session -> 6 tests passed (finally restores on forced exception, SIGTERM/SIGHUP handlers invoked directly restore+SystemExit(128+signum), no-op on non-tty stdin, suspended() exits/reenters raw mode)
- [x] run_picker loop de render + suspend_terminal para prompts in-process (AC-25, AC-26) (completed) · python3 -m unittest tests.test_harness.TuiTests -v -k 'test_run_picker or test_suspend_terminal' -> 7 tests passed (navigate+select, freetext fallback end-to-end vía render loop real con termios mockeado, Esc por timeout-flush, Ctrl-C, freetext puro sin items, suspend_terminal no-op sin sesión y delegando con sesión activa)
- [x] Reemplazar menu()/tools_menu()/mcp_menu()/plugins_menu()/vault_menu()/choose()/wizard() por adaptadores sobre run_picker (AC-24) (completed) · python3 -m unittest -k tools_menu -k mcp_menu -k plugins_menu -v tests.test_harness -> 6 tests passed; python3 -m unittest tests.test_harness.HarnessTests.test_set_agents_tools_catalog tests.test_harness.HarnessTests.test_set_agents_mcp_across_harnesses tests.test_harness.HarnessTests.test_set_agents_plugins -v -> 3 passed (subprocess CLI surface untouched); choose()/wizard() migrados en setup_models.py preservando fallback de texto libre
- [x] Separar datos de impresión en cmd_status/cmd_tools/cmd_mcp/cmd_plugins preservando stdout máquina (AC-28) (completed) · python3 -m unittest -k stdout_is_byte_exact -v tests.test_harness -> 5 tests passed (baseline capturado ANTES del refactor a _tools_data/_mcp_data/_plugins_data/_status_data, confirmado byte-idéntico después)
- [x] Cerrar deuda de menú: orden [9] Vault, validación mcp_menu, plugins_menu legible, EOFError/KeyboardInterrupt limpio (AC-29) (completed) · python3 -m unittest -k menu_orders -k mcp_menu -k plugins_menu -k safe_input -v tests.test_harness -> 8 tests passed (Vault reordenado antes de Salir, action/harness de mcp_menu son enums cerrados sin freetext, plugins_menu nunca imprime formato máquina, EOFError/KeyboardInterrupt no producen traceback)
- [x] Actualizar README.md/INSTALACION.md con la descripción del nuevo selector (AC-30) (completed) · grep confirmó las grillas [1]..[8] en README.md/INSTALACION.md (les faltaba [9] Vault); reemplazadas por prosa del selector de flechas con las 9 opciones en orden (Vault antes de Salir); python3 -m unittest tests.test_harness.HarnessTests.test_readme_covers_all_oses -v -> 1 passed; grep -c '\[1\]\|\[8\]\|\[9\] ' README.md INSTALACION.md -> 0

## Hallazgos

- F-01 [high] closed — Reabierto: el fix de F-01 arreglo el busy-spin del loop win32 pero 8 de 9 call sites de run_picker en TuiTests no mocke…
- F-02 [high] closed — decode_keys emits a PASTE event but reduce() has no branch for it in any mode; bracketed-paste payloads are silently di…
- F-03 [high] closed — Menu context (server/harness state tables, status output, drift banner) is printed to the normal screen just before run…
- F-04 [high] closed — _status_data() is called unconditionally by cmd_status even for human=False (scripted/--json callers), adding 6 subproc…
- F-05 [medium] closed — TerminalSession bases the TTY decision on stdin.isatty() but writes ANSI unconditionally to stdout; set-agents | tee du…
- F-06 [low] closed — TerminalSession.__enter__ enters raw mode/alternate screen before installing SIGTERM/SIGHUP handlers; an exception betw…
- F-07 [medium] closed — vault_menu (the riskiest of the 5 rewritten menus -- feeds paths into mutating cmd_vault_init/cmd_vault_link, private-t…
- F-08 [medium] closed — F-08 cerrado a medias: el viewport se entrego pero la segunda clausula del finding ("search mode does not filter the li…
- F-09 [low] closed — Three user-facing strings still reference stale menu numbers (opción [1], opción [2]) after the numbered grid was repla…
- F-10 [low] closed — TuiTests scripted-bytes helper treats None as pending forever, so an unresolved picker hangs the test run instead of fa…
- D-02 [high] closed — Regresion nueva por el fix de F-05: _render ahora no escribe nada si stdout no es TTY, pero _enter_raw decide raw mode …
- D-03 [medium] closed — El header de F-03 no se clampea contra la altura de terminal; _viewport_slice solo clampea items, no el header, asi que…
- D-05 [low] closed — Residual de F-09 en un archivo que el propio repair edito: setup_models.py:234 todavia dice opcion 1/2 despues de que e…
- D-06 [low] closed — Nit del fix de F-06: el cleanup del except BaseException en __enter__ vuelve a llamar signal.signal, que si fallo por l…

## Recorrido

- review: repair_required (10 hallazgos)
- verificación: 0 refutados, 7 sostenidos
- verificación: 0 refutados, 4 sostenidos
- repair: F-01 → 2 archivos
- repair: F-02, F-03, F-04, F-05, F-06, F-07, F-08, F-09, F-10 → 4 archivos
- repair: F-01, D-02, D-03, F-08, D-05, D-06 → 3 archivos
- delta review: repair_required
- delta review: repair_required
- delta review: pass
- testing: pass
- runtime QA: pass (waived)
- gate `verify.sh`: pass
- gate `unittest`: pass
- gate `build.sh--check`: pass
- gate `git-diff--check`: pass

↩ [[features/005-portable-harness|005-portable-harness]]
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
