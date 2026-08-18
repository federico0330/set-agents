# 033-menos-espera-menos-cuota · PKG-4

<!-- notas:auto -->
## Motivo

- objetivo: Windows sin mentiras: cerrar las 8 fallas residuales y el flaky de macOS, con techo de skips
- ruteo: cursor-host native subagent; no route-decide → implementer (inherit)
- complejidad: high
- riesgo: medium
- paths: `tests`, `.github/workflows/ci.yml`, `ai/scripts/vault_ops.py`

## Tareas

- [x] los 4 tests que llaman bash directo pasan por la guarda de toolchain (completed) · python3 -m unittest HarnessTests AC-4.1 sites + pin: ok (build_check, generate, install, guest_copy, ac41 pin). Bite: bash reinserted → pin FAIL; cp restore → ok. Probe tests/__init__.py:420-428 untouched.
- [x] diagnosticar y resolver los casos 5 a 8 uno por uno, con evidencia por caso (completed) · casos 5-8 unittest OK: tools-install TOOL_REJECTED (as_posix TOML), stdin-dev-null via run() rc=2, vault merge + _plan_relpath posix bite FAIL then OK, ADR slug from docs/historia archive. No set_agents_app.py.
- [x] techo de skips fijado en el job windows-bootstrap (completed) · ci.yml WINDOWS_BOOTSTRAP_SKIP_CEILING=660 prints WINDOWS_BOOTSTRAP_SKIPS and fails if skips>ceiling. test_windows_bootstrap_job_pins_a_skip_ceiling + parser OK. Bite ceiling 0 → pin FAIL; parser regex broken → ERROR; cp restore → OK. build.sh --check BUILD_CHECK_PASS.
- [x] volver determinista el test de liveness de macOS sin subir el sleep (completed) · test_slow_liveness_reports_stderr_progress_without_changing_provider_stdout OK (stream Event handshake, no extra sleep, tui.py untouched).

## Recorrido

- review: pass (0 hallazgos)
- testing: pass
- runtime QA: pass
- gate `check-owned-paths`: pass
- gate `build-check`: pass
- gate `verify`: pass
- gate `git-diff-check`: pass
- gate `risk-classification`: pass

## Spawns

- SPAWN-001 package-planner · modelo cursor/inherit
- SPAWN-002 implementer · modelo cursor/inherit
- SPAWN-003 gate-runner · modelo cursor/inherit
- SPAWN-004 package-reviewer · modelo cursor/inherit
- SPAWN-005 security-auditor · modelo cursor/inherit

context pack: `docs/specs/033-menos-espera-menos-cuota/context/PKG-4.md`

↩ [[features/033-menos-espera-menos-cuota|033-menos-espera-menos-cuota]]
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
