# Defecto latente: matching_modules no entiende la semantica nueva de owned_paths

<!-- notas:auto -->
- fecha: 2026-08-15 · actor: orchestrator
- alcance: [[features/027-controles-que-miran|027-controles-que-miran]] · [[features/027-controles-que-miran/P4-owned-paths-matchea-directorios|P4-owned-paths-matchea-directorios]]

## Contexto

El reviewer independiente de 027/P4 (hallazgo P4-F07, low, preexistente) encontro un segundo consumidor de owned_paths que va a discrepar del gate de alcance: ai/scripts/feature_state_lib/render_modules.py:104-125 y :144-152 hacen fnmatch(candidate_path, module_pattern) usando el string de owned_paths como si fuera una ruta. Con la semantica que P4 introduce, owned_paths ['tests'] significa 'todo tests/' para check-owned-paths.py, pero fnmatch('tests', 'tests/**') es False, asi que la deteccion de impacto de modulos da cero hits donde la grafia 'tests/**' si daba hits. Es la limitacion F-06 que el propio docstring ya documenta (:110-118, ADR-0036) y es solo advisory: nunca gatea nada.

## Decisión

No se repara dentro de P4. render_modules.py no esta en los owned_paths del paquete y arreglarlo seria un refactor oportunista, que la doctrina del harness prohibe. Se registra como defecto latente, medido y con su file:line, en la misma familia que F-06, para que lo tome una feature que sea duena de ese archivo.

## Consecuencias

P4 convierte la grafia de directorio pelado en ciudadana de primera, asi que la probabilidad de caer en este punto ciego sube: cuantos mas paquetes declaren 'tests' en vez de 'tests/**', mas seguido la deteccion de impacto de modulos va a informar cero hits sin que nadie lo note. Es advisory, no bloqueante, pero es exactamente la forma de los seis defectos que la feature 027 vino a reparar: algo que informa OK sobre algo que no mira.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
