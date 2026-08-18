# Digest no ensucia el diff de un paquete con bitacoras ajenas

<!-- notas:auto -->
- fecha: 2026-08-18 · actor: orchestrator
- alcance: [[features/033-menos-espera-menos-cuota|033-menos-espera-menos-cuota]] · [[features/033-menos-espera-menos-cuota/PKG-5|PKG-5]]

## Contexto

sync-notes/digest reescribio bitacoras de features 002-032. check-owned-paths las conto como out_of_scope de PKG-5. No son trabajo del paquete.

## Decisión

Revertir esas bitacoras a HEAD. Registrar excepciones docs/notas y docs/specs/033-menos-espera-menos-cuota, igual que en PKG-4. El fallo de producto es otro: ImportError tests al invocar verify_reporter.py como script.

## Consecuencias

El gate de ownership deja de mezclar ruido del digest con el diff del paquete.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
