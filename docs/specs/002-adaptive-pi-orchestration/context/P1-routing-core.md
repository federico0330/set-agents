# P1 context pack — routing core

## Objective

Implement schema-2 configuration, deterministic routing, proportional execution plans/native gates,
privacy-preserving telemetry, and route explanation/reporting CLI surfaces.

## Approved contract

- `../spec.md`
- `../acceptance.md` AC-05 through AC-13
- `../design.md`
- `../../../../docs/adr/0004-adaptive-routing-pi-runtime.md`
- Package plan in `../tasks.md` P1-T1 through P1-T5

## Ownership

- `models.toml`
- `ai/scripts/models_config.py`
- `ai/scripts/setup_models.py`
- new `ai/scripts/routing.py`
- shared `ai/scripts/set_agents_app.py` (P1 owns route explain/report; P2 may later add Pi doctor only)
- new `tests/test_routing.py`

Read-only context: `roles.tsv`, `ai/scripts/generate.py`, `ai/scripts/install.py`, `tests/test_harness.py`,
`tests/fixtures/models.toml`, and ADR 0003.

## Hard boundaries

- Do not implement Pi generation/install/doctor/child guards in P1.
- Do not modify canonical roles or existing runtime generation.
- Preserve schema-1 behavior through in-memory normalization; no implicit rewrite.
- `harness_gate` maps an allowlisted ID to immutable argv and never accepts shell text.
- Route IDs and model/family/provider values come only from the catalog.
- Telemetry serialization is allowlist-only and keyed by an installation-local HMAC salt.

## Required validations

- `python3 -m unittest discover -s tests -p 'test_routing.py' -v`
- `python3 ai/scripts/setup_models.py --check`
- `python3 -m py_compile ai/scripts/models_config.py ai/scripts/setup_models.py ai/scripts/routing.py ai/scripts/set_agents_app.py tests/test_routing.py`
- `./ai/scripts/verify.sh`

## Done conditions

Schema 1/2, eligibility/tiering/ranking/reviewer/fallback/lane/gate/telemetry/CLI behavior is deterministic,
fail-closed where specified, privacy-safe, and covered by focused tests without regressing existing mappings.
