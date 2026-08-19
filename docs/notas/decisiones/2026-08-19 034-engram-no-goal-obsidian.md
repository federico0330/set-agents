# Engram no-goal: el vault Obsidian ya es el contexto

<!-- notas:auto -->
- fecha: 2026-08-19 · actor: orchestrator
- alcance: [[features/034-cuota-organica-y-writer-barato|034-cuota-organica-y-writer-barato]] · [[features/034-cuota-organica-y-writer-barato/PKG-A|PKG-A]]

## Contexto

Federico usa Obsidian para el contexto. Pregunto si Engram sigue haciendo falta; si no, no implementarlo. ADR-0012 y ADR-0056 ya hacen mandatory el vault. Gentle-AI usa Engram; SET no lo copia.

## Decisión

Engram queda fuera de 034. El contexto durable es docs/notas/ (vault) mas feature-state.py. No hay paquete Engram ni MCP enable de engram para este slice.

## Consecuencias

Quien busque memoria cross-session lee el vault y BUENOS-DIAS.md. Un pedido futuro de Engram es otro feature, no un add-on silencioso de 034.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
