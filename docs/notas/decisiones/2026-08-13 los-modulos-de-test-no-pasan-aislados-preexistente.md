# Los modulos de test no pasan aislados, y es preexistente

<!-- notas:auto -->
- fecha: 2026-08-13 · actor: orchestrator
- alcance: [[features/022-disponibilidad-real|022-disponibilidad-real]]

## Contexto

Al correr un test dirigido de tests/test_harness.py aparecio ModuleNotFoundError: No module named 'provider_registry'. models_config.py lo importa a nivel de modulo desde ADR-0042, y el _import de test_harness carga por ruta sin poner ai/scripts en sys.path. La sospecha inicial del orquestador fue que 022 lo habia introducido.

## Decisión

MEDIDO Y DESCARTADO como regresion de 022. 'python3 -m unittest tests.test_harness' aislado da hoy 118 errores; el mismo comando sobre un checkout limpio del commit b119ca7, ANTES de 022, da 120 errores y 2 failures. O sea el aislamiento ya estaba roto y 022 lo dejo levemente mejor. No se toca en esta feature.

## Consecuencias

Defecto latente real y registrado: la suite solo pasa ENTERA, porque algun modulo parchea sys.path antes que los demas y el resto se beneficia del efecto colateral. Un CI que corra modulos por separado, o cualquiera que corra un test dirigido, ve rojo. Es la misma familia que 021 cerro en build.sh --check: algo que pasa por la razon equivocada. Candidato a paquete propio junto con check-owned-paths.py -que no ve archivos nuevos- y el orden del gate de pi en _probe_pairs.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
