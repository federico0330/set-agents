# P1 — runner AC-06 (Feature 011)

Estado: `partial` — la evidencia real queda bloqueada honestamente hasta que exista una suscripción Anthropic controlada y agotada, y un alterno usable.

## Runner opt-in

`ai/scripts/quota_failover_e2e.py` no lee `.env`, no imprime salida de Pi ni credenciales, y no invoca Pi sin los cuatro requisitos explícitos: `--enable-live-run`, una atestación JSON acotada sin campos sensibles, un `--pi-command` JSON que incluya `--ac06-live`, y la DB/ruta original a inspeccionar. Si falta o no valida cualquiera de ellos, escribe una sola línea JSON con `status=BLOCKED`, `reason=HUMAN_DECISION_REQUIRED`, `gate=AC-06` y sale con código 3. En ese camino no abre la DB ni ejecuta Pi.

La atestación debe declarar, sin secretos: schema `set-agentes.ac06-precondition/v1`, suscripción Anthropic controlada agotada, alterno usable, tarea mínima aprobada y que el setup no cambió presupuesto, cuota ni inventario. Tras una ejecución habilitada, la DB se abre sólo en modo SQLite read-only y se exige: original `terminal_failure/quota_exhausted`, exactamente un reemplazo enlazado y `terminal_success`, y exclusión global del proveedor original aún vigente. No hay mocks ni un resultado PASS por skip.

## Validaciones ejecutadas

```text
python3 ai/scripts/quota_failover_e2e.py
{"detail":"live_run_not_explicitly_enabled","gate":"AC-06","reason":"HUMAN_DECISION_REQUIRED","status":"BLOCKED"}
exit 3

python3 ai/scripts/quota_failover_e2e.py --self-test
{"gate":"AC-06-runner-self-test","live_provider_invoked":false,"status":"PASS"}
exit 0

python3 -m py_compile ai/scripts/quota_failover_e2e.py
PASS
```

No se ejecutó Pi ni se mutó una DB durante esas validaciones. Falta decisión/aporte humano de la precondición controlada para la corrida live.
