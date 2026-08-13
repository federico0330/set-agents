# El gate de credenciales de pi corre despues del subproceso, y es preexistente

<!-- notas:auto -->
- fecha: 2026-08-13 · actor: orchestrator
- alcance: [[features/022-disponibilidad-real|022-disponibilidad-real]] · [[features/022-disponibilidad-real/P3-liveness-real|P3-liveness-real]]

## Contexto

El delta review final de P3 reporto P3-D01 (high): con un auth.json invalido el par de pi no entra al inventario, pero 'pi --list-models' se ejecuta IGUAL antes de consultar pi_auth_provider_keys(). Salida literal del reviewer: gate_legitimo resultado={('pi','openai-codex'):{'gpt-5.6-luna'}} subprocesses=1; gate_invalido resultado={} subprocesses=1.

## Decisión

NO se repara en P3. Medido: en la version commiteada b119ca7, ANTES de 022, el gate ya estaba despues de los subprocesos (catalog.py:517 de ese commit) y su propio comentario lo declara deliberado: 'Belt-and-suspenders (T-305, spike Q2): the auth.json key-set is a cheap, non-subprocess signal ALONGSIDE the naturally fail-closed column-parse below'. O sea es preexistente y por diseno, no una regresion de P3, y esta fuera de AC-07..AC-10, que son firma y cache. El resultado observable es CORRECTO en las dos direcciones: con auth invalido el par queda excluido.

## Consecuencias

Queda como defecto latente registrado, no cerrado: el probe de pi puede bloquear hasta PI_PROBE_MIN_TIMEOUT_SECONDS (60 s) y ese costo se paga aunque la credencial ya se sepa invalida. No es una filtracion ni un fail-open. Candidato a paquete propio junto con el arreglo de check-owned-paths.py, que tampoco se hizo aca. Adelantar el gate cambia el comportamiento de pi y necesita su propio review; no se hace en un paquete sin presupuesto de review restante.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
