# 049-identidad-honesta-modelos · PKG-A

<!-- notas:auto -->
## Motivo

- objetivo: Proyección efectiva para instalación y drift locales
- ruteo: Route decision dec1_874f5386d86738581762fbe607c1dc46 was supplied; its resolved provider/model is not present in readab… → implementer (inherit)
- complejidad: medium
- riesgo: medium
- riesgo: Local installation targets must not change factory or Global artifacts.
- paths: `ai/scripts/generate.py`, `build.sh`, `ai/scripts/check-drift.sh`, `ai/scripts/install.py`, `tests/test_effective_projection_049.py`

## Tareas

- [x] effective-generate-api (completed) · generate.py --effective opt-in; py_compile PASS
- [x] local-install-projection (completed) · build --install passes effective; focal install test PASS
- [x] local-drift-projection (completed) · check-drift effective; DRIFT_OK focal PASS
- [x] projection-regressions (completed) · tests/test_effective_projection_049.py four tests PASS in bounded groups; git diff --check PASS

## Hallazgos

- PKG-A-F01 [medium] closed — correctness

## Recorrido

- review: repair_required (1 hallazgos)
- verificación: 0 refutados, 1 sostenidos
- repair: PKG-A-F01 → 2 archivos
- testing: pass
- runtime QA: pass
- gate `diff-check`: pass
- gate `py-compile`: pass
- gate `focused-tests`: pass
- gate `build-check`: pass
- gate `owned-paths`: pass
- gate `risk-classification`: pass

## Spawns

- SPAWN-001 implementer · modelo static/static-base · effort medium · route dec1_24710c7532e6fc75454be2ab8fe6f0b3
- SPAWN-002 gate-runner · modelo anthropic/haiku · effort medium · route dec1_9681f895add5bad5585e440cb459394b
- SPAWN-003 package-reviewer · modelo anthropic/haiku · effort medium · route dec1_7331cbb3a4f19849e0131df9c735f955
- SPAWN-004 security-auditor · modelo anthropic/haiku · effort medium · route dec1_af2be38cd664978c5d0fcde0ad511384
- SPAWN-005 finding-verifier · modelo anthropic/haiku · effort medium · route dec1_9bb3fc9dd0587046847e4e86b830d21a
- SPAWN-006 repair-agent · modelo static/static-base · effort medium · route dec1_14f44354427c2e515cc3a55708b97fde

context pack: `docs/specs/049-identidad-honesta-modelos/context/PKG-A.md`

↩ [[features/049-identidad-honesta-modelos|049-identidad-honesta-modelos]]
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
