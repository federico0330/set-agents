# P2 post-repair gates

Date: 2026-08-14
Scope: read-only post-repair verification for `P2-nada-escribe-afuera`.

## Results

| Check | Exact command | Exit code | Result | Output marker |
|---|---|---:|---|---|
| Global drift fixture | `python3 -m unittest tests.test_harness.HarnessTests.test_build_check_detects_global_drift_and_names_the_file` | 0 | PASS | `Ran 1 test in 55.795s`; `OK` |
| P2 write guards + writer isolation | `python3 -m unittest tests.test_harness.HarnessTests.test_unittest_write_guard_allows_private_temporary_directory tests.test_harness.HarnessTests.test_unittest_write_guard_rejects_home_and_cli_destinations_before_mutation tests.test_harness.HarnessTests.test_app_config_writers_never_clobber_each_other` | 0 | PASS | `Ran 3 tests in 0.151s`; `OK` |
| Diff whitespace | `git diff --check` | 0 | PASS | no output |
| Build check (heartbeat) | `./ai/scripts/heartbeat-run.py --interval 25 -- ./build.sh --check` | 0 | PASS | `SELF_SCAFFOLD_SYNC_OK files=2`; `GLOBAL_TREE_SYNC_OK profile=go-zen harnesses=4`; `BUILD_CHECK_PASS` |

## Fixture write-scope confirmation

PASS: the repaired drift fixture copies the repository into a `TemporaryDirectory` guest and performs its mutations only under that temporary guest. The dedicated private-temporary-directory guard passed, and the home/CLI-destination guard passed before mutation.

No production, test, or configuration files were repaired or modified by these checks. Artifact: this evidence file.

## Additional focal gates (2026-08-14)

Command executed with heartbeat:

`./ai/scripts/heartbeat-run.py --interval 25 -- python3 -m unittest tests.test_harness.HarnessTests.test_guest_copy_scaffolds_and_verifies_portably tests.test_onboarding.ScopedInstallDriftTests.test_targeted_install_records_scope_and_drift_check_honors_it tests.test_harness.HarnessTests.test_child_cannot_open_external_file_for_writing tests.test_harness.HarnessTests.test_write_guard_rejects_parent_symlink_remove_and_rename tests.test_routing.RoutingTests.test_crash_between_begin_and_commit_preserves_consistency`

Result: **INCOMPLETE / FAIL (exit 130)**. The process emitted repeated `heartbeat-run: still running, 25s without output` markers and was interrupted after approximately four minutes without producing unittest completion output (`Ran ...`, `OK`, or a failure traceback). Individual focal attribution is unavailable from this combined run.

`git diff --check` — **PASS (exit 0)**; no output.

## Hang isolation and corrected focal names (2026-08-14)

Guest focal command (timeout 180 s; log: `/tmp/p2-guest.log`):

`timeout 180s python3 -m unittest tests.test_harness.HarnessTests.test_guest_copy_scaffolds_and_verifies_portably`

Result: **FAIL (exit 1, not timeout)**. The outer test completed in `136.305s`, but its guest subprocess reported `FAILED (errors=14)` while running `test_shell_scripts_parse`; the precise failing phase is nested `bwrap` executing guest `bash -n` commands, with `subprocess.CalledProcessError` exit status 1. The outer assertion then failed. No `Ran ... OK` marker was produced. The process listing after completion showed only the enclosing sandbox `bwrap`; no guest `build.sh` or unittest remained.

The first four-test command used two names that do not exist and therefore is not evidence for those guards. Its valid tests did run: onboarding and routing each passed (`.`, `.`), while the two invalid names produced loader `AttributeError`; command exit 1 after `Ran 4 tests in 120.957s`.

Corrected guard command (timeout 180 s; no guest):

`timeout 180s python3 -m unittest tests.test_harness.HarnessTests.test_unittest_descendant_cannot_open_an_external_absolute_path_for_writing tests.test_harness.HarnessTests.test_unittest_write_guard_rejects_symlink_parent_for_remove_rename_and_dir_fd`

Result: **PASS (exit 0)** — `Ran 2 tests in 0.119s`; `OK`.
