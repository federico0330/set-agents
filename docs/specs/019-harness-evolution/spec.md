# 019 — Evolución del harness: auto-adopción de providers, costo, capa cognitiva, doctrina y tools

- **Estado**: aprobado por Federico (2026-08-10). Relevamiento: 3 exploraciones + auditoría
  Codex read-only sobre `routing_core`. Prompt de origen:
  `docs/specs/019-harness-evolution/PROMPT-OPUS5.md`.
- **ADRs**: 0034 (auto-adopción), 0035 (billing-aware ordering + consola), 0036 (capa
  cognitiva `docs/modules/`), 0037 (resolvé antes de preguntar), 0038 (tools discovery).

## Objetivo

Cinco cambios independientes pero coherentes:

1. Que todo provider autenticado y verificable del runtime opencode se vuelva routable
   automáticamente (tráfico real, no solo fallback), sin abrir la vía curada.
2. Que a igual tier el router prefiera suscripción/free sobre metered, y que la consola
   muestre y diagnostique el inventario vivo.
3. Que el harness registre el **estado cognitivo del software construido**
   (`docs/modules/`), no solo el estado del pipeline.
4. Que la narración, el integrator y la question policy incorporen impacto humano y
   resolución previa; que exista `/explicar`.
5. Que el catálogo de tools se abra con flujo propose → aprobación humana → approve →
   install.

## Decisiones de producto (tomadas, no re-litigables)

- **DEC-1 Providers**: provider autenticado en opencode ⇒ routable automáticamente. Las
  filas curadas ganan empates.
- **DEC-2 Costo**: a igual tier gana suscripción/free; metered (zen) entra solo cuando es
  el único que satisface tier o independencia de reviewer. Sin techo mensual.
- **DEC-3 Capa humana**: `docs/modules/` en español; bloque "Impacto humano" en narración;
  sección de software en el digest; comando `/explicar`. Sin gate permanente de
  codex-audit.
- **DEC-4 Tools**: catálogo abierto a pedido, con aprobación humana previa a instalar.
  Sudo siempre manual.
- **DEC-5 Question policy**: "resolvé antes de preguntar"; nunca preguntar lo ya
  dicho/registrado.

## Medición en vivo (evidencia previa al diseño, opencode 1.18.14, 2026-08-10)

`opencode auth list --pure` (4 credenciales) y `opencode models <id> --pure` tras
`--refresh`:

| auth display | auth.json key | CLI id listable | modelos |
|---|---|---|---|
| `OpenCode Go` (api) | `opencode-go` | `opencode-go` | 18 |
| `OpenAI` (oauth) | `openai` | `openai` | 13 |
| `GitHub Copilot` (oauth) | `github-copilot` | **ninguno** (`Provider not found`) | 0 |
| `OpenCode Zen` (api) | `opencode` | `opencode` | 60 |

Consecuencias de diseño, ya incorporadas a los ACs:

- **M-1**: `github-copilot` está autenticado pero opencode no expone modelos para él ni
  tras `opencode models --refresh`. Por la regla fail-closed del propio spec, copilot **no
  es routable** en esta feature: se lo detecta, se lo registra como `detected, unlistable`
  y se lo excluye. No se hardcodea ningún CLI id no verificado.
- **M-2**: el provider opencode `openai` (OAuth ChatGPT) **ya es** el par
  `("opencode", "openai-codex")` del catálogo (`_OPENCODE_CLI_IDS`), que hoy resuelve
  display `openai` y CLI id `openai`. No se agrega un provider de catálogo duplicado; lo
  que faltaba era que sus modelos descubiertos fueran routables, que es exactamente lo que
  destraba la auto-adopción.
- **M-3**: `ollama` aparece en `opencode models` sin credencial: la adopción es
  auth-gated, así que queda fuera (fail-closed) — sirve de caso de test negativo.
- **M-4**: zen expone `claude-*` y `gpt-*`: el riesgo de independencia de reviewer por
  mismo vendor-stem bajo otro provider es real y vivo, no teórico.

## Criterios de aceptación

### PKG-1 — Auto-adopción de providers autenticados (ADR-0034)

- **AC-01**: `discovered_providers` acepta el valor `"auto"` (nuevo default) además de una
  lista; sobrevive el ciclo load → `emit()` → load sin perderse ni degradar a lista.
- **AC-02**: con `"auto"`, `build_effective_snapshot` deriva los providers del inventario
  probeado ∩ providers de `_PAIR_COMMANDS`; la rama deja de estar muerta y
  `set-agents --route-decide` puede devolver providers descubiertos (zen/go/openai-codex)
  para roles no-frontier, registrado en `decisions-v1.jsonl`.
- **AC-03**: un spawn real vía `opencode_spawn.py` con un provider descubierto materializa
  sin `PROVIDER_UNSUPPORTED`: existe **una sola fuente** `provider_id → prefijo CLI`
  compartida por catálogo y spawners; `PROVIDER_UNSUPPORTED` queda solo para lo
  genuinamente desconocido.
- **AC-04**: una fila curada gana el empate contra una sintetizada del mismo tier por un
  flag explícito `is_inferred` en el sort key, no por el número `curated_priority=1000`.
- **AC-05**: una ruta sintetizada nunca alcanza tier `frontier` (cap `balanced`); se
  elimina la promoción por sufijo de nombre (`_FRONTIER_HINTS`). Frontier exige fila
  curada.
- **AC-06**: una ruta inferida solo es elegible como reviewer si su vendor-stem resuelve y
  difiere del writer; stem no resoluble ⇒ excluida (fail-closed) con reason code nuevo
  `REVIEW_IDENTITY_UNRESOLVED_INFERRED`. Un escenario que hoy da
  `REVIEWER_INDEPENDENCE_UNAVAILABLE` resuelve con un provider descubierto, y zen
  `claude-*` NO revisa a un writer anthropic (mismo stem).
- **AC-07**: `_parse_opencode_auth` deja de tratar filas `○` como autenticadas; el CLI id
  nunca se deriva por heurística espacio→guion; un provider cuyo CLI id no se verifica es
  no routable (caso `github-copilot`, M-1).
- **AC-08**: auth fresca en cada composición; el cache persiste solo listados de modelos,
  con key = set normalizado de providers autenticados + path/mtime del binario opencode +
  versión de schema. Cambiar el binario (mtime) invalida. Tras un fallo de reprobe del
  candidato elegido se re-rankea.
- **AC-09**: pins y preferencias validan contra el snapshot efectivo vivo, no contra la
  constante de 4 providers.
- **AC-10**: test lockstep `DISCOVERABLE_PROVIDERS == {p for _, p in _PAIR_COMMANDS}`.
  `enabled_providers`, `routes.v1.toml` y `ROUTING_PROVIDERS` no se amplían.
- **AC-11**: ADR-0034 escrito e indexado; tests-contrato afectados reescritos citando el
  ADR.

### PKG-2 — Billing-aware ordering + superficie de consola (ADR-0035)

- **AC-12**: `PROVIDER_BILLING_KIND` completo (subscription: openai-codex, anthropic,
  opencode-go; metered: opencode-zen) y `billing_rank(provider, model)` puro: 0 =
  subscription o modelo free (sufijo `-free`), 1 = metered/desconocido.
- **AC-13**: `billing_rank` entra en el sort key tras `TIER_ORDER` y antes de
  `_bias_rank`. Las exclusiones duras no cambian: zen se elige exactamente cuando es el
  único que satisface tier o el único que da independencia (dos tests).
- **AC-14**: reason code aditivo que deja el rank observable en `decisions-v1.jsonl`.
- **AC-15**: `set-agents --route-doctor` corre con probes frescos y reporta por par: auth,
  modelos, billing y diagnóstico del cache.
- **AC-16**: el panel de modelos muestra "proveedores descubiertos rutables: auto → lista
  viva" con billing; se reescriben el rótulo `DEFAULTS CURADOS (fallback…)` y la línea de
  política citando ADR-0034/0035; el wizard ofrece
  `auto (recomendado) / lista manual / ninguno`.

### PKG-3 — Capa cognitiva: `docs/modules/` (ADR-0036)

- **AC-17**: schema del doc de módulo en español, bloque máquina entre `<!-- notas:auto -->`
  reutilizando `merge_note`/`write_note`/`_short`, con zona humana preservada:
  Responsabilidad → Puntos de entrada → Componentes → Flujo → Posee/Depende de →
  Invariantes → Decisiones (wikilinks) → Últimos cambios estructurales (capado ~10).
- **AC-18**: registro `docs/modules/modules.toml` (`[module.<slug>]` con `nombre`,
  `responsabilidad`, `paths`), fuente de la detección: `owned_paths` del paquete +
  `changed_files` del receipt contra los globs.
- **AC-19**: `feature_state_lib/render_modules.py` con el mismo contrato never-raises /
  atómico / `render-failures.log` que `render_notes`; enganchado a la pasada de mutación y
  a `sync-notes`; un repo sin `docs/modules/` no falla.
- **AC-20**: comandos `record-module-impact` (con `--cambio` y `--modelo-mental`, imprime
  el bloque **Impacto humano**), `module-impact-detect` (no muta) y
  `--module-impact-waived --reason`.
- **AC-21**: gate — entrar a `INTEGRATION` exige que cada paquete accepted tenga
  `module_impacts` no vacío o waiver; `done_ready` agrega el mismo check. La relación con
  ADR-0024 queda registrada en el ADR-0036.
- **AC-22**: `cmd_digest` suma la sección `## Qué cambió en el software`.
- **AC-23**: merge idempotente con zona humana intacta (test round-trip); el render nunca
  rompe una mutación; `tests/test_module_docs.py` nuevo.
- **AC-24**: seed real de este repo: `modules.toml` + docs iniciales (routing,
  feature-state/estado, generación de árboles, app de consola, narración/notas) y
  `docs/architecture/overview.md` regenerado.

### PKG-4 — Doctrina: Impacto humano, question policy, `/explicar` (ADR-0036 + 0037)

- **AC-25**: el bloque de cierre de paquete en `orchestrator.md` suma el sub-bloque fijo
  `Impacto humano:` / `Módulo:` / `Cambio de modelo mental:` / `Tenés que saber:`, sin
  tocar los registros Cliente/Ingeniería (ADR-0027) ni el bloque de fin de turno
  (ADR-0033).
- **AC-26**: `integrator.md` suma el paso de `module-impact-detect` +
  `record-module-impact`/waiver + verificación de docs no stale; `architect.md` suma la
  creación de la entrada en `modules.toml` al diseñar un módulo nuevo.
- **AC-27**: ADR-0037 — protocolo `**Resolvé antes de preguntar (ADR-0037)**` insertado
  ANTES de la lista askable: cuatro fuentes en orden (pedido original, `docs/notas/`,
  `ai/state/decisions-log.jsonl`, spec aprobada/ADRs); lo ya resuelto se ejecuta con
  `log-decision`. El carve-out de plataforma nombrada queda como caso particular. Espejos
  de 2-3 líneas en `Global/_shared/CLAUDE.md`, `AGENTS.pi.md`, `AGENTS.opencode.md`,
  `Global/codex/AGENTS.md` y `skills/request-triage`.
- **AC-28**: `/explicar` — comando + skill canónicos, read-only, sin estado de feature:
  lee `modules.toml` + doc del módulo, sigue el código desde los puntos de entrada y
  devuelve el trace en registros `Cliente:`/`Ingeniería:` con `file:line` (ADR-0026);
  avisa si el doc está stale. Disponible en los 4 runtimes.
- **AC-29**: frases doctrinales exactas asserteadas en `test_harness.py`; árboles
  regenerados sin drift; `roles.tsv` sin cambios.

### PKG-5 — Tools discovery con aprobación humana (ADR-0038)

- **AC-30**: `--tools-propose <name> --kind cli|mcp|skill --detect <bin>
  --install-<method> "<cmd>" --why "<motivo>"` valida nombre y comando, **rechaza sudo y
  pipes ocultos**, imprime la pregunta consolidada y NO instala.
- **AC-31**: `--tools-approve <name>` escribe el bloque en `tools.local.toml` (nuevo,
  untracked, mergeado en `load_catalog`) + `log-decision`; la instalación sigue por el
  `cmd_tools_install` existente sin cambios de postura (sudo se muestra y se pregunta aun
  con `--yes`; MCPs entran disabled). Round-trip propose → approve → catalogado → install
  probado.
- **AC-32**: `TOOL_UNKNOWN` sugiere el flujo propose en vez de ser callejón sin salida.
- **AC-33**: `coord_policy._tools_channel_allowed` extiende el argv-walker a las dos flags
  con gramática cerrada (precedente SEC-001: nunca regex laxo).
- **AC-34**: skills instalables solo project-local (`.claude/skills/` del proyecto
  destino); mutar `Global/_canonical/` queda fuera de alcance, explícito en el ADR.
- **AC-35**: doctrina — "tool faltante" deja de ser blocker en `orchestrator.md` e
  `implementer.md`; ítem de menú "Proponer herramienta nueva" y las dos flags en consola.

## No-goals

- No se abre la vía curada: `enabled_providers`, `routes.v1.toml` y `ROUTING_PROVIDERS` no
  se amplían más allá de lo especificado.
- No hay techo de gasto mensual ni presupuesto por provider.
- No se agrega un gate permanente de auditoría externa (codex-audit).
- El gate de módulos no aplica a quick-fixes triviales: el waiver es la válvula.
- No se persisten listados descubiertos en `models.toml` (solo política y exclusiones).

## Riesgos

1. `tests/test_routing.py` y `tests/test_harness.py` son suites-contrato (frases por grep,
   defaults, byte-igualdad de las copias de `feature_state_lib`). Todo cambio doctrinal va
   ADR → test → código.
2. `models_config.emit()` dropea keys desconocidas: cada campo nuevo necesita test
   round-trip.
3. Copilot autenticado pero sin modelos listables (M-1): la auto-adopción debe fallar
   cerrada sin romper el resto del inventario.
4. El gate de módulos puede volverse fricción; el waiver debe ser barato y registrado.

## Gates

Por paquete: `python3 -m pytest tests/ -x` en verde, `./build.sh --check` sin drift, ACs
con evidencia `file:line`. Review independiente, findings estructurados, repair
consolidado, delta review, máximo 2 ciclos.
