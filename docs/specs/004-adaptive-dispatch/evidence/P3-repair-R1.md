# P3-pi-lane — repair R1 (security-auditor findings)

Date: 2026-07-27. Baseline for this pass: the uncommitted P3-pi-lane implementation (T-301..T-305,
`docs/specs/004-adaptive-dispatch/evidence/P3-implementation.md`) on top of `ced2caa`. Scope: exactly the
six findings below (SEC-A01..SEC-A05, PKG-N01, PKG-N02) from the consolidated security-auditor review. No
opportunistic refactors; `service.py` untouched by this pass; `routes.v1.toml`/`roles.tsv`/
`Global/_canonical/agents/**` untouched (read-only per the package's owned_paths).

## SEC-A01 — HIGH — untrusted `task` argument injection — FIXED

**File**: `ai/scripts/set_agents_spawn.py`, `spawn()` (now ~L207-237, guard added at L231-237).

**Live confirmation of the vulnerability, pinned pi 0.81.1** (before writing the fix): a task of exactly
`--offline` given as the trailing positional is silently consumed by pi's own CLI parser as a recognized
boolean flag — it never reaches pi as message text (the process starts a session and returns exit 0 with
zero conversation, confirmed via `pnpm dlx --package @earendil-works/pi-coding-agent@0.81.1 pi --print
--mode json --no-session --no-extensions --tools read,grep,find,ls --append-system-prompt role.md
"--offline" < /dev/null`, EXIT 0, one `session` event, nothing else). Separately, `--model ... "--tools=bash,edit,write"`
prints `Error: Unknown option: --tools` (pi's parser does not accept the `=`-form for that flag, but still
attempts to parse the trailing token as an option rather than treating it as message text) — and a bare
`--` end-of-options sentinel before the task is REJECTED outright by pinned pi (`Error: Unknown options: --,
--tools`), confirming the "preferred: fail-closed" path in the finding is the only viable one; `--` cannot
be used at all.

**Fix**: `spawn()` now fails closed BEFORE building the argv or starting any subprocess whenever
`task.lstrip().startswith("-")`, returning `("failure", {"reason": "TASK_LOOKS_LIKE_FLAG"})`. This covers
every hostile shape found live (`--tools=...`, `--offline`, a bare `-x`), because ANY task pi's parser could
possibly consume as an option must itself start with `-`.

**Tests**: `tests/test_routing.py::test_spawn_refuses_a_task_that_lexically_looks_like_a_flag` — asserts
`spawn()` refuses `"--tools=bash,edit,write"`, `"-x"`, `"--offline"`, and a leading-whitespace variant, and
that `subprocess.run` is **never called** for any of them (proving refusal happens before any child starts,
not just that the flags "win" — the reviewer's exact ask). An ordinary task is proven unaffected in the same
test.

**Live proof (this repair pass, real pinned pi, openai-codex only, unmocked)**:
```
outcome: failure detail: {'reason': 'TASK_LOOKS_LIKE_FLAG'} elapsed_seconds: 0.0
```
(fully real `spawn()` call, nothing mocked — zero elapsed time confirms no subprocess/pnpm/network was ever
touched) vs. the legitimate control call immediately after, same process, unmocked:
```
outcome: success detail: {'model': 'openai-codex/gpt-5.6-luna', 'usage': {..., 'cost': {'total': 0.002417}}} elapsed_seconds: 6.21
```
proving the fix is precise (hostile tasks refused instantly, ordinary tasks unaffected).

## SEC-A02 — MEDIUM — `GUARD_TOOLS_CODE_RW` re-opens depth-0 escape — FIXED

**Files**: `ai/scripts/set_agents_spawn.py` (`GUARD_TOOLS_CODE_RW` comment ~L71-78; `spawn()`'s argv ~L243-246;
`route_and_spawn()` signature ~L304-305 and body ~L347-349); `docs/adr/0007-pi-lane.md` (new "Enmienda —
repair R1" section); `docs/architecture/overview.md` (P3 section updated).

**Fix, two parts**:
1. `route_and_spawn()` no longer has a `guard_tools` parameter at all — it unconditionally calls
   `spawn(..., guard_tools=GUARD_TOOLS_READONLY, ...)`. `main()` already never exposed a `--guard-tools` CLI
   flag, so with this change `GUARD_TOOLS_CODE_RW` is unreachable from either of this package's real
   lifecycle entry points; only a caller of the low-level `spawn()` primitive directly (out-of-package,
   e.g. a future package's own tests) can still select it. Documented in a code comment next to
   `GUARD_TOOLS_CODE_RW` and in ADR-0007's new amendment section: widening requires a bash-sandbox story
   that prevents a code-rw child's `bash` tool from re-invoking `pnpm dlx ... pi ...` and spawning its own
   pi children (which `--no-extensions` does nothing to stop, since it only blocks pi's in-process
   pi-subagents extension, not a shell re-exec of the pi binary itself).
2. `--no-context-files` is now unconditional in `spawn()`'s argv (alongside `--no-session`/
   `--no-extensions`), verified live that pinned pi 0.81.1 supports it (`pi --help` lists
   `--no-context-files, -nc  Disable AGENTS.md and CLAUDE.md discovery and loading`) — a caller-passed
   `spawn_cwd` can no longer auto-load its own project-local AGENTS.md/CLAUDE.md config into the child.

**Tests**:
- `test_spawn_guard_flags_are_unconditional_and_default_tools_are_readonly` (extended) — asserts
  `--no-context-files` is present at both the default and the (still-reachable-from-`spawn()`-directly)
  code-rw tier.
- `test_route_and_spawn_never_exposes_a_code_rw_override_and_always_spawns_readonly` (new) — asserts calling
  `route_and_spawn(..., guard_tools=GUARD_TOOLS_CODE_RW)` raises `TypeError` (no such parameter exists), and
  that the internal `spawn()` call `route_and_spawn` makes always passes `guard_tools=GUARD_TOOLS_READONLY`.

## PKG-N01 / SEC-A03 — LOW — orphan run on lifecycle-CLI exception — FIXED

**File**: `ai/scripts/set_agents_spawn.py`, `route_and_spawn()` (~L347-373).

**Fix**: the dispatch → spawn → terminal sequence (everything after `run_id` is authorized) now runs inside
one `try/except Exception` block. Any exception — a `_run_app_cli` subprocess surprise
(`TimeoutExpired`/`OSError` from the `--route-dispatched` or `--route-terminal` calls) or anything else —
is caught, and a best-effort `--route-terminal <run_id> failure` close is attempted (itself wrapped in its
own `try/except Exception: pass`, so it can never raise back out), before returning
`{"status": "failure", "run_id": ..., "reason": "ORCHESTRATION_EXCEPTION", "detail": ...}`. This covers both
call sites the finding named (the original `--route-dispatched` at the old L249 and `--route-terminal` at
the old L258) plus the exception-safety of the close call itself.

**Tests**:
- `test_route_and_spawn_closes_run_as_failure_when_a_lifecycle_cli_call_raises` (new) — `--route-dispatched`
  raises `subprocess.TimeoutExpired`; asserts `spawn()` is never called (the child never starts), the
  best-effort `--route-terminal ... failure` is attempted exactly once, and the result reports
  `status="failure"`, `reason="ORCHESTRATION_EXCEPTION"`, with the correct `run_id`.
- `test_route_and_spawn_survives_a_terminal_cli_exception_after_a_successful_spawn` (new) — the child
  `spawn()` genuinely succeeds, but every `--route-terminal` attempt raises `OSError`; asserts the function
  never raises, reports `status="failure"` (never a false "success" once the close itself is uncertain), and
  that the best-effort close was attempted a second time (2 total `--route-terminal` attempts: the normal
  one plus the exception-handler's retry).

## SEC-A04 — LOW (DiD) — model-fallback not detected — FIXED

**File**: `ai/scripts/set_agents_spawn.py`, `_model_fallback_marker()` (new, ~L182-199) and its call site
inside `spawn()` (~L266-268).

**Investigation** (against the pinned pi 0.81.1 package source, `dist/main.js` / `dist/core/sdk.js`): the
SDK's `modelFallbackMessage` (from `createAgentSession`) is passed ONLY into `InteractiveMode` — `main.js`'s
non-interactive branch (`runPrintMode`, used by `--print --mode json`, the only mode this spawner uses)
never receives or threads it into the JSON event stream on stdout. There is therefore no literal
`modelFallbackMessage`-shaped event to scan for in the stream this spawner actually parses. However, pi's
own CLI model resolver (`resolveCliModel`/`buildFallbackModel` in `dist/core/model-resolver.js`) DOES emit
an equivalent plain-text diagnostic to **stderr** (via `reportDiagnostics`/`console.error`) whenever it
silently substitutes a different real model's underlying config under a requested-but-unmatched id
(`"Using custom model id."`) or fails to restore a saved session's model (`"Could not restore model ..."`).
Live-confirmed (`--model openai-codex/not-a-real-model`):
```
STDOUT: {"role":"assistant", ..., "provider":"openai-codex","model":"not-a-real-model", ...}
STDERR: Warning: Model "not-a-real-model" not found for provider "openai-codex". Using custom model id.
```
— the assistant message still ECHOES the requested (fake) id, so the existing `observed == target_id` check
alone would not catch a case where the substituted model's backend happened to accept the request instead
of rejecting it (this instance was additionally caught by the pre-existing `stopReason == "error"` check,
but that is coincidental to this specific provider's remote validation, not a property of the fallback
mechanism itself).

**Fix**: `spawn()` now scans `proc.stderr` for these markers on EVERY spawn (not only the crash path) and,
if found, returns `("model_mismatch", {"expected": target_id, "observed": target_id, "reason":
"PI_MODEL_FALLBACK", "detail": ...})` — never trusting a matching echoed model as proof nothing was
substituted.

**Test**: `test_spawn_detects_stderr_model_fallback_marker_and_never_trusts_the_echoed_model` (new) — the
shared stub gains a `SIMULATE:fallback` task that prints the exact live-observed warning to stderr while
still echoing a MATCHING model/provider on stdout (proving the new stderr scan, not the pre-existing
observed-mismatch check, is what catches it); asserts `outcome == "model_mismatch"` and
`detail["reason"] == "PI_MODEL_FALLBACK"`.

## SEC-A05 — LOW (DiD) — raw pi stderr in persisted envelope — FIXED

**File**: `ai/scripts/set_agents_spawn.py`, `_redact()` + `_SECRET_PATTERNS` (new, ~L83-96), applied at all
three text-detail sites: the crash-stderr capture (~L265, was `proc.stderr.strip()[-2000:]`, now
`_redact(proc.stderr.strip())[-500:]`), the subprocess-exception detail (~L254, `str(exc)`), and the
turn-error `errorMessage` (~L281).

**Fix**: `_redact()` substitutes `[REDACTED]` for common secret shapes (`sk-...` style keys, `Bearer <token>`,
and `api_key=`/`token=`/`secret=`/`password=`-style assignments, case-insensitive) before truncating every
persisted/returned text field, and the crash-stderr cap was additionally reduced from 2000 to 500 chars —
still enough for debugging (reason/exit-code/first-500-chars) without a raw dump of a child process that
inherits the full `os.environ`.

**Test**: `test_spawn_never_persists_raw_stderr_secrets` (new) — the stub's `SIMULATE:crash-with-secret`
task exits 1 after printing a fake `Authorization: Bearer sk-ant-...` string to stderr; asserts the returned
`detail["stderr"]` does NOT contain the raw secret substring and DOES contain `[REDACTED]`.

## PKG-N02 — LOW — probe timeout vs doctor cold-pnpm — FIXED (real fix, not a doc note)

**File**: `ai/scripts/routing_core/catalog.py`, `PI_PROBE_MIN_TIMEOUT_SECONDS = 60.0` (new constant, ~L26-34)
and its use in `_probe_pairs()` (~L263-266).

**Fix**: `_probe_pairs()` now computes `pair_timeout = max(timeout, PI_PROBE_MIN_TIMEOUT_SECONDS) if runtime
== "pi" else timeout` per pair before running its subprocess(es) — aligned with
`set_agents_spawn.DOCTOR_TIMEOUT_SECONDS` (60.0), which already documents the cold-`pnpm-dlx` allowance.
Only the `pi` pairs get the floor; the other three runtimes' probes keep whatever timeout the caller passed
(no slowdown to the already-fast codex/claude-code/opencode probes), and `probe_inventory`'s own default
(20.0, unchanged) is still what every other runtime effectively uses.

**Test**: `test_probe_pi_pair_timeout_is_raised_to_the_cold_pnpm_allowance` (new) — mocks
`subprocess.run` to capture the `timeout=` kwarg per call; probes `[("pi","openai-codex"),
("codex","openai-codex")]` with an explicit `timeout=5.0`; asserts the pi pair's call received
`timeout >= PI_PROBE_MIN_TIMEOUT_SECONDS` (60.0) while the codex pair's call received exactly `5.0`.

## Local validation (real output, this repair pass)

1. **`python3 -m unittest discover -s tests -v`** → `Ran 172 tests ... OK` (grew from 165 baseline by
   exactly the 7 new tests listed above: `test_spawn_refuses_a_task_that_lexically_looks_like_a_flag`,
   `test_spawn_detects_stderr_model_fallback_marker_and_never_trusts_the_echoed_model`,
   `test_spawn_never_persists_raw_stderr_secrets`,
   `test_route_and_spawn_never_exposes_a_code_rw_override_and_always_spawns_readonly`,
   `test_route_and_spawn_closes_run_as_failure_when_a_lifecycle_cli_call_raises`,
   `test_route_and_spawn_survives_a_terminal_cli_exception_after_a_successful_spawn`,
   `test_probe_pi_pair_timeout_is_raised_to_the_cold_pnpm_allowance`). No existing test was weakened;
   `test_spawn_guard_flags_are_unconditional_and_default_tools_are_readonly` was strengthened (added
   `--no-context-files` assertions) — every other pre-existing test is byte-identical to the pre-repair
   version. Wall time 160.8s (dominated by the real live `pi`/`pnpm` doctor CLI subprocess test that was
   already part of the baseline).
2. **`./build.sh --check`** → `CHECK_PASS: generated and validated profile go-zen`.
3. **`python3 -m py_compile ai/scripts/*.py ai/scripts/routing_core/*.py tests/*.py`** → clean, no output.
4. **`./ai/scripts/verify.sh`** → `Ran 172 tests in 156.6s ... OK` then `VERIFY_PASS` (drift-vs-fresh-build
   check clean; `git status --short Global` empty).
5. **`git diff --check`** → exit 0, no whitespace errors.
6. **SEC-A01 live proof** — see above (real pinned pi 0.81.1, openai-codex only, unmocked): hostile task
   refused in 0.0s (no subprocess/network touched), legitimate control task succeeded normally
   (`gpt-5.6-luna`, cost $0.002417). No anthropic/Claude live calls were made anywhere in this repair pass
   (Claude quota exhaustion noted in the original implementation evidence was respected).

## Findings NOT in scope of this pass

None — all six findings in the repair brief (SEC-A01, SEC-A02, PKG-N01/SEC-A03, SEC-A04, SEC-A05, PKG-N02)
are addressed above. `service.py` was not touched (no finding required it). `routes.v1.toml`/`roles.tsv`/
`Global/_canonical/agents/**` were not touched (read-only, no finding required it).
