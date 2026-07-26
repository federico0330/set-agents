# P1R implementation evidence

Baseline captured before P1R implementation: `66164c2a520aef4fc326b996e515a2240706d976`.
The planning handoff also named an earlier ephemeral baseline (`51b84e3f…`); the checked-out package baseline was the former.

## T-001 — trusted facts and immutable catalog

Changed `ai/catalogs/routes.v1.toml`, `ai/scripts/routing_core/domain.py`,
`ai/scripts/routing_core/catalog.py`, `ai/scripts/routing_core/service.py`, and the compatibility facade.
The static ID uses the approved nine-field tuple, excludes runtime, and facts are mandatory/fresh with pair-keyed runtime inventory.

## T-002 — identity and independent review

Changed `routing_core/domain.py`, `routing_core/service.py`, and `routing_core/store.py`.
Run IDs are `run1_` plus `secrets.token_hex(16)`; review identity is read only from a terminal-success persisted writer and excludes its family.

## T-003 — SQLite lifecycle

Changed `routing_core/store.py`.
The fixed default is `~/.local/state/set-agentes/routing-v2`; the adapter uses POSIX checks, `0700`/`0600`, WAL/FULL/FK/busy-timeout zero, `BEGIN IMMEDIATE`, and closes the fallback window before primary dispatch.

## T-004 — operator surface

Changed `ai/scripts/set_agents_app.py`, `ai/scripts/routing.py`, and focused tests.
Explain composes only simulated inputs and does not connect to SQLite. JSON output is the v2 envelope. Legacy detection is `lstat`-only.

## T-005 — local validation

Passed:

```text
python3 -m unittest discover -s tests -p 'test_routing.py' -v
python3 -m unittest -v tests.test_harness.HarnessTests.test_install_sh_dry_run_plans_missing_tools
python3 -m unittest -v tests.test_harness.HarnessTests.test_models_config_emit_roundtrip
python3 ai/scripts/setup_models.py --check
python3 -m py_compile ai/scripts/models_config.py ai/scripts/setup_models.py ai/scripts/routing.py ai/scripts/routing_core/*.py ai/scripts/set_agents_app.py tests/test_routing.py tests/test_harness.py
python3 -m unittest -v tests.test_routing.RoutingTests.test_gate_and_telemetry_negative_cases
./ai/scripts/verify.sh
python3 PROYECTO/ai/scripts/check-owned-paths.py --state-file ai/state/features/003-trusted-routing-pi-runtime.json --package-id P1R-trusted-routing --baseline 66164c2a520aef4fc326b996e515a2240706d976
git diff --check
```

`verify.sh` completed successfully; ownership reported `OWNERSHIP_PASS` and no read-only violation.

## Remaining risks

The adapter intentionally has no external execution integration: dispatch callers must invoke `mark_dispatched` before invoking any external runtime. This is the P1R contract boundary, not a Pi adapter; P2/P3 remain unimplemented.

## Destilado

El router anterior basado en JSON fue reemplazado por un núcleo con catálogo controlado, hechos observados y ciclo SQLite privado. La explicación es simulada y no crea estado; las autorizaciones persistentes cierran la ventana de fallback antes de cualquier llamada externa.
