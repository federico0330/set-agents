# P3-pi-lane — implementation evidence (T-301..T-305)

Date: 2026-07-27. Baseline: `ced2caa` (P2 accepted+installed, T-300 spike committed). Pi authenticated
live for both `anthropic` and `openai-codex` throughout this work. Followed the recommended architecture in
`docs/specs/004-adaptive-dispatch/context/P3-pi-lane.md` (CLI-subprocess spawner, guards-as-flags, no
generated Pi agent tree — see `docs/adr/0007-pi-lane.md` for the full design record).

## Summary of changes, per task

### T-301 — managed pinned Pi install, `--doctor --harness pi`

- `ai/scripts/routing_core/catalog.py:18-36` — `PI_PACKAGE`, `PI_PINNED_VERSION = "0.81.1"`,
  `pi_pinned_argv(*args)`: every pi invocation (probe here, spawn in `set_agents_spawn.py`) goes through
  `pnpm dlx --package @earendil-works/pi-coding-agent@0.81.1 pi <args>` — an EXACT pin, never the personal
  `~/.local/bin/pi` wrapper's release-age soft pin.
- `ai/scripts/routing_core/catalog.py` (`pi_auth_provider_keys`) — read-only `auth.json` KEY-SET (provider
  names only, never token values), used by both the probe and the doctor.
- `ai/scripts/set_agents_spawn.py` (`doctor()`) — redacted report: `pinned_version`, `version_ok`,
  `auth_providers`, `list_models_ok`, `doctor_green`.
- `ai/scripts/set_agents_app.py` — new `--doctor` flag (line ~1286 area) and `--harness` gains `"pi"`;
  `cmd_doctor(harness, human)` wires `--doctor --harness pi` to a schema-2 envelope (exit 0 green / 1
  not-green / 2 `DOCTOR_HARNESS_UNSUPPORTED` for anything but `pi`).
- **Status** = the doctor command itself. **Rollback** = revert `PI_PINNED_VERSION` (one line); pnpm's
  content-addressed store keeps every previously-resolved version cached, so no reinstall is needed.

Live proof:
```
$ python3 ai/scripts/set_agents_app.py --doctor --harness pi --json
{"command": "doctor", "data": {"auth_providers": ["anthropic", "openai-codex"], "doctor_green": true,
 "list_models_ok": true, "pinned_version": "0.81.1", "version_ok": true},
 "ok": true, "reason_codes": [], "schema_version": 2, "warnings": []}
```

### T-302 — minimal `pi` target (no generated tree)

- `ai/scripts/generate.py` — `validate_pi_target(roles)` (new function) asserts every active role has its
  canonical prompt on disk; wired into `validate()` right after `check_variant_catalog_coherence`.
- `ai/scripts/install.py` — **unchanged**. Per the context pack's pre-approved deviation, there is no
  per-user file tree for this repo to write for Pi (unlike `~/.config/opencode`/`~/.claude`/`~/.codex`);
  the "target" is the canonical prompt (already tracked, already installed by the other three harnesses)
  plus `--doctor --harness pi` (reads `~/.pi/agent/` directly). Documented and flagged for review scrutiny
  in `docs/adr/0007-pi-lane.md` Decision 4.

### T-303 — `ai/scripts/set_agents_spawn.py` (new file, the spawner)

- `pi_model_id(provider, model)` — catalog id -> Pi id (identity for openai-codex, curated map for
  anthropic); `SpawnError("MODEL_ID_UNMAPPED")` for anything else.
- `spawn(role, task, provider, model, prompt_path, guard_tools=GUARD_TOOLS_READONLY, cwd=None, timeout=300)`
  — builds the exact-pinned argv, runs it from an isolated scratch cwd (own tempdir if `cwd` is not given,
  removed after), parses the `--mode json` event stream, and returns `("success"|"model_mismatch"|
  "failure", detail)`. Crash (`exit != 0` or no `agent_settled`) always → `failure`; a decided-model
  mismatch (from the last `assistant` message's `provider`/`model`) → `model_mismatch`, never `success`; a
  final turn with `stopReason == "error"` (a defensive extra beyond the literal crash rule) → `failure`.
- `route_and_spawn(role, task_class, task, ...)` — the full P1 lifecycle over the CLI:
  `--route-decide` → (non-executable ⇒ `{"status":"refused",...}`, no session ever) → `--route-dispatched`
  → `spawn()` → `--route-terminal <success|failure>`. Accepts `routing_test_root` (maps to
  `SET_AGENTS_ROUTING_TEST_ROOT`) so hermetic/QA callers never touch the production store.
- `main()` — a small CLI (`--role/--task-class/--task/...` or `--doctor`) for direct/manual use.

### T-304 — guards as flags (002 AC-04 at this enforcement point)

- `GUARD_TOOLS_READONLY = ("read","grep","find","ls")` — the default and only allowlist this package ever
  composes. `GUARD_TOOLS_CODE_RW` exists as a documented future tier, never wired as a default anywhere.
- `--no-session` and `--no-extensions` are built into `spawn()`'s argv UNCONDITIONALLY — never gated by
  `guard_tools`, proven both hermetically (`test_spawn_guard_flags_are_unconditional_and_default_tools_are_readonly`)
  and live (below).
- argv/cwd/env: argv is a fixed tuple (`subprocess.run`, never `shell=True`); `cwd` defaults to a
  spawner-owned scratch dir, never the caller's; `env` is the spawner's own `CI/NO_COLOR/TERM` hygiene copy
  — the task text has no channel into any of the three.

### T-305 — pi pairs, model-ID map, the flip

- `ai/scripts/routing_core/catalog.py` — `("pi","openai-codex")` and `("pi","anthropic")` added to
  `_PAIR_COMMANDS` (both share the single argv `pi_pinned_argv("--list-models")`, memoized once per
  `_probe_pairs` call like the opencode pair already does). `_parse_pi_models(stdout, provider)` reads the
  `provider  model  ...` column table; openai-codex ids pass through verbatim (catalog-IDENTITY);
  anthropic raw ids are translated through `PI_MODEL_MAP["anthropic"] = {"opus":"claude-opus-4-8",
  "sonnet":"claude-sonnet-5","haiku":"claude-haiku-4-5"}`. The `pi` branch in `_probe_pairs` additionally
  gates on `pi_auth_provider_keys()` containing the provider (belt-and-suspenders alongside the naturally
  fail-closed column parse).
- `ai/scripts/routing_core/service.py:14-22,132` — `PI_SIMULATION_ONLY = False` (module constant, one
  place) and `elif PI_SIMULATION_ONLY and facts.selected_runtime == "pi": reason="PI_SIMULATION_ONLY"`. With
  it `False`, a pi route falls through to the SAME `self.inventory.get((runtime, provider))` check every
  other runtime already passes through — an unprobed/unauthenticated pi pair still fails closed as
  `PROVIDER_UNAUTHENTICATED`. Rollback = the constant back to `True`.
- `docs/architecture/overview.md` — new "P3 Pi lane" section (flow diagram, pin, guards, pairs/map, the
  flip, doctor).
- `docs/adr/0007-pi-lane.md` — the full design record.

## A real bug found and fixed by live QA

Initial `pi_pinned_argv` used `("pnpm","dlx","--package",pkg,"pi","--",*args)`. Live QA discovered `pnpm
dlx` does **not** strip that `--`; it is forwarded verbatim into `pi`'s own argument parser. `pi --version`
and `pi --list-models` both tolerate the stray leading `--` (each short-circuits on the first recognized
early-exit flag regardless of anything else on the line), which silently masked the bug for T-301's doctor
and T-305's probe — but a real spawn invocation (`--model ... --print --mode json ...`) failed hard:
```
$ pnpm dlx --package @earendil-works/pi-coding-agent@0.81.1 pi -- --model openai-codex/gpt-5.6-luna --print ...
Error: Unknown option: --
```
Fixed by dropping the separator (`ai/scripts/routing_core/catalog.py:27-38`); confirmed working end to end
below. This is exactly the class of finding a review panel should specifically re-verify (grep the repo for
any remaining `"pi", "--"` argv construction).

## Local validation (real output)

1. **`python3 -m unittest discover -s tests -v`** — `Ran 165 tests ... OK` (baseline was 152; +13
   additive: 2 catalog pair/parser tests folded into the existing probe-parser test plus a dedicated
   auth-keys test, 2 pair-scoping/flip tests, 5 spawner/guard tests, 1 doctor test, 3 `route_and_spawn`
   lifecycle tests, 1 CLI doctor test, 1 generate.py pi-target test). One pre-existing test
   (`test_pi_is_simulation_only_and_runtime_auth_is_pair_scoped`) was renamed and its assertions updated
   to match the new reality it itself now legitimately produces (pi moving from
   pair-table-absent/`RUNTIME_UNAVAILABLE` to pair-table-present-but-unprobed/`PROVIDER_UNAUTHENTICATED`,
   plus a companion positive test proving the flip authorizes exactly like every other runtime once
   probed) — no assertion was weakened, the underlying invariant (never executable without a fresh
   positive probe) is unchanged and re-asserted more precisely.
2. **`./build.sh --check`** → `CHECK_PASS: generated and validated profile go-zen`. **`./build.sh`**
   (generate.py changed) → same, and `git status --short Global` is empty (no drift).
3. **`python3 -m py_compile ai/scripts/*.py ai/scripts/routing_core/*.py tests/*.py`** → clean, no output.
4. **`./ai/scripts/verify.sh`** → `Ran 165 tests ... OK` then `VERIFY_PASS` (includes the `Global/`
   diff-vs-fresh-build drift check).
5. **`git diff --check`** → exit 0, no whitespace errors.
6. **Live QA** (below).
7. **Guard proofs** (below, part of live QA).

## Live QA (real Pi, real network, hermetic routing store)

All routing lifecycle calls used `SET_AGENTS_ROUTING_TEST_ROOT` (never the production
`~/.local/state/set-agentes/routing-v2` — its `routing.db` mtime is unchanged by this session, confirmed by
`ls -la` before/after). Every pi spawn ran from an isolated scratch cwd (pi mutates cwd).

### 1. Doctor green
```
$ python3 ai/scripts/set_agents_app.py --doctor --harness pi --json
{"data": {"auth_providers": ["anthropic", "openai-codex"], "doctor_green": true,
 "list_models_ok": true, "pinned_version": "0.81.1", "version_ok": true}, "ok": true, ...}
```

### 2. openai-codex — full decide→dispatch→spawn→terminal, real network, via `route_and_spawn`
```python
set_agents_spawn.route_and_spawn(role="implementer", task_class="documentation",
    task="Reply with exactly: PI OK", routing_test_root=".../pi-routing-root-a")
```
Result:
```json
{"status": "success", "run_id": "run1_a83306cffe420219355008a3d80cbf7b",
 "provider": "openai-codex", "model": "gpt-5.6-luna",
 "detail": {"model": "openai-codex/gpt-5.6-luna",
            "usage": {"input": 3221, "output": 6, "totalTokens": 3227, "cost": {"total": 0.003257}}},
 "terminal_exit_code": 0}
```
`--routing-report --json` against that same test root then showed `retained_events: 6` (authorize,
dispatch, terminal, plus rollups) for exactly `route_id rt1_ed77d66bea906421` — the fast-tier
`openai-codex/gpt-5.6-luna` row, the naturally-winning candidate (lowest `curated_priority` at every tier
in `routes.v1.toml` is always `openai-codex`, see note below).

### 3. anthropic — decide→dispatch→spawn→terminal(failure), real network
`routes.v1.toml` gives `openai-codex` `curated_priority=10` and `anthropic` `curated_priority=20` at
**every** tier, so a normal `--route-decide` for `implementer` always selects `openai-codex` — there is no
descriptor field to force provider selection, and `models.toml`'s `[routing].enabled_providers` is
all-or-nothing (a provider with catalog rows that is NOT enabled makes `build_snapshot` fail the whole
catalog with `CATALOG_INVALID`, confirmed live when I tried `enabled_providers = ["anthropic"]` — reverted
immediately, `git diff models.toml` is empty). So the anthropic run below drives `RoutingService.route()`
(the real production method) through the same sanctioned hermetic composition seam every other test in
this repo uses (`routing._compose_for_tests`, real `routes.v1.toml`/roster/config, an injected inventory
dict with only `("pi","anthropic"): {"haiku"}` positive), then calls the REAL `spawn()` against the real
network for the actual agent turn, then closes the run with the store's real `terminal()`:
```json
decision: {"route_id": "rt1_fd4b56e524a42515", "runtime": "pi", "provider": "anthropic", "model": "haiku",
           "execution_enabled": true, "run_id": "run1_15cab29aaa40727e83d39d7eb27085c5", ...}
spawn outcome: failure {"reason": "PI_TURN_ERROR",
  "detail": "400 {\"type\":\"error\",\"error\":{\"type\":\"invalid_request_error\",
             \"message\":\"You're out of extra usage. Add more at claude.ai/settings/usage and keep going.\"}...}"}
terminal state closed; store.open_runs() == [] afterward (run is not left open)
```
This account's Claude Max usage was genuinely exhausted during this session (confirmed reproducible via a
second, independent raw `pi --model anthropic/claude-haiku-4-5 ...` call outside any of this code — same
error). Before that error path, `spawn()`'s model-mismatch check had already passed (`observed ==
"anthropic/claude-haiku-4-5" == target_id`) — i.e. Pi genuinely resolved and attempted the DECIDED model,
confirmed by the request itself being billed against the account's quota; the failure is downstream of
model verification, not a mismatch. **Flag for the review panel**: this is a real environmental constraint
(quota), not a code path I could avoid — it doubles as a live proof of the `PI_TURN_ERROR` defensive branch
(a real API error, correctly classified as `failure`, never `success`) and of `enabled_providers`
being all-or-nothing (a legitimate, if incidental, finding worth a follow-up doc note).

### 4. Crash⇒failure (two real crash shapes)
- **Unsupported provider outright** (bypassing our own `pi_model_id` guard, hitting pi's own CLI parser
  directly): `pi --model bogus-provider/whatever --print --mode json ...` → `exit 1`, **zero** JSON events
  on stdout, stderr `Error: Model "bogus-provider/whatever" not found...`. This is exactly the
  `proc.returncode != 0` branch in `spawn()`.
- **Real subprocess timeout** (`spawn(..., timeout=0.5)`, real pnpm/pi child killed mid-flight): raised
  `subprocess.TimeoutExpired`, caught, returned
  `("failure", {"reason": "PI_CRASH", "detail": "Command '(...)' timed out after 0.5 seconds"})`.
- **Bad model within a known/authenticated provider** (`openai-codex/not-a-real-model`): pi does NOT hard
  crash — it runs the full lifecycle to `agent_settled` with `stopReason: "error"` on the final message
  (`"Codex error: The 'not-a-real-model' model is not supported..."`), which `spawn()` classifies as
  `("failure", {"reason": "PI_TURN_ERROR", ...})`, never `success`. This is a real, live confirmation that
  pi distinguishes "provider entirely unknown" (hard exit) from "provider known, model unknown" (soft
  in-stream error) — exactly the two branches `spawn()` implements.

### 5. Guard proofs (live, real Pi)
- **Protected-path / any-path write, read-only tier**: spawned a real child (`GUARD_TOOLS_READONLY`)
  explicitly instructed to "use your write tool right now to create the file
  `<scratch>/pi_guard_should_not_write.txt` containing HACKED". Result: `outcome == "success"` (the child
  replied, since replying doesn't need a tool), and `target.exists() == False` — the write tool was simply
  never available to invoke.
- **No delegation, even at the widest tool tier**: spawned a real child with `GUARD_TOOLS_CODE_RW` (read,
  grep, find, ls, edit, write, bash — every builtin) and `--no-extensions` still on, asked it to list every
  tool it has available. Reply:
  ```
  functions.read
  functions.grep
  functions.find
  functions.ls
  functions.edit
  functions.write
  functions.bash
  multi_tool_use.parallel
  ```
  No delegation/subagent tool anywhere — `pi-subagents` (the only extension Pi ships that could add one)
  never loaded, confirmed live even under the tool tier that is NOT this package's default.

## Deviations from the context pack (all pre-approved, restated for the review panel)

1. **No TypeScript/SDK host, CLI-subprocess spawner instead** (context pack's own recommendation, ADR-0007
   Decision 1) — the review panel should specifically scrutinize whether the CLI-subprocess boundary is
   sufficiently observable/auditable vs. an in-process SDK host; I believe it is (fixed argv list, own
   scratch cwd, own env dict, structured JSON stream), but this is the single highest-leverage architecture
   choice in the package.
2. **No generated `pi` agent tree, `install.py` untouched** (ADR-0007 Decision 4) — literal deviation from
   AC-10's text ("`install.py` gains a pi target"); the context pack pre-approved this, but it IS a
   deviation the panel should re-confirm is acceptable given the actual AC wording.
3. **`enabled_providers` all-or-nothing discovered, not pre-known** — not a deviation from the plan, but a
   real repo behavior I ran into live; worth a note in `docs/architecture/overview.md` or a follow-up
   backlog item if the panel agrees it is surprising enough to warrant one (I did not add one myself since
   it is P1 behavior outside this package's ownership).
4. **The `--` argv bug** (above) — caught by live QA, not by the hermetic test suite (the stub-based
   spawner tests use a real Python interpreter as the "pi" binary, which never independently re-validates
   `pnpm`'s actual arg-forwarding semantics). Flagging this explicitly: hermetic tests validate OUR code's
   logic; only the live run validated the ACTUAL third-party CLI contract. The review panel should treat
   any other `pi_pinned_argv` callers/future changes with the same live-verification discipline.

## Known risks / scrutinize

- **Flip safety**: `PI_SIMULATION_ONLY = False` is a static, code-reviewed constant, not a live per-decision
  doctor check — by design (AM-2/performance), but it means a REGRESSION in the pi pair's probe correctness
  (e.g., a future Pi CLI output-format change silently breaking `_parse_pi_models`) would fail closed
  (`PROVIDER_UNAUTHENTICATED`, never a false authorization) rather than being caught by the doctor at
  decision time. The doctor is a separate, operator-facing signal (`--doctor --harness pi`), not wired into
  `route()` itself — confirm this separation is the intended safety model.
- **Guard surface is 100% inside `set_agents_spawn.py`** (ADR-0007 consequence) — there is no second
  enforcement layer (no extension, no sandboxed subprocess wrapper beyond the flags themselves). The tool
  allowlist and `--no-extensions`/`--no-session` are pi's OWN interpretation of its own flags; this repo
  cannot verify pi's internal enforcement beyond observing its behavior (which I did, live, above).
- **`enabled_providers` all-or-nothing** — a real repo invariant, not introduced by me, but it means this
  package can never live-test "provider X unavailable, provider Y available" through the real `--route-decide`
  CLI without either editing `routes.v1.toml` (read-only for this package) or breaking the catalog build.
  I used the sanctioned `_compose_for_tests` seam instead — confirm the panel is comfortable with that
  substitution for the anthropic live-decide portion specifically.
- **Anthropic quota exhaustion** — the anthropic live proof above is a genuine account-quota failure, not a
  clean `success`. A re-run once quota resets would be a strictly stronger proof; I could not force that
  within this session.

## Assumptions

- `PI_PINNED_VERSION = "0.81.1"` is the version actually installed/verified in this environment; a version
  bump is a deliberate, reviewed, one-line change per ADR-0007.
- The anthropic model-ID curated map (`opus/sonnet/haiku`) covers every anthropic model
  `routes.v1.toml` currently declares; `fable` is intentionally absent (not a routed model in the catalog).
