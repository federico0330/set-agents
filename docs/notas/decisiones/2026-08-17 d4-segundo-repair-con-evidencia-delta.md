# D4 usa el último repair batch con evidencia directa del delta

<!-- notas:auto -->
- fecha: 2026-08-17 · actor: orchestrator
- alcance: [[features/025-consola-minima-y-flexible|025-consola-minima-y-flexible]] · [[features/025-consola-minima-y-flexible/D4-harness-por-CLI|D4-harness-por-CLI]]

## Contexto

El paquete tiene 7 de 8 spawns; delta independiente ya reprodujo F01 y DR02 sobre el árbol integrado.

## Decisión

Por presupuesto, el delta documentado opera como verificación de F01 para el segundo repair; se reserva el único spawn restante para implementar ambos cambios.

## Consecuencias

El cierre posterior usará testing/runtime QA integrado y no podrá abrir un tercer repair.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
