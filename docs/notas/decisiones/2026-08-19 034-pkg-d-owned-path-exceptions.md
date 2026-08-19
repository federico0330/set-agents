# Excepciones PKG-D: arboles emitidos y suciedad A/B/C

<!-- notas:auto -->
- fecha: 2026-08-19 · actor: orchestrator
- alcance: [[features/034-cuota-organica-y-writer-barato|034-cuota-organica-y-writer-barato]] · [[features/034-cuota-organica-y-writer-barato/PKG-D|PKG-D]]

## Contexto

build.sh emite Global/cursor y el resto de harnesses. check-owned-paths vs HEAD ve A/B/C sucios. fixtures/models.toml es el twin de catalog.cursor.

## Decisión

Waivers de Global/, PROYECTO/, docs/, tests/fixtures/models.toml y scripts de estado de A/B/C. owned_paths de D no se ensancha.

## Consecuencias

P001 puede pasar.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
