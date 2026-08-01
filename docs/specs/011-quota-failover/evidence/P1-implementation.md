# P1 — checkpoint de implementación (Feature 011)

Estado: `partial` — no aprobado.

## Cambios aplicados

- Schema aditivo 6→7: `dispatches.replacement_of_run_id` con FK propia, índice parcial único, `terminal_outcome` y tabla global `provider_exhaustions`.
- Predicado puro y fail-closed para el único error Pi/Anthropic permitido (`settled`, `400`, `invalid_request_error`, `out of extra usage`).
- Inicio de `close_exhausted_and_authorize_replacement` bajo `BEGIN IMMEDIATE`, con cierre/uso observado del original, exclusión UTC global y despacho enlazado por la identidad fallback guardada.
- La selección ordinaria y la autorización durable rechazan un proveedor con exclusión vigente.
- Adaptador Pi/CLI sólo transmite los hechos normalizados allowlisted, sin cuerpo crudo del provider.

## Validaciones ejecutadas

```text
python3 -m py_compile ai/scripts/routing_core/domain.py ai/scripts/routing_core/store.py ai/scripts/routing_core/service.py ai/scripts/set_agents_app.py ai/scripts/set_agents_spawn.py
PASS

python3 -m unittest tests.test_routing.RoutingTests.test_spawn_model_mismatch_and_turn_error_are_never_reported_as_success tests.test_routing.RoutingTests.test_close_run_persists_usage_on_the_dispatched_terminal_branch
PASS (2 tests)
```

## Próximos pasos/riesgo

1. Cerrar la corrida completa de `tests.test_routing`, reparar cualquier divergencia de fixture/migración 6→7 y agregar los casos deterministas AC-01..05.
2. Probar explícitamente concurrencia, reintento idempotente, expiry UTC, ausencia de uso y que no se reescriben campos de identidad/fallback.
3. Agregar runner AC-06 que, sin una suscripción agotada controlada verificada, informe `BLOCKED` / `HUMAN_DECISION_REQUIRED` y nunca `PASS` con mock.

El E2E real no se ejecutó: no hay una suscripción agotada controlada verificada en esta sesión.
