# El control de alcance no ve los archivos nuevos: usa git diff, que solo lista trackeados

<!-- notas:auto -->
- fecha: 2026-08-13 · actor: orchestrator
- alcance: [[features/022-disponibilidad-real|022-disponibilidad-real]] · [[features/022-disponibilidad-real/P1-registro-de-proveedores|P1-registro-de-proveedores]]

## Contexto

check-owned-paths.py:40-42 obtiene los archivos cambiados con 'git diff --name-only <baseline> --', que NO lista archivos sin trackear. Medido en 022/P1: el paquete creo ai/scripts/provider_registry.py -el archivo central, el registro unico del que derivan siete tablas- y NO figura en owned_paths ni aparece en out_of_scope. El chequeo dio OWNERSHIP_FAIL por cinco archivos trackeados y guardo silencio sobre el unico archivo nuevo. Tambien se midio que 'docs/adr' en owned_paths no cubre docs/adr/README.md: no se trata como prefijo de directorio.

## Decisión

Se registran approved_exceptions para los cinco archivos y se deja constancia de las dos fallas del propio chequeo. NO se arregla en P1: esta fuera de su alcance y el reparador de un control no puede ser el paquete que el control acaba de aprobar.

## Consecuencias

Un paquete puede crear cualquier archivo, en cualquier lugar del repo, y el control de alcance nunca lo nota. Es la misma clase de defecto que 021 cerro en build.sh --check y que el review de este paquete encontro en dos guardas: un control que informa OK sobre algo que no mira. Candidato directo a una feature de la familia 'gates que no mienten'. Reproducible: crear un archivo nuevo y correr check-owned-paths.py contra cualquier baseline.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
