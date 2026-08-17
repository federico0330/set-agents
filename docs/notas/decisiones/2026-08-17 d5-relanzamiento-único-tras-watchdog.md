# D5 relanzamiento único tras watchdog

<!-- notas:auto -->
- fecha: 2026-08-17 · actor: orchestrator
- alcance: [[features/025-consola-minima-y-flexible|025-consola-minima-y-flexible]] · [[features/025-consola-minima-y-flexible/D5-vault-en-todo-spawn|D5-vault-en-todo-spawn]]

## Contexto

El implementador inicial dejó checkpoint parcial D5-implementation.md sin commit; el watchdog agotó su ventana.

## Decisión

Relanzar una vez con otro modelo, conservar cambios/evidencia parciales y exigir commit o checkpoint final.

## Consecuencias

No se consume una nueva decisión de producto; si vuelve a agotarse, se registra bloqueo operativo real.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
