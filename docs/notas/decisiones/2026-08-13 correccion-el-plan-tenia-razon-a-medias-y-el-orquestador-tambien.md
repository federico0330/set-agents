# Correccion: el plan tenia razon sobre un camino que la base no exhibia

<!-- notas:auto -->
- fecha: 2026-08-13 · actor: orchestrator
- alcance: [[features/023-senales-de-consumo|023-senales-de-consumo]] · [[features/023-senales-de-consumo/B1-registro-que-no-miente|B1-registro-que-no-miente]]

## Contexto

El orquestador re-midio el diagnostico del plan y concluyo que era FALSO: la base mostraba 54 'absent' y ningun 'ok' con NULLs, y --usage no aparecia en la doctrina canonica. Sobre esa base enmendo la spec de 023.

## Decisión

CORRECCION. El implementer de B1 encontro que claude_code_spawn.py:602-605 y opencode_spawn.py:318-321 SI adjuntan --usage en cada dispatch, con las formas {'total_cost_usd','modelUsage'} y {'tokens'}, que _usage_row NO reconoce. Antes del endurecimiento de AC-02 esas formas producian exactamente lo que el plan describia: usage_status='ok' con todas las columnas en NULL. Verificado en la base: 0 filas 'ok' con todo NULL y 0 'invalid', porque esos lanes no se ejercitaron -esta sesion despacho por la herramienta Agent y por codex exec, y el orquestador cerro los runs a mano-. O sea el plan describia un defecto REAL Y LATENTE que la base no exhibia, no una falsedad.

## Consecuencias

Las dos mitades son ciertas y ninguna sola alcanza: (a) la doctrina nunca pide --usage al orquestador, que es lo que B1 arregla; (b) los lanes de spawn lo mandan en una forma que el store descarta, que es lo que falta. El endurecimiento de AC-02 convierte ese descarte silencioso en 'invalid' contado, pero NO traduce las formas. Cablear los adaptadores de spawn a routing_core/usage.py entra al alcance de B2, que hasta ahora era solo el doble conteo. La leccion de proceso: el orquestador afirmo 'el plan se equivocaba' con una medicion correcta pero parcial -miro la base y no el codigo de los lanes-, y lo dijo al usuario antes de que un segundo actor lo revisara.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
