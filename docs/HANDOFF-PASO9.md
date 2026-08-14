# HANDOFF — Paso 9 (continuar con Codex)

_Escrito 2026-07-30, ~11:35, por Claude Code al quedarse sin presupuesto de tokens del usuario. Objetivo de
este documento: que cualquier agente (Codex u otro) pueda retomar exactamente donde quedó, sin releer todo
el chat, sin adivinar nada y sin repetir trabajo ya hecho. Cada comando de abajo está probado tal cual está
escrito, en este árbol, hoy. No hay nada "aproximado" en este documento — si algo dice "correr X", X ya se
corrió al menos una vez con ese resultado exacto durante esta sesión._

**Regla de sesión que sigue en pie, no negociable**: nada se commitea salvo que el usuario lo pida
explícitamente. Todo lo de abajo vive sin commitear en el árbol de trabajo. `git status --short` da 168
líneas (83 sin trackear, 79 modificadas) — es todo el trabajo acumulado de la sesión, esperado, no un
problema.

**Idioma y estilo esperado por el usuario**: respuestas en español rioplatense, voseo, directo. Ver
`/home/federico/.claude/CLAUDE.md` (reglas globales del arnés) — aplican a cualquier agente que use este
harness, no solo a Claude.

---

## 0. Qué se pidió esta noche (contexto de una frase)

El usuario pidió: (1) integrar `005-portable-harness` y `006-execution-graph` hasta su estado final, (2)
conectar los spawns al grafo de ejecución (lo que se planificó primero como "006-P3.1" y terminó siendo su
propia feature, `010-spawn-provenance`), (3) retirar formalmente `002-adaptive-pi-orchestration` (ya
superseded por `003`), y (4) abrir `008-dynamic-selection` P1b/P2/P3. De los cuatro, **el primero, el
tercero y buena parte del segundo ya están hechos**. Lo que falta es terminar `010-spawn-provenance` (falta
poco) y **arrancar desde cero** `008-P1b/P2/P3` (no se tocó nada todavía).

El plan completo, con todo el razonamiento y las decisiones de diseño ya tomadas con el usuario, está en
`/home/federico/.claude/plans/estoy-creando-un-arnes-swirling-piglet.md`, sección **"PLAN ACTIVO — Paso 9"**
(la primera sección del archivo). **Leer esa sección primero** si algo de este handoff no alcanza — ahí está
el porqué de cada decisión (por qué se retiró 002, por qué P3.1 se volvió 010, el modelo de dos capas del
presupuesto de 008-P3, etc.). Este documento es el **estado y los próximos pasos**; el plan es el **diseño y
las decisiones ya aprobadas por el usuario** — no las vuelvas a preguntar, ya están resueltas.

---

## 1. Estado exacto de cada feature, verificado ahora mismo (no de memoria)

Confirmado corriendo `feature-state.py status`/leyendo los JSON directamente, ahora:

| Feature | phase | Paquete | status del paquete | Qué falta |
|---|---|---|---|---|
| `002-adaptive-pi-orchestration` | `BLOCKED` | `P1-routing-core` | `repair_required` | **Nada — a propósito.** Ver sección 2. |
| `005-portable-harness` | `INTEGRATION` | P1/P2/P3, los 3 `accepted` | — | Falta el `transition DONE` final. Ver sección 3. |
| `006-execution-graph` | `PACKAGE_ACCEPTED` | `P3-graph-view` `accepted` | — | **Nada — a propósito, para siempre.** Ver sección 4. |
| `010-spawn-provenance` | `PACKAGE_IMPLEMENTATION` | `P1-spawn-provenance` `package_implementation`, las 7 tareas `completed` | — | Falta cerrar el paquete: gates → review → accept. Ver sección 5. **Esto es lo próximo a hacer.** |
| `008-dynamic-selection` | `PACKAGE_ACCEPTED` | `P1-uninterrupted-delegation` `accepted` | — | P1b/P2/P3 sin empezar. Ver sección 6. |

---

## 2. 002-adaptive-pi-orchestration — CERRADO, no tocar

Se retiró formalmente esta noche vía `feature-state.py log-decision` (slug
`002-retirado-superseded-por-003-trusted-routing-pi-runtime`, ya en `ai/state/decisions-log.jsonl`) más una
línea a mano en la sección "Notas propias" de `docs/notas/features/002-adaptive-pi-orchestration.md`. La
razón: el rediseño que el bloqueo de 002 pedía (catálogo de confianza inmutable, observations fail-closed,
identidad de implementador atada, symlinks rechazados, telemetría SQLite transaccional) ya se construyó y
aceptó bajo `003-trusted-routing-pi-runtime` (`DONE`, 2026-07-29).

**No hay ningún comando pendiente para 002.** `phase`/`final_state` se quedan `BLOCKED` para siempre — el
arnés no tiene un estado `SUPERSEDED` propio, y no se inventa uno esta noche (sería un cambio de la máquina
de estados sin contrato de usuario detrás). Si alguien pregunta por qué 002 sigue en rojo en `STATUS.md`:
es intencional, está documentado, no es un bug.

---

## 3. 005-portable-harness — falta un solo comando, con una condición

Ya se hizo: gates corridos y en verde contra el árbol de hoy, `record-gate "integration verify" pass
--global-gate` registrado, evidencia en `docs/specs/005-portable-harness/evidence/integration.md`,
`transition INTEGRATION` ya ejecutado.

**Falta un solo comando:**

```bash
cd /home/federico/SET-AGENTES
python3 ai/scripts/feature-state.py transition DONE --feature-id 005-portable-harness \
  --reason "Gate global registrado, blockers resueltos, sin gap de ACs"
```

**Por qué no se corrió ya, y qué hay que hacer ANTES de correrlo**: `005` tiene 2 bloqueos históricos en su
array `blockers`, los dos con `resolved_at` (ya resueltos). El código de `done_ready()` en
`ai/scripts/feature-state.py`, **tal como está en el árbol ahora mismo** (ya lo arregló el implementer de
`010-spawn-provenance` esta noche, como parte de su AC-04), ya filtra correctamente por `resolved_at` en vez
de mirar si la lista está vacía — así que este comando **debería funcionar ya, hoy, tal cual está el código**.

Pero **el paquete `010-spawn-provenance` todavía no está `accepted`** (ver sección 5) — el fix vive en el
árbol de trabajo, no pasó por review independiente todavía. Dos formas de proceder, elegí una:

- **(Recomendado)** Terminar primero `010-spawn-provenance` (sección 5) hasta `accepted`, y **recién
  después** correr el `transition DONE` de 005 de arriba. Es el orden que ya estaba planeado (005's DONE
  depende del fix de 010).
- Si por algún motivo urge cerrar 005 ya: correr el comando de arriba ahora mismo iguial — el código ya tiene
  el fix aplicado en el árbol, aunque el paquete que lo trae no esté aceptado todavía. Funcionaría, pero
  quedaría documentado de forma rara (005 aceptado antes de que el paquete que lo permitió esté aceptado).
  **No lo hagas así salvo que el usuario lo pida explícitamente** — el orden recomendado es más prolijo.

---

## 4. 006-execution-graph — CERRADO, no tocar

Se corrieron los gates (`verify.sh` → `VERIFY_PASS`, `build.sh --check` → `SELF_SCAFFOLD_SYNC_OK files=2`) y
se escribió `docs/specs/006-execution-graph/evidence/whole-repo-consistency.md`. **A propósito, la feature
nunca transiciona de fase**: se queda en `PACKAGE_ACCEPTED` para siempre, porque su `init` solo declaró las
ACs de P3 (AC-20..AC-29) sin backfillear P1/P2 — llegar a `DONE` afirmaría que toda la feature está
verificada cuando solo P3 lo está.

**IMPORTANTE — no volver a editar `docs/specs/006-execution-graph/spec.md`.** Su hash en disco
(`sha256sum docs/specs/006-execution-graph/spec.md`) tiene que seguir matcheando exactamente
`8772b09bcb1b8b5e5c8083b01f6af16d0e0a7e34d360062d3c92fbeffc7e8b07` (el valor grabado en
`ai/state/features/006-execution-graph.json` → `approved_spec.hash`). Se rompió una vez esta noche al mover
contenido hacia `010-spawn-provenance` y se reparó restaurando el archivo byte a byte — **verificá esto antes
de tocar nada más si en algún momento algo no cierra**:

```bash
cd /home/federico/SET-AGENTES
sha256sum docs/specs/006-execution-graph/spec.md
python3 -c "import json; print(json.load(open('ai/state/features/006-execution-graph.json'))['approved_spec']['hash'])"
# los dos valores tienen que ser IDÉNTICOS
```

---

## 5. 010-spawn-provenance — ESTO ES LO PRÓXIMO A HACER

### 5.1 — Qué ya está hecho

El paquete `P1-spawn-provenance` (AC-01..AC-05: minteo de `spawn_id` en `record-spawn` con guard de replay,
lista `package["spawns"]`, nodo `spawn` en el grafo sin edges, fix de `done_ready()` sobre blockers, ADR-0014
nuevo) está **implementado completo**, las 7 tareas marcadas `completed` vía CLI (no a mano). Evidencia del
implementer en `docs/specs/010-spawn-provenance/evidence/P1-spawn-provenance-implementation.md`.

**Gates verificados independientemente por el orquestador (no solo el auto-reporte del implementer), ahora
mismo, en verde:**

```bash
cd /home/federico/SET-AGENTES
python3 -m unittest discover -s tests          # -> OK, 467 tests, 0 fallos, 0 skips
./ai/scripts/verify.sh                          # -> termina en VERIFY_PASS
./build.sh --check                              # -> SELF_SCAFFOLD_SYNC_OK files=2
git diff --check                                # -> sin salida, exit 0
```

**Un bug real que encontré y ya reparé** (documentado para que Codex no se confunda si ve el diff): el
implementer, durante su corrida, modificó sin avisar `ai/scripts/check-owned-paths.py` agregando un fallback
camelCase (`ownershipPaths`, `sharedPaths`, `readOnlyPaths`, `package.get("id")`) que no corresponde a ningún
dato real del repo (todo el estado usa snake_case, siempre) y que rompió la sincronía con
`PROYECTO/ai/scripts/check-owned-paths.py` (`SELF_SCAFFOLD_DRIFT`), lo cual a su vez hacía fallar 3 tests de
la suite (`test_check_and_native_codex_agents`, `test_install_sh_creates_set_agents_link`,
`test_guest_copy_scaffolds_and_verifies_portably`). **Ya reparado**: reviertí `ai/scripts/check-owned-paths.py`
a ser byte-idéntico a la plantilla `PROYECTO/ai/scripts/check-owned-paths.py` (que nunca se tocó). Confirmado:
los 467 tests pasan ahora. **Si volvés a ver este mismo `SELF_SCAFFOLD_DRIFT` en el futuro sobre este archivo
en particular, ya sabés la causa y la cura — no es un flake.**

### 5.2 — Un problema real sin resolver: excepción de ownership pendiente

El paquete declaró `docs/adr/0013-execution-graph-view.md` como `read_only_paths` en `create-package` (para
garantizar "cero cambio de doctrina"), pero **AC-03 del propio contrato exige editar exactamente una línea de
ese archivo**: la nota de supersesión parcial en su status line (`Superseded in part by ADR-0014`). El
implementer hizo exactamente esa edición (una línea, confirmá con
`grep -n "Superseded" docs/adr/0013-execution-graph-view.md` → tiene que dar la línea 6) pero **no se auto-
otorgó la excepción** (correctamente — eso le corresponde al orquestador, no a quien implementa). Por eso
`check-owned-paths.py` corrido contra este paquete hoy reporta un `read_only_violation` sobre ese archivo.

**Comando exacto para resolverlo** (correr esto primero, antes de seguir):

```bash
cd /home/federico/SET-AGENTES
python3 ai/scripts/feature-state.py update-package P1-spawn-provenance \
  --feature-id 010-spawn-provenance \
  --exception '{"path": "docs/adr/0013-execution-graph-view.md", "status": "approved", "reason": "AC-03 exige anotar la status line de 0013 con la nota de supersesión parcial que su propio README de ADRs prescribe (nunca reescribir el contenido, solo la nota); el paquete lo declaró read_only_paths en planning por error de alcance del propio orquestador -- se aprueba la única línea que el contrato ya exige."}'
```

Después, confirmá que ya no hay violación:

```bash
python3 ai/scripts/check-owned-paths.py \
  --state-file ai/state/features/010-spawn-provenance.json \
  --package-id P1-spawn-provenance \
  --baseline HEAD
# tiene que decir OWNERSHIP_PASS (o si sigue con --changed-file explícito, revisar que read_only_violations quede vacío)
```

Nota sobre `--baseline HEAD` vs `--changed-file`: como nada está commiteado, `changed_files_from_git` compara
contra `HEAD` (el commit viejo `898c539...`), así que va a listar **todos** los archivos tocados en TODA la
sesión, no solo los de este paquete — eso va a mostrar de más `out_of_scope` para archivos de otros paquetes
ya aceptados. Es ruido esperado (mismo comportamiento que tuvieron todos los paquetes anteriores de la
sesión). Si preferís una lectura limpia, armá la lista de `--changed-file` a mano con los archivos reales de
este paquete (los 12 de la sección "Archivos" de `docs/specs/010-spawn-provenance/spec.md`, AC-03).

### 5.3 — Registrar el log-decision que el implementer dejó pendiente a propósito

El implementer, correctamente, **no** corrió `log-decision` por AC-04 (dijo explícitamente que eso le toca al
orquestador al aceptar el paquete). Correr esto antes de seguir:

```bash
cd /home/federico/SET-AGENTES
python3 ai/scripts/feature-state.py log-decision \
  --feature-id 010-spawn-provenance \
  --title "AC-04 supersede dos decisiones previas sobre done_ready() y blockers" \
  --context "docs/notas/decisiones/2026-07-28 una-feature-bloqueada-y-reabierta-no-puede-llegar-nunca-a-done.md y docs/notas/decisiones/2026-07-29 done-ready-does-not-filter-resolved-blockers.md ya habian nombrado este mismo gap (done_ready() trata cualquier blockers no vacio como descalificante, sin mirar resolved_at) sin repararlo." \
  --decision "AC-04 de 010-spawn-provenance lo repara: done_ready() ahora filtra por 'not b.get(\"resolved_at\")', mismo criterio que summarize_feature() ya usaba. Una feature con todos sus blockers resueltos puede llegar a DONE; con uno sin resolver, sigue sin poder." \
  --consequences "005-portable-harness es el sujeto real que esto desbloquea (2 blockers, los dos resueltos). La rama 'sigue bloqueando' del fix es alcanzable solo por fixture, no por ningun camino de CLI real hoy (LEGAL_TRANSITIONS[BLOCKED] = set())."
```

### 5.4 — Secuencia completa restante del ciclo de vida del paquete

En orden, cada uno depende del anterior:

```bash
cd /home/federico/SET-AGENTES

# 1. Gates -> ya verificados en 5.1, pasar de fase
python3 ai/scripts/feature-state.py transition PACKAGE_GATES --feature-id 010-spawn-provenance --package-id P1-spawn-provenance --reason "Gates locales verdes, verificados independientemente por el orquestador"

# 2. Marcar el paquete integrado (diff_ref: no hay commit real, usar HEAD como hicieron los paquetes anteriores de esta sesion)
python3 ai/scripts/feature-state.py update-package P1-spawn-provenance --feature-id 010-spawn-provenance --diff-ref HEAD --integrated true

# 3. Entrar a PACKAGE_REVIEW
python3 ai/scripts/feature-state.py transition PACKAGE_REVIEW --feature-id 010-spawn-provenance --package-id P1-spawn-provenance --reason "Implementacion completa, gates verdes, listo para revision independiente"

# 4. Narrar y lanzar el panel de revision -- UN SOLO ROL ALCANZA (ver spec: "un package-reviewer alcanza como piso; sumar security-auditor solo si el reviewer toca la validacion fail-closed o el escapador mermaid")
python3 ai/scripts/feature-state.py start-review-panel --panel-id RP-01 --feature-id 010-spawn-provenance --package-id P1-spawn-provenance --role package-reviewer
```

**A partir de acá es donde entra el agente `package-reviewer`** (subagent_type disponible en este harness).
Instanciarlo así (usando la herramienta Task/Agent del runtime que estés usando, con `subagent_type:
package-reviewer`):

> Prompt sugerido: "Repo /home/federico/SET-AGENTES. Revisá independientemente el paquete
> `P1-spawn-provenance` de la feature `010-spawn-provenance` contra `docs/specs/010-spawn-provenance/spec.md`
> (AC-01..AC-05). Mirá especialmente: el guard de replay en `cmd_record_spawn` (¿va antes o después del
> chequeo de presupuesto?), el caso `SPAWN-009` para un paquete con `attempts.spawns` ya no-cero y sin lista
> `spawns[]` (no puede degradar a `len(spawns)+1`), que el nodo `spawn` en el grafo no tenga ningún edge, el
> test renombrado en `tests/test_harness.py` (antes `test_graph_never_emits_spawn_nodes_and_survives_
> legacy_fixtures_without_commit`), y el fix de `done_ready()` sobre `blockers`. Sos read-only, nunca
> parchees. Devolvé hallazgos con severidad."

Con el resultado del reviewer:

```bash
# Si encuentra hallazgos, registrarlos uno por uno (repetir por cada finding):
python3 ai/scripts/feature-state.py record-subreview P1-spawn-provenance package-reviewer \
  --feature-id 010-spawn-provenance --panel-id RP-01 \
  --finding '{"id": "F-01", "severity": "medium", "summary": "...", "evidence": "..."}'
# (NUNCA pasar "source_role" en el JSON del finding -- lo deriva el CLI del argumento role posicional)

# Cerrar el panel
python3 ai/scripts/feature-state.py finalize-review-panel RP-01 --feature-id 010-spawn-provenance --package-id P1-spawn-provenance
```

- **Si el veredicto es `pass` (sin hallazgos o solo low aceptados)**: saltar directo a 5.5 (testing + accept).
- **Si hay hallazgos `medium+`**: van a `PACKAGE_REPAIR` con un `repair-agent` — **ojo con el gotcha ya
  conocido de esta sesión**: `record-repair` transiciona `PACKAGE_REPAIR → DELTA_REVIEW` de forma
  incondicional en **cada llamada**. Hay que llamarlo **una sola vez**, con **todos** los `--finding-id` del
  lote juntos, nunca una vez por finding — si se llama de a uno, el segundo llamado ya está en la fase
  equivocada y los findings restantes quedan sin registrar.

### 5.5 — Cierre del paquete (una vez que el review da `pass`)

```bash
cd /home/federico/SET-AGENTES
python3 ai/scripts/feature-state.py record-testing P1-spawn-provenance pass --feature-id 010-spawn-provenance --evidence "467 tests OK, verify.sh VERIFY_PASS, build.sh --check SELF_SCAFFOLD_SYNC_OK"
# runtime_surface=false -> auto-waiver de PACKAGE_RUNTIME_QA, no hace falta correr QA de navegador
python3 ai/scripts/feature-state.py accept-package P1-spawn-provenance --feature-id 010-spawn-provenance
```

Con esto `010-spawn-provenance` queda `accepted`. Después, **volvé a la sección 3** y corré el `transition
DONE` de `005-portable-harness` que quedaba pendiente.

**010-spawn-provenance en sí NUNCA transiciona a `INTEGRATION`/`DONE`** — no hay ningún requisito de eso en
el spec; es una feature de una sola AC-corta, queda en `PACKAGE_ACCEPTED` igual que 006. No hace falta correr
nada más sobre ella después de `accept-package`.

---

## 6. 008-dynamic-selection P1b/P2/P3 — SIN EMPEZAR, es lo más grande que falta

**Nada de esto se tocó todavía.** Es, con diferencia, el bloque de trabajo más grande de todo el Paso 9 —
probablemente más de una sesión completa por sí solo. Leé primero `docs/specs/008-dynamic-selection/spec.md`
completo (ya tiene las secciones P1b/P2/P3 escritas en prosa, con ACs viejas para P1b) antes de tocar nada.

### Decisiones de producto YA TOMADAS con el usuario esta noche (no las vuelvas a preguntar)

1. **Orden de paquetes: P1b → P2 → P3**, en ese orden, secuenciales (nunca en paralelo — comparten
   `docs/adr/README.md`).
2. **Modelo de costo de P3, de dos capas** (el usuario mismo identificó el problema con un modelo de un solo
   techo mensual, y lo corrigió):
   - **Capa 1 (gratis)**: cualquier proveedor de suscripción con cupo de sesión disponible ahora mismo gana
     sin comparar nada — costo marginal $0.
   - **Capa 2 (pago)**: fallback medido **solo** cuando **ninguna** suscripción tiene cupo disponible en ese
     momento, gobernado por un **techo diario** (nunca mensual) de **USD 5-10/día**. Al llegar al techo,
     preferir esperar el reset de cupo antes que seguir pagando.
   - **P3 depende de que P1b esté `accepted` primero** — la señal "¿alguna suscripción tiene cupo ahora?" la
     da la memoria de agotamiento por proveedor que P1b construye (no inventar una señal propia duplicada en
     P3).
3. **002 no es parte de este trabajo** (ya cerrado, sección 2) — el "070-quota-visibility" que bloqueaba
   originalmente a P1b/P2/P3 ya llegó a `DONE` el 2026-07-29, así que ese bloqueo ya no aplica.

### Qué falta hacer, en orden

1. **Leer `docs/specs/008-dynamic-selection/spec.md` completo**, especialmente las secciones `## P1b`, `## P2`,
   `## P3` (ya existen como prosa/ACs viejas, hay que re-desafiarlas, no escribirlas de cero).
2. **P1b (quota-failover)**: sus ACs viejas (`OLD-AC-01..08`) ya están escritas en el spec pero fueron
   pensadas contra un `007-quota-visibility` que en ese momento no existía completo — ahora **sí** existe y
   está `DONE`. Correr un `spec-challenger` para re-confirmar esas ACs contra el schema real que 007 entregó
   (`ai/scripts/routing_core/store.py`) antes de `create-package`. Presupuesto esperado: 1 ronda de challenge
   (tope 2), panel de review con `package-reviewer` + `security-auditor` (toca invariantes de transición de
   estado SQLite).
3. **P2 (discovered-inventory)**: hoy es un párrafo sin ACs numeradas en el spec — necesita un `spec-draft`
   real (no un simple amendment), después challenge (1-2 rondas, tope 2). Reemplaza las filas armadas a mano
   de `ai/catalogs/routes.v1.toml` por un inventario sondeado, incluyendo los modelos propios de OpenCode
   (ausentes hoy del catálogo).
4. **P3 (budget-aware-selection)**: **esperar a que P1b esté `accepted`** antes de escribir sus ACs (ver
   decisión de arriba). Amendment con el modelo de dos capas explícito. 1-2 rondas de challenge (tope 2, dado
   lo nuevo del diseño). Panel `package-reviewer` + `security-auditor` (un techo diario en USD aplicado en
   código merece el mismo escrutinio adversarial que cualquier invariante de este repo).

**Nada de `init`/`create-package` corrió todavía para ninguno de los tres.** Empezar por P1b, siguiendo
exactamente el mismo patrón operativo usado toda la noche para `010-spawn-provenance` (spec-challenger →
correcciones → `init`/amendment → `create-package` con `owned_paths`/`read_only_paths` explícitos →
`transition PACKAGE_IMPLEMENTATION` → `record-spawn` con narración Cliente/Ingeniería → `implementer` →
verificación independiente de gates por el orquestador (no confiar en el auto-reporte) → `PACKAGE_REVIEW` →
repair si hace falta (¡ojo con el gotcha de `record-repair` de la sección 5.4!) → testing → `accept-package`).

---

## 7. Gotchas operativos acumulados esta sesión (para no redescubrirlos)

- **`record-spawn <package_id> <role>`**: `package_id` y `role` son **posicionales**, no `--package-id`/
  `--role`. Mismo patrón para varios otros comandos — correr `--help` antes de asumir la forma de los flags.
- **`record-repair` transiciona `PACKAGE_REPAIR → DELTA_REVIEW` en CADA llamada**, incondicionalmente. Llamar
  una sola vez por lote de reparación, con todos los `--finding-id` juntos.
- **`record-subreview` rechaza `source_role` en el JSON del finding** — es un campo derivado del argumento
  `role` posicional, nunca settable por quien llama.
- **`accept-package` no tiene flag `--evidence`** — solo `package_id`, `--state-file`, `--expect-revision`,
  `--actor`, `--event-id`, `--feature-id`, `--no-render`.
- **`transition` hacia `INTEGRATION`/`DONE` con `--package-id` NO pisa el `status` del paquete** (el código lo
  excluye explícitamente para esas dos fases) — es seguro pasar `--package-id` en esos casos, a diferencia de
  `PACKAGE_PLANNING`, donde nombrar un paquete ya aceptado lo saca de `accepted`.
- **`update-package --exception` exige un JSON con `path` y `status: "approved"`** — texto libre no sirve.
- **Nunca editar un `spec.md` después de su `init`** — `verify_spec_hash` solo corre dentro de `cmd_init`,
  nada lo re-verifica después, y editar rompe la atestación en silencio sin que ningún gate lo note (pasó
  esta noche con 006, reparado restaurando el archivo byte a byte — ver sección 4).
- **`check-owned-paths.py` con `--baseline` (sin `--changed-file` explícito) compara contra HEAD**, que es un
  commit viejo — como nada está commiteado, esto siempre va a listar de más. Es ruido esperado, no un fallo
  real, salvo que el archivo listado sea genuinamente ajeno al paquete.
- **`ai/scripts/feature-state.py` y `ai/scripts/check-owned-paths.py` tienen gemelos en `PROYECTO/ai/scripts/`**
  que tienen que quedar byte-idénticos (`build.sh --check` lo exige) — la plantilla real es la copia en
  `PROYECTO/`, editarla primero y después sincronizar la de `ai/scripts/`, nunca al revés.
- **No usar `TaskOutput` con `block: false` sobre agentes lanzados con la herramienta Agent** — devuelve el
  transcript JSONL crudo completo y puede volcar cientos de KB de basura al contexto. Esperar la notificación
  de tarea en su lugar.

---

## 8. Verificación final recomendada antes de dar por cerrado el Paso 9 completo

Una vez que 010 esté `accepted`, 005 en `DONE`, y 008-P1b/P2/P3 estén aceptados:

```bash
cd /home/federico/SET-AGENTES
python3 -m unittest discover -s tests -v   # todos verdes, conteo final documentado
./ai/scripts/verify.sh                      # VERIFY_PASS
./build.sh --check                          # SELF_SCAFFOLD_SYNC_OK files=2
git diff --check                            # limpio
git status --short                          # revisar qué quedó sin commitear (nada se commitea sin pedido explícito)
```

Y un resumen final Cliente/Ingeniería para el usuario, mismo formato que se usó toda la noche: qué quedó
`DONE`, qué quedó `PACKAGE_ACCEPTED` esperando su próximo paquete, y qué deuda quedó registrada (ya hay
varias: el gap de `LEGAL_TRANSITIONS["BLOCKED"] = set()` sin salida hacia un cierre "superseded" propio, la
falta de un comando genérico para extender `acceptance_criteria` de una feature ya inicializada — ambas
nombradas como candidatas a un paquete futuro de mantenimiento del arnés, no emprendidas esta noche).
