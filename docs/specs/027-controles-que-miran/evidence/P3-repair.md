# P3 repair evidence — gates-que-preguntan-antes (repair round 1)

Consolidated repair of 5 findings from an independent review of P3 (`ai/scripts/routing_core/catalog.py`,
`ai/scripts/routing_cli.py`, `tests/test_routing.py`, `docs/specs/027-controles-que-miran/evidence/P3-implementer.md`).
P3-F06 and P3-F07 are explicitly out of this repair's scope (orchestrator registers them with `log-decision`).

The P3 work was uncommitted in the frozen worktree `agent-af2935e12697877fc` (its branch tip was byte-identical
to base `9a2c8c2`), so it was pulled in with plain `cp` (not `git merge`) of the 4 named files — verified with
`git diff HEAD --stat` before any edit:

```
ai/scripts/routing_cli.py          | 15 ++++++-
ai/scripts/routing_core/catalog.py | 17 +++++---
tests/test_routing.py              | 89 ++++++++++++++++++++++++++++++++++++++
3 files changed, 114 insertions(+), 7 deletions(-)
```

(plus the new `P3-implementer.md`).

## Finding -> change -> verification

| Finding | Change | file:line | Verification |
|---|---|---|---|
| P3-F01 (medium, open `MODEL_REQUEST_` family prefix) | Filter now matches the two NAMED codes with trailing spaces (`"MODEL_REQUEST_APPLIED "`, `"MODEL_REQUEST_UNAVAILABLE "`), never the bare family prefix; docstring updated | `ai/scripts/routing_cli.py:98-102` (code), `:80-96` (docstring) | New assertion `MODEL_REQUEST_TOTALLY_NEW_HARD_FAILURE` -> `(False, 1)` in `test_decide_status_helper_matrix`, `tests/test_routing.py:3591-3597`. RED/GREEN below. |
| P3-F02 (medium, false comment about `MODEL_PIN_UNAVAILABLE`) | Rewrote the comment in `routing_cli.py`, the test comment, and the implementer evidence paragraph to state the TRUE reason (out-of-scope-per-spec.md-D-5, known/measured gap, orchestrator `log-decision`) instead of the false "purely additive vs. real outcome" semantic claim `service.py:503-509` disproves | `ai/scripts/routing_cli.py:84-96`, `tests/test_routing.py:3552-3560`, `docs/specs/027-controles-que-miran/evidence/P3-implementer.md` (Summary, Assumptions) | Prose-only change (no behavior change, as instructed); read back after edit, matches `service.py:503-509`'s actual wording. No new test — the standing `MODEL_PIN_UNAVAILABLE -> (False, 1)` assertion already covers the (unchanged) behavior. |
| P3-F03 (medium, no end-to-end proof the CLI filter matches what `service.py` actually emits) | New end-to-end assertion inside `test_route_decide_cli_hermetic_matrix`: writes a real `model-preference.toml` `[model_pin]` entry pinning role `package-reviewer` to the identity the existing `verified` reviewer decision already won on its own merits, re-runs `--route-decide` through the real CLI subprocess, asserts exit 0 and `MODEL_PINNED <identity>` in `data.reason_codes` | `tests/test_routing.py:3372-3394` | RED/GREEN below (removed the `MODEL_PINNED ` filter line and reran). |
| P3-F04 (low, gate moved outside its wrapping try/except) | The moved `if runtime == "pi": pi_auth_provider_keys()` gate is now wrapped in its own `try/except (RoutingError, ValueError, KeyError, IndexError, TypeError): continue`, same discipline as every other branch in `_probe_pairs` | `ai/scripts/routing_core/catalog.py:824-828` | New test `test_ac06_pi_key_gate_surprise_only_drops_the_pair_never_raises`, `tests/test_routing.py:4991-5022`. RED/GREEN below. |
| P3-F05 (low, stale docstrings in a file P3 was authorized to touch only for this) | Corrected the `ModelRequestBarrierTests`/`ModelRequestCliTests` class docstrings in `tests/test_model_request.py` — the `_decide_status` review-role gap they described is now narrowed to `MODEL_PIN_UNAVAILABLE` only (P3 closed the `MODEL_PINNED`/`MODEL_REQUEST_*` part of it) | `tests/test_model_request.py:52-66`, `:320-326` | Docstring-only change (no test body touched). `python3 -m unittest tests.test_model_request`: `Ran 15 tests in 3.047s — OK` (below). |

## RED/GREEN evidence (every new/modified test: neutralize production change, confirm red, revert, paste)

Backups of the two production files taken before any neutralization:
`/var/tmp/claude/claude-1000/-home-federico-SET-AGENTES/d40ea0e0-c4b6-4bd0-a488-a584f10bc6c4/scratchpad/{routing_cli.py,catalog.py}.good`
(session scratchpad, never under `~`). Restored via plain `cp` after each probe, never `git checkout`/`restore`.

### F01 — `MODEL_REQUEST_TOTALLY_NEW_HARD_FAILURE` assertion

Neutralized `routing_cli.py` back to the bare-prefix filter (`not code.startswith("MODEL_REQUEST_")`):

```
$ python3 -m unittest tests.test_routing.RoutingTests.test_decide_status_helper_matrix -v
test_decide_status_helper_matrix ... FAIL
======================================================================
FAIL: test_decide_status_helper_matrix
----------------------------------------------------------------------
Traceback (most recent call last):
  File ".../tests/test_routing.py", line 3592, in test_decide_status_helper_matrix
    self.assertEqual(set_agents_app._decide_status(RD(*[None]*6,False,
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        ("MODEL_REQUEST_TOTALLY_NEW_HARD_FAILURE",))),(False,1))
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Tuples differ: (True, 0) != (False, 1)
First differing element 0:
True
False
- (True, 0)
+ (False, 1)
----------------------------------------------------------------------
Ran 1 test in 0.004s
FAILED (failures=1)
```

Restored `routing_cli.py` from the `.good` backup:

```
$ python3 -m unittest tests.test_routing.RoutingTests.test_decide_status_helper_matrix -v
test_decide_status_helper_matrix ... ok
----------------------------------------------------------------------
Ran 1 test in 0.002s
OK
```

`diff ai/scripts/routing_cli.py .../scratchpad/routing_cli.py.good` after restore: no output (identical).

### F03 — end-to-end pinned-review-decision assertion

Neutralized `routing_cli.py` by removing the `and not code.startswith("MODEL_PINNED ")` line entirely:

```
$ python3 -m unittest tests.test_routing.RoutingTests.test_route_decide_cli_hermetic_matrix -v
test_route_decide_cli_hermetic_matrix ... FAIL
======================================================================
FAIL: test_route_decide_cli_hermetic_matrix
----------------------------------------------------------------------
Traceback (most recent call last):
  File ".../tests/test_routing.py", line 3392, in test_route_decide_cli_hermetic_matrix
    self.assertEqual(pinned.returncode,0,(pinned.stdout,pinned.stderr))
AssertionError: 1 != 0 : ('{"command": "route-decide", "data": {..., "independence_verified": true,
"model": "haiku", ..., "provider": "anthropic",
"reason_codes": ["BILLING_RANK provider=anthropic rank=0", "MODEL_PINNED anthropic/haiku"],
"role_class": "review", ..., "selection_path": "pin", "tier": "fast"}, "ok": false,
"reason_codes": ["BILLING_RANK provider=anthropic rank=0", "MODEL_PINNED anthropic/haiku"],
"schema_version": 2, "warnings": []}\n', '')
----------------------------------------------------------------------
Ran 1 test in 1.874s
FAILED (failures=1)
```

(`MODEL_PINNED anthropic/haiku` genuinely present in the real envelope, `ok: false` / exit 1 anyway —
exactly the gap F03 named: the marker reaching the wire proves nothing about the filter being wired to it.)

Restored `routing_cli.py` from the `.good` backup:

```
$ python3 -m unittest tests.test_routing.RoutingTests.test_route_decide_cli_hermetic_matrix -v
test_route_decide_cli_hermetic_matrix ... ok
----------------------------------------------------------------------
Ran 1 test in 2.484s
OK
```

`diff ai/scripts/routing_cli.py .../scratchpad/routing_cli.py.good` after restore: no output (identical).

### F04 — `test_ac06_pi_key_gate_surprise_only_drops_the_pair_never_raises`

Neutralized `catalog.py` back to the unwrapped gate:

```python
if runtime == "pi" and provider not in pi_auth_provider_keys():
    continue
```

```
$ python3 -m unittest tests.test_routing.RoutingTests.test_ac06_pi_key_gate_surprise_only_drops_the_pair_never_raises -v
test_ac06_pi_key_gate_surprise_only_drops_the_pair_never_raises ... ERROR
======================================================================
ERROR: test_ac06_pi_key_gate_surprise_only_drops_the_pair_never_raises
----------------------------------------------------------------------
Traceback (most recent call last):
  File ".../tests/test_routing.py", line 5040, in test_ac06_pi_key_gate_surprise_only_drops_the_pair_never_raises
    result = cat.probe_inventory(self.config, pairs=[("pi", "openai-codex")], timeout=5.0)
  File ".../ai/scripts/routing_core/catalog.py", line 895, in probe_inventory
    return _probe_pairs(config, selected, timeout, listed_out=listed_out)
  File ".../ai/scripts/routing_core/catalog.py", line 824, in _probe_pairs
    if runtime == "pi" and provider not in pi_auth_provider_keys():
                                           ~~~~~~~~~~~~~~~~~~~~~^^
  File "/usr/lib/python3.14/unittest/mock.py", line 1176, in __call__
    return self._mock_call(*args, **kwargs)
  ...
  File "/usr/lib/python3.14/unittest/mock.py", line 1241, in _execute_mock_call
    raise effect
ValueError: boom
----------------------------------------------------------------------
Ran 1 test in 0.005s
FAILED (errors=1)
```

Restored `catalog.py` from the `.good` backup:

```
$ python3 -m unittest tests.test_routing.RoutingTests.test_ac06_pi_key_gate_surprise_only_drops_the_pair_never_raises -v
test_ac06_pi_key_gate_surprise_only_drops_the_pair_never_raises ... ok
----------------------------------------------------------------------
Ran 1 test in 0.003s
OK
```

`diff ai/scripts/routing_core/catalog.py .../scratchpad/catalog.py.good` after restore: no output (identical).

## F01 full reason->exit table, rerun after the repair

Same 7-scenario table the review pasted, rerun directly against the repaired `_decide_status`:

```python
>>> for reasons in [
...     ("MODEL_PINNED anthropic/claude-opus-4-8",),
...     ("MODEL_REQUEST_APPLIED openai-codex/gpt-5.6-sol",),
...     ("MODEL_REQUEST_UNAVAILABLE requested=x reason=y",),
...     ("MODEL_REQUEST_TOTALLY_NEW_HARD_FAILURE",),
...     ("MODEL_REQUEST_",),
...     ("MODEL_PIN_UNAVAILABLE openai-codex/gpt-5.6-sol",),
...     ("FACTS_INCOMPLETE", "MODEL_PINNED anthropic/x"),
... ]:
...     print(set_agents_app._decide_status(RD(*[None]*6, False, reasons)), reasons)
(True, 0)  ('MODEL_PINNED anthropic/claude-opus-4-8',)          <- still correct
(True, 0)  ('MODEL_REQUEST_APPLIED openai-codex/gpt-5.6-sol',)  <- still correct
(True, 0)  ('MODEL_REQUEST_UNAVAILABLE requested=x reason=y',)  <- still correct
(False, 1) ('MODEL_REQUEST_TOTALLY_NEW_HARD_FAILURE',)          <- was (True, 0) before this repair — F01 fixed
(False, 1) ('MODEL_REQUEST_',)                                  <- was (True, 0) before this repair — F01 fixed
(False, 1) ('MODEL_PIN_UNAVAILABLE openai-codex/gpt-5.6-sol',)  <- unchanged (F02 comment-only)
(False, 1) ('FACTS_INCOMPLETE', 'MODEL_PINNED anthropic/x')     <- unchanged, still not allow-all
```

## Full-module runs (as instructed: no `discover -s tests`, no `verify.sh`)

```
$ python3 -m unittest tests.test_routing
Ran 324 tests in 101.073s
FAILED (failures=2, errors=2, skipped=1)
```

The 4 failures are exactly the documented pre-existing, environmental `ai/state/project.json`-gitignored
failures — same set the review already confirmed `IDENTICAL_FAILURE_SETS` for base vs. P3:

```
ERROR: test_comment_only_divergence_migrates_and_opens
ERROR: test_routing_migrate_uses_harness_identity_and_test_store
FAIL: test_routing_migrate_prints_the_divergence_to_stderr
FAIL: test_the_migration_banner_reports_the_versions_it_observed
```

None of the 4 findings' new/modified tests are in this list — confirmed by name against the 4 above.

```
$ python3 -m unittest tests.test_model_request -v
... (15 tests, all "ok")
Ran 15 tests in 3.047s
OK
```

## Unverified

- Full-repo gates (`discover -s tests`, `verify.sh`, `build.sh --check`): not run, per explicit instruction —
  left to the independent gate-runner.
- P3-F06 (`MODEL_METADATA_INFERRED` unfiltered) and P3-F07 (the 4 `ai/state/project.json` tests): not touched,
  per explicit instruction — registered by the orchestrator with `log-decision`, not part of this repair.
