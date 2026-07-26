# P1R-R3 — tercera reparación consolidada (contrato enmendado)

Autorización explícita del usuario (2026-07-24): presupuesto nuevo (spawns 14-16, ciclo 3/3) y enmienda del
threat model registrada en `decisions-log.jsonl` (`r3-threat-model-amendment`), `design.md` ("Threat model
clarification (R3 amendment)") y ADR-0005. Adversario in-process/same-UID fuera de scope; "caller" = intent no
confiable, no código no confiable.

| Delta | Causa corregida | Archivos | Verificación |
|---|---|---|---|
| FD-001 (parte factible) | La composición de producción quedaba abierta: snapshot/inventory eran argumentos públicos del constructor y la validación de identidad era tautológica contra el snapshot recibido. | `service.py`, `routing.py` | `RoutingService(catalog_path, roster, config, …)` construye snapshot e inventory internamente; seam `_for_tests` privado; el binding se recomputa desde los campos canónicos y la identidad se revalida contra un snapshot fresco leído del catálogo en disco antes de autorizar. Permit no-forjable in-process = excepción aprobada. |
| FD-002 | `request.risk` no se leía nunca y los enums no se validaban; un pedido low no podía subir ni bajar nada porque el risk observado tampoco se usaba. | `domain.py`, `service.py`, tests | Vocabularios cerrados (`TASK_CLASSES`, `CRITICAL`, `RISK_ORDER`, `OPERATIONS`) validados en `validate()` y sobre el request; `combined_risk` = max(observado, pedido); riesgo efectivo alto o criticality exige contexto/critical_coverage. Test: downgrade imposible, enums inválidos → `FACTS_INCOMPLETE`. |
| FD-003 | `probe_inventory` hacía `json.loads` de TODO output (codex es texto, opencode es texto decorado con ANSI y falla con exit 0) → `{}` en producción → ninguna ruta ejecutable. | `catalog.py`, tests | Parser por par: `codex login status` (texto "Logged in…"), `claude auth status --json` (`loggedIn` y descarte del doc crudo con email), `opencode auth list/models` (strip ANSI, bullets de credenciales, líneas `provider/model`, texto `Error:` = par no disponible). Modelos = intersección con el catálogo canónico de models.toml. Cualquier sorpresa degrada sólo ese par. |
| FD-004 (parte factible) | El root respetaba `$HOME` (redirigible por entorno). | `store.py` | Root desde `pwd.getpwuid(os.getuid()).pw_dir`. Clasificación positiva de FS (`statfs`) y traversal descriptor-relative completo = excepción aprobada (sqlite abre por pathname; el residual es del adversario excluido). |
| FD-005 | La validación RO comparaba 5 substrings del DDL; columnas/tipos/PK/CHECK/índices exactos no se verificaban. | `store.py`, tests | Igualdad estricta del DDL normalizado contra el schema canónico construido en `:memory:` desde los mismos literales de `_create_schema` (única fuente de verdad). Test: DROP INDEX o schema_version viejo → `ROUTING_UNAVAILABLE` byte-idéntico. |
| FD-006 | `build_snapshot` hardcodeaba runtimes por provider, tenía un parámetro `inventory` muerto y la "revalidación" de autorización releía el mismo dict cacheado. | `catalog.py`, `service.py` | Runtimes derivados de la tabla auditada `_PAIR_COMMANDS`; parámetro muerto eliminado; modelos siempre intersectados con el catálogo canónico; en autorización se revalida contra snapshot fresco de disco. Re-probe (subprocesos) por autorización = excepción aprobada. |
| FD-007 | `consume_fallback` rechazaba sin auditar; CHECKs de lifecycle incompletos; guard constante en `_transition`. | `store.py`, tests | `_rejection_event` en `FALLBACK_DENIED` y `STATE_CONFLICT`; CHECKs nuevos (`role_class='writer'`, dispatched⇒actual, terminal⇒window=0, orden de timestamps, consumed⇒fallback) con bump `SCHEMA=3` — una DB v2 existente pasa a `ROUTING_UNAVAILABLE` y el operador decide (documentado, sin migración automática). Eventos terminales auditan la identidad realmente despachada (fallback si se consumió). |
| FD-008 | Contadores `exclusion/consumed/success/failure` siempre en 0; rechazos no compactaban; compactación en conexión/transacción separada dejaba ventana de 10001 filas y re-corría `integrity_check` O(n) por evento. | `store.py`, tests | Todos los contadores se incrementan una sola vez en el insert; `_compact_in` corre dentro de la MISMA transacción de todo write path (incluidos rechazos); mejora real de performance (una conexión por operación). |
| FD-009 (alcance pragmático autorizado) | 9 tests sin matrices de crash/concurrencia/retención/privacidad/CLI. | `tests/test_routing.py`, `gates.py` | 19 tests: crash SIGKILL entre BEGIN y COMMIT (consistencia + rollback), lock concurrente con `busy_timeout=0` (perdedor fail-closed, DB consistente), retención 10.000/90d dentro de la transacción, privacidad de bytes de la DB (sin task class, usuario, home, email), matriz CLI de exclusión de modos, parsers de probes contra formas grabadas (hermético). GateSpec nuevo `v2:routing-unit`. Tests production-shaped del output exacto de CLIs de terceros = exclusión aprobada. |
| FD-010 | La exclusión de modos enumeraba flags a mano y omitía `--yes`, `--no-install`, `--harness`, etc. | `set_agents_app.py`, tests | Chequeo genérico: cualquier argumento ≠ default del parser fuera de `--json`/`--route-explain`/`--routing-report` → `ROUTING_INPUT_INVALID`, exit 2. Test paramétrico con `--yes`, `--no-install`, `--harness`. |

## Validaciones locales (implementador)

| Comando | Resultado |
|---|---|
| `python3 -m unittest discover -s tests -p 'test_routing.py'` | 19 tests OK (14.8s) |
| 2 regresiones `HarnessTests` requeridas | OK |
| `python3 ai/scripts/setup_models.py --check` | PASS |
| `py_compile` (todos los módulos del paquete) | PASS |
| `./ai/scripts/verify.sh` | 117 tests, VERIFY_PASS (53.4s) |

## Excepciones aprobadas (decisión `r3-threat-model-amendment`)

1. Permit no forjable contra código in-process (FD-001 residual) — imposible en CPython; composición sellada es la garantía exigible.
2. Clasificación positiva de filesystem vía statfs/mountinfo y traversal descriptor-relative completo (FD-004 residual) — no portable y sólo detección frente a un adversario excluido.
3. Re-probe de inventario por autorización (FD-006 residual) — subprocesos de hasta 5s por una ventana de microsegundos; el probe es por invocación.
4. Tests que fijan el output exacto de versiones de CLIs de terceros (FD-009 residual) — perecederos; los parsers propios se testean contra formas grabadas.

## Nota operativa

El bump a `SCHEMA=3` invalida la DB de producción previa (`~/.local/state/set-agentes/routing-v2/routing.db`,
schema 2, telemetría de prototipo). Por diseño no hay migración ni recreación automática: el operador debe borrar
el directorio para reactivar el routing persistente. Los tests ya no tocan el estado de producción (defecto
preexistente corregido: la suite anterior autorizaba escrituras reales en la DB del usuario).
