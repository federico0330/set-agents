# App de consola (set-agents)

<!-- notas:auto -->
## Responsabilidad

CLI+TUI unificado: install/repair, self-update, routing (--route-decide/--route-doctor/...), catálogo de tools/MCP, wizard de modelos.

## Posee

- `ai/scripts/set_agents_app.py`
- `ai/scripts/tui.py`

## Últimos cambios estructurales

- 2026-08-12 019-harness-evolution/P5-tools-discovery — La consola dejo de tener un catalogo de herramientas cerrado. load_catalog ahora mergea tools.toml (curado, trackeado) con tools.local.toml (untracked, por clon del harness), y aparecieron --tools-pr…

_Debajo de esta línea la prosa es mantenida a mano — contrastala con la fecha del último cambio estructural._
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._

## Puntos de entrada

- `ai/scripts/set_agents_app.py:3252` `main()` — arma el `ArgumentParser` (`prog="set-agents"`)
  con todos los flags mutuamente excluyentes de rutas de routing (`--route-decide`,
  `--route-explain`, `--route-doctor`, `--routing-report`, ...) más install/update/tools/MCP.
- `set-agents` (script wrapper en la raíz del repo/instalado) invoca este `main()`.
- Sin flags: cae al TUI (`ai/scripts/tui.py`, `run_picker`).

## Componentes

- `set_agents_app.py:454-821` — los `cmd_route_*`/`cmd_routing_*`/`cmd_doctor*`: cada uno
  compone contra `routing.py`/`routing_core/` (módulo `routing`) o `models_config.py`.
- `set_agents_app.py:327-414` — `cmd_model_preference_*`/`cmd_model_pin_*`: el wizard de
  preferencias/pines de modelo.
- `set_agents_app.py:1089` `cmd_status(human=False)` — el `--status` de una línea.
- `ai/scripts/tui.py` — el picker interactivo (`run_picker`) que los distintos menús
  reutilizan.

## Flujo

`set-agents [--flag ...]` → `main()` parsea (cada modo es mutuamente excluyente, con su
propio conjunto cerrado de modificadores exentos — ver `docs/architecture/overview.md`,
tabla del "Adaptive dispatch CLI contract") → despacha al `cmd_*` correspondiente → para
las rutas de routing, compone `routing.compose()`/`RoutingService` (módulo `routing`) →
imprime texto humano o `--json` según el flag.

## Posee / Depende de

Posee: ver "Posee" arriba. Depende de `routing.py`/`routing_core/` (decisión de ruteo),
`models_config.py` (inventario descubierto) y `feature-state.py`/`feature_state_lib/`
indirectamente para los subcomandos que tocan estado de features (no reimplementa esa
lógica, delega).

## Invariantes

- `--route-decide` para un rol writer es la única ruta explícitamente documentada y
  permisionada como MUTANTE; todo lo demás (`--route-explain`, `--routing-report`,
  `--routing-open-runs`, `--routing-recent-writers`) es de solo lectura.
- Cada modo de routing tiene su propio conjunto cerrado de modificadores exentos —
  agregar un flag nuevo sin declararlo exento rompe la exclusión mutua por diseño.
- `--route-doctor`/`--doctor` corren con probes frescos, nunca con el cache silencioso
  (ADR-0035).

## Decisiones

- ADR-0018 (model preference policy), ADR-0029 (probe-driven model selection), ADR-0034
  (auto-adopted providers), ADR-0035 (billing-aware ordering, `--route-doctor` y el wizard
  `auto (recomendado) / lista manual / ninguno`).
