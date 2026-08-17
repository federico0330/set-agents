# ADR-0057 — narración que enseña: campos que obligan (contrato de escritura)

- Estado: Accepted (2026-08-16). Feature 028-narracion-que-ensena, paquete N1
  (`campos-que-obligan`). AC-01..AC-08.

## Contexto

Federico, dueño del repo, ingeniero: *"no quiero que mencione 'hice el fix de PKG-007,
sigue el item A que quedó de spec.md'. […] yo soy ingeniero y muchas veces no le puedo
seguir el estado del proyecto porque no explica."* (`ai/state/decisions-log.jsonl`,
slug `narracion-que-explica-en-vez-de-apuntar`).

`docs/specs/028-narracion-que-ensena/spec.md` mide el defecto sobre las 178 entradas
reales de `narrative-log.jsonl`: 42% de los cierres llevan un identificador pelado en
`tech`, 11.8% en `client` (una regla que ya existía y se viola una de cada ocho veces
sin que nadie lo note), y ninguna capa del CLI valida contenido — sólo presencia de
texto (`tests/test_digest.py:269-276`, `tests/test_harness.py`, ambas prueban que la
DOCTRINA está bien escrita, nunca que una narración PRODUCIDA la cumple).

La primera versión de la guarda (E-1) medía **longitud**: un piso de caracteres. Un
desafío independiente (`SPEC_CHALLENGE`) la rompió con **8 de 9 ataques construidos**,
reimplementando las reglas y corriéndolas — incluido el caso literal que dio origen a
la feature, un espacio en vez de un guión (`PKG 007`). La spec fue enmendada: el
diagnóstico (D-1..D-6) queda intacto, el mecanismo de detección se reemplaza entero.

## Decisión

### 1. Densidad de punteros por cláusula, no longitud (AC-04a, el corazón de la enmienda)

`ai/scripts/narration_lint.py` (nuevo): cuenta los identificadores ("punteros") de
seis familias —`Pn`/`Dn`/`Rn` pelado, compuesto `P2-F01`, `XX-nnn`, separador flexible
(`PKG 007`, `PKG_007`), feature-id `NNN-slug`, archivo suelto sin línea— y los divide
por el número de **cláusulas** (separadores fuertes `. ; : , ( )` y las conjunciones
`y/o/pero/sino/aunque`). Topes: **≤ 0.35** en `client` y en `tech`. Es un **cociente**:
agregar una cláusula de relleno sin contenido no baja la densidad si no hay un punto,
coma o conjunción que la separe de la cláusula con el puntero — sólo una cláusula
REAL, con prosa, diluye el cociente (`narration_lint.py::pointer_density`,
`tests/test_narracion_contrato.py::PointerDensityUnitTests`).

`archivo:línea` (evidencia, ADR-0026) se resta del conteo de punteros en `tech` —es
obligatoria ahí— pero nunca en `learned`/`next`/`why`, donde no puede ser el contenido
único (AC-04b): si al borrarla junto con los punteros el campo queda sin una sola
palabra de prosa, se rechaza.

### 2. `--milestone yes|no`, sin default (AC-02, E-6)

`learned`/`next`/`why` son obligatorios **sólo** cuando el llamador declara
`--milestone yes` — nunca inferido del estado (E-3: el orden narrar-vs-registrar no
está fijado, `transitions.py:129`). Los spawns intra-fase que ADR-0027 decidió no
mostrarle al humano (`orchestrator.md:712`, *"persisted, not narrated"*) siguen
narrando con `--milestone no` y ningún campo nuevo obligatorio — exigir que enseñen
donde nadie los lee fabrica ritual.

### 3. `--alternative`, sólo en dos bifurcaciones genuinas (AC-03, E-3 reescrito)

Obligatorio sólo en `--result blocked` de causa técnica (`--human-decision` lo exime:
la alternativa ahí es del humano) y en `PACKAGE_PLANNING` (declarado por el llamador
vía `--phase`, nunca leído de estado — ver §5). `next_transition`
(`transitions.py:54-129`) **resuelve** el resto de las bifurcaciones que el ternario
de su código sugiere, no las ofrece — la premisa anterior de la spec era falsa y se
retiró. `--alternative none` es legal, con `--why` obligatorio explicando por qué el
camino es único.

### 4. Dos bypasses cerrados (AC-08, E-9)

`--result started` con cualquier campo que sólo tiene sentido en un cierre
(`--milestone`/`--learned`/`--next`/`--why`/`--alternative`) se rechaza como
`CLOSE_DISGUISED_AS_START` — `started` desaparece del digest
(`cli_reporting.py`, filtro `result not in ("started", ...)`), así que un cierre
narrado como apertura no le llega a nadie. **Limitación declarada, no resuelta**: la
detección de "apertura sin su cierre correspondiente al cambiar de fase" (la otra
mitad de AC-08) necesitaría correlacionar llamadas a través del tiempo, y esta guarda
es deliberadamente una función pura de sus propios argumentos (ver §5) — queda fuera,
igual que B5 (spec, sección "No muerde").

`log-quickfix` (`cli_reporting.py::cmd_log_quickfix`) queda **exento con razón
escrita**: su esquema (`summary` solo) no tiene los cuatro contenidos porque no
describe un cierre de PAQUETE — es la acción directa del orquestador fuera de la
máquina de paquetes, y retrofitear `client`/`tech`/`learned`/`next`/`why` ahí sería un
cambio de forma de datos mayor, fuera del alcance aditivo de N1 (spec AC-08 ofrece
esta salida explícitamente: *"entra al mismo contrato o se declara exento con su
razón escrita"*).

### 5. La guarda nunca lee estado (AC-07, E-4)

`log-narrative` gana `add_common_state_args` (mismo parser que cada otro verbo de
escritura), pero **no** lee `ai/state/features/*.json` para decidir nada — el motivo
que la propia AC-07 nombra: `state_path()` es una ruta relativa hardcodeada
(`model.py:199-200`) y la suite corre con `cwd=ROOT`, así que un enganche que leyera
estado leería **producción** durante los tests — la familia exacta de ADR-0051 (027
la reparó para `check-owned-paths.py`; acá se evita de raíz). Todo lo que la guarda
necesita (`--phase`, `--human-decision`) viaja como argumento explícito del llamador.
`--feature-id` pasa a obligatorio sólo al cerrar (`done`/`blocked`) — hoy 11 de 178
entradas son `sin-feature`, 6 de ellas cierres.

### 6. Forma de datos: ausencia de clave es la versión (AC-01, E-15)

`narrative-log.jsonl` es append-only. Los cinco campos nuevos (`milestone`,
`learned`, `next`, `why`, `alternative`) sólo se escriben cuando el llamador los pasó
— nunca `None`/`"-"` como centinela, y no se agrega número de esquema: la ausencia de
clave **es** la versión. Las 178 entradas preexistentes siguen leyéndose sin error
(`tests/test_narracion_contrato.py::GuardCliTests::test_legacy_entry_without_new_keys_still_absent_not_none`).

### 7. El mensaje enseña (AC-06)

`narration_lint.render_rejection`: cada violación es una oración completa — qué
campo, por qué importa (una consecuencia, nunca un código pelado) — y el bloque
siempre termina con una invocación corregida y ejecutable. Un mensaje que sólo dijera
`NARRATION_LINT_FAIL learned=missing` reprueba su propio AC; el desafío independiente
llamó a esta idea *"la mejor de la feature"*.

## Alternativas rechazadas

- **Piso de longitud + solapamiento de vocabulario (versión original).** Rechazada
  por el desafío: 8 de 9 ataques la atraviesan diluyendo el conteo con relleno; el par
  `next`×`why` idénticos carácter por carácter (B7) pasaba el umbral del 70%.
- **Etiquetado gramatical (verbo conjugado + sustantivo no-artefacto).** Prototipado y
  descartado (spec, "No muerde #2"): sin librería estándar de POS-tagging, el proxy
  más cercano (stoplist de artefactos) es otro piso de longitud disfrazado, y el
  ejemplo en inglés de la propia spec lo atraviesa.
- **Inferir `--milestone` del estado.** Rechazada (E-3): reintroduce el
  no-determinismo que la enmienda existe para eliminar.
- **Retrofitear `client`/`tech`/`learned`/`next`/`why` en `log-quickfix`.** Rechazada
  para N1: cambio de forma de datos mayor sobre un verbo con semántica distinta
  (acción directa, no cierre de paquete); ver §4.

## Consecuencias

- `ai/scripts/narration_lint.py` (y su espejo `PROYECTO/ai/scripts/narration_lint.py`)
  es la única fuente de verdad de la guarda — función pura, sin I/O, veintitantas
  reglas declaradas y calibrables (ver "Sin verificar" abajo).
- `log-narrative` rechaza en escritura: ninguna narración que no pase la guarda llega
  a `narrative-log.jsonl`.
- Corpus de nueve ataques (spec, normativo): **8 rojo, B5 verde y declarado**
  (`tests/test_narracion_contrato.py::AttackCorpusTests`).
- **Regresión conocida, fuera de `owned_paths` de N1**:
  `tests/test_digest.py:574-590`
  (`DigestRegenerationCadenceTests::test_log_narrative_alone_never_writes_the_digest`)
  invoca `log-narrative --result done` sin `--milestone` y con `--client "avanzamos"`
  (una sola palabra, ratio de castellano 0.00) — falla con `MILESTONE_REQUIRED` +
  `CLIENT_NOT_SPANISH` tras este cambio. La spec contó "exactamente 4 invocaciones,
  todas en `tests/test_harness.py`"; la medición era incompleta — hay una quinta en
  `tests/test_digest.py`, archivo explícitamente fuera de los `owned_paths` de N1 y
  en la lista "No toques" del encargo. Fix trivial de una línea
  (`"--milestone", "no",` + ajustar `--client` a algo con más de una palabra
  funcional), pero requiere autorización explícita para tocar ese archivo o que N2
  (dueño de `tests/test_digest.py` por AC-16) lo absorba. Reportado, no reparado acá.
- Umbrales (`DENSITY_THRESHOLD=0.35`, `SPANISH_RATIO_THRESHOLD=0.25`, topes de
  longitud 400/240) son un primer corte contra un corpus de nueve ataques y una
  decena de ejemplos buenos — calibrables, no contratos (spec, "Sin verificar #1").

## Evidencia

`docs/specs/028-narracion-que-ensena/evidence/N1-implementer.md` — tabla AC → cambio
(`archivo:línea`) → prueba; los nueve ataques con su salida; el mensaje de rechazo
pegado literal; las mordidas rojo→revertido→verde.
