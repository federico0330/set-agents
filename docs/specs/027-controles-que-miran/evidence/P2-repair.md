# P2 repair evidence — fixture `build.sh --check`

Date: 2026-08-14

## Finding and root cause

`HarnessTests.test_build_check_detects_global_drift_and_names_the_file` deliberately wrote
`ROOT/Global/opencode/AGENTS.md`. P2's process-wide destination guard correctly rejects that
write because `ROOT` is the shared checkout, not the private unittest sandbox. Its `finally`
also tried to restore the shared file and was correctly rejected for the same reason.

## Repair

Changed only `tests/test_harness.py`. The fixture now copies the checkout into a
`TemporaryDirectory`, excluding `.git`, bytecode, and credential-shaped paths; it invokes the
same `bash <guest>/build.sh --check` command in that temporary copy. The clean check still must
return zero. The fixture then dirties only `<guest>/Global/opencode/AGENTS.md`, requires a
non-zero result, and requires the output to name `AGENTS.md`.

No guard exception or whitelist was added, and no production/build contract changed.

## Red / green evidence

| Stage | Command | Exit code | Evidence |
|---|---|---:|---|
| Red (before repair, guard active) | `python3 ai/scripts/heartbeat-run.py --interval 20 -- python3 -m unittest tests.test_harness.HarnessTests.test_build_check_detects_global_drift_and_names_the_file` | 1 | `PermissionError: test write outside private sandbox denied: /home/federico/SET-AGENTES/Global/opencode/AGENTS.md` at the deliberate write; the attempted finally restore was rejected too. |
| Green (after repair) | same command | 0 | The focused unittest completed successfully. Its fixture asserted a clean copied-tree `build.sh --check` result of 0, then a dirtied copied-tree result different from 0 containing `AGENTS.md`. |
| Diff hygiene | `git diff --check` | 0 | No whitespace errors. |

## Scope and next gate

Owned changes are limited to test fixtures (`tests/test_harness.py`, `tests/test_routing.py`,
and `tests/test_provider_registry.py`) and this evidence file. The shared checkout,
`tests/__init__.py`, `build.sh`, production files, P3, and P4 were not changed. Next: package
gate runner should execute the prescribed P2 gates from the context pack, beginning with the
focused harness test and then the package/global commands available in the project.

## Follow-up repair: explicit provider fixtures

The subsequent `verify.sh` run completed 1125 tests but exposed four fixtures that were still
implicitly using machine state after P2 relocated `HOME`:

| Red gate result | Root cause | Repair |
|---|---|---|
| `tests/test_routing.py:3422` and `:3451`: `PROVIDER_UNAUTHENTICATED` | The terminal-usage CLI fixtures called the real `codex`/`claude`/`opencode` probes through inherited `PATH`. | Each fixture now prepends its existing local `_probe_stubs()` directory. |
| `tests/test_routing.py:5973`: no selected provider | The end-to-end preference test expected two providers authenticated on the developer machine. | It now declares those same two providers through `_probe_stubs()` and the temporary routing/state roots. |
| `tests/test_provider_registry.py:474`: `--provider-remove ollama` non-zero | Install seeded `home/.local/state/set-agentes`, but the CLI inherited the suite's unrelated `SET_AGENTS_STATE`. | The removal invocation names the state directory below that fixture's `home`. |

Focused green command (exit 0):

```sh
python3 ai/scripts/heartbeat-run.py --interval 20 -- python3 -m unittest -v \
  tests.test_routing.RoutingTests.test_route_terminal_usage_flows_from_the_cli_into_the_stored_row \
  tests.test_routing.RoutingTests.test_route_terminal_large_but_valid_usage_still_closes_the_run \
  tests.test_routing.RoutingTests.test_model_preference_production_plumbing_end_to_end_via_real_cli \
  tests.test_provider_registry.InstallProviderRenderTests.test_removed_provider_does_not_come_back_on_a_later_install
```

This follow-up changes tests only; it neither reads real credentials nor changes the P2 guard or
production behavior.

## Consolidated-review checkpoint — P2-F01 / P2-F02 / P2-F03

Date: 2026-08-14. No long suite was started for this repair pass.

- **P2-F01 (high):** the Python audit hook does not propagate into arbitrary child processes.
  Feasibility check: `/usr/bin/bwrap` is available. Planned test-infrastructure boundary: create a
  private checkout inside the unittest sandbox and run descendants in Bubblewrap with the host
  filesystem read-only, the private unittest sandbox writable, and that checkout mounted at the
  canonical repository path. Thus a child can read/run the repository but any apparent write to
  its root lands only in the private copy; writes to real home/repository paths fail at the OS
  boundary. A regression child will attempt an absolute external `os.open(..., O_WRONLY)` and
  prove failure before mutation.
- **P2-F02 (high):** current `remove`/`rename` protection keeps the whole path lexical when the
  final entry must not be followed, leaving an escaping parent symlink unresolved. Planned fix:
  resolve parent components and append only the final lexical name; cover symlink-parent and
  `dir_fd` removal/rename paths without an external mutation.
- **P2-F03 (medium):** `SET_AGENTS_STATE` is suite-global even when a fixture changes `HOME`.
  Existing named fixture repair showed the required pattern; this pass will centralize/cohere the
  temporary state per explicit fixture home and assert the resulting state location.

No product/config/credential/state file has been modified by this checkpoint.

## Consolidated repair progress — checkpoint 2

### Implemented partial changes

| Finding | Test-infrastructure change | Focused result |
|---|---|---|
| P2-F01 | `tests/__init__.py` now copies the checkout under the per-run sandbox and wraps descendant `subprocess.Popen` calls in Bubblewrap: host root is `ro-bind`, only the private sandbox is writable, and the private checkout is mounted at the canonical repository path. | PASS: `test_unittest_descendant_cannot_open_an_external_absolute_path_for_writing` (an `os.open('/etc/hosts', O_WRONLY)` child fails and `/etc/hosts` bytes remain unchanged); `test_unittest_descendant_preserves_fixture_path_inside_private_sandbox` also passes. |
| P2-F02 | `tests/__init__.py` resolves a path's parent before retaining its final lexical segment for remove/rename. | PASS: `test_unittest_write_guard_rejects_symlink_parent_for_remove_rename_and_dir_fd`; direct remove, `dir_fd` remove, and `dir_fd` rename through an escaping parent symlink raise before mutation. |
| P2-F03 | Descendant environment coalesces a fixture-provided `HOME` with a state path below that home whenever it would otherwise inherit the suite-global state. | PASS: `test_unittest_child_home_implicitly_moves_state_to_that_fixture_home`. |

Focused command and result:

```sh
python3 ai/scripts/heartbeat-run.py --interval 20 -- python3 -m unittest -v \
  tests.test_harness.HarnessTests.test_unittest_descendant_cannot_open_an_external_absolute_path_for_writing \
  tests.test_harness.HarnessTests.test_unittest_write_guard_rejects_symlink_parent_for_remove_rename_and_dir_fd \
  tests.test_harness.HarnessTests.test_unittest_child_home_implicitly_moves_state_to_that_fixture_home
# exit 0, Ran 3 tests, OK
```

### Current blocker within this repair attempt

The pre-existing routing focal fixtures were rerun after the boundary:

```sh
python3 ai/scripts/heartbeat-run.py --interval 20 -- python3 -m unittest -v \
  tests.test_routing.RoutingTests.test_route_terminal_usage_flows_from_the_cli_into_the_stored_row \
  tests.test_routing.RoutingTests.test_route_terminal_large_but_valid_usage_still_closes_the_run \
  tests.test_routing.RoutingTests.test_model_preference_production_plumbing_end_to_end_via_real_cli \
  tests.test_provider_registry.InstallProviderRenderTests.test_removed_provider_does_not_come_back_on_a_later_install
```

Result: exit 1; the provider-registry test passed, but all three routing tests returned
`PROVIDER_UNAUTHENTICATED`. Their fixture-local probe binaries are present and a separate nested
child-PATH regression passes, yet `probes.log` was not created by routing composition, indicating
that the mounted-checkout descendant is not reaching the expected live-probe path. This must be
resolved before P2-F01/F03 can be declared repaired; no suite-wide gate was started.

## Consolidated repair final evidence — P2-F01 / P2-F02 / P2-F03

| Finding | Minimal repair | Focused verification |
|---|---|---|
| P2-F01 (high) | `tests/__init__.py` creates a private checkout and wraps descendants with Bubblewrap (`ro-bind /`, writable private sandbox, private checkout at the canonical root). The first attempt made `/dev/null` unavailable because it inherited the read-only host `/dev`; catalog probes open `subprocess.DEVNULL` and therefore failed before invoking a stub. Adding Bubblewrap's private `--dev /dev` restores the device without a writable host bind. | `test_unittest_descendant_cannot_open_an_external_absolute_path_for_writing`; `test_unittest_descendant_preserves_fixture_path_inside_private_sandbox`; `tests.test_routing.RoutingTests.test_route_probe_fixture_reaches_stubs_inside_descendant_boundary` all pass. The last one proves nested routing probes find and execute fixture-local stubs inside the boundary. |
| P2-F02 (high) | `_resolved_write_target(..., follow_final_symlink=False)` now resolves the parent and appends only the lexical final name. | `test_unittest_write_guard_rejects_symlink_parent_for_remove_rename_and_dir_fd` passes for direct remove, `dir_fd` remove, and `dir_fd` rename through an escaping parent symlink, before mutation. |
| P2-F03 (medium) | Child environment derives `SET_AGENTS_STATE` below a fixture's overridden `HOME` rather than retaining the suite-global state. Routing and provider fixtures also explicitly declare their local stubs/state. | `test_unittest_child_home_implicitly_moves_state_to_that_fixture_home` passes; provider-removal focal passes. |

Final routing/provider focal command completed naturally (captured at
`/tmp/p2-routing-focals.FrTc0F.log`):

```sh
python3 ai/scripts/heartbeat-run.py --interval 20 -- python3 -m unittest -v \
  tests.test_routing.RoutingTests.test_route_terminal_usage_flows_from_the_cli_into_the_stored_row \
  tests.test_routing.RoutingTests.test_route_terminal_large_but_valid_usage_still_closes_the_run \
  tests.test_routing.RoutingTests.test_model_preference_production_plumbing_end_to_end_via_real_cli \
  tests.test_provider_registry.InstallProviderRenderTests.test_removed_provider_does_not_come_back_on_a_later_install
```

Result: **exit 0 — Ran 4 tests in 77.522s — OK**. No long suite was executed for this repair.

## Hardened-gate follow-up

Root causes and repairs, all in `tests/__init__.py`:

- Bubblewrap's `ro-bind /` made literal `/tmp` read-only. Descendants now receive a distinct
  per-run writable directory mounted at `/tmp`; it remains within `_TEST_SANDBOX`, so no host
  temporary area or checkout becomes writable.
- A copied guest harness already resides below `_TEST_SANDBOX`. Rebinding a second checkout over
  that guest root was invalid under Bubblewrap's mount setup. The wrapper now detects that case
  and uses the existing private guest subtree; non-guest runs still mount the private checkout at
  the canonical root.
- Bubblewrap reports a SIGKILL child as exit `137`; `_SandboxPopen` translates conventional
  `128 + signal` values back to the `subprocess.Popen` negative-signal contract.

Focused verification completed: `tests.test_routing.RoutingTests.test_crash_between_begin_and_commit_preserves_consistency`
passed, preserving `returncode == -signal.SIGKILL`. The combined guest focal was still running
when its execution channel ended, so it is deliberately not claimed as pass here. `git diff --check`
completed with exit 0. No long suite was run.

## Hardened-gate repair — installer fixture stall

### Root cause

The first test after `test_install_py_flags_codex_model_change_distinctly` in the current
`HarnessTests` order is `test_install_sh_creates_set_agents_link`. Its first,
`install.sh --dry-run`, invocation is not the stall. A trace with the fixture's exact
`HOME` and stub `PATH` completed through `BOOTSTRAP_DONE` with exit 0 in about 2.5 seconds.

The fixture's next two invocations use `--skip-deps --skip-auth --no-install --yes`. Although
`--no-install` prevents CLI installation, `install.sh` still warms the Pi lane by executing
`pnpm dlx --package <pinned Pi package> pi --version`. The fixture declared stubs for
`opencode`, `claude`, and `codex`, but not for `pnpm`, so it fell through to the machine pnpm.
The Bubblewrap trace stopped exactly at that `pnpm dlx` command after 30 seconds. The same
command run through the original (non-Bubblewrap) Popen completed with exit 0, confirming this
is an undeclared host/network dependency in the fixture rather than a writable-mount or cwd
failure in the boundary.

### Minimal repair

`tests/test_harness.py` now includes `pnpm` in this fixture's explicit stub set. The normal
stub returns immediately for the warm-up probe, preserving the test's actual contract (creation
and idempotence of `~/.local/bin/set-agents`) without contacting the machine runtime or network.
The Bubblewrap boundary, audit guard, private `/tmp`, guest marker, and signal assertion are
unchanged.

### Focused evidence

| Command | Exit | Result |
|---|---:|---|
| exact wrapped `bash -x install.sh --dry-run` with `_bootstrap_env(..., (opencode, claude, codex))` | 0 | Trace reached `BOOTSTRAP_DONE`; no stall. |
| exact wrapped `bash -x install.sh --skip-deps --skip-auth --no-install --yes` before repair, bounded only for diagnosis | 0 (diagnostic process) | Child timed out after 30 seconds; final traced command: `pnpm dlx --package @earendil-works/pi-coding-agent@0.84.0 pi --version`. |
| same exact command through `_ORIGINAL_POPEN` (native comparison) | 0 | Completed through `BOOTSTRAP_DONE`, demonstrating the host pnpm fallback. |
| `timeout 60s python3 -m unittest -v tests.test_harness.HarnessTests.test_install_sh_creates_set_agents_link` after repair | 0 | `Ran 1 test in 2.653s — OK`. |

No long suite was run for this focused repair. Next applicable gate: rerun the hardened harness
sequence/package gate outside this repair task.
