# ADR-0034 — Auto-adopción de providers autenticados en el runtime OpenCode

- Estado: Accepted (2026-08-10). Feature 019 (harness-evolution), PKG-1. Extiende ADR-0029 ("el probe
  manda") — no lo supersede: ADR-0029 hizo routable un set FIJO y opt-in de providers (`_pair`s
  declarados a mano en `[routing].discovered_providers`); esta ADR abre ese mismo mecanismo a un
  valor `"auto"` que deriva el set del inventario probeado en vivo, cerrado siempre al universo
  auditado (`_PAIR_COMMANDS`).

## Contexto

`[routing].discovered_providers` (ADR-0029) ya podía volver routable un provider descubierto, pero
default `[]` lo dejaba muerto en la práctica: activarlo exigía editar `models.toml` a mano, listando
providers uno por uno. Medición en vivo del inventario real de esta máquina (opencode 1.18.14,
2026-08-10, `opencode auth list --pure` + `opencode models <id> --pure --refresh`):

| display auth | auth.json key | CLI id listable | modelos |
|---|---|---|---|
| `OpenCode Go` | `opencode-go` | `opencode-go` | 18 |
| `OpenAI` | `openai` | `openai` | 13 |
| `GitHub Copilot` | `github-copilot` | **ninguno** — `Error: Provider not found: github-copilot` | 0 |
| `OpenCode Zen` | `opencode` | `opencode` | 60 |

El log real de decisiones (`~/.local/state/set-agentes/routing-v2/decisions-v1.jsonl`, 185 entradas)
tenía 0 decisiones zen, 0 copilot, y 9 halts `REVIEWER_INDEPENDENCE_UNAVAILABLE` — tráfico real que un
inventario más amplio habría podido resolver.

Consecuencias vinculantes de la medición (no re-litigables en este ADR):

- **M-1 (github-copilot)**: autenticado pero **no listable** por opencode, ni siquiera tras
  `--refresh`. La regla fail-closed del proyecto (nunca hardcodear un CLI id no verificado, nunca
  derivar por heurística) hace que copilot **no sea routable** en esta feature. Se detecta y se
  descarta explícitamente (el bucle de auto-adopción sigue el resto del inventario intacto); no hay
  ningún par `("opencode","github-copilot")` en `_PAIR_COMMANDS`. `--route-doctor` (PKG-2) es quien
  reportará este caso al usuario; aquí solo se documenta el límite.
- **M-2 (openai)**: el provider opencode `openai` (credencial OAuth de ChatGPT) YA es el par
  `("opencode","openai-codex")` del catálogo (`catalog.py:111,121`, display `openai`, CLI id
  `openai`). No se agrega un provider de catálogo `openai` nuevo — sería un duplicado que colisiona
  en `_check_family_collisions` y en `SUBSCRIPTION_BY_PREFIX`. Lo único que faltaba era que sus
  modelos descubiertos fueran routables, que es justamente lo que "auto" destraba.
- **M-3 (ollama)**: aparece en `opencode models` sin credencial — la adopción es auth-gated
  (`_parse_opencode_auth` exige una fila de credencial real), así que queda afuera. Sirve de test
  negativo.
- **M-4 (vendor-stem)**: `opencode-zen` expone modelos `claude-*` y `gpt-*` bajo un provider
  distinto de `anthropic`/`openai-codex` — el riesgo de que una fila inferida "independiente por
  provider" en realidad comparta vendor real con el writer es vivo, no teórico (ver AC-06 más abajo).

## Decisión

1. **`discovered_providers` acepta `"auto"` como nuevo default** (`models_config.ROUTING_DEFAULTS`),
   además de seguir aceptando una lista explícita del set auditado (`DISCOVERABLE_PROVIDERS`, sin
   cambios: `{openai-codex, anthropic, opencode-zen, opencode-go}` — ni `github-copilot` ni `openai`
   se agregan, M-1/M-2). Un `[]` explícito sigue siendo la desactivación total, y sobrevive
   `emit()` (la comparación pasa a ser contra el default real, no contra "truthy", así un `[]`
   explícito ya no se pierde en el re-emit).
2. **Derivación única y compartida**: `catalog.resolve_discovered_providers(config, inventory)` es la
   ÚNICA función que traduce `"auto"` (o una lista) al set concreto de providers a sintetizar —
   `"auto"` deriva del inventario REALMENTE probeado (`probe_inventory`, ya calculado) intersectado
   con `{provider para (_, provider) en _PAIR_COMMANDS}`, nunca un universo más amplio. Tanto
   `service.py` (composición inicial) como su lambda `recheck` (re-probe de autorización) invocan
   esta misma función pura sobre inventarios frescos distintos — si derivaran por caminos separados,
   un candidato sintetizado autorizado en la composición podría no re-validar en el recheck
   (`AUTHORIZATION_INVALID` espurio).
3. **La fila curada sigue ganando el empate**, ahora por un flag explícito `is_inferred` en el sort
   key de `service.route` (posición inmediatamente antes de `curated_priority`, después de
   `_bias_rank`) — no por el número mágico `curated_priority=1000` que una fila sintetizada ya traía.
   PKG-2 (ADR-0035) insertará `billing_rank` entre `TIER_ORDER` y `_bias_rank`; la tupla final que
   deja esta ADR es:
   `(same_provider_as_writer, pin_rank, TIER_ORDER, _bias_rank, is_inferred, curated_priority, route_id)`.
4. **Una ruta sintetizada nunca alcanza `frontier`** (`routing_core/inference.infer_tier`, cap
   `balanced`): se elimina la promoción por sufijo de nombre (`_FRONTIER_HINTS`, hallazgo Codex #2 de
   la auditoría previa) — un label que el propio provider elige libremente (`-pro`, `-max`, `-opus`,
   ...) no puede auto-otorgarse trabajo de nivel frontier. `_FAST_HINTS` se mantiene: degradar a
   tier más bajo por convención de nombre es conservador (nunca amplía lo que el modelo puede hacer);
   promover a frontier no lo es.
5. **Independencia de reviewer para una fila inferida — fail-closed reforzado**: si el vendor-stem
   de una ruta inferida **no resuelve** contra ningún patrón conocido (`inference._VENDOR_STEMS`),
   esa ruta nunca es elegible como reviewer, código nuevo `REVIEW_IDENTITY_UNRESOLVED_INFERRED` — un
   stem desconocido no puede demostrar independencia del writer, así que se excluye en vez de
   asumirla. Este es el ÚNICO sentido en el que la inferencia puede mover una decisión: quitar
   elegibilidad, nunca otorgarla (ADR-0029 d.3, sin cambios).
6. **`_parse_opencode_auth` dejó de tratar `○` como autenticado** — solo `●`/`*` cuentan como
   credencial real. Verificado en vivo (1.18.14): las cuatro filas presentes hoy son `●`, así que
   este cambio no altera el inventario real de esta máquina; cierra el defecto igual (un futuro
   estado `○` — invitación pendiente, sesión expirada — ya no se contaría como autenticado).
7. **Cache de probe con key ampliada** (`catalog._cache_key`): además del hash de `[catalog]`/
   `[routing]` y el uid, ahora incluye (a) el set normalizado de providers OpenCode autenticados
   (lectura fresca y barata de `opencode auth list --pure`, sin listar modelos — la propia
   composición sigue leyendo auth fresca siempre, nunca cacheada), (b) path+mtime del binario
   `opencode` resuelto en PATH, y (c) una versión de schema de cache. Cambiar el binario invalida
   el cache sin exigir un bump manual de versión; el disco sigue guardando solo listados de
   modelos, nunca credenciales (F06/F09 intactos).
8. **Re-probe del candidato elegido re-rankea en vez de abortar**: si el candidato autorizado falla
   el re-probe fresco previo a la autorización durable, `service.route` descarta ese candidato y
   reintenta con el siguiente de la lista ya filtrada (misma revalidación de snapshot/inventario por
   candidato) — solo si ninguno sobrevive se devuelve `PROVIDER_UNAUTHENTICATED`. Un inventario
   dinámico amplía el pool de candidatos; abortar en el primer fallo desperdiciaba ese pool. Repair
   P1 (hallazgo F-04): cada candidato descartado por esta ruta deja un rastro aditivo en
   `exclusions` (`REPROBE_REJECTED <provider>/<model>`) — nunca reemplaza ni reordena un código
   existente, nunca cambia `success`/`runtime`/`identity`/`fallback` — así una decisión ganadora que
   NO fue el top-ranked original queda explicada en `decisions-v1.jsonl`, no muda.
9. **Una sola fuente `provider_id → prefijo CLI opencode`** (AC-03): `opencode_spawn.py` importa la
   tabla de `routing_core.catalog` (import perezoso, módulo hoja) en vez de mantener su propia copia
   parcial — un provider autorizado por el router ya no puede morir en materialización con
   `PROVIDER_UNSUPPORTED` por desincronización entre las dos tablas. `anthropic` sigue fallando
   cerrado ahí (el redirect a `claude-code` lo posee); `PROVIDER_UNSUPPORTED` queda solo para lo
   genuinamente desconocido.
10. **Pins y preferencias de modelo validan contra el snapshot efectivo vivo** cuando hay uno
    compuesto (AC-09): `_MODEL_PREFERENCE_PROVIDERS` deja de ser el techo — el set válido pasa a ser
    la unión de ese set auditado base y los providers que el snapshot efectivo actual reporta como
    routables. En el arranque (`load_model_preference`, donde probar red puede ser caro/imposible)
    esto degrada a WARNING en vez de `die()` cuando el snapshot no puede resolverse sin red — nunca
    vuelve el arranque dependiente de un probe.

## Alcance NO tocado por esta ADR

`enabled_providers`, `routes.v1.toml` (6 filas curadas) y `ROUTING_PROVIDERS` no se amplían — la vía
curada sigue cerrada. Billing/costo, `--route-doctor`, el panel de consola y el wizard son PKG-2
(ADR-0035), no se adelantan acá. No se persisten listados descubiertos en `models.toml` (solo
política y exclusiones, sin cambios de esa disciplina).

## Rejected alternatives

- **Hardcodear un CLI id para `github-copilot`**: violaría la regla fail-closed del proyecto —
  "nunca inventar heurística sobre un provider no verificado". Un futuro `opencode models --refresh`
  que sí lo liste activará la adopción automáticamente sin tocar código, porque `resolve_discovered_
  providers` deriva de inventario real, no de una lista mantenida a mano.
- **Agregar un segundo provider de catálogo `openai`** para separar la credencial OAuth de ChatGPT
  del `openai-codex` existente: es la MISMA credencial y el MISMO CLI id ya cubierto por
  `("opencode","openai-codex")` — un segundo provider sería un duplicado detectado por
  `_check_family_collisions`/`SUBSCRIPTION_BY_PREFIX`, sin beneficio real.
- **Promover tier por sufijo también en `"auto"`** (dejar `_FRONTIER_HINTS` vivo): un provider podría
  auto-otorgarse trabajo de auditoría/planificación crítico nombrando su modelo `algo-max`; eliminado
  por ser exactamente la inversión de "la inferencia solo puede quitar, nunca otorgar" (ADR-0029 d.3).

## Evidencia

`docs/specs/019-harness-evolution/evidence/P1-implementer.md` — tabla AC→archivo:línea→prueba, salida
real de `--route-decide`/`--routing-decisions`, la tupla final del sort key, y la enumeración
test-por-test de cada aserción reescrita en las suites-contrato.
