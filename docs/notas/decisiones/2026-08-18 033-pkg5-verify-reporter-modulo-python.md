# El presenter del gate vive en un modulo Python testeable, no en el shell

<!-- notas:auto -->
- fecha: 2026-08-18 · actor: orchestrator
- alcance: [[features/033-menos-espera-menos-cuota|033-menos-espera-menos-cuota]] · [[features/033-menos-espera-menos-cuota/PKG-5|PKG-5]]

## Contexto

verify.sh no es testeable sin TTY. AC-5.1 a 5.5 exigen un TestResult/TestRunner propio y un test de que el conjunto ejecutado no cambia. El pack recomienda extraer el reporter a un .py bajo ai/scripts/ cuando exista, sin adivinar el nombre.

## Decisión

El implementer escribe ai/scripts/verify_reporter.py y tests/test_verify_reporter.py. Esas dos rutas se registran como excepciones de owned_paths (update-package no expone --owned-path). verify.sh solo invoca el reporter. AC-5.6 no se implementa en este paquete salvo prueba de aislamiento.

## Consecuencias

Si el implementer elige otro nombre, para y reporta; no se adivina un tercero.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
