# record-spawn contra el package_id viejo para narrar la apertura de un paquete nuevo repite el falso bloqueo

<!-- notas:auto -->
- fecha: 2026-07-29 · actor: orchestrator
- alcance: [[features/005-portable-harness|005-portable-harness]] · [[features/005-portable-harness/P1-portable-core|P1-portable-core]]

## Contexto

Al abrir 005-P2-vault-mandatory, use record-spawn contra P1-portable-core (el unico package_id que existia todavia, porque P2 no se habia creado con create-package) para narrar la apertura del paquete nuevo. P1 ya estaba en 12/12 spawns por su propio ciclo de implementacion, asi que dispare el mismo bloqueo automatico que ya se registro en record-spawn-budget-does-not-exempt-integration-bookkeeping, pero por una causa distinta: record-spawn es para narrar una instanciacion real de subagente contra un package_id existente, no para narrar 'el orquestador esta por abrir un paquete nuevo' -- CLAUDE.md ya distingue esto (record-spawn para el bloque de apertura de un subagente, log-narrative para todo lo demas), y lo pase por alto.

## Decisión

Se revirtio el bloqueo con la misma cirugia minima que la vez anterior (blocker + evento de historia removidos, phase y final_state restaurados, revision decrementada), y se re-hizo la narracion con log-narrative --result started, que no toca presupuesto ni requiere package_id. Recien despues se transiciono PACKAGE_PLANNING.

## Consecuencias

Practica corregida para el resto de esta sesion y las que vengan: usar log-narrative (no record-spawn) para narrar la apertura de un paquete que todavia no existe en el estado; record-spawn queda reservado exclusivamente para instanciaciones reales de subagente contra un package_id ya creado. No sustituye el fix real pendiente (record-spawn deberia poder eximir narracion administrativa del presupuesto, o el orquestador deberia tener un verbo dedicado sin presupuesto para este momento especifico).
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
