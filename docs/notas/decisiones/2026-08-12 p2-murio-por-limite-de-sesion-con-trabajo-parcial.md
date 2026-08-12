# El implementer de P2 murio por limite de sesion con AC-06, 08 y 09 hechos y AC-07 pendiente

<!-- notas:auto -->
- fecha: 2026-08-12 · actor: orchestrator
- alcance: [[features/021-gates-que-no-mienten-ni-callan|021-gates-que-no-mienten-ni-callan]] · [[features/021-gates-que-no-mienten-ni-callan/P2-gates-que-no-callan|P2-gates-que-no-callan]]

## Contexto

run1_6bffcca9361c13a28ea235b3412105de termino con 'You've hit your session limit'. No es stall ni falla en la tarea: es agotamiento de cuota, que por doctrina no consume presupuesto de reintentos. Verificado en disco por el orquestador que dejo trabajo REAL y utilizable: ai/scripts/heartbeat-run.py nuevo (AC-06), tests/test_harness.py +117 lineas con tres tests que PASAN, TIPS-USO.md y ADR-0041 extendido (AC-08), y su archivo de evidencia. Lo que falta es AC-07: Global/_canonical/ no fue tocado, o sea que la doctrina todavia no dice que hacer en vez del antipatron.

## Decisión

Se relanza acotado UNICAMENTE a AC-07. El resto no se rehace: esta hecho, testeado y verificado. La mitigacion de escribir a disco por tramo funciono -- es la tercera vez en la sesion que un agente muere y deja trabajo aprovechable en vez de nada.

## Consecuencias

El orquestador se equivoco DOS veces al evaluar este estado: primero dijo que faltaban los dos AC de fondo (habia buscado el latido dentro de verify.sh, cuando vive en un archivo nuevo), y despues tuvo que corregirse de nuevo. Octava y novena afirmacion de la sesion que no resiste la verificacion. La leccion se repite: mirar donde uno espera no es medir.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
