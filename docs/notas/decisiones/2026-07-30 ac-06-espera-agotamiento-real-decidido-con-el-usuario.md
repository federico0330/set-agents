# El usuario elige esperar un agotamiento real de cuota en vez de forzarlo o relajar AC-06

<!-- notas:auto -->
- fecha: 2026-07-30 · actor: orchestrator
- alcance: [[features/011-quota-failover|011-quota-failover]] · [[features/011-quota-failover/P1-quota-failover|P1-quota-failover]]

## Contexto

P1-quota-failover quedo BLOCKED en PACKAGE_GATES: el runner E2E de AC-06 (credential-gated) verifico correctamente que no hay una suscripcion Anthropic genuinamente agotada disponible en esta sesion, y se detuvo fail-closed sin abrir la DB ni invocar Pi. El propio contrato de 011 (Contracts #6) exige que sin esa precondicion el criterio quede BLOCKED/HUMAN_DECISION_REQUIRED, nunca passing ni waived.

## Decisión

Preguntado explicitamente, el usuario elige la opcion de menor riesgo: dejar 011 en BLOCKED y esperar a que una suscripcion se agote de verdad en el uso normal del arnes. En ese momento se corre el runner E2E ya construido (credential-gated, documentado en el paquete) y recien ahi se acepta P1-quota-failover. No se fuerza un agotamiento a proposito (evita gasto real innecesario) ni se acepta el paquete sin la prueba en vivo (evita relajar una exigencia que el propio contrato escribio para prevenirlo).

## Consecuencias

011 permanece BLOCKED indefinidamente, sin fecha. 008-P3 (budget-aware selection, modelo de dos capas) sigue dependiendo de que P1b/011 este accepted, asi que tambien queda a la espera. 008-P2 (discovered-inventory) no depende logicamente de la memoria de agotamiento de P1b y puede avanzar en paralelo sin esperar a 011.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
