# owned_paths escrito contra un diseno que el ADR despues cambio: error del orquestador, no del implementer

<!-- notas:auto -->
- fecha: 2026-08-12 · actor: orchestrator
- alcance: [[features/020-honest-dashboard|020-honest-dashboard]] · [[features/020-honest-dashboard/P1-digest-no-esconde|P1-digest-no-esconde]]

## Contexto

Al crear P1 declare owned_paths con render_notes.py como sede del predicado compartido. ADR-0040 despues decidio ponerlo en model.py y descarto render_notes.py explicitamente en sus alternativas rechazadas. Nunca actualice owned_paths, asi que el archivo donde vive el corazon de AC-02 quedo fuera del alcance declarado, junto con cli_lifecycle.py (AC-04) y tests/test_digest.py. Ademas el nombre del ADR en la lista era inventado (0040-honest-dashboard.md; el real es 0040-honest-digest-shared-liveness-predicate.md). El reviewer lo probo con check-owned-paths.py del propio repo: OWNERSHIP_FAIL rc=2.

## Decisión

Se registran las tres rutas faltantes como excepciones aprobadas con su razon, y se deja constancia de que render_notes.py sobra en la lista. update-package no expone --owned-path, asi que la excepcion es el mecanismo disponible; no se edita el JSON a mano. LECCION DURABLE: cuando el ADR fija un diseno distinto al que se planeo al crear el paquete, owned_paths se actualiza en el mismo movimiento -- si no, el gate de ownership deja de ser una verdad verificable y pasa a ser una lista vieja de una intencion temprana. Vale para todo el harness.

## Consecuencias

check-owned-paths.py va a seguir reportando la diferencia hasta que exista una via para editar owned_paths; las excepciones dejan el porque auditable.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
