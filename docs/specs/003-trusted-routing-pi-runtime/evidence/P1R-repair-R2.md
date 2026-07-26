# P1R-R2 — reparación consolidada del delta

Baseline histórico revisado: `51b84e3f8782789ac532d0c0e50167cf917a7eda`.

| Delta | Causa corregida | Archivos | Verificación |
|---|---|---|---|
| DR-001 | La autorización seguía dependiendo de datos de llamada; el permiso de un solo uso no debía aceptar identidades fuera del snapshot. | `service.py`, `store.py`, `domain.py` | Emisión privada de nonce CSPRNG, consumo único por el store y revalidación de identidad estática; suite de routing. |
| DR-002 | El scope era copiable y los hechos no se asociaban al objeto emitido. | `service.py`, `tests/test_routing.py` | Registro por identidad del objeto, clone/replay/conflicto terminan en `FACTS_INCOMPLETE`. |
| DR-003, DR-006 | El catálogo no verificaba la intersección con modelos canónicos y los probes debían quedar cerrados por par. | `catalog.py`, `routing.py`, tests | Tabla cerrada de probes, inventario por `(runtime, provider)` y modelos permitidos desde `models.toml`; Pi no autoriza. |
| DR-004 | El detector legacy podía atravesar un directorio enlace. | `routing.py`, `store.py`, tests | `lstat` del directorio antes del listado y `lstat` de cada candidato; raíz persistente fija y checks no-follow existentes se conservan. |
| DR-005 | La validación de SQLite no comprobaba DDL/índices suficientes antes de RW/WAL. | `store.py`, tests | Open RO e `integrity_check` previos; DDL, checks, PK e índices requeridos; fixture corrupta queda byte-idéntica. |
| DR-007 | La prueba no demostraba identidad real tras fallback/terminal. | `store.py`, `service.py`, tests | Transiciones `BEGIN IMMEDIATE` conservan identidad actual y reviewer sólo deriva escritor terminal; reject/eventos se mantienen allowlisted. |
| DR-008 | Faltaba prueba de percentiles/retención acotados. | `store.py`, tests | Compacción transaccional existente 90d/10k e índices; prueba de p50/p90 nearest-rank sobre SQLite. |
| DR-009 | GateSpecs no tenían ejecutor sellado ni pruebas de argv/env. | `gates.py`, `routing.py`, tests | `run_gate` acepta sólo spec declarado, argv absoluto, cwd exacto y env allowlisted; rechaza shell/PATH inyectados. |
| DR-010 | Los modos de observabilidad podían combinarse con comandos operativos. | `set_agents_app.py`, `routing.py`, tests | Exclusión total de modo, JSON de una línea, éxito explain `0`, conflicto `2`, diagnósticos humanos sólo stderr. |

## Gates ejecutados

| Comando | Exit | Tiempo |
|---|---:|---:|
| `python3 -m unittest discover -s tests -p 'test_routing.py' -v` | 0 | 14.6s |
| dos regresiones `HarnessTests` requeridas | 0 | 0.31s |
| `python3 ai/scripts/setup_models.py --check` | 0 | <1s |
| `python3 -m py_compile ...` requerido | 0 | <1s |
| GateSpec negativo/positivo enfocado | 0 | 0.05s |
| `./ai/scripts/verify.sh` | 0 | 55.3s |
| CLI explain/conflicto JSON | 0 | explain=0, conflict=2 |
| `git diff --check` | 0 | <1s |

## Riesgos residuales y bloqueo

SQLite se abre por pathname después de la validación RO; un atacante concurrente con el mismo UID que pueda intercambiar paths entre esas operaciones sigue fuera del modelo local de ADR-0005 y se rechaza cuando cambian fingerprints detectables. La verificación de ownership contra el baseline histórico falla por cambios preexistentes/read-only fuera de ownership (`docs/adr/0005` y contexto 002), no por esta reparación; no se los revirtió ni modificó R2.
