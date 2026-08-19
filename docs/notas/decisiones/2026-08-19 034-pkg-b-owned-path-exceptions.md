# Excepciones de ownership PKG-B: lifecycle, espejos y docs vivos

<!-- notas:auto -->
- fecha: 2026-08-19 · actor: orchestrator
- alcance: [[features/034-cuota-organica-y-writer-barato|034-cuota-organica-y-writer-barato]] · [[features/034-cuota-organica-y-writer-barato/PKG-B|PKG-B]]

## Contexto

create-package copia next_rung a writer_rung en cli_lifecycle.py, fuera de owned_paths. build.sh regenera Global/* y PROYECTO twins. check-owned-paths vs HEAD sigue viendo el working tree entero incluyendo docs vivos.

## Decisión

Waivers: cli_lifecycle.py, Global/*/, PROYECTO feature_state_lib/, docs/{notas,modules,specs,adr,architecture}/, tests vecinos de init. No se ensancha owned_paths de producto.

## Consecuencias

P001 puede pasar. Un archivo de producto nuevo fuera de esos arboles sigue fallando.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
