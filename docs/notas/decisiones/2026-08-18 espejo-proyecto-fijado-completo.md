# El espejo PROYECTO/ queda fijado entero, no por lista de nombres

<!-- notas:auto -->
- fecha: 2026-08-18 · actor: orchestrator

## Contexto

test_mirror_parity_ai_scripts_vs_proyecto nombraba tres archivos (narration_lint.py, feature-state.py, cli_reporting.py) y solo esos tres. Medido el 2026-08-18 sobre HEAD=eb9b9ed: de los 24 archivos que viven en los dos arboles, 3 habian derivado y NINGUNO estaba en la lista. render_bitacora.py del template seguia cortando la narracion en 300 caracteres, que ES el hallazgo N3b-F01 de la feature 028, declarado reparado y cerrado. A axes.py del template le faltaba validate_row entera, o sea la validacion por eje de la feature 029, tambien cerrada.

## Decisión

La paridad se afirma sobre el conjunto completo de archivos que existen en los dos arboles, con verify.sh como unica excepcion declarada y justificada (el del harness gatea este repo, el del template sniffea el stack de un proyecto generico: responden preguntas distintas). Las dos derivas se sincronizaron.

## Consecuencias

Dos features en DONE estaban medio entregadas y nada lo decia: la reparacion habia llegado a una de las dos copias. Una lista por nombre solo protege lo que alguien se acordo de anotar. El piso de 23 archivos verificados impide que el espejo se encoja en silencio.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
