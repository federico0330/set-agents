# P2 implementer evidence — checkpoint

## Summary

Implemented the process-wide unittest write guard in `tests/__init__.py`, while preserving
P1's package-import isolation setup. The guard creates one private temporary root, relocates
`HOME`, temp variables and `SET_AGENTS_STATE` before test-module imports, disables bytecode
writes, and rejects audit events for write/create/truncate/rename/delete/directory mutations
whose resolved destination falls outside that root. Its error includes the resolved target.

The guard deliberately treats pipes/sockets as non-filesystem descriptors and `/dev/null` as a
non-mutating device; neither is a destination that can modify user state. Deletion/rename checks
retain a final symlink lexically, because they mutate the sandbox directory entry rather than an
external symlink referent.

## Changed files

- `tests/__init__.py`
- `tests/test_harness.py`

## RED/GREEN evidence

1. RED (test added before guard):
   `python3 -m unittest tests.test_harness.HarnessTests.test_unittest_write_guard_allows_private_temporary_directory tests.test_harness.HarnessTests.test_unittest_write_guard_rejects_home_and_cli_destinations_before_mutation`
   exited non-zero because `tests._ORIGINAL_HOME` did not yet exist (`NameError`).
2. RED bite with guard temporarily neutralized in a separate process:
   `python3 ai/scripts/heartbeat-run.py --interval 20 -- python3 -c '... tests._WRITE_GUARD_ENABLED = False ...'`
   test went red with `FileNotFoundError` for `/home/federico/p2-write-guard-.../home.txt`.
   The parent directory is intentionally non-existent, so this proves the assertion depends on
   the guard without creating any external file.
3. GREEN:
   `python3 ai/scripts/heartbeat-run.py --interval 20 -- python3 -m unittest tests.test_harness.HarnessTests.test_unittest_write_guard_allows_private_temporary_directory tests.test_harness.HarnessTests.test_unittest_write_guard_rejects_home_and_cli_destinations_before_mutation tests.test_harness.HarnessTests.test_app_config_writers_never_clobber_each_other`
   passed: `Ran 3 tests ... OK`. This covers an allowed temporary write, effective real-home
   rejection before mutation with resolved destination in the exception, the STATE_DIR/.claude/
   .codex/.pi/.config/opencode destination matrix, and the existing `write_app_config` fixture.

## Additional local validation

- `python3 -m unittest tests.test_routing.RoutingTests.test_adr0043_ac07_ac08_codex_refresh_keeps_the_cache_warm_and_logout_invalidates_it_via_probe_inventory tests.test_routing.ClaudeCodeSpawnTests.test_spawn_survives_non_utf8_decodable_child_stdout_without_raising`
  passed: `Ran 2 tests in 20.534s ... OK`.
- Initial routing run exposed two guard integration defects: pipe descriptors were falsely
  treated as relative paths, and `subprocess.DEVNULL` was falsely treated as a writable file.
  Both were repaired in `tests/__init__.py`; the focused regressions above pass afterward.
- Full `python3 -m unittest tests.test_routing` was started through `heartbeat-run.py`; the
  execution channel stopped after its first 20-second heartbeat before it yielded a final status.
  **SIN VERIFICAR**: no pass/fail is claimed for that full module yet.
- `git diff --check`: pending final run after the checkpoint.

## Residual risks

- The guard observes Python-level filesystem audit events. Child processes inherit relocated
  home/temp/state variables, but OS-level writes made directly by non-Python children are not
  themselves intercepted by the parent audit hook.

## Exact next steps

1. Run the complete `tests.test_routing` and `tests.test_harness` validations to completion.
2. Run discovery, `verify.sh`, `build.sh --check`, and `git diff --check` as the pack requires.
3. Update this evidence with final command exit codes and output markers; hand to package gates.
