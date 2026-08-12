# Segunda vez que escribo owned_paths con un nombre de ADR que todavia no existe

<!-- notas:auto -->
- fecha: 2026-08-12 · actor: orchestrator
- alcance: [[features/021-gates-que-no-mienten-ni-callan|021-gates-que-no-mienten-ni-callan]] · [[features/021-gates-que-no-mienten-ni-callan/P1-check-que-verifica|P1-check-que-verifica]]

## Contexto

P1-F02: owned_paths de P1 declara docs/adr/0041-gates-que-no-mienten-ni-callan.md y el ADR real es docs/adr/0041-build-check-verifies-global.md. Adivine el nombre del archivo al crear el paquete, antes de que el implementer lo escribiera, y por el mismatch check-owned-paths marca como fuera de alcance justo el ADR que el spec pedia escribir. Es la SEGUNDA vez en la sesion: 020/F-03 fue exactamente el mismo error, con el agravante de que ahi tambien habia dejado un archivo declarado que nunca tuvo diff.

## Decisión

CONTRAMEDIDA PERMANENTE: al crear un paquete, owned_paths lleva el DIRECTORIO del ADR (docs/adr/) o nada, nunca un nombre de archivo inventado. El nombre lo elige quien escribe el ADR, y el numero es lo unico predecible. Si hace falta declararlo con precision, se registra la excepcion cuando el archivo existe.

## Consecuencias

Vale para todo el harness. Mientras owned_paths no sea editable por comando (update-package no expone --owned-path), la correccion se registra como excepcion aprobada.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
