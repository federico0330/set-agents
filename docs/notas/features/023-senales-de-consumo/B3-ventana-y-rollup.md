# 023-senales-de-consumo · B3-ventana-y-rollup

<!-- notas:auto -->
## Motivo

- objetivo: Rollups en la misma transaccion que close_run, y retencion que no borra lo referenciado
- complejidad: medium
- paths: `ai/scripts/routing_core`, `tests`, `docs/adr`
- depende de: B2-el-reporte-dice-de-donde-sale

## Tareas

- [x] Schema 8 con usage_rollups en la misma transaccion que close_run (AC-06) (completed) · unittest: 1098 OK / 3 skips (orquestador); verify.sh VERIFY_PASS; build.sh --check GLOBAL_TREE_SYNC_OK + BUILD_CHECK_PASS. Los fallos que reporto el implementer eran del sandbox de codex (.git/hooks en filesystem read-only), no defectos.
- [x] Retencion de dispatches que nunca borra una fila referenciada (AC-07) (completed) · unittest: 1098 OK / 3 skips (orquestador); verify.sh VERIFY_PASS; build.sh --check GLOBAL_TREE_SYNC_OK + BUILD_CHECK_PASS. Los fallos que reporto el implementer eran del sandbox de codex (.git/hooks en filesystem read-only), no defectos.

## Hallazgos

- B3-F01 [critical] closed
- B3-F02 [critical] closed
- B3-F03 [high] closed
- B3-F04 [medium] closed
- B3-F05 [medium] closed
- B3-F06 [low] closed

## Recorrido

- review: repair_required (6 hallazgos)
- verificación: 0 refutados, 6 sostenidos
- repair: B3-F01, B3-F02, B3-F03, B3-F04, B3-F05, B3-F06 → 2 archivos
- delta review: pass
- testing: pass
- runtime QA: pass
- gate `unittest-suite`: pass
- gate `verify-sh`: pass
- gate `build-check`: pass
- gate `git-diff-check`: pass

## Spawns

- SPAWN-001 implementer · modelo anthropic/opus · effort medium · route run1_0f2ddb58515f213d3953f34d5916ee0a
- SPAWN-002 implementer · modelo openai-codex/gpt-5.6-terra · effort high · route run1_af1780fa18fbfe6ba4f94492c96be20c
- SPAWN-003 package-reviewer · modelo anthropic/opus · effort medium · route dec1_97e06bb0ce17530ac0d6c162c01b986e
- SPAWN-004 repair-agent · modelo anthropic/opus · effort medium · route run1_26d316ee214122eceb945694e42e6d52
- SPAWN-005 delta-reviewer · modelo openai-codex/gpt-5.6-terra · effort high

context pack: `docs/specs/023-senales-de-consumo/context/B3-ventana-y-rollup.md`

↩ [[features/023-senales-de-consumo|023-senales-de-consumo]]
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
