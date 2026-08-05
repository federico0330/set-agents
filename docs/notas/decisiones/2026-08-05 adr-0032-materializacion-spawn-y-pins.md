# ADR-0032: materialización en el spawn para opencode/codex y pins de modelo

<!-- notas:auto -->
- fecha: 2026-08-05 · actor: orchestrator

## Contexto

ADR-0030 dejó a los ~22 roles no tiered de opencode/codex en MODEL_STATIC_FALLBACK como camino normal; el wizard seguía pidiendo asignación manual de modelos. Evidencia viva: opencode 1.18.10 acepta -m y --variant por invocación; codex 0.146.0 acepta -m, -c model_reasoning_effort y -c developer_instructions.

## Decisión

Dos CLIs nuevos (opencode_spawn.py / codex_spawn.py) con modos dispatch-writer/review/simulate materializan la decisión de --route-decide en el spawn para cualquier rol; [model_pin] en model-preference.toml (infra ADR-0018) da precedencia pin > dinámico > fallback con reason codes MODEL_PINNED/MODEL_PIN_UNAVAILABLE y selection_path en decisions-v1.jsonl; el wizard declara Automático (recomendado) vs Fijar modelo; MODEL_STATIC_FALLBACK queda como degrade residual. Ver docs/adr/0032-spawn-time-model-materialization-and-pins.md

## Consecuencias

28/28 roles ejecutan el modelo decidido o pinneado en los 4 lanes; contratos congelados intactos (roster tiered=6, frase de doctrina, DDL routing.db, shape de load_model_preference); simulate sigue sin autorizar nada durable.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
