# La narracion del orquestador tiene que ensenar, no apuntar a un identificador

<!-- notas:auto -->
- fecha: 2026-08-15 · actor: orchestrator

## Contexto

Pedido directo de Federico el 2026-08-15: 'no quiero que mencione hice el fix de PKG-007, sigue el item A que quedo de spec.md. Eso solo es informacion para el que sabe y recuerda que se encuentra ahi dentro. Quiero que el orquestador intente explicar/ensenar/debatir-proponiendo-ideas cual es el paso a seguir. Yo soy ingeniero y muchas veces no le puedo seguir el estado del proyecto porque no explica.' El diagnostico es preciso: un identificador de paquete y un numero de AC son PUNTEROS, utiles para reanudar trabajo, inutiles para decidir. ADR-0027 ya exige dos registros (Cliente e Ingenieria) pero ninguno de los dos obliga a explicar el porque ni a proponer el siguiente paso con sus alternativas.

## Decisión

La narracion de cierre de cada agente pasa a ser explicativa por contrato, no descriptiva. Minimo exigible: que se entienda sin abrir la spec ni recordar que significa el identificador; que diga que se aprendio y no solo que se hizo; y que el siguiente paso venga con su porque y, cuando haya mas de un camino razonable, con la alternativa y el criterio para elegir. El identificador puede acompanar, nunca sustituir. Se implementa como feature del repo en la doctrina canonica del orquestador, para que valga en cualquier maquina y no solo en la sesion donde se pidio.

## Consecuencias

Cambia lo que el harness produce para su usuario humano, que es el unico consumidor que no puede leer el estado. El riesgo a vigilar es el opuesto: narracion inflada que dice mucho y no informa nada. El criterio de calidad no es longitud sino que un ingeniero que no siguio el hilo pueda tomar la siguiente decision con lo leido. Se necesita un test que muerda: una narracion que solo nombre identificadores tiene que poder detectarse.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
