# 025-consola-minima-y-flexible · D5-vault-en-todo-spawn

<!-- notas:auto -->
## Motivo

- objetivo: Que cada spawn de proyecto use Obsidian, verificando primero que se cumple hoy en un spawn real
- complejidad: medium
- paths: `ai/scripts`, `Global/_canonical`, `tests`, `docs/adr`
- depende de: D4-harness-por-CLI

## Tareas

- [x] Medir en un spawn REAL que parte de ADR-0012 se cumple hoy, antes de asumir nada (AC-12) (completed) · python3 -m unittest tests.test_harness.HarnessTests.test_codex_dispatch_writer_embeds_the_vault_block_ahead_of_the_task tests.test_harness.HarnessTests.test_opencode_dispatch_writer_embeds_the_vault_block_ahead_of_the_task -v
- [x] Cerrar la brecha entre lo que el ADR declara y lo que el spawn hace (AC-12) (completed) · python3 -m unittest tests.test_spawn_materialization.VaultDegradationParityTests -v

## Recorrido

- review: pass (0 hallazgos)
- testing: pass
- runtime QA: pass
- gate `d5-focused-tests`: pass
- gate `d5-diff-check`: pass

## Spawns

- SPAWN-001 implementer · modelo openai/gpt-5.6-terra · effort medium

↩ [[features/025-consola-minima-y-flexible|025-consola-minima-y-flexible]]
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
