# 027-controles-que-miran · P1-alcance-y-aislamiento

<!-- notas:auto -->
## Motivo

- objetivo: Que el control de alcance vea los archivos nuevos y que los modulos de test pasen aislados
- complejidad: medium
- paths: `ai/scripts/check-owned-paths.py`, `tests`, `docs/adr`

## Tareas

- [x] check-owned-paths ve los archivos sin trackear (AC-01) (completed) · unittest discover: 1123 OK / 3 skips (orquestador); test_harness aislado 464 OK; test_routing aislado 320 OK; verify.sh VERIFY_PASS; build.sh --check BUILD_CHECK_PASS
- [x] Los modulos de test pasan aislados (AC-02) (completed) · unittest discover: 1123 OK / 3 skips (orquestador); test_harness aislado 464 OK; test_routing aislado 320 OK; verify.sh VERIFY_PASS; build.sh --check BUILD_CHECK_PASS
- [x] Un test impide que el aislamiento se rompa de nuevo (AC-03) (completed) · unittest discover: 1123 OK / 3 skips (orquestador); test_harness aislado 464 OK; test_routing aislado 320 OK; verify.sh VERIFY_PASS; build.sh --check BUILD_CHECK_PASS

## Hallazgos

- P1-F01 [medium] closed

## Recorrido

- review: repair_required (1 hallazgos)
- verificación: 0 refutados, 1 sostenidos
- repair: P1-F01 → 2 archivos
- delta review: pass
- testing: pass
- runtime QA: pass
- gate `unittest-suite`: pass
- gate `verify-sh`: pass
- gate `build-check`: pass
- gate `git-diff-check`: pass
- gate `test-isolation`: pass

## Spawns

- SPAWN-001 repair-agent · modelo openai/gpt-5.6-terra · effort medium
- SPAWN-002 gate-runner · modelo openai/gpt-5.6-luna · effort low
- SPAWN-003 delta-reviewer · modelo openai/gpt-5.6-sol · effort high
- SPAWN-004 test-writer · modelo openai/gpt-5.6-terra · effort medium
- SPAWN-005 runtime-verifier · modelo openai/gpt-5.6-terra · effort medium

context pack: `docs/specs/027-controles-que-miran/context/P1-alcance-y-aislamiento.md`

↩ [[features/027-controles-que-miran|027-controles-que-miran]]
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
