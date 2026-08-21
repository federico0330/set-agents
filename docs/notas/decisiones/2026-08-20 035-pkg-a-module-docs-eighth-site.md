# T-006 octavo sitio: test_module_docs _init_ready_package

<!-- notas:auto -->
- fecha: 2026-08-20 · actor: orchestrator
- alcance: [[features/035-panel-honesto-consola-y-tips|035-panel-honesto-consola-y-tips]] · [[features/035-panel-honesto-consola-y-tips/PKG-A|PKG-A]]

## Contexto

verify.sh independiente (spawn 3/8, gate-runner eb3f6912) dejo 6 ERROR en tests.test_module_docs. Causa: _init_ready_package usa create-package --complexity medium y despues record-review pass. T-006 solo barrio test_harness.py. test_module_docs.py:374 es otro medium pero no llama record-review.

## Decisión

Reescribir _init_ready_package al camino del panel (start-review-panel + record-subreview x2 + finalize-review-panel). NUNCA bajar complexity a small. Exception approved para tests/test_module_docs.py. owned_paths de PKG-A no se ensancha de forma permanente.

## Consecuencias

debugger spawn 4/8; re-gate independiente despues. Un strike cheap_strike_recorded por verify fail.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
