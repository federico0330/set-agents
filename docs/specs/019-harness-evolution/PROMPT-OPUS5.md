# PROMPT — Feature 019: capa cognitiva + routing abierto + autonomía real

> Pegar este prompt completo en una sesión limpia (Opus 5) parada en `/home/federico/SET-AGENTES`.

---

Sos el orquestador del harness SET-AGENTES trabajando SOBRE el propio harness. Implementá la feature 019 según el spec de abajo, siguiendo el workflow del repo (`feature-state.py init --mode feature`, paquetes, gates, review independiente, delta review). El spec ya fue relevado, auditado (3 exploraciones + auditoría Codex read-only de `routing_core`) y aprobado por Federico; las decisiones de producto listadas en §0 están TOMADAS — no las re-preguntes.

## §0. Decisiones de producto ya tomadas (no re-litigar)

1. **Providers**: todo provider autenticado en opencode se vuelve routable automáticamente ni bien se configura (tráfico real, no solo fallback). Incluye `openai` (OAuth ChatGPT), `github-copilot`, `opencode-go`, `opencode-zen` y modelos free. Las filas curadas ganan empates.
2. **Costo**: a igual tier gana suscripción/free; zen (metered) entra solo cuando aporta algo que los otros no tienen (único que satisface el tier, o independencia de reviewer). Sin techo mensual por ahora.
3. **Capa humana**: `docs/modules/` en **español**; bloque "Impacto humano" en narración; digest con sección de software; comando `/explicar`. NO se agrega gate permanente de codex-audit.
4. **Tools**: el catálogo se abre a pedido con flujo propose→aprobación humana→approve→install. Siempre preguntar antes de instalar algo nuevo; sudo siempre manual.
5. **Question policy**: regla general "resolvé antes de preguntar" — el agente solo pregunta lo que genuinamente no entiende o es decisión nueva; nunca lo ya dicho/registrado.

## §1. Contexto verificado (hallazgos de la auditoría, con anclas)

### 1a. Routing: zen/copilot son estructuralmente inelegibles hoy

- Log real `~/.local/state/set-agentes/routing-v2/decisions-v1.jsonl`: 185 decisiones (2026-08-05→07), 184 `selection_path: "dynamic"`, **0 zen, 0 copilot**, 9 halts `REVIEWER_INDEPENDENCE_UNAVAILABLE` por escasez de providers.
- Cuatro compuertas cerradas (documentado en `models.toml:17-25` — "all four selectability gates, none opened here"):
  1. `ai/catalogs/routes.v1.toml` — solo 6 filas curadas (openai-codex ×3, anthropic ×3).
  2. `enabled_providers = ["openai-codex","anthropic"]` (`models.toml:39`; filtros `routing_core/catalog.py:509,539`).
  3. `models_config.py:211` `ROUTING_PROVIDERS` closed set.
  4. `discovered_providers = []` default → rama `build_effective_snapshot` muerta (`routing_core/service.py:142-151`).
- Copilot no existe en NINGUNA tabla: `_OPENCODE_PROVIDER_KEYS` (`catalog.py:111`), `_OPENCODE_CLI_IDS` (`catalog.py:121`), `_PAIR_COMMANDS` (`catalog.py:133-141`), `DISCOVERABLE_PROVIDERS = {openai-codex, anthropic, opencode-zen, opencode-go}` (`models_config.py:41`), pins (`set_agents_app.py:120,202`), spawn map `_PROVIDER_PREFIXES` (`opencode_spawn.py:117`).
- Los probes SÍ funcionan: `opencode auth list --pure` + `opencode models <cli-id> --pure` (`catalog.py:380-396`) detectan hoy los 4 providers autenticados (verificado en vivo: zen 60 modelos, go 16).
- ADR-0029 / `routing_core/inference.py` ya sintetiza rutas para modelos descubiertos (tier por sufijo de nombre, `curated_priority=1000`, flag `inferred`), pero está apagado por la compuerta 4.
- `PROVIDER_BILLING_KIND` (`catalog.py:145`) registra metered/subscription pero nada lo lee ("008-P3's territory").
- Sort key actual (`service.py:348-350`): `(same-provider-as-writer, pin, TIER_ORDER, _bias_rank, curated_priority, route_id)`. Precedencia pin > dinámico > fallback (ADR-0032).
- Probe-cache `~/.local/state/set-agentes/probe-cache.json`: hoy solo 2 pares (anthropic, openai-codex); los pares opencode faltan — probable PATH stale tras reinstalación de opencode (2026-08-06). TTL 5 min (`catalog.py:20,281`), key sin versión de CLI ni set de providers (`catalog.py:261`).

### 1b. Hallazgos de la auditoría Codex (incorporarlos como requisitos)

1. **Crítico** — discovery ingenuo puede burlar la independencia de reviewer: `inference.py:70` sintetiza todo modelo para todo rol; las exclusiones de `service.py:312-337` solo conocen alias canónicos curados. Un mismo modelo bajo alias/provider distinto evadiría `REVIEW_MODEL_CONFLICT`.
2. **Alto** — nombres inferidos pueden auto-otorgarse frontier: `_FRONTIER_HINTS` (`inference.py:40`) mapea `-pro/-max/-ultra/...` a frontier; un label controlado por el provider influiría en elegibilidad para trabajo crítico.
3. **Alto** — copilot detectado por auth-parse (fixture `tests/test_routing.py:3096` devuelve `github copilot`) pero descartado en cada compuerta.
4. **Alto** — un provider nuevo elegido por el router muere en materialización: `opencode_spawn.py:117-120` solo mapea 3 prefijos → `PROVIDER_UNSUPPORTED` DESPUÉS de autorizar.
5. **Alto** — `_parse_opencode_auth` (`catalog.py:196-207`) devuelve display text, no CLI ID; NUNCA derivar el CLI ID reemplazando espacios por guiones (el caso zen ya lo demuestra: display "opencode zen" vs CLI id "opencode"). Además trata filas `○` como autenticadas (`catalog.py:203`) — corregir.
6. **Medio** — cache stale con discovery dinámico: leer auth fresca en cada composición; cachear solo listados de modelos, con key = set normalizado de providers autenticados + path/mtime del binario opencode + versión de schema; re-rankear tras fallo de reprobe del candidato elegido (`service.py:409`).
7. **Medio** — "curada gana" es convención numérica (1000 vs 10/20), no invariante: falta flag explícito `is_inferred` en el sort key.
8. **Medio** — pins/preferencias validan contra constante de 4 providers (`set_agents_app.py:120,202`): deben validar contra el snapshot efectivo vivo. Y `models_config.emit()` (`models_config.py:487`) dropea silenciosamente keys `[catalog]` desconocidas — todo campo nuevo debe persistir en load Y emit (no persistir listados descubiertos en `models.toml`; solo política/exclusiones).

### 1c. Capa humana: el harness no registra estado cognitivo del software

- La única doc global del software construido es `docs/architecture/overview.md`, mantenida a mano por `architect` en fase de diseño (`Global/_canonical/agents/architect.md:41-47`), sin gate — está stale en este mismo repo (congelada en "trusted routing P1R" mientras el harness llegó a ADR-0033).
- No existe `docs/modules/`. La narración entera (ADR-0027/0033, `orchestrator.md:637-724`) y el digest (`cli_reporting.py:152-244`) cuentan pipeline, nunca "cómo quedó construido".
- Infra reutilizable tal cual: `feature_state_lib/render_notes.py` — `merge_note():52` (bloque máquina entre `<!-- notas:auto -->` + zona humana preservada), `write_note():68` (atómico), `_short():79` (neutraliza `<!--`), `notes_root():36`. Enganche central de regeneración: `feature-state.py:166-170` (`mutate`) + `sync-notes`/`digest`.
- INTEGRATION: `transitions.py:108-114` sin precondición de entrada (deliberado, ADR-0024); `done_ready` (`model.py:449-472`) no chequea documentación; `integrator.md:17-25` no menciona docs.

### 1d. Question policy y tools

- `orchestrator.md:517-553` tiene lista askable/no-askable; el único "no preguntes lo ya dicho" es el carve-out de plataforma nombrada (ADR-0025.2). No hay protocolo general de resolución previa contra pedido/notas/decisiones.
- Tools: closed set (`tools.toml`, 9 CLIs + 3 MCPs; `TOOL_UNKNOWN` duro en `set_agents_app.py:1164`; allowlist orquestador `coord_policy.py:170-204`). ADR-0025 rechazó abrirlo → el cambio requiere ADR que lo supersede parcialmente.

## §2. SPEC — cinco paquetes

Cada cambio doctrinal lleva su ADR ANTES del código (los tests-contrato `tests/test_routing.py` ~4968 líneas y `tests/test_harness.py` ~8653 pinean frases y defaults; enumerá test-por-test qué cambia y por qué, con el ADR como fuente). Tras tocar `Global/_canonical/` o `feature_state_lib/`, SIEMPRE `./build.sh` y verificar drift (`build.sh --check`) — hay copias byte-identical en los 4 árboles + `PROYECTO/`.

### PKG-1 — Routing: auto-adopción de providers autenticados (ADR-0034)

**Objetivo**: con `discovered_providers = "auto"` (nuevo valor, nuevo default), todo provider del set auditado con probe autenticado se vuelve routable; curada gana empates como invariante.

Cambios:
- `models_config.py`: aceptar `"auto"` o lista en `discovered_providers` (validación `:207-210`, default en `ROUTING_DEFAULTS:44`); `DISCOVERABLE_PROVIDERS:41` += `{"github-copilot", "openai"}`; entradas de suscripción para ambos (`_PROVIDER_SUBSCRIPTION:234`, `SUBSCRIPTION_BY_PREFIX:52`); `emit()` serializa `"auto"` y lo preserva en re-emit.
- `routing_core/service.py:142-151`: con `"auto"`, derivar providers del inventario probeado ∩ providers de `_PAIR_COMMANDS`; la rama `build_effective_snapshot` deja de estar muerta.
- `routing_core/catalog.py`: pares nuevos `github-copilot` y `openai` en `_OPENCODE_PROVIDER_KEYS`/`_OPENCODE_CLI_IDS` (con eso `_PAIR_COMMANDS` se deriva solo). **AC duro**: medir EN VIVO el display text de `opencode auth list --pure` y el CLI id de `opencode models <id> --pure` antes de hardcodear (precedente: el split two-token de zen). Provider con CLI id no verificable = fail-closed (no routable), nunca heurística espacio→guion. Corregir el parse que acepta filas `○` como autenticadas (`catalog.py:203`).
- **Fuente única** `provider_id → prefijo CLI opencode` compartida entre catálogo y spawners (hoy duplicada/incompleta en `opencode_spawn.py:117`); `PROVIDER_UNSUPPORTED` solo para lo genuinamente desconocido.
- Guardas (Codex #1, #2, #7):
  - `inference.py`: rutas sintetizadas **cap `balanced`** — eliminar la promoción a frontier por sufijo de nombre; frontier requiere fila curada.
  - Reviewer: una ruta inferida solo es elegible como reviewer si su vendor-stem resuelve y difiere del writer; stem no resoluble = excluida (fail-closed), nuevo reason code (p.ej. `REVIEW_IDENTITY_UNRESOLVED_INFERRED`).
  - Sort key (`service.py:348-350`): insertar flag explícito `is_inferred` (curada primero) — la precedencia deja de depender del número 1000.
- Probe-cache (Codex #6): auth fresca por composición; cache solo de listados de modelos con key = set de providers autenticados + path/mtime del binario + versión de schema; re-rank tras fallo de reprobe del elegido.
- Pins (Codex #8): `--model-pin-set`/preferencias validan contra snapshot efectivo vivo (`set_agents_app.py:120,202`).
- `enabled_providers` y `routes.v1.toml` NO se tocan (siguen gobernando solo la vía curada) — minimiza blast radius.

ACs:
1. Con los 4 providers opencode autenticados y `"auto"`, `set-agents --route-decide` puede devolver zen/copilot/go/openai para roles no-frontier, y `decisions-v1.jsonl` lo registra.
2. Un spawn real vía `opencode_spawn.py` con provider descubierto materializa sin `PROVIDER_UNSUPPORTED`.
3. Fila curada gana el empate contra sintetizada del mismo tier (test con flag `is_inferred`).
4. Sintetizada nunca frontier; reviewer inferido con stem no resoluble excluido (tests).
5. Escenario que hoy da `REVIEWER_INDEPENDENCE_UNAVAILABLE` (writer anthropic, único alternativo excluido) resuelve con un provider descubierto; y zen `claude-*` NO revisa a writer anthropic (mismo stem).
6. Cache: cambiar el binario opencode (mtime) invalida; test lockstep `DISCOVERABLE_PROVIDERS == {p for _,p in _PAIR_COMMANDS}`.
7. ADR-0034 escrito e indexado en `docs/adr/README.md`; tests-contrato afectados (`test_routing.py`, `test_discovered_routes.py`, `test_probe_subscriptions.py`, `test_spawn_materialization.py`, `test_decide_always.py`) reescritos con referencia al ADR.

### PKG-2 — Billing-aware ordering + superficie de consola (ADR-0035)

- Completar `PROVIDER_BILLING_KIND` (`catalog.py:145`): subscription = openai-codex, anthropic, opencode-go, github-copilot, openai; metered = opencode-zen.
- `billing_rank(provider, model)` puro (domain.py o catalog.py): 0 = subscription o modelo free (sufijo `-free`, convención ya usada por `inference.py:41`), 1 = metered/desconocido.
- Sort key: insertar tras `TIER_ORDER` y antes de `_bias_rank`. Las exclusiones duras no cambian → zen entra exactamente cuando es el único que satisface tier/independencia.
- Reason code aditivo (estilo `MODEL_METADATA_INFERRED`) para observabilidad del rank en `decisions-v1.jsonl`.
- Consola: nuevo `set-agents --route-doctor` (corre `--fresh-probes`, reporta por par: auth, modelos, billing, y diagnostica el cache); panel de modelos (`setup_models.py:_panel_lines:139-190`) muestra "proveedores descubiertos rutables: auto → <lista viva>" con billing, y se reescriben el rótulo `"DEFAULTS CURADOS (fallback...)"` y la línea de política citando ADR-0034/0035; wizard "Proveedores descubiertos" → `auto (recomendado) / lista manual / ninguno` (`setup_models.py:362-379`).

ACs: a igual tier gana subscription/free (test); zen elegido solo en los dos casos que aportan (tests); `--route-doctor` funcional; textos de panel/wizard actualizados (`test_models_wizard_ui.py`, `test_menu_ui.py`); ADR-0035.

### PKG-3 — Capa cognitiva: docs/modules/ + estado + gate + digest (ADR-0036)

**Objetivo**: que Federico pueda abrir `docs/modules/<slug>.md` y en 90 segundos recuperar qué hace el módulo, por dónde fluye, qué invariantes tiene y qué cambió últimamente.

- **Schema del doc** (español, bloque máquina entre `<!-- notas:auto -->` reutilizando `merge_note`/`write_note`/`_short` de `render_notes.py` — cero infra nueva de merge; zona humana debajo, preservada):
  `# <Nombre>` → `## Responsabilidad` (1-2 líneas) → `## Puntos de entrada` → `## Componentes` → `## Flujo` (cadena corta tipo `HTTP → Controller → Service → Repo`) → `## Posee / Depende de` → `## Invariantes` → `## Decisiones` (wikilinks `[[...]]` a ADRs/decisiones, estilo `_decision_body`) → `## Últimos cambios estructurales` (lista capada ~10, derivada de `module_impacts`: `<fecha> <feature/pkg> — <cambio>`).
- **Registro** `docs/modules/modules.toml`: `[module.<slug>]` con `nombre`, `responsabilidad`, `paths = [globs]`. Fuente para detección de afectados: match de `owned_paths` del paquete + `changed_files` del receipt (ADR-0024, `cli_integration.py`) contra los globs.
- **Motor**: nuevo `feature_state_lib/render_modules.py` (mismo contrato never-raises/atómico/`render-failures.log` que render_notes) + en `feature-state.py`:
  - `record-module-impact <fid> --package-id P --module <slug> --cambio "<qué cambió estructuralmente>" --modelo-mental "<qué tenés que saber ahora>"` → append a `package["module_impacts"]`, regenera `docs/modules/<slug>.md`, imprime el bloque **Impacto humano** listo para narración.
  - `module-impact-detect <fid> --package-id P` → lista módulos candidatos sin mutar.
  - `--module-impact-waived --reason` como válvula (quick-fixes triviales no pagan un doc entero).
- **Gate**: `transitions.py` — entrar a `INTEGRATION` exige que cada paquete accepted tenga `module_impacts` no vacío o waiver registrado; `done_ready` (`model.py:449-472`) agrega el mismo check como error nuevo. Registrar la relación con ADR-0024 (que evitó preconditions ahí) en el ADR-0036.
- **Render pipeline**: sumar `render_modules` a la pasada de `feature-state.py:166-170` y a `sync-notes` (solo módulos con impacts; repos sin `docs/modules/` no fallan — patrón `notes_root`).
- **Digest**: `cli_reporting.cmd_digest` suma sección `## Qué cambió en el software` desde los `module_impacts` del período.
- **Seed**: crear `docs/modules/modules.toml` + docs iniciales para los módulos de ESTE repo (routing, feature-state/estado, generación de árboles, app de consola, narración/notas) y regenerar el `docs/architecture/overview.md` stale como parte de la evidencia.

ACs: merge idempotente con zona humana intacta (test de round-trip); gate bloquea INTEGRATION sin impacts/waiver; `done_ready` lo exige; digest muestra la sección; render nunca rompe una mutación; nuevo `tests/test_module_docs.py`; copias `feature_state_lib` re-sincronizadas (`build.sh`); ADR-0036.

### PKG-4 — Doctrina: Impacto humano, question policy, /explicar (ADR-0036 + ADR-0037)

- **Narración** (`Global/_canonical/agents/orchestrator.md:637-724`): el bloque de cierre de paquete (hito b) suma sub-bloque fijo:
  `Impacto humano:` → `Módulo:` / `Cambio de modelo mental:` / `Tenés que saber:` — tomado del `record-module-impact`. Mantener registros Cliente/Ingeniería (ADR-0027) y el bloque de fin de turno (ADR-0033) intactos.
- **Integrator** (`integrator.md:17-25`): paso nuevo — correr `module-impact-detect`, registrar `record-module-impact` por módulo afectado (o waiver con reason), verificar que `docs/architecture/overview.md` y los docs de módulos tocados no queden stale.
- **Architect** (`architect.md:41-47`): al diseñar un módulo nuevo, crear su entrada en `modules.toml` + doc inicial.
- **Question policy** (ADR-0037, extiende 0025): insertar ANTES de la lista askable en `orchestrator.md:517-553` un protocolo con encabezado exacto testeable, p.ej. `**Resolvé antes de preguntar (ADR-0037)**`: ninguna pregunta sale sin pasar por 4 fuentes en orden — (1) el pedido original del turno/feature, (2) `docs/notas/` (Qué falta / Approach y decisiones), (3) `ai/state/decisions-log.jsonl`, (4) spec aprobada/ADRs. Lo que alguna fuente ya resuelve, se ejecuta con `log-decision`, no se pregunta. El carve-out de plataforma nombrada queda como caso particular. Espejos de 2-3 líneas en `Global/_shared/CLAUDE.md` y gemelas (`AGENTS.pi.md`, `AGENTS.opencode.md`, `Global/codex/AGENTS.md`) + `skills/request-triage` (las preguntas de scoping también pasan el filtro).
- **/explicar**: nuevo `Global/_canonical/commands/explicar.md` + skill `Global/_canonical/skills/explicar/SKILL.md` (generate.py ya propaga commands/skills a los 4 árboles). Contrato: read-only, sin estado de feature (como `/consult`); entrada = pregunta o nombre de módulo; procedimiento = leer `modules.toml` + doc del módulo → seguir el código desde los puntos de entrada → devolver el trace en lenguaje humano (registro `Cliente:` + `Ingeniería:`) con `file:line` como evidencia (ADR-0026); si el doc del módulo está stale respecto del código, decirlo y ofrecer regenerarlo.

ACs: frases doctrinales exactas presentes y asserteadas en `test_harness.py` (estilo grep existente); árboles regenerados sin drift; `/explicar` disponible en los 4 runtimes; `roles.tsv` NO cambia; ADR-0036/0037 indexados.

### PKG-5 — Tools discovery con aprobación humana (ADR-0038, supersede parcial 0025)

- Flujo: tool no catalogada → el rol investiga fuente oficial (read-only: npm/pacman/brew/URL MCP, qué es, por qué hace falta) → `set-agents --tools-propose <name> --kind cli|mcp|skill --detect <bin> --install-<method> "<cmd>" --why "<motivo>"` valida (nombre `_CATALOG_NAME`, comando parseable, **rechaza sudo/pipes ocultos**) e imprime la **pregunta consolidada** (qué se instala, de dónde, comando exacto, por qué) sin instalar → el orquestador hace UNA pregunta al usuario (askable por diseño) → `set-agents --tools-approve <name>` escribe el bloque en **`tools.local.toml`** (nuevo, untracked, mergeado con `tools.toml` en `load_catalog():1104`; el `tools.toml` del repo sigue curado por humanos) + `log-decision` → instalación por el `cmd_tools_install` existente (`:1161-1209`) sin cambios de postura (sudo siempre muestra la línea y pregunta, aun con `--yes`; MCPs entran disabled).
- `TOOL_UNKNOWN` (`set_agents_app.py:1164`) pasa de callejón a sugerir el flujo propose.
- `coord_policy.py:_tools_channel_allowed` (`:170-204`): extender el argv-walker a `--tools-propose`/`--tools-approve` con gramática cerrada (precedente SEC-001: nunca regex laxo).
- Skills instalables: solo project-local (`.claude/skills/` del proyecto destino); mutar `Global/_canonical/` queda explícitamente fuera de alcance en el ADR.
- Doctrina: `orchestrator.md` §tool catalog (`:621-635`) + `implementer.md:59` — "tool faltante" ya no es blocker: es propose→pregunta→approve→install.
- Consola: ítems de menú "Proponer herramienta nueva" (`MENU_ITEMS:2357`) y flag `--modules-status` si no entró en PKG-3.

ACs: round-trip propose→approve→catalogado→install en test; propose con sudo/pipe raro rechazado; merge `tools.local.toml` no rompe catálogo existente; allowlist coord_policy cerrado (`test_autonomy_policy.py`); ADR-0038.

## §3. Orden, gates y cierre

- Orden: PKG-1 → PKG-2 → PKG-3 → PKG-4 → PKG-5 (4 depende de 3; 1 y 3 son independientes si necesitás paralelizar reviews).
- Gates por paquete: `python3 -m pytest tests/ -x` verde, `./build.sh --check` sin drift, y los ACs del paquete como evidencia con `file:line`.
- Review: workflow normal del harness (review independiente, findings estructurados, repair consolidado, delta review, máx 2 ciclos).
- **Criterio de cierre de la feature**: (a) suite completa verde; (b) con los providers opencode autenticados, `set-agents --routing-decisions` muestra decisiones nuevas con zen/copilot/go/openai y el billing rank; (c) `docs/modules/` seedeado y `feature-state.py digest` muestra "Qué cambió en el software"; (d) `/explicar routing` devuelve un trace coherente; (e) los 5 ADRs (0034-0038) escritos e indexados; (f) el bloque de fin de turno final le explica a Federico, en registro Cliente, qué cambió en SU harness.

## §4. Riesgos operativos (leer antes de tocar nada)

1. `tests/test_routing.py` y `tests/test_harness.py` son suites-contrato: pinean frases doctrinales por grep, defaults, y byte-igualdad de las copias de `feature_state_lib` (4 árboles + PROYECTO). Cambio doctrinal ⇒ ADR primero, luego test, luego código.
2. Display text/CLI id de `github-copilot` y `openai` en opencode: medir en vivo (AC de PKG-1) — la trampa two-token vs single-token de zen es el precedente documentado en `catalog.py:105-121`.
3. `models_config.emit()` dropea keys desconocidas: cada campo nuevo debe sobrevivir el ciclo load→emit→load (test de round-trip).
4. El gate de módulos tiene waiver como válvula: no lo conviertas en fricción para quick-fixes.
5. No toques `enabled_providers`/`routes.v1.toml`/`ROUTING_PROVIDERS` más de lo especificado: la vía curada queda cerrada a propósito.
