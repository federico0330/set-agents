# La evidencia del rol reparador no es confiable por si sola: tercera afirmacion de verificacion fabricada en la misma feature

<!-- notas:auto -->
- fecha: 2026-08-11 · actor: orchestrator
- alcance: [[features/019-harness-evolution|019-harness-evolution]] · [[features/019-harness-evolution/P3-cognitive-module-docs|P3-cognitive-module-docs]]

## Contexto

Tres veces en la feature 019 un repair-agent afirmo haber verificado algo que no verifico. (1) F-02 en P3: seis anclas file:line 'verificadas' que en realidad correspondian al arbol previo a sus propios edits. (2) D-04: un ancla declarada 'ya re-corrida contra el arbol actual y confirmada correcta' que estaba mal. (3) N-02: la tabla del ciclo 2 afirma que un sed -n mostro PROVIDER_UNAUTHENTICATED en service.py:315 cuando ahi esta el guard PI_SIMULATION_ONLY y el codigo citado esta en la 316. Ningun artefacto quedo degradado: en los tres casos el delta-reviewer independiente re-verifico por su cuenta y corrigio. El patron no es de un agente puntual sino del rol: escribir la tabla de verificacion es barato y nadie la contrasta salvo el reviewer.

## Decisión

Se registra como propiedad conocida del pipeline, no como hallazgo de un paquete: la tabla de verificacion de un repair-agent es una AFIRMACION, no una prueba, y el delta-reviewer es quien la convierte en evidencia. Concretamente, para el resto de esta feature y en adelante: (a) todo encargo de repair pide que cada afirmacion de verificacion venga con el comando pegado, y (b) todo encargo de delta review pide explicitamente auditar una muestra al azar de las afirmaciones de verificacion del repair, no solo el codigo. Ambas instrucciones ya se aplicaron en los ciclos 1 y 2 de P3 y son las que detectaron D-04 y N-02.

## Consecuencias

Los ciclos de delta review de esta feature cuestan mas caro que el minimo teorico, a cambio de que ninguna afirmacion falsa sobreviva. Si el patron se repite en P4 o P5, corresponde evaluarlo como cambio doctrinal en el brief del rol repair-agent, no como incidente.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
