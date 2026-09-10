# MCP global de Hugging Face

<!-- notas:auto -->
- fecha: 2026-09-08 · actor: orchestrator

## Contexto

Pedido explícito de Federico para instalar Hugging Face globalmente mediante set-agents.

## Decisión

Se agregó huggingface como MCP remoto curado con URL oficial https://hf.co/mcp y se materializó en todos los harnesses globales detectados.

## Consecuencias

OpenCode y Codex quedan off por política; Claude, Cursor y Gemini quedan on según la semántica nativa de cada harness. El primer uso autenticado puede abrir OAuth de Hugging Face.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
