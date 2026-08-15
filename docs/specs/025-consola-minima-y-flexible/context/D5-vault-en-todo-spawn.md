# Context pack — D5-vault-en-todo-spawn

Spec: `docs/specs/025-consola-minima-y-flexible/spec.md`, **AC-12**. Depende de D4. Último de 025.

## La verificación empírica, hecha: qué parte de ADR-0012 se cumple hoy en un spawn

**Ninguna, en el spawn.** La medición que este paquete exigía arrancar haciendo, hecha:

```
grep -c "vault" ai/scripts/claude_code_spawn.py   -> 0
grep -c "vault" ai/scripts/codex_spawn.py         -> 0
grep -c "vault" ai/scripts/opencode_spawn.py      -> 0
grep -c "vault" ai/scripts/set_agents_spawn.py    -> 0
```

Cuatro spawners, **cero menciones al vault**. Ningún agente spawneado recibe el vault por
construcción. Repetí el grep vos mismo antes de escribir una línea: es la base de todo el paquete.

`context_pack.py` (120 líneas) **no es el spawn**: es el helper de lectura de `--context`
(byte-caps, marcador de contenido no confiable, contención de symlinks). Su propio docstring
:3-9 aclara que `cmd_context`/`find_vault` viven en `set_agents_app.py`.

### Lo que SÍ existe

| Pieza | Dónde |
|---|---|
| Flags | `--vault-init` `set_agents_app.py:3704` · `--vault-link` :3705 · `--vault` :3706 · `--context` :3707 · `--vault-doctor` :3711 · `--repair` :3712 · `--include-notes` :3717 |
| Handlers | `find_vault()` :2699 · `cmd_context(project, as_json)` :3076 · doctor :3002-3035 |
| Ops | `vault_ops.py`: `VAULT_HUB = "00 - INICIO.md"` :32, `VAULT_REGISTRY = ".set-agentes-vault.json"` :37, `read_vault_registry` :62, `write_vault_registry_entry` :71, `vault_link_private` :209, `vault_doctor_report` :370 |
| **Canal allowlisted** | `coord_policy.py:76` — `--context` con `modifiers={"--json":0,"--project":1}`, enumerado exhaustivamente. El comentario :68-75 lo llama *"a THIRD sanctioned channel"*, justificado por ser read-only, y narra SEC-001: antes alcanzaba con matchear `argv[2]` y eso dejaba pasar `--context --scaffold X`. **No relajes esa enumeración.** |
| Instrucción | `Global/_canonical/agents/orchestrator.md:138` — *"**If a vault is linked** (`set-agents --vault-link`), run `set-agents --context [--project DIR] --json`"* |

**Ese `If` es toda la brecha.** El vault llega a un agente sólo si (a) hay vault linkeado, (b) el
orquestador se acuerda de correr `--context`, y (c) pega la salida en el texto de la tarea. Tres
condiciones voluntarias, ninguna verificada por nada. ADR-0012 se titula *"Mandatory vault"* y
`docs/adr/0012-mandatory-vault.md:19-25` ya describe la falla original: *"nothing reads the vault
back into the orchestrator's context"* y los 29 archivos del vault de `~/iey/` que no existían en
ningún otro lado. **El ADR arregló el lado del orquestador; el lado del spawn quedó sin cerrar.**

### El punto de inyección

`compose_task(task, supplementary)` — `claude_code_spawn.py:309-344`. Su docstring :316 dice que
embebe la nota de archivos disponibles *"ahead of `task`"*. Es el único lugar por donde pasa todo
lo que un agente lee, y llega ahí desde `spawn()` :505 (`stdin_text = compose_task(...)`), usado por
`dispatch_writer` :534 y `dispatch_review` :660. Los otros tres spawners tienen la estructura
equivalente. **Hay cuatro, y una implementación en uno solo deja tres agujeros.**

## La trampa

**Meter el vault en todos los spawns multiplica por N la superficie de prompt injection que
ADR-0012 ya tuvo que fencear una vez.**

`context_pack.py:83-105` existe por esto: `_UNTRUSTED_OPEN`/`_UNTRUSTED_CLOSE` envuelven el
contenido, y `_mark_untrusted` **neutraliza el marcador dentro del cuerpo** porque —DR-002, :95-99—
el mismo actor que escribe en el vault puede escribir el marcador y forjar un cierre falso. El
docstring :88-90 dice que `--context` *"is called unconditionally at every turn/feature open"*: hoy
es **una** llamada por turno, del orquestador. AC-12 la vuelve **una por spawn**, y encima el
contenido aterriza en `compose_task`, **delante de la tarea**, que es la posición más privilegiada
del prompt. Si inyectás el texto del vault sin la valla de `_mark_untrusted`, o la ponés después de
la tarea, o dejás que el contenido del vault sea lo primero que el agente lee sin marcar, creaste
un canal de inyección en cada rol del harness. `_resolve_within` (:108-120) contiene los symlinks
del vault: **cualquier lectura nueva pasa por ahí, ninguna por `open()` directo**.

Segunda trampa, y hunde el paquete si la ignorás: **"obligatorio" no puede significar "falla
cerrado"**. Hoy, sin vault, todo funciona — el `If` de `orchestrator.md:138` lo hace opcional por
diseño. Un spawn que aborte con `VAULT_NOT_FOUND` (el string existe: `set_agents_app.py:2854,3002,
3014`) rompe **cada proyecto sin vault, incluido este repo si no está linkeado**. Degradá: sin
vault, el spawn sale igual y lo deja anotado.

Tercera: `--context` **hace I/O de disco** (`_read_capped` :40-62, `_resolve_company_dir` :76-80,
lectura del registry). Llamarlo una vez por spawn agrega latencia a cada delegación, y sobre un
vault sincronizado por Syncthing puede colgarse. Cacheá por corrida o poné timeout — y si esa
latencia se vuelve visible, es exactamente el caso de D2. **Medila y pegá el número.**

## La mordida exigida

Nueve guardas falsas-verdes en este repo. Cinco tests, cada uno con su rojo demostrado:

1. **Los cuatro spawners, no uno**: test parametrizado sobre `claude_code_spawn`, `codex_spawn`,
   `opencode_spawn` y `set_agents_spawn`. Rojo: sacá el vault de UNO y confirmá que falla ese caso.
   Un test que sólo cubre `claude_code_spawn` es una guarda hueca — hoy el grep da 0 en los cuatro.
2. **El contenido llega marcado**: el texto compuesto contiene `_UNTRUSTED_OPEN` **y**
   `_UNTRUSTED_CLOSE` alrededor del contenido del vault. Rojo: quitá el marcado, confirmá el fallo.
3. **El marcador forjado sigue neutralizado** cuando el camino es el spawn y no `cmd_context`: nota
   de vault que contiene el literal `_UNTRUSTED_CLOSE` → aparece defanged en la tarea compuesta.
   Rojo: saltate `_mark_untrusted`, confirmá el fallo. Es DR-002 reprobado en el camino nuevo.
4. **Degradación sin vault**: sin vault linkeado, el spawn **compone y sale igual**, y el texto lo
   dice. Rojo: hacé que aborte, confirmá el fallo.
5. **Contención de path**: un `vault_path` del registry que apunte afuera del vault **no se lee**
   (`_resolve_within`). Rojo: usá `open()` directo, confirmá el fallo. SEC-002/SEC-003.

Y una verificación fuera de test, obligatoria en la evidencia: **un spawn real de proyecto**,
corrido de punta a punta, con la tarea compuesta pegada mostrando el bloque del vault dentro. Es
literalmente lo que pide el AC. Sin eso, el paquete repite el defecto que 027 pasó la noche
reparando: un AC construido sobre "el ADR lo dice".

## Restricciones

- **ADR reservado: 0056** (`ls docs/adr/`; 0050 reservado sin escribir por D1, 0052 tomado por
  027/P4, 0053 D2, 0054 D3, 0055 D4). Indexalo en `docs/adr/README.md`. **Amienda ADR-0012**, no lo
  reemplaza: citá qué parte quedaba sin cumplir y qué cierra esta.
- `owned_paths`: `ai/scripts`, `Global/_canonical`, `tests`, `docs/adr`.
- **No relajes `coord_policy.py:61-76`.** Si el spawn necesita un flag nuevo, se enumera
  exhaustivamente en `modifiers`; jamás `modifiers=None` ni un regex con wildcard al final. SEC-001
  y la nota DR-02 (:87-93) documentan exactamente qué pasó las dos veces que se aflojó.
- **No metas el contenido del vault en argv.** Los spawners son explícitos: la tarea va por STDIN o
  por archivo, nunca como token de argv (`claude_code_spawn.py:24-26,103,707-710,739-740`).
- **Nada de credenciales ni PII en la tarea compuesta.** El vault es del cliente.
- `context_pack.py` es hoja por diseño (:9): **no le agregues imports de `set_agents_app` ni de
  `vault_ops`** — rompe `tests/test_harness.py::_import()`.
- Tocás `Global/_canonical` (la instrucción de `orchestrator.md:138`) → `./build.sh --check`.
- No uses `git checkout`/`restore`/`stash`. No toques nada bajo `~`. Nunca `./build.sh --install`.

## Validación

`python3 -m unittest discover -s tests` (**`pytest` NO está instalado**) · `./ai/scripts/verify.sh` →
`VERIFY_PASS` · **`./build.sh --check` → `GLOBAL_TREE_SYNC_OK` + `BUILD_CHECK_PASS`** ·
`git diff --check`. Manual: `set-agents --context --json` con y sin vault, pegadas ambas.

**Comandos largos: `ai/scripts/heartbeat-run.py --interval 20 -- <comando>`** (ADR-0041).

## Evidencia

`docs/specs/025-consola-minima-y-flexible/evidence/D5-implementer.md`, primer minuto: **el grep de
los cuatro spawners, antes y después**; tabla AC → cambio (`archivo:línea`) → prueba; **la tarea
compuesta de un spawn real, pegada, con el bloque del vault fenceado**; la latencia que agrega
`--context` por spawn, medida; el caso sin vault; y las cinco pruebas de mordida con su rojo. Cada
bloque literal o marcado como recortado. Si no lo corriste, "sin verificar".

## Fuera de alcance

Menú/flags/`--json` (D1) · spinner (D2) · posturas (D3) · instalar/desinstalar por CLI (D4) · el
ruteo y el sort key · rediseñar la topología del vault o la migración de `--vault-doctor --repair` ·
cambiar el esquema JSON de `--context` (ADR-0012/AC-18 lo fija en `{hub, company, project, pending}`).
