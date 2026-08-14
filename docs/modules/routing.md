# Routing (trusted dispatch)

<!-- notas:auto -->
## Responsabilidad

Decide y autoriza qué runtime/provider/modelo ejecuta un spawn, persiste el resultado y expone explain/report de solo lectura.

## Posee

- `ai/scripts/routing.py`
- `ai/scripts/routing_core/**`
- `ai/catalogs/routes.v1.toml`

## Últimos cambios estructurales

- 2026-08-14 023-senales-de-consumo/B4-estimado-nunca-dato-del-proveedor — Todo numero estimado viaja con base, ventana y cobertura, y sin presupuesto declarado no existe 'restante'
- 2026-08-14 023-senales-de-consumo/B3-ventana-y-rollup — usage_rollups por ventana en la misma transaccion que close_run, retencion de dispatches, y un candado que impide cambiar un DDL sin bumpear el esquema
- 2026-08-13 023-senales-de-consumo/B2-el-reporte-dice-de-donde-sale — Los adaptadores de spawn traducen su forma al vocabulario del store, y el reporte separa las dos fuentes
- 2026-08-13 023-senales-de-consumo/B1-registro-que-no-miente — La doctrina exige --usage al cerrar un run y hay un normalizador unico con la muestra real del cable por runtime
- 2026-08-13 026-orquestador-elige-modelo/P2-modelo-por-instancia — El descriptor de ruteo acepta model_request: preferencia de modelo por instancia, efimera
- 2026-08-13 026-orquestador-elige-modelo/P1-latencia-por-modelo-no-por-sufijo — El coordinador deja de estar obligado al sufijo -fast y pasa a un modelo no-GPT de suscripcion
- 2026-08-13 022-disponibilidad-real/P3-liveness-real — Firma de credencial por runtime en la clave de cache y una sola cache en la raiz del store
- 2026-08-13 022-disponibilidad-real/P5-altas-y-bajas-automaticas — Verificacion empirica del CLI id, liveness real en --provider-verify y separacion listed/usable en tres superficies
- 2026-08-13 022-disponibilidad-real/P1-registro-de-proveedores — Las siete tablas de proveedores pasan a derivarse de provider_registry.PROVIDERS
- 2026-08-13 022-disponibilidad-real/P2-techo-catalogo-tri-estado — [catalog].opencode_zen/go pasa a tri-estado: lista = techo, [] = veto, ausente = auto

_Debajo de esta línea la prosa es mantenida a mano — contrastala con la fecha del último cambio estructural._
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._

## Puntos de entrada

- `routing.compose(config, roster, *, simulate=False, fresh_probes=False, store=None)`
  (`ai/scripts/routing.py:18`) — la composición de producción: nunca acepta un snapshot o
  inventario provistos por el caller, siempre construye el catálogo desde disco.
- `set_agents_app.py`'s `--route-decide` / `--route-explain` / `--route-doctor` /
  `--routing-report` (módulo `consola`, no citamos línea acá: `check-anchors` resuelve
  basename solo dentro de los `paths` del módulo que chequea, SC-01) son la superficie de
  CLI real sobre este módulo.
- `RoutingService.route(request, facts, review_of_run_id=None, unverified_review=False)`
  (`ai/scripts/routing_core/service.py:243`) es el punto de entrada programático que decide.

## Componentes

- `routing_core/domain.py` — value objects inmutables: `TaskRequest` (`:148`),
  `RouteDecision` (`:212`), `CatalogSnapshot` (`:200`), `RoutingError` (`:9`).
- `routing_core/catalog.py` — `build_snapshot(catalog_path, roster, config, digest=None)`
  (`:611`) arma el `CatalogSnapshot` inmutable; `pi_pinned_argv(*args)` (`:42`) fija el pin
  exacto de la lane Pi.
- `routing_core/service.py` — `RoutingService` (`:93`) es el caso de uso; `PI_SIMULATION_ONLY`
  (`:21`) es el flag de una sola línea que habilita/deshabilita la lane Pi (ADR-0007).
- `routing_core/store.py` — `RoutingStore` (`:286`), adaptador SQLite local fixed-root
  (`routing-v2/routing.db`), única persistencia de dispatches/events/rollups.
- `routing_core/gates.py` — `GateSpec`/`gate_specs`/`run_gate` (`:8-27`), gates de
  dispatch/write.

## Flujo

`set-agents --route-decide` → `routing.compose()` (facade) → `RoutingService.route()` (usa el
`CatalogSnapshot` + inventario de pares auth/probes) → `RouteDecision` → para roles writer,
autoriza (`RoutingStore`, run_id CSPRNG) → el caller cierra la ventana de fallback y despacha
(`--route-dispatched` / `--route-terminal`). `--route-explain` es de solo lectura: puede leer
`routing-v2/probe-cache.json` pero nunca lo escribe.

## Posee / Depende de

Posee: ver "Posee" arriba (globs de `modules.toml`). Depende de `ai/catalogs/routes.v1.toml`
(catálogo estático de rutas) y de `ai/scripts/models_config.py` (inventario descubierto,
ADR-0029/ADR-0034) para resolver providers/modelos autenticados en runtime.

## Invariantes

- Policy y valores inmutables viven en el dominio; las dependencias apuntan hacia adentro
  (`docs/architecture/overview.md`, sección "Component map").
- El intent del caller nunca puede suplantar facts observados, catálogo, auth, IDs o paths.
- Auth nunca cruza runtimes: solo los pares auditados en `routing_core/catalog.py` son
  ejecutables; un par no probado/no autenticado falla cerrado (`PROVIDER_UNAUTHENTICATED`),
  nunca autoriza en silencio (`routing_core/service.py:315` y alrededores, `PI_SIMULATION_ONLY`).
- `--route-explain` deja el estado SQLite de dispatch/event byte-idéntico.

## Decisiones

- [[decisiones/2026-08-10 el-nuevo-default-discovered-providers-auto-rompe-setup-models-py-que-es-propiedad-de-p2|providers "auto" y setup_models.py]]
- ADR-0029 "el probe manda", ADR-0030 "decide siempre", ADR-0034 "auto-adopción de
  providers", ADR-0035 "billing-aware ordering" — ver `docs/adr/README.md` para el índice
  completo; este módulo es donde las cinco aterrizan.
