# 034 — Cuota orgánica y escritor barato

> Este spec está escrito para que lo implemente **Cursor**. Cada criterio nombra
> archivos y líneas del árbol **medidos el 2026-08-19**. Donde no pude medir,
> digo **sin verificar**. 033 no se reabre.

**Estado del contrato:** Draft (post-challenge 386b0051; F-034-01..08
aplicados, producto sin cambio).  
**Slice persistido:** `034-slice-cuota-plus-organic`
(`docs/notas/decisiones/2026-08-19 034-slice-cuota-plus-organic.md`).  
**Supersede parcial:** 032 AC-06 (y la cláusula `model: inherit` de 032 AC-01).
El resto de 032 (target Cursor, skills, install, `--check`, bootstrap, no-hooks)
sigue vigente. 032 está **shippeado**; este contrato no lo reabre.

---

## Problema

Federico paga varias suscripciones y el harness igual se come la cuota en
cambios chicos y en el volumen del escritor. Gentle-AI v2.3.0 (leído en
`/tmp/gentle-ai-v2.3.0`, tag `v2.3.0`) hace mejor tres cosas que este slice
copia **como comportamiento**, no como código:

1. Un cambio de 1–3 archivos no arranca ceremonia SDD
   (`internal/components/agentguidance/routing.go:46-58`,
   `docs/trigger-rules.md` rutas Direct inline / Optional SDD).
2. El trabajo de aplicar puede ir a un modelo barato
   (`docs/opencode-profiles.md`, perfil `sdd-apply-cheap` — configuración
   manual del usuario, no un default medido).
3. En Cursor, un subagente *puede* pinnear modelo en el frontmatter; SET hoy
   fuerza `inherit` en todos (`ai/scripts/generate.py:572-574`,
   `tests/test_harness.py:14016-14022`).

Y hay huecos que **nadie** cubre (canvas
`set-agents-vs-gentle-ai.canvas.tsx`, bloque "Nadie"):

- % medido de "el escritor barato cierra el gate a la primera".
- Default del implementer = lo más barato/gratis que cumpla tools (hoy el
  test obliga `-fast` = OpenAI).
- Techo de llamadas frontier distinto del techo de despachos.
- Un solo salvage caro si el barato falla.
- Auto-promotion de tier cuando el barato falla seguido.

El diagnóstico interno ya está medido y **no se re-litiga**:

| señal | valor | fuente |
|---|---|---|
| 033 menú freeze | cerrado (first paint ~30 ms en unittest) | `docs/specs/033-menos-espera-menos-cuota/evidence/INTEGRATION-before-after.md` |
| 033 CI | tres jobs verdes, SHA `8fd15fe72af2a97cbc9924af6cbc509d76cf2fdc` | misma evidencia, run `32208953619` |
| Hot-path `-fast` | `implementer` y `product-analyst` *deben* terminar en `-fast` | `tests/test_harness.py:733-749` · ADR-0044 |
| `billing_rank` | 0 = subscription o sufijo `-free`; 1 = metered | `ai/scripts/routing_core/catalog.py:196-207` · ADR-0035 |
| Cursor inherit | todos los agentes `model: inherit` | `docs/specs/032-cursor-como-runtime/spec.md` AC-06 · `generate.py:572-574` |
| Quick-fix en doctrina | default de 1–3 archivos, sin enforcement | `Global/_canonical/skills/request-triage/SKILL.md:88-98` |
| Init real | `--mode` default **`scoped`** | `ai/scripts/feature-state.py:875-878` |
| Techo scoped | 8 despachos/paquete — **no** es el techo frontier | `ai/scripts/feature_state_lib/model.py:123-128` |

El choque operativo: la skill dice que el default de un cambio 1–3 archivos
es quick-fix (`request-triage/SKILL.md:88-98`), y la tabla de la misma skill
dice que `scoped` es el default (`:122`). El CLI concreta el segundo: quien
corre `init` sin flag entra a ceremonia de paquetes. ADR-0020 ya unificó el
número 3 del lado de **lectura** (`orchestrator.md:24-41`); el lado de
**escritura** sigue siendo un párrafo.

---

## Usuarios

- Federico, operando el harness en **Cursor** (runtime anfitrión, 032) y en
  OpenCode/Claude/Codex cuando hay cuota.
- El orquestador (clasifica modo, despacha, no escribe código).
- Quien lee `cost-report.py` y la bitácora para ver si la cuota alcanza.

---

## Invariantes (no se relajan)

1. **Independencia writer/reviewer (ADR-0011).** En lanes con routing, el
   reviewer no comparte familia con el implementer. En Cursor, si se pinnea,
   el pin del reviewer **debe** ser familia distinta, o la degradación es
   ruidosa (evidencia en `record-subreview --evidence` /
   `finalize-review-panel --evidence`, como 033).
2. **`billing_rank` (ADR-0035) se queda.** A igual tier, subscription/free
   gana a metered. Este spec no toca la posición de `billing_rank` en el
   sort key.
3. **Los tests no se aflojan.** El test
   `test_repo_go_zen_routes_hot_path_to_fast_variants_and_keeps_reviewers_apart`
   (`tests/test_harness.py:733-766`) se **reescribe** con la razón nueva
   (barato/free primero; `product-analyst` sale del loop), no se borra. Mismo
   patrón que ADR-0044 usó con `orchestrator`.
4. **`MODE_BUDGETS` scoped = 8 no es el techo frontier.** El techo frontier
   es otro contador (N despachos pesados). No se sube `max_spawns`.
5. **`feature-state.py` es la única mutación de estado.** Cualquier
   contador, métrica o promoción se escribe por un verbo de ese CLI.
6. **033 no se reabre.** Menú freeze, lane única OpenCode, CI 8fd15fe y
   PKG-6 (context pack, P001, panel por riesgo) siguen.
7. **El vault Obsidian es mandatory** (ADR-0012, ADR-0056). No se reemplaza
   por Engram.

---

## Decisiones de producto (ya tomadas — no reabrir)

Persistidas en `034-slice-cuota-plus-organic` y en este contrato:

| id | decisión |
|---|---|
| DEC-SALVAGE | Una instancia de repair/modelo pesado **por paquete** si el escritor barato falla el gate. Segunda falla = `HUMAN_DECISION_REQUIRED`. No hay segundo salvage automático. |
| DEC-PROMOTE | Auto-promotion: **2 paquetes consecutivos** de la misma feature cuyo implementer-barato **no** cerró green-on-first-attempt → el próximo paquete sube un nivel. Grano: **máximo +1 por paquete**. Cheap-rojo + salvage-rojo en el mismo paquete = **un** consecutivo, no dos. Salvage-rojo **no** suma un segundo. No es un %. Un green-on-first-attempt del barato reinicia el contador. Feature nueva = BASE/pin barato (no `writer_tier="fast"`). En Cursor la subida es **override de invocación** al slug más pesado medido (o `HUMAN_DECISION_REQUIRED` si no hay override); no agentes `@tier` (`generate.py:581-585` es OpenCode-ONLY). |
| DEC-ROLES-BARATO | Default barato: todos los roles `capability == code-rw` (`roles.tsv:11-17`: `test-writer` … `integrator`, incl. `repair-agent`). El pin permanente de `repair-agent` es **siempre** el barato (AC-D.1). El modelo pesado es **override de invocación** solo en el salvage; si no hay override medido → `HUMAN_DECISION_REQUIRED`. No se pinnea pesado “por las dudas”. |
| DEC-ROLES-FRONTIER | Roles de juicio pueden seguir siendo frontier: `spec-challenger`, `package-reviewer`, `adversarial-judge`, `architect`. El ahorro es el volumen del implementer, no sacar al juez. |
| DEC-ANALYST | `product-analyst` es clase `decision` (ADR-0018: `duty IN {coord, docs}`; `roles.tsv:4` `docs-rw`/`docs`). Frontier **permitido**. Sale del loop `-fast`. No se trata como escritor. |
| DEC-FRONTIER-CAP | Techo frontier: **4** despachos pesados por paquete, **16** por feature. Chocar el techo = `HUMAN_DECISION_REQUIRED`. No se toca `MODE_BUDGETS`. |
| DEC-ORGANIC | Default operativo de un cambio 1–3 archivos **sin** señal de riesgo = quick-fix (`implement → gate → log-quickfix`) **sin** llamar `init`. `init --mode quick-fix` sigue existiendo (modo liviano con estado); no es el default 1–3. `scoped`/`feature` exige señal de riesgo **nombrada y persistida**. Gate rojo en quick-fix → reintento local o escala con señal nombrada; **no** salvage (el salvage es por paquete, DEC-SALVAGE). |
| DEC-CURSOR-PIN | Cursor pinnea modelo por rol. Federico lo eligió explícitamente. Rompe 032 AC-06 a propósito. |
| DEC-PRECEDENCE-CEILING | Si auto-promotion o salvage exigirían un despacho frontier y el techo ya está lleno, gana el techo → `HUMAN_DECISION_REQUIRED`. |

Señales de riesgo que **sí** justifican `scoped`/`feature` (lista cerrada, ya
en `request-triage/SKILL.md:73-75`): dinero/billing, migración de datos,
auth/permisos/PII, contrato público o API compartida, trabajo genuinamente
multi-módulo, o el usuario pidiendo el pipeline completo. "Se siente grande"
no es señal.

---

## Alcance

### 1) Escritor barato + un salvage caro + techo frontier + % green-on-first-attempt

- El default del implementer (y del resto `code-rw`) deja de ser "variante
  `-fast` de OpenAI" (hoy `[areas.implement].opencode = "openai/gpt-5.6-fast"`,
  `models.toml:109-113`; el test `:748-749` lo clava). Pasa a ser el modelo
  más barato/gratis que **cumpla tools** (el escritor tiene que poder editar y
  correr validación local). `billing_rank` ordena a igual tier.
- Un salvage caro por paquete si ese barato falla el gate.
- Contador frontier separado de `max_spawns`.
- Métrica `% green-on-first-attempt` del escritor barato, visible en estado
  y en `cost-report.py` Sección 2 (`ai/scripts/cost-report.py:14-24`).

### 2) Ruteo orgánico REAL (enforceable)

- Doctrina alineada: quick-fix es el default operativo de 1–3 archivos, no
  `scoped`.
- Un chequeo **observable** (test que falla) si un cambio 1–3 archivos entra
  a `scoped` sin señal de riesgo persistida.
- Cierre quick-fix sigue exigiendo `log-quickfix`
  (`feature-state.py:1194-1201`; skill `:97-98`).

### 3) Cursor pinnea modelo por rol

- `generate.py` deja de emitir `model: inherit` para todos.
- El validador `validate_cursor_target` (`generate.py:735-748`) y el test
  `test_no_cursor_agent_pins_a_model` (`tests/test_harness.py:14016-14022`)
  se reescriben: el pin existe, es por rol, y reviewer ≠ familia del
  implementer (o degradación ruidosa).
- Cursor **sigue sin ser lane de ruteo**: `--route-decide` y `*_spawn.py`
  siguen prohibidos en el anfitrión Cursor (`generate.py:125-132`).

---

## Fuera de alcance (no-goals, uno por uno)

1. **16 runtimes nuevos** (Windsurf, Kimi, Gemini, Gentle-Pi, etc.). SET se
   queda en los cinco harnesses actuales. Fuente Gentle: README tabla
   "Supported Agent Integrations" en `/tmp/gentle-ai-v2.3.0`.
2. **RDD nativo de Gentle** (`review start` / receipt / kill switch
   `review mode disable`, gates pre-commit/push/PR). Fuente:
   `/tmp/gentle-ai-v2.3.0/docs/architecture/organic-rdd.md` §§1–5 y
   `routing.go:61-72`. SET ya tiene panel + gates de repo; no se copia el
   control plane.
3. **Installer Go / brew / curl** de Gentle. SET sigue con
   `git clone` + `build.sh --install`.
4. **`bench/` de 36 journeys** de Gentle (`organic-rdd.md` §8,
   `bench/README.md` en el clone). SET sigue con `verify.sh` + bitácora.
5. **Perfiles OpenCode Tab** (`sdd-apply-cheap` / `sdd-orchestrator-{name}`).
   Fuente: `/tmp/gentle-ai-v2.3.0/docs/opencode-profiles.md`. SET no agrega
   un overlay de perfiles Tab; el default barato vive en `models.toml` +
   pins Cursor.
6. **Engram.** Federico usa Obsidian como contexto. El vault es mandatory
   (ADR-0012, `docs/notas/` + vault). Si el spawn no lee el vault, eso es
   **defecto de 005/025 / ADR-0056**, no un motivo para copiar Engram. Este
   spec no toca memoria cross-session más allá de lo que el vault ya es.
7. **Reabrir 033.** El menú, las lanes, Windows/CI y PKG-6 quedan como
   están.
8. **Subir `MODE_BUDGETS.scoped.max_spawns_per_package`.** El techo frontier
   es otro contador.
9. **Aflojar, saltear o borrar tests de regresión** para hacer pasar el
   cambio de política de modelos.
10. **Redactar ADRs desde este spec.** Architecture ya tiene 0060–0064 en
    draft (`docs/adr/0060-code-rw-default-barato-no-fast.md` y hermanos).
    Este spec **no** los redacta ni los stamp-ea; el índice ADR los trata
    como Proposed hasta `USER_APPROVAL`. Sigue exigiendo enmienda de 032
    AC-06 y de ADR-0044 (la razón `-fast`).

---

## Primer corte entregable

Los cuatro paquetes tentativos están en el slice ya decidido. El **primer
corte que desbloquea valor** es PKG-A (dejar de meter un arreglo de tres
archivos en ceremonia) + PKG-B (el escritor deja de ser OpenAI-por-sufijo).
PKG-C y PKG-D pueden seguir en el mismo feature; no son un segundo spec.

---

## Paquetes tentativos (el planner puede reagrupar)

### PKG-A — Ruteo orgánico enforceable

**Objetivo.** Un cambio 1–3 archivos sin señal de riesgo **no puede**
entrar a `scoped`/`feature` en silencio. Quick-fix es el camino que el
harness toma y que un test puede romper.

**Dónde vive el defecto hoy**

- Doctrina write-side: `Global/_canonical/skills/request-triage/SKILL.md:88-98`
  (quick-fix = default) vs `:122` (`scoped` = default del `--mode`).
- CLI: `ai/scripts/feature-state.py:875-878` (`default="scoped"`, con
  comentario que asume que quien llega a `init` ya tiene señal de riesgo).
- Read-side ya numerado: `Global/_canonical/agents/orchestrator.md:24-41`
  (ADR-0020). El ADR dice explícitamente que el write-side es mode
  selection, no un umbral nuevo — y ese mode selection **no se chequea**.
- Cierre: `log-quickfix` existe (`feature-state.py:1194-1201`) y es
  obligatorio en la skill (`:97-98`); no hay test que falle si un 1–3
  archivos se `init` como `scoped` sin señal.
- Contraste Gentle: `routing.go:46-58` — Direct inline 1–3 archivos;
  "File count … or perceived risk alone never selects SDD" (`:57`).
  SET no copia esa última frase: **una señal de riesgo nombrada SÍ
  selecciona scoped**. Lo que se copia es "sin señal, no hay ceremonia".

**Criterios**

- **AC-A.1** Tres superficies dicen lo mismo: (1) skill `request-triage`,
  (2) `orchestrator.md`, (3) el error nombrado `RISK_SIGNAL_REQUIRED` de
  `init --mode scoped`/`feature` sin señal (AC-A.3). Default operativo de
  1–3 archivos sin señal = quick-fix (`implement → gate → log-quickfix`).
  La tabla de presupuestos deja de llamar `scoped` "default" para ese
  caso. El número 3 sigue siendo la constante cruzada de ADR-0020:
  cambiarlo en un lado obliga a revisitar el otro.
- **AC-A.2** Existe un test que **falla** si un trabajo de blast radius
  1–3 archivos, sin ninguna de las señales de riesgo de la lista cerrada,
  queda registrado como modo `scoped` o `feature`. El HOW del guarda
  (flag `--risk-signal` en `init`, clasificador puro, o ambos) es
  **UNVERIFIED** y lo confirma architecture; el observable no.
- **AC-A.3** `init --mode scoped` o `feature` sin señal de riesgo
  persistida (vía `feature-state.py`, no a mano en el JSON) se rechaza
  con error nombrado `RISK_SIGNAL_REQUIRED`. La señal es uno de los
  tokens de la lista cerrada, o `user-asked-full-pipeline`.
- **AC-A.4** Un quick-fix que termina `done` sin `log-quickfix` sigue
  siendo defecto de doctrina; el test de A.2 no lo sustituye. El verbo
  `log-quickfix` no se elimina ni se vuelve opcional.
- **AC-A.5** Precedencia con 033 AC-6.1: el context pack obligatorio
  aplica a paquetes en `PACKAGE_IMPLEMENTATION`. Quick-fix **no crea**
  paquete; AC-6.1 no aplica. Si el diff revela una señal de riesgo, se
  escala a `scoped`/`feature` nombrando la señal (`request-triage/SKILL.md:94-96`)
  y ahí sí rige 033. Gate rojo en quick-fix (sin paquete): reintento
  local o escala con señal nombrada; **no** salvage.
- **AC-A.6** El universo de "cambio 1–3 archivos" es el blast radius
  declarado o medido del trabajo (archivos que el arreglo toca o nombra),
  no "cualquier repo con tres archivos". Ausencia de `init` no es fallo:
  el camino correcto de un 1–3 sin señal **es** no inicializar feature.
  `init --mode quick-fix` **sigue existiendo** (modo liviano con estado
  y presupuestos 4/1/2); el default 1–3 **no** lo llama. Un fixture que
  `init` scoped un arreglo de un archivo de copy **sin** señal tiene que
  poner el test en rojo. `init --mode quick-fix` no pinta AC-A.2 de rojo.

### PKG-B — Escritor barato y un salvage

**Objetivo.** El default del escritor es lo más barato/gratis que cumpla
tools. El test `-fast` se reescribe, no se borra. Un salvage caro por
paquete; el segundo fallo para.

**Dónde vive el defecto hoy**

- Test: `tests/test_harness.py:733-749` — loop
  `("implementer", "product-analyst")` exige
  `opencode_model.endswith("-fast")`. El comentario admite que eso mide
  "tiene que ser OpenAI", no latencia (ADR-0044).
- Default de área: `models.toml:109-113` `[areas.implement].opencode =
  "openai/gpt-5.6-fast"`.
- Tiers del implementer: `models.toml:240-247` luna/sol/terra — todos
  OpenAI, ninguno `-free`.
- `billing_rank` ya premia subscription/`-free` **dentro del sort**, no
  como default del rol (`catalog.py:196-207`).
- `product-analyst` no es escritor: `roles.tsv:4` `docs-rw`/`docs`.
- Salvage: el repair loop existe (`orchestrator.md:523-524`, un
  `repair-agent` consolidado) pero **no** hay política "1 escalada de
  modelo por paquete" (canvas, fila salvage).
- Ya hay un precedente `-free` en el árbol:
  `[roles.local-gate-runner].opencode = "opencode/deepseek-v4-flash-free"`
  (`models.toml:249-250`). **UNVERIFIED** si ese id (u otro `-free` vivo)
  cumple tools de un implementer.

**Criterios**

- **AC-B.1** El modelo por defecto de todo rol `code-rw` es el más
  barato/gratis del catálogo vivo que cumple tools de escritura y
  validación local. A igual capacidad, `billing_rank == 0` gana a
  `billing_rank == 1`. No se inventa un segundo ranking. El default de
  una **feature nueva** (paquete 1) es ese BASE/pin barato — **no**
  `writer_tier="fast"` ni `implementer@fast`
  (`models.toml:240-241` luna; `generate.py:581-585` variantes `@tier`
  son OpenCode-ONLY). Copiar `fast` al primer paquete viola este AC.
- **AC-B.2** `test_repo_go_zen_routes_hot_path_to_fast_variants_and_keeps_reviewers_apart`
  se reescribe (mismo nombre o sucesor documentado en el comentario del
  test, como ADR-0044 documentó la salida de `orchestrator`):
  - El loop `-fast` **ya no incluye** `product-analyst`.
  - `implementer` (y al menos un segundo rol `code-rw` de muestra,
    `debugger` o `frontend-engineer`) aserta barato/free-primero, no el
    sufijo `-fast`.
  - La mitad de independencia se **conserva**:
    `package-reviewer` / `adversarial-judge` siguen en familia distinta
    a `implementer` (`tests/test_harness.py:750-766`).
  - El comentario del test explica la razón nueva. Un test que nunca se
    vio rojo no cuenta.
- **AC-B.3** `product-analyst` puede resolver a un modelo frontier /
  de juicio. Ningún test lo obliga a `-fast` ni a `-free`.
- **AC-B.4** Si el implementer-barato falla el gate del paquete, hay
  **exactamente un** salvage: el mismo rol `repair-agent` (u otra
  mutante fresca) invocada con **override** al modelo pesado. El
  frontmatter/pin permanente de `repair-agent` sigue el barato (AC-D.1).
  Si el anfitrión no ofrece override de invocación medido →
  `HUMAN_DECISION_REQUIRED`, no se cambia el pin a pesado. Queda
  persistido vía `feature-state.py` (qué paquete, que fue salvage).
- **AC-B.5** Un segundo fallo de gate en el mismo paquete después del
  salvage = `HUMAN_DECISION_REQUIRED`. No hay segundo salvage automático.
  El retry de agotamiento de cuota (ADR-0011 D2) **no** es un salvage:
  es relaunch por plan exhausted, no por gate rojo, y sigue acotado a uno.
- **AC-B.6** Auto-promotion: 2 **paquetes** consecutivos de la misma
  feature cuyo implementer-barato **no** cerró green-on-first-attempt
  → el próximo paquete usa un nivel más pesado. Grano: **máximo +1 por
  paquete**. Cheap-rojo y salvage-rojo en el mismo paquete no suman dos.
  Salvage-rojo no incrementa. Se persiste. Un green-on-first-attempt del
  barato reinicia. Feature nueva = BASE barato, no `writer_tier="fast"`.
  En Cursor la subida es override de invocación al slug más pesado
  medido (o `HUMAN_DECISION_REQUIRED`); no se emiten agentes `@tier` ni
  se cambia el pin de `implementer.md`.
- **AC-B.7** Ningún test se borra para hacer pasar B. Si un test viejo
  ancla `-fast` en `implementer`/`product-analyst`, se reescribe
  conservando el invariante que todavía existe (independencia, o
  barato/free).

### PKG-C — Techo frontier y % green-on-first-attempt

**Objetivo.** Se puede ver y se puede chocar un cupo de modelos pesados
sin tocar `max_spawns`. Se puede leer qué porcentaje del barato cierra
a la primera.

**Dónde vive el defecto hoy**

- `MODE_BUDGETS` (`feature_state_lib/model.py:123-128`) cuenta despachos,
  no peso del modelo. 033 AC-6.4 hizo visible `usados/techo`; no distingue
  frontier.
- `cost-report.py` Sección 2 cuenta sesiones de `spawns[]` / `record-spawn`
  (`:14-24`, `:417-448`); no hay rollup por tier ni green-on-first-attempt.
- Canvas, filas "Nadie": métrica y techo frontier.

**Universo de la métrica (ausencia es señal)**

- **Universo:** todo spawn de implementer-barato de una feature que llegó
  a un gate de paquete.
- **Éxito (numerador):** ese spawn, **sin** salvage posterior en el
  paquete, deja el gate verde.
- **Denominador:** todos los del universo, incluidos los que salvagearon
  o quedaron en rojo.
- **Ausencia:** un paquete sin spawn de implementer-barato **no entra**
  al denominador (no es 0% ni 100%). Un paquete que no corrió gate no entra.
- **Fixture que lo engañaría:** contar un gate verde **después** del
  salvage como green-on-first-attempt. Prohibido. El criterio tiene que
  sobrevivir ese fixture.

**Criterios**

- **AC-C.1** El estado de feature expone, por paquete y por feature,
  `frontier_used / frontier_cap` (4 por paquete, 16 por feature,
  DEC-FRONTIER-CAP). Vive en el JSON de feature y se muta solo con
  `feature-state.py`. `MODE_BUDGETS` no cambia.
- **AC-C.2** Un despacho cuenta como frontier cuando el modelo asignado
  **no** es el default barato/free de AC-B.1. El salvage de AC-B.4 cuenta.
  `local-gate-runner` / P001 no cuentan (no son modelo pesado; 033 AC-6.2).
  Roles de juicio en modelo pesado **sí** cuentan — el techo recorta
  volumen de jueces, no los elimina.
- **AC-C.3** `record-spawn` (o el verbo que architecture nombre) rechaza
  un despacho frontier que excedería el techo, con error nombrado, y el
  orquestador persiste `HUMAN_DECISION_REQUIRED`. No se sube
  `max_spawns_per_package`.
- **AC-C.4** Precedencia con DEC-PROMOTE / DEC-SALVAGE: si el próximo
  movimiento legal sería un frontier y el cupo está lleno, gana el
  techo.
- **AC-C.5** `cost-report.py` Sección 2 muestra, por feature (y un total
  del `--project` / `--since`): `% green-on-first-attempt` del
  implementer-barato, más `frontier_used/cap`. No se suman Sección 1 y 2
  (023 AC-04, intacto).
- **AC-C.6** La métrica y los cupos se rellenan con los verbos existentes
  de ciclo (`record-spawn`, `record-gate`, salvage) — no con un JSON
  editado a mano. Un test de mordida rompe el conteo (p.ej. marca salvage
  como first-attempt) y ve el test rojo.

### PKG-D — Pins Cursor por rol (enmienda 032)

**Objetivo.** Cada rol Cursor declara un modelo. Independencia o
degradación ruidosa. 032 AC-06 queda parcialmente superseded.

**Dónde vive el defecto hoy**

- Generación: `ai/scripts/generate.py:565-578` hardcodea
  `"model: inherit"`.
- Validación: `generate.py:735-748` — si no hay `\nmodel: inherit\n`,
  `die`.
- Test: `tests/test_harness.py:14016-14022`
  `test_no_cursor_agent_pins_a_model`.
- Doctrina emitida: `generate.py:136-139` y
  `Global/cursor/AGENTS.md` / `.cursor/rules/00-harness.mdc` ("No model
  is pinned").
- 032 AC-01 pide frontmatter con `model: inherit`; AC-06 prohíbe ids
  concretos (`docs/specs/032-cursor-como-runtime/spec.md:32-47`).
- Live emitido: `Global/cursor/agents/implementer.md:4` `model: inherit`.
- Docs Cursor (citadas por 032, verificadas 2026-08-18): el campo
  `model` existe y default `inherit`; un id concreto es legal en el
  frontmatter. Catálogo vivo de slugs Cursor: **UNVERIFIED** (objetivo
  móvil; architecture mide contra https://cursor.com/docs/subagents
  y el picker de la sesión).

**Criterios**

- **AC-D.1** `./build.sh` emite un `model:` por rol en
  `Global/cursor/agents/<rol>.md`. No todos son `inherit`. Los roles
  `code-rw` — **incluido `repair-agent`** — pinnean el barato de AC-B.1
  (mapeado a un id Cursor **UNVERIFIED** hasta que architecture lo mida).
  El salvage pesado y la promoción de AC-B.6 son override de invocación,
  no un segundo agente ni un pin permanente pesado. Si no hay override
  medido → `HUMAN_DECISION_REQUIRED`. Los roles de juicio de
  DEC-ROLES-FRONTIER pinnean un modelo distinto, de familia distinta
  a la del implementer.
- **AC-D.2** `product-analyst` (y el resto `duty=docs` de juicio de
  producto: al menos `architect`) **pueden** pinnear frontier. No están
  obligados al pin barato.
- **AC-D.3** Independencia: el pin de `package-reviewer` (y
  `adversarial-judge`) no comparte familia con el pin de `implementer`.
  Si el catálogo Cursor no ofrece dos familias, se pinnea distinto
  modelo y se registra degradación ruidosa (mismo canal ADR-0011 D3).
  Mismo modelo + mismo pin que el escritor **no** es aceptable mientras
  exista alternativa.
- **AC-D.4** `validate_cursor_target` y
  `test_no_cursor_agent_pins_a_model` se **reescriben** (no se borran):
  dejan de exigir `inherit` universal; exigen pin presente, roster
  completo, readonly intacto (032 AC-01 resto), e independencia o
  degradación explícita. El comentario cita este spec y 032 AC-06
  superseded.
- **AC-D.5** Este contrato **supersede parcialmente** 032: AC-06 entero
  y la cláusula `model: inherit` de AC-01. Siguen vigentes 032 AC-01
  (roster, name/description, readonly), AC-02, AC-03, AC-04, AC-05,
  AC-07 (sigue sin `hooks.json`). Cursor no entra a
  `models_config.RUNTIMES`. `--route-decide` sigue prohibido en el
  anfitrión (`generate.py:125-132`).
- **AC-D.6** La doctrina instalada (regla `00-harness.mdc`,
  `AGENTS.md` Cursor, bloque `CURSOR_DELEGATION_OVERRIDE` en
  `generate.py:125-139`) deja de decir "no model is pinned". Dice:
  pins por rol, independencia o degradación ruidosa, sin
  `--route-decide`.

---

## Contratos públicos

- `feature-state.py` sigue siendo el único escritor de
  `ai/state/features/*.json`. Schema nuevo (cupos frontier, métrica,
  salvage, promoción, señal de riesgo) es **UNVERIFIED** en forma;
  architecture lo nombra. Producto exige los observables de C y A.
- `billing_rank(provider, model) -> 0|1` no cambia de semántica
  (`catalog.py:196-207`).
- `log-quickfix` conserva flags actuales
  (`--summary/--result/--file/--gate`, `:1194-1201`).
- `cost-report.py` no mezcla Sección 1 y Sección 2.

---

## Dinero, identidad, auditoría, concurrencia

- **Dinero:** el default barato y `billing_rank` existen para gastar
  suscripción/free antes que metered. El techo frontier es cupo de
  llamadas pesadas, no un presupuesto en USD. No hay techo mensual en
  dinero (sigue no-goal de ADR-0035).
- **Identidad:** no se tocan credenciales, `.env`, ni probes de
  suscripción más allá de usar el inventario ya probe-driven.
- **Auditoría:** salvage, promoción, señal de riesgo y despachos
  frontier quedan en el registro de feature (JSONL / JSON vía CLI).
  Degradación Cursor de independencia sigue en evidencia de review.
- **Concurrencia:** un paquete, un salvage. Dos repairs en paralelo
  contra el mismo gate no son salvage legal.

---

## Riesgos

| riesgo | mitigación |
|---|---|
| El modelo más barato no cumple tools (no edita, no corre tests) | AC-B.1 exige "cumple tools"; architecture verifica en vivo; no se pinnea un id ciego |
| Pins Cursor con slugs que Cursor no reconoce | AC-D.1 UNVERIFIED hasta medición; fail-closed a un id medido, no a inherit silencioso para todos |
| El guarda orgánico se vuelve un párrafo más | AC-A.2 es un test que falla; sin ese test el paquete no cierra |
| El techo frontier ahoga un panel de juicio legítimo | 4/paquete cubre reviewer + security + judge + salvage; chocar = humano, no subir scoped=8 |
| Auto-promotion y techo pelean | DEC-PRECEDENCE-CEILING: gana el techo |
| Reescribir el test `-fast` pierde independencia | AC-B.2 conserva `:750-766` |
| Copiar Engram "porque el spawn no lee el vault" | no-goal 6; defecto 005/025/ADR-0056 |
| 033 se reabre "de yapa" | no-goal 7; owned_paths de 034 no incluyen tui/wizard/lanes |

---

## Assumptions (HOW — UNVERIFIED, para architecture)

1. Forma del guarda orgánico (`init --risk-signal TOKEN` vs función pura
   testeada + doctrina). Producto exige el test de AC-A.2.
2. Id concreto del implementer barato en OpenCode y el slug Cursor
   equivalente. Candidato en árbol: `opencode/deepseek-v4-flash-free`
   (`models.toml:250`) — **sin verificar** tools de implementer.
3. Campos JSON exactos de frontier / green-on-first-attempt / salvage
   flag / consecutive-fail counter. Producto ya fija el grano: +1 por
   paquete si no hubo green-on-first-attempt; salvage no incrementa.
4. Mapa `models.toml` → `model:` de Cursor (catálogo vivo). Promoción y
   salvage en Cursor son override de invocación (no `@tier`;
   `generate.py:581-585` OpenCode-ONLY). Sin override medido → humano.
5. Si `family()` (`models_config.py:560-568`) alcanza para comparar pins
   Cursor o hace falta una tabla de familias Cursor.
6. Si `frontend-engineer`'s override actual
   (`models.toml:237-238` `openai/gpt-5.3-codex-spark`) se borra para
   heredar el barato de área o se reemplaza por un barato propio.
7. Nombre del campo de “nivel del escritor” si existe: el default del
   paquete 1 **no** puede ser el token `fast` de `MODEL_TIERS`
   (`models_config.py:45`, `models.toml:240-247`). Architecture nombra
   el HOW; el WHAT es BASE barato.

---

## Relación con 032 y 033

- **032** shippeado. Este spec supersede **parcialmente** AC-06 y la
  cláusula inherit de AC-01. No se reedita el archivo 032 (contrato
  cerrado); el índice y este spec lo declaran. Architecture escribe el
  ADR de enmienda.
- **033** en INTEGRATION, CI `8fd15fe`, menú freeze cerrado. No se
  reabre. AC-6.1 (context pack) cede ante quick-fix (AC-A.5).
- **ADR-0044** queda enmendado en la razón del test hot-path
  (latencia/`-fast` → barato/free). Architecture redacta. El patrón
  "reescribir el test, no borrarlo" se reutiliza.

---

## Spec audit

### Detección / ausencia — universo nombrado

| requisito | universo | ausencia | ¿la fuente carga la señal? |
|---|---|---|---|
| AC-A.2 / A.3 scoped sin señal | todo `init` / registro de modo de un trabajo 1–3 archivos | no hay `init` → es el camino correcto (quick-fix + `log-quickfix`) | `feature-state.py` `init`/`log-quickfix` sí; hoy **no** carga "señal de riesgo" — hay que agregarla |
| AC-C.5 % green-on-first-attempt | implementer-barato que llegó a gate de paquete | paquete sin ese spawn o sin gate → **fuera del denominador**, no 0% | `spawns[]` + `record-gate` sí existen; **no** hay flag salvage/first-attempt hoy |
| AC-C.1 techo frontier | despachos con modelo no-barato por paquete/feature | cero frontier → `0 / cap`, visible, no silencio | `record-spawn` registra rol; **no** registra peso frontier hoy |
| AC-B.6 consecutivos | paquetes de la feature cuyo barato no fue green-on-first-attempt | feature nueva → 0; salvage-rojo **no** entra | hay que persistir por paquete, no por evento de gate |
| AC-A.5 gate rojo quick-fix | quick-fixes que llegaron a gate | no-init + gate rojo → reintento o escala; no salvage | `log-quickfix --result` puede ser `blocked`; no hay paquete |
| Vault no leído al spawn | fuera de alcance (no-goal Engram); universo es 025/ADR-0056 | — | — |

### Parejas que disparan sobre la misma entidad

| par | conflicto | precedencia |
|---|---|---|
| AC-A.2 (quick-fix 1–3) vs 033 AC-6.1 (context pack) | un paquete exige pack; un quick-fix no es paquete | AC-A.5: quick-fix gana; si escala, 033 gana |
| AC-A.3 (scoped exige señal) vs usuario que pide SDD de 034 mismo | 034 es feature porque el usuario pidió SDD | señal `user-asked-full-pipeline` |
| AC-B.4 salvage vs AC-C.3 techo | salvage es frontier | DEC-PRECEDENCE-CEILING: techo gana |
| AC-B.6 cheap-rojo + salvage-rojo vs DEC-PROMOTE | dos gates rojos en un paquete | máximo +1 por paquete; salvage no suma |
| AC-B.1 BASE vs `writer_tier="fast"` | primer paquete en `implementer@fast` | BASE gana; `fast` no es el default de feature nueva |
| AC-B.4 salvage pesado vs AC-D.1 pin `repair-agent` | pin permanente vs invocación | pin barato siempre; pesado = override o humano |
| AC-B.6 promote vs AC-C.3 | promote convierte al escritor en frontier | techo gana |
| DEC-SALVAGE vs quick-fix gate rojo | salvage es por paquete; 1–3 no tiene | AC-A.5: reintento o escala; no salvage |
| AC-B.1 barato vs ADR-0011 independencia | barato writer + frontier reviewer es la forma **buena** | se conserva AC-B.2 mitad reviewer |
| AC-B.1 vs `billing_rank` | dos órdenes | default elige el pin; `billing_rank` ordena candidatos a igual tier. No se reemplazan |
| AC-D.1 pin vs 032 AC-06 inherit | contradictorios | 034 supersede parcial |
| AC-B.2 reescribe `-fast` vs ADR-0044 | la razón del test cambia | enmienda ADR-0044; el test no se borra |
| DEC-ANALYST frontier vs volumen | analyst en quick-fix no corre; en feature es un despacho | aceptable; no entra al loop barato |
| AC-C.2 jueces cuentan frontier vs "el ahorro es el implementer" | el techo puede cortar un segundo judge | 4/paquete deja reviewer+security+judge+salvage; el 5º para |
| ADR-0011 D2 exhaustion relaunch vs DEC-SALVAGE | parecen dos "segundas chances" | D2 = cuota/plan exhausted, modelo distinto, no es gate rojo. Salvage = gate rojo. Presupuestos separados |

### HOW marcado UNVERIFIED

Listado en Assumptions. Vacío en esta sección habría significado que no
miré.

### Qué no pude verificar

- Catálogo vivo de slugs `model:` de Cursor al 2026-08-19 (fetch a
  `https://cursor.com/docs/subagents` timeout en esta sesión; 032 lo
  midió el 2026-08-18 con `inherit` como default).
- Si `opencode/deepseek-v4-flash-free` (u otro `-free` del probe) puede
  editar y correr la validación local de un implementer.
- El plan `install_vs_gentle-ai` vive fuera del repo
  (`~/.cursor/plans/install_vs_gentle-ai_40940f7f.plan.md`); el canvas
  del proyecto es la comparativa canónica citada.
- Conteos live de `opencode models` hoy (033 dejó "sin verificar" el
  recuento 125; este spec no los necesita).
