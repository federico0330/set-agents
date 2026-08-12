# 019-harness-evolution · P4-doctrine-human-layer

<!-- notas:auto -->
## Motivo

- objetivo: Doctrina: sub-bloque Impacto humano en la narracion, pasos de integrator y architect, protocolo 'Resolve antes de preguntar' y comando /explicar en los 4 runtimes (ADR-0036 + ADR-0037)
- complejidad: medium
- riesgo: test_harness.py assertea frases doctrinales por grep; los 4 arboles deben quedar sin drift
- paths: `docs/adr/0037-resolve-before-asking.md`, `Global/_canonical/commands/explicar.md`, `Global/_canonical/skills/explicar/SKILL.md`
- depende de: P3-cognitive-module-docs

## Tareas

- [x] Sub-bloque Impacto humano en el cierre de paquete, sin tocar ADR-0027/0033 (completed) · test_harness.py:7718 test_ac25_package_close_narrates_impacto_humano_subblock_additively
- [x] integrator.md: detect + record-module-impact/waiver + docs no stale; architect.md: alta en modules.toml (completed) · test_harness.py:7736 test_ac26_integrator_and_architect_carry_module_impact_procedure
- [x] ADR-0037 + protocolo con encabezado exacto + espejos en las gemelas y request-triage (completed) · test_harness.py:7753+7773 test_ac27_resolve_before_asking_header_precedes_askable_list y _mirrored_in_shared_doctrine_and_triage
- [x] /explicar: comando + skill canonicos, read-only, trace con file:line (completed) · test_harness.py:7791+7807 test_ac28_explicar_is_read_only... y _reaches_the_four_runtime_trees
- [x] ./build.sh y verificacion de drift en los 4 arboles + PROYECTO (completed) · build.sh --check CHECK_PASS + SELF_SCAFFOLD_SYNC_OK files=2; test_harness.py:7824 test_ac29_roles_tsv_unchanged_by_explicar

## Hallazgos

- F-01 [low] closed — 
- F-02 [low] closed — 

## Recorrido

- review: repair_required (2 hallazgos)
- verificación: salteada (Los dos findings son de severidad low y ambos son de calidad de la evidencia (conteo 8-vs-7 y un comando elidido), no a…)
- repair: F-01 → 1 archivos
- repair: F-02 → 1 archivos
- delta review: pass
- testing: pass
- runtime QA: pass
- gate `verify`: pass
- gate `build-check`: pass
- gate `diff-check`: pass

## Spawns

- SPAWN-001 implementer · modelo openai-codex/gpt-5.6-terra · effort high · route run1_9a1d67ac54fc4a0e961b8eb4f36461ab
- SPAWN-002 package-reviewer · modelo anthropic/sonnet · effort medium · route dec1_7cc40574306ab8aedb624339e7d2ab07

context pack: `docs/specs/019-harness-evolution/context/P4-doctrine-human-layer.md`

↩ [[features/019-harness-evolution|019-harness-evolution]]
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
