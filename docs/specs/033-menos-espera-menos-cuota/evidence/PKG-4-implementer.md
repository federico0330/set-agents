# PKG-4 implementer evidence — windows-sin-mentiras

Package: PKG-4. Feature: 033-menos-espera-menos-cuota.
Owned paths: `tests`, `.github/workflows/ci.yml`, `ai/scripts/vault_ops.py`.
Probe not touched: `tests/__init__.py:420-428` (verified after the diff).

## AC → change → proof

| AC | Change (file:line) | Proof |
|---|---|---|
| AC-4.1 | `run()` accepts `cwd`/`timeout`/`stdin` (`tests/test_harness.py:43-71`). Four named sites plus the same-class cursor-tree check now call `run()`: `:518`, `:549`, `:1331`, `:4767`/`:4795`, `:13573`. Pin: `:10472`. | `test_ac41_named_windows_failures_call_bash_only_through_run` OK. Focused build/install/guest tests OK. Bite: re-insert `subprocess.run(["bash", …])` → pin FAIL; `cp` restore → OK. |
| AC-4.2.5 | Fixture writes TOML with `marker.as_posix()` (`tests/test_harness.py:1836-1844`). No `set_agents_app.py`. | `test_cmd_tools_install_rejects_a_hand_edited_local_catalog_entry_with_a_disallowed_command` OK. Linux reproduction of the Windows TOML: `str(PureWindowsPath(r"C:\Users\…"))` inside a basic string raises `TOMLDecodeError` (measured in diagnosis). |
| AC-4.2.6 | `test_stdin_from_dev_null…` uses `run(..., stdin=devnull)` (`:3003-3007`). Same WSL-stub bash as cases 1–4; Python `main()` tty contract already covered by `test_main_never_touches_menu…`. | Focused unittest OK (rc=2 on this POSIX host). |
| AC-4.2.7 | `_plan_relpath` (`ai/scripts/vault_ops.py:272-279`) used at `:317`, `:323`, `:332-338`. | `test_vault_migration_plan_merge_with_nested_dirs_and_zero_collisions` OK. New `test_vault_plan_relpath_is_posix_even_for_windows_paths` (`tests/test_harness.py:3479`). Bite below. |
| AC-4.2.8 | Reads tracked archive `docs/historia/estado-2026-08/decisions-log.jsonl` with `encoding="utf-8"` (`tests/test_harness.py:6188-6199`). | `test_adr_0017_and_0007_amendment_and_superseding_decision_recorded` OK. `git ls-files` lists the archive; live `ai/state/decisions-log.jsonl` is gitignored (ADR-0047). |
| AC-4.3 | `.github/workflows/ci.yml:70-85` prints `WINDOWS_BOOTSTRAP_SKIPS` and fails if `skips > 660`. Parser `tests/test_harness.py:74-81`. Pins `:10452`, `:10461`. | Both new tests OK. Bites below. Ceiling = 654 (spec, 2026-08-18) + 4 AC-4.1 sites + case 6 + cursor-tree drift now gated by `run()`. |
| AC-4.4 | Stream handshake, no extra sleep (`tests/test_provider_registry.py:297-330`). `tui.py` not edited. | Focused unittest OK in 1.395s with the cheap bundle. |
| AC-4.5 | Not this spawn. Ceiling is ready; orchestrator cites the CI SHA at package close. | — |

`./build.sh --check` → `BUILD_CHECK_PASS` + `GLOBAL_TREE_SYNC_OK profile=go-zen harnesses=5`. `git diff --check` clean. Probe `tests/__init__.py:420-428` unchanged.

## Cases 5–8 diagnosis

### 5 — TOOL_UNKNOWN vs TOOL_REJECTED (harness fixture, fixed)

Measured: `cmd_tools_install` prints `TOOL_UNKNOWN` when `load_catalog()` has no `cli.backdoor`. `_load_local_catalog` reads `ROOT/"tools.local.toml"` and on `TOMLDecodeError` returns `{}`. The fixture interpolated `str(Path(td)/"marker")` into a TOML basic string. On Windows that is `C:\Users\...`; `\U` is a unicode escape → parse fail → overlay dropped. Confirmed on this Linux host with `PureWindowsPath(r"C:\Users\runner\AppData\Local\Temp\x\marker")` inside the same TOML shape: `tomllib.TOMLDecodeError`. Decision: fix the fixture (`as_posix()`), do not skip, do not touch `set_agents_app.py`.

### 6 — rc=1 vs 2 (toolchain, skip via existing guard)

Measured: the test called `subprocess.run(["bash", "set-agents"], stdin=/dev/null)` and bypassed `run()`. Spec CI 32153232496: `bash` is the WSL launcher with no distro — the same defect as cases 1–4, which returns 1, not Python `main()`. `set_agents_app.py:4392-4394` already does `print_help(); return 2` when stdin is not a tty; that contract is asserted in-process by `test_main_never_touches_menu_or_the_picker_when_stdin_is_not_a_tty`. Decision: route through `run()` so native Windows skips with `_TOOLCHAIN_REASON`. Not a product bug.

### 7 — `\` vs `/` (real portability defect, fixed)

Measured: `vault_migration_plan` stored `str(rel)`. `str(PureWindowsPath("features")/"replenishment-v2.md")` is `features\replenishment-v2.md` even on Linux. Decision: `_plan_relpath` → `as_posix()`. Not a skip.

### 8 — ERROR FileNotFound (harness read of gitignored state, fixed)

Measured: the test read `ROOT/"ai/state/decisions-log.jsonl"`. `/ai/state/` is gitignored (ADR-0047). `windows-bootstrap` runs `unittest discover` without `verify.sh`'s `seed-state.py`. Even a seed is an empty skeleton (no slug). Linux `verify.sh` is green on machines that already have a live log; a fresh clone without history ERRORs. `git ls-files` shows the slug in the tracked archive `docs/historia/estado-2026-08/decisions-log.jsonl:14` (`ac09-ac10-pi-minimal-target-accepted`). PYTHONUTF8=1 is already on the Windows job, so this is not cp1252. Decision: assert the tracked archive with `encoding="utf-8"`. Invariant kept (slug still pinned). No skip.

## Bite evidence

Commands used `cp` to `/tmp/pkg4-bite/`, never `git checkout`/`restore`/`stash`.

### `test_vault_plan_relpath_is_posix_even_for_windows_paths`

Broke `_plan_relpath` to `return str(path.relative_to(root))`.

```
FAIL: ... AssertionError: 'features\\replenishment-v2.md' != 'features/replenishment-v2.md'
```

`cp` restore → `ok`.

### `test_windows_bootstrap_job_pins_a_skip_ceiling`

Set `WINDOWS_BOOTSTRAP_SKIP_CEILING: "0"`.

```
FAIL: ... Regex didn't match: 'WINDOWS_BOOTSTRAP_SKIP_CEILING:\\s*[\\"\']?660'
```

`cp` restore → `ok`.

### `test_windows_bootstrap_skip_count_parser_reads_unittest_summaries`

Regex `skipped=` → `SKIPPED_NEVER=`.

```
ERROR: ValueError: unittest output has no skip count to enforce the windows-bootstrap ceiling
```

(The first assertion raises before comparing 654; still red against the broken parser.) `cp` restore → `ok`.

### `test_ac41_named_windows_failures_call_bash_only_through_run`

Re-inserted `subprocess.run(["bash", str(guest / "build.sh"), "--check"])` in `test_build_check_detects_global_drift_and_names_the_file`.

```
FAIL: ... Regex matched: 'subprocess.run(["bash"' ... still invokes bash without the toolchain guard
```

`cp` restore → `ok`.

## Focused unittest (literal)

Cheap bundle (9 tests, 1.395s):

```
test_vault_plan_relpath_is_posix_even_for_windows_paths ... ok
test_windows_bootstrap_job_pins_a_skip_ceiling ... ok
test_windows_bootstrap_skip_count_parser_reads_unittest_summaries ... ok
test_ac41_named_windows_failures_call_bash_only_through_run ... ok
test_cmd_tools_install_rejects_a_hand_edited_local_catalog_entry_with_a_disallowed_command ... ok
test_stdin_from_dev_null_exits_2_with_help_never_entering_the_menu ... ok
test_vault_migration_plan_merge_with_nested_dirs_and_zero_collisions ... ok
test_adr_0017_and_0007_amendment_and_superseding_decision_recorded ... ok
test_slow_liveness_reports_stderr_progress_without_changing_provider_stdout ... ok
Ran 9 tests in 1.395s
OK
```

AC-4.1 build/install (heartbeat-run, 98.55s; the cursor-tree name under HarnessTests was a loader error, re-run under `CursorRuntimeTargetTests`):

```
test_build_check_detects_global_drift_and_names_the_file ... ok
test_build_sh_generate_mode_regenerates_global_and_installs_the_drift_hook ... ok
test_install_sh_yes_terminates_the_opencode_auth_loop ... ok
```

```
test_build_check_fails_when_the_tracked_cursor_tree_drifts (CursorRuntimeTargetTests) ... ok
Ran 1 test in 56.095s
OK
```

```
test_guest_copy_scaffolds_and_verifies_portably ... ok
Ran 1 test in 20.708s
OK
```

```
SELF_SCAFFOLD_SYNC_OK files=23
GLOBAL_TREE_SYNC_OK profile=go-zen harnesses=5
BUILD_CHECK_PASS
```

`git diff --check` empty (exit 0).

## complete-task

All four `ok` (`changed: true`), `--actor implementer`, `--no-render`. Revision 23. PKG-4 still `package_implementation` (no accept-package from this spawn).

## Changed files

- `tests/test_harness.py`
- `tests/test_provider_registry.py`
- `ai/scripts/vault_ops.py`
- `.github/workflows/ci.yml`
- `docs/specs/033-menos-espera-menos-cuota/evidence/PKG-4-implementer.md` (this file)

Not edited: `tests/__init__.py` probe, `ai/scripts/set_agents_app.py`, `ai/scripts/tui.py`.
