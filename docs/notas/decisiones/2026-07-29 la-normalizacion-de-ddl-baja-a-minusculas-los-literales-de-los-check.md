# El comparador de DDL acepta una base cuyos CHECK enumeran valores distintos, porque normaliza a minusculas tambien adentro de los literales

<!-- notas:auto -->
- fecha: 2026-07-29 · actor: orchestrator
- alcance: [[features/007-quota-visibility|007-quota-visibility]] · [[features/007-quota-visibility/P1-schema-normalize|P1-schema-normalize]]

## Contexto

Encontrado por el orquestador verificando el 'pass' sin hallazgos del package-reviewer, no por el panel. La normalizacion aplica .lower() al texto entero, literales de string incluidos -- conducta PREEXISTENTE, identica antes y despues de 007-P1. SQLite compara strings con sensibilidad a mayusculas. Reproducido punta a punta contra un archivo de estado descartable: una base schema-5 cuyo CHECK del estado enumera ('AUTHORIZED','DISPATCHED',...) en vez de ('authorized','dispatched',...) normaliza IGUAL al canonico, _validate_existing_readonly la ACEPTA, y despues el primer insert del propio arnes muere con 'CHECK constraint failed'. O sea el comparador abre una base que deberia rechazar, y el fallo se muda de la apertura al runtime.

## Decisión

Se registra y no se repara en P1. Es preexistente, no lo empeora este paquete, y arreglarlo es tightening: dejar de bajar a minusculas cambia QUE BASES YA EN DISCO validan, que es exactamente el invariante que el context pack de P1 declara intocable. Un cambio asi necesita su propio paquete y su propia decision sobre las instalaciones existentes. La reparacion natural es no bajar a minusculas adentro de los tramos citados -- la maquina de estados de _normalize_ddl ya los identifica, asi que el cambio es de pocas lineas y el riesgo esta entero del lado de la compatibilidad, no de la implementacion.

## Consecuencias

Deja dicho ademas que el argumento con el que el package-reviewer sostuvo su veredicto limpio es FALSO: afirmo que 'ningun DDL divergente puede normalizar igual al canonico porque los largos van a diferir', y aca los largos son identicos y los DDL son semanticamente distintos. El veredicto puede ser correcto para el alcance de P1; el lema que lo sostiene no lo es, y un lema falso en un registro de review es peor que un hallazgo de mas porque el proximo revisor lo hereda como establecido. La degradacion de tier del panel (haiku por agotamiento de cuota) queda registrada aparte como excepcion aprobada.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
