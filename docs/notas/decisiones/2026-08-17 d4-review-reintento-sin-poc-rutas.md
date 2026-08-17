# D4 relanza revisión de producto sin PoC de rutas

<!-- notas:auto -->
- fecha: 2026-08-17 · actor: orchestrator
- alcance: [[features/025-consola-minima-y-flexible|025-consola-minima-y-flexible]] · [[features/025-consola-minima-y-flexible/D4-harness-por-CLI|D4-harness-por-CLI]]

## Contexto

El revisor identificó AC-11 diferido, pero su segundo experimento de rutas quedó bloqueado por el filtro de seguridad y no dejó evidencia final.

## Decisión

Se descarta el análisis incompleto y se relanza una sola revisión read-only del comportamiento AC-11/documentación, sin pruebas de seguridad ofensivas.

## Consecuencias

El hallazgo de AC-11 se decide por artefactos y runtime observable; rutas quedan fuera de este pase.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
