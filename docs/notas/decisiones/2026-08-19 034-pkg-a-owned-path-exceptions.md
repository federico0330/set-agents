# Excepciones de ownership PKG-A: docs vivos, spec 034 y suciedad 033

<!-- notas:auto -->
- fecha: 2026-08-19 · actor: orchestrator
- alcance: [[features/034-cuota-organica-y-writer-barato|034-cuota-organica-y-writer-barato]] · [[features/034-cuota-organica-y-writer-barato/PKG-A|PKG-A]]

## Contexto

check-owned-paths vs HEAD lista el working tree entero, incluyendo notas regeneradas, ADRs 0060-0064, spec 034, y leftovers 033 que ya estaban sucios al arrancar. El implementer de PKG-A no es duenio de esos arboles.

## Decisión

Waivers de directorio: docs/notas/, docs/modules/, docs/specs/, docs/adr/, docs/architecture/. Se suman a los mirrors Global/*/PROYECTO y tests vecinos ya aprobados. No ensancha owned_paths de producto.

## Consecuencias

P001 vuelve a correr. Un archivo de producto fuera de esos arboles sigue fallando el gate.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
