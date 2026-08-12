# HUMAN_DECISION_REQUIRED: sexto stall de la sesion y segunda muerte del review de P2

<!-- notas:auto -->
- fecha: 2026-08-12 · actor: orchestrator
- alcance: [[features/021-gates-que-no-mienten-ni-callan|021-gates-que-no-mienten-ni-callan]] · [[features/021-gates-que-no-mienten-ni-callan/P2-gates-que-no-callan|P2-gates-que-no-callan]]

## Contexto

El package-reviewer de P2 murio dos veces con 'no progress for 600s'. La segunda murio TEMPRANO -- sus ultimas palabras fueron 'ahora leo la evidencia del implementer y el ADR' -- o sea NO esperando la suite, que era la hipotesis del orquestador. Eso descarta la explicacion anterior. Seis stalls en una sesion, en roles mutadores y read-only, uno de ellos leyendo archivos: es el entorno de ejecucion, no la redaccion de los encargos ni el patron del pipe. La doctrina propia del orquestador dice: un relanzamiento por asignacion, y una segunda muerte de la misma asignacion es un blocker real que se reporta.

## Decisión

NO se intenta un tercer relanzamiento identico. Se reporta como blocker y se le ofrecen a Federico tres caminos: (a) partir el review en dos encargos mas chicos, cada uno con menos ejes y sin correr la suite completa; (b) que el orquestador haga una verificacion reducida y la etiquete explicitamente como NO-review-independiente, dejando el paquete aceptado con esa salvedad registrada; (c) esperar y reintentar mas tarde, si el entorno mejora. El orquestador recomienda (a): conserva la independencia, que es lo que el paquete necesita, y ataca la unica variable que controlamos, que es el tamano del encargo.

## Consecuencias

P2 queda implementado con sus cuatro AC hechos y los gates en verde (977 OK / 2 skips, VERIFY_PASS, GLOBAL_TREE_SYNC_OK + BUILD_CHECK_PASS, git diff --check limpio), pero SIN review independiente. 021 no puede pasar a DONE hasta resolverlo. El arbol quedo sano tras las dos muertes, verificado.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
