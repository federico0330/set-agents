# Excepciones PKG-C: suciedad de A/B, espejos y docs

<!-- notas:auto -->
- fecha: 2026-08-19 · actor: orchestrator
- alcance: [[features/034-cuota-organica-y-writer-barato|034-cuota-organica-y-writer-barato]] · [[features/034-cuota-organica-y-writer-barato/PKG-C|PKG-C]]

## Contexto

check-owned-paths vs HEAD ve el working tree entero. models.toml y cli_repair.py son de B; canonicos y docs de A/B; build.sh regenera Global y PROYECTO.

## Decisión

Waivers de directorio para Global, PROYECTO, docs, y archivos puntuales de A/B. owned_paths de C no se ensancha.

## Consecuencias

P001 puede pasar sin atribuir a C el lote anterior.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
