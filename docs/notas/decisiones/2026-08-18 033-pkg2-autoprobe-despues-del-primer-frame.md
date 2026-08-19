# El vivo llega solo despues del primer frame; el test de labels se aisla

<!-- notas:auto -->
- fecha: 2026-08-18 · actor: orchestrator
- alcance: [[features/033-menos-espera-menos-cuota|033-menos-espera-menos-cuota]] · [[features/033-menos-espera-menos-cuota/PKG-2|PKG-2]]

## Contexto

El revisor sostuvo que la tecla Refrescar no puede ser el unico probe. El test de labels del harness entra al wizard sin mock del probe.

## Decisión

Si el cache falta o vencio, el segundo ciclo del menu mide vivo con with_progress y vuelve a pintar. La tecla Refrescar sigue forzando. Primer frame sigue sin probe. El test de labels mockea detect_subscriptions. None de primer frame no se etiqueta como probe fallido; despues del vivo se llena live_discovered.

## Consecuencias

Hay que ampliar la excepcion de owned-paths a tests/test_harness.py. El techo de repair queda en 200 lineas.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
