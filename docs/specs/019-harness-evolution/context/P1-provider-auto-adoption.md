# Context pack — P1-provider-auto-adoption (ADR-0034)

Spec: `docs/specs/019-harness-evolution/spec.md` (aprobada, hash en el state file). Leé AC-01..AC-11
y la sección **Medición en vivo** completa — este pack cura, no reemplaza ese texto.

## Objetivo (AC-01..AC-11)

Que `[routing].discovered_providers = "auto"` (valor nuevo, default nuevo) vuelva **routable** todo
provider del set auditado que esté autenticado y cuyo CLI id sea verificable, con la vía curada
intacta. Hoy la rama existe pero está muerta: `discovered_providers` default `[]`
(`models_config.py:44`) apaga `build_effective_snapshot` (`service.py:142-151`), y el log real
(`~/.local/state/set-agentes/routing-v2/decisions-v1.jsonl`, 185 decisiones) tiene **0 zen, 0
copilot** y 9 halts `REVIEWER_INDEPENDENCE_UNAVAILABLE`.

## Medición viva YA HECHA — no la repitas, respetala (opencode 1.18.14, 2026-08-10)

`opencode auth list --pure` → 4 credenciales. `opencode models --pure` tras `--refresh` → prefijos
`ollama`, `openai`, `opencode`, `opencode-go`. Claves reales de `~/.local/share/opencode/auth.json`:
`opencode-go`, `openai`, `github-copilot`, `opencode`.

| display auth | auth.json key | CLI id listable | modelos |
|---|---|---|---|
| `OpenCode Go` | `opencode-go` | `opencode-go` | 18 |
| `OpenAI` | `openai` | `openai` | 13 |
| `GitHub Copilot` | `github-copilot` | **ninguno** — `Error: Provider not found: github-copilot` | 0 |
| `OpenCode Zen` | `opencode` | `opencode` | 60 |

Consecuencias **vinculantes**:

- **M-1 copilot**: autenticado pero opencode no lo lista ni tras `opencode models --refresh`. Por la
  regla fail-closed del spec: **no se agrega ningún par para `github-copilot`**, no se hardcodea
  ningún CLI id, no se inventa heurística. Lo que sí se hace: que la ruta de auto-adopción lo
  **detecte y lo descarte explícitamente** sin romper el resto del inventario, y que `--route-doctor`
  (P2) pueda reportarlo. Escribí esto en el ADR-0034 como límite conocido, con la medición como
  evidencia.
- **M-2 openai**: el provider opencode `openai` **ya es** el par `("opencode","openai-codex")`
  (`catalog.py:111,121` — display `openai`, CLI id `openai`). **No agregues un provider de catálogo
  `openai` nuevo**: sería un duplicado que colisiona en `_check_family_collisions` y en
  `SUBSCRIPTION_BY_PREFIX`. Lo que faltaba es que sus modelos descubiertos sean routables, que es lo
  que destraba `"auto"`.
- **M-3 ollama**: aparece en `opencode models` sin credencial → la adopción es auth-gated y lo deja
  afuera. Usalo como test negativo.
- **M-4**: zen expone `claude-*` y `gpt-*` — el riesgo de independencia de reviewer por vendor-stem
  bajo otro provider es real y vivo.

Neto esperado en producción: `"auto"` habilita tráfico real para `opencode-zen` y `opencode-go`
(y mantiene `openai-codex`); copilot no.

## Archivos (por qué cada uno)

- `ai/scripts/models_config.py`
  - `:41` `DISCOVERABLE_PROVIDERS` — hoy `{openai-codex, anthropic, opencode-zen, opencode-go}`.
    **AC-10**: agregá el test lockstep `DISCOVERABLE_PROVIDERS == {p for _, p in _PAIR_COMMANDS}`.
    Hoy eso YA se cumple; el test es la guarda. No agregues `github-copilot` (M-1) ni `openai` (M-2).
  - `:44` `ROUTING_DEFAULTS["discovered_providers"]` → nuevo default `"auto"`.
  - `:206-210` validación: aceptar el string `"auto"` **o** la lista actual. Nada más.
  - `:480-500` `emit()` — la clave vive en `[routing]`; verificá con un test round-trip
    load→emit→load que `"auto"` sobrevive como string y no degrada a lista (riesgo 2 del spec).
  - `:234` `_PROVIDER_SUBSCRIPTION` y `:52` `SUBSCRIPTION_BY_PREFIX`: no requieren entradas nuevas
    dado M-1/M-2. Si tocás algo acá, justificalo con la medición.
- `ai/scripts/routing_core/service.py`
  - `:142` `discovered = tuple(...)` — con `"auto"`, derivá los providers del **inventario probeado**
    ∩ `{p for _, p in _PAIR_COMMANDS}`. `inventory` ya está calculado en `:133`; usalo, no re-probees.
    La lambda `recheck` (`:146-148`) reprobea: la derivación tiene que ser la MISMA función pura en
    ambos lugares, o el recheck compone un universo distinto y todo cae en `AUTHORIZATION_INVALID`.
  - `:350` sort key. Hoy:
    `(same-provider-as-writer, pin_rank, TIER_ORDER, _bias_rank, curated_priority, route_id)`.
    **AC-04**: insertá un flag explícito `is_inferred` (curada = 0 primero) para que "curada gana
    empates" deje de depender del número `1000`. Posición: después de `TIER_ORDER` y del rank de
    billing que agrega P2 — coordiná: **P1 inserta `is_inferred` inmediatamente antes de
    `curated_priority`**; P2 insertará `billing_rank` entre `TIER_ORDER` y `_bias_rank`. Dejá un
    comentario que enumere la tupla final y un test tripwire que la pinee (precedente: el
    "point-5 tripwire test" de 014).
  - `:312-337` bucle de exclusiones. **AC-06**: agregá la guarda de reviewer para rutas inferidas.
    Hoy `:318-319` ya excluye por `_vendor_stem` igual al writer; falta el caso **fail-closed**: si
    el stem de una ruta inferida **no resuelve** (`vendor_stem` devuelve el id crudo, es decir no
    matcheó ningún `_VENDOR_STEMS`), la ruta **no es elegible como reviewer** → reason code nuevo
    `REVIEW_IDENTITY_UNRESOLVED_INFERRED`. No toques las exclusiones curadas.
  - `:409-421` re-probe del elegido. **AC-08**: hoy un fallo de reprobe devuelve
    `PROVIDER_UNAUTHENTICATED` y termina. Con inventario dinámico eso desperdicia candidatos
    válidos: **re-rankeá** contra el resto de los candidatos ya filtrados en vez de abortar, y
    recién si no queda ninguno devolvé el código actual. Mantené la propiedad de que lo que se
    autoriza fue reprobado fresco.
- `ai/scripts/routing_core/inference.py`
  - `:40` `_FRONTIER_HINTS` y `:60-67` `infer_tier`. **AC-05**: una ruta sintetizada nunca alcanza
    `frontier` — cap `balanced`. Eliminá la promoción por sufijo (un label controlado por el provider
    no puede auto-otorgarse trabajo crítico, hallazgo Codex #2). `_FAST_HINTS` se mantiene.
  - El docstring del módulo ya dice "an id nothing matches lands on `balanced`, NEVER `frontier`" —
    actualizalo para que diga la regla nueva completa y cite ADR-0034.
- `ai/scripts/routing_core/catalog.py`
  - `:196-207` `_parse_opencode_auth`. **AC-07**: `line.startswith(("●","○","*"))` trata las filas
    `○` como autenticadas. Corregilo: solo `●`/`*` cuentan. Verificado en vivo: en 1.18.14 todas las
    filas presentes son `●`, así que el cambio no altera el inventario real de esta máquina — pero
    cierra el defecto. Documentá eso en el ADR (cambio sin efecto observable hoy, correcto igual).
  - `:111` `_OPENCODE_PROVIDER_KEYS` / `:121` `_OPENCODE_CLI_IDS` / `:133-141` `_PAIR_COMMANDS`:
    **no se agregan pares** (M-1/M-2). Sí actualizá el comentario `:105-121` con la medición
    2026-08-10 y con la regla explícita "nunca derivar el CLI id por espacio→guion".
  - `:157-177` `_configured_models`: el techo por `[catalog]` de models.toml se **mantiene**
    (fail-closed). Las listas `opencode_zen`/`opencode_go` de `models.toml:24-25` fueron medidas el
    2026-07-30 y hoy difieren de lo vivo (ej.: ya no existen `claude-opus-4-1` ni
    `ling-3.0-flash-free`; aparecieron `ling-3.0-tiny-free`, `longcat-2.0-free`, `mimo-v2.5-free`,
    `qwen3.5-plus`). Refrescalas con lo medido en vivo y dejá la fecha en el comentario. La
    intersección es la que hace que "auto" no pueda ampliar el set auditado — no la saques.
  - `:261` `_cache_key` y `:281`/`:16` `PROBE_CACHE_TTL`. **AC-08**: la key debe incluir (a) el set
    normalizado de providers autenticados, (b) `path` + `mtime` del binario `opencode` resuelto, y
    (c) una versión de schema del cache. Además: la **auth se lee fresca en cada composición** y el
    cache guarda solo listados de modelos. Cuidá el fail-closed que ya existe (`_validate_cache_dir`,
    permisos 0600/0700, negativos nunca cacheados — F06/F09) y no lo debilites.
  - `:593-643` `build_effective_snapshot`: `providers` viene de config; con `"auto"` el llamador
    (service) le pasa la lista derivada. Mantené el guard `if provider not in audited: continue`.
- **Fuente única `provider_id → prefijo CLI opencode` (AC-03)**: hoy está duplicada e incompleta en
  `opencode_spawn.py:117` `_PROVIDER_PREFIXES = {openai-codex, opencode-zen, opencode-go}` frente a
  `catalog._OPENCODE_CLI_IDS` (que además incluye `anthropic`). Un provider descubierto elegido por
  el router muere en materialización con `PROVIDER_UNSUPPORTED` **después** de haber sido autorizado
  (hallazgo Codex #4). Unificá: `opencode_spawn.opencode_model_ref` debe leer la MISMA tabla que el
  catálogo (importá de `routing_core.catalog`, no copies), conservando el fail-closed de `anthropic`
  (el redirect a claude-code lo posee) y `PROVIDER_UNSUPPORTED` solo para lo genuinamente desconocido.
  Cuidado con los imports: `opencode_spawn.py` es un leaf; usá import perezoso si hace falta y probá
  que `tests/test_spawn_materialization.py` sigue verde.
- `ai/scripts/set_agents_app.py:92` `_MODEL_PREFERENCE_PROVIDERS` (tupla de 4) — **AC-09**: pins y
  preferencias validan contra el **snapshot efectivo vivo**, no contra la constante. Ojo: la
  validación corre también en `load_model_preference` en el arranque, donde probar puede ser caro o
  imposible; resolvelo sin volver el arranque dependiente de red (p. ej. validar contra el set
  auditado de `_PAIR_COMMANDS` + los providers del snapshot efectivo cuando ya hay uno compuesto, y
  degradar a advertencia en vez de `die()` cuando no se puede resolver). Justificá la elección en el
  ADR; no rompas el shape público de dos claves de `load_model_preference` (contrato ADR-0018/0032).

## Read-only (referencia, NO editar)

`ai/catalogs/routes.v1.toml` (6 filas curadas — la vía curada sigue cerrada), `models.toml`
`[routing].enabled_providers` y `models_config.ROUTING_PROVIDERS:36` (no se amplían, riesgo 5 del
spec), `ai/scripts/routing_core/store.py`, `ai/scripts/codex_spawn.py`,
`ai/scripts/claude_code_spawn.py`, `docs/adr/0029-probe-driven-model-selection.md`,
`docs/adr/0011-uninterrupted-delegation.md` (D4: `REVIEWER_INDEPENDENCE_UNAVAILABLE` sigue siendo
halt duro cuando de verdad no hay alternativa).

## Restricciones

- **ADR primero, después test, después código.** `tests/test_routing.py` (4968 líneas) y
  `tests/test_harness.py` (8653) son suites-contrato: pinean defaults, frases y tuplas por grep. Todo
  test que cambies se reescribe **citando ADR-0034 en el comentario**, y enumerás test-por-test qué
  cambió y por qué en la evidencia. Nunca debilites, saltees ni borres una aserción de regresión.
- El número de ADR: `ls docs/adr/` lista hasta `0033` hoy; usá **0034** y re-verificá justo antes de
  crear el archivo. Indexalo en `docs/adr/README.md`.
- No hay refactors oportunistas. No cambies APIs públicas fuera de lo que los ACs piden.
- La inferencia solo puede **quitar** independencia, nunca otorgarla (ADR-0029 d.3). Toda guarda
  nueva va en esa dirección.

## Validación local (correr todo antes de entregar)

`python3 -m pytest tests/ -x` (el conteo sube, nunca baja; cero skips nuevos) ·
`./ai/scripts/verify.sh` → `VERIFY_PASS` · `./build.sh --check` sin drift ·
`git diff --check` limpio · `python3 ai/scripts/check-owned-paths.py` contra el baseline.

Pruebas vivas que además tenés que dejar como evidencia (no reemplazan a los tests):

```
echo '{"role":"implementer","task_class":"implementation","risk":"low","selected_runtime":"opencode"}' \
  | ./set-agents --route-decide - --fresh-probes
./set-agents --routing-decisions --limit 5
```

## Evidencia esperada

Un archivo de evidencia con: AC → cambio (`file:line`) → prueba. Incluí (a) la salida real de
`--route-decide` mostrando un provider descubierto elegido, (b) la línea de `decisions-v1.jsonl`, (c)
la tupla final del sort key, (d) el test de copilot fail-closed, (e) el round-trip de `"auto"`.

## Checkpoint obligatorio

Este paquete toca autorización (independencia de reviewer). Cuando `"auto"` ya componga y ANTES de
tocar cache/pins, parate y escribí en tu archivo de evidencia el estado parcial + próximos pasos
exactos (disciplina de checkpoint del harness), por si te quedás sin presupuesto.

## Fuera de alcance — NO tocar

- `enabled_providers`, `routes.v1.toml`, `ROUTING_PROVIDERS` (más allá del test lockstep).
- Billing/costo, `--route-doctor`, panel y wizard: **eso es P2**, no lo adelantes.
- `docs/modules/`, narración, question policy, tools: P3/P4/P5.
- Agregar pares para `github-copilot` o un provider de catálogo `openai` (M-1/M-2).
- Persistir listados descubiertos en `models.toml` (solo política y exclusiones).
