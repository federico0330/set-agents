# 034 — Design: cuota orgánica y escritor barato

Feature `034-cuota-organica-y-writer-barato`. Slice `034-slice-cuota-plus-organic`.
Contrato de producto: `spec.md` (Draft). Este documento nombra el HOW; no reescribe el contrato.

**Estado:** design for implementer. Ningún campo JSON nuevo existe hoy en el árbol:
tratar cada nombre de este archivo como **UNVERIFIED-hasta-que-el-paquete-lo-persista**,
no como un hecho del código.

---

## Baseline

**Ninguna de las cuatro categorías de `solution-baselines` aplica.** SET-AGENTES es un
harness local multi-runtime (CLI + generación de árboles de agentes), no un dashboard
de gestión, un pipeline de scraping/ML, una API B2B ni un store/landing. El stack ya
está decidido (024/032: `git clone` + `./build.sh --install`; cinco harnesses; vault
Obsidian). El baseline aporta solo su checklist de riesgo y los tres ejes
data/gateway/deploy — y esos tres ya vienen respondidos por el pedido (abajo).
Convenciones existentes ganan.

### Confirmaciones (una línea, sin ADR)

- `billing_rank` se queda en su posición del sort key (ADR-0035). 034 no la mueve.
- `MODE_BUDGETS.scoped.max_spawns_per_package == 8` (`feature_state_lib/model.py:123-128`) no se toca.
- Cursor no entra a `models_config.RUNTIMES` (`models_config.py:44`) ni a `SELECTED_RUNTIMES`. `--route-decide` sigue prohibido en el anfitrión (`generate.py:125-132`).
- Vault Obsidian mandatory (ADR-0012, ADR-0056). Engram es no-goal.
- 033 no se reabre (menú freeze, lane única OpenCode, CI `8fd15fe`, PKG-6).
- `feature-state.py` es el único escritor de `ai/state/features/*.json` (ADR-0047: el path se mantiene, gitignorado).
- Independencia writer/reviewer (ADR-0011). Tests de independencia se reescriben, no se borran.
- El número 3 del umbral 1–3 archivos sigue cruzado con ADR-0020 (`orchestrator.md:24-41`).

### Desviaciones (cada una → ADR)

| Desviación | ADR |
|---|---|
| Default `code-rw` = barato/free que cumple tools, no sufijo `-fast`; `product-analyst` sale del loop | [0060](../../adr/0060-code-rw-default-barato-no-fast.md) (enmienda 0044) |
| Contador frontier distinto de `attempts.spawns`; techo 4/16; techo gana a salvage/promote | [0061](../../adr/0061-techo-frontier-aparte-de-spawns.md) |
| Un salvage pesado por paquete; convive con el techo de líneas de 0023; no es D2 de 0011 | [0062](../../adr/0062-salvage-unico-convive-con-0023.md) |
| Pins Cursor por rol desde `models.toml`; `inherit` deja de ser universal; 032 AC-06 superseded | [0063](../../adr/0063-cursor-pins-por-rol.md) |
| `init --mode scoped\|feature` exige `--risk-signal`; el test es CLI, no un LLM | [0064](../../adr/0064-ruteo-organico-enforceable.md) (enmienda 0020 write-side) |

---

## Scale / Data / Security decisions

Respuesta explícita a los tres ejes de `system-design-decisions`. Cada “no” es YAGNI
con umbral, no un silencio.

### Data store

**No hay store nuevo.** Los contadores frontier / salvage / green-on-first-attempt /
señal de riesgo / promoción viven en el JSON de feature-state que ya existe
(`ai/state/features/<id>.json`, gitignorado, ADR-0047). Relacional vs vector: **N/A** —
no hay búsqueda semántica nueva; el vault es markdown (ADR-0012).

Acceso: un writer (`feature-state.py` + lib), lectores derivados (`cost-report.py`
Sección 2, `render_status`, bitácora). Consistencia: un `mutate()` por verbo, el mismo
`atomic_write` de hoy. ACID vs BASE: el JSON es un documento local de un solo operador;
no hay réplica. Normalización: campos aditivos con `.get()` (precedente
`late_reviews` / `spawns` en `model.py:293-306`), nunca backfill de historia.

**YAGNI — umbral para un store aparte:** un techo mensual en USD, o un segundo
operador concurrente sobre el mismo feature file. Ambos están fuera de 034
(no-goal de ADR-0035 el primero; el harness es single-operator el segundo).

Componentes que **no** se agregan (cola, caché, CDN, réplica, shard, API Gateway):
ninguno tiene trigger medible. El “cupo” es un entero en el JSON, no un rate-limiter
distribuido.

### API Gateway

**N/A.** Harness local, sin API pública nueva. Un gateway se abriría si apareciera
un segundo consumidor externo de `--route-decide` o del JSON de feature; no es este
feature.

### Deploy

**Ya decidido (024/032):** `git clone` + `./build.sh --install`. No Vercel, no PaaS,
no VPS nuevo. 034 no cambia topología. Cursor sigue siendo runtime anfitrión (032),
no una lane de ruteo.

### Security (día uno, no se defiere)

- **AuthN/AuthZ:** no se tocan credenciales, `.env`, ni probes de suscripción más
  allá del inventario probe-driven ya existente (ADR-0029). Pins Cursor no habilitan
  `--route-decide` en el anfitrión.
- **Least privilege:** reviewers siguen `readonly: true` (032 AC-01, predicado
  Codex `sandbox_mode` reusado en `generate.py:572-574`). El pin de modelo no
  amplia herramientas.
- **Aislamiento:** Cursor host ≠ lane; un pin mal puesto gasta la sesión de Cursor,
  no la cuota OpenCode/Claude por un spawn CLI. Fail-closed: slug Cursor no medido
  no se inventa; no se vuelve a `inherit` universal en silencio (DEC-CURSOR-PIN).
- **Sesión/token:** sin cambio. El JSON de estado no lleva secretos; `risk_signal`
  es un token cerrado de producto, no PII.
- **Recovery:** el JSON sigue gitignorado; la siembra ADR-0047 no pisa un
  `ai/state/` existente. Un techo frontier chocado es `HUMAN_DECISION_REQUIRED` +
  `reopen` con contador etiquetado (extensión de ADR-0039, ver ADR-0061) — no un
  wipe del feature.

Observabilidad (excepción a defer): `% green-on-first-attempt` y `frontier_used/cap`
en `cost-report.py` Sección 2 (`cost-report.py:14-24`) y en status. No se suman
Sección 1 y 2 (023 AC-04).

---

## Capas y límites

034 no introduce un módulo nuevo. Extiende tres módulos ya registrados en
`docs/modules/modules.toml`:

| Módulo | Qué gana | Qué no gana |
|---|---|---|
| `estado` | señal de riesgo en `init`; `frontier_used`; flag salvage; contador de consecutivos; verbos que mutan esos campos | un segundo archivo de estado; Engram |
| `generacion-arboles` | dimensión `cursor` en `models.toml`; emisión de `model:` por rol; validador reescrito | Cursor como miembro de `RUNTIMES` |
| `routing` | default estático barato en `[areas.implement]`; razón del test hot-path | nueva posición de `billing_rank`; fila curada zen en `routes.v1.toml` (ver 0060, límite honesto) |

Regla de dependencia: la política “qué es barato” y “qué es frontier” vive en
funciones puras reusando `billing_rank` (`catalog.py:196-207`) y el piso de tools
ya existente (`service.py:368`, `set_agents_app.py:731`). El JSON no decide; el CLI
clasifica al persistir. El dominio de ruteo no importa feature-state; feature-state
puede leer `models.toml` / `billing_rank` para clasificar un `--model`, no al revés.

---

## Hoy X (medido 2026-08-19, re-leído esta sesión)

| Hoy | Evidencia |
|---|---|
| `init --mode` default `scoped`, comentario que asume señal de riesgo ya presente | `feature-state.py:875-878` |
| `cmd_init` no persiste señal de riesgo | `cli_lifecycle.py:150-181` |
| Skill dice quick-fix = default 1–3; tabla dice `scoped (default)` | `request-triage/SKILL.md:88-98` vs `:122` |
| Cierre `log-quickfix` con `--summary/--result/--file/--gate` | `feature-state.py:1194-1201` |
| Hot-path: loop `implementer`+`product-analyst` exige `endswith("-fast")` | `tests/test_harness.py:733-749` |
| `[areas.implement].opencode = "openai/gpt-5.6-fast"` | `models.toml:109-113` |
| `billing_rank` → 0 si subscription o sufijo `-free`, si no 1 | `catalog.py:196-207` |
| `MODE_BUDGETS.scoped` 8 despachos | `model.py:123-128` |
| `record-spawn` incrementa `attempts.spawns` y bloquea contra `max_spawns_per_package` | `feature-state.py:420-425` |
| Spawn entry opcional `--model/--provider/--effort/--route-id` | `feature-state.py:980-984` |
| `compact_package` no tiene frontier, salvage ni first-attempt | `model.py:277-347` |
| `generate.py` hardcodea `"model: inherit"` | `generate.py:572-574` |
| Variantes `<role>@<tier>` OpenCode-only (Cursor/Claude/Codex no las reciben) | `generate.py:581-585` |
| `MODEL_TIERS = ("fast", "balanced", "frontier")` | `models_config.py:45` |
| `validate_cursor_target` muere si no hay `\nmodel: inherit\n` | `generate.py:735-748` |
| Test `test_no_cursor_agent_pins_a_model` | `tests/test_harness.py:14016-14022` |
| Doctrina Cursor: “every role inherits” | `generate.py:136-139` |
| Live emitido `Global/cursor/agents/implementer.md:4` `model: inherit` | ese archivo |
| `AREA_FIELDS = ("claude", "codex", "codex_effort", "opencode")` — no hay `cursor` | `models_config.py:39` |
| `RUNTIMES` no incluye cursor | `models_config.py:44` |
| `family()` solo especializa `opencode_model` y `codex_model` | `models_config.py:560-568` |
| Un `opencode/*` **no proyecta** a `routes.v1.toml` | `generate.py:667-677` |
| Coherencia de variantes: exactamente 1 fila curada | `generate.py:689-711` |
| Tools de writer en `--route-decide`: `("read", "shell", "write")` | `set_agents_app.py:731` |
| Exclusión dura `TOOLS_MISSING` | `service.py:368` |
| `product-analyst` es `docs-rw` / `docs` | `roles.tsv:4` |
| `code-rw` en `roles.tsv:12-17` | test-writer … integrator, incl. repair-agent |
| Precedente `-free` vivo: `local-gate-runner` y `app-runner` | `models.toml:189-190`, `:249-250` |
| Override que contradice barato de área: `frontend-engineer` spark, `refactor-specialist` spark | `models.toml:237-238`, `:271-273` |
| Tiers implementer luna/sol/terra, todos OpenAI | `models.toml:240-247` |
| cost-report S2 cuenta `spawns[]` / history `record-spawn`; no hay % first-attempt ni frontier | `cost-report.py:14-24`, `:417-448` |
| Un `repair-agent` consolidado (doctrina), sin política de 1 escalada de modelo | `orchestrator.md:523-524` |
| Techo de líneas de repair: `check-repair-ceiling.py`, freeze en `record-repair` | ADR-0023, `cli_repair.py:36-41` |
| Exhaustion ≠ fallo de gate: 1 relaunch otro modelo | ADR-0011 D2 |
| `block_with_reason` etiquetas de contador: solo `attempts` \| `finding` | `cli_lifecycle.py:444-460` |
| cost-report S1 y S2 nunca se suman | `cost-report.py:26-30` |

---

## 1. Escritor barato (ADR-0060)

### Qué es “barato” (sin segundo decision-maker, sin ranking USD)

No hay fuente viva de precios USD en el repo (ADR-0026: memoria de modelo no es
fuente). No se agrega un scraper ni una tabla de list prices.

**Barato** = el candidato que (1) sobrevive el piso de tools de escritor ya
existente y (2) tiene `billing_rank == 0`. Entre varios `== 0`, se usa la
convención **ya declarada** dentro de `billing_rank` (`catalog.py:190-192`): el
sufijo `-free` es la convención FREE; un provider `subscription` es el otro
camino a 0. Orden de desempate para la **celda estática** (no para el sort key
de `route()`):

1. Piso de tools: el modelo tiene que poder `read` + `shell` + `write`
   (`set_agents_app.py:731`; exclusión `TOOLS_MISSING` en `service.py:368`).
2. `billing_rank == 0` gana a `== 1`. Si no hay ningún 0 que cumpla tools →
   `HUMAN_DECISION_REQUIRED` con el inventario medido, no un id inventado.
3. Entre varios 0: preferir `_FREE_MODEL_SUFFIX` (misma regex que
   `billing_rank`) sobre “solo subscription”. Eso no es un ranking USD ni un
   elemento nuevo del sort de `route()`.
4. Empate restante: orden ya existente del catálogo (`curated_priority`,
   `route_id`). Cero list prices.

**`billing_rank` no se inserta, no se reordena, no gana un tercer valor.**

### Dónde vive el default

La celda **estática** `[areas.implement].opencode` (`models.toml:109-113`, hoy
`openai/gpt-5.6-fast`). `load_roles` / `resolve_role` (`models_config.py:582-609`)
es lo que el test hot-path lee (`tests/test_harness.py:733-749`). Los roles
`code-rw` sin tabla `tiers` (test-writer, frontend-engineer, refactor-specialist,
repair-agent, integrator) heredan esa celda.

Overrides que hoy contradicen el default de área y **se borran** para heredar
el barato (DEC-ROLES-BARATO, un default, no un spark propio):

- `[roles.frontend-engineer].opencode = "openai/gpt-5.3-codex-spark"` (`models.toml:237-238`)
- `[roles.refactor-specialist].opencode = "openai/gpt-5.3-codex-spark"` (`models.toml:271-273`)

`product-analyst` (`roles.tsv:4`, `docs-rw`/`docs`, clase `decision` ADR-0018)
**sale del loop `-fast`**. Puede resolver frontier. Ningún test lo obliga a
`-fast` ni a `-free`. `[areas.docs]` no está forzado a copiar el barato de
implement.

### Límite honesto: variantes `@tier` y `routes.v1.toml`

`[roles.implementer.tiers.fast]` (`models.toml:240-241`) alimenta el agente
`implementer@fast`. `check_variant_catalog_coherence` (`generate.py:689-711`)
exige que ese id proyecte a **exactamente una** fila de `routes.v1.toml`.
`_opencode_projected_route` (`generate.py:667-677`) **solo** proyecta
`openai/<M>` → `(openai-codex, M)`. Un id `opencode/deepseek-v4-flash-free`
devuelve `None` y el build muere.

034 **no** abre el catálogo curado a zen, **no** relaja la coherencia de
variantes, **no** mueve `is_inferred` en el sort. Consecuencia: el default
barato/free aterriza en la celda **BASE** y en el pin Cursor (ADR-0063). El
`implementer@fast` ruteado en OpenCode sigue en la escalera curada luna/sol/terra
(todos `billing_rank` 0 por ser `openai-codex` subscription, ninguno `-fast`).
Auto-promotion (DEC-PROMOTE) sube **esa** escalera. El volumen de 034 en el
anfitrión Cursor no pasa por `@tier`.

**UNVERIFIED (T-B01, antes de pinnear):** si
`opencode/deepseek-v4-flash-free` (`models.toml:250`) — u otro `-free` vivo —
puede editar y correr validación local de un implementer. Si no, el siguiente
`-free`/subscription que sí cumpla tools. No se pinnea un id ciego.

### Test hot-path (patrón ADR-0044)

`test_repo_go_zen_routes_hot_path_to_fast_variants_and_keeps_reviewers_apart`
se **reescribe**, no se borra:

- `product-analyst` fuera de cualquier loop que exija `-fast`.
- `implementer` + al menos `debugger` o `frontend-engineer`: asertan barato/free
  (rank 0; si el elegido es `-free`, el sufijo es evidencia, no la regla).
- Mitad independencia `:750-766` **conservada** (`package-reviewer` /
  `adversarial-judge` familia distinta de `implementer`).
- Comentario del test cita 034 / ADR-0060. Mordida RED→GREEN obligatoria.

---

## 2. Salvage único (ADR-0062)

Un paquete cuyo implementer-barato dejó el gate rojo tiene **exactamente un**
salvage: `repair-agent` (u otra mutante fresca) en modelo **pesado**. Segunda
falla de gate en el mismo paquete → `HUMAN_DECISION_REQUIRED`. No hay segundo
salvage automático.

### Tres techos que conviven, no se sustituyen

| Techo | Qué cuenta | Dónde | Si se choca |
|---|---|---|---|
| `MODE_BUDGETS` `max_spawns` | despachos, cualquier modelo | `attempts.spawns` vs `budgets.max_spawns_per_package` (`feature-state.py:420-425`) | `spawn budget exhausted` |
| Frontier (0061) | despachos **no-barato** | `frontier_used` vs 4/16 | `FRONTIER_CAP_EXHAUSTED` |
| Líneas de repair (ADR-0023) | tamaño del diff de repair | `repair_ceiling` + `check-repair-ceiling.py` | `repair exceeded its frozen line ceiling` (`cli_repair.py:36-41`) |
| Salvage (este ADR) | escaladas de **modelo** por paquete | `package.salvage` (abajo) | segundo salvage rechazado → humano |
| Exhaustion (ADR-0011 D2) | plan/cuota agotada | relaunch 1× otro modelo | no es salvage; no es gate rojo |

El salvage **cuenta** como frontier (AC-C.2). Si el cupo frontier está lleno,
gana el techo (DEC-PRECEDENCE-CEILING, ADR-0061): no hay salvage “por arriba”
del cupo.

En lanes con `--route-decide`, el modelo pesado del salvage es un
`model_request` efímero (ADR-0044 P2) al frontier de la escalera, **después**
de las exclusiones duras. En Cursor: frontmatter de `repair-agent` **sigue
barato** (AC-D.1); el pesado es override de invocación (V-D03). Si V-D03
falla, **no** se pinnea pesado: `HUMAN_DECISION_REQUIRED`.

Doctrina: un `repair-agent` por fase de repair sigue siendo
`orchestrator.md:523-524`. 034 agrega: esa instancia, cuando es salvage de un
gate rojo del barato, va en modelo pesado y no se repite.

---

## 3. Techo frontier y métrica (ADR-0061)

Constantes **fuera** de `MODE_BUDGETS`:

```python
FRONTIER_CAP_PER_PACKAGE = 4
FRONTIER_CAP_PER_FEATURE = 16
```

Hoy `compact_package` (`model.py:277-347`) y `base_state` (`model.py:242-274`)
**no** tienen estos campos. Nombres abajo = diseño; el código aún no los tiene
(**UNVERIFIED-en-árbol**).

### Shape (aditivo, `.get()` default 0 / `None`, precedente `spawns`)

Feature (`base_state`):

```text
risk_signal: <token cerrado>          # set en init (ADR-0064)
frontier_used: int                    # default 0
writer_promotion: {                   # default {cheap_consecutive_failures: 0, next_rung: "base"}
  cheap_consecutive_failures: int     # +1 como máximo una vez por paquete (abajo)
  next_rung: "base" | "balanced" | "frontier"   # NUNCA "fast". Feature nueva = "base"
}
```

Package (`compact_package`):

```text
frontier_used: int                    # default 0
salvage: null | {spawn_id, role, model, at}
writer_rung: "base" | "balanced" | "frontier"   # copiado de next_rung al create-package; .get() → "base"
cheap_strike_recorded: bool           # latch: este paquete ya aportó +1 al contador de consecutivos
```

`next_rung` / `writer_rung` **no** defaultan a `"fast"`. `"fast"` es el primer
valor de `MODEL_TIERS` (`models_config.py:45`) y el nombre del agente
`implementer@fast` — OpenCode-only (`generate.py:581-585`: las variantes
`<role>@<tier>` no se emiten a Cursor, Claude ni Codex). El rung barato de
034 es la celda BASE (`[areas.implement]` / pin Cursor), no `@fast` (luna).
Feature nueva = `"base"`. Promoción Cursor = override de invocación (mismo
canal V-D03 que el salvage), no un agente `@tier` que Cursor no tiene.

Caps **no** se duplican en el JSON (evitar drift con las constantes). Status
renderiza `used/cap` leyendo la constante. `budgets.max_spawns_per_package`
sigue siendo el 8/12/4/6 de `MODE_BUDGETS`.

### Qué incrementa frontier

Un `record-spawn` cuenta frontier cuando **todas** son verdaderas:

1. `--model` está presente.
2. El modelo **no** es el default barato/free de AC-B.1 (celda
   `[areas.implement].opencode` resuelta, o el pin Cursor barato equivalente).
3. El rol **no** es `local-gate-runner` y el spawn **no** es P001
   (`feature-state.py:414-418` ya rechaza P001 en `gate-runner`; esos no
   cuentan).

Jueces en modelo pesado **sí** cuentan. Salvage **sí** cuenta. Spawn barato del
implementer **no** cuenta. `--model` ausente (callers viejos): **no** incrementa
frontier (aditivo, no rompe la suite; doctrina ADR-0031: el orquestador **debe**
pasar `--model` en 034). No hay flag `--frontier` seteable a mano: la
clasificación es del CLI, no del caller.

### Verbos

No hay un CLI nuevo de mutación. Se extienden los existentes:

| Verbo | Cambio |
|---|---|
| `init` | `--risk-signal TOKEN` (ADR-0064) |
| `record-spawn` | clasifica frontier; incrementa package+feature; `--salvage` marca `package.salvage` una vez |
| `record-gate` | **+1 `cheap_consecutive_failures` como máximo una vez por paquete** si el barato no fue green-on-first-attempt. Latch: `package.cheap_strike_recorded`. Si `package.salvage` **ya existe**, **no** incrementar de nuevo (el rojo del salvage no es un segundo fallo *del barato*). Green-on-first-attempt (gate verde **y** `salvage is None`) resetea el contador de feature a 0. Verde-después-del-salvage **no** resetea. |
| `create-package` | copia `writer_promotion.next_rung` → `package.writer_rung` (ausente → `"base"`). 2 consecutivos → `next_rung` sube `"base"` → `"balanced"` → `"frontier"` **para el próximo** paquete. OpenCode: `"balanced"`/`"frontier"` son `@tier` (`generate.py:581-585`). Cursor: override de invocación, no `@tier`. |
| `cost-report.py` S2 | deriva `% green-on-first-attempt` y muestra `frontier_used/cap` |

Errores nombrados: `FRONTIER_CAP_EXHAUSTED`, `SALVAGE_ALREADY_USED`. El
orquestador persiste `HUMAN_DECISION_REQUIRED` vía `block_with_reason`.

**Precedencia (DEC-PRECEDENCE-CEILING):** el chequeo de techo corre **antes** de
aceptar un salvage o un spawn promovido a no-barato. Cupo lleno → humano, no se
ignora el techo.

**ADR-0039:** `block_with_reason` hoy solo etiqueta `scope ∈ {attempts, finding}`
(`cli_lifecycle.py:451-456`). 0061 agrega un tercer shape cerrado:

```text
{"scope": "frontier", "key": "used", "grain": "package" | "feature"}
```

`reopen` resetea exactamente ese contador. No se mete `frontier_used` dentro de
`attempts` (el punto de 034 es que **no** es `attempts.spawns`).

### % green-on-first-attempt (derivado, no persistido)

Universo AC-C.6: spawn de implementer-barato que llegó a un gate de paquete.

- Numerador: gate verde **y** `package.salvage is None`.
- Denominador: todos los del universo (incluidos salvageados o rojos).
- Ausencia: paquete sin implementer-barato o sin gate → **fuera** del
  denominador (no 0%, no 100%).
- Fixture prohibido: contar verde-después-del-salvage como first-attempt.
  El porcentaje **no** se guarda en el JSON; `cost-report.py` lo calcula de
  `spawns[]` + `gates[]` + `salvage`. Un campo precomputado se stalea.

Auto-promotion: 2 fallos consecutivos del implementer-barato **en la feature**
(cada paquete aporta **como máximo +1**, aunque el salvage también deje el
gate rojo) → el **próximo** paquete arranca un rung más alto (`base` →
`balanced` → `frontier`). Feature nueva = `"base"`, no hereda, no arranca en
`"fast"`. No hay umbral %. En Cursor la subida es override de invocación
(`generate.py:581-585` no emite `@tier` ahí); si V-D03 no da override y el
rung no es `"base"` → `HUMAN_DECISION_REQUIRED`, no un pin pesado en
frontmatter.

---

## 4. Pins Cursor (ADR-0063)

### Fuente del pin

`models.toml`, dimensión nueva `cursor`, mismo merge ADR-0003: `[roles.<role>].cursor`
gana a `[areas.<duty>].cursor`. `AREA_FIELDS` pasa a incluir `"cursor"`
(`models_config.py:39`). `resolve_role` expone `cursor_model`.

Esto **no** hace a Cursor una lane: `RUNTIMES` (`models_config.py:44`) no
cambia; `generate.py:125-132` sigue prohibiendo `--route-decide` en el
anfitrión.

`[catalog].cursor` es la lista cerrada de slugs **medidos**. Un pin que no
está en esa lista hace `die` en `load_roles` (fail-closed, mismo patrón
claude/codex). **UNVERIFIED:** el contenido de esa lista — `https://cursor.com/docs/subagents`
timeout esta sesión (igual que el spec). T-D01 mide contra docs + picker de la
sesión **antes** de escribir un id. No se vuelve a `inherit` universal si la
medición falla: `HUMAN_DECISION_REQUIRED` con los slugs observados.

`generate.py:572-574` deja de hardcodear `"model: inherit"`. Emite
`model: {cursor_model}`. `validate_cursor_target` (`:735-748`) y
`test_no_cursor_agent_pins_a_model` (`tests/test_harness.py:14016-14022`) se
reescriben: pin presente, roster completo, `readonly` intacto, no todos
`inherit`, independencia o degradación explícita.

Doctrina (`CURSOR_DELEGATION_OVERRIDE` `generate.py:136-139`,
`Global/cursor/AGENTS.md`, `.cursor/rules/00-harness.mdc`): deja de decir
“No model is pinned”. Dice: pin por rol, independencia o degradación ruidosa,
sin `--route-decide`.

032 AC-06 entero y la cláusula `model: inherit` de 032 AC-01 quedan
**parcialmente superseded**. El archivo 032 no se reedita (contrato cerrado).
Siguen: roster, name/description, readonly, skills, install, `--check`,
bootstrap, no `hooks.json`.

### Independencia

`family()` (`models_config.py:560-568`) gana una rama `cursor_model`: consulta
`[families]` si hay entrada, si no el valor crudo (los slugs Cursor no traen
los sufijos OpenCode). **UNVERIFIED** si alcanza para dos familias reales —
T-D02 mide dos slugs vivos. Si el catálogo Cursor medido no ofrece dos
familias: pins de **modelo distinto** + degradación ruidosa en
`record-subreview --evidence` / `finalize-review-panel --evidence` (mismo
canal ADR-0011 D3 / 033). Mismo modelo que el escritor mientras exista
alternativa = fallo.

Roles `code-rw` pinnean el barato de 0060 (slug Cursor mapeado, UNVERIFIED).
DEC-ROLES-FRONTIER (`spec-challenger`, `package-reviewer`, `adversarial-judge`,
`architect`) pinnean otra familia. `product-analyst` / `architect` **pueden**
frontier; no están forzados al pin barato.

### Salvage y promoción en Cursor

Frontmatter de **todo** `code-rw`, incluido `repair-agent`, = barato (AC-D.1).
**No hay excepción que pinnee `repair-agent` pesado.** El modelo pesado del
salvage (y el de un paquete promovido, `writer_rung != "base"`) es override
de invocación. **UNVERIFIED** si Cursor acepta override de `model` al
despachar un subagente nativo (`~/.cursor/agents/repair-agent.md`) — V-D03.
Si V-D03 falla: `HUMAN_DECISION_REQUIRED`. No se cambia el frontmatter. Las
variantes `<role>@<tier>` son OpenCode-only (`generate.py:581-585`); Cursor
no tiene `implementer@balanced.md` que generar. Lanes con `model_request`
no necesitan override de frontmatter.

---

## 5. Ruteo orgánico enforceable (ADR-0064)

### Qué se TESTEA (no un LLM-judge)

Se **confirma** la propuesta del spec. El observable es el CLI, no un
clasificador de intención:

**Fixture:** un trabajo de blast radius 1–3 archivos (copy), sin ninguna señal
de la lista cerrada, que corre

```text
feature-state.py init … --mode scoped
```

**sin** `--risk-signal` → el comando **falla** con error nombrado
`RISK_SIGNAL_REQUIRED` y **no** crea (o no deja válido) el state file. El test
queda rojo si ese `init` es aceptado.

Ausencia de `init` es el camino feliz (AC-A.6): quick-fix =
`implement → gate → log-quickfix` (`feature-state.py:1194-1201` intacto). El
test de A.2 **no** exige un JSON de feature en el verde.

No se parsea el diff con un modelo. No hay “clasificador puro” obligatorio
además del flag: el orquestador **nombra** la señal (doctrina
`request-triage`) y el CLI **exige** que esté persistida para `scoped`/`feature`.
Una función pura `valid_risk_signal(token) -> bool` sobre el frozen-set es el
único predicado; el test del CLI es el de mordida.

### Flag y tokens

`init` gana `--risk-signal TOKEN`, obligatorio cuando `--mode` ∈ {`scoped`,
`feature`}. `incident` no (break-glass). `quick-fix` no (y el default operativo
de 1–3 sin señal **ni siquiera llama** `init`).

`--mode` default sigue siendo `scoped` (`feature-state.py:878`). Efecto:
`init` desnudo sin flag **falla**. Eso es lo que corta la ceremonia accidental.
No se cambia el default a `quick-fix` (eso crearía state file, contradice
AC-A.6).

Tokens cerrados (lista de `request-triage/SKILL.md:73-75` + el token de
producto ya nombrado):

```text
RISK_SIGNAL_TOKENS = frozenset({
    "money-billing",
    "data-migration",
    "auth-pii",
    "public-contract",
    "multi-module",
    "user-asked-full-pipeline",
})
```

Token desconocido → `RISK_SIGNAL_INVALID`. Un JSON editado a mano no es camino
verde (AC-X.2).

034 misma se `init --mode feature --risk-signal user-asked-full-pipeline`
(el usuario pidió SDD).

### Doctrina

Una sola frase en `request-triage` **y** `orchestrator.md`: default operativo
de 1–3 archivos sin señal = quick-fix. La tabla de presupuestos deja de llamar
`scoped` “default” para ese caso. El 3 sigue cruzado con ADR-0020.

Precedencia 033 AC-6.1: quick-fix **no crea** paquete → context pack no aplica.
Si el diff revela una señal, se escala con la señal nombrada y ahí rige 033.

ADR-0020 dijo que el write-side “ya está cubierto por mode selection”. 0064
hace **enforceable** esa mode selection en `init`. El número 3 no cambia.

---

## Trazado de consumidores (no-regresión)

| Campo / superficie | Quién lo lee hoy | Cambio 034 | ¿seguro? |
|---|---|---|---|
| `billing_rank` | `service.py` sort key | no se mueve | sí |
| `attempts.spawns` | `record-spawn`, `validate_state`, status, reopen | no se reusa para frontier | sí — contador nuevo |
| `MODE_BUDGETS` | `cmd_init`, `validate_state` | byte-igual scoped=8 | sí; tests de igualdad |
| `model: inherit` | `validate_cursor_target`, test 14016, doctrina | se reescribe, no se borra | sí si el sucesor aserta pin+readonly+independencia |
| loop `-fast` | test 733-749 | se reescribe | sí si independencia `:750-766` se conserva |
| `log-quickfix` flags | skill + CLI | intactas | sí |
| cost-report S1 vs S2 | `cost-report.py:26-30` | S2 gana dos líneas; no se suman | sí |
| `block_with_reason.counter` | `cmd_reopen` | tercer scope `frontier` | sí si el vocabulario queda cerrado y el default omitido sigue no reseteando |
| `[areas.implement].opencode` | `load_roles`, BASE agents, hot-path test | celda barata | sí para BASE; `@tier` no lee esta celda |
| `AREA_FIELDS` | `resolve_role` die on unknown | +`cursor` | sí; roles/áreas sin la clave fallan cerrado hasta que PKG-D las llene |

---

## Contrato del implementer

1. **No tocar** `billing_rank` ni su posición en el sort, ni `MODE_BUDGETS` scoped=8, ni 033, ni Engram, ni `RUNTIMES`.
2. **Mutar estado solo** por `feature-state.py`. Campos nuevos = los nombrados aquí; no existen en el árbol hasta que el paquete los persista (`.get()` / default, sin backfill).
3. **Tests de política se reescriben** (hot-path `-fast`, `test_no_cursor_agent_pins_a_model`, `validate_cursor_target`); no se borran. Independencia `:750-766` y `readonly` 032 se conservan. Mordida RED→GREEN en cada uno.
4. **Barato** = tools floor + `billing_rank==0` (+ preferir `-free` entre varios 0). Medir tools del candidato **antes** de pinnear. `opencode/*` no va a `tiers.*` (no proyecta). Borrar overrides spark de frontend-engineer y refactor-specialist.
5. **Orgánico:** `init --mode scoped|feature` sin `--risk-signal` → `RISK_SIGNAL_REQUIRED`. El fixture 1–3/copy sin señal es ese `init`. Salvage una vez; techo 4/16 gana; ADR-0023 intacto; D2 de 0011 no es salvage. `cheap_consecutive_failures` +1 **una vez por paquete**; si `salvage` ya existe, no otra vez. Feature nueva = rung `"base"`, nunca `"fast"`. Cursor: `cursor=` en `models.toml`, slugs **medidos**, frontmatter `code-rw` barato (incl. `repair-agent`); salvage/promoción = override o `HUMAN_DECISION_REQUIRED` (V-D03), no pin pesado ni `@tier`.

## Review gates que este cambio debe pasar

- `./build.sh --check` (incluye coherencia de variantes: no romperla con un `-free` en `tiers.*`).
- `ai/scripts/verify.sh` verde; aserciones netas de independencia no bajan.
- `git diff --check`; `check-owned-paths` **excluye** tui/wizard/lanes/CI de 033.
- Mordida: (A) `init --mode scoped` sin flag rojo; (B) pin barato roto rojo; (C) salvage-verde no sube numerador first-attempt; (D) `inherit` universal rojo; 5º frontier de un paquete muere.
- Panel independiente; writer ≠ familia reviewer (o evidencia de degradación no vacía).

## Tareas de verificación ANTES de implementar (UNVERIFIED)

| ID | Qué probar | Bloquea |
|---|---|---|
| V-B01 | ¿El `-free` candidato edita + corre validación local? | pin de `[areas.implement]` |
| V-D01 | Slugs `model:` vivos en Cursor (docs + picker). Timeout de fetch no cuenta como medición | cualquier pin Cursor |
| V-D02 | ¿`family("cursor_model", …)` distingue dos familias del catálogo medido? | independencia D; si no, degradación ruidosa |
| V-D03 | ¿La invocación de subagente Cursor acepta override de modelo (salvage y promoción)? | si no: `HUMAN_DECISION_REQUIRED`; frontmatter `code-rw` sigue barato |

---

## Fuera de alcance (reafirmado)

16 runtimes, RDD nativo Gentle, installer Go/brew, bench 36 journeys, perfiles
OpenCode Tab, Engram, reabrir 033, techo USD mensual, aflojar tests.
