# Cuarto desliz de bookkeeping del orquestador: omiti --route-dispatched en un relanzamiento

<!-- notas:auto -->
- fecha: 2026-08-12 · actor: orchestrator
- alcance: [[features/021-gates-que-no-mienten-ni-callan|021-gates-que-no-mienten-ni-callan]]

## Contexto

Al relanzar el implementer de P2 acotado a AC-07 corri --route-decide y record-spawn pero NO --route-dispatched. El run quedo en authorized, el --route-terminal success posterior no lo registro como writer, y el --route-decide del reviewer devolvio REVIEW_IDENTITY_INVALID. Lo mismo habia pasado con el writer de 019/P4, que tambien habia quedado sin cerrar.

## Decisión

Corregido dispatchando y cerrando el run en orden. LECCION: la secuencia route-decide -> record-spawn -> route-dispatched es una unidad; omitir el tercer paso rompe la verificacion de independencia del reviewer siguiente, y el sintoma (REVIEW_IDENTITY_INVALID) no dice cual fue el paso que falto. Vale para todo relanzamiento, que es justo donde se saltea porque uno cree estar repitiendo algo ya hecho.

## Consecuencias

Cuarto desliz de bookkeeping del orquestador en la sesion, sumado a los dos de owned_paths y al presupuesto de verificacion contado por llamadas. Todos del mismo tipo: estado que el orquestador debe mantener a mano y ninguna herramienta le recuerda. Candidato claro a mejora del harness -- no esta en el plan aprobado y queda propuesto, no hecho.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
