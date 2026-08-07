# Correccion diagnostico 400 out-of-extra-usage en pi

<!-- notas:auto -->
- fecha: 2026-08-07 · actor: orchestrator

## Contexto

El usuario tenia limites de sesion disponibles (Claude Code operativo en simultaneo), asi que el 400 'out of extra usage' con Anthropic en pi no era la cuota del plan. Reproducido 2026-08-06 con 'pi --print --model anthropic/claude-sonnet-5' -> 400.

## Decisión

Las apps de terceros (Sign in with Claude, como pi) facturan contra el balde prepago 'extra usage' (claude.ai/settings/usage), separado de los limites de sesion Max que usa Claude Code; con saldo extra en cero pi falla con Anthropic aunque Claude Code funcione. Mitigacion: cargar extra usage, usar openai-codex en pi, o lane claude-code para modelos Anthropic. Reemplaza el diagnostico anterior ('mismo bucket que Claude Code').
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
