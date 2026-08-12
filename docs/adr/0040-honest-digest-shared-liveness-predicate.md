# ADR-0040 — Tablero honesto: un predicado compartido de "feature viva", nunca reimplementado por sitio

- Estado: Accepted (2026-08-12). Feature 020-honest-dashboard, PKG-1 (`P1-digest-no-esconde`) y
  PKG-2 (`P2-anclas-verificables`) — misma decisión, segunda mitad: el tablero deja de mentir tanto
  por lo que esconde (PKG-1) como por lo que cita mal (PKG-2).

## Contexto

`docs/notas/BUENOS-DIAS.md` (el digest matinal, ADR-0027) y `docs/notas/00 - Proyecto.md` (el hub,
`_hub_body`) reimplementaban, cada uno por su cuenta, la misma pregunta — "¿esta feature sigue
necesitando atención?" — y las dos implementaciones estaban mal de la misma forma:

- `cli_reporting.py:194` (`cmd_digest`): `active = [d for d in states if not d.get("final_state")]`
- `feature-state.py`, `_hub_body` (~`:199`): `if data.get("final_state"): continue`

Ambas tratan **cualquier** `final_state` truthy como "ya no importa". Pero `TERMINAL = {"DONE",
"BLOCKED"}` (`model.py:51`) tiene dos miembros, no uno, y `block_with_reason` (`cli_lifecycle.py:396-402`)
asigna `final_state = "BLOCKED"` exactamente igual que una feature terminada asigna `"DONE"`. El
resultado medido en este repo el 2026-08-11: `002-adaptive-pi-orchestration` (bloqueada desde
2026-07-24) y `011-quota-failover` (bloqueada desde 2026-07-30), las dos con
`HUMAN_DECISION_REQUIRED`, no aparecían en el digest que Federico lee todas las mañanas, y tampoco en
la sección "Qué falta" del hub (aunque sí figuraban, con etiqueta `BLOCKED`, en la sección "Features"
del propio hub — la mitad del artefacto sabía que estaban bloqueadas, la otra mitad las trataba como
cerradas).

El defecto se duplicó **porque no había un solo lugar que respondiera la pregunta**. Cada artefacto
derivado nuevo que alguien agregue (y ya hay un tercer consumidor, `cmd_status`, AC-04 de esta misma
feature) iba a copiar el mismo filtro truthy si nadie lo centralizaba primero.

## Decisión

### 1. Un predicado, un lugar: `feature_state_lib/model.py`

```python
STALE_THRESHOLD_DAYS = 7

def feature_is_live(data) -> bool:
    return data.get("final_state") != "DONE"
```

Vive en `model.py`, no en `render_notes.py` ni en `cli_reporting.py`, por la misma razón que
`cli_integration.py:1-13` documenta para `integration_ready`: `model.py` no importa nada dentro de
`feature_state_lib/` (es la base del grafo de imports), así que cualquier módulo puede consumirlo sin
riesgo de ciclo. Los tres consumidores (`cli_reporting.cmd_digest`, `feature-state._hub_body`,
`cli_lifecycle.cmd_status`) ya hacen `from feature_state_lib import model`.

La comparación es **exacta** contra `"DONE"` (no truthy, no case-insensitive): `final_state` es un
campo de vocabulario cerrado — todo el código real que lo escribe (`cmd_transition`, que valida
`to_phase` contra `PHASES`, todo mayúsculas; `block_with_reason`/`fail-task`, que escriben literalmente
`"BLOCKED"`) solo produce `"DONE"` o `"BLOCKED"`. Una feature bloqueada sigue siendo "viva" para este
predicado — necesita más atención humana que una en curso, no menos.

Junto al predicado, tres funciones más pequeñas, todas en `model.py`, todas derivadas de los mismos
campos que ya existen (`data["blockers"]`, `data["updated_at"]`) sin inventar un campo nuevo:

```python
def open_blocker(data) -> dict | None: ...   # el ÚLTIMO blocker sin resolved_at, o None
def days_since(timestamp) -> int | None: ... # días enteros desde un ISO timestamp hasta ahora (UTC)
def blocked_days(data) -> int | None: ...    # days_since(open_blocker(data)["at"]) si hay uno
def stale_days(data) -> int | None: ...      # solo si feature_is_live Y open_blocker es None
def feature_is_stale(data) -> bool: ...      # stale_days(data) is not None and >= STALE_THRESHOLD_DAYS
```

`open_blocker` devuelve el **último** elemento de `blockers[]` sin `resolved_at` — nunca el primero, y
nunca `updated_at` a ciegas. `002` tiene dos entradas (`2026-07-24T15:57` resuelta,
`2026-07-24T16:16` vigente); contar desde `updated_at` habría dado una fecha distinta a "desde cuándo
espera una decisión", que es la pregunta que AC-01 responde.

`stale_days` (y por lo tanto `feature_is_stale`) incorpora el "no bloqueada" en su propia definición
en vez de dejarlo como un chequeo que cada llamador repite — otra forma del mismo principio de este
ADR: la exención de las bloqueadas (AC-03) no es un `if` que cada artefacto vuelva a escribir, es parte
de lo que "estancada" significa.

### 2. El umbral es una constante nombrada única, no un número repetido

`STALE_THRESHOLD_DAYS = 7` vive junto al predicado, en `model.py`. AC-01 (días de bloqueo) y AC-03
(marca de estancada) leen el mismo valor a través de `stale_days`/`feature_is_stale`; no hay un
segundo `7` escrito en otro archivo. Es un supuesto de producto, no una verdad medida — documentado
como limitación conocida en la spec (SC-10): cambiarlo es editar una línea, nunca buscar y reemplazar.

### 3. "Necesita tu decisión" — la sección nueva, y por qué el tope es dos menciones

`cmd_digest` gana `## Necesita tu decisión`, la PRIMERA sección del documento (antes de "Qué quedó
listo"): itera **todos** los `states` (no el subconjunto vivo — una feature con un blocker sin
resolver es relevante *independientemente* de su `final_state`, aunque en la práctica de hoy eso solo
puede ser `BLOCKED`) buscando `open_blocker(data)`, y por cada una imprime `feature_id`, la razón
acortada por `_short`, y `days_since(blocker["at"])`. Es una sección **fija**: si no hay ninguna,
dice explícitamente que no hay nada pendiente — una sección que aparece y desaparece según el estado
se lee como ruido; una fija se lee como tablero (ADR-0027 ya establece este principio para "Qué
falta").

Con AC-02 ampliando el conjunto "vivo" para incluir las bloqueadas, esas mismas features
también calificarían para "Qué se está haciendo" (listado de vivas) y para "Qué falta"
(vía `_pending_bits`, que ya sabe emitir `⛔ bloqueo: ...`). Nombrarlas en las tres secciones más el
titular de "Necesita tu decisión" es la misma clase de ruido que esta feature vino a arreglar, solo
que desplazada de "invisible" a "redundante". La partición fija:

| Sección | Conjunto | Contenido para una bloqueada |
|---|---|---|
| `## Necesita tu decisión` | todos los `states` con `open_blocker` | titular: razón + días |
| `## Qué se está haciendo` | vivas SIN `open_blocker` | **ausente** (no es "trabajo en curso") |
| `## Qué falta` | vivas (con y sin blocker) | bit `⛔ bloqueo: ...` vía `_pending_bits` |

Dos menciones por feature bloqueada, nunca cuatro. Una feature viva no bloqueada que además está
estancada (`feature_is_stale`) gana una marca en su línea de "Qué se está haciendo" con los días —
esa es su única mención extra, y son mutuamente excluyentes con el caso bloqueado por construcción
(`stale_days` ya excluye a las bloqueadas).

**Precisión (repair del review independiente de PKG-1, F-01):** `_pending_bits` puede devolver más
de un bit para una misma feature — el `⛔ bloqueo: ...`, más "N hallazgos abiertos" y/o "tareas
pendientes en <paquete>: ..." si el paquete bloqueado los tiene (el caso real de `002` y `011`: cada
una llegó a "Qué falta" con **dos** bits de `_pending_bits`, no uno, lo que daba tres menciones
totales — titular + bloqueo + el bit informativo — hasta que se corrigió). El tope de dos se sostiene
así: en `cmd_digest`, para toda feature que ya tiene titular en "Necesita tu decisión"
(`open_blocker(data) is not None`), el bit `⛔ bloqueo: ...` de "Qué falta" se omite —es la
duplicación literal del titular, mismo texto y mismo truncado, cero información nueva— y **todos los
demás bits se conservan**, porque sí aportan información que el titular no tiene. `_hub_body` no
aplica este filtro (no tiene una sección "Necesita tu decisión" de la que el bloqueo sea duplicado),
así que en el hub el bit `⛔ bloqueo: ...` de "Qué falta" sigue apareciendo sin filtrar.

### 4. `_hub_body` y `cmd_status` consumen el mismo predicado, sin reimplementarlo

`_hub_body` cambia su único filtro (`if data.get("final_state"): continue` → `if not
model.feature_is_live(data): continue`) delante del loop que llama `_pending_bits`. Nada más se toca:
la sección "Features" del hub ya nombraba las bloqueadas con su etiqueta; el bug estaba solo en que
"Qué falta" las excluía después de que "Features" ya las había mostrado.

`cmd_status` (per-feature, `cli_lifecycle.py:188`) suma `blocked_days`/`stale_days` calculados con
`model.blocked_days`/`model.stale_days` a su salida JSON — nunca un agregado global que el comando no
tiene (la redacción original de AC-04 lo pedía; se corrigió durante el challenge de la spec porque no
era verificable). Es aditivo: `output_state` (la función que comparten ~20 comandos mutadores) no se
toca, solo el cuerpo propio de `cmd_status`, así que ningún otro comando cambia su forma de salida.

### 5. PKG-2 — `check-anchors`: las anclas `file:line` de `docs/modules/` dejan de derivar sin red

D-2 de la spec (ver también el Contexto de esta ADR): las cinco secciones sembradas a mano de
`docs/modules/*.md` citan símbolos con `file:line`, y esas citas derivan en silencio cuando el
archivo real crece — `set_agents_app.py:2510` decía ser `main()`; el `main()` real está **742 líneas**
más abajo. Ningún review de paquete podía verlo (cada uno mira su propio diff); solo apareció cuando
alguien corrió a mano el chequeo que `/explicar` promete. `feature_state_lib/check_anchors.py` es la
red: un comando read-only, `check-anchors [--module <slug>]`, que reporta cada ancla rota con su
archivo, su línea y por qué.

**Gramática, dos formas, casi 1:1 en los docs de hoy** (cubrir solo la obvia daría `rc=0` verificando
la mitad, la misma clase de mentira que esta feature ataca):

1. **completa** — un solo token entre backticks, `basename.ext:N` o `basename.ext:N-M`
   (`render_notes.py:51`).
2. **abreviada** — `` `:N` `` suelta, resuelta contra **el último archivo nombrado en el mismo ítem de
   lista o párrafo** (complete-form o una mención bare como `` `render_notes.py` ``). El contexto se
   resetea en cada línea en blanco, encabezado, o bullet nuevo (`- `) — nunca cruza de un ítem a otro.
   Una `` `:N` `` sin archivo nombrado antes en el mismo ítem se reporta **no resoluble**, nunca se
   saltea en silencio.

Un solo regex por forma (`check_anchors.py:56-59`), diseñado contra los falsos positivos reales del
repo: exige que la parte de archivo termine en una extensión corta (≤4 caracteres alfanuméricos), lo
que descarta `localhost:8080`/`12:30`/`http://x:80` (sin punto en la parte de archivo) y, como efecto
secundario deliberado, también descarta citas estilo `módulo.símbolo` (p. ej. `cli_reporting.cmd_digest`,
extensión "cmd_digest", 10 caracteres) que de otro modo se confundirían con un nombre de archivo real.

**Resolución de archivo, acotada al módulo que se chequea (bloqueante, spec-challenge SC-01):** un
ancla sin ruta completa se resuelve por basename **solo dentro de los `paths` del módulo dueño del doc
que se está chequeando** (`modules.toml`, expandidos a archivos reales en disco vía `glob`) — nunca por
búsqueda global, porque `feature_state_lib/*.py` está duplicado byte a byte en cinco árboles y una
búsqueda global sería no determinística. Cero matches, o más de uno, dentro de esos `paths` es en sí
mismo un ancla rota reportable.

**Consecuencia no anticipada, corregida en AC-10 en vez de forzada en el checker:** esta regla acotada
hace que una cita **entre módulos** (un doc de un módulo citando la línea de un archivo que pertenece a
otro) sea, por diseño, no verificable como ancla — expandir el alcance rompería el determinismo que
SC-01 exige, y ensanchar el `paths` de un módulo para que abarque archivos de otro violaría la
partición de ADR-0036 (fuera de alcance de este paquete). Dos citas reales de hoy caían acá
(`routing.md` citando `set_agents_app.py`, dueño del módulo `consola`; `narracion-notas.md` citando
`feature-state.py`/`cli_reporting.py`, dueños del módulo `estado`) — AC-10 las corrigió bajando el
número de línea y dejando el puntero al módulo dueño en prosa, la misma postura de "recortá y dejá
constancia" que AC-08 usa en todos lados.

**Verificación semántica, acotada a propósito (AC-08):** se compara el identificador como texto plano
contra una ventana chica (±2 líneas) del archivo destino, y **solo** cuando un símbolo entre backticks
viene inmediatamente adyacente al ancla, en la misma línea, sin nada más que espacio en blanco entre
ambos — el caso insignia, `` `set_agents_app.py:2510` `main()` ``. Rangos, comodines (`cmd_route_*`,
que ni siquiera puede ser un identificador válido) y símbolos separados del ancla por prosa
(`` `check_transition` (`:17` ``, con un `(` de por medio) reciben solo resolución + chequeo de rango.
Nada de parsear Python — es una comparación de texto, con las limitaciones de una comparación de
texto: una coincidencia casual dentro de un docstring cercano (un caso real, documentado en la
evidencia de P2) puede hacer pasar una línea que en realidad está mal.

**Cobertura real, medida, no solo posible (repair del review independiente, F-02):** la condición de
adyacencia de arriba es estricta a propósito, y eso tiene un costo medido, no solo teórico. Sobre los
5 módulos reales de hoy, después de las correcciones de AC-10 (`rc=0`, 38 anclas): **solo 12 de 38
(32%)** reciben la verificación semántica activa — 10 de las 18 completas, 2 de las 20 abreviadas
(medido corriendo `_scan_doc` directo contra `docs/modules/*.md` y contando cuántas entradas traen la
clave `symbol`; ver `docs/specs/020-honest-dashboard/evidence/P2-repair.md` para el comando exacto).
Las otras 26 pasan el chequeo de rango y nada más: un "es", un "define", o simplemente el hecho de que
la forma abreviada casi nunca trae backticks pegados apaga la verificación en silencio (ver el
docstring de `_adjacent_symbol` en `check_anchors.py`, ampliado en el mismo repair). `rc=0` de
`check-anchors` hoy significa "ninguna línea está fuera de rango y el 32% de los símbolos adyacentes
coincide en texto", no "la documentación no miente" en sentido semántico completo — la prueba concreta
es `` `foo.py:8` es `alpha()` `` con la línea 8 real diciendo `beta`: pasa (`ok=True`) porque "es" apaga
la adyacencia.

**Magnitud de la ventana ±2, medida (repair F-03, cifra corregida por el delta-review, F-05):** sobre
las 12 anclas con chequeo activo, simulando un corrimiento de ±1 a ±20 líneas alrededor de **la línea
real citada en el archivo destino** (40 posiciones por ancla, 479 evaluables de 480 posibles — una cae
fuera del archivo real y se descarta —, usando `_semantic_check` real, no una reimplementación) —
**75 de 479 (≈15.7%)** posiciones corridas siguen pasando por coincidencia textual. No hay ninguna
ancla por debajo del 10%: el mínimo medido es **4/40 (10%)** (`oc_permissions`, `generate_pi_prompts`,
`validate_pi_target`, `write_note`, `notes_root`, `render_status`) y el máximo es **10/40 (25%)**
(`main`@consola.md:3252, `validate`@generacion-arboles.md:678) — es decir, la ancla peor cubierta pasa
**una posición corrida de cada cuatro**. Tabla completa (ancla, línea destino real, pasan/probadas):
`main`@consola:3252 10/40, `cmd_status`@consola:1089 9/40, `main`@generate:716 7/39 (una posición cae
fuera del archivo), `load_roles`@generate:55 6/40, `oc_permissions`@generate:129 4/40,
`generate_pi_prompts`@generate:376 4/40, `validate_pi_target`@generate:657 4/40,
`validate`@generate:678 10/40, `merge_note`@narracion-notas:51 9/40, `write_note`@narracion-notas:67
4/40, `notes_root`@narracion-notas:37 4/40, `render_status`@narracion-notas:70 4/40. No es el caso
aislado que documentaba la evidencia original de P2 (`generate.py:669`→`validate`): es una propiedad
estructural de comparar texto en una ventana fija, presente en **toda** ancla medida, no en un
subconjunto — y en proporción alta, no baja. Dato para quien algún día evalúe convertir esto en gate:
el `rc=0` de hoy no certifica ausencia de drift, certifica ausencia de drift **detectable por esta
ventana**, con un margen de falso negativo medido de **15.7% agregado, 10%-25% por ancla** — no un
margen bajo.

**Nota de corrección (F-05, delta-review, 2026-08-12):** la primera versión de esta medición
(**17/480 ≈3.5%**, repair de P2, ver `docs/specs/020-honest-dashboard/evidence/P2-repair.md` §F-03 y
la nota que agrega este mismo repair) tenía **un bug de medición real, no una discrepancia de
metodología**. El script usaba `r["line"]` como línea del archivo destino, pero esa clave
(`check_anchors.py:173`, dentro de `_build_entry`) es **la fila del ancla dentro del `.md`**, no la
línea citada en el archivo destino — esa existe internamente como `target_start`
(`check_anchors.py:178`) pero **nunca se guarda** en el dict que `_scan_doc`/`_build_entry` devuelven.
El script terminó simulando corrimientos alrededor de, por ejemplo, la fila 26 de `consola.md` (la
línea del ancla dentro del Markdown) en vez de la línea 3252 de `set_agents_app.py` (la línea que esa
ancla realmente cita) — midiendo drift sobre una zona de archivo sin relación con `main()`. Corregido
extrayendo la línea real desde `r["raw"]` (regex `` :(\d+)`$ `` sobre el texto entre backticks, seguro
porque toda entrada con `symbol` activo es de línea única por construcción — `_build_entry` nunca
corre el chequeo semántico sobre un rango). El número corregido (75/479, 15.7%) reproduce casi exacto
el que citó el reviewer original ("entre 4 y 10 de las 40 posiciones, 10%-25%") — la nota de honestidad
del repair anterior, que asumía una "metodología de simulación distinta" del reviewer para explicar la
discrepancia, estaba equivocada: no era una diferencia de método, era el bug de arriba. Ver
`docs/specs/020-honest-dashboard/evidence/P2-repair-2.md` para el script corregido completo y su salida
literal.

**`sync-notes` nunca falla por esto (AC-09):** mismo contrato never-raises que `render_notes.py`
(`render_notes.py:281-285`, `RENDER_FAILURE_LOG`) — `check-anchors` corre al final de `cmd_sync_notes`
dentro de un `try/except Exception` que solo imprime por stderr. `check-anchors` **no es gate
bloqueante de ninguna fase** (no-goal explícito de la spec): avisa, no traba.

## Alternativas rechazadas

- **Reimplementar el filtro una tercera vez dentro de `cmd_status`.** Es exactamente el defecto que
  esta ADR existe para cerrar — la duplicación es la causa raíz, no un detalle de implementación.
- **Poner el predicado en `render_notes.py`.** Ese módulo ya importa de `model.py` y de
  `transitions.py`; ponerlo ahí habría dejado a `cli_lifecycle.py` (que no importa `render_notes.py`)
  sin acceso directo, forzando un import cruzado nuevo en el grafo que `cli_integration.py:1-13` ya
  describe como cuidadosamente acíclico.
- **Comparación truthy pero excluyendo `"BLOCKED"` con un segundo caso especial.** Funcionalmente
  equivalente a `!= "DONE"` para el vocabulario cerrado actual, pero menos legible como afirmación
  positiva ("solo lo genuinamente terminado se excluye") y más frágil si `TERMINAL` ganara un tercer
  valor algún día.
- **Inventar un campo `paused`/`estado_pausado` para que `006`/`010` (esperando impacto de módulo, no
  realmente estancadas) no se marquen igual que una feature abandonada por accidente.** Fuera de
  alcance a propósito (spec, "Limitaciones conocidas" SC-11): el schema no distingue las dos causas
  hoy, y para una feature sobre honestidad, sobre-marcar es el default más seguro — queda nombrado
  como limitación, no resuelto con un campo nuevo sin AC que lo pida.
- **(PKG-2) Búsqueda global de basename en vez de acotada al módulo.** Resolvería las dos citas
  cruzadas de módulo sin recortar prosa, pero reintroduce exactamente el no-determinismo que SC-01
  existe para prohibir: `feature_state_lib/*.py` está duplicado byte a byte en cinco árboles, y
  "encontrado en alguno de los cinco" no es una respuesta verificable.
- **(PKG-2) Ensanchar `paths` de un módulo para que alcance archivos de otro, solo para que una cita
  cruzada resuelva.** Viola la partición de ownership de ADR-0036 (`modules.toml` describe quién es
  dueño estructural de qué, no "qué le conviene citar a quién") y está fuera del alcance explícito de
  este paquete (no tocar el schema de `docs/modules/` ni esa partición).
- **(PKG-2) Parsear Python (AST) para la verificación semántica de AC-08.** El spec-challenger lo
  marcó como el punto donde este paquete más fácil se convierte en un proyecto disfrazado. Una
  comparación de texto en una ventana chica, acotada a la adyacencia inmediata, cubre el defecto
  insignia con un regex, no con un parser — al costo aceptado de algún falso negativo por coincidencia
  textual (documentado, no escondido).
- **(PKG-2) Convertir `check-anchors` en gate bloqueante de alguna fase.** No-goal explícito de la
  spec: "avisa; no traba". Convertirlo en gate es una decisión de producto de Federico, no algo que
  este paquete decida unilateralmente.

## Consecuencias

- `docs/notas/BUENOS-DIAS.md` nombra toda feature bloqueada con su razón y sus días, en una sección
  fija que nunca desaparece en silencio.
- `docs/notas/00 - Proyecto.md` dejó de contradecirse entre su sección "Features" (que sí marcaba
  `BLOCKED`) y su sección "Qué falta" (que las omitía).
- `cmd_status` cuenta la misma verdad que el digest y el hub — ningún comando puede decir una cosa
  mientras el informe matinal dice otra.
- `feature_state_lib/` tiene copias byte-idénticas en `ai/scripts/`, los árboles generados de
  `Global/opencode`, `Global/claude-code`, `Global/codex` (vía `./build.sh`, `generate.py`) y
  `PROYECTO/ai/scripts/` (copiado a mano, sin generador propio, verificado por
  `./build.sh --check` para `feature-state.py`/`check-owned-paths.py` y por convención de paridad
  para el resto del paquete) — todas requieren el mismo cambio.
- Sigue sin resolverse (a propósito, fuera de alcance de este ADR) **por qué** `002` y `011` están
  bloqueadas: esta feature hace visible el bloqueo, no lo levanta.
- (PKG-2) `python3 ai/scripts/feature-state.py check-anchors` devuelve `rc=0` sobre los cinco módulos
  sembrados hoy; las anclas rotas encontradas (drift real de 019 más una regresión nueva introducida
  por el propio PKG-1 en `model.py`) quedaron corregidas.
- (PKG-2, repair F-02) Ese `rc=0` cubre chequeo de rango en las 38 anclas y chequeo semántico activo
  en solo 12 (32%, ver sección 5) — no "toda cita verificada de punta a punta". Y esa ventana semántica
  tiene un margen de falso negativo medido de **15.7% agregado, 10%-25% por ancla, ninguna por debajo
  del 10%** (sección 5, F-03, cifra corregida por F-05 — la versión original, 3.5%, tenía un bug de
  medición): `rc=0` es una garantía parcial, y el margen que deja sin cubrir no es chico.
- (PKG-2) Dos citas entre módulos (`routing.md`→`consola`, `narracion-notas.md`→`estado`) dejaron de
  citar una línea que el checker no puede verificar por diseño, y en su lugar nombran el módulo dueño
  en prosa — ninguna información se perdió, solo dejó de fingir precisión que la herramienta no puede
  respaldar.
- (PKG-2) `sync-notes` nunca falla por `check-anchors`: un verificador roto, o anclas rotas, solo
  producen una advertencia por stderr (`ANCHORS_WARN`/`ANCHORS_CHECK_FAILED`), nunca abortan la
  consolidación de notas.
