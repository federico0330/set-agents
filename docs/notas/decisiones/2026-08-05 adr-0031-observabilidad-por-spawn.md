# Observabilidad por spawn (ADR-0031): log de decisiones + campos estructurados en record-spawn

<!-- notas:auto -->
- fecha: 2026-08-05 · actor: orchestrator

## Contexto

ADR-0030 prometía que las decisiones simulate quedaban registradas, pero se computaban con store=None y se perdían; record-spawn no tenía campos de modelo y no existía join entre run_id y SPAWN-NNN.

## Decisión

Cada --route-decide (simulate incluido) appendea una línea a decisions-v1.jsonl junto a routing.db con un decision_id dec1_<hex>; record-spawn acepta --model/--provider/--effort/--route-id; superficies de consulta: set-agents --routing-decisions y feature-state.py spawns; la bitácora, la nota de paquete y el grafo muestran el modelo por spawn. ADR formal: docs/adr/0031-per-spawn-routing-observability.md.

## Consecuencias

La pregunta '¿qué modelo corrió SPAWN-NNN?' se responde desde estado. simulate sigue sin autorizar nada durable; el log es best-effort y nunca input de un gate.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
