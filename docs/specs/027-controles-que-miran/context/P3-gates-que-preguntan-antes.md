# Context pack — P3-gates-que-preguntan-antes

Spec: `docs/specs/027-controles-que-miran/spec.md`; **AC-06, AC-07**. Dependencies: none.

## Objective

Ask Pi's credential gate before starting `pi --list-models`, while retaining the existing
fail-closed parser for a credential that is present. Treat model-pin/request markers as
informational when classifying a review decision, without converting a real denial into success.

## Current evidence and candidate surface

- `_probe_pairs` loops in `ai/scripts/routing_core/catalog.py:735-839`. Today it invokes
  `_run_cached` for Pi at `:806-814`, then calls `pi_auth_provider_keys()` at `:826-834`: this is
  the order AC-06 changes. Pi's timeout floor is 60 seconds at `:43-51`.
- `pi_auth_provider_keys` is read-only/fail-closed for missing, symlinked, foreign, malformed, or
  unexpected auth data (`catalog.py:348-385`). Preserve it and never log credentials.
- Pi pairs share `pi_pinned_argv("--list-models")` (`catalog.py:170-176`); invalid-key cases must
  skip that subprocess.
- `_decide_status` filters only `RUNTIME_REDIRECTED`/`BILLING_RANK` at
  `ai/scripts/routing_cli.py:68-86`. Its matrix is `tests/test_routing.py:3487-3516`.
  `MODEL_PINNED` and `MODEL_REQUEST_*` are produced at `routing_core/service.py:503-540`.

## Tasks and ownership

Owned paths:

- `ai/scripts/routing_core/catalog.py` — move the Pi key-set gate before `_run_cached`; do not
  move the Pi column parser or change pair/cache semantics.
- `ai/scripts/routing_cli.py` — extend only the informational-marker filter in `_decide_status`.
- `tests/test_routing.py` — direct probe-order and decision-status matrix regressions.

Read-only: `ai/scripts/routing_core/service.py`, `ai/scripts/set_agents_app.py`,
`tests/test_model_request.py`, models/routes config, ADRs, spec, and state. Do not touch sort key,
CLI envelope schema, Pi pin/version, or unrelated selection logic.

## Required red/green bite

Add tests before each production edit and prove them red against the current order/filter:

- **AC-06 invalid:** mock `pi_auth_provider_keys()` with no relevant provider and make
  `catalog.subprocess.run` a fail-fast spy. Probe the explicit Pi pair; it is absent and the spy
  has zero calls. This fails today because the pinned Pi process runs first.
- **AC-06 valid:** return the audited provider and valid Pi table; assert the list-models process
  is called and the same curated model returns. Bad/nonzero/empty columns remain absent,
  fail-closed.
- **AC-07 informational-only:** extend `test_decide_status_helper_matrix` with standalone and
  mixed `MODEL_PINNED`, `MODEL_REQUEST_APPLIED`, and `MODEL_REQUEST_UNAVAILABLE` markers. They may
  not make an executable decision fail or a non-executable review fail by themselves.
- **AC-07 complement:** pair each marker with `FACTS_INCOMPLETE` or
  `REVIEWER_INDEPENDENCE_UNAVAILABLE`; result remains `(False, 1)`. Never replace the closed
  reason table with an allow-all rule.

## Risks and invariants

- Order: evaluate/use Pi keys before any Pi `_run_cached` call; do not preflight other runtimes or
  change their timeout.
- Fail closed: bad/missing keys => no process/no pair; valid key plus bad CLI output => no pair.
- Status: remove only named informational prefixes; unknown/hard reason codes keep exit 1.
- No P3 owned-path overlap with P1/P2/P4. `tests/test_routing.py` is shared only if P2 needs a Pi
  fixture adjustment; preserve its changes if that happens.

## Local validations and package gates

Run long commands through `ai/scripts/heartbeat-run.py --interval 20 -- <command>` (ADR-0041):

- `python3 -m unittest tests.test_routing.RoutingTests.<new_P3_tests>`
- `python3 -m unittest tests.test_routing`
- `python3 -m unittest tests.test_model_request`
- `python3 -m unittest discover -s tests`
- `./ai/scripts/verify.sh`
- `./build.sh --check`
- `git diff --check`

Expected markers: `VERIFY_PASS`; `SELF_SCAFFOLD_SYNC_OK`, `GLOBAL_TREE_SYNC_OK`,
`BUILD_CHECK_PASS`. Focused P3 names are not created yet; no gate was run for this planning pack.
Runtime surface: `true` (route-decision workflow). Test owner: implementer.

## Done conditions

AC-06/07 close only when invalid Pi credentials demonstrably invoke no subprocess, valid Pi
credentials still probe and parse fail-closed, informational model codes retain intended status,
and co-occurring hard failures stay closed.
