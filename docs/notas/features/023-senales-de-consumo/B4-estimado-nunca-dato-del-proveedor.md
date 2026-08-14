# 023-senales-de-consumo · B4-estimado-nunca-dato-del-proveedor

<!-- notas:auto -->
## Motivo

- objetivo: Que ningun numero estimado viaje sin su base, su ventana y su cobertura
- complejidad: medium
- paths: `ai/scripts`, `tests`, `docs/adr`
- depende de: B3-ventana-y-rollup

## Tareas

- [x] basis, provider_reported false, ventana nombrada por su definicion y cobertura (AC-08) (completed) · unittest: 1107 OK / 3 skips (orquestador); verify.sh VERIFY_PASS; build.sh --check BUILD_CHECK_PASS
- [x] Guard test: una superficie sin etiqueta falla el gate (AC-09) (completed) · unittest: 1107 OK / 3 skips (orquestador); verify.sh VERIFY_PASS; build.sh --check BUILD_CHECK_PASS
- [x] Sin presupuesto declarado no se muestra restante, se muestra consumido (AC-10) (completed) · unittest: 1107 OK / 3 skips (orquestador); verify.sh VERIFY_PASS; build.sh --check BUILD_CHECK_PASS

## Recorrido

- review: pass (0 hallazgos)
- testing: pass
- runtime QA: pass
- gate `unittest-suite`: pass
- gate `verify-sh`: pass
- gate `build-check`: pass
- gate `git-diff-check`: pass

## Spawns

- SPAWN-001 implementer · modelo anthropic/opus · effort medium · route run1_3d6812bc5e71422d4a3dbbec86712b86

context pack: `docs/specs/023-senales-de-consumo/context/B4-estimado-nunca-dato-del-proveedor.md`

↩ [[features/023-senales-de-consumo|023-senales-de-consumo]]
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
