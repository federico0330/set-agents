# App de consola (set-agents)

<!-- notas:auto -->
## Responsabilidad

CLI+TUI unificado: install/repair, self-update, routing (--route-decide/--route-doctor/...), catálogo de tools/MCP, wizard de modelos.

## Posee

- `ai/scripts/set_agents_app.py`
- `ai/scripts/tui.py`

## Últimos cambios estructurales

- 2026-09-10 049-identidad-honesta-modelos/PKG-D2 — Integration tests prove honest model identity + isolated TTY observation on repaired C2 candidate
- 2026-09-10 049-identidad-honesta-modelos/PKG-C2 — Apply/restore/pin writers share one lock; ModelState cache-first home; host refresh isolated; exact readback or pending_apply
- 2026-09-10 049-identidad-honesta-modelos/PKG-C2 — Apply/restore/pin writers share one lock; ModelState cache-first home; host refresh isolated; exact readback or pending_apply
- 2026-08-21 035-panel-honesto-consola-y-tips/PKG-B — La segunda pasada de extraccion no muda el residuo de routing/vault: queda enumerado con experimento propio. Se borro una copia identica de vault_link_private. El CLI publico no cambia.
- 2026-08-19 033-menos-espera-menos-cuota/PKG-3 — El picker agrupa por proveedor, muestra n de total, marca el actual con un punto, y wipea con ESC H J en vez de 2J. ENTER en un header no selecciona.
- 2026-08-17 025-consola-minima-y-flexible/D5-vault-en-todo-spawn — Los spawners de codex/opencode/claude ahora materializan el bloque de vault con degradacion honesta y sink protegido para fallas transitorias.
- 2026-08-17 025-consola-minima-y-flexible/D4-harness-por-CLI — Sesión virgen por CLI con HOME/XDG/CODEX_HOME temporales y argv hijo opcional.
- 2026-08-17 025-consola-minima-y-flexible/D3-posturas-de-autonomia — La postura y metodología son preferencias persistidas con contrato runtime explícito, fallbacks comunes y precedencia ADR-0037.
- 2026-08-17 025-consola-minima-y-flexible/D2-trabajo-visible — El trabajo visible se activa luego de 300 ms por stream y el handoff de hijos interactivos queda sin escritores concurrentes.
- 2026-08-17 025-consola-minima-y-flexible/D1-superficie-humana — La CLI ahora separa la ayuda cotidiana de los controles avanzados y muestra estado humano por defecto sin alterar los formatos JSON de automatización.

_Debajo de esta línea la prosa es mantenida a mano — contrastala con la fecha del último cambio estructural._
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._

## Puntos de entrada

- `ai/scripts/set_agents_app.py` `main()` — arma el `ArgumentParser` (`prog="set-agents"`)
  con todos los flags mutuamente excluyentes de rutas de routing (`--route-decide`,
  `--route-explain`, `--route-doctor`, `--routing-report`, ...) más install/update/tools/MCP.
- `set-agents` (script wrapper en la raíz del repo/instalado) invoca este `main()`.
- Sin flags y con stdin TTY: cae al menú (`menu()`); la primera vez, al wizard guiado
  (`ai/scripts/onboarding.py` `run()`). Sin TTY: `print_help()` y `rc 2`, nunca el menú.

## Componentes

- `set_agents_app.py` — los `cmd_route_*`/`cmd_routing_*`/`cmd_doctor*`: cada uno compone
  contra `routing.py`/`routing_core/` (módulo `routing`) o `models_config.py`.
- `set_agents_app.py` — `cmd_model_preference_*`/`cmd_model_pin_*`: preferencias y pines
  de modelo.
- `set_agents_app.py` `cmd_status(human=False)` — el `--status` de una línea.
- `set_agents_app.py` `HOME_ACTIONS` / `visible_actions()` / `_run_home_action()` — la tabla
  del menú y su despacho **por clave estable** (ADR-0074). `MENU_ITEMS` es un valor derivado,
  nunca una segunda lista a mantener.
- `ai/scripts/tui.py` — el motor del picker (`run_picker`): raw mode, decodificación de teclas,
  viewport, búsqueda, y desde 048 multi-selección aditiva (`multi=True` → `tui.Marked`).
- `ai/scripts/ui.py` — el ÚNICO sistema visual (ADR-0075): paleta Rose Piné por rol,
  `caps()` recalculado por llamada, `cell_width()` como autoridad de ancho, `is_safe_label()`
  como regla de etiqueta, componentes y `SessionCache`. Reemplaza al borrado `tui_views.py`.
- `ai/scripts/onboarding.py` — los cinco pasos del primer arranque. Pantallas puras; las
  mutaciones se inyectan desde `set_agents_app._onboarding_ops()`.

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
- **Una función de pintado nunca mide.** `probe_host_model_counts()` levanta un subproceso por
  CLI; se invoca sólo desde `measure_hosts()`, que `menu()` corre una vez con
  `tui.with_progress` antes de abrir el loop. Un header que probea vuelve a stallear el picker
  en cada tecla.
- **El glifo decorativo es del renderer, nunca de la etiqueta** (ADR-0050 / ADR-0075). Toda
  etiqueta visible pasa `ui.is_safe_label` y mide una celda por carácter.
- **El menú despacha por clave, jamás por índice** (ADR-0074).
- **El techo de extracción sigue en pie** (ADR-0066): `menu()`, `hosts_menu`, `vault_menu`,
  `tools_menu`, `mcp_menu`, `plugins_menu` y todo `cmd_*` viven en `set_agents_app.py`. Sólo
  sale código puro y no parcheado (`ui.py`, `onboarding.py`), el precedente de `routing_cli.py`
  y `vault_ops.py`.

## Decisiones

- ADR-0018 (model preference policy), ADR-0029 (probe-driven model selection), ADR-0034
  (auto-adopted providers), ADR-0035 (billing-aware ordering, `--route-doctor` y el wizard
  `auto (recomendado) / lista manual / ninguno`).
- ADR-0050 (superficie humana: sin glifo estructural, flags internas ocultas no borradas),
  ADR-0053 (el progreso jamás en stdout), ADR-0066 (techo de extracción).
- ADR-0074 (despacho por clave estable) y ADR-0075 (sistema visual único, ancho de celda real,
  capacidad de color medida por llamada) — feature `048-consola-para-humanos`.
