# 033-menos-espera-menos-cuota · PKG-5

<!-- notas:auto -->
## Motivo

- objetivo: El gate se ve: progreso en vivo, falla temprana, resumen final y los 10 tests mas lentos
- ruteo: cursor-host native subagent; no route-decide → implementer (inherit)
- complejidad: medium
- riesgo: low
- paths: `ai/scripts/verify.sh`

## Tareas

- [x] linea de progreso en vivo con ETA derivada del ritmo real (completed) · python3 -m unittest tests.test_verify_reporter tests.test_harness.HarnessTests.test_shell_scripts_parse
- [x] bloque de falla impreso apenas ocurre, no al final (completed) · python3 -m unittest tests.test_verify_reporter tests.test_harness.HarnessTests.test_shell_scripts_parse
- [x] resumen final con fallas, skips agrupados y los 10 tests mas lentos (completed) · python3 -m unittest tests.test_verify_reporter tests.test_harness.HarnessTests.test_shell_scripts_parse
- [x] prueba de que el conjunto de tests ejecutados no cambia (completed) · python3 -m unittest tests.test_verify_reporter tests.test_harness.HarnessTests.test_shell_scripts_parse
- [x] discover_suite importa tests cuando verify_reporter.py se invoca como script (completed) · python3 -m unittest tests.test_verify_reporter -v, python3 ai/scripts/heartbeat-run.py --interval 20 -- ./build.sh --check, git diff --check

## Recorrido

- gate `verify`: pass
- gate `build-check`: pass
- gate `git-diff-check`: pass
- gate `check-owned-paths`: pass

## Spawns

- SPAWN-001 implementer · modelo cursor/inherit
- SPAWN-002 gate-runner · modelo cursor/inherit
- SPAWN-003 implementer · modelo cursor/inherit
- SPAWN-004 gate-runner · modelo cursor/inherit

context pack: `docs/specs/033-menos-espera-menos-cuota/context/PKG-5.md`

↩ [[features/033-menos-espera-menos-cuota|033-menos-espera-menos-cuota]]
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
