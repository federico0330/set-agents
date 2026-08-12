# Commitear un paquete que esta en PACKAGE_REVIEW: guardar no es aceptar

<!-- notas:auto -->
- fecha: 2026-08-12 · actor: orchestrator
- alcance: [[features/021-gates-que-no-mienten-ni-callan|021-gates-que-no-mienten-ni-callan]]

## Contexto

El package-reviewer de 021/P1 señalo, con razon, que el orquestador commiteo a main local (3c50d9f) un paquete que en ese momento estaba en PACKAGE_REVIEW con su propia revision en curso, y que eso es inusual respecto de la separacion de fases declarada. Re-anclо sus comandos a --baseline 76b50a7 y verifico que el contenido era identico, asi que no invalido su trabajo.

## Decisión

El commit fue una operacion de RESGUARDO, no de aceptacion, y el mensaje lo dice explicito: '021/P1 (ADR-0041) -- IMPLEMENTADO Y CON GATES VERDES, BAJO REVIEW'. El disparador fue concreto: 234 archivos y 32321 lineas de una sesion entera vivian sin commitear, con riesgo real de perderse, y Federico lo autorizo cuando se lo planteo. La maquina de estados no cambio: el paquete siguio en PACKAGE_REVIEW y ahora esta en repair. Nada se acepto por estar commiteado.

## Consecuencias

Regla que queda: un commit no adelanta ninguna fase ni sustituye ningun gate; el estado de la feature es la unica autoridad sobre si algo esta aceptado. Y cuando se commitea con un review en vuelo, el mensaje tiene que decirlo -- que es lo que permitio al reviewer re-anclar su baseline sin perder trabajo. Si en el futuro se quiere evitar la ambiguedad, la alternativa es commitear solo hasta el ultimo paquete aceptado, a costa de dejar el resto sin resguardo.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
