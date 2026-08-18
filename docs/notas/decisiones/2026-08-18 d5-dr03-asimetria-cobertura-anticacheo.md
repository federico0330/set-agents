# D5-DR03: asimetría de cobertura anti-cacheo de fallos transitorios

<!-- notas:auto -->
- fecha: 2026-08-18 · actor: orchestrator
- alcance: [[features/025-consola-minima-y-flexible|025-consola-minima-y-flexible]]

## Contexto

El anti-cacheo de fallos transitorios de vault tiene test dedicado sólo en codex_spawn y opencode_spawn (tests/test_spawn_materialization.py:119-145). Por inspección la implementación es idéntica y correcta en los cuatro carriles.

## Decisión

No es defecto vivo. Registrado como deuda. No bloquea el cierre.

## Consecuencias

Si alguien modifica el anti-cacheo en set_agents_spawn o claude_code_spawn sin tests, el defecto pasaría desapercibido.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
