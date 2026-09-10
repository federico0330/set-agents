# 049-identidad-honesta-modelos · PKG-D2

<!-- notas:auto -->
## Motivo

- objetivo: Integración de identidad de modelos, ayuda y TTY aislada sobre candidato reconstruido
- ruteo: Replacement integration package depends on the isolated PKG-C2 candidate chosen by the user. → integrator (inherit)
- complejidad: medium
- riesgo: medium
- riesgo: Integrated TTY evidence must preserve the no-transcript privacy boundary.
- paths: `tests/test_model_identity_integration_049.py`, `tests/test_model_identity_tty_049.py`, `docs/specs/049-identidad-honesta-modelos/evidence/`
- depende de: PKG-A, PKG-B, PKG-C2

## Tareas

- [x] integrated-model-identity-regressions (completed) · 13 unittest OK session Astra→Luna + help/argv in test_model_identity_integration_049
- [x] help-and-argv-regressions (completed) · help human vs --avanzado; invalid --model-state rc2 no partial JSON
- [x] isolated-opencode-tty (completed) · TTY tests: fake OpenCode 1.18.14 observe or closed degrade; evidence PKG-D2-tty.md
- [x] global-gates-and-contract-hash (completed) · build --check PASS; diff --check PASS; contract-hash root sha256:47923adc…; verify.sh FAIL pre-C2/045-048 sibling-test drift (owner-return, not D2)

## Hallazgos

- PKG-D2-F01 [medium] closed — test-gap
- PKG-D2-SEC-001 [medium] closed — security
- PKG-D2-SEC-002 [medium] closed — security

## Recorrido

- review: repair_required (3 hallazgos)
- verificación: 0 refutados, 3 sostenidos
- repair: PKG-D2-F01, PKG-D2-SEC-001, PKG-D2-SEC-002 → 3 archivos
- delta review: pass
- testing: pass
- runtime QA: pass
- gate `focused-tests`: pass
- gate `build-check`: pass
- gate `diff-check`: pass
- gate `owned-paths`: pass
- gate `contract-hash`: pass
- gate `verify-sh`: fail
- gate `repair-ceiling`: pass

## Spawns

- SPAWN-001 implementer · modelo local/BASE · effort low
- SPAWN-002 package-reviewer · modelo local/BASE · effort low
- SPAWN-003 security-auditor · modelo local/BASE · effort low
- SPAWN-004 finding-verifier · modelo local/BASE · effort low
- SPAWN-005 repair-agent · modelo local/BASE · effort low
- SPAWN-006 delta-reviewer · modelo local/BASE · effort low
- SPAWN-007 runtime-verifier · modelo local/BASE · effort low
- SPAWN-008 adversarial-judge · modelo local/BASE · effort low
- SPAWN-009 adversarial-judge · modelo local/BASE · effort low
- SPAWN-010 adversarial-judge · modelo local/BASE · effort low
- SPAWN-011 adversarial-judge · modelo local/BASE · effort low

context pack: `docs/specs/049-identidad-honesta-modelos/context/PKG-D2.md`

↩ [[features/049-identidad-honesta-modelos|049-identidad-honesta-modelos]]
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
