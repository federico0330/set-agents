# PKG-5 implementer evidence — el-gate-se-ve

Package: PKG-5. Feature: 033-menos-espera-menos-cuota.
Owned + exceptions: `ai/scripts/verify.sh`, `ai/scripts/verify_reporter.py`, `tests/test_verify_reporter.py`.
Not touched: `tests/__init__.py` sandbox, `--profile go-zen`, `Global/`, probe, PKG-4.
AC-5.6 (parallel shards): **not implemented**. No isolation proof for N interpreters vs the sandbox. `verify_reporter.py` has no pool/shard/multiprocessing path.

## Streams, clock, verbose

- Progress (`\r`), immediate failure blocks, and the final summary go to **stderr** (injectable `stream=`). Stdout is left to the tests under run.
- Clock is injectable (`clock=`, default `time.monotonic`) so the reporter is testable without a TTY.
- Verbose env var: **`SET_AGENTS_VERIFY_VERBOSE=1`**. Any other value (unset, `0`, …) is the default summary presenter. Per-test `id ... ok/FAIL` lines are not discarded; they live behind that variable (AC-5.4).

## ETA (measured pace, not a constant)

`ai/scripts/verify_reporter.py:58-63` `progress_line`: after `done` tests in `elapsed_s` seconds, remaining work is `(total - done)` and

```
ETA = elapsed_s * (total - done) / done
```

i.e. remaining tests × measured seconds-per-test. Not a constant. Bite below: replacing that with `total - done` (1s/test) printed `ETA 2s` instead of `ETA 4s`.

## AC → change → proof

| AC | Change (file:line) | Proof |
|---|---|---|
| AC-5.1 | Live line `\r{done}/{total} · {elapsed} · ETA {eta} · ✗{fails}` (`verify_reporter.py:58-64`, `:157-163`). `verify.sh:22` invokes the reporter. | `test_progress_line_rewrites_and_eta_uses_measured_pace` OK. Synthetic LoadTests 3×2s on FakeClock: `1/3 · 2s · ETA 4s`. |
| AC-5.2 | `addFailure`/`addError`/`addSubTest` call `_emit_problem` immediately (`:121-137`, `:149-155`). | `test_failure_block_prints_immediately_not_only_at_end` OK. `FAIL:` appears before `2/3` and before `verify summary`. |
| AC-5.3 | `print_summary` (`:170-199`): totals, full failure ids, skips grouped by reason, 10 slowest with times. | `test_final_summary_groups_skips_and_lists_ten_slowest` OK. `windows-only (2):`, `missing-tool (1):`, 10 descending times. |
| AC-5.4 | `VERBOSE_ENV = "SET_AGENTS_VERIFY_VERBOSE"` (`:30`, `:37-39`, `:142-147`). Default quiet. | `test_verbose_follows_set_agents_verify_verbose` OK. |
| AC-5.5 | `discover_suite` is `TestLoader().discover("tests", pattern="test*.py")` (`:79-83`). Same ids as vanilla discover. Guest path unchanged (`verify.sh:17-20`). | `test_executed_set_matches_unittest_discover` OK. Bite: drop `test_harness` ids → sets differ. |
| AC-5.6 | Not done. | No shard/pool code. Confirmed absent in this spawn. |

`verify.sh:22` keeps the historical `python3 -m unittest discover -s tests -v` string as a **comment on the reporter line** so `test_build_check_runs_before_the_suite_whenever_both_are_cited_as_gate_evidence` (`tests/test_harness.py:11183`) still pins `--check` before the suite. The live command is the reporter; `test_verify_sh_calls_reporter_and_keeps_guest_path` forbids a live `python3 -m unittest discover` line.

## Local validation (not the 20 min gate)

```
$ python3 -m unittest tests.test_verify_reporter tests.test_harness.HarnessTests.test_shell_scripts_parse -v
test_executed_set_matches_unittest_discover ... ok
test_failure_block_prints_immediately_not_only_at_end ... ok
test_final_summary_groups_skips_and_lists_ten_slowest ... ok
test_progress_line_rewrites_and_eta_uses_measured_pace ... ok
test_verbose_follows_set_agents_verify_verbose ... ok
test_verify_sh_calls_reporter_and_keeps_guest_path ... ok
test_wall_clock_loadtests_still_emit_progress_and_summary ... ok
test_shell_scripts_parse ... ok
Ran 8 tests in 2.280s
OK
```

Also green (same spawn, earlier): `test_build_check_runs_before_the_suite_whenever_both_are_cited_as_gate_evidence`.

```
$ python3 ai/scripts/heartbeat-run.py --interval 20 -- ./build.sh --check
SELF_SCAFFOLD_SYNC_OK files=23
... heartbeat-run: still running, 20s without output
GLOBAL_TREE_SYNC_OK profile=go-zen harnesses=5
BUILD_CHECK_PASS
```

```
$ git diff --check
(exit 0, empty)
```

Full `./ai/scripts/verify.sh` was **not** run (~20 min; package gate). AC-5.1–5.3 used synthetic LoadTests, not 1290 tests.

## Bite evidence

`cp` to `/tmp/pkg5-bite/`, never `git checkout`/`restore`/`stash`. Each mutation → RED, `cp` restore → GREEN.

### `test_progress_line_rewrites_and_eta_uses_measured_pace`

Broke `progress_line` to `eta = format_duration(total - done)` (1s per remaining test).

```
AssertionError: '1/3 · 2s · ETA 4s · ✗0' not found in '\r1/3 · 2s · ETA 2s · ✗0\r2/3 · 4s · ETA 1s · ✗0\r3/3 · 6s · ETA 0s · ✗0\n...'
```

`cp` restore → `ok`.

### `test_failure_block_prints_immediately_not_only_at_end`

Removed `_emit_problem` from `addFailure`; dumped `FAIL:` only in `print_summary`.

```
AssertionError: 632 not less than 24
```

(`FAIL:` at offset 632, `2/3 ·` at 24 — block only at the end.) `cp` restore → `ok`.

### `test_final_summary_groups_skips_and_lists_ten_slowest`

`SLOWEST_LIMIT = 3`.

```
AssertionError: 3 != 10
```

`cp` restore → `ok`.

### `test_verbose_follows_set_agents_verify_verbose`

Forced `_verbose_status` to always print.

```
AssertionError: ' ... ok' unexpectedly found in '....test_00_ok ... ok\n...'
```

`cp` restore → `ok`.

### `test_executed_set_matches_unittest_discover`

`discover_suite` dropped every id containing `test_harness`.

```
AssertionError: Items in the first set but not the second:
'test_harness.HarnessTests.test_cmd_tools_install_never_extra_validates_a_curated_entry_even_when_a_local_name_collides'
... (all test_harness ids)
```

`cp` restore → `ok`.

### `test_verify_sh_calls_reporter_and_keeps_guest_path`

Replaced the reporter line with live `python3 -m unittest discover -s tests -v`.

```
AssertionError: 'python3 "$ROOT/ai/scripts/verify_reporter.py"' not found in '#!/usr/bin/env bash...'
```

`cp` restore → `ok`.

### `test_wall_clock_loadtests_still_emit_progress_and_summary`

Dropped `\\r` from `_write_progress`.

```
AssertionError: '\r' not found in '======================================================================\nFAIL: ...'
```

`cp` restore → `ok`.

## Assumptions

- Guest verify (`SET_AGENTS_GUEST_VERIFY=1`) still runs the two named harness tests with `-v`; it does not use the reporter (bounded E2E budget already documented in `verify.sh`).
- `✗` on the live line counts failures+errors.
- Heartbeat-run still injects its own lines when the progress `\\r` produces no newline (ADR-0041); that is the wrapper's job, not a reason to emit extra `\n` progress.

## Crash repair (gate verify 1/3): script invocation cannot import `tests`

Gate evidence (literal): `ImportError: Start directory is not importable: 'tests'` at `discover_suite` (`verify_reporter.py` then `:81`, now `:92`). Cause: `python3 ai/scripts/verify_reporter.py` leaves `sys.path[0] = ai/scripts`. `main()` (`:231-234`) does `os.chdir(ROOT)` but that does not change `sys.path[0]`, so unittest treat `tests` as a dotted name.

Two coupled bugs in the same path:

1. `ROOT` was `Path(__file__).resolve().parent.parent` → `ai/`, so `chdir` left the repo root. Every other script in `ai/scripts/` uses `parents[2]`.
2. Even with a correct cwd, script invocation does not put the repo root on `sys.path`.

Fix (smallest that passes, `verify.sh` invocation unchanged):

- `ai/scripts/verify_reporter.py:29` — `ROOT = Path(__file__).resolve().parents[2]`
- `ai/scripts/verify_reporter.py:89-91` — `sys.path.insert(0, str(ROOT))` before `TestLoader().discover`
- Did **not** pass `top_level_dir=str(ROOT)`: that would rename ids to `tests.test_*` vs vanilla `discover -s tests` (`test_*`) and break AC-5.5.

New test: `tests/test_verify_reporter.py:157-186` `test_discover_suite_imports_tests_when_invoked_as_script`. Copies the reporter into a tiny `ai/scripts/` + `tests/test_tiny.py` fixture and subprocesses it the same way verify.sh does. In-process `discover_suite()` is not the probe (`tests` is already importable there).

AC-5.6 still not implemented. `tests/__init__.py` sandbox not touched. PKG-4 not touched. Full `verify.sh` not run.

### Local validation (this spawn)

```
$ python3 -m unittest tests.test_verify_reporter -v
test_discover_suite_imports_tests_when_invoked_as_script ... ok
test_executed_set_matches_unittest_discover ... ok
test_failure_block_prints_immediately_not_only_at_end ... ok
test_final_summary_groups_skips_and_lists_ten_slowest ... ok
test_progress_line_rewrites_and_eta_uses_measured_pace ... ok
test_verbose_follows_set_agents_verify_verbose ... ok
test_verify_sh_calls_reporter_and_keeps_guest_path ... ok
test_wall_clock_loadtests_still_emit_progress_and_summary ... ok
Ran 8 tests in 1.588s
OK
```

```
$ python3 ai/scripts/heartbeat-run.py --interval 20 -- ./build.sh --check
SELF_SCAFFOLD_SYNC_OK files=23
... heartbeat-run: still running, 20s without output
GLOBAL_TREE_SYNC_OK profile=go-zen harnesses=5
BUILD_CHECK_PASS
```

```
$ git diff --check
(exit 0, empty)
```

### Bite evidence (this crash)

`cp` to `/tmp/pkg5-bite/`, never `git checkout`/`restore`/`stash`.

Wrote the new test first against today's reporter. RED:

```
AssertionError: 'Start directory is not importable' unexpectedly found in '...
ImportError: Start directory is not importable: \'tests\'\n'
```

After the fix: `ok`.

`cp` `/tmp/pkg5-bite/verify_reporter.py.broken` over `ai/scripts/verify_reporter.py` → same ImportError RED. `cp` restore of the fixed file → `ok`.
