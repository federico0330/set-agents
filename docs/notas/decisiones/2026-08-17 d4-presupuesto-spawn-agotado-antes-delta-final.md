# D4 agotó su presupuesto de spawns antes del delta final

<!-- notas:auto -->
- fecha: 2026-08-17 · actor: orchestrator
- alcance: [[features/025-consola-minima-y-flexible|025-consola-minima-y-flexible]] · [[features/025-consola-minima-y-flexible/D4-harness-por-CLI|D4-harness-por-CLI]]

## Contexto

El segundo repair de D4 cerró F01/DR02 y fue probado, pero el paquete ya consumió los 8 spawns por un gate inicial incompleto y un review interrumpido por policy.

## Decisión

No autoaprobar ni registrar un delta sin revisor independiente; bloquear la feature hasta que se autorice ampliar D4 en una instancia delta-reviewer o una excepción explícita.

## Consecuencias

D4 queda en DELTA_REVIEW; D5, 028, 029, 030 e integración no deben adelantarse.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
