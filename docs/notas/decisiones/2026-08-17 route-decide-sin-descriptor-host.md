# route-decide sin descriptor en host OpenCode

<!-- notas:auto -->
- fecha: 2026-08-17 · actor: orchestrator
- alcance: [[features/025-consola-minima-y-flexible|025-consola-minima-y-flexible]] · [[features/025-consola-minima-y-flexible/D1-superficie-humana|D1-superficie-humana]]

## Contexto

Bash del orquestador niega pipes y escritura. route-decide necesita JSON por archivo o stdin.

## Decisión

Spawn BASE finding-verifier por Task host con MODEL_STATIC_FALLBACK declarado.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
