# El orquestador de OpenCode sale de opencode-go y vuelve a la lane openai-codex

<!-- notas:auto -->
- fecha: 2026-08-18 · actor: orchestrator

## Contexto

ADR-0044 puso [areas.coord].opencode go-zen en opencode-go/grok-4.5 razonando que la lane subscription-billed no consumia el presupuesto por token de Copilot ni de zen. Medicion de uso real de Federico (2026-08-18): la cuota DIARIA de opencode-go se agota antes de terminar una sola sesion de coordinacion, y con grok en opencode-go duro menos de un prompt. 'Subscription-billed' no significo presupuesto suficiente: significo un techo mas duro y menos visible que el por-token.

## Decisión

models.toml [areas.coord].opencode go-zen pasa de 'opencode-go/grok-4.5' a 'openai/gpt-5.5'. openai/gpt-5.5 ya esta curado en [catalog].opencode_zen y usado por [areas.audit] y [areas.judge], y no colisiona con ningun [roles.<rol>.tiers.*] (todos luna/sol/terra). Las lanes zen y openai-only quedan como estaban.

## Consecuencias

El coordinador de OpenCode ya no consume la cuota diaria de opencode-go. Global/opencode/agents/orchestrator.md y Global/opencode/opencode.json quedaron regenerados con model: openai/gpt-5.5. Queda pendiente revisar ADR-0044, cuyo razonamiento sobre 'subscription-billed' quedo desmentido por la medicion.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
