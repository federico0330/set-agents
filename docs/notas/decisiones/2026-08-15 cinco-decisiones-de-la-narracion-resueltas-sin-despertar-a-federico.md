# Las cinco preguntas del desafio a 028, resueltas con doctrina vigente

<!-- notas:auto -->
- fecha: 2026-08-15 · actor: orchestrator

## Contexto

El spec-challenger de 028 devolvio 'no aprobable' con 15 objeciones y cinco preguntas dirigidas al usuario. Federico esta durmiendo y pidio explicitamente no detener la ejecucion. ADR-0037 (resolve antes de preguntar) obliga a revisar primero el pedido original, docs/notas, decisions-log y la spec/ADRs aprobados: las cinco quedan resueltas ahi, ninguna es una decision de producto incompatible.

## Decisión

1) Los cuatro campos que ensenan son obligatorios solo en los HITOS de ADR-0027, no en los spawns intra-fase que orchestrator.md:712 declara 'persisted, not narrated': exigirlos donde nadie los lee fabrica ritual, que es el riesgo opuesto que Federico no nombro pero va a sufrir. 2) --alternative obligatorio solo en blocked de causa tecnica y en PACKAGE_PLANNING, la unica bifurcacion real de la maquina, con --alternative none como valor legal: next_transition RESUELVE la bifurcacion, no la ofrece (transitions.py:66-71). 3) archivo.py:linea permitido en tech porque ADR-0026 lo exige como evidencia, prohibido como contenido unico en learned/next/why. 4) Los paquetes se reordenan a N3a -> N1 -> N2 -> N3b: AC-11..14 no dependen de nada y son lo unico que Federico puede VER en una manana. 5) El digest se regenera en cierre de fase o de turno, no en cada mutacion, porque BUENOS-DIAS.md esta trackeado en git y STATUS.md no (024/C1), y regenerarlo siempre lo mete en el diff de toda feature en vuelo.

## Consecuencias

Ninguna de las cinco cambia la intencion del pedido de Federico; las cinco la protegen del fracaso mas probable, que es que la feature se vuelva tramite. Quedan como decisiones del orquestador, revisables por el cuando despierte, no como supuestos tapados. La objecion central del challenger -que la guarda es la falsa-verde numero once, con 8 de 9 bypasses pasando al primer intento, incluida la narracion exacta que Federico rechazo con un espacio en vez de un guion- NO se resuelve por decision: vuelve al analista como enmienda E-1, con la alternativa honesta de declarar AC-04 como piso de longitud si la prueba de oracion no es implementable.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
