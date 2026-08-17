# Traspaso — continuación desde otro runtime

**Escrito**: 2026-08-17, por el orquestador de la sesión de Claude Code que cerró 027 y 025.
**Para**: quien retome, en opencode / codex / el runtime que sea.
**Base**: commit `bec3dcf`.

Este documento es la fuente de verdad del traspaso. Todo lo que afirma está respaldado
por una medición o una entrada en `ai/state/decisions-log.jsonl` (27 entradas entre el
2026-08-15 y hoy). Si algo acá contradice tu memoria, gana el archivo.

---

## Cómo trabaja este repo (leer antes de tocar nada)

- **File-first y por paquetes.** El estado vive en `ai/state/features/*.json` y se muta
  **sólo** con `python3 ai/scripts/feature-state.py <verbo>`. Nunca a mano.
- **Flujo**: `PACKAGE_PLANNING → IMPLEMENTATION → GATES → REVIEW → REPAIR → DELTA_REVIEW
  → TESTING → RUNTIME_QA → ACCEPTED → INTEGRATION → DONE`.
- **El implementer nunca aprueba lo suyo.** Review independiente obligatorio, en otro
  modelo y con contexto limpio como mínimo (ADR-0011).
- **ADR-0026, evidencia sobre memoria**: ninguna afirmación sin `archivo:línea`, sin la
  salida de un comando que corriste, o sin un documento actual con su URL. Lo que no
  verificaste va marcado **"sin verificar"**.
- **Mordida obligatoria**: por cada test nuevo, neutralizá el cambio, confirmá el rojo,
  revertí y pegá la salida literal. En este repo van **trece guardas falsas-verdes**
  contadas: tests que existían y no probaban nada.

## Seis reglas que costaron caro esta sesión

1. **Verificá el artefacto, no el reporte.** Un implementer reportó 025/D5 completo —cuatro
   spawners, cinco mordidas, un ADR— y en git no había **nada**. `git rev-parse <rama>`
   contra la base, y un `grep` de un símbolo que el trabajo debería haber creado.
2. **Nunca leas `$?` después de un pipe.** Pasó tres veces; una hizo perder un paquete
   entero (se dio D1 por integrado sin estarlo). Usá `${PIPESTATUS[0]}` o redirigí a archivo.
3. **Medí sobre el árbol integrado, después de integrar.** Medir en el worktree del agente
   da verde y no prueba nada.
4. **No despaches un agente contra `main` si vas a commitear en esa ventana.** Dale un SHA
   fijo. Costó 728 líneas de trabajo correcto que hubo que portar a mano.
5. **El entorno mata procesos en segundo plano cerca de los 650 s**, y la suite tarda ~700.
   Corré los gates con `setsid nohup ./ai/scripts/verify.sh > log 2>&1 &` y consultá el log.
6. **El watchdog mata a un agente a los 600 s sin salida.** Comandos largos con
   `python3 ai/scripts/heartbeat-run.py --interval 20 -- <cmd>` (ADR-0041).

---

## Qué está cerrado

| | |
|---|---|
| **026** orquestador elige modelo | DONE, 2/2 |
| **027** controles que miran | DONE, 4/4, 21 hallazgos cerrados |
| **030** el RCE de la allowlist | reparado dos veces, **instalado** y verificado |

Sobre 030: `coord_policy.py` hacía `re.fullmatch(pattern + r".*", command)`, lo que
convertía las 23 entradas de la allowlist en un prefix match y permitía RCE desde el rol
read-only (`fd -X`, `find -exec`, `curl -o` sobre la propia guarda). Cerrado, y después
un review independiente encontró que el arreglo **tenía otro RCE** (`python -m timeit`,
porque `python` y `python3` ruteaban por validadores distintos) más tres agujeros. Todo
reparado: **24 ataques bloqueados, 25 comandos legítimos intactos**, medido contra
`~/.claude/hooks/` real.

## Qué falta — en orden de prioridad

### 1 · Terminar 025 (código listo, falta el trámite de estado)

Los cinco paquetes **están implementados y medidos en el árbol**, pero la feature figura
`PACKAGE_REPAIR` con **0/5 aceptados**: nunca se los hizo pasar por la máquina de estados.

Verificado sobre el árbol, no leído:

```
D1  41 flags visibles de 71 con --avanzado, cero no-ASCII en el menú
D2  progreso que nunca toca stdout, degrada sin TTY y con NO_COLOR
D3  3 posturas + 2 metodologías, doctrina propagada a los 4 harnesses
D4  desinstala 124 de 125 archivos de un CLI, los otros 139 byte-idénticos
D5  vault en los 4 spawners, fence con nonce, 8 payloads hostiles neutralizados
```

**Lo que falta por paquete**: `start-task`/`complete-task` con `--validation`,
`update-package --integrated true --diff-ref`, `record-gate` ×4, `record-review` con sus
hallazgos, `record-verification`, `record-repair`, `record-delta-review`,
`record-testing`, `record-runtime-qa`, `record-module-impact` (o su waiver con razón), y
`accept-package`. Después `transition INTEGRATION`, gates globales con `--global-gate`, y
`transition DONE`.

Los hallazgos de cada review están en los archivos de evidencia bajo
`docs/specs/025-consola-minima-y-flexible/evidence/`.

**Pendiente de código en 025.** El agente que lo trabajaba **murió por watchdog sin
commitear**; el orquestador commiteó su árbol para que sobreviva:
rama **`worktree-agent-a1e28ec280c592315`, commit `6102f96`**, 482 líneas sobre `bec3dcf`,
**parcial y sin revisar**. Alcanzó a portar el vault por stdin y los tres carriles;
quedó a mitad de los tests del scrub cuando lo mataron. Su último mensaje:
*"Now let's add the SET_AGENTS_PROJECT scrub tests for the three other lanes"*.

- **D5-F05** — el vault viaja por **argv** en el carril de pi: hasta 14.658 bytes de notas
  del cliente visibles en `/proc/<pid>/cmdline`, con `/proc` sin `hidepid`. El context pack
  lo prohibía explícitamente. **Confirmado que pi 0.84.0 lee stdin**
  (`dist/main.js:45,664`, `dist/cli/initial-message.js:5-21`), así que la mitigación es
  mandarlo por stdin.
- **D5-F06** — la degradación del vault es **muda**, y un timeout congela "sin vault" para
  toda la corrida (`blk is blk2 → True`).
- **D5-F07** — sólo el prompt del orquestador conoce la valla del vault; implementer,
  package-reviewer y security-auditor reciben el contenido sin la doctrina.
- **Atribución de proyecto en tres carriles.** `set_agents_app.py:4141` exporta
  `SET_AGENTS_PROJECT`, `project_identity.py:56` le da **precedencia sobre el cwd**, y
  `_run_app_cli` hereda el entorno entero. Resultado: **el spawn atribuye su trabajo al
  proyecto del padre en vez de al del `spawn_cwd`**, corrompiendo `dispatches.project_key`.
  Reparado en `set_agents_spawn.py` (carril pi); `claude_code_spawn.py:574,637`,
  `codex_spawn.py:300,324` y `opencode_spawn.py:323,350` siguen igual. El parche son tres
  líneas por archivo: pasar `None` en `env` significa "desasignala en el hijo". **No cambies
  la firma de `_run_app_cli`** — está mockeada con firma exacta en `tests/test_pi_effort.py`
  y otros módulos.

> **Sobre la rama `worktree-agent-a1e28ec280c592315`**: tiene los cuatro arreglos de arriba
> **más una reimplementación completa y divergente de D5** (se la despachó contra una base
> sin D5 por un error de secuencia del orquestador). **La base de D5 de `main` se queda** —ya
> pasó review de seguridad—. De esa rama se portan **sólo los cuatro arreglos**, y el de
> degradación (F06) hay que **rehacerlo** sobre la arquitectura de `main`
> (`_fetch_vault_block` por spawner), no portarlo (usa una función compartida distinta).

### 2 · Terminar 028 — narración que enseña

Spec en `docs/specs/028-narracion-que-ensena/spec.md`, **enmendada tras un desafío
independiente que rechazó su primera guarda** (8 de 9 ataques la atravesaban, incluido el
caso literal de Federico con un espacio en vez de un guion). **No tiene state file: hay que
crearlo con `feature-state.py init`.**

- **N3a** `la-manana-que-se-entiende` — **ya integrado**. Es lo que hizo que la columna
  "Próximo paso" de `ai/state/STATUS.md` diga *"falta declarar el impacto de módulo — sin
  novedades hace 12 días"* en vez de `PACKAGE_ACCEPTED`. El "por qué" ya existía en
  `transitions.py` y `render_status.py:66` lo descartaba una línea antes de mostrarlo.
- **N1** `campos-que-obligan` — **parcial**. Su agente murió por watchdog sin commitear; el
  orquestador commiteó el árbol: rama **`worktree-agent-a47274084a7696ad1`, commit
  `6a1949a`**, 1784 líneas sobre `bec3dcf`, **sin revisar**. Trae `ai/scripts/narration_lint.py`
  (445 líneas), `tests/test_narracion_contrato.py` (575) y el ADR-0057 (156). Murió en plena
  segunda mordida (*"Mordida 2 — AC-02 milestone requeridness"*), así que **las mordidas están
  incompletas y hay que rehacerlas**.
  Campos `--learned/--next/--why/--alternative/--milestone` con guarda de **densidad de
  punteros por cláusula** (un cociente: rellenar no ayuda). El corpus de nueve ataques es
  **normativo y está en la spec**; la evidencia debe mostrarlos en rojo, y **B5 debe dar
  verde y estar declarado**.
- **N2** `doctrina-que-explica` — pendiente. Va **después** de N1: una doctrina que mande
  pasar un flag inexistente es una doctrina falsa.
- **N3b** — AC-15 y AC-16, pendientes, dependen de N1.

### 3 · Implementar 029 — convenciones antes del código

Spec en `docs/specs/029-convenciones-antes-del-codigo/spec.md`, escrita, desafiada y
**enmendada con seis bloqueantes resueltos**. Cero implementación. **Sin state file.**

El pedido de Federico: que el orquestador, ante *"haceme una web para scrapear Mercado
Libre"*, cierre convenciones antes de implementar —audiencia, alojamiento inicial y al
escalar, modelo de datos, tiempo real, mobile, embeddings— sin volverse un cuestionario y
sin inventar.

Lo más valioso que la spec descubrió: **el 80% ya existe y nadie lo enchufa**.
`Global/_canonical/skills/solution-baselines/references/*.md` tienen tablas
`| Eje | Postura | Umbral YAGNI |` por categoría, y `scraping-datos-ml.md:19` cubre
literalmente el ejemplo de Federico. Pero `grep -rn "solution-baselines"
Global/_canonical/agents/*.md` da **2 resultados**, y **el orquestador no lo nombra nunca**.

Cuatro paquetes: A1 `ejes-al-momento-de-hablar`, A2 `el-default-trae-su-umbral`,
A3 `una-decision-que-queda-escrita`, A4 `no-se-arranca-con-ejes-abiertos`.

### 4 · Deuda de proceso del orquestador

- **028, 029 y 030 no existen en la máquina de estados.** `STATUS.md` y el digest no las
  ven: el tablero dice que lo único en vuelo es 025. Hay que correr `feature-state.py init`
  para las tres. **Es la misma familia de defectos que 027 vino a reparar**, cometida por el
  orquestador.
- **030 no tiene spec** — sólo evidencia en
  `docs/specs/030-guardas-que-no-se-pueden-prefijar/evidence/S1-implementer.md` y ADR-0059.
- **El gate completo no se corrió limpio** tras las últimas integraciones.
- **La instalación quedó 4 archivos atrás** (`./build.sh --install --yes`, deja backup).

### 5 · Deuda técnica registrada, no reparada

Todas en `ai/state/decisions-log.jsonl` con su medición. Las que más pesan:

- **El CI lleva desde el 2026-08-03 en rojo**, por tres causas distintas, ya diagnosticadas:
  Linux (3 tests exigen credenciales vivas, **no pueden pasar en un runner hospedado**);
  macOS (`/var` es symlink y `_private_dir` rechaza ancestros symlink — los tests deberían
  usar `Path(td).resolve()`); Windows (`import pwd` sin guarda en `set_agents_app.py:14`, y
  el paso `Compile python scripts` pasa en verde porque `py_compile` **no importa** el módulo).
- **`log-decision` deduplica por `(slug, title, decision)` sin `feature_id`**: dos features
  con el mismo texto colisionan y la segunda recibe `deduped: true` **sin escribir fila**.
- **`freeze-candidate` compara HEAD contra HEAD** cuando el trabajo está sin commitear, mide
  cero, y `cli_repair.py` deriva un techo de reparación de **cero líneas** — el paquete no se
  puede reparar nunca más.
- **`matching_modules`** (`render_modules.py:104-125`) es ciego a los directorios pelados en
  `owned_paths`, así que la detección de impacto da cero hits.
- **Cuatro tests leen `ai/state/project.json`**, que está gitignoreado desde 024/C1: **la
  suite no puede dar verde en un clon fresco**, y el repo es público.
- **`MODEL_PIN_UNAVAILABLE` y `MODEL_METADATA_INFERRED` siguen sin filtrar** en
  `_decide_status`. La causa raíz es estructural: cada vez que `service.py` agrega un reason
  code "purely additive", `routing_cli.py` queda atrás. El arreglo durable es una lista
  nombrada de prefijos informativos **declarada junto a donde se emiten**.
- **`generate.py:186-197`** tiene una **cuarta copia** del invariante de composición de shell,
  en globs para la lane de OpenCode, con agujeros distintos a los tres guardas de Python.
- **`git show HEAD:<ruta>` y `./build.sh --output` quedaron denegados** por la política nueva.
  Son huecos de disponibilidad, no de seguridad, y son una línea cada uno.

### 6 · Lo que espera decisión humana

- **024 sigue `BLOCKED`**: `generate.py:475` shippea el codename de un cliente real al
  `orchestrator.md` que se instala en la máquina de cada tercero, y el repo es **público**.
  Tres opciones: sanear sólo el árbol actual, reescribir historia, o volver el repo privado.
- **Los 6 commits de esta sesión no están pusheados.**

---

## Cómo verificar que algo está realmente hecho

No confíes en un reporte. Estos son los comandos que este repo usa para medir:

```sh
./build.sh --check                    # SELF_SCAFFOLD_SYNC_OK + GLOBAL_TREE_SYNC_OK + BUILD_CHECK_PASS
git diff --check                      # limpio
setsid nohup ./ai/scripts/verify.sh > /tmp/gate.log 2>&1 &   # ~700 s, VERIFY_PASS al final
python3 ai/scripts/check-owned-paths.py --state-file <state> --package-id <pkg> --baseline HEAD
python3 ai/scripts/feature-state.py status <feature-id>
```

Y para un paquete concreto: corré su comportamiento, no su grep. Ejemplos reales de esta
sesión que sirven de molde:

```sh
# D1: la superficie encogió de verdad
python3 ai/scripts/set_agents_app.py --help | grep -cE '^\s+--'          # 41
python3 ai/scripts/set_agents_app.py --help --avanzado | grep -cE '^\s+--'  # 71

# D4: desinstalar un CLI no toca los otros
#   instalar dos con --home temporal, desinstalar uno, hashear el otro antes y después

# 030: la política sigue cerrada y el harness sigue funcionando
python3 -c "import sys;sys.path.insert(0,'ai/scripts');import coord_policy as c;print(c.allowed('fd . -X touch p'), c.allowed('git status --porcelain'))"
```

---

## Ramas de agente que valen la pena (y las que no)

El repo quedó con veinte ramas `worktree-agent-*`. **Casi todas son ruido**: apuntan a un
commit viejo porque su agente nunca commiteó y su trabajo ya está integrado en `main`. Las
únicas cuatro con contenido propio útil:

| rama | commit | qué tiene |
|---|---|---|
| `worktree-agent-a47274084a7696ad1` | `6a1949a` | **028/N1 parcial**: `narration_lint.py` (445), `test_narracion_contrato.py` (575), ADR-0057. Mordidas incompletas. |
| `worktree-agent-a1e28ec280c592315` | `6102f96` | **025 spawners parcial**: vault por stdin, scrub en los 3 carriles. Tests del scrub a medias. |
| `worktree-agent-a0475a05026769224` | `c034277` | Repair de D5 **ya integrado en `main`**. Sólo referencia. |
| `worktree-agent-a034…`/`a062…`/etc. | varios | Ya integrados. Ignorar. |

**Cómo distinguir señal de ruido**: `git diff bec3dcf <rama> --numstat`. Si el número es
grande *y* la rama apunta a un commit anterior a `bec3dcf`, es ruido — su trabajo ya está
en `main` y el diff sólo mide lo que `main` avanzó después. Las dos primeras filas de la
tabla apuntan a commits **posteriores** a `bec3dcf`: ésas sí tienen contenido nuevo.

Cuando termines de portar lo útil, borralas: `git branch -D $(git branch --list
'worktree-agent-*' | tr -d ' ')`.

## Por qué murieron siete agentes en esta sesión

Vale saberlo para no repetirlo:

- **Cinco de golpe** por límite de sesión de Anthropic. No fallaron en su tarea. La doctrina
  manda relanzar una vez con otro modelo y persistir la causa; funcionó (haiku tenía cuota).
- **Dos por el watchdog de 600 s sin salida**, los dos por correr algo largo sin heartbeat.
- **Lo único que se salvó de todos ellos fue lo que ya estaba escrito en un archivo.** Por eso
  todos los spawns de esta sesión terminaron pidiendo: escribí la evidencia mientras trabajás,
  y commiteá antes de reportar.
