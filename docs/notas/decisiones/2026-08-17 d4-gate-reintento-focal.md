# D4 relanza el gate focal por evidencia incompleta

<!-- notas:auto -->
- fecha: 2026-08-17 · actor: orchestrator
- alcance: [[features/025-consola-minima-y-flexible|025-consola-minima-y-flexible]] · [[features/025-consola-minima-y-flexible/D4-harness-por-CLI|D4-harness-por-CLI]]

## Contexto

El primer gate ejecutó una suite amplia que fue interrumpida y no creó evidencia de sandbox ni veredicto.

## Decisión

No se registra como gate; se relanza una sola vez con pruebas temporales cerradas de AC-09..11 y sin unittest global.

## Consecuencias

El siguiente resultado, exitoso o fallido, queda como evidencia del paquete.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
