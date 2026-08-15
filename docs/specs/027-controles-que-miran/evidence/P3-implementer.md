# P3 implementer evidence — gates-que-preguntan-antes

## Summary

AC-06: `_probe_pairs`'s pi branch (`ai/scripts/routing_core/catalog.py`) now checks
`pi_auth_provider_keys()` BEFORE any subprocess for that pair, instead of after. The
belt-and-suspenders column parser is untouched (still runs, still fail-closed) for a
credential that IS present. codex/claude-code are unaffected — the gate is `if runtime ==
"pi" and ...`, scoped to the pi branch only.

AC-07: `_decide_status` (`ai/scripts/routing_cli.py`) now also filters `MODEL_PINNED ` and
the two NAMED `MODEL_REQUEST_APPLIED `/`MODEL_REQUEST_UNAVAILABLE ` reason codes (each
matched by its full name plus a trailing space, never the bare `MODEL_REQUEST_` family
prefix — P3-F01 repair round 1 closed a fail-open gap where an unknown future
`MODEL_REQUEST_*` code would have auto-classified as informational) as informational, same
discipline as the existing `RUNTIME_REDIRECTED`/`BILLING_RANK ` filters. `MODEL_PIN_UNAVAILABLE`
is deliberately left unfiltered — NOT because it names a semantically different outcome
(service.py:503-509 says it is exactly as purely-additive as `MODEL_PINNED`, same `if`, same
discipline as `RUNTIME_REDIRECTED`) but because filtering it would exceed AC-07's approved
scope (spec.md D-5 names only `MODEL_PINNED` and the two named `MODEL_REQUEST_*` codes); the
gap is a known, measured one, recorded as an orchestrator decision (P3-F02 repair round 1)
rather than a semantic justification invented after the fact — proven by a dedicated
assertion.

## Changed files

- `ai/scripts/routing_core/catalog.py` (AC-06: reordered the pi key-gate in `_probe_pairs`,
  `catalog.py:806-816` in the new numbering; belt-and-suspenders comment moved/adjusted, no
  parser or cache semantics changed. P3-F04 repair round 1: the moved gate wrapped in its
  own `try/except`, `catalog.py:824-828`.)
- `ai/scripts/routing_cli.py` (AC-07: extended `_decide_status`'s informational-marker
  filter, `routing_cli.py:98-102` in the new numbering. P3-F01 repair round 1: named-code
  matching instead of the bare `MODEL_REQUEST_` family prefix.)
- `tests/test_routing.py` (new AC-06 tests + AC-07 extension of
  `test_decide_status_helper_matrix`; only file I own for tests per the context pack.
  Repair round 1 additions: `MODEL_REQUEST_TOTALLY_NEW_HARD_FAILURE` assertion (P3-F01),
  corrected `MODEL_PIN_UNAVAILABLE` comment (P3-F02), an end-to-end pinned-review-decision
  assertion in `test_route_decide_cli_hermetic_matrix` (P3-F03), and
  `test_ac06_pi_key_gate_surprise_only_drops_the_pair_never_raises` (P3-F04).)
- `tests/test_model_request.py` (P3-F05 repair round 1, orchestrator-authorized,
  docstring-only: corrected two stale claims about `_decide_status`'s review-role gap on
  `ModelRequestBarrierTests`/`ModelRequestCliTests` now that 027 PKG-3 narrowed it to
  `MODEL_PIN_UNAVAILABLE` only. No test bodies changed.)
- `docs/specs/027-controles-que-miran/evidence/P3-implementer.md` (this file: corrected the
  same false `MODEL_PIN_UNAVAILABLE` justification per P3-F02, updated the AC-07/AC-06
  tables and file list for the four repaired findings.)

## AC -> change -> test

| AC | Change (file:line, post-edit) | Test |
|----|-------------------------------|------|
| AC-06 (invalid pi credential never pays the subprocess) | `catalog.py:816` — `if runtime == "pi" and provider not in pi_auth_provider_keys(): continue` moved before the `_run_cached` loop | `test_ac06_pi_invalid_credentials_never_pay_the_list_models_subprocess` |
| AC-06 (valid pi credential still probes + fail-closed parse) | same gate; parser at `catalog.py:840` (`_parse_pi_models`) unchanged | `test_ac06_pi_valid_credentials_still_probe_and_parse_fail_closed` |
| AC-07 (MODEL_PINNED/MODEL_REQUEST_APPLIED/MODEL_REQUEST_UNAVAILABLE informational, standalone + mixed with REVIEW_IDENTITY_UNVERIFIED) | `routing_cli.py:98-102` — `and not code.startswith("MODEL_PINNED ")` / `and not code.startswith("MODEL_REQUEST_APPLIED ")` / `and not code.startswith("MODEL_REQUEST_UNAVAILABLE ")` (named codes only, P3-F01 repair round 1 — no bare `MODEL_REQUEST_` family prefix) | `test_decide_status_helper_matrix` |
| AC-07 (complement: never allow-all, MODEL_PIN_UNAVAILABLE stays unfiltered, hard codes still close, unknown `MODEL_REQUEST_*` stays a hard failure) | same lines | same test, assertions pairing each marker with `FACTS_INCOMPLETE`/`REVIEWER_INDEPENDENCE_UNAVAILABLE`, the standalone `MODEL_PIN_UNAVAILABLE` assertion, and `MODEL_REQUEST_TOTALLY_NEW_HARD_FAILURE` (P3-F01 repair round 1) |
| AC-07 (end-to-end: the CLI's own exit code + envelope for a real pinned review decision, not a synthetic RouteDecision) | same lines, exercised through `set_agents_app.py --route-decide` | `test_route_decide_cli_hermetic_matrix` (P3-F03 repair round 1) |
| AC-06 (pi key-gate surprise never propagates out of `_probe_pairs`, only drops the pair) | `catalog.py:824-828` — the moved gate now wrapped in its own `try/except (RoutingError, ValueError, KeyError, IndexError, TypeError): continue` (P3-F04 repair round 1) | `test_ac06_pi_key_gate_surprise_only_drops_the_pair_never_raises` |

## RED/GREEN evidence (every new test, neutralize -> confirm red -> revert -> paste)

Backups taken before any production edit:
`/var/tmp/.../scratchpad/p3-backup/{catalog.py,routing_cli.py,test_routing.py}.orig`
(session scratchpad, never under `~`).

### 1. Tests written first, run against UNMODIFIED production code (natural red state)

Command:
```
python3 ai/scripts/heartbeat-run.py --interval 20 -- python3 -m unittest \
  tests.test_routing.RoutingTests.test_ac06_pi_invalid_credentials_never_pay_the_list_models_subprocess \
  tests.test_routing.RoutingTests.test_ac06_pi_valid_credentials_still_probe_and_parse_fail_closed \
  tests.test_routing.RoutingTests.test_decide_status_helper_matrix -v
```
Literal output (excerpt):
```
test_ac06_pi_invalid_credentials_never_pay_the_list_models_subprocess ... FAIL
test_ac06_pi_valid_credentials_still_probe_and_parse_fail_closed ... ok
test_decide_status_helper_matrix ... FAIL

======================================================================
FAIL: test_ac06_pi_invalid_credentials_never_pay_the_list_models_subprocess
----------------------------------------------------------------------
...
  File ".../ai/scripts/routing_core/catalog.py", line 809, in _probe_pairs
    completed_item = _run_cached(ran, argv, pair_timeout, probe_env)
  File ".../ai/scripts/routing_core/catalog.py", line 728, in _run_cached
    ran[argv] = subprocess.run(argv, ...)
  File ".../tests/test_routing.py", line 4938, in fail_fast
    raise AssertionError(
        f"subprocess.run must never be called for a pi pair with no valid credential: {argv!r}")
AssertionError: subprocess.run must never be called for a pi pair with no valid credential:
('pnpm', 'dlx', '--package', '@earendil-works/pi-coding-agent@0.84.0', 'pi', '--list-models')

======================================================================
FAIL: test_decide_status_helper_matrix
----------------------------------------------------------------------
...
    self.assertEqual(set_agents_app._decide_status(RD(*[None]*6,False,
        ("MODEL_PINNED anthropic/claude-opus-4-8",))),(True,0))
AssertionError: Tuples differ: (False, 1) != (True, 0)

----------------------------------------------------------------------
Ran 3 tests in 0.012s

FAILED (failures=2)
```
`test_ac06_pi_valid_credentials_still_probe_and_parse_fail_closed` is `ok` here, honestly —
that half of AC-06 (a genuinely present pi credential) runs the same subprocess either
order, so it was never expected to be red by the reordering alone; it exists to prove the
fix does not accidentally start SKIPPING the call for valid credentials too. Flagged, not
hidden.

### 2. Production changes applied (AC-06 + AC-07)

### 3. GREEN

Same command as above:
```
test_ac06_pi_invalid_credentials_never_pay_the_list_models_subprocess ... ok
test_ac06_pi_valid_credentials_still_probe_and_parse_fail_closed ... ok
test_decide_status_helper_matrix ... ok

----------------------------------------------------------------------
Ran 3 tests in 0.009s

OK
```

### 4. Neutralize each production change independently, reconfirm red, restore

**catalog.py neutralized** (`cp` the pre-edit backup over the live file, AC-07 fix in
`routing_cli.py` still applied):
```
--- catalog.py neutralized, running AC-06 tests ---
test_ac06_pi_invalid_credentials_never_pay_the_list_models_subprocess ... FAIL
test_ac06_pi_valid_credentials_still_probe_and_parse_fail_closed ... ok

======================================================================
FAIL: test_ac06_pi_invalid_credentials_never_pay_the_list_models_subprocess
----------------------------------------------------------------------
...
AssertionError: subprocess.run must never be called for a pi pair with no valid credential:
('pnpm', 'dlx', '--package', '@earendil-works/pi-coding-agent@0.84.0', 'pi', '--list-models')

----------------------------------------------------------------------
Ran 2 tests in 0.008s

FAILED (failures=1)
```
Restored the AC-06 fix verbatim (re-applied the same edit, diff against the backup then
confirmed non-empty, i.e. genuinely different from the neutralized version).

**routing_cli.py neutralized** (`cp` the pre-edit backup over the live file, AC-06 fix in
`catalog.py` still applied):
```
--- routing_cli.py neutralized, running AC-07 test ---
test_decide_status_helper_matrix ... FAIL

======================================================================
FAIL: test_decide_status_helper_matrix
----------------------------------------------------------------------
...
    self.assertEqual(set_agents_app._decide_status(RD(*[None]*6,False,
        ("MODEL_PINNED anthropic/claude-opus-4-8",))),(True,0))
AssertionError: Tuples differ: (False, 1) != (True, 0)

----------------------------------------------------------------------
Ran 1 test in 0.004s

FAILED (failures=1)
```
Restored the AC-07 fix verbatim. Final combined run (both fixes back in place) confirmed
green again — see the "GREEN" block above, re-run identically after restoration:
```
Ran 3 tests in 0.009s

OK
```

### Spy zero-calls proof (literal, standalone)

From the GREEN run's own assertions (`spy.call_count == 0` and `spy2.call_count == 0` for
the two audited pi providers, `openai-codex`/`anthropic`) — no assertion error raised means
both counts were exactly 0; the fail-fast `side_effect` additionally guarantees any call at
all surfaces as an immediate, named `AssertionError` rather than a silent pass, which is
exactly what happened in the RED run above (the very first call raised it).

## Local validations run

- `python3 -m unittest tests.test_routing` (full module, post-fix):
  `Ran 323 tests in 74.523s` — `FAILED (failures=2, errors=2, skipped=1)`. All 4
  failures/errors are `test_routing_migrate_uses_harness_identity_and_test_store`,
  `test_comment_only_divergence_migrates_and_opens`,
  `test_routing_migrate_prints_the_divergence_to_stderr`,
  `test_the_migration_banner_reports_the_versions_it_observed` — all four read
  `ai/state/project.json` directly (e.g. `tests/test_routing.py:2810`), which does not
  exist in this worktree (`ai/state/` is entirely absent here; ADR-0047 moved state out of
  the tracked clone). Pre-existing, environmental, unrelated to `_probe_pairs`/
  `_decide_status`, and `ai/state/` is explicitly out of my owned/editable paths for this
  package. None of the 4 touch the pi probe order or the reason-code filter.
- `python3 -m unittest tests.test_model_request`: `Ran 15 tests in 4.256s` — `OK`.
- Did NOT run `discover -s tests`, `verify.sh`, or `build.sh --check` per the explicit
  instruction to leave those to the independent gate-runner (two other agents competing for
  the machine).

## Assumptions

- The context pack's "MODEL_PINNED and MODEL_REQUEST_*" is exact and exclusive:
  `MODEL_PIN_UNAVAILABLE` (same ADR-0032 family, adjacent in `service.py:503-509`) is
  deliberately NOT filtered. Round 1 review (P3-F02) found the original justification here
  false: `service.py:503-509` is explicit that `MODEL_PIN_UNAVAILABLE` is JUST AS
  purely-additive as `MODEL_PINNED` (same `if`, same discipline as `RUNTIME_REDIRECTED`) —
  there is no semantic difference. The true reason it stays unfiltered is scope: spec.md D-5
  names only `MODEL_PINNED` and the two `MODEL_REQUEST_*` codes, and filtering
  `MODEL_PIN_UNAVAILABLE` too would exceed AC-07 as approved. This is a known, measured gap
  the orchestrator registered with `log-decision`, not a semantic boundary this package
  discovered. Documented in the production comment and a dedicated test assertion so a
  reviewer sees the boundary was considered, not missed.
- `"MODEL_PINNED "` (with a trailing space) is used as the prefix rather than bare
  `"MODEL_PINNED"`, matching the `"BILLING_RANK "` precedent already in the file and the
  actual emitted shape (`f"{marker} {pin[0]}/{pin[1]}"` in `service.py:509`) — this also
  keeps the filter from ever accidentally matching a hypothetical future
  `MODEL_PINNED_SOMETHING` code by prefix collision. Round 1 review (P3-F01) found the
  `MODEL_REQUEST_*` filter had NOT been given the same discipline — it originally matched the
  bare `MODEL_REQUEST_` family prefix, which would have auto-classified any future/unknown
  `MODEL_REQUEST_*` code as informational too. Repaired to match the two named codes with
  their own trailing spaces (`"MODEL_REQUEST_APPLIED "`, `"MODEL_REQUEST_UNAVAILABLE "`),
  consistent with `MODEL_PINNED "`'s own stated rationale.
- P3-F04 (round 1): moving the pi key-gate before the subprocess loop (AC-06) took the
  `pi_auth_provider_keys()` call out of the `try/except` that used to wrap it, so a surprise
  from that call would have propagated out of `probe_inventory` instead of only dropping the
  one pair — contradicting the function's own "never raises" docstring promise. Not reachable
  in production today (the real credential reader already fails closed on its own), but
  wrapped in its own `try/except (RoutingError, ValueError, KeyError, IndexError, TypeError):
  continue` anyway, same discipline as every other branch in this function.

## Known risks / unverified

- Full-repo gates (`discover -s tests`, `verify.sh`, `build.sh --check`) were explicitly
  not run by me (out of scope for this pass) — "sin verificar" for those three; the
  independent gate-runner covers them once.
- The pre-existing `ai/state/project.json`-dependent failures in `test_routing` were not
  investigated further (outside owned paths, unrelated to AC-06/AC-07) beyond confirming
  they reference a file/directory that plainly does not exist in this worktree.

## Blockers

None.
