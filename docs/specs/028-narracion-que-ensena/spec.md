# 028 — Narración que enseña

- **Estado**: Draft, **enmendada tras `SPEC_CHALLENGE`** (2026-08-15). El desafío independiente
  confirmó el diagnóstico entero y **rechazó la guarda**: reimplementó las reglas y demostró
  corriendo que la mayoría de los ataques las atraviesan. Esta versión reemplaza el mecanismo de
  detección; el diagnóstico queda como estaba.
- **Origen**: pedido directo de Federico (2026-08-15), en `ai/state/decisions-log.jsonl`, slug
  `narracion-que-explica-en-vez-de-apuntar`:
  *"no quiero que mencione 'hice el fix de PKG-007, sigue el item A que quedó de spec.md'. Eso solo
  es información para el que sabe y recuerda que se encuentra ahí dentro. […] yo soy ingeniero y
  muchas veces no le puedo seguir el estado del proyecto porque no explica."*
- **ADR**: 0057.
- **Precondición**: ninguna. No depende de 025 ni de 027.

## El problema, en una frase

Un identificador es un **puntero**: `PKG-007` sirve para reanudar trabajo, no para decidir. Hoy la
narración del harness está llena de punteros y vacía de porqués, y el dueño del repo —que es
ingeniero— no puede seguir su propio proyecto sin abrir la spec.

## Qué cambió en esta enmienda

| # | Enmienda | Efecto |
|---|---|---|
| E-1 | La guarda medía **longitud**, no contenido | AC-04 reescrito sobre **densidad de punteros por cláusula** |
| E-2 | Faltaban cinco familias de identificadores | Patrón ampliado; `archivo:línea` tratado aparte |
| E-3 | AC-03 se apoyaba en bifurcaciones que no existen | `--alternative` sólo en bloqueo técnico y planificación |
| E-4 | `log-narrative` no recibe estado | Cambio de contrato del CLI; `--feature-id` obligatorio al cerrar |
| E-5 | Lo visible para Federico llegaba último | Orden `N3a → N1 → N2 → N3b` |
| E-6 | Se exigía ritual en cierres que nadie lee | Campos obligatorios sólo en **hitos** de ADR-0027 |
| E-7 | AC-13 cubría uno de tres truncados | Extendido; AC-15 corregido de 400 a 300 |
| E-8 | AC-12 no prohibía nombres de fase | Ampliado a fases y a inglés crudo |
| E-9 | Dos bypasses estructurales | AC nuevos para `--result started` y `log-quickfix` |
| E-10 | Cuatro estados sin contrato | Definidos |
| E-11 | La regla del 70% era evadible | Reemplazada por contención |
| E-15 | La forma de datos estaba implícita | Registrada como decisión explícita |

---

## Lo que ya funciona, y no se toca

- **La narración se persiste siempre.** `record-spawn` + `log-narrative` escriben al JSONL y de ahí
  salen `STATUS.md`, la `bitacora.md` por feature y el digest. La cañería está entera.
- **Hay narración buena en el propio historial**, y es la vara. La mejor medida
  (`narrative-log.jsonl`, 2026-08-14T23:14:40, repair-agent, `done`):
  > *"La causa era una simulación incompleta: faltaba el stub de pnpm, y el instalador intentaba
  > calentar Pi por red. Ya quedó simulado; el focal termina en 2,6 segundos."*

  Dice qué pasaba, por qué pasaba, y con qué número se comprueba. Densidad de punteros: **0.00**.

El defecto no es que el harness no sepa narrar. Es que **nada se lo exige y varias capas se lo
deshacen**.

> **Higiene de citas**: `narrative-log.jsonl` es append-only y sus números de línea se corren solos
> —una cita de la versión anterior de esta spec ya se había desplazado de la 163 a la 169 mientras se
> escribía—. Todas las citas al log van **por timestamp + rol + fragmento**, nunca por línea.

---

## Los defectos, medidos

*(Sección validada por el desafío independiente: D-1, D-3, D-4a, D-4d, D-5 y D-6 fueron
re-verificados de forma autónoma y confirmados. Se corrige un número propio en D-3.)*

### D-1 — La doctrina pide describir, no explicar

`Global/_canonical/agents/orchestrator.md:731-737`, bloque de cierre:

```
✓ <role> terminó — <resultado en pocas palabras>
  Cliente: <qué quedó listo, o qué falta para que lo pueda usar>
  Ingeniería: <evidencia concreta, transición registrada en estado, próximo eslabón>
```

*"próximo eslabón"* pide el **nombre** del siguiente paso, no su razón. Ninguno de los dos registros
pide qué se **aprendió**, ni por qué el siguiente paso es ése y no otro. La única línea de toda la
doctrina que obliga a un porqué es `Conviene ahora: <próximo paso concreto Y por qué es el
siguiente>` (línea 767) — y es **una por TURNO**, no por agente. Un turno con seis cierres produce
un porqué.

ADR-0027 (`docs/adr/0027-milestone-narration-digest.md:17-21`) regula **cuándo** se narra y **en qué
registros**, nunca **qué contenido mínimo** lleva cada registro. La hipótesis del pedido queda
confirmada.

### D-2 — El registro `Ingeniería:` está hecho de punteros

Universo: las 178 entradas de `ai/state/narrative-log.jsonl`, 130 de ellas cierres
(`result` ∈ `done|blocked`).

| Medición | Resultado |
|---|---:|
| Cierres cuyo `tech` contiene un identificador | **54 / 130 (42%)** |
| Entradas con densidad de punteros en `tech` > 0.35 (evidencia excluida) | **53 / 178 (30%)** |
| Entradas cuyo `tech` contiene un nombre de fase | **51 / 178** |

Tres ejemplos reales:

1. `narrative-log.jsonl`, 2026-08-14T20:42, package-reviewer, `done`:
   > *"Review independiente repair_required: P2-F01 descendientes sin frontera, P2-F02
   > symlink-padre, P2-F03 estado global al cambiar HOME. Reparación consolidada requerida."*

   **Por qué falla**: es un índice. No dice que los tres hallazgos son la misma clase —la frontera
   de escritura no se hereda—, ni cuál es grave, ni qué se decide con eso. Densidad: **1.40**.

2. `docs/specs/003-trusted-routing-pi-runtime/bitacora.md:253`:
   > *"R3 complete within authorized budget (spawns 14-16, cycle 3/3): FD-001..FD-010 closed (6
   > resolved, 4 resolved-by-approved-exception per r3-threat-model-amendment)…"*

   **Por qué falla**: catorce identificadores y cero información. Un rango (`FD-001..FD-010`) no
   dice nada de ningún hallazgo. Y está cortado a mitad de palabra — ver D-4(d).

3. `narrative-log.jsonl`, 2026-08-14T23:46:51, gate-runner, `done`:
   > *"verify.sh confirmó la frontera endurecida y el diff limpio; el paquete pasa a revisión delta
   > focalizada."*

   **Por qué falla**: la mejor de las tres y aun así deja al lector afuera. Dice **qué** sigue,
   nunca **por qué** delta y no aceptación directa.

### D-3 — Nada valida el contenido, y el registro `Cliente:` cumple menos de lo que creí

- `ai/scripts/feature-state.py:919-920`: en `record-spawn`, `--client` y `--tech` son
  `default=""`. Un spawn puede registrarse sin una palabra de narración.
- En `log-narrative` (`feature-state.py:1118-1119`) son `required=True`, pero
  `cmd_log_narrative` (`ai/scripts/feature_state_lib/cli_reporting.py:53-80`) escribe la cadena tal
  cual. **`--client "ok" --tech "ok" --result done` se acepta hoy.**
- `ai/scripts/coord_policy.py`: `grep -in "client\|tech\|narrat"` da **cero** resultados.
- Las únicas pruebas existentes son de **presencia de texto en la doctrina**
  (`tests/test_digest.py:269-276`, `tests/test_harness.py:4287-4314`, `:4328-4333`). Ninguna mira
  una narración producida. Una doctrina puede estar perfectamente escrita y perfectamente ignorada,
  y las tres pasan en verde.

> **Corrección a la versión anterior de esta spec.** Ahí escribí que el registro `Cliente:` *"ya está
> limpio"*, con **1 de 178** entradas con identificador. Ese número salía de un patrón demasiado
> angosto. Con las familias que faltaban (E-2), la medición real es **21 de 178 (11.8%)** — casos
> como *"P1 quedó implementado con pruebas focalizadas verdes"* o *"la segunda reparación será
> acotada a DR-001..DR-010"*. La regla existe desde `orchestrator.md:786-788` y se viola una de cada
> ocho veces sin que nadie lo note. El registro `Cliente:` es **el más sano de los dos, no un
> registro sano**.

### D-4 — Las superficies que Federico lee convierten la narración en puntero

Es el defecto más caro: **deshace la cura**. Aunque el agente narre bien, el render lo devuelve a
punteros.

a) **`STATUS.md` tira la razón que ya tiene en la mano.** `ai/state/STATUS.md:32` y `:34` dicen
   literalmente `PACKAGE_IMPLEMENTATION` y `DELTA_REVIEW`. En
   `ai/scripts/feature_state_lib/render_status.py:66`:
   ```python
   "next": (next_transition(data).get("next") or "-"),
   ```
   `next_transition` (`transitions.py:54-129`) devuelve **`{"next": ..., "reason": ...}`** y el
   render se queda sólo con `next`. La explicación existe en estado y se descarta al renderizar.

b) **El digest publica cadenas de uso del CLI.** `docs/notas/BUENOS-DIAS.md:25-26`:
   > *"→ `PACKAGE_ACCEPTED` — P3-graph-view: module impact required (record-module-impact) or waived
   > (--module-impact-waived --reason)"*

   Cadena de origen completa: `model.py:546-549` (`module_impacts_ready`) arma el texto →
   `transitions.py:123-125` lo pone como `reason` → `render_notes.py:150` lo interpola crudo.

c) **El digest publica IDs de tareas en inglés.** `BUENOS-DIAS.md:27` lista *"additive
   schema/migration and invariants, narrow classifier + Pi terminal plumbing…"* — origen
   `render_notes.py:170-172`.

d) **El truncado borra exactamente el porqué.** `BUENOS-DIAS.md:41-58`: **las 18 decisiones** de
   "Decisiones nuevas" están cortadas a mitad de oración con `…` (`cli_reporting.py:301`,
   `_short(..., 200)`). No es un corte neutro: en una decisión bien escrita **el porqué va al
   final**, así que el truncado por cabeza conserva el "qué" y borra el "por qué". Lo mismo en
   `cli_reporting.py:220` (bloqueos, **120** caracteres — y es la sección *"Necesita tu decisión"*,
   la primera del digest) y `:232` (cierres, **300**).

e) **La bitácora corta a 400 y no avisa.** `render_bitacora.py:100-101` aplica `_short(..., 400)`:
   **11** `client` y **31** `tech` de 178 se leen truncados hoy (p. ej.
   `docs/specs/010-spawn-provenance/bitacora.md:93`, `003-trusted-routing-pi-runtime/bitacora.md:241`
   y `:253`).

### D-5 — El digest está viejo y ninguna doctrina dice cuándo correrlo

`BUENOS-DIAS.md:4`: *"Ventana: desde `2026-08-11T18:09:06` · generado 2026-08-12T21:09:06"*.
`STATUS.md:5`: *"Actualizado: 2026-08-15T02:32:13"*. **Tres días de atraso** en la superficie que el
pedido llama la más importante.

Causa: `grep -n "digest"` sobre `orchestrator.md`, `Global/_shared/*.md` y
`Global/_canonical/commands/*.md` devuelve **sólo menciones descriptivas**. Ninguna dice cuándo
ejecutarlo. `STATUS.md` y las notas se regeneran solas en cada mutación
(`cli_reporting.py:76-79`); el digest **no**.

### D-6 — La doctrina de Codex quedó atrás, y la guarda mira tres archivos de cuatro

`Global/_shared/AGENTS.codex.md:14-16` todavía dice *"The coordinator narrates **every
instantiation** … once before delegating and once when the instance returns"* — doctrina
**pre-ADR-0027**. Los otros tres compartidos dicen *"by MILESTONE, not by spawn (ADR-0027)"*
(`CLAUDE.md:12`). Y la prueba que debería atrapar la deriva, `tests/test_digest.py:269-272`, itera
sobre **tres** archivos y omite `AGENTS.codex.md`.

Es la misma familia de las diez guardas falsas-verdes del repo: **enumeración incompleta**. Queda
**sin verificar** si la omisión fue deliberada; la spec asume deriva y obliga a confirmarlo.

---

## Qué es una narración que enseña

*(Definición validada por el desafío independiente. No se re-litiga.)*

Un cierre de agente **enseña** cuando un ingeniero que no siguió el hilo puede **tomar la siguiente
decisión** con lo leído, sin abrir la spec ni recordar qué significa un identificador. Cuatro
contenidos:

1. **Qué cambió en el mundo** — el registro `Cliente:`. Ya existe.
2. **Qué aprendimos** — lo que ahora sabemos y antes no. Incluye el caso honesto *"nada nuevo:
   confirmó que X"*. Distinto de "qué hicimos".
3. **Qué conviene ahora y por qué** — el porqué se expresa como **consecuencia**: qué se rompe, qué
   queda sin saber, o qué se paga si no se hace. *"Porque toca"* no es un porqué.
4. **La alternativa y el criterio para elegir** — cuando hay más de un camino razonable.

Y dos reglas de forma:

- **El identificador acompaña, nunca sustituye.** Un identificador puede calificar una oración; una
  oración hecha de identificadores es un puntero.
- **La calidad no es longitud.** No hay mínimo de palabras en ninguna capa de esta spec — un mínimo
  es una invitación a rellenar.

---

## El corpus de ataque

Nueve narraciones construidas para atravesar la guarda. La provenance es el desafío independiente
(reimplementación en `lint.py`); el corpus se fija **acá** y no en un scratchpad, porque una guarda
que se prueba contra un archivo temporal no está probada.

| # | Ataque | Guarda v1 | Guarda enmendada |
|---|---|---|---|
| B0 | `PKG 007` con espacio en vez de guión — **el caso literal de Federico** | verde | **rojo** `WHY_NO_CONTENT` |
| B1 | El ejemplo D-2 de esta misma spec (`FD-001..FD-010`, inglés) | verde | **rojo** ×5 |
| B2 | Índice de hallazgos (`P2-F01, P2-F02, P2-F03`) | verde | **rojo** ×4 |
| B3 | Familia `XX-nnn` (`SC-01`, `SEC-007`, `FD-010`) | verde | **rojo** ×4 |
| B4 | `Pn`/`Dn`/`Rn` pelados (`P2 cerrado, D3 pendiente, R3 no aplica`) | verde | **rojo** ×5 |
| B5 | Archivo suelto como prosa vaga (`spec.md`, `acceptance.md`) | verde | **verde** ⚠️ |
| B6 | Feature-id `NNN-slug` | verde | **rojo** ×4 |
| B7 | `next` y `why` idénticos carácter por carácter | verde | **rojo** `WHY_CONTAINS_NEXT` |
| B8 | Cierre registrado como `--result started` para esquivar la guarda | verde | **rojo** `CLOSE_DISGUISED_AS_START` |

**B0, textual**, para que no haya ambigüedad sobre qué tiene que fallar:

```
--client  "Hice el fix del paquete siete."
--tech    "PKG 007 reparado, sigue el item A de spec.md."
--learned "Que el item A todavía sigue pendiente."
--next    "Hacer el item A que quedó de spec.md."
--why     "Porque es lo que sigue en spec.md."
```

**B5 sobrevive, y se declara.** Ver "Lo que no muerde".

---

## Paquetes

Orden de entrega **N3a → N1 → N2 → N3b** (E-5). Tres de las cuatro comprobaciones del criterio de
cierre son de N3a, y AC-11..14 **no dependen** de N1 ni de N2: leen `next_transition`,
`render_notes.py` y `cli_reporting.py`, todo preexistente. Con el orden anterior, lo único que
Federico podía ver en una mañana llegaba último.

### N3a — `la-manana-que-se-entiende` *(primero)*

Las superficies de lectura, con el código que ya existe. Entregable solo y visible el mismo día.

- **AC-11** — La columna "Próximo paso" de `STATUS.md` deja de ser un nombre de fase pelado: lleva
  la `reason` que `next_transition` ya devuelve y `render_status.py:66` descarta. **Sujeto a AC-12**
  (ver la pasada de conflicto): el `reason` crudo no se pega, se traduce.
- **AC-12** — El digest y `STATUS.md` dejan de publicar lenguaje de máquina. Prohibido en las
  secciones que lee un humano: `--flags`, nombres de comando crudos, **nombres de fase**
  (`PACKAGE_ACCEPTED` y compañía — hoy `BUENOS-DIAS.md:25` abre con uno, y es incoherente con AC-04,
  que sí los rechaza en `client`), y los IDs de tarea en inglés de `render_notes.py:170-172`
  (D-4c, que ningún AC anterior tocaba). Prueba que falle contra el archivo generado de hoy.
- **AC-13** — El truncado deja de comerse el porqué **en los tres puntos**, no en uno:
  `cli_reporting.py:220` (bloqueos, 120 — la sección *"Necesita tu decisión"*, la primera del
  digest), `:232` (cierres, 300) y `:301` (decisiones, 200). O se rinde el texto completo, o una
  forma corta escrita a propósito; **nunca un corte por caracteres a mitad de oración**. Criterio:
  cero `…` al final de línea en esas tres secciones. Hoy son 18 de 18 en decisiones.
- **AC-14** — El digest se regenera en **cierre de fase o de turno**, no en cada mutación.
  *(Decisión tomada, E-14.)* `BUENOS-DIAS.md` está trackeado en git y `STATUS.md`/`bitacora.md` no
  (consecuencia de 024/C1): regenerarlo en cada mutación lo mete en el diff de toda feature en vuelo
  y choca con `check-owned-paths.py`, que 027 acaba de endurecer. Medible: tras un cierre de fase, la
  marca *"generado"* de `BUENOS-DIAS.md:4` no queda más vieja que `Actualizado:` de `STATUS.md:5`.
  Hoy la brecha es de tres días.
- **AC-17** *(E-10)* — Los cuatro estados sin contrato quedan definidos, porque AC-11 los va a
  atravesar:
  - **Fase terminal**: `transitions.py:57` devuelve `reason="terminal"`. AC-11 promovería la palabra
    `terminal`, en inglés, a las **17 filas `DONE`** de `STATUS.md`. En fase terminal la columna
    dice `—`, no un motivo.
  - **Rama sin paquete**: `transitions.py:129` devuelve *"record required event before continuing"*.
    Se traduce; no se publica crudo.
  - **`blocked` de decisión humana**: el próximo paso es del humano. La columna lo dice así y **no**
    exige alternativa (ver AC-03).
  - **Muerte por cuota a mitad de camino**: la instancia no llega a narrar. El estado queda sin
    cierre y **eso no puede leerse como cierre**; la superficie lo muestra como interrumpido.

**owned_paths**: `ai/scripts/feature_state_lib/render_status.py`,
`ai/scripts/feature_state_lib/render_notes.py`, `ai/scripts/feature_state_lib/cli_reporting.py`,
más los espejos bajo `PROYECTO/ai/scripts/feature_state_lib/`, `tests/test_narracion_digest.py`
(nuevo), `docs/adr`.

### N1 — `campos-que-obligan`

El contrato de escritura. Es el paquete que hace que la regla exista *en el código*.

- **AC-01** *(E-15, decisión de forma de datos)* — `log-narrative` acepta cuatro campos nuevos:
  `--learned`, `--next`, `--why`, `--alternative`. **Forma de datos, registrada explícitamente**: el
  `narrative-log.jsonl` es append-only y la compatibilidad se resuelve **por ausencia de clave**, no
  por valor centinela — una entrada vieja no tiene la clave, y toda superficie que la renderice
  omite la sección en vez de escribir `None` o `-`. No se agrega versión de esquema al log: la
  ausencia de clave **es** la versión. Las 178 entradas existentes siguen leyéndose sin error.
- **AC-02** *(E-6, acotado)* — Los tres primeros son obligatorios **sólo en los hitos de ADR-0027**
  (`orchestrator.md:705-711`), no en los spawns persistidos, que ADR-0027 decidió deliberadamente
  no mostrarle al humano (`orchestrator.md:712`, *"persisted, not narrated"*). Exigir cuatro campos
  que enseñan en cierres que nadie va a leer es fabricar ritual.
  - El hito se declara con un flag explícito **`--milestone yes|no`, sin default**, obligatorio
    cuando `--result` es `done` o `blocked`. **No se infiere del estado**: inferirlo reintroduce el
    no-determinismo que E-3 eliminó (dependería de si la transición se grabó antes o después de
    narrar, y `orchestrator.md:794` no fija ese orden). Omitirlo es error duro, no escape silencioso;
    declarar `no` sobre algo que la doctrina llama hito es una violación revisable por CH-1.
  - **Consecuencia resuelta, no delegada**: hay exactamente **4** invocaciones de `log-narrative` en
    la suite, todas en `tests/test_harness.py`, y **2** con `--result done`
    (`:2911-2920` y `:4103-4112`). Las dos necesitan el flag nuevo. Por eso `tests/test_harness.py`
    **entra a los `owned_paths` de N1**. El cambio es **aditivo** —se agrega un flag, no se afloja
    ninguna aserción—, así que no viola la prohibición de debilitar tests de regresión. El
    implementer no llega al gate con la suite roja y sin permiso de arreglarla.
- **AC-03** *(E-3, reescrito)* — `--alternative` es obligatorio **sólo** en dos casos:
  (a) `--result blocked` **de causa técnica** —excluido `HUMAN_DECISION_REQUIRED`, donde la
  alternativa es del humano, no del agente—; y (b) `PACKAGE_PLANNING`, la única bifurcación
  genuinamente abierta que existe (`transitions.py:63`, elegir qué paquete sigue).
  **`--alternative none` es un valor legal**, y exige un `--why` que explique por qué el camino es
  único. Un vocabulario para "no hay alternativa" cuesta mucho menos que ruido fabricado.
  > La premisa anterior era falsa y se retira: `next_transition` **no ofrece** bifurcaciones en
  > `PACKAGE_GATES` ni en `PACKAGE_REVIEW`, las **resuelve**. El ternario de `transitions.py:66-71`
  > tiene dos brazos en el código, pero en cada llamada concreta el estado ya determinó cuál. En el
  > momento de narrar, la alternativa no existe.
- **AC-04** *(E-1 + E-2, el corazón de la enmienda)* — **La detección de punteros se mide por
  densidad, no por longitud.** Tres reglas componibles, ninguna de ellas un piso de caracteres:
  - **AC-04a — densidad de punteros por cláusula.** Se cuentan los punteros y se divide por las
    cláusulas (separadores fuertes: `. ; : , ( )` y las conjunciones). Topes: **≤ 0.35** en `client`,
    **≤ 0.35** en `tech`. Es un **cociente**: rellenar no ayuda, porque agregar cláusulas de relleno
    exige agregar cláusulas reales, que es justamente lo que se pide.
    Medido — narración buena de referencia **0.00**; los nueve ataques **0.33 a 1.40**.
  - **AC-04b — la evidencia no es contenido** *(decisión E-2)*. `archivo.py:línea` es **obligatorio**
    en `tech` por ADR-0026 y por lo tanto **no** cuenta como puntero ahí. Pero en `learned`, `next` y
    `why` **no puede ser el contenido único**: si al borrar citas de evidencia y punteros el campo se
    queda sin una sola palabra de contenido, se rechaza. No es negociable en ninguna dirección: ni
    romper la regla de evidencia, ni dejar el bypass abierto.
  - **AC-04c — el registro `Cliente:` en castellano y sin identificadores.** Cero punteros y cero
    nombres de fase, sin umbral (ya es doctrina en `orchestrator.md:786-788`; se viola en 21 de 178).
    Y proporción de palabras funcionales del castellano **≥ 0.25**, que es lo que atrapa el inglés
    crudo. Se aplica **sólo a `client`**: en `tech` la prosa técnica en inglés es legítima (118 de
    178 entradas caerían), y ahí el trabajo lo hace AC-04a.

  **Familias de identificadores** (E-2). Medido: 35 de los 130 cierres llevan punteros que el patrón
  anterior no veía. Las cinco que faltaban:

  | familia | cierres | invisibles antes |
  |---|---:|---:|
  | `Pn`/`Dn`/`Rn` pelado (`P1`, `D3`, `R3`) | 60 | **23** |
  | `XX-nnn` (`SC-01`, `SEC-007`, `FD-010`) | 59 | **13** |
  | archivo suelto (`spec.md`, `verify.sh`) | 46 | **11** |
  | feature-id `NNN-slug` | 8 | **3** |
  | separador flexible (`PKG 007`, `PKG_007`) | — | B0 |

  Verificado a mano: `FD-001` **no** matcheaba `F-?\d{2}` porque después de la `F` viene una `D`; y
  el ejemplo del punto 2 de D-2 dejaba **154** caracteres alfanuméricos tras borrar identificadores,
  muy por encima del umbral de 20 de la versión anterior. Los dos números son reproducibles.

- **AC-05** — Anti-inflación, **sólo topes, ningún piso**: `client` y `tech` máximo **400**
  caracteres (heredado del truncado que `render_bitacora.py:100-101` ya aplica en silencio);
  `learned`, `next`, `why`, `alternative` máximo **240** cada uno.
- **AC-05b** *(E-11, reemplaza la regla del 70%)* — La regla de solapamiento de vocabulario **se
  retira**: eximía el par `next`×`why`, así que dos campos **idénticos carácter por carácter**
  pasaban (B7), y con sinónimos se evadía trivialmente. La reemplaza una regla de **contención**:
  `why` no puede contener a `next` como subcadena ni al revés. Un porqué que repite el paso no es un
  porqué. Es más angosta y más honesta que un umbral estadístico que no medía lo que decía medir.
- **AC-06** — **El mensaje de rechazo de la guarda es él mismo un ejemplo de la doctrina.** Dice qué
  falta, por qué importa, y muestra la invocación corregida. Un error que sólo diga
  `NARRATION_LINT_FAIL learned=missing` reprueba su propio AC. Prueba: el texto contiene el nombre
  del campo, una oración de consecuencia y un ejemplo ejecutable.
- **AC-07** *(E-4, cambio de contrato del CLI)* — `log-narrative` gana `add_common_state_args`, y
  `--feature-id` pasa a **obligatorio** cuando `--result` es `done` o `blocked`.
  **Por qué es un cambio de contrato y no un detalle**: hoy su parser **no llama** a
  `add_common_state_args` (`feature-state.py:1117-1126`), `state_path()` es una ruta relativa
  hardcodeada (`model.py:199-200`) y la suite corre con `cwd=ROOT` (`tests/test_harness.py:41-49`).
  Una guarda enganchada en el despacho único que consultara estado **leería el estado de producción
  durante los tests** — la familia exacta de ADR-0051, que 027 acaba de reparar. Y `--feature-id` es
  opcional hoy: **11 de 178** entradas son `sin-feature`, **6 de ellas cierres**.
- **AC-08** *(E-9, los dos bypasses estructurales)* —
  - **Cierre disfrazado de apertura**: `--result started` no exige ningún campo y además desaparece
    del digest (`cli_reporting.py:225` filtra `started`). Un agente apurado registra el cierre como
    apertura y esquiva la guarda entera. La guarda tiene que detectar el cierre declarado como
    apertura; como mínimo, una apertura sin su cierre correspondiente al cambiar de fase es un error
    ruidoso, no un silencio.
  - **`log-quickfix` es un cierre narrado que ninguna guarda alcanza**: la doctrina lo trata como
    bloque narrado (`orchestrator.md:714`, *"ONE narrated block at close"*) y se publica en el
    digest, pero `cmd_log_quickfix` (`cli_reporting.py:33-51`) **no tiene campos `client`/`tech` en
    absoluto** — sólo `summary`. Entra al mismo contrato o se declara exento con su razón escrita;
    lo que no puede es quedar fuera por olvido.

**owned_paths**: `ai/scripts/narration_lint.py` (nuevo), `ai/scripts/feature-state.py`,
`PROYECTO/ai/scripts/feature-state.py`, `ai/scripts/feature_state_lib/cli_reporting.py` y su espejo
*(por AC-08: `cmd_log_quickfix` y el filtro de `started` viven ahí)*, `tests/test_harness.py`
*(por AC-02, 2 líneas)*, `tests/test_narracion_contrato.py` (nuevo), `docs/adr`.

> **Solape declarado con N3a**: los dos paquetes tocan `cli_reporting.py`. Son secuenciales y las
> regiones son disjuntas — N3a en `cmd_digest`, N1 en `cmd_log_narrative`/`cmd_log_quickfix` y el
> filtro de `started`. Se declara en vez de disimularse; 027 ya entregó cuatro paquetes con
> `owned_paths` solapados de la misma forma.

### N2 — `doctrina-que-explica`

La regla escrita, en la doctrina canónica, para que valga en cualquier máquina. Va **después** de N1:
una doctrina que mande pasar un flag inexistente es una doctrina falsa.

- **AC-09** — El bloque de cierre de `orchestrator.md:731-737` incorpora los cuatro contenidos, la
  regla del identificador y el flag `--milestone`. El registro `Ingeniería:` deja de pedir *"próximo
  eslabón"* y pasa a pedir el paso **con su consecuencia**.
- **AC-10** — La doctrina llega a los **cuatro** runtimes. Prueba sobre el árbol de `build.sh
  --output`, en `opencode/`, `claude-code/`, `codex/` (leído con `tomllib`, para que la aserción
  pruebe también el escapado) y `pi/`, al estilo de `tests/test_harness.py:4287-4314`.
- **AC-16** — La deriva de D-6: los **cuatro** archivos de `Global/_shared/` dicen lo mismo sobre
  narración, y la prueba itera sobre los cuatro, corrigiendo la enumeración incompleta de
  `tests/test_digest.py:269-272`. **Antes de unificar** se confirma si la divergencia de Codex fue
  deliberada; si lo fue, el resultado es una excepción documentada con su prueba, no una
  unificación.
- **AC-18** — La doctrina dice **cuándo** correr `feature-state.py digest`: cierre de fase y cierre
  de turno, coherente con AC-14. Prueba de presencia en los cuatro runtimes.

**owned_paths**: `Global/_canonical/agents/orchestrator.md`, `Global/_shared`, `Global/claude-code`,
`Global/codex`, `Global/opencode`, `Global/pi`, `tests/test_digest.py` *(por AC-16)*,
`tests/test_narracion_doctrina.py` (nuevo), `docs/adr`.

### N3b — `los-campos-donde-se-leen` *(último)*

Lo de N3 que sí depende de N1.

- **AC-15** — El truncado silencioso de la bitácora se vuelve ruidoso.
  **Corregido**: la versión anterior razonaba sobre 400 mientras el digest corta en **300**
  (`cli_reporting.py:232`), así que un `client` de 350 pasaba la guarda de escritura, salía truncado
  en el digest, y AC-15 lo habría etiquetado *"entrada histórica previa a la guarda"* — un cartel que
  miente, puesto por la feature que existe para que los carteles no mientan. La regla correcta: el
  tope de escritura (400) y el tope de render (300) **no pueden estar en desacuerdo**; se alinean, y
  sólo lo genuinamente anterior a la guarda se marca como histórico.
- **AC-19** — Los campos nuevos se ven donde se lee: `learned`, `next`, `why` y `alternative`
  aparecen en la `bitacora.md` por feature y en el digest. Una entrada histórica sin esas claves se
  rinde como hoy, sin huecos ni `None` (AC-01).

**owned_paths**: `ai/scripts/feature_state_lib/render_bitacora.py` y su espejo,
`tests/test_narracion_digest.py`, `docs/adr`.

---

## Qué es mecánicamente testeable y qué no

Todo lo de abajo se corrió antes de escribirse.

### Sí muerde, medido

Contra el corpus de nueve ataques, la guarda enmendada da **8 en rojo**. Contra la mejor narración
real del historial, con los campos nuevos completados, da **cero** hallazgos. Distingue las dos.

Lo mecánicamente decidible es **estructura y proporción**, nunca estilo: densidad de punteros por
cláusula, presencia de campo, tope de longitud, contenido restante tras borrar punteros y evidencia,
contención entre `next` y `why`, proporción de palabras funcionales del castellano, y la obligación
de `--alternative` derivada de dos condiciones explícitas. Nada de eso requiere entender el texto.

Falsos positivos sobre las 178 entradas reales, con los umbrales propuestos:

| regla | dispara |
|---|---:|
| `CLIENT_POINTER_DENSITY` (> 0.35) | 6 / 178 (3.4%) |
| `TECH_POINTER_DENSITY` (> 0.35, evidencia excluida) | 53 / 178 (29.8%) |
| `CLIENT_NOT_SPANISH` (< 0.25) | 15 / 178 (8.4%) |
| `CLIENT_HAS_IDENTIFIER` | 21 / 178 (11.8%) |
| **alguna** | **71 / 178 (39.9%)** |

**El 30% de `tech` no es ruido: es el tamaño del problema.** Coincide, por dos caminos
independientes, con el 42% de cierres que llevan un identificador en `tech` (D-2). La guarda no es
retroactiva —no se reescribe la historia— pero ese número **predice fricción real** en las próximas
features, y hay que mirarlo de frente en vez de bajarlo hasta que quede lindo. Si en los primeros
veinte usos el umbral de `tech` resulta impracticable, la respuesta correcta es **discutir la regla**,
no aflojar el número en silencio.

### No muerde, y hay que decirlo

1. **B5 sobrevive.** Prosa vaga alrededor de nombres de archivo —*"Porque acceptance.md depende de lo
   que quedó escrito en spec.md"*— pasa las nueve reglas: tiene densidad baja, contenido no vacío y
   castellano legítimo. Es circular y no informa, y ninguna regla que yo pueda construir la separa de
   una prosa honestamente breve.
2. **La prueba de oración literal —verbo conjugado + sustantivo no-artefacto— no es implementable con
   robustez suficiente, y se descarta.** Se prototipó. El requisito de "sustantivo" necesita
   etiquetado gramatical, que no está en la biblioteca estándar; el proxy más cercano (contar
   palabras de contenido tras una stoplist de artefactos del harness) **es otro piso de longitud
   disfrazado** y lo derrota B1: el ejemplo en inglés de la propia spec puntúa **10**, dentro del
   rango de la narración buena (7 a 14). Se reemplazó por densidad, que es un cociente y no una
   cuenta, y por eso no premia el relleno.
3. **Una narración inflada en prosa no se detecta.** Un párrafo hueco de 350 caracteres bien escrito
   pasa. No hay heurística que lo arregle.
4. **No es detectable si el porqué es verdadero** ni si la alternativa es razonable. Un `--why` que
   diga *"porque es el siguiente paso del plan"* tiene la forma correcta y el contenido nulo.

Los cuatro se reemplazan por controles humanos declarados:

- **CH-1 — Un eje nuevo en la revisión de paquete.** El `package-reviewer` —ya read-only e
  independiente— evalúa **una muestra al azar de tres cierres** contra tres preguntas: *(i)* ¿se
  entiende sin abrir la spec?, *(ii)* ¿dice algo que no supiéramos?, *(iii)* ¿el porqué nombra una
  consecuencia concreta? Veredicto con `record-subreview --evidence`.
  **E-6 lo vuelve una defensa real**: con los campos obligatorios sólo en hitos, el universo por
  paquete baja de ~15 cierres a ~5 (027 registró 5 spawns por paquete), y muestrear 3 de 5 sostiene
  algo. Muestrear 3 de 15 no sostenía nada.
- **CH-2 — Federico, sobre el digest.** La prueba final no es un test: es leer `BUENOS-DIAS.md` una
  mañana y poder decir cuál es el próximo paso y por qué. Está en el criterio de cierre.

**Limitación declarada, no tapada**: contra la narración inflada y contra B5, la única defensa es
humana.

---

## No-goals

- **No se cambia cuándo se narra.** La cadencia por hito de ADR-0027 queda intacta: esta feature es
  sobre el **contenido**, no la frecuencia. No se vuelve a narrar por spawn ni se agrega un dial de
  verbosidad (ADR-0027 ya lo rechazó).
- **No se agrega un mínimo de palabras** en ningún campo, en ninguna capa.
- **No se reescribe la historia.** Las 178 entradas no se migran; la guarda es hacia adelante.
- **No se cambia el bloque de cierre de turno** (ADR-0033) ni el sub-bloque `Impacto humano`
  (ADR-0036).
- **No se exige narración que enseña en los spawns intra-fase** (E-6). ADR-0027 decidió no
  mostrárselos al humano; obligarlos a enseñar es ritual.
- **No se resuelve el atraso del digest reescribiéndolo a mano**: se arregla el disparador.
- **No se arregla la deriva del espejo `PROYECTO/`** más allá de lo que cada paquete espeje.

---

## Riesgos

1. **El umbral de `tech` marca el 30% del registro histórico.** Es el riesgo principal de fricción.
   Mitigación: no es retroactivo, y el implementer tiene mandato explícito de reportar —no de
   aflojar— si en los primeros veinte usos resulta impracticable.
2. **La guarda bloquea al orquestador en medio de un paquete.** Está en el camino crítico de
   escritura. Mitigación: código distinto de cero **más** el mensaje ejecutable de AC-06, así que el
   reintento es de un paso. Vigilar: la guarda no puede dejar el estado a medio escribir.
3. **`--milestone` sin default rompe toda invocación existente que no lo pase.** Acotado y medido:
   4 invocaciones en la suite, 2 afectadas, ambas en `tests/test_harness.py`, que está en los
   `owned_paths` de N1.
4. **N1 sin N2 deja una ventana donde el orquestador recibe un error que su doctrina no explica.**
   Acotada a un paquete, y amortiguada por AC-06 —el mensaje enseña la doctrina antes de que la
   doctrina exista—. Si N2 se demora, es motivo para parar.
5. **El espejo `PROYECTO/ai/scripts/` sólo está protegido en dos archivos.** `build.sh:92-105`
   compara únicamente `feature-state.py` y `check-owned-paths.py`; `feature_state_lib/` sólo se
   compila (`ai/scripts/verify.sh:20`). Hoy están idénticos —verificado con `cmp` sobre
   `cli_reporting.py`, `render_notes.py`, `render_status.py` y `feature-state.py`—, pero nada lo
   sostiene. Cada paquete espeja lo suyo y lo declara.
6. **AC-16 puede estar corrigiendo algo deliberado.** Si la narración por spawn de Codex fue una
   decisión, unificar sería una regresión. El AC obliga a confirmar primero.
7. **Que la feature se vuelva ceremonia.** Tres campos obligatorios por hito son tres oportunidades
   de relleno. La única defensa real es CH-1, y CH-1 es muestreo. Si la primera muestra sale mal, el
   problema no es el agente: es que los campos pidan algo que no se puede contestar honestamente en
   ese punto del ciclo, y hay que rediscutir el contrato.

---

## Gates

Por paquete: suite en verde (`pytest` no está instalado; base declarada por 027 en
`narrative-log.jsonl` 2026-08-14T23:46:51: **1130 OK** — **reverificar al arrancar**, hay tres
paquetes de 027 sin commitear), `./ai/scripts/verify.sh` → `VERIFY_PASS`, `./build.sh --check` →
`SELF_SCAFFOLD_SYNC_OK` + `GLOBAL_TREE_SYNC_OK` + `BUILD_CHECK_PASS`, ACs con evidencia `file:line`.
Review independiente en otro proveedor, repair consolidado, delta review.

Dos gates propios de esta feature:

1. **Toda prueba nueva se demuestra en las dos direcciones** —la narración pobre falla, la buena
   pasa— con la salida de las dos corridas en la evidencia.
2. **Los nueve ataques del corpus corren en rojo**, y la evidencia del paquete los incluye con su
   salida. Ocho tienen que dar rojo; **B5 tiene que dar verde y estar declarado como limitación
   conocida en la evidencia** — un B5 que pasara a rojo sin que nadie explique cómo es un resultado
   sospechoso, no una victoria. Una guarda que no se prueba contra los ataques que ya conocemos no
   está probada.

---

## Criterio de cierre

1. Invocar `log-narrative --result done --milestone yes --client "Hice el fix del paquete siete."
   --tech "PKG 007 reparado, sigue el item A de spec.md." …` con los campos de B0 y que **falle**,
   nombrando qué falta y cómo se escribe bien.
2. Abrir `ai/state/STATUS.md` y que "Próximo paso" diga algo más que un nombre de fase — y que las
   17 filas `DONE` digan `—`, no `terminal`.
3. Abrir `docs/notas/BUENOS-DIAS.md` recién generado y no encontrar ninguna línea cortada a mitad de
   oración en *"Necesita tu decisión"*, *"Qué quedó listo"* ni *"Decisiones nuevas"*, ni una sola
   cadena con `--flags` o nombres de fase.
4. **La prueba de Federico**: leer ese `BUENOS-DIAS.md` una mañana, sin abrir la spec ni el estado, y
   poder decir en voz alta cuál es el próximo paso y por qué es ése. Si no puede, la feature no está
   lista, aunque los tres puntos anteriores estén en verde.

---

## Auditoría de la spec

**Verificado con evidencia**

- Universo nombrado y contado en cada medición: **178** entradas de `ai/state/narrative-log.jsonl`
  (el historial completo, no una muestra), **130** cierres. Todo porcentaje sale de ahí.
- La guarda enmendada se **corrió** contra el corpus de nueve ataques (8 rojos, B5 verde) y contra
  las 178 entradas (tabla de falsos positivos). Los números son salida de esas corridas.
- Los dos números del desafío se reprodujeron de forma independiente: el ejemplo de D-2 deja **154**
  caracteres alfanuméricos tras borrar identificadores, y `FD-001` **no** matchea `F-?\d{2}`.
- Corregida una afirmación propia: el registro `Cliente:` no lleva 1 de 178 identificadores sino
  **21 de 178** (D-3).
- `log-narrative` en la suite: **4** invocaciones, todas en `tests/test_harness.py`, **2** con
  `done|blocked` (contado con `grep`).
- `cmd_log_quickfix` (`cli_reporting.py:33-51`) leído: **no tiene** campos `client`/`tech`.
- `transitions.py` tiene **129** líneas: la rama sin paquete está en `:129` y la terminal en `:57`
  (la enmienda las citaba como `:135`; corregido).
- `STATUS.md` tiene **17** filas `DONE` (contadas).
- Ausencia comprobada, no supuesta: `coord_policy.py` no menciona narración; ningún documento de
  `Global/` dice cuándo correr `digest`.
- Espejos `PROYECTO/` comparados con `cmp`: hoy idénticos en los cuatro archivos relevantes.

**Pasada de conflicto entre requisitos**

- **AC-04a × AC-05**: no compiten. Densidad es cociente, el tope es absoluto. Un texto puede fallar
  los dos; se reportan los dos.
- **AC-05 × AC-02**: un campo obligatorio con tope podría empujar a truncar en vez de partir.
  **Precedencia: la obligatoriedad gana** —el campo se escribe— y el tope se respeta partiendo
  contenido, nunca recortando el porqué.
- **AC-04b × ADR-0026**: conflicto real y resuelto por decisión. La evidencia `archivo:línea` es
  obligatoria en `tech` y por eso **no** cuenta como puntero ahí; en `learned`/`next`/`why` no puede
  ser el contenido único. Sin esta separación, la guarda castigaría la regla de evidencia del propio
  repo.
- **AC-04c × `tech`**: la regla de castellano **no** se aplica a `tech` a propósito: 118 de 178
  entradas caerían, y la prosa técnica en inglés es legítima ahí.
- **AC-11 × AC-12**: **conflicto real**. Las dos leen el mismo `reason` de `next_transition`, y ese
  `reason` es hoy exactamente la cadena de flags que AC-12 prohíbe: `transitions.py:123-125` reenvía
  el texto de `module_impacts_ready` (`model.py:546-549`), y `:70-71` el de `package_review_ready`.
  **Precedencia: AC-12 manda.** AC-11 no se resuelve pegando el `reason` crudo; hay que producir una
  forma legible, y la misma sirve a las dos superficies. Sin esta regla, N3a arreglaría una
  superficie rompiendo la otra.
- **AC-11 × AC-17**: en fase terminal AC-11 publicaría `terminal` en 17 filas. AC-17 manda: `—`.
- **AC-13 × AC-15**: se refuerzan una vez alineados los topes de escritura (400) y de render (300).
- **AC-02 × AC-08**: `--milestone` sin default y la detección de cierre-como-apertura cubren la misma
  familia de escape por dos vías; se conservan las dos, no hay contradicción.

**Sin verificar — va a arquitectura / package-reviewer**

1. **Los umbrales**: 0.35 de densidad, 0.25 de proporción de castellano, 400 y 240 de tope. Sólo el
   400 tiene fuente (el truncado existente). Los otros salen de separar un corpus de nueve ataques de
   una decena de ejemplos buenos: **es una muestra chica**, y son puntos de partida a calibrar, no
   contratos.
2. **La segmentación en cláusulas** (separadores fuertes) es una heurística. Un `tech` sin puntuación
   cuenta como una cláusula y su densidad se dispara; uno con listas separadas por comas se diluye.
   No se probó contra texto adversarial construido para manipular el denominador.
3. **La lista de familias de identificadores** sale de inspeccionar el historial, **no** de un
   esquema. Una forma nueva se escapa. Confirmar contra el esquema real de IDs del harness.
4. **La stoplist de palabras funcionales del castellano** se escribió a mano para el prototipo. Su
   cobertura no está medida contra un corpus externo.
5. **Dónde engancha la guarda.** `feature-state.py:1175-1180` tiene despacho único, pero con AC-07
   (`add_common_state_args`) el acceso a estado cambia de forma. Confirmar que el enganche ve lo que
   AC-03 necesita sin volver a leer estado de producción bajo test.
6. **Si `record-spawn` debe llevar también los campos nuevos.** Esta spec los pide sólo en el cierre.
   Decisión de alcance, no verdad comprobada.
7. **Si la divergencia de `AGENTS.codex.md` fue deliberada** (D-6, AC-16).
8. **El costo de regenerar el digest** (AC-14): `cmd_digest` recorre todos los estados y tres JSONL.
   Se acotó a cierre de fase/turno por la razón de git, pero **el costo no se midió**.
9. **Cómo detecta AC-08 un "cierre disfrazado de apertura"** sin volverse un falso positivo sobre
   aperturas legítimas. El AC nombra el requisito; el mecanismo no está resuelto y puede resultar no
   implementable, en cuyo caso corresponde declararlo como limitación, igual que B5.
10. **El índice `docs/specs/README.md` no se actualizó**: el encargo restringió la escritura a este
    archivo. Falta la fila `| 028 | Narración que enseña | Draft | 2026-08-15 |` antes de
    `USER_APPROVAL`.
