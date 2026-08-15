# 029 — Convenciones antes del código

- **Estado**: Draft. Origen en pedido directo de Federico (2026-08-15):

  > *"el orquestador cuando uno le habla tiene que ser analítico. Si alguien le dice 'haceme una
  > página web para scrapear en Mercado Libre', no puede avanzar sin decirle 'ok, cerremos algunas
  > convenciones: ¿para quién es, qué vamos a usar de embedding, dónde va a estar alojada
  > inicialmente y cuándo escale?, la base de datos ¿es vectorial, relacional, no relacional?,
  > ¿queremos optimizarla como una app de tiempo real?, ¿vamos a hacer una app mobile?' etc. […]
  > No me interesa que el harness mienta ni invente, pero tampoco que comience a implementar sin
  > tener conocimiento —ni el desarrollador tampoco— de las decisiones que se van a llevar a cabo
  > en el proyecto."*

- **ADR reservado: 0058.** Verificado con `ls docs/adr/`: el último archivo escrito es `0052`.
  Los números intermedios están **reservados sin escribir**: `0050` y `0053`–`0056` por la feature
  025 (`docs/specs/025-consola-minima-y-flexible/context/D1-superficie-humana.md:66`,
  `D2-trabajo-visible.md:77`, `D3-posturas-de-autonomia.md:82`, `D4-harness-por-CLI.md:112`,
  `D5-vault-en-todo-spawn.md:99`), y `0057` por la feature 028
  (`docs/specs/028-narracion-que-ensena/spec.md:8-13`).
- **Relación con 028**: son complementarias y **no se pisan**. La 028 gobierna **cómo se cuenta lo
  que ya pasó** (campos de `log-narrative`, `STATUS.md`, digest). Esta gobierna **qué se cierra
  antes de que pase algo**. Ningún AC de esta spec toca `log-narrative`, `record-spawn`,
  `render_status.py` ni `render_notes.py` en los campos que 028 reclama. Punto de contacto único y
  declarado: la 029 produce el **contenido** (decisión + umbral + fuente) que la 028 exige que se
  **explique**. Si 028 se implementa primero, 029 le da material; si se implementa después,
  029 no pierde nada.
- **Precondición**: ninguna dura. **Acoplamiento blando con 028**, declarado abajo (E-5 y AC-18):
  las dos features necesitan el mismo predicado anti-relleno y el mismo espejo `PROYECTO/`. Se
  resuelve con orden y `owned_paths`, no con dependencia.

---

## Qué cambió en esta enmienda (ronda 1 de desafío)

| # | Enmienda | Efecto |
|---|---|---|
| E-1 | AC-18 validaba **sintaxis**, no aseveraciones: 3 modos de falla de 8 | Reescrito como **matriz origen × obligación**, con `source` **resoluble** y denylist |
| E-2 | `origin: user` era el camino más barato y nada podía desmentirlo | `asked_at` obligatorio, contrastado contra `narrative-log.jsonl` |
| E-3 | La guarda no tenía de dónde leer, y los dos arreglos obvios eran trampas | AC-23 (`--axes-log` explícito, **log ausente ⇒ rechazo**) + AC-24 (las 46 sedes de test) |
| E-4 | `log-decision` deduplica sin `feature_id`: colisión **esperada**, no borde | AC-12: JSONL propio `axes-log.jsonl`; `log-decision` queda intacto. AC-12c fija "gana el último" |
| E-5 | Sin `owned_paths`, choque con 028 en cuatro archivos y ruido en el digest | `owned_paths` por paquete + el JSONL propio resuelve el ruido |
| E-6 | *"un quick-fix no pasa por `init`"* era **falso** | AC-22 reescrito con el hecho; `incident` decidido explícitamente |
| E-7 | AC-08 (4×9 celdas) empujaba adonde AC-09 prohíbe ir | Sólo filas **diferenciables con fuente**; los transversales viven una vez |
| E-8 | El tope de 5 hacía que embeddings **no se preguntara nunca** | El tope acota lo que el harness **agrega**, no lo que el pedido **trae** |
| E-9 | El diagrama metía "registrar" dentro de la rama condicional | Registrar (incondicional) y preguntar (por evidencia) separados |
| E-10 | Carve-out de plataforma, `description` del frontmatter, regresión de template, conteo | Corregidos; el conteo de guardas falsas-verdes es **once** |
| E-11 | El pedido decía *"y cuándo escale"*: había `threshold`, faltaba el **adónde** | Campo `next_stance` en AC-12 |
| E-12 | Para el ejemplo de Federico el eje más consecuente no estaba | **Eje 10: legalidad y términos de uso**, con fuente en el repo |

---

## El problema, en una frase

El harness ya tiene escrita, en cuatro archivos, la arquitectura de referencia de cada categoría de
proyecto **con sus umbrales YAGNI** — y no la mira nadie en el único momento en que sirve: cuando el
usuario está hablando y todavía no se escribió una línea.

---

## La tensión central, y cómo se resuelve

Federico pide dos cosas que tiran en direcciones opuestas, en la misma oración:

1. **Que pregunte.** No arrancar sin las decisiones estructurales cerradas y a la vista.
2. **Que no invente.** ADR-0026 ya rige: ninguna afirmación técnica sin fuente.

Y hay una tercera fuerza que él no nombró: **un cuestionario no es análisis.** Un formulario que
dispara "¿base vectorial o relacional?" a secas es burocracia — le devuelve al usuario el trabajo de
diseñar. Un arquitecto trae un default razonado, dice hasta dónde aguanta, y convierte la pregunta
en **un bit** que el usuario sí puede contestar.

Las tres se resuelven con **una sola regla**, que es el corazón de esta spec:

> ### Contrato de la Pregunta Analítica (CPA)
>
> Una pregunta de intake sólo puede salir si lleva las cuatro partes:
>
> | Parte | Qué es | Qué falla si no está |
> |---|---|---|
> | **Default** | La postura propuesta, **citando el archivo que la contiene** | Sin default es un formulario |
> | **Umbral** | La condición medible que invalida ese default | Sin umbral el usuario no puede decidir |
> | **El bit** | Qué lado del umbral es su caso — no qué tecnología quiere | Sin bit se le delega el diseño |
> | **Consecuencia** | Qué cambia en el entregable si el bit se da vuelta | Sin consecuencia la pregunta es ociosa |
>
> **Y la cláusula ADR-0026**: si el harness no puede citar `archivo:línea` para el default o para el
> umbral, **no inventa el número**. Formula el eje abierto y lo marca `sin default verificado`.
> Un umbral inventado es peor que ninguno: el usuario contesta con confianza sobre una cifra falsa.

La forma canónica, con el ejemplo que dio Federico:

- ❌ *"¿La base de datos es vectorial, relacional o no relacional?"*
- ✅ *"Para scraping de Mercado Libre la postura por defecto es PostgreSQL con tabla cruda separada
  de la normalizada (`solution-baselines/references/scraping-datos-ml.md:19`). Se sostiene hasta
  ~50M filas calientes, y sólo cambia si vas a buscar por **similitud semántica** sobre el texto
  scrapeado — ahí primero se activa pgvector sobre el mismo Postgres, no una base aparte.
  **¿Vas a necesitar búsqueda por similitud, sí o no?** Si sí, se suma un paquete de embeddings y
  el costo de indexado; si no, no se toca nada."*

La segunda no es más larga porque sí: es más larga porque **el harness hizo el trabajo antes de
preguntar**. Ése es todo el delta entre un formulario y un análisis.

### Y la regla que impide que esto sea un interrogatorio

**Resolvé antes de preguntar (ADR-0037) tiene precedencia absoluta sobre el intake.** Un eje que ya
resolvió el pedido original, `docs/notas/`, `ai/state/decisions-log.jsonl` o la spec/ADR aprobados
**no se pregunta: se registra**. El intake de esta feature no agrega una pregunta más al harness;
agrega **un registro obligatorio por eje**, del cual preguntar es sólo uno de los orígenes posibles.

Ésa es la inversión que resuelve la tensión: **lo obligatorio no es preguntar, es que el eje quede
cerrado y escrito.** Preguntar es el camino más caro de los cuatro, y el último.

---

## Lo que ya existe y no se toca

Medido antes de proponer nada, para no reescribir lo que está y sólo enchufarlo.

> **Nota de nomenclatura**: acá los ítems son `Y-n` (*ya existe*). Los `E-n` de la tabla de arriba
> son las **enmiendas** de la ronda de desafío. Son dos series distintas.

### Y-1 — Los defaults con umbral **ya están escritos**, categoría por categoría

`Global/_canonical/skills/solution-baselines/SKILL.md:3` promete *"the three architecture axes
already taken with explicit YAGNI thresholds"*, y **es cierto**. Los cuatro archivos de
`references/` tienen cada uno una tabla `| Eje | Postura | Umbral YAGNI |`:

| Archivo | Línea de la tabla | Ejemplo de umbral verificado |
|---|---|---|
| `references/scraping-datos-ml.md` | `:16-21` | *"Embeddings/búsqueda semántica sobre texto scrapeado → pgvector; volumen > ~50M filas calientes → evaluar particionado antes que otra DB"* (`:19`) |
| `references/gestion-dashboard.md` | `:16-21` | *"costo PaaS > VPS×2 sostenido 3 meses"* (`:21`) |
| `references/api-b2b-integraciones.md` | `:16-21` | *"Volumen de eventos > ~1k/s sostenido → broker real"* (`:19`) |
| `references/ecommerce-landing.md` | `:19-24` | *"Personalización/recomendaciones → recién ahí evaluar eventos + pgvector"* (`:22`) |

**El caso exacto que Federico usó de ejemplo ya tiene su baseline**: `scraping-datos-ml.md:3-4`
describe *"recolectar datos de sitios/APIs de terceros, normalizarlos, almacenarlos con historia"*,
y `api-b2b-integraciones.md:3-4` nombra **MercadoLibre/MercadoPago** literalmente. La materia prima
del intake que él pidió está escrita desde el 27 de julio.

### Y-2 — El marco de decisión de diseño está completo

`Global/_canonical/skills/system-design-decisions/SKILL.md` (152 líneas) trae la tabla
"Add WHEN (measurable trigger)" para cache, cola, réplica, sharding y API Gateway (`:32-41`), el
árbol de plataforma de deploy (`:52-68`), la elección de store por patrón de acceso (`:80-98` —
incluye el criterio vector *"pgvector antes que un motor dedicado"*, `:92-98`), y la sección de
seguridad día-uno que **explícitamente no se difiere** (`:114-131`).

### Y-3 — El loop pre-aprobación existe y funciona

`REQUIREMENTS → SPEC_DRAFT → SPEC_CHALLENGE → USER_APPROVAL` está en
`Global/_canonical/agents/orchestrator.md:48-51`, y el `spec-challenger` **ya tiene** el chequeo de
los tres ejes como hallazgo bloqueante: `Global/_canonical/skills/spec-challenge/SKILL.md:16-20`
(*"A surface that plausibly needs one of these with no ADR addressing it is a blocking gap, not a
safe default to assume past"*). La Question policy también ya prohíbe el default silencioso en esos
tres ejes: `orchestrator.md:588-593`.

### Y-4 — El triage ya tiene el disparo y ya sabe que hay que interrogar

`Global/_canonical/skills/request-triage/SKILL.md:127-142`, sección "Architecture red-flags", es
**transversal a todos los modos** y ya distingue evidencia de plausibilidad
(*"The check fires on EVIDENCE, not plausibility"*, `:130-131`), con el ejemplo justo:
*"'add semantic search to the docs page' is a one-line ask, but it is a data-store decision"*
(`:135-136`). Y `:50-54` ya ordena, en modo feature, *"run the scoping interrogation (load
`system-design-decisions`)"*.

### Y-5 — La cañería de persistencia existe

`log-decision` (`ai/scripts/feature-state.py:1128-1139`) escribe a
`ai/state/decisions-log.jsonl` **y** regenera `docs/notas/decisiones/` con su nota `[[enlazada]]`,
y es idempotente (`ai/scripts/feature_state_lib/cli_reporting.py:83-113`). Hay 127 decisiones
registradas. No hace falta inventar un almacén nuevo.

### Y-6 — Ya existe el precedente exacto de "aserción obligatoria"

`ai/scripts/feature-state.py:806-808`:

```python
# Required, like `reopen --authorized-by`: an assertion that defaults to a value
# nobody chose is exactly the assertion this command used to make for free.
init.add_argument("--approved-by", required=True)
```

La guarda de esta feature **es la misma jugada, un nivel más abajo**: si `init` ya no acepta
"aprobado por nadie", tampoco puede aceptar "arrancado sin ejes".

**Conclusión de la medición: el 80% del contenido ya está en el repo. Lo que falta es la conexión
al momento de la conversación, el registro, y la guarda.**

---

## Los defectos, medidos

### D-1 — Los baselines nunca llegan al orquestador

`grep -rn "solution-baselines" Global/_canonical/agents/*.md` devuelve **exactamente dos**
resultados:

- `Global/_canonical/agents/project-bootstrapper.md:5`
- `Global/_canonical/agents/architect.md:20`

`orchestrator.md` **no lo nombra nunca**, y `request-triage/SKILL.md` tampoco (el mismo grep sobre
la skill da cero). El único skill que el orquestador tiene mandado cargar en el primer turno es
`request-triage` (`orchestrator.md:12`).

Y el frontmatter lo confirma como intención declarada:
`solution-baselines/SKILL.md:6` → `enabled_for: architect, project-bootstrapper, package-planner`.
El orquestador **no está en la lista**. La biblioteca de defaults con umbral existe y está dirigida
a roles que sólo aparecen **después** de que el usuario dejó de hablar.

### D-2 — Los ejes se revisan un paso tarde, y el chequeo es un hallazgo, no un intake

El flujo de delegación (`orchestrator.md:151-169`) es explícito en su orden:

1. `product-analyst` redacta el contrato y la aceptación (`:153-154`).
2. `architect` *"always checks the three named architecture axes"* (`:155-158`).
3. `spec-challenger` los vuelve a chequear contra `design.md` (`:162-165`).
4. Recién ahí `USER_APPROVAL` (`:166-169`).

O sea: **la spec se escribe primero y los ejes se auditan después.** Cuando el `architect` descubre
que el eje está abierto, ya hay un documento redactado sobre supuestos no declarados, y el camino de
vuelta es un hallazgo bloqueante del `spec-challenger` → revisión → re-redacción. El harness paga
un ciclo de reparación por algo que se resolvía con una pregunta de una línea antes de empezar.

`enabled_for` **no es un mecanismo**: `grep -rn "enabled_for" --include="*.py" --include="*.sh" .`
devuelve **cero** coincidencias en código (la única línea es un comentario en
`tests/test_harness.py:10787`). El ruteo de skills es prosa; nada impide ni obliga nada.

### D-3 — El intake no deja rastro, por construcción

El archivo de estado nace **después** de la aprobación. Medido sobre los 24 archivos de
`ai/state/features/*.json`: el evento `init` de **los 24** tiene `from: "USER_APPROVAL"` y
`to: "PACKAGE_PLANNING"` (conjunto único de transiciones de init = `{('USER_APPROVAL',
'PACKAGE_PLANNING')}`). Y está documentado como deliberado en
`ai/scripts/check-feature-state.py:20-25`: *"A spec is legitimately written and revised during
SPEC_DRAFT and SPEC_CHALLENGE, before the state file is supposed to exist"*.

Consecuencia: **las cuatro fases donde se decide la arquitectura del proyecto son las únicas del
ciclo sin ningún artefacto de máquina.** Y el registro voluntario tampoco se usa. Medido sobre las
entradas de `ai/state/decisions-log.jsonl` (127 en la primera pasada, 130 al reverificar) cruzadas
contra el timestamp de `init` de cada feature:

| Medición | Resultado |
|---|---|
| Features con archivo de estado | 24 |
| Features con **cero** decisiones registradas antes de su `init` | **18 / 24** |
| Features desde la 010 inclusive con cero decisiones pre-`init` | **16 / 16** |
| Decisiones pre-`init` en total | 14, todas en 003-009 |
| De esas 14, cuántas cierran un eje de arquitectura | **0** |

Las 14 se inspeccionaron una por una: son autorizaciones de reparación, enmiendas y actas de
incidente (*"Excepción autorizada: tercer intento de arquitectura P1R"*, *"Re-init forzado del
estado de 008"*, *"La feature 006 se entrego sin archivo de estado"*). Ninguna dice qué store, qué
deploy o qué gateway se eligió y por qué. Las otras 113 son post-`init` por construcción, así que no
pueden ser registros de intake.

**El pedido de Federico — *"ni el desarrollador tampoco"* — está medido: en las últimas 16 features,
cero decisiones estructurales quedaron escritas antes de empezar.**

### D-4 — No hay un catálogo de ejes: hay tres, y Federico nombró ocho

Todo el aparato existente gira sobre **"the three named architecture axes"**: data store, API
Gateway, deploy platform. Aparece con ese nombre en `orchestrator.md:156`,
`request-triage/SKILL.md:128-129`, `spec-challenge/SKILL.md:16`, `architect.md:29` y
`spec-challenger.md:21`.

El pedido nombra ocho: **para quién es** (audiencia), **embeddings**, **alojamiento inicial**,
**alojamiento al escalar**, **modelo de datos**, **tiempo real**, **superficie mobile**, y por
implicación **costo**. De ésos, los baselines cubren hoy tres y medio:

- data store ✅, deploy inicial ✅, gateway ✅
- **deploy al escalar**: parcialmente, dentro del umbral de deploy (`gestion-dashboard.md:21`)
- **audiencia / tiempo real / mobile / auth / costo**: no son ejes; aparecen sueltos dentro del
  stack golden-path (ej. auth en `gestion-dashboard.md:11-12`, costo sólo como umbral de deploy)

"Los tres ejes" no es un error, es un alcance: son los tres **irreversibles**. Pero el pedido de
Federico es más ancho y la spec tiene que decir explícitamente cuáles son de primera clase
(bloquean el arranque) y cuáles son de segunda (se asumen y se declaran).

### D-5 — El destino documental del intake existe y se entrega vacío

`project-bootstrapper.md:5-7` manda registrar la baseline elegida en
`docs/project/architecture.md`. Ese archivo lo crea `ai/scripts/bootstrap_project.py:27` con
contenido literal:

```python
"docs/project/architecture.md": "# Architecture\n\nTODO: boundaries, dependencies, and deployment.\n",
```

Un `TODO:` de tres líneas. Y en este propio repo el path **no existe** (`ls docs/` → sin `project/`);
está en la lista de waivers de `ai/scripts/check-canonical-paths.py:42` precisamente para que la
guarda no lo reporte. El lugar donde debería vivir el resultado del intake es un placeholder
waiveado.

### D-6 — Nada mecánico distingue "eje decidido" de "eje nunca mirado"

`ai/scripts/coord_policy.py` (327 líneas) es una allowlist de comandos; no conoce el concepto de eje
ni de intake. `ai/scripts/verify.sh` corre unittest, `py_compile`, `check-canonical-paths.py` y
`check-feature-state.py` (`verify.sh:13-60`) — ninguno mira decisiones de diseño. `init` exige
`--approved-by` y nada más sobre el contenido de lo aprobado.

Es exactamente la familia de defecto que la 027 catalogó: *"algo que informa OK sobre algo que no
mira"* (`docs/specs/027-controles-que-miran/spec.md:17`; el conteo del repo hasta 027 es 5 guardas
falsas-verdes ya reparadas + 4 abiertas + 1 flageada, `:11-17`; **la undécima** la encontró 028 y la
nombra sin sumarla: `tests/test_digest.py:266-268` itera sobre tres archivos compartidos y omite
`AGENTS.codex.md`). Acá el caso es peor: no hay guarda que mienta, **no hay guarda**.

---

## El disparo: registrar es incondicional, preguntar es por evidencia

*(reescrito por E-9: la versión anterior metía "registrar TODOS los ejes" adentro de la rama
condicional, y una feature que no tocaba ningún eje rebotaba en `init` sin camino para llegar a los
registros.)*

**Son dos obligaciones distintas y no se disparan igual.** Confundirlas fue el defecto de la ronda
anterior:

| | **Registrar** | **Preguntar** |
|---|---|---|
| Alcance | **Todo lo que llegue a `feature-state.py init`**, sin excepción de modo | Sólo lo que queda abierto |
| Condición | Incondicional | Evidencia en el pedido + las cuatro fuentes de ADR-0037 mudas |
| Universo | Los **10** ejes del catálogo, siempre | Un subconjunto, acotado por AC-05 |
| Costo típico | 6-8 filas son `assumed` o `n/a` de una línea | 3 a 7 preguntas en **un** bloque |

```
                          pedido del usuario
                                  │
                        ┌─────────┴─────────┐
                        │  request-triage   │   (obligatorio, orchestrator.md:12)
                        └─────────┬─────────┘
                                  │ modo
     ┌──────────────┬─────────────┼──────────────┬──────────────┐
     │              │             │              │              │
  consult      quick-fix      incident        scoped         feature
     │              │             │              │              │
  sin init     ¿red-flag      init --mode        └──────┬───────┘
  sin ejes     arquitect.?    incident                  │
     │         (SKILL:127)    (AC-22)          ┌────────┴────────┐
     │          sí → escala        │           │ PREGUNTAR corre │
     │          no  → sigue        │           └────────┬────────┘
     │              │              │            1. clasificar baseline
     │         log-quickfix        │            2. resolver por ADR-0037
     │         (sin init,          │            3. lo que queda: CPA, ≤7, 1 bloque
     │          sin ejes)          │                     │
     │              │              │                     │
     └──────────────┘              ▼                     ▼
                          ┌─────────────────────────────────────┐
                          │ REGISTRAR: los 10 ejes, siempre     │
                          │ origin ∈ {request notas log adr     │
                          │           user assumed n/a}         │
                          └──────────────────┬──────────────────┘
                                             ▼
                                 feature-state.py init
                          rechaza: eje ausente · relleno ·
                          source irresoluble · assumed sin umbral
```

**Preguntar corre** cuando se cumplen las dos: (a) el modo es `scoped` o `feature`, **y** (b) al
menos un eje del catálogo está tocado por evidencia en el pedido y no lo resuelve ninguna de las
cuatro fuentes de ADR-0037.

**Preguntar no corre** en `consult` (no hay `init`), en `quick-fix` (su único control sigue siendo
el red-flag transversal, `request-triage/SKILL.md:127-142`, cuyo resultado es una **escalada de
modo** que a su vez dispara el intake) ni en `incident` (ver AC-22: producción caída no se detiene
por un cuestionario).

**Registrar corre siempre que haya `init`** — incluido `init --mode quick-fix` e
`init --mode incident`, que **existen** (ver E-6 / AC-22). Una feature que no toca ningún eje no
rebota: registra los diez como `n/a` con razón, que es una decisión legítima y barata.

---

## El catálogo de ejes: el universo a escanear

**Éste es el universo, y son diez**: fijo, no "los ejes que alguien se acordó de mencionar". La
ausencia de un eje del catálogo en el registro es un defecto detectable, distinta de un eje
registrado como `n/a`. Nueve salen de la medición y del pedido; el décimo (legalidad) se agregó en
la ronda de enmiendas y tiene su propia sección abajo.

### Primera clase — bloquean el arranque (los tres irreversibles, ya doctrinales)

| # | Eje | Fuente del default | Se puede asumir sin preguntar |
|---|---|---|---|
| 1 | **Modelo/motor de datos** (relacional / documental / KV / grafo / vectorial) | tabla `Data store` del baseline que matchee | **No** — `orchestrator.md:590-592` lo prohíbe explícitamente |
| 2 | **Plataforma de deploy** (inicial **y** el umbral al escalar) | tabla `Deploy` del baseline | **No** — misma línea |
| 3 | **API Gateway / punto de entrada** | tabla `API Gateway` del baseline | **No** — misma línea |

Para estos tres, *"existe un default seguro"* **no** excusa la pregunta: la doctrina vigente dice
que el usuario es el ingeniero responsable y se queda en el loop por diseño
(`orchestrator.md:590-592`). Esta spec **no relaja** esa regla; la hace más barata de cumplir dándole
al orquestador el default y el umbral en la mano.

### Segunda clase — se asumen, se declaran, y se preguntan sólo si el bit cambia el primer slice

| # | Eje | Postura por defecto y su fuente | Umbral que la cambia |
|---|---|---|---|
| 4 | **Audiencia / quién lo usa** | Sin fuente en el repo — **sin verificar**, lo debe fijar A2 | Interno vs. público cambia auth, rate-limit y superficie |
| 5 | **Embeddings / búsqueda semántica** | pgvector sobre el Postgres existente antes que motor dedicado (`system-design-decisions/SKILL.md:92-98`) | *"once the extension's scale/latency genuinely falls short"* (`:97-98`) |
| 6 | **Tiempo real** | Request/response síncrono (`system-design-decisions/SKILL.md:29-30`) | Cola sólo con *"traffic spikes to absorb, or long/slow work"* (`:38`) |
| 7 | **Superficie mobile** | Sin fuente en el repo — **sin verificar**, lo debe fijar A2 | App nativa cambia el contrato de API y el ciclo de release |
| 8 | **Autenticación / autorización** | Proveedor gestionado, roles simples, *"nunca auth artesanal"* (`gestion-dashboard.md:11-12`); authN y authZ como dos pilares día uno (`system-design-decisions/SKILL.md:116-119`) | Multi-tenant, SSO empresarial u object-level ACL |
| 9 | **Costo / modelo de gasto** | Sólo existe como umbral de deploy: *"costo PaaS > VPS×2 sostenido 3 meses"* (`gestion-dashboard.md:21`) | Presupuesto declarado por el cliente |

### Eje 10 — Legalidad y términos de uso *(E-12, nuevo)*

| # | Eje | Postura por defecto y su fuente | Umbral que la cambia |
|---|---|---|---|
| 10 | **Legalidad del dato: ToS, robots, anti-bot, rate limits, datos personales** | *"respetar robots/ToS del cliente, backoff con jitter, User-Agent honesto"* (`scraping-datos-ml.md:34`) | Cualquier adquisición de datos de terceros, o datos personales / requisito regulatorio (`gestion-dashboard.md:21`, *"Requisito de datos on-premise/regulatorio"*) |

**Por qué entra, y por qué no es un capricho.** Para el ejemplo exacto que dio Federico —scrapear
Mercado Libre— el eje más consecuente de la vida real no es la base de datos: es si se puede.
Y **el repo ya lo sabe**: `scraping-datos-ml.md:34-35` cierra con
*"riesgo legal es decisión del CLIENTE (Question policy), no del implementador"*. O sea, la doctrina
vigente **ya lo enruta a la Question policy** — está archivado como *riesgo* y clasificado como
*decisión del cliente* al mismo tiempo. Sumarlo al catálogo no inventa nada: **conecta una decisión
que el repo ya declaró del cliente y que ningún mecanismo le pregunta nunca.** Es la tesis entera de
esta feature aplicada al caso que la originó.

**Clase**: primera clase **condicional**. Bloquea el arranque —se pregunta aunque haya default—
cuando el pedido involucra (a) adquisición de datos de un tercero, o (b) datos personales /
requisito regulatorio. Fuera de esos dos casos se registra `n/a` con razón. No es irreversible como
los tres primeros; es **inexcusable**: un harness que planifica un scraper y nunca pregunta si es
legal tiene un problema de producto, no de ingeniería.

**Lo que este eje NO hace**: no emite un juicio legal. El harness no dictamina si scrapear Mercado
Libre es legal —no tiene fuente para eso y afirmarlo sería exactamente lo que ADR-0026 prohíbe—.
Pregunta quién asume la decisión y con qué límites operativos (rate limit, User-Agent, robots), y
registra la respuesta. La diferencia entre *"esto es legal"* y *"el cliente decidió asumirlo, con
estos límites"* es la diferencia entre inventar y registrar.

---

**Nótese qué NO hace este catálogo**: no trae un solo número que no esté citado. Los ejes 4 y 7 van
marcados **sin verificar** a propósito — hoy el repo no tiene una postura escrita para audiencia ni
para mobile, y **inventarla en esta spec sería exactamente el defecto que la feature trata**.
Cerrarlos con fuente es trabajo del paquete A2, y si A2 no encuentra base, esos dos ejes se preguntan
abiertos y marcados. **Esa marca se defiende en review contra la presión de A2 por llenar celdas.**

### Orden de prioridad del bloque de preguntas *(E-8)*

El defecto que corrige: con el tope de 5 y dos ejes `sin default`, el bloque quedaba
**determinístico** —3 de primera clase + audiencia + mobile = 5, tope agotado— y **embeddings no se
preguntaba nunca**. La spec presentaba como modelo de buena pregunta una pregunta que su propio tope
permitía no hacer jamás. Es el eje que Federico nombró segundo.

La corrección es de principio, no de número: **el tope acota lo que el harness AGREGA, no lo que el
pedido TRAE.** Una pregunta sobre un eje que el usuario mismo puso arriba de la mesa no es
burocracia — es escucharlo. El orden queda escrito:

1. **Los tres ejes de primera clase.** Siempre, salvo carve-out de plataforma nombrada (AC-04.2).
2. **El eje 10**, cuando dispara su condición.
3. **Todo eje tocado por evidencia en el pedido** —el mismo criterio de
   `request-triage/SKILL.md:130-131`—, en el orden en que el pedido los nombra. *"qué vamos a usar
   de embedding"* es evidencia de eje 5; *"app mobile"* lo es de eje 7; *"tiempo real"*, de eje 6.
4. **Ejes sin default verificado** (hoy 4 y 7), si quedan cupos.
5. **El resto**: `assumed`, declarado en el mismo bloque con su umbral.

Con el ejemplo de Federico, el bloque sale así: data store, deploy, gateway, legalidad, embeddings
(él lo nombró), audiencia (él lo nombró) = **6 preguntas**. Tiempo real, mobile, auth y costo se
asumen y se declaran. La pregunta canónica de la spec —la de pgvector— **se hace**.

**Techo duro: 7.** Si los ejes que pasan por los filtros 1-3 superan 7, eso **no** es motivo para
preguntar más: es la señal de que el pedido es un proyecto entero y el modo correcto es `feature`
con un pase `architect`, no un interrogatorio más largo. Esa escalada es el resultado registrado, y
es una salida que el harness ya sabe tomar (`request-triage/SKILL.md:43-60`).

---

## Paquetes

### A1 — `ejes-al-momento-de-hablar`

Conecta lo que existe (Y-1, Y-2) al primer turno (D-1, D-2). Doctrina, en los cuatro runtimes.

- **AC-01** — `request-triage/SKILL.md` incorpora, en el paso 0 de intake, la carga de
  `solution-baselines`: clasificar el pedido en una categoría y leer **sólo** el archivo de
  `references/` que matchee. Respeta ADR-0020: es **un** archivo de ~36 líneas, dentro del umbral de
  lectura directa 1-3 (`orchestrator.md:29-32`). Declarar *"ninguna baseline aplica"* es una salida
  legítima y explícita, con una línea de por qué.
- **AC-02** — El frontmatter `enabled_for` de `solution-baselines/SKILL.md:6` suma `orchestrator`.
  Sabemos que `enabled_for` **no se ejecuta** (D-2), así que la corrección es doble: el frontmatter
  declara la intención **y** `orchestrator.md` nombra el skill en prosa, que es el mecanismo real.
  Un AC que sólo tocara el frontmatter sería una falsa-verde.
- **AC-03** — El **Contrato de la Pregunta Analítica** queda escrito con sus cuatro partes y su
  cláusula ADR-0026, en `request-triage/SKILL.md` y espejado en la Question policy de
  `orchestrator.md`. Incluye la forma canónica ❌/✅ de esta spec como ejemplo literal.
- **AC-04** — La precedencia queda escrita, no inferida:
  1. **ADR-0037 gana siempre**: un eje resuelto por cualquiera de las cuatro fuentes se registra con
     su origen, nunca se pregunta.
  2. **Los tres ejes de primera clase se preguntan aunque haya default** (`orchestrator.md:590-592`
     intacto). El default sirve para dar forma a la pregunta, no para saltearla.
     **Excepción única, ya vigente: el carve-out de plataforma nombrada** (`orchestrator.md:594-598`,
     ADR-0025.2) — *"when the request itself names the platform ('deploy this to Vercel', 'put it on
     Supabase'), that IS the user's decision on that axis"*. Ese eje se registra con
     `origin: request` y su `source`, y **no se pregunta**. *(E-10: escribir AC-04.2 en absoluto
     producía una contradicción con una línea que vive cuatro renglones más abajo en el mismo
     archivo. El carve-out no es una excepción suelta: es el caso (1) de ADR-0037.)*
  3. **Los de segunda clase se asumen y se declaran**, salvo que caigan en los filtros 2 y 3 del
     orden de prioridad.
  4. **Todas las preguntas del intake salen en UN bloque consolidado**, como ya exige
     `orchestrator.md:604`.
- **AC-05** *(reescrito por E-8)* — El presupuesto de preguntas acota **lo que el harness agrega**,
  no lo que el pedido trae. Queda escrito el orden de prioridad de la sección homónima (primera
  clase → eje 10 si dispara → tocados por evidencia → sin default verificado → resto `assumed`), con
  **techo duro de 7** en un bloque. Superar 7 después de los filtros 1-3 **no autoriza preguntar
  más**: obliga a escalar a modo `feature` con pase `architect`
  (`request-triage/SKILL.md:43-60`) y registrar esa escalada.
  Prueba de que el AC no volvió a la trampa anterior: **con el pedido literal de Federico, el eje 5
  (embeddings) tiene que quedar entre las preguntas emitidas.** Un diseño donde no queda reprueba.
- **AC-06** — El intake **no gasta spawns**. Es trabajo propio del orquestador sobre 1 archivo de
  baseline. En modo `feature` puede delegar un pase `architect` read-only, contabilizado en el
  presupuesto del modo (`request-triage/SKILL.md:104-114`). En `scoped` no delega.
- **AC-07** — La doctrina llega a los **cuatro** runtimes. Prueba sobre el árbol generado
  (`Global/{claude-code,codex,pi,opencode}/`), no sobre `_canonical` solamente — el defecto D-6 de
  la 028 (`docs/specs/028-narracion-que-ensena/spec.md:167`) fue exactamente una doctrina que quedó
  en tres de cuatro.

**owned_paths**: `Global/_canonical/skills/request-triage/SKILL.md`,
`Global/_canonical/skills/solution-baselines/SKILL.md` *(frontmatter, por AC-02)*,
`Global/_canonical/agents/orchestrator.md`, `Global/{claude-code,codex,pi,opencode}/`,
`tests/test_intake_doctrina.py` (nuevo), `docs/adr`.

> **Solape declarado con 028/N2**, que también reclama `Global/_canonical/agents/orchestrator.md` y
> los cuatro árboles (`docs/specs/028-narracion-que-ensena/spec.md:433-435`). Las regiones son
> disjuntas: 028/N2 toca el **bloque de cierre de narración**; 029/A1 toca **Intake** y **Question
> policy**. Se declara en vez de disimularse, igual que 028 declaró su solape N1×N3a
> (`spec.md:410-412`).

### A2 — `el-default-trae-su-umbral`

Cierra D-4: el catálogo de diez ejes queda completo y **con fuente**, o marcado.

**Decisión sobre E-7, tomada y argumentada.** La ronda anterior pedía 4 tablas × 9 filas = 36
celdas. Medido: 8 no tienen fuente y ~16 sólo podrían citar una línea genérica o de otra categoría.
Llenarlas sin inventar obliga a escribir la misma postura cuatro veces — **y eso vacía el valor de
una baseline, que existe precisamente porque su postura es *por categoría***
(`solution-baselines/SKILL.md:12-16`: *"Deriving every architecture from first principles costs
tokens and produces inconsistent systems"*). Peor: cuadruplica la superficie de mantenimiento y
agrava R-6 por cuatro. **Acepto la recomendación del challenger**: sólo van a la tabla por categoría
los ejes **diferenciables y con fuente**; los transversales viven **una sola vez**.

- **AC-08** *(reescrito)* — Las tablas de `references/` suman **sólo** los ejes cuya postura difiere
  entre categorías **y** tiene fuente. Medido hoy, el que califica es **embeddings** (eje 5): tres
  de las cuatro categorías ya traen un umbral vectorial distinto —`scraping-datos-ml.md:19`
  (texto scrapeado → pgvector), `gestion-dashboard.md:19` (*"búsqueda semántica pedida
  explícitamente"*), `ecommerce-landing.md:22` (*"personalización/recomendaciones"*)— y
  `api-b2b-integraciones.md` no lo menciona: esa cuarta celda se escribe o se marca
  `sin fuente — abierto`. **Un eje que terminara con la misma postura en las cuatro categorías es,
  por definición, transversal y no va acá.**
- **AC-08b** *(nuevo, E-7)* — Los ejes transversales (audiencia, tiempo real, mobile, auth, costo,
  legalidad) viven **una vez** en una tabla `Defaults transversales` dentro de
  `solution-baselines/SKILL.md`, con la misma estructura postura/umbral/fuente. Prueba: ninguna
  postura transversal aparece duplicada en dos archivos de `references/`.
- **AC-09** *(intacto, y se defiende en review)* — Los ejes 4 (audiencia) y 7 (mobile) se resuelven
  de una de dos maneras, ambas aceptables, **ninguna inventada**: (a) postura con fuente
  verificable, o (b) `sin default`, y pasan a preguntarse abiertos. **Rellenarlos con una postura
  plausible sin fuente reprueba el AC**, y el reviewer tiene mandato explícito de rechazar la
  celda plausible-sin-fuente aunque suene sensata. Es el AC que encarna el *"no quiero que invente"*.
- **AC-10** — La distinción primera/segunda clase —y la condicionalidad del eje 10— queda escrita en
  `solution-baselines/SKILL.md`, no sólo en esta spec: qué eje bloquea el arranque y cuál se asume.
- **AC-10b** *(nuevo, E-10)* — La `description` del frontmatter de `solution-baselines/SKILL.md:3`
  promete hoy *"the three architecture axes already taken with explicit YAGNI thresholds"*. Al pasar
  a diez, esa promesa queda **falsa** — y la `description` es lo que el runtime muestra para decidir
  si carga el skill. Se actualiza en el mismo paquete. Un skill que se describe mal se carga mal.
- **AC-11** — `system-design-decisions/SKILL.md:6` suma `orchestrator` a `enabled_for`, y la
  doctrina dice cuándo se carga: **sólo** cuando ninguna baseline matchea, o cuando un eje cruza su
  umbral. Cargar las 152 líneas en cada intake es el costo que los baselines existen para evitar
  (`solution-baselines/SKILL.md:11-16`).

**owned_paths**: `Global/_canonical/skills/solution-baselines/` *(SKILL.md + los 4 `references/`)*,
`Global/_canonical/skills/system-design-decisions/SKILL.md`, sus espejos en
`Global/{claude-code,codex,pi,opencode}/skills/`, `tests/test_intake_baselines.py` (nuevo).

> **Solape con A1** en `solution-baselines/SKILL.md`: A1 toca el frontmatter `enabled_for` (AC-02),
> A2 toca la `description` (AC-10b) y el cuerpo (AC-08b). Secuenciales, regiones disjuntas dentro
> del mismo archivo. Si el planner prefiere, A1 cede el frontmatter entero a A2 — es una decisión de
> planificación, no de producto.

### A3 — `una-decision-que-queda-escrita`

Cierra D-3 y D-5: el intake deja rastro de máquina.

**Decisión sobre E-4: almacén propio, `log-decision` intacto.** El defecto es de código y está
verificado: `cli_reporting.py:92-99` deduplica por `(slug, title, decision)` y **`feature_id` no
está en la clave**; si hay duplicado devuelve la entrada vieja y no escribe. Con diez ejes por
feature y `n/a` como stance mayoritario, dos features que registran *"mobile — no aplica"* colisionan
por texto: la segunda recibe `deduped: true`, no obtiene fila, e `init` la rechaza por eje faltante.
**Un rechazo que el usuario no puede corregir repitiendo el comando, porque el comando dice que
funcionó.** Es el caso esperado, no el borde.

De las dos salidas —meter `feature_id`+`axis` en la clave, o almacén propio— **tomo la segunda**,
por tres razones acumulativas: (1) no toca la semántica de idempotencia de un CLI con 130 entradas
vivas; (2) resuelve solo el ruido en el digest y en `docs/notas/decisiones/` (E-5); (3) deja a 029 y
028 sin disputa sobre `cmd_log_decision`.

- **AC-12** *(reescrito)* — Nace `ai/state/axes-log.jsonl`, JSONL propio, y su subcomando de
  escritura. `log-decision` y `decisions-log.jsonl` **no se tocan**. Campos:

  | Campo | Obligatorio | Qué es |
  |---|---|---|
  | `feature_id` | sí | y **entra en la clave de identidad**, junto con `axis` |
  | `axis` | sí | uno de los **10** del catálogo, valor cerrado |
  | `stance` | sí | qué se decidió |
  | `origin` | sí | `request \| notas \| decisions-log \| adr \| user \| assumed \| n/a` |
  | `source` | según origen | `archivo:línea` **resoluble**, o el turno del usuario |
  | `threshold` | según origen | qué invalidaría la postura — **el "cuándo"** |
  | `next_stance` | según origen | **adónde se va cuando el umbral se cruza — el "adónde"** *(E-11)* |
  | `revisit` | según origen | qué señal obliga a revisarlo |
  | `reason` | si `origin: n/a` | por qué no aplica *(E-1.4: AC-14 exigía una razón que no tenía dónde vivir)* |
  | `asked_at` | ver AC-25 | timestamp de la pregunta emitida |

- **AC-12b** *(nuevo, E-11)* — `next_stance` existe porque el pedido dice *"dónde va a estar
  alojada inicialmente **y cuándo escale**"*. `threshold` cubre el **cuándo**; sin `next_stance` el
  **adónde** se pierde. Para deploy en la baseline de gestión, la fila completa es:
  `stance: PaaS` · `threshold: costo PaaS > VPS×2 sostenido 3 meses` (`gestion-dashboard.md:21`) ·
  `next_stance: VPS/IaaS`. Obligatorio en los mismos casos que `threshold`.
- **AC-12c** *(nuevo, E-4)* — **Regla de reescritura, escrita.** El log es append-only; la identidad
  de una fila es `(feature_id, axis)`. Registrar dos veces el mismo eje **es legal y esperado** (el
  usuario contesta después de un `assumed`): se anexa una fila nueva y **gana la última por
  timestamp**. Toda superficie que lea el log —la guarda de A4, el render— aplica la misma regla, y
  la fila superada queda visible como historia. *"Gana el último" hoy no está escrito en ningún
  lado; acá lo está.*
- **AC-13** *(ampliado)* — `origin: assumed` exige `threshold`, `next_stance` y `revisit`, los tres
  con contenido real según AC-18. Un default asumido sin el umbral que lo desarma es indistinguible
  de una decisión inventada, que es lo que Federico prohibió.
- **AC-14** *(corregido)* — `origin: n/a` exige `reason` (el campo de AC-12), y **no** exige
  `threshold`/`next_stance`. **La ausencia de un eje del catálogo no es `n/a`**: `n/a` es una
  decisión tomada, la ausencia es un eje nunca mirado, y A4 los trata distinto.
- **AC-15** — El registro se ve donde el humano lee: los ejes de la feature aparecen como tabla en
  `docs/notas/`, y para un proyecto scaffoldeado en `docs/project/architecture.md` — que deja de
  entregarse como `TODO:` de tres líneas (D-5, `bootstrap_project.py:27`) y pasa a traer la tabla de
  ejes vacía con sus **diez** filas nombradas.
- **AC-15b** *(nuevo, E-10 — regresión de template)* — `bootstrap_project.py:95-99` es
  create-if-missing **y**, si el archivo existe con contenido distinto, lo apila en `conflicts`.
  Cambiar el template de `docs/project/architecture.md` (AC-15) hace que **todo proyecto ya
  scaffoldeado reporte un conflicto** en el próximo bootstrap. El paquete se hace cargo: o el
  cambio es aditivo sin disparar conflicto, o el conflicto se reporta con un mensaje que explique
  que es la tabla de ejes nueva y no una colisión real. Test que lo pinche.
- **AC-16** — El registro es **anterior** a `init`, con `feature_id` seteado. Hoy la capacidad
  existe (`log-decision --feature-id`, `feature-state.py:1133`) y no se usa: 18 de 24 features
  tienen cero registros pre-`init` (D-3).
- **AC-16b** *(nuevo, E-5 — no ensuciar la cura de 028)* — El digest filtra decisiones **sólo por
  ventana temporal**: `cli_reporting.py:297-301`, `[e for e in _read(...) if e.get("at","") >= since]`,
  sin ningún filtro de tipo. Y `docs/notas/decisiones/` rinde **un archivo por entrada** (medido:
  130 entradas, 130 archivos). Diez ejes por feature meterían ~10 entradas de bajo contenido en la
  sección *"Decisiones nuevas"* de `BUENOS-DIAS.md` — **la superficie exacta que 028/AC-13 existe
  para volver legible**. Con el JSONL propio (AC-12) esto se resuelve por construcción: los ejes
  **no** entran a `decisions-log.jsonl`. El AC exige la prueba: tras registrar diez ejes, el digest
  no gana ninguna línea en *"Decisiones nuevas"*, y los ejes se ven en su propia sección o tabla.

**owned_paths**: `ai/scripts/feature-state.py` **y `PROYECTO/ai/scripts/feature-state.py`**,
`ai/scripts/feature_state_lib/` *(módulo de ejes nuevo + render)* y su espejo bajo `PROYECTO/`,
`ai/scripts/bootstrap_project.py` *(por AC-15/AC-15b)*, `tests/test_intake_ejes.py` (nuevo),
`docs/adr`.

> **El espejo no es opcional y hay que nombrarlo (E-5).** `tests/test_harness.py:30` define
> `FEATURE_STATE = ROOT / "PROYECTO/ai/scripts/feature-state.py"`: **la suite ejerce el espejo, no
> el original**. Implementar sólo en `ai/scripts/` da la suite en verde y deja el repo real sin
> guarda; implementar sólo en `PROYECTO/` deja verde la suite y sin guarda al harness. Los dos, o
> ninguno. Es la trampa perfecta y queda escrita.
>
> **Solape declarado con 028/N1**, que reclama `ai/scripts/feature-state.py`, su espejo y
> `cli_reporting.py` (`docs/specs/028-narracion-que-ensena/spec.md:404-407`). Regiones disjuntas:
> 028/N1 vive en `cmd_log_narrative`/`cmd_log_quickfix` y el filtro de `started`; 029/A3 vive en el
> subcomando de ejes y su módulo nuevo. **029/A3 no toca `cmd_log_decision`** — ésa fue la razón
> principal para elegir el almacén propio.

### A4 — `no-se-arranca-con-ejes-abiertos`

La guarda. Sin esto, en dos features la regla se evaporó.

> **La lección de método, anotada donde se va a leer (E-1.5).** La versión anterior de AC-18
> enumeraba **tres** modos de falla y dejaba **cinco** puertas abiertas — el challenger las escribió
> todas en una pasada. Y como AC-19 exige *"un test por cada modo de falla de AC-18"*, **la
> enumeración de AC-18 ES el techo real de la guarda**: lo que no está enumerado no se prueba, y lo
> que no se prueba no muerde. Regla para este paquete y para los que vengan: **los modos de falla se
> enumeran DESPUÉS de intentar burlar la regla, nunca antes.** Quien implemente A4 tiene mandato de
> intentar pasarla y agregar lo que encuentre; encontrar una sexta puerta es entregable, no
> hallazgo.

- **AC-17** — `feature-state.py init` **rechaza** si el universo de ejes no está completo para ese
  `feature_id`: los **10** ejes del catálogo deben tener fila vigente (AC-12c), cada uno con
  `origin` válido. Misma jugada que `--approved-by` (`feature-state.py:806-808`), citada como
  precedente en el código.

- **AC-18** *(reescrito por E-1: de tres bullets a matriz origen × obligación)* — **La parte que
  decide si esta feature sirve.** El rechazo no se satisface con presencia:

  | `origin` | `source` | `threshold` + `next_stance` + `revisit` | `reason` | `asked_at` |
  |---|---|---|---|---|
  | `request` | **resoluble** o cita del turno | recomendado | — | — |
  | `notas` / `decisions-log` / `adr` | **resoluble** (ver V-1) | recomendado | — | — |
  | `user` | cita del turno | recomendado | — | **sí, si el eje es de primera clase** |
  | `assumed` | **resoluble** (de dónde sale el default) | **obligatorios** | — | **sí, si es de primera clase** |
  | `n/a` | — | — | **obligatorio** | **sí, si es de primera clase** |

  Y **cinco reglas de contenido** (`V-n`, de *validación* — no confundir con los riesgos `R-n`),
  todas nuevas salvo la primera:

  - **V-1 — `source` resoluble, no parseable.** Un regex `\S+:\d+` acepta
    `docs/adr/0058-convenciones-antes-del-codigo.md:41` — **un ADR que no existe, que reserva esta
    misma spec** — y acepta `foo.md:1`, y la línea 9999 de un archivo de 36. La validación es:
    **el archivo existe**, **la línea está dentro del rango** (`len(readlines())`), y para
    `origin: adr` **el ADR está indexado en `docs/adr/README.md`** (que ya declara
    *"One row per ADR, no exceptions"*, `README.md:3`). Son tres llamadas a `os.path` y un conteo de
    líneas. Si el `source` es un turno del usuario en vez de un archivo, se marca como tal y no
    pretende ser una ruta.
  - **V-2 — anti-relleno en `stance`, `threshold`, `next_stance`, `revisit` y `reason`**, no sólo en
    `stance`: vacío, igual al nombre del eje, o por debajo del largo mínimo → rechazo. Más
    **denylist explícita**: `n/a`, `na`, `ninguno`, `-`, `--`, `tbd`, `todo`, `por definir`,
    `a definir`, `cuando haga falta`, `ver después`, `ok`. *(La versión anterior pedía sólo
    "`threshold` no vacío", y `--threshold "n/a"` pasaba.)*
  - **V-3 — no repetición entre ejes.** El mismo `stance` en los diez ejes es relleno, no decisión.
    **Se implementa con el MISMO módulo de lint que 028**, no con un criterio paralelo: 028/N1
    declara `ai/scripts/narration_lint.py` como archivo nuevo en sus `owned_paths`
    (`docs/specs/028-narracion-que-ensena/spec.md:404`) y 028/AC-05b ya reemplazó su regla del 70%
    por una de **contención** (*"`why` no puede contener a `next` como subcadena ni al revés"*,
    `spec.md:375-379`). A4 importa ese predicado y lo aplica entre ejes. **Dos linters anti-relleno
    con criterios distintos en el mismo repo es exactamente la incoherencia que 028 acaba de
    corregir.** Ver la nota de acoplamiento abajo.
  - **V-4 — `origin: n/a` tiene reglas propias**, ya no es una puerta libre: exige `reason` que pase
    V-2, y el `reason` no puede ser idéntico entre ejes (V-3 aplica). *(La versión anterior no le
    ponía ninguna regla: diez `n/a` sin nada más pasaban.)*
  - **V-5 — `asked_at`**: ver AC-25.

- **AC-19** *(ampliado)* — La prueba **muerde en las dos direcciones**, y es condición de aceptación
  del paquete: un test con los 10 ejes correctos donde `init` **pasa**; y **un test por cada modo de
  falla enumerado en AC-18** —las cinco reglas `V-n`, con sus sub-casos: ADR inexistente, línea fuera de
  rango, ADR no indexado, `threshold: "n/a"`, stance repetido, `n/a` sin `reason`, `user` sin
  `asked_at`, log ausente (AC-23)— donde `init` **falla con exit≠0**. Un test que sólo prueba el
  camino feliz sería la **duodécima** guarda falsa-verde de este repo y se rechaza en review.
- **AC-20** — El mensaje de rechazo **es él mismo un ejemplo de la doctrina** (patrón tomado de
  028/AC-06, `spec.md:250`): nombra **qué eje** falta o qué regla falló, **cuál es el default de la
  baseline que matchea con su archivo:línea**, y **el comando exacto** para registrarlo. Un rechazo
  que dice "faltan ejes" obliga a leer la spec; uno que trae el default hace el trabajo — y es lo
  que mantiene barato el camino honesto frente al relleno (mitigación de R-4).
- **AC-21** — La guarda **no rompe lo que ya pasó**. Las 24 features existentes tienen su archivo de
  estado creado y no se re-inician: la validación corre en `init`, no en `validate` ni en
  `transition`. Un `init --force` sobre una feature vieja sí la exige — es un arranque nuevo.

- **AC-22** *(reescrito por E-6: la afirmación anterior era falsa)* — **El hecho, verificado**:
  `feature-state.py:819` es `init.add_argument("--mode", choices=sorted(MODE_BUDGETS), default="scoped")`
  y `MODE_BUDGETS` (`feature_state_lib/model.py:106-111`) contiene `quick-fix` **e** `incident`. Hay
  test vigente que hace `init_state(state, "--ac", "AC-1", "--mode", "quick-fix")`
  (`tests/test_harness.py:8712`, y otra vez en `:8730`). **Decir *"un quick-fix no pasa por `init`,
  por construcción"* era falso.** Lo que es cierto es que `log-quickfix` (`feature-state.py:1108`)
  no crea estado y no pasa por `init`. Las dos vías coexisten. Decisiones explícitas:
  - **`log-quickfix`**: exento. No hay `init`, no hay ejes. Por construcción, ahora sí.
  - **`init --mode quick-fix`**: **exige los ejes.** Quien crea archivo de estado está abriendo una
    feature, cualquiera sea la etiqueta de presupuesto. Con seis a ocho filas `n/a`/`assumed` y el
    mensaje de AC-20 dando el default, el costo es de un minuto.
  - **`init --mode incident`**: **exento en el momento, obligatorio en el follow-up.** Producción
    caída, *"speed matters more than ceremony"* (`request-triage/SKILL.md:90-96`); bloquear el
    break-glass detrás de diez registros es **literalmente el escenario de R-5** — la guarda que
    molesta en el peor momento es la guarda que alguien desactiva. La exención se paga: el modo ya
    obliga a *"(b) open a follow-up task to do it properly"* (`SKILL.md:95`), y el registro de ejes
    entra en ese follow-up. La exención queda **escrita en el estado** —no es un silencio— y es
    visible en la superficie que Federico lee.

- **AC-23** *(nuevo, E-3 — la guarda tiene que saber de dónde leer, y los dos atajos son trampas)* —
  Hecho verificado: `init` recibe `--state-file` y `log-decision` resuelve su log en
  `Path("ai/state")` **relativo al CWD** (`cli_reporting.py:90`); **ninguna convención los liga**.
  Y hay **46 sedes** de `init` en la suite con `--state-file` en un tmpdir sin log alguno: 38 vía el
  helper `init_state` (`tests/test_harness.py:278-289`) más 8 invocaciones directas
  (`test_integration_hook.py:110,171`, `test_module_docs.py:53,349`, `test_rdd_schema.py:148,282`,
  `test_repair_ceiling.py:57`, `test_living_scope.py:32`). Bajo AC-17 **las 46 fallan**. Las dos
  reparaciones baratas quedan **prohibidas por escrito**:
  - ❌ *"si el log no existe, no chequeo"* → **fail-open**, y el caso sin log es precisamente un
    proyecto recién scaffoldeado, que es donde la feature más importa. Sería la guarda falsa-verde
    número doce, escrita a propósito.
  - ❌ derivar `state.parent.parent / axes-log.jsonl` → con un state file en `/tmp/xxx/` eso apunta a
    **`/tmp/axes-log.jsonl`**, compartido entre tests y sesiones. Rompe exactamente el aislamiento
    que ADR-0051 acaba de reparar (`docs/adr/0051-owned-paths-sees-untracked-files-and-test-isolation.md`).

  La regla: **`--axes-log` explícito** en `init`, con derivación escrita y determinista cuando no se
  pasa (junto al `--state-file` si lo hay; si no, `ai/state/` relativo a la raíz del proyecto — nunca
  a `/tmp`, nunca al CWD del test). **Log ausente ⇒ rechazo**, con el mensaje de AC-20. Test que
  pinche las dos trampas: uno que verifique que el log ausente falla, y uno que verifique que dos
  state files en tmpdirs distintos **no comparten** log.
- **AC-24** *(nuevo, E-3)* — Las 46 sedes se hacen cargo en este paquete, no en el siguiente: el
  helper `init_state` y las 8 invocaciones directas pasan un log de ejes de prueba, o el paquete
  declara y prueba el modo de test. `tests/test_harness.py`, `tests/test_integration_hook.py`,
  `tests/test_module_docs.py`, `tests/test_rdd_schema.py`, `tests/test_repair_ceiling.py` y
  `tests/test_living_scope.py` entran a los `owned_paths` de A4. **Una feature que rompe 46 tests y
  no lo dice en la spec es una feature que va a terminar aflojando la guarda a las tres de la
  mañana.**

- **AC-25** *(nuevo, E-2 — `origin: user` era el camino más barato y nada podía desmentirlo)* —
  El escenario es peor que el que temíamos: no hace falta marcar los diez como `assumed`; alcanza
  con marcarlos `user`, que en la versión anterior **no exigía ni fuente resoluble ni umbral**. Diez
  líneas de trámite, cero preguntas, `init` en verde, y **más barato que el camino honesto**.
  Verificado que nada puede desmentirlo: `ai/state/narrative-log.jsonl` tiene exactamente las claves
  `actor, at, client, feature_id, package_id, result, role, tech` (178 entradas) — **ningún campo
  registra una pregunta emitida**. Hoy **no existe ningún artefacto de máquina que distinga "se
  preguntó" de "se dijo que se preguntó"**, así que AC-04.2 —la regla que esta spec declara que
  nunca se relaja— era justamente la única que su guarda no podía verificar.

  La regla: para los ejes de **primera clase** (1, 2, 3, y el 10 cuando dispara), un `origin` ∈
  `{user, assumed, n/a}` exige **`asked_at`**: un timestamp que se corresponda con una entrada real
  de `narrative-log.jsonl` con ese `feature_id`, dentro de una ventana de tolerancia. Sigue siendo
  auto-aseverado —no hay forma de probar que el texto contenía la pregunta— pero **obliga a que la
  pregunta exista en la superficie que Federico lee**, que es el único proxy mecánico disponible
  hoy. Un intake que no narró nada no puede afirmar que preguntó.

  **Y esto invalida una afirmación del encabezado de la ronda anterior**: dije que 029 y 028 no
  tenían punto de acoplamiento. Lo tienen, y es éste. Queda declarado arriba y en la nota de abajo.

**owned_paths**: `ai/scripts/feature-state.py` **y `PROYECTO/ai/scripts/feature-state.py`**,
`ai/scripts/feature_state_lib/` *(validador de ejes)* y su espejo, `ai/scripts/narration_lint.py`
*(por V-3)*, `tests/test_intake_guarda.py` (nuevo), y los seis módulos de test de AC-24.

> **Acoplamiento con 028, declarado (E-5 + V-3 + AC-25).** Tres puntos de contacto reales:
> (a) el predicado anti-relleno vive **una vez** (`narration_lint.py`, que 028/N1 declara como
> archivo nuevo); (b) `asked_at` lee `narrative-log.jsonl`, cuya forma 028 está cambiando
> (028/AC-07 vuelve `--feature-id` obligatorio al cerrar — lo cual **ayuda** a AC-25, porque hoy
> 11 de 178 entradas son `sin-feature`); (c) el espejo `PROYECTO/` y `feature-state.py`.
> **Orden recomendado: 028/N1 antes que 029/A4.** Si 029/A4 llega primero, crea el módulo de lint
> con los primitivos compartidos y 028/N1 los importa. Lo que **no** es aceptable es que cada
> feature escriba su propio anti-relleno. Esto degrada la "Precondición: ninguna" del encabezado a
> **acoplamiento blando con orden recomendado**, y así queda escrito arriba.

---

## Qué pasa si el usuario no contesta, o dice "elegí vos"

Es el caso más frecuente y el más peligroso, y tiene camino explícito:

1. El harness **elige el default de la baseline que matchea** y lo nombra con su `archivo:línea`.
2. Lo registra con `origin: assumed` y `threshold` + `next_stance` + `revisit` obligatorios
   (AC-13), más `asked_at` si es de primera clase (AC-25).
3. Lo **declara en el mismo turno**, en el registro `Cliente:`, en una línea: qué se asumió, hasta
   dónde aguanta, **adónde se va cuando lo cruce**, y qué señal obliga a revisarlo.
4. **Sigue trabajando.** Nunca queda trabado — eso viola la continuidad de turno
   (`orchestrator.md:613-618`).
5. **Nunca escribe `origin: user` sobre algo que el usuario no dijo.** Un default asumido y un
   default elegido son dos hechos distintos y quedan distinguibles en el log para siempre. Y desde
   AC-25 la diferencia **cuesta**: `user` en un eje de primera clase exige `asked_at`, así que
   marcar `user` ya no es más barato que decir la verdad. Ése era el agujero.

**Precedencia con la Question policy**: para los ejes de primera clase, `assumed` es legal **sólo
después** de haber preguntado —y AC-25 lo vuelve verificable por proxy—. Asumir sin preguntar en
ésos viola `orchestrator.md:590-592` y es un hallazgo de review, no una optimización. **Salvo el
carve-out de plataforma nombrada** (`orchestrator.md:594-598`): ahí el eje no es `assumed`, es
`request`, y no había pregunta que hacer. Para los de segunda clase, `assumed` sin preguntar es el
camino normal y esperado.

---

## Qué es mecánicamente testeable y qué no

### Sí muerde

| Qué | Cómo se prueba |
|---|---|
| Universo completo de **10** ejes antes de `init` | `init` con 9 ejes → exit≠0 (AC-17, AC-19) |
| `stance`/`threshold`/`next_stance`/`revisit`/`reason` vacíos o de relleno | test por cada campo → exit≠0 (AC-18/V-2) |
| Denylist (`n/a`, `tbd`, `por definir`, `ok`…) en cualquier campo de contenido | test por término → exit≠0 (AC-18/V-2) |
| `assumed` sin `threshold` o sin `next_stance` | test → exit≠0 (AC-13, AC-18) |
| **`source` que apunta a un archivo inexistente** | test con `docs/adr/0058-*.md:41` antes de que exista → exit≠0 (AC-18/V-1) |
| **`source` con línea fuera de rango** | test con `:9999` sobre un archivo de 36 líneas → exit≠0 (AC-18/V-1) |
| **`origin: adr` con ADR no indexado en `docs/adr/README.md`** | test → exit≠0 (AC-18/V-1) |
| **Mismo `stance` repetido entre ejes** | test → exit≠0 (AC-18/V-3, vía el lint compartido) |
| **`origin: n/a` sin `reason`, o con `reason` repetido** | test → exit≠0 (AC-18/V-4) |
| **`origin: user` en eje de primera clase sin `asked_at`** | test → exit≠0 (AC-25) |
| **`asked_at` sin entrada correspondiente en `narrative-log.jsonl`** | test → exit≠0 (AC-25) |
| **Log de ejes ausente** | test → exit≠0, **nunca fail-open** (AC-23) |
| **Dos state files en tmpdirs distintos no comparten log** | test de aislamiento, familia ADR-0051 (AC-23) |
| Regla de reescritura: gana la última fila por `(feature_id, axis)` | test con dos filas del mismo eje (AC-12c) |
| El camino feliz sigue pasando | 10 ejes válidos → exit 0 (AC-19) |
| Las 46 sedes de `init` de la suite siguen verdes | la suite entera (AC-24) |
| Doctrina en los 4 runtimes | grep sobre el árbol generado (AC-07) |
| Sólo los ejes diferenciables están en `references/`; los transversales, una vez | parse de las tablas markdown (AC-08, AC-08b) |
| `enabled_for` incluye `orchestrator`, y la `description` no promete "three axes" | parse del frontmatter (AC-02, AC-10b, AC-11) |
| El mensaje de rechazo nombra eje + default + comando | assert sobre stderr (AC-20) |
| Features viejas no se rompen | `validate`/`transition` sobre los 24 JSON existentes (AC-21) |
| `log-quickfix` exento; `init --mode quick-fix` exige; `incident` exento con follow-up | tres tests (AC-22) |
| El digest no gana líneas en "Decisiones nuevas" por registrar ejes | test tras 10 registros (AC-16b) |
| El template de `architecture.md` no dispara conflicto falso en bootstrap | test (AC-15b) |

### No muerde, y hay que decirlo

1. **La calidad de la pregunta no es testeable.** Que una pregunta cumpla el CPA de verdad — que el
   umbral sea el correcto, que el bit sea contestable — lo juzga un humano o un reviewer. Lo
   mecánico llega hasta *"la pregunta menciona un default con su archivo:línea"*, que es forma, no
   fondo. **Control propuesto**: `spec-challenger` suma al chequeo que ya hace (`spec-challenge/
   SKILL.md:16-20`) la lectura del registro de ejes, y reporta como hallazgo un `stance` que
   contradice la baseline sin ADR de deviation.
2. **Que la baseline elegida sea la correcta no es testeable.** Clasificar un pedido en
   `scraping-datos-ml` vs `api-b2b-integraciones` es juicio. Mitigación: la clasificación se
   registra con su razón (AC-01) y queda auditable; equivocarse y quedar escrito es recuperable,
   equivocarse en silencio no.
3. **Que el usuario haya entendido la pregunta no es testeable.** Ningún test distingue un "dale"
   informado de uno de cansancio. Ésta es la razón del techo de 7 en AC-05: el riesgo real no es
   preguntar poco, es preguntar tanto que la respuesta deje de significar algo.
4. **Que el intake haya corrido cuando debía** sólo es verificable **hacia atrás**: si corrió, hay
   registro; si no corrió, `init` rechaza. Pero un pedido que nunca llegó a `init` (un `quick-fix`
   cerrado con `log-quickfix` que debió ser `scoped`) escapa a la guarda por diseño. El único
   control ahí es el red-flag transversal existente (`request-triage/SKILL.md:127-142`), que ya es
   prosa y sigue siéndolo. **Lo declaro como límite conocido, no lo tapo.**
5. **`asked_at` es un proxy, no una prueba** *(E-2)*. Verifica que **existió una narración** en la
   ventana de la pregunta, no que esa narración **contenía la pregunta**. Un agente decidido a
   mentir puede narrar cualquier cosa y poner el timestamp. Lo asumo a conciencia: es el único
   proxy mecánico disponible hoy —`narrative-log.jsonl` no tiene campo de pregunta emitida— y su
   valor real es que **encarece el atajo** hasta ponerlo por encima del camino honesto, que es lo
   único que un incentivo puede hacer. **Control humano propuesto**: el `spec-challenger`, que ya
   lee la spec antes de aprobar, contrasta los ejes de primera clase contra la narración de la
   ventana. Y si algún día se agrega un campo de pregunta al log de narración, AC-25 se endurece
   solo — dejo escrito el punto de mejora en vez de fingir que la guarda es más fuerte de lo que es.
6. **Que el eje 10 sea correcto no es testeable, y no debe serlo.** El harness no dictamina
   legalidad; registra quién la asume y con qué límites. Un test que verificara "la respuesta legal
   es correcta" sería el harness inventando derecho.

---

## No-goals

- **No se toca `cmd_log_narrative`, `record-spawn` ni los renders de narración de 028.** El único
  contacto es de lectura (`asked_at` lee `narrative-log.jsonl`) y el módulo de lint compartido.
- **No se toca `cmd_log_decision` ni `decisions-log.jsonl`** *(E-4)*. Los ejes viven en su propio
  JSONL, y ésa fue una decisión tomada, no una omisión.
- **No se crea un modo nuevo.** El intake vive dentro de los cinco modos existentes.
- **No se relaja `orchestrator.md:590-592`.** Los ejes de primera clase se siguen preguntando, con
  la única excepción que ya era doctrina (carve-out de plataforma nombrada, `:594-598`).
- **No se agregan preguntas al carril `quick-fix`.** Su único control sigue siendo el red-flag.
  *(Distinto de registrar: `init --mode quick-fix` sí registra, ver AC-22.)*
- **No se bloquea el break-glass.** `init --mode incident` queda exento en el momento (AC-22).
- **No se inventan umbrales.** Los ejes 4 y 7 pueden terminar `sin default` y está bien (AC-09).
- **No se emite juicio legal** en el eje 10: se registra quién asume la decisión y con qué límites.
- **No se implementa el `intent artifact` de gentle-ai.** Ver la sección de referencias externas.
- **No se retrofitea el registro de ejes a las 24 features existentes** (AC-21).
- **No se toca `coord_policy.py`.** La guarda vive en `init`, no en la allowlist de comandos.
- **No se agrega un campo de "pregunta emitida" a `narrative-log.jsonl`.** Sería la guarda fuerte
  que AC-25 aproxima, pero es cambio de contrato sobre un log que 028 ya está modificando. Queda
  nombrado como mejora futura, no ejecutado acá.

---

## Riesgos

| # | Riesgo | Mitigación en la spec |
|---|---|---|
| R-1 | **El intake se vuelve un formulario** — el riesgo principal, y el que mataría la feature | CPA obligatorio (AC-03) + techo de 7 con orden de prioridad (AC-05) + ADR-0037 con precedencia (AC-04.1) |
| R-2 | **Los ejes se registran de relleno** para pasar la guarda: diez `stance: "ok"` | AC-18 con matriz + 5 reglas; AC-19 exige un test por cada modo de falla |
| R-3 | **El default inventado**: el orquestador produce un umbral plausible sin fuente | Cláusula ADR-0026 del CPA + AC-09 acepta explícitamente "sin default" + AC-18/V-1 exige `source` **resoluble** |
| R-4 | **Fricción en features chicas**: 10 ejes para un `scoped` de dos archivos | 6-8 son `assumed`/`n/a` sin preguntar; AC-20 trae el default en el mensaje; `log-quickfix` exento |
| R-5 | **La guarda se desactiva** porque molesta (el fracaso clásico, `check-feature-state.py:22-23`: *"a guard that reports violations that are not violations gets disabled"*) | AC-21 la limita a `init`; AC-20 hace útil el rechazo; **AC-22 exime `incident`**, que era el escenario que la habría matado |
| R-6 | **Las tablas de baseline envejecen** y el default citado deja de ser sensato | `solution-baselines/SKILL.md:35-36` ya manda actualizar la referencia; **AC-08 reduce la superficie** de 36 celdas a las diferenciables (E-7), así que hay menos que envejecer |
| R-7 | **A2 se convierte en investigación abierta** buscando fuentes para audiencia y mobile | AC-09 acota: dos salidas, y "sin default" es una de ellas |
| R-8 | *(nuevo, E-3)* **La guarda se afloja para que pasen los 46 tests** | AC-23 prohíbe por escrito los dos atajos (fail-open y `/tmp` compartido); AC-24 pone las 46 sedes dentro del paquete, no como daño colateral |
| R-9 | *(nuevo, E-1)* **La enumeración de modos de falla vuelve a quedar corta** — y es el techo real de la guarda | La regla de método escrita en A4: enumerar **después** de intentar burlarla; encontrar una puerta nueva es entregable |
| R-10 | *(nuevo, E-5)* **Dos linters anti-relleno con criterios distintos** entre 028 y 029 | V-3 de AC-18 obliga al módulo compartido; el orden 028/N1 → 029/A4 queda recomendado |
| R-11 | *(nuevo, E-12)* **El eje legal se vuelve teatro**: se registra "el cliente asume" y nadie lo lee | Es de primera clase condicional: se **pregunta**, no se asume, cuando dispara; y queda en la tabla que el humano lee (AC-15) |

---

## Gates

- `./ai/scripts/verify.sh` verde al cierre de cada paquete, **incluidas las 46 sedes de `init`**
  (AC-24). Una suite verde con la guarda aflojada no cuenta.
- La prueba adversaria de A4 (AC-19) es **condición de aceptación del paquete**, no un extra: sin un
  test por cada modo de falla enumerado en AC-18, el paquete no se acepta.
- `docs/adr/0058-*.md` escrito **e indexado en `docs/adr/README.md`** — y esto no es sólo higiene:
  AC-18/V-1 valida `origin: adr` contra ese índice, así que un ADR sin fila hace fallar la guarda.
- El módulo de lint anti-relleno es **uno solo** en el repo (AC-18/V-3), verificable con un grep.
- Aplicación a sí misma: la feature 029, al llegar a su propio `init`, registra sus **diez** ejes.
  Es de categoría "no aplica baseline" (un CLI de Python sobre archivos), así que se espera mayoría
  de `n/a` con razón — y eso, si AC-20 es bueno, tiene que ser barato. **Si registrar los ejes de
  esta propia feature resulta pesado, el diseño está mal y hay que revisarlo antes de cerrar A4.**
  El eje 10 acá se registra `n/a` con razón: el harness no adquiere datos de terceros.

---

## Criterio de cierre

La feature está lista cuando, sobre un pedido nuevo de tipo *"haceme una página web para scrapear
Mercado Libre"*:

1. El orquestador clasifica en `scraping-datos-ml` y lo dice con su archivo.
2. Sale **un** bloque de a lo sumo 7 preguntas, cada una con default citado, umbral y el bit. Entre
   ellas están, necesariamente: los tres de primera clase, **la legalidad/ToS** (eje 10, que dispara
   porque hay adquisición de datos de un tercero) y **embeddings** (eje 5, porque el pedido lo
   nombra). *(Los dos que la ronda anterior dejaba afuera.)*
3. El usuario contesta, o dice "elegí vos", y en ambos casos el harness sigue en el mismo turno.
4. Los 10 ejes quedan en `ai/state/axes-log.jsonl` y en la tabla de `docs/notas/`, cada uno con
   `origin`, `source` resoluble, y —donde corresponda— `threshold` + `next_stance`. El digest **no**
   gana diez líneas de ruido (AC-16b).
5. `feature-state.py init` acepta. Y si se le borra un eje, o se le pone `threshold: "n/a"`, o se le
   apunta el `source` a un ADR inexistente, **rechaza nombrando qué falló y cuál sería el default**.

---

## Auditoría de la spec

### Qué verifiqué, y con qué

- **`ls docs/adr/`** → último archivo `0052`; reservas de 025 y 028 leídas en sus specs. **0058
  libre.** Verificado.
- **Los cuatro archivos de `solution-baselines/references/`**: leídos completos. Las cuatro tablas de
  tres ejes con umbral **existen**, con las líneas citadas. Verificado.
- **`system-design-decisions/SKILL.md`**: leído completo (152 líneas). Verificado.
- **`request-triage/SKILL.md`**: leído completo (174 líneas). La lista real de lo que pregunta hoy
  es: paso 0 → *"1–2 scoping questions"* sobre alcance/riesgo/intención (`:22-24`), y en modo feature
  → *"what future/scale do you expect? where centralized vs decentralized? what must be secure day
  one?"* más los tres ejes nombrados (`:50-54`). **No hay más preguntas escritas en ningún lado.**
  Verificado.
- **`grep -rn "solution-baselines" Global/_canonical/agents/*.md`** → 2 resultados, ninguno el
  orquestador. Verificado.
- **`grep -rn "enabled_for" --include="*.py" --include="*.sh" .`** → 0 en código. Verificado.
- **24 archivos `ai/state/features/*.json`** parseados: todos los `init` van de `USER_APPROVAL` a
  `PACKAGE_PLANNING`. Verificado.
- **Las entradas de `decisions-log.jsonl`** cruzadas contra los timestamps de `init`: 14 pre-`init`,
  inspeccionadas de a una, ninguna cierra un eje. Verificado. *(El log tenía 127 entradas en la
  primera pasada y **130** al reverificar horas después — creció durante la sesión. El número que
  importa no cambió: **cero** cierres de eje.)*
- **`feature-state.py:806-808`** (`--approved-by` required) y **`:1128-1139`** (`log-decision`) y
  **`cli_reporting.py:83-113`**: leídos. Verificado.
- **`bootstrap_project.py:27`** (`docs/project/architecture.md` = `TODO:`) y
  **`check-canonical-paths.py:42`** (waiver del mismo path). Verificado.
- **`ls docs/`** → no existe `docs/project/` en este repo. Verificado.

**Verificado en la ronda de enmiendas** (todo lo que el desafío afirmó, comprobado antes de
escribirlo — no acepté ninguna corrección de memoria):

- **E-2**: claves de `ai/state/narrative-log.jsonl` = `actor, at, client, feature_id, package_id,
  result, role, tech`, sobre 178 entradas. **No hay campo de pregunta emitida.** Verificado.
- **E-3**: `cli_reporting.py:90` resuelve el log con `Path("ai/state")` relativo al CWD. Sedes de
  `init` en la suite: **38** vía `init_state` (`tests/test_harness.py:278-289`) + **8** directas
  (`test_integration_hook.py:110,171`; `test_module_docs.py:53,349`; `test_rdd_schema.py:148,282`;
  `test_repair_ceiling.py:57`; `test_living_scope.py:32`) = **46**. *(El desafío estimó ~42; el
  conteo exacto es 46. Uso el mío, que es reproducible con `grep -c`.)* Verificado.
- **E-4**: `cli_reporting.py:92-99`, clave de duplicado = `(slug, title, decision)`, **sin
  `feature_id`**. Verificado leyendo el bloque completo.
- **E-5**: `tests/test_harness.py:30` → `FEATURE_STATE = ROOT / "PROYECTO/ai/scripts/feature-state.py"`.
  Y `cli_reporting.py:297-301`: el digest filtra decisiones **sólo** por `at >= since`. Y
  `docs/notas/decisiones/` tiene **130 archivos para 130 entradas** — uno por entrada. Verificado.
- **E-6**: `feature-state.py:819` con `choices=sorted(MODE_BUDGETS)`; `model.py:106-111` incluye
  `quick-fix` **e** `incident`; `tests/test_harness.py:8712` y `:8730` inicializan en quick-fix.
  **La afirmación de la ronda anterior era falsa** y está corregida en AC-22. Verificado.
- **E-7**: contadas las celdas. 4 archivos × 9 ejes = 36; los diferenciables con fuente hoy son los
  3 originales + embeddings (3 de 4 categorías con umbral distinto). Verificado leyendo las cuatro
  tablas.
- **E-10 / conteo**: **once** guardas falsas-verdes, no diez. Derivación explícita: las diez que 028
  cita (`docs/specs/028-narracion-que-ensena/spec.md:196`, que a su vez se apoya en el desglose de
  027 — 5 reparadas + 4 abiertas + 1 flageada, `docs/specs/027-controles-que-miran/spec.md:11-17`)
  **más** la que la propia 028 encontró y nombra sin sumar al conteo: `tests/test_digest.py:266-268`
  itera sobre **tres** archivos compartidos (`CLAUDE.md`, `AGENTS.opencode.md`, `AGENTS.pi.md`) y
  **omite `AGENTS.codex.md`**. Leí las líneas. Once.
- **E-12**: `scraping-datos-ml.md:34-35` — *"riesgo legal es decisión del CLIENTE (Question policy),
  no del implementador"*. Y `gestion-dashboard.md:21` — *"Requisito de datos on-premise/
  regulatorio"*. **El repo ya lo declara decisión del cliente**; el eje 10 no inventa, conecta.
  Verificado.
- **028 en su versión actual**: releída. Declara `owned_paths` por paquete (`spec.md:299-301`,
  `:404-407`, `:433-435`, `:452-453`), tiene `narration_lint.py` como archivo nuevo en N1, y
  AC-05b reemplazó la regla del 70% por **contención** (`:375-379`). Todas las referencias que hago
  a 028 salen de esa lectura, no de la versión que leí en la primera ronda. Verificado.
- **`docs/adr/README.md:3`** — *"One row per ADR, no exceptions"*. Es lo que hace viable el chequeo
  de índice de AC-18/V-1. Verificado.
- **`bootstrap_project.py:95-99`** — create-if-missing **y** `conflicts.append(relative)` cuando el
  contenido difiere. Es la regresión de AC-15b. Verificado.

### Lo que NO pude verificar, nombrado

1. **La postura por defecto de audiencia (eje 4) y de superficie mobile (eje 7).** Busqué y **no hay
   fuente en el repo**. Están marcados `sin verificar` en el catálogo a propósito, y AC-09 acepta
   explícitamente que terminen `sin default`. Inventarlos acá habría sido el defecto que la feature
   trata.
2. **gentle-ai** — verificado parcialmente, y con la distinción que corresponde:
   - **Verificado en el repo**: la referencia existe y es real.
     `Global/_canonical/skills/strict-tdd/SKILL.md:16-17` — *"Ported from `gentle-ai`'s (Gentleman
     Programming) RDD strict-TDD module"* — y `docs/adr/0020-*.md:3-6` documenta un estudio previo de
     cinco ADRs (0020-0024) sobre ese harness.
   - **Verificado en la fuente**: existe un diseño publicado que es **exactamente** lo que pide
     Federico. `gh api repos/Gentleman-Programming/gentle-ai/issues/994` devuelve
     `{"number":994, "title":"feat(idd): add IDD discovery V1 — pre-SDD intent refinement phase",
     "state":"open", "created_at":"2026-06-30T06:25:04Z", "updated_at":"2026-07-29T03:44:18Z"}`.
     Es una **fase de descubrimiento previa a SDD**, con un loop interactivo de preguntas de dominio
     **de a una por vez**, que produce un *intent artifact* con campos `goal, reason, users, domain
     entities, constraints, decisions, open questions, ready assessment`, y una evaluación de
     confianza que permite a `sdd-propose` saltear su propia ronda de preguntas cuando la confianza
     es media o mayor.
   - **Lo que NO puedo afirmar**: el issue está **abierto** y su propio texto pide *"architectural
     decision before a PR"*. Es un **diseño propuesto, no comportamiento entregado**. No leí el
     código de gentle-ai. Cualquier afirmación sobre cómo se comporta hoy en la práctica sería
     invento, y no la hago.
   - **Cómo lo usa esta spec**: como **confirmación independiente de que el problema es real** (otro
     harness serio llegó a la misma conclusión: falta una fase antes de SDD), y como **contraste
     deliberado**. Dos diferencias de diseño, tomadas a conciencia:
     (a) gentle-ai pregunta **de a una por vez**; esta spec exige **un bloque consolidado** con
     techo de 7, porque `orchestrator.md:604` ya manda batchear y porque la continuidad de turno
     (`:613-618`) penaliza el ida y vuelta;
     (b) gentle-ai produce un **artefacto nuevo** (`intent artifact`); esta spec también termina en
     un almacén propio (`axes-log.jsonl`, AC-12), pero **por una razón medida** —la colisión de
     idempotencia de E-4— y no por simetría con gentle-ai. *(En la ronda anterior dije que 029
     reusaba `decisions-log`; la enmienda E-4 lo cambió. Lo corrijo acá en vez de dejar la
     comparación vieja en pie.)*
3. **Si `enabled_for` tiene algún consumidor fuera del repo** (un runtime que lo lea al cargar
   skills). Grepeé el repo y no hay ninguno; no inspeccioné los runtimes instalados. **Sin
   verificar** — por eso AC-02 arregla el frontmatter **y** la prosa, en vez de confiar en uno solo.
4. **El costo real en tokens del intake.** Estimé "1 archivo de ~36 líneas" leyendo los archivos, no
   midiendo un turno real. **Sin verificar**; es una estimación, no un dato.
5. **La ventana de tolerancia de `asked_at`** (AC-25): no fijé número. Depende de cuánto tarda un
   turno real entre narrar y registrar, y eso **no lo medí**. Lo enruto a arquitectura con un
   default conservador sugerido —la duración del turno— y marcado UNVERIFIED.
6. **Si las 46 sedes de test se arreglan con un log de prueba o con un modo de test** (AC-24): no
   corrí nada, así que no sé cuál de los dos es menos invasivo. **Sin verificar**; lo que sí está
   decidido es que las dos salidas prohibidas de AC-23 no son opción.
7. **Si `narration_lint.py` de 028/N1 va a existir cuando A4 se implemente.** Depende del orden de
   entrega, que no controlo. Por eso AC-18/V-3 define la regla en las dos direcciones.
8. **No corrí la suite ni `verify.sh`** — el árbol tiene paquetes de 027 sin commitear, un
   `verify.sh` y un delta-reviewer trabajando. Todas las mediciones de esta spec son lecturas de
   archivos, `grep`, `gh api` y consultas de solo lectura al estado. **Ninguna afirmación de esta
   spec depende de haber ejecutado la suite.**

### Pase de conflictos entre requisitos

Recorridos los pares que pueden dispararse sobre la misma entidad:

- **AC-04.2 (primera clase se pregunta siempre) × la vía `assumed`** — **conflicto real, resuelto
  con precedencia explícita**: `assumed` en primera clase es legal **sólo después** de haber
  preguntado. Y desde AC-25 la precedencia dejó de ser sólo prosa: `assumed`/`user`/`n/a` en primera
  clase exigen `asked_at`. Asumir sin preguntar sigue siendo hallazgo de review, pero ahora también
  cuesta.
- **AC-04.2 × el carve-out de plataforma nombrada** *(E-10, conflicto nuevo y resuelto)* — escribir
  AC-04.2 en absoluto contradice `orchestrator.md:594-598`, que vive cuatro líneas más abajo de la
  regla que AC-04.2 cita. Precedencia: el carve-out gana, porque **es** el caso (1) de ADR-0037. El
  eje se registra `origin: request`, no `user` ni `assumed`, y **no** exige `asked_at` (no hubo
  pregunta que hacer).
- **AC-05 (techo de 7) × AC-04.2** — compatibles: primera clase son 3 (4 con el eje 10 disparado),
  quedan 3-4 cupos. El techo nunca fuerza a saltear un eje de primera clase.
- **AC-05 × el orden de prioridad** *(E-8, el conflicto que la ronda anterior no vio)* — con tope 5
  y dos ejes `sin default`, el bloque quedaba determinístico y **embeddings jamás se preguntaba**.
  Resuelto invirtiendo el criterio: el presupuesto acota lo que el harness **agrega**, no lo que el
  pedido **trae**. Un eje tocado por evidencia entra antes que uno sin default.
- **AC-17 (universo completo) × AC-05 (techo de preguntas)** — **no compiten, y es el punto de
  diseño más importante de la spec**: registrar 10 ≠ preguntar 10. La obligación es de **registro**.
  6 a 8 se registran `assumed` o `n/a` sin gastar una pregunta. El diagrama de disparo ahora separa
  las dos columnas explícitamente (E-9).
- **AC-14 (`n/a` con `reason`) × AC-17 (ausencia rechaza)** — se refuerzan: separan "decidí que no
  aplica" de "nunca lo miré". Y AC-18/V-4 le puso reglas al `n/a`, que antes era puerta libre.
- **AC-18 (validación estricta) × R-4 (fricción)** — tensión real: cuanto más estricta, más caro
  registrar. Resuelta por AC-20 —el rechazo trae el default, así que el camino de menor esfuerzo es
  copiar una postura correcta— y por AC-22, que saca a `incident` de la ecuación.
- **AC-18/V-1 (`source` resoluble contra `docs/adr/README.md`) × el propio ADR-0058** — **conflicto
  de secuencia, declarado**: mientras 0058 no exista e indexado, ningún eje puede citarlo. Es
  correcto y deliberado: es exactamente el fixture que la ronda anterior no atrapaba. El ADR se
  escribe en el gate del paquete que lo produce, y recién ahí puede citarse.
- **AC-21 (no retrofit) × AC-17** — necesarios juntos: sin AC-21, el primer `validate` sobre las 24
  features existentes reprobaría y la guarda se desactivaría en una semana (R-5).
- **AC-22 (`incident` exento) × AC-17 (universo completo)** — **excepción explícita, no agujero**:
  el break-glass no registra en el momento y sí en el follow-up que el modo ya obliga
  (`request-triage/SKILL.md:95`). La exención queda escrita en el estado, visible.
- **AC-23 (log ausente ⇒ rechazo) × AC-24 (46 tests)** — la tensión que produce R-8. Resuelta
  poniendo las 46 sedes **dentro** del paquete: no es daño colateral que alguien repare de apuro
  aflojando la guarda.
- **029 × 028** — **hay solape y está declarado en tres lugares** (encabezado, `owned_paths` de A1,
  A3 y A4, y la nota de acoplamiento). Cuatro archivos compartidos, regiones disjuntas, orden
  recomendado 028/N1 → 029/A4, y **un solo módulo de lint anti-relleno**. *(En la ronda anterior
  afirmé que no había punto de contacto. Era falso: `asked_at` lee la superficie de 028. Corregido.)*
- **029 × 027** — sin solape de archivos, pero **sí de lección**: ADR-0051 acaba de reparar el
  aislamiento de tests, y AC-23 prohíbe por escrito el atajo que lo volvería a romper
  (`/tmp/axes-log.jsonl` compartido). 027 también aporta el conteo de guardas falsas-verdes.

### Supuestos de nivel HOW, marcados UNVERIFIED para arquitectura

Ninguno de estos es un contrato de datos que yo pueda afirmar; los enruto a arquitectura:

- **UNVERIFIED** — el nombre y la firma del subcomando de ejes. AC-12 fija los **campos** y AC-12c
  la **regla de reescritura**; la firma la resuelve arquitectura. *(Lo que ya NO es unverified es la
  colisión de idempotencia: `cli_reporting.py:92-99` está leído y el defecto es un hecho. Por eso
  AC-12 decide almacén propio en vez de dejarlo abierto.)*
- **UNVERIFIED** — la regla de derivación exacta del path del log cuando no se pasa `--axes-log`
  (AC-23). Sé cuáles son las dos derivaciones **prohibidas** y por qué; cuál es la correcta depende
  de cómo `init` resuelve la raíz del proyecto hoy, y eso no lo leí. **Arquitectura lo fija, y el
  test de aislamiento de AC-23 lo prueba.**
- **UNVERIFIED** — el largo mínimo de contenido en AC-18/V-2. A propósito no puse número: lo fija
  arquitectura mirando los topes que 028 usa (`028/AC-05`: 400 y 240) para que los dos criterios no
  se contradigan, ya que **comparten módulo** (V-3).
- **UNVERIFIED** — la ventana de tolerancia de `asked_at` (AC-25).
- **UNVERIFIED** — el formato de la tabla de ejes en `docs/project/architecture.md` (AC-15) y cuál
  de las dos salidas de AC-15b evita la regresión de conflicto (`bootstrap_project.py:95-99`).
- **UNVERIFIED** — si `enabled_for` en el frontmatter tiene efecto en algún runtime (punto 3).
- **UNVERIFIED** — si el predicado de contención de 028/AC-05b se aplica tal cual entre ejes o
  necesita un ajuste (comparar N campos entre sí no es lo mismo que comparar dos campos de una
  entrada). **Arquitectura lo confirma al importar el módulo; lo que la spec fija es que el módulo
  sea uno solo.**

### Fixtures que engañarían a estos criterios, y por qué no pasan

La regla de fidelidad: un criterio que pasaría con un fixture armado y fallaría contra el uso real
es un defecto aunque "testee".

**Las ocho puertas de la ronda anterior, y qué las cierra ahora.** Tres las había enumerado yo;
las cinco restantes las encontró el desafío intentando burlar la regla — que es exactamente por qué
la enumeración va **después** de intentar pasarla (regla de método en A4).

| # | El fixture que pasaba | Qué lo mata ahora |
|---|---|---|
| 1 | `stance: "ok"` en los diez | AC-18/V-2 (anti-relleno) — *ya estaba* |
| 2 | `origin: assumed` sin `threshold` | AC-13 + AC-18 — *ya estaba* |
| 3 | `origin: adr` sin `source` | AC-18/V-1 — *ya estaba, pero era débil* |
| 4 | **`source: docs/adr/0058-*.md:41` — un ADR que no existe, que reserva esta misma spec** | AC-18/V-1: archivo existe + línea en rango + ADR indexado en `docs/adr/README.md` |
| 5 | **`--threshold "n/a"`** (AC-13 sólo pedía "no vacío") | AC-18/V-2: denylist explícita en **todos** los campos de contenido |
| 6 | **El mismo `stance` repetido en los diez ejes** | AC-18/V-3, con el módulo de lint compartido con 028 |
| 7 | **`origin: n/a` sin ninguna regla** | AC-18/V-4: exige `reason`, que pasa R-2 y no se repite |
| 8 | **`origin: user` en los diez — el más barato de todos, y nada podía desmentirlo** | AC-25: `asked_at` contrastado contra `narrative-log.jsonl` |

Y las que se agregaron con los ACs nuevos:

- **El fixture que engañaría a AC-23**: hacer que la guarda no chequee cuando el log no existe.
  Pasaría los 46 tests de una. **AC-23 lo prohíbe por escrito y exige el test que lo pincha** — sería
  una guarda falsa-verde escrita a propósito, la número doce.
- **El fixture que engañaría a AC-24**: arreglar las 46 sedes derivando el log a `/tmp`. Verde, y
  rompe el aislamiento que ADR-0051 acaba de reparar. **AC-23 lo prohíbe con nombre y apellido.**
- **El fixture que engañaría a AC-01/AC-02**: agregar `orchestrator` al frontmatter y declarar el AC
  cumplido. Pasaría un parse de YAML. **Lo mata la medición D-2**: `enabled_for` no lo lee nadie —
  por eso AC-02 exige las dos mitades, y AC-10b agrega la `description`.
- **El fixture que engañaría a AC-07**: grepear `Global/_canonical/` y dar verde. **AC-07 exige el
  árbol generado, los cuatro runtimes** — el defecto D-6 de 028 fue exactamente ése, y la guarda que
  debía atraparlo (`tests/test_digest.py:266-268`) mira tres de cuatro. Es la guarda falsa-verde
  **número once** de este repo.
- **El fixture que engañaría a A3/A4 enteros**: implementar en `ai/scripts/` y no en
  `PROYECTO/ai/scripts/`. **La suite queda verde porque ejerce el espejo** (`tests/test_harness.py:30`)
  **y el repo real queda sin guarda.** Los `owned_paths` nombran los dos, y está escrito como
  trampa conocida.
- **El fixture que engañaría a AC-19**: un test que registra 10 ejes válidos y verifica exit 0.
  Verde perpetuo, mire o no mire la guarda. **AC-19 exige un test por cada uno de los ocho modos de
  la tabla de arriba, más los de AC-23 y AC-25** — es la lección de las **once** guardas
  falsas-verdes de este repo (`docs/specs/027-controles-que-miran/spec.md:11-17` para diez;
  `tests/test_digest.py:266-268` para la undécima).
