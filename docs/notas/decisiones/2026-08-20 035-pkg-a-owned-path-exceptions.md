# Excepciones PKG-A: suciedad de spec/consult/notas

<!-- notas:auto -->
- fecha: 2026-08-20 · actor: orchestrator
- alcance: [[features/035-panel-honesto-consola-y-tips|035-panel-honesto-consola-y-tips]] · [[features/035-panel-honesto-consola-y-tips/PKG-A|PKG-A]]

## Contexto

check-owned-paths vs HEAD 788eb62 ve spec 035, design.md, overview.md, COMO-FUNCIONA.md (consult/PKG-C, tambien read_only) y docs/notas regeneradas. owned_paths de PKG-A no se ensancha.

## Decisión

Waivers de docs/architecture/overview.md, docs/specs/README.md, docs/specs/035-panel-honesto-consola-y-tips (incluye design/context/spec; evidence ya es owned), docs/COMO-FUNCIONA.md y docs/notas. El candado de codigo sigue en feature_state_lib, twins, tests, Global y docs/adr.

## Consecuencias

P001/owned-paths puede pasar sin atribuir a PKG-A el corte C ni las notas vivas.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
