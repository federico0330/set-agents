# Excepciones PKG-C por A y B sin commitear

<!-- notas:auto -->
- fecha: 2026-08-21 · actor: orchestrator
- alcance: [[features/035-panel-honesto-consola-y-tips|035-panel-honesto-consola-y-tips]] · [[features/035-panel-honesto-consola-y-tips/PKG-C|PKG-C]]

## Contexto

A y B accepted, working tree sucio vs 788eb62. check-owned-paths de C veria ai/scripts, Global, tests, adr, bitacoras. C solo posee TIPS, COMO-FUNCIONA, README y evidence.

## Decisión

update-package --exception sobre suciedad de A/B y docs vivas. No ensancha owned_paths. No autoriza editar codigo.

## Consecuencias

El candado de C sigue en TIPS-USO.md, docs/COMO-FUNCIONA.md, README.md y evidence.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
