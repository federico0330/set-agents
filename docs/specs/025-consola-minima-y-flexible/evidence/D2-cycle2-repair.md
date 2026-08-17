# D2-trabajo-visible — reparación consolidada, ciclo 2

Package: `D2-trabajo-visible`
Base fija: `489ecff52a7c8aca84ce931180c6f0005cb8a63c`
Estado: `validación focal completada; commit pendiente`

## Alcance y checkpoint

- Se leyeron completos `context/D2-trabajo-visible.md`, `evidence/D2-delta-review.md`,
  `evidence/D2-cycle2-verification.md` y `evidence/D2-repair.md`, además de las instrucciones
  de `package-repair`, `safe-implementation` y `quality-gates`.
- El árbol compartido ya contenía cambios modificados y no trackeados ajenos; se preservan. Este
  batch sólo toca `ai/scripts/set_agents_app.py`, `tests/test_provider_registry.py`,
  `tests/test_menu_ui.py`, `evidence/D2-repair.md` y este archivo.
- Cambio preparado, todavía sin gate: `cmd_provider_verify()` ahora envuelve la fase de liveness
  con `tui.with_progress(..., stream=sys.stderr)` y deja el protocolo `PROVIDER_*` en stdout;
  `run_tty()` y el install post-update sin `--yes` ejecutan el hijo directamente, conservan el
  handoff de `suspend_terminal()` y escriben sólo el estado persistente después del hijo.
- Pruebas preparadas: demora controlada de 350 ms para D2-F01; prompts controlados de 350 ms para
  `run_tty` y post-update sin `--yes` para D2-DR01.
- Próximo paso exacto: ejecutar los tres tests focales con `heartbeat-run.py`, revisar cualquier
  falla y luego correr `git diff --check 489ecff^ HEAD` sobre el commit resultante.

## Reparación y pruebas

| Finding | Cambio | Prueba focal | Resultado |
|---|---|---|---|
| D2-F01 | `ai/scripts/set_agents_app.py:2723-2749` separa el cuerpo síncrono y lo ejecuta bajo `tui.with_progress` exclusivamente en stderr; `PROVIDER_*` queda en stdout. | `tests/test_provider_registry.py:293-313` demora `_provider_liveness` 350 ms, exige la línea degradada y final en stderr, y prohíbe el indicador en stdout. | verde, exit 0. |
| D2-DR01 | `ai/scripts/set_agents_app.py:1451-1461` sólo anima post-update con `--yes`; `:3631-3642` ejecuta `run_tty` sin renderer concurrente. Ambas rutas dejan estado final después del hijo. | `tests/test_menu_ui.py:180-228` hace que el hijo escriba un prompt y espere 350 ms; prohíbe `\\r` entre prompt y final, y cubre `run_tty` + post-update sin `--yes`. | verde, exit 0. |
| D2-DR02 | `evidence/D2-repair.md:3-4` elimina los dos trailing spaces introducidos en el commit anterior. | `git diff --check` sobre el worktree. El rango exacto se registra tras commitear. | verde, exit 0. |

## Mordidas RED/GREEN

1. **D2-F01 RED.** Se guardó `ai/scripts/set_agents_app.py` en
   `/tmp/d2-cycle2-set_agents_app.py`, se sustituyó temporalmente el wrapper por una llamada
   directa a `_cmd_provider_verify`, y se ejecutó:
   `python3 ai/scripts/heartbeat-run.py --interval 20 -- python3 -m unittest tests.test_provider_registry.ProviderVerifyLivenessScopeTests.test_slow_liveness_reports_stderr_progress_without_changing_provider_stdout -v`.
   **Exit 1** en 0.353 s: faltó `· verificando proveedores…` en stderr. Se restauró el archivo
   con `cp` desde la copia controlada.
2. **D2-DR01 RED.** Con la misma copia/restauración se envolvieron temporalmente ambos hijos con
   `tui.with_progress`; `python3 ai/scripts/heartbeat-run.py --interval 20 -- python3 -m unittest tests.test_menu_ui.InteractiveInstallerProgressTests -v`
   terminó **exit 1** en 0.706 s. Ambas aserciones encontraron `\\r| …` entre el prompt y
   `CHILD_DONE`. Se restauró el archivo con `cp`.
3. **GREEN.** `python3 ai/scripts/heartbeat-run.py --interval 20 -- python3 -m unittest tests.test_provider_registry.ProviderVerifyLivenessScopeTests tests.test_menu_ui.InteractiveInstallerProgressTests tests.test_menu_ui.RouteDoctorProgressTests tests.test_menu_ui.DoctorAllProgressTests -v` → **exit 0**, `Ran 13 tests in 2.143s`, `OK`.
4. `git diff --check` → **exit 0**. El gate requerido de rango exacto se ejecuta tras el commit
   de esta reparación; no se ejecutaron suite global, `verify.sh` ni `build.sh --check` porque son
   gates de otro rol.

## Próximo paso exacto

Commitear exclusivamente los cinco archivos de este batch, ejecutar
`git diff --check 489ecff^ HEAD`, y registrar su exit real junto con el SHA en esta evidencia.
