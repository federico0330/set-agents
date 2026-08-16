# ADR-0056 — Vault en todo spawn: cierra el `If` que ADR-0012 dejó abierto del lado del spawn

- Estado: Accepted (2026-08-16). Feature `025-consola-minima-y-flexible`, paquete D5
  (`vault-en-todo-spawn`), AC-12.
- **Amends `docs/adr/0012-mandatory-vault.md`.** No lo reemplaza ni lo supersede: ADR-0012 resolvió el
  lado del *orquestador* del vault obligatorio (registry, migración merge-aware, `--vault-doctor`); este
  ADR cierra el lado del *spawn*, que ADR-0012 nunca tocó — su propio `Contexto` ya describía la falla
  original ("nothing reads the vault back into the orchestrator's context") y esa frase seguía siendo
  literalmente cierta para cada agente *delegado*, no solo para el orquestador, hasta este paquete.
- Cada cita `file:line` de abajo fue verificada contra el árbol de trabajo el 2026-08-16, antes y después
  del cambio.

## Contexto

### Lo que ADR-0012 cerró y lo que dejó abierto

ADR-0012 hizo obligatorio el vault del lado del *registro* (DEC-6, `.set-agentes-vault.json`) y de la
*migración* (merge-aware, backup/rollback). No tocó cómo un agente *delegado* — el que efectivamente hace
el trabajo — recibe ese contenido. La única instrucción existente es condicional, en
`Global/_canonical/agents/orchestrator.md:138`: *"If a vault is linked (`set-agents --vault-link`), run
`set-agents --context [--project DIR] --json`"*. Ese `If` es voluntario: depende de que (a) haya vault
linkeado, (b) el orquestador se acuerde de correr `--context`, y (c) pegue la salida en el texto de la
tarea de CADA spawn. Medido antes de este paquete:

```
grep -c "vault" ai/scripts/claude_code_spawn.py   -> 0
grep -c "vault" ai/scripts/codex_spawn.py         -> 0
grep -c "vault" ai/scripts/opencode_spawn.py      -> 0
grep -c "vault" ai/scripts/set_agents_spawn.py    -> 0
```

Cero. Ningún agente spawneado recibía el vault por construcción; dependía enteramente de que el
orquestador lo pegara a mano en el texto de la tarea.

### El primitivo de fencing existente, y por qué no alcanzaba tal cual

`ai/scripts/context_pack.py`'s `_mark_untrusted` (usado por `cmd_context`, `set_agents_app.py:3076-3123`)
envuelve cada campo (`hub`/`company`/`project`/`pending`) con un marcador fijo
(`<<<UNTRUSTED VAULT CONTENT ...>>>` / `<<<END UNTRUSTED VAULT CONTENT>>>`) y neutraliza ocurrencias
*literales* de ese marcador dentro del cuerpo (DR-002, 005-P2 delta review) — defiende contra un actor
con acceso de escritura al vault que forje un cierre falso. Una auditoría de este paquete (025/D5) demostró
que esa defensa por `str.replace()` exacto deja pasar *look-alikes de formato*: espacio interno extra,
minúsculas, el marcador partido por un salto de línea, o un carácter de ancho cero intercalado entre sus
letras — ninguno de esos es el substring exacto, así que `.replace()` nunca los toca. Contra `cmd_context`
esto ya era una debilidad real (una nota del vault puede escribir cualquiera de esas variantes). AC-12
multiplica la superficie por cuatro (una llamada por turno → una llamada por spawn, en cuatro runtimes),
así que el mismo defecto ahora se ejecuta cuatro veces más.

## Decisión

### DEC-1 — Los cuatro spawners fetchean el vault, no el orquestador a mano

`ai/scripts/claude_code_spawn.py`, `codex_spawn.py`, `opencode_spawn.py` y `set_agents_spawn.py` ganan
cada uno su propia `_fetch_vault_block(cwd)`: un subproceso a
`python3 set_agents_app.py --context --json --project <cwd>` — el MISMO canal sancionado que ya usa el
orquestador (`coord_policy.py:76`, la "THIRD sanctioned channel"), nunca un segundo mecanismo de
descubrimiento de vault. Se descartó reimplementar `find_vault` en proceso: `set_agents_app.py` importa
`set_agents_spawn` en su propio nivel de módulo (`set_agents_app.py:37`), así que un `import set_agents_app`
desde dentro de `set_agents_spawn.py` sería un ciclo directo, garantizado — no solo teórico — bajo
`tests/test_harness.py`'s `_import()`. Los otros tres spawners son, por arquitectura deliberada de este
mismo feature ("never a call into" un módulo hermano, ver el propio docstring de `claude_code_spawn.py`),
módulos separados entre sí: `_fetch_vault_block` se duplica una vez por archivo (mismo patrón que
`_redact`/`_run_app_cli`/`SpawnError`, ya duplicados así en los cuatro), no se comparte vía import.

El fetch se ejecuta en los **puntos de entrada de producción reales** — `dispatch_writer`/`dispatch_review`
(y `dispatch_simulate` donde existe: `codex_spawn.py`, `opencode_spawn.py`) para los tres runtimes CLI, y
`route_and_spawn` para pi — **nunca dentro del primitivo `spawn()` de bajo nivel**. Los tres módulos
documentan `spawn()` como un primitivo reusable por un "future package's own tests" o un llamador directo,
no la vía de producción; `main()` nunca lo llama directo, siempre a través de esos puntos con lifecycle
(grepeado exhaustivamente, ver evidencia). Esto mantiene ~90 tests existentes que llaman `spawn()` (los
cuatro módulos) sin tocar el nuevo fetch — verificado: la suite focal corre en 0.4-7s, sin overhead
perceptible.

### DEC-2 — Endurecer `_mark_untrusted` con nonce por invocación, no un segundo esquema

`context_pack._mark_untrusted` deja de envolver con el string fijo `_UNTRUSTED_OPEN`/`_UNTRUSTED_CLOSE`
completo y en su lugar genera, en cada llamada, `secrets.token_hex(8)` (64 bits) y arma
`<<<UNTRUSTED VAULT CONTENT-{nonce} -- ...>>>` / `<<<END UNTRUSTED VAULT CONTENT-{nonce}>>>`. Antes de
envolver, un regex case-insensitive y tolerante a espacios (`_MARKER_LOOKALIKE_RE`) neutraliza CUALQUIER
substring con forma de marcador — literal, look-alike, o con un nonce adivinado — y los caracteres de
ancho cero conocidos se eliminan primero. Esto no es un segundo esquema de fencing: es el **mismo**
primitivo (`_mark_untrusted`, un solo lugar, reusado tal cual por `cmd_context` Y por los cuatro
`compose_task`) endurecido en su única implementación. `set_agents_app.py:3069-3073` importa
`_UNTRUSTED_OPEN`/`_UNTRUSTED_CLOSE` por nombre — no se toca ese archivo (fuera de ownership de este
paquete) — así que esos dos nombres se conservan como los PREFIJOS estáticos que todo marcador real sigue
empezando/terminando con, nunca el string completo.

**Por qué nonce y no otra alternativa**: este mismo repo ya tiene, revisado y aprobado (SEC-004,
`claude_code_spawn.py:320-329` y sus gemelos en `codex_spawn.py`/`opencode_spawn.py`), un fence por nonce
para `supplementary` (el diff bajo revisión) — la MISMA amenaza (contenido externo no confiable, delante
de la tarea, que podría forjar su propio cierre). Reusar esa forma para el vault, en el ÚNICO lugar donde
vive el fencing del vault, es consistencia con un precedente ya deliberado y probado en este código, no una
invención nueva.

### DEC-3 — El bloque va delante de todo, vía el `supplementary`/`compose_task` existente cuando aplica

`compose_task(task, supplementary=None, vault_block=None)` (las tres lanes CLI) y `spawn(..., vault_block=None)`
(pi lane, que no tiene concepto de `supplementary` — el `task` es el positional final de `pi`) ganan un
parámetro nuevo, `None` por defecto, con el contrato explícito de que el valor de retorno es
**byte-idéntico** al de antes de ADR-0056 cuando se omite. `vault_block`, si está presente, se antepone a
TODO lo demás (incluso antes del bloque `<<<DATA:{nonce}>>>` del diff bajo revisión) — la posición más
privilegiada, tal como pide AC-12. Se decidió NO mezclarlo dentro del parámetro `supplementary` existente:
`tests/test_routing.py::test_dispatch_review_never_touches_the_routing_store` pinnea
`spawn_mock.call_args.kwargs.get("supplementary") == "diff content here"` exacto — mutarlo hubiera roto
un test que no es propiedad de este paquete.

### DEC-4 — "Obligatorio" nunca es "falla cerrado"

`_fetch_vault_block` nunca lanza. Sin vault, subproceso caído, timeout (10s, generoso frente a un vault
sincronizado por Syncthing que puede colgarse), o salida no parseable: todos degradan a `None`, y el spawn
compone y sale exactamente como si `vault_block` nunca hubiera existido — nunca un nuevo modo de falla
`VAULT_NOT_FOUND` a nivel de spawn. Esto es deliberado: un spawn que abortara sin vault rompería cada
proyecto sin vault linkeado, este propio repo incluido en cualquier corrida donde no esté linkeado.

### DEC-5 — Cacheado por proceso, no persistido entre invocaciones

Cada módulo mantiene un dict `_vault_block_cache` keyeado por el cwd resuelto. Medido (tres corridas,
`python3 ai/scripts/set_agents_app.py --context --json`): 150-225ms por invocación real (arranque de
Python + import de `set_agents_app.py`), instantáneo en cache-hit. En producción cada `main()` corre en su
propio subproceso por spawn — el cache solo ahorra dentro de una misma invocación (el reintento de
quota-exhausted, que sí reusa `vault_block` ya fetcheado). Cachear en disco entre invocaciones queda fuera
de este paquete (no lo pidió el AC; el costo medido es aceptable frente al tiempo real de una llamada a
un LLM).

## Límite conocido, documentado explícitamente (no barrido bajo la alfombra)

**El lane pi mete el bloque del vault en argv, no en stdin.** Los otros tres spawners entregan la tarea
por STDIN, nunca como token de argv (`claude_code_spawn.py:24-26,103`). El lane pi es arquitectónicamente
distinto: `task` YA era, antes de este paquete, el positional final del argv de `pi` (`set_agents_spawn.py`,
SEC-A01 documenta exactamente este riesgo para el texto de la tarea). `vault_block` se antepone al MISMO
`task` string que ya viajaba así — no se abre un canal nuevo, se reusa el que ya existía. Esto es visible
vía `/proc/<pid>/cmdline` (exposición local, no de red) y está acotado por los mismos topes que ya existen
en `cmd_context` (`CONTEXT_BYTE_CAP=4000` + `CONTEXT_SECTION_BYTE_CAP=2000` por campo, ~14 KB en el peor
caso con los cuatro campos), muy por debajo de `MAX_ARG_STRLEN` (128 KiB en Linux) — pero el margen de
seguridad es menor que en las otras tres lanes. Aceptado como límite existente de la arquitectura del CLI
`pi` (que no documenta un modo stdin), no una regresión que este paquete introduce.

## Alcance del vault inyectado

Se inyecta el bloque `{hub, company, project, pending}` completo que `cmd_context` ya produce — no un
índice ni una sección recortada. Se consideró acotar (un índice, o solo `pending`) para reducir superficie,
pero el AC-18 fija ese esquema JSON como el contrato de `--context`, y `cmd_context` ya aplica sus propios
topes de bytes por campo; recortarlo más en el punto de consumo sería una tercera fuente de verdad sobre
qué parte del vault es relevante, divergiendo del contrato que el orquestador ya usa. El techo medido
(~14 KB en el peor caso) es aceptable frente al tamaño típico de un prompt de rol.

## Consecuencias

- Los cuatro spawners quedan con `vault` como término real en su código (antes: cero ocurrencias) —
  `grep -rn "vault" ai/scripts/*_spawn.py | wc -l` pasa de 0 a un número positivo, verificado en la
  evidencia de este paquete.
- `cmd_context` (el llamado del orquestador, no solo el de los spawns) se beneficia igual del
  endurecimiento de `_mark_untrusted` — un solo primitivo, un solo lugar donde arreglarlo.
- `tests/test_harness.py` gana un nuevo bloque de tests (uno por spawner, sensible a que SU wiring propio
  se quite; un test de fencing con payload hostil real, incluyendo los look-alikes que motivaron DEC-2; dos
  tests de degradación; uno de contención de path heredada de SEC-002/003).
- El lane pi acumula el límite conocido de la sección anterior — candidato a paquete futuro si algún día
  `pi`'s propio CLI gana un modo stdin.

## Alternativas descartadas

- **Reusar `_mark_untrusted` tal cual (marcador fijo).** Descartado: la auditoría de este mismo paquete ya
  demostró look-alikes que sobreviven, y AC-12 multiplica por cuatro la superficie que esa debilidad cubre.
- **Un segundo esquema de fencing solo para el vault-en-spawn (paralelo al de `_mark_untrusted`).**
  Explícitamente prohibido por el contrato de este paquete y descartado por diseño: dos esquemas activos
  simultáneamente es más superficie de auditoría, no menos, y el prompt final terminaría mezclando dos
  convenciones de marcador distintas frente al mismo agente.
- **Fetch en proceso, reimplementando `find_vault` sin `app_config()`.** Descartado: `app_config()` es el
  mecanismo REAL que `--vault-link` usa como fallback (`cmd_vault_link` llama
  `write_app_config(vault=...)` en cada link exitoso) — omitirlo dejaría sin vault a cualquier proyecto
  cuyo vault no sea literalmente un ancestro del cwd, que es el caso común. Reimplementarlo completo
  requeriría importar `set_agents_app`, el ciclo que DEC-1 ya descarta.
- **Inyectar el vault dentro de `spawn()` en vez de en los puntos de entrada con lifecycle.** Descartado:
  `spawn()` es, por diseño de este mismo feature, un primitivo de bajo nivel que ~90 tests existentes
  llaman directo sin pasar por `dispatch_writer`/`dispatch_review`/`route_and_spawn` — inyectar ahí habría
  significado que esos tests (no propiedad de este paquete) empiecen a disparar el subproceso de fetch en
  cada corrida, sin ganar cobertura real (ningún llamador de producción entra por `spawn()` directo).

## Repair (post-review, mismo ciclo)

Un security-auditor con PoC ejecutado encontró la primera versión de `_MARKER_LOOKALIKE_RE` (arriba,
"nonce-per-invocation... independently neutralizes anything merely SHAPED like a marker") rota en tres
formas independientes: el `\b` final dejaba pasar `CONTENT_<nonce>`/`CONTENTS-<nonce>` (guion bajo, plural);
la lista de 7 codepoints zero-width sin normalización Unicode dejaba pasar soft hyphen, invisible times,
combining grapheme joiner, brackets fullwidth NFKC-plegables y homóglifos de script; y `[^>]*` era greedy y
cruzaba saltos de línea, borrando en silencio contenido legítimo del vault entre un `<<<` accidental y un
`>>>` no relacionado muchas líneas después — pérdida de datos, no solo defensa fallida, en `cmd_context`,
corrido sin condición en cada turno.

**Arreglo**: `_mark_untrusted` deja de intentar reconocer la FORMA de "UNTRUSTED VAULT CONTENT" — un cuerpo
de vault nunca necesita literalmente `<<<`/`>>>` — y en cambio neutraliza toda ocurrencia de esas dos
subcadenas, sin condición, después de despojar codepoints de formato invisibles (categoría Unicode `Cf`,
una CLASE, no una lista) y normalizar NFKC (pliega fullwidth a ASCII). Dos pasadas: un span acotado a una
sola línea (`<<<[^\n<>]*>>>`, no puede cruzar saltos de línea ni contener otro `<`/`>`) que traga un
marcador forjado completo cuando está en una sola línea, más una pasada de resto que neutraliza cualquier
delimitador suelto que la primera no haya podido emparejar. Homóglifos de script ya no necesitan trato
especial: esta defensa nunca vuelve a mirar la palabra "VAULT". El bloque ahora reporta cuántos spans
neutralizó (`[N spans neutralizados]`) en vez de tragárselo. `tests/test_harness.py`'s guardia insignia
(`test_compose_task_vault_block_neutralizes_a_hostile_lookalike_marker_embedded_in_vault_content`) gana la
aserción que su propio comentario ya prometía y se parametriza sobre la tabla de payloads que motivó el
repair, no solo el caso que la auditoría original probó.

**Diferido de este ciclo** (medium, sin PoC, presupuesto de líneas del repair — ADR-0023): la degradación
muda de `_fetch_vault_block` en los cuatro spawners (un timeout cachea `None` para toda la corrida, sin
distinguir "sin vault" de "fetch roto") y la doctrina del marcador ausente de los prompts de
implementer/reviewer. Quedan como hallazgos abiertos para un ciclo de repair posterior.
