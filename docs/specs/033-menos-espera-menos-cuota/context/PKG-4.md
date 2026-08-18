# Context pack — PKG-4 windows-sin-mentiras

Spec: `docs/specs/033-menos-espera-menos-cuota/spec.md` (hash `18dcffaf…e4894c`). **AC-4.1–AC-4.5**. Orden: primero a implementar.

**Objetivo.** `windows-bootstrap` verde sin que verde = no probamos nada: los 4 `subprocess.run(["bash", …])` directos pasan por la guarda; casos 5–8 diagnosticados uno por uno; techo de skips en el job; flaky de macOS determinista **sin** subir el `sleep`.

## Paths (leídos hoy)

- `tests/test_harness.py:43-69` — helper `run()`: si `cmd[0] != sys.executable` llama `tests.require_posix_toolchain()`; en no-POSIX antepone `bash` a `*.sh`. **Usar esto, no reinventar.**
- `tests/__init__.py:431-435` — `require_posix_toolchain()` → `SkipTest` con razón nombrada. **No tocar el probe** (`:420-428`).
- AC-4.1, cuatro sitios que **bypassean** `run()`:
  - `:488-525` `test_build_check_detects_global_drift_and_names_the_file` — `["bash", str(guest/"build.sh"), "--check"]` en `:507` y `:517`
  - `:527-566` `test_build_sh_generate_mode_regenerates_global_and_installs_the_drift_hook` — `:551`
  - `:1313-1343` `test_install_sh_yes_terminates_the_opencode_auth_loop` — `:1337` `["bash", "install.sh", …]`
  - `:4719-4798` `test_guest_copy_scaffolds_and_verifies_portably` — `:4762` `build.sh --install`, `:4790` `verify.sh`
- AC-4.2 caso 5: `:1832-1858` espera `TOOL_REJECTED backdoor`; Windows obtuvo `TOOL_UNKNOWN`. `cmd_tools_install` (`set_agents_app.py:2111-2118`) imprime `TOOL_UNKNOWN` cuando `load_catalog()` no ve el overlay; `_load_local_catalog` lee `ROOT/"tools.local.toml"` (`:1471-1502`); `_tools_root` (`test_harness.py:1642-1648`) copia `tools.toml` y parchea `app.ROOT`. **No es bash.** Diagnosticar por qué el overlay no entra (shape `:1530-1541`, parse warning, ROOT). Si el defecto es del harness → arreglar; si es capacidad ausente → skip con razón medida en el código.
- AC-4.2 caso 6: `:2998-3013` `["bash", "set-agents"]` + `/dev/null` espera rc=2. `main()` ya hace `print_help(); return 2` si `not stdin.isatty()` (`set_agents_app.py:4392-4394`). `set-agents:12` es `exec python3 …`. El test **también** llama bash directo: si stderr es el lanzador WSL sin distro, es toolchain (guarda); si Python corrió y devolvió 1, es contrato de `main()`.
- AC-4.2 caso 7: `:3470-3479` compara `plan["files"]` con `/`. `vault_ops.vault_migration_plan` (`:272-331`) hace `str(rel)` en `:319-323` — en Windows `Path` emite `\`. `set_agents_app.py:2851-2856` reexporta esa función. Huele a defecto real: `as_posix()`, no skip.
- AC-4.2 caso 8: `:6177-6189` **ERROR** no diagnosticado. Lee `ROOT/"docs/adr/…"` y `ROOT/"ai/state/decisions-log.jsonl"` (`:6188`). Traza FileNotFound vs encoding vs sandbox.
- AC-4.4: `tests/test_provider_registry.py:296-316` — `time.sleep(0.35)` vs `_PROGRESS_DELAY_SECONDS = 0.3` (`tui.py:574`) y modo degradado `TERM=dumb` (`:559-568`, `:621-622`). El runner macOS termina antes del primer `· verificando proveedores…\n` y solo deja `verificando proveedores: listo\n`. **Inyectar reloj/stream. Prohibido subir el sleep.**
- `.github/workflows/ci.yml:32-66` — job `windows-bootstrap`; suite en `:58-66` **sin techo de skips**. Hoy 654/1276 (spec). AC-4.3: imprimir skips y fallar si suben sin declararlo.

## ADRs / invariantes

- [Windows nativo = bootstrap, no runtime](../../../notas/decisiones/2026-08-18%20windows-nativo-es-bootstrap-no-runtime.md) — no inventar runtime Windows.
- ADR-0038 — catálogo local; `TOOL_REJECTED` vs `TOOL_UNKNOWN` es el contrato del caso 5.
- ADR-0041 — `heartbeat-run.py --interval N -- <cmd>`; sin pipes/tail como alternativa.
- ADR-0051 — sandbox en `tests/__init__.py`; no relajar aislamiento para que Windows pase.

## Validación local

```
python3 -m unittest tests.test_harness.HarnessTests.test_build_check_detects_global_drift_and_names_the_file tests.test_harness.HarnessTests.test_build_sh_generate_mode_regenerates_global_and_installs_the_drift_hook tests.test_harness.HarnessTests.test_install_sh_yes_terminates_the_opencode_auth_loop tests.test_harness.HarnessTests.test_cmd_tools_install_rejects_a_hand_edited_local_catalog_entry_with_a_disallowed_command tests.test_harness.HarnessTests.test_stdin_from_dev_null_exits_2_with_help_never_entering_the_menu tests.test_harness.HarnessTests.test_vault_migration_plan_merge_with_nested_dirs_and_zero_collisions tests.test_harness.HarnessTests.test_adr_0017_and_0007_amendment_and_superseding_decision_recorded tests.test_provider_registry.ProviderVerifyLivenessScopeTests.test_slow_liveness_reports_stderr_progress_without_changing_provider_stdout
python3 ai/scripts/heartbeat-run.py --interval 20 -- python3 -m unittest tests.test_harness.HarnessTests.test_guest_copy_scaffolds_and_verifies_portably
python3 ai/scripts/heartbeat-run.py --interval 20 -- ./build.sh --check
git diff --check
```

`pytest` no existe. AC-4.5: tres jobs verdes, SHA de esa corrida en la evidencia.

## Reviewers / runtime / tests

- `required_reviewers`: `["package-reviewer"]` — no auth/secrets/PII; no UI de producto.
- `runtime_surface`: **true** — `vault_ops.py` es planificador de migración (AC-4.2.7); el techo de skips es workflow de CI.
- test owner: **implementer** (scoped). `strict_tdd`: **false**.

## Fuera de alcance

PKG-5 (`verify.sh` presenter) · PKG-1 lanes · runtime Windows nativo · subir sleeps · relajar/borrar tests · probe de toolchain · 032.

## Excepciones recomendadas (`update-package --exception`)

`owned_paths` ya cubre `tests`, `.github/workflows/ci.yml`, `ai/scripts/vault_ops.py`.

- `ai/scripts/set_agents_app.py` — **si** el caso 5 (overlay no leído) o el 6 (rc=1 de `main`) exigen arreglo de producto. No está en owned.
- `ai/scripts/tui.py` — **solo** si AC-4.4 no se puede inyectar el reloj desde el test (el delay vive en `:574`). Preferir seam de test.

## Mordida

Todo test nuevo: `cp` del archivo de producción → romper → rojo → `cp` restaurar → verde. Nunca `git checkout`/`restore`/`stash`.
