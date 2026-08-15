# P2 gate retry evidence

Retry date: 2026-08-14

| Command | Exit code | Markers / evidence | Result | Recommendation |
|---|---:|---|---|---|
| `python3 -m unittest tests.test_harness` | BLOCKED | Persistent session `98092` produced test progress and markers including `AUTO_UPDATE=off`, `AUTO_UPDATE=on`, and `VAULT_LINK_OK`; it was interrupted before a natural exit code. | BLOCKED/SIN VERIFICAR | Re-run to natural completion and capture exit code. |
| `python3 -m unittest tests.test_routing` | BLOCKED | Not started; no final output or exit code. | BLOCKED/SIN VERIFICAR | Run after the preceding gate completes. |
| `python3 -m unittest discover -s tests` | BLOCKED | Not started; no final output or exit code. | BLOCKED/SIN VERIFICAR | Run after the preceding gate completes. |
| `./ai/scripts/verify.sh` | BLOCKED | Not started; no final output or exit code. | BLOCKED/SIN VERIFICAR | Run after the preceding gate completes. |
| `./build.sh --check` | BLOCKED | Not started; no final output or exit code. | BLOCKED/SIN VERIFICAR | Run if time permits after required gates. |
| `git diff --check` | BLOCKED | Not started; no final output or exit code. | BLOCKED/SIN VERIFICAR | Run after the preceding gates. |

No source, test, configuration, product documentation, or state files were modified by this retry.

## Focused post-marker retry

Marker presence check:

`rg -n "SET_AGENTS_TEST_SANDBOXED" .` -> exit `0`; found in `tests/__init__.py` (lines 40 and 102).

Command:

`timeout 240s python3 -m unittest tests.test_harness.HarnessTests.test_guest_copy_scaffolds_and_verifies_portably`

Captured log: `/tmp/p2-guest.log`

Exit code: `0`

Tail:

```text
.
----------------------------------------------------------------------
Ran 1 test in 132.345s

OK
```

Result: PASS. No further suite was run.

## Full hardened verify retry

Command:

`python3 ai/scripts/heartbeat-run.py --interval 20 -- ./ai/scripts/verify.sh`

Log: `/tmp/p2-verify.log`

Result: `BLOCKED/SIN VERIFICAR`. The persistent session was monitored for approximately 36 minutes. It remained alive and emitted heartbeat lines, but produced no final exit code, `Ran...`, or `OK/FAILED` summary. The last substantive test output before the prolonged stall was `test_install_py_flags_codex_model_change_distinctly ... ok`; the final log lines were repeated `heartbeat-run: still running, 20s without output`. Process-tree inspection from the session namespace could not expose child process details beyond the wrapper. The session was then terminated with Ctrl-C under the requested controlled diagnostic procedure.

`git diff --check` -> exit `0` (no output).

## Full P2 gate second retry

Command: `python3 ai/scripts/heartbeat-run.py --interval 20 -- ./ai/scripts/verify.sh`

Log: `/tmp/p2-verify-final.log`

- Exit code: `0`
- Test summary: `Ran 1130 tests in 1809.496s`; `OK (skipped=4)`
- Gate markers: `GLOBAL_PORTABILITY_OK`, `CANONICAL_PATHS_OK`, `FEATURE_STATE_OK`, `VERIFY_PASS`
- `git diff --check`: exit `0`, no output
- Result: PASS

The full verify gate completed naturally; no repairs or state changes were made.

## Orchestrator persistent-session confirmation

The orchestrator reran `python3 ai/scripts/heartbeat-run.py --interval 20 -- python3 -m unittest tests.test_harness`
in a persistent session and polled it every 30 seconds. The command remained alive substantially
longer than the prior agent windows, progressed through many tests, and emitted one `E`, but did not
emit unittest's final summary or traceback before the verification budget expired. The test-only
process was then interrupted and exited `130`; this is **BLOCKED/SIN VERIFICAR**, not a test pass or
a diagnosed product failure. Observed sandbox paths under `/var/tmp/set-agentes-unittest-...` confirm
that the P2 relocation was active.

## Authorized extended rerun after fixture repair

With Federico's authorization for an extended execution window, the repaired command
`python3 ai/scripts/heartbeat-run.py --interval 20 -- python3 -m unittest tests.test_harness`
ran to natural completion in a persistent session. Exit code: **0**. Final result:
`Ran 466 tests in 820.976s` and `OK (skipped=2)`. The prior error was repaired by moving the
intentional build-drift mutation into a copied temporary checkout; the focused post-repair gate
and the complete module are both green.
