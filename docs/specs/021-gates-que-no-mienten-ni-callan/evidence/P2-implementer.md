# Evidencia — PKG-2 `P2-gates-que-no-callan` (021-gates-que-no-mienten-ni-callan)

ADR extendido: `docs/adr/0041-build-check-verifies-global.md` (sección nueva agregada por este
paquete, no un ADR nuevo).

Estado: EN PROGRESO — este archivo se guarda a disco a medida que avanza (checkpoint: cuatro
instancias murieron por stall en esta sesión, ver más abajo el arreglo aplicado a mí mismo).

## 0. Autoaplicación — cómo corro yo los comandos largos en este paquete

Ningún comando de este paquete se pipea a `tail`. Para la suite completa (7-10 min) uso
`run_in_background` (nunca `timeout N ... | tail`) y reviso el log completo después, o
`ai/scripts/heartbeat-run.py` una vez implementado. Evidencia de cada corrida real se pega abajo,
completa o marcada como recortada.

## 1. Tabla AC → cambio → prueba

| AC | Cambio | Archivo:línea | Prueba |
|---|---|---|---|
| AC-06 | `heartbeat-run.py`: corre el comando dado, reenvía su stdout+stderr combinado línea por línea a medida que llegan (nunca espera EOF) e inyecta un latido propio si pasan `--interval` segundos (default 60) sin una línea real | `ai/scripts/heartbeat-run.py` (archivo nuevo, 96 líneas) | `tests/test_harness.py:9013` `test_heartbeat_run_never_goes_more_than_the_interval_without_emitting` — subproceso sintético, umbral reducido (0.3s), gaps medidos al LEER (nunca vía `tail`). Mordida en §4 |
| AC-07 | Doctrina nueva en `TIPS-USO.md`: patrón prohibido `\| *tail -N`, tres patrones correctos en orden de preferencia (flujo crudo, archivo+lectura posterior, `heartbeat-run.py`), y aclaración de portabilidad (`python3 -u`/`PYTHONUNBUFFERED=1`, nunca `stdbuf`) | `TIPS-USO.md:86-110` (sección nueva "Running long commands without going silent") | `tests/test_harness.py:9090` `test_tips_uso_and_adr0041_document_the_corrected_root_cause_and_the_watchdog_boundary`. Mordida en §4 |
| AC-08 | Queda escrito que el watchdog de 600s es del runtime del agente, no de este repo, y que el repo solo controla no crear la condición | `TIPS-USO.md:93-94` + `docs/adr/0041-build-check-verifies-global.md:150-206` (sección "Addendum — PKG-2") | Mismo test que AC-07 (`assertIn("agent runtime", tips)` + `assertIn("runtime del agente", adr)`) |
| AC-09 | Test que ancla que el patrón `\| *tail\b` (regex fijado por la spec, F-07) no aparece en ningún archivo versionado de `Global/_canonical/` (briefs) ni `PROYECTO/` (plantillas que se copian a cada proyecto nuevo). Prevención, no corrección: el patrón nunca vivió ahí (§2 de este documento no aplica acá — ver spec F-05) | `tests/test_harness.py:9055` `test_the_tail_pipe_antipattern_never_lands_in_a_versioned_brief_or_template` | Mordida en §4 (planté el patrón en `Global/_canonical/agents/orchestrator.md`, confirmé rojo nombrando el archivo, restauré con `cp`) |

## 2. Medición del defecto (línea base, antes de tocar nada)

Reproducido yo mismo, con `timeout` acotando cada repro (nunca corridas sin límite):

Caso 1 — la suite real pipeada a `tail -3`, cero bytes en 25s:

```
$ time timeout 25 bash -c 'python3 -m unittest discover -s tests -v 2>&1 | tail -3'
(sin salida)
real	0m25,004s
EXIT=124
```

Caso 2 — `stdbuf -oL` + `python3 -u` + `flush=True` explícito (el remedio que el primer
diagnóstico proponía) NO arregla nada: sigue en cero bytes en 8s, con un escritor sintético que
sí flushea cada línea:

```
$ time timeout 8 bash -c 'stdbuf -oL python3 -u -c "
import time, sys
for i in range(20):
    print(f\"line {i}\", flush=True)
    time.sleep(1)
" | tail -3'
(sin salida)
real	0m8,002s
EXIT=124
```

Caso 3 — control: el mismo escritor sintético, sin `tail` en la cadena, emite línea por línea
con normalidad:

```
$ time timeout 5 bash -c 'python3 -u -c "
import time
for i in range(20):
    print(f\"line {i}\", flush=True)
    time.sleep(1)
"'
line 0
line 1
line 2
line 3
line 4
real	0m5,003s
EXIT=124
```

Confirma la causa raíz corregida (F-04 de la spec): `tail -N` sin `-f` no puede emitir nada
hasta ver EOF, sea cual sea el buffering del escritor upstream (Caso 2 vs Caso 3, mismo escritor,
mismo flush explícito, la única diferencia es la presencia de `| tail -3`). El remedio no es
`stdbuf`.

## 3. Falsos positivos del grep, en las dos direcciones

Dirección 1 — un `grep` ingenuo por `tail` (sin anclar al pipe) da falsos positivos hoy, todos
dentro de "detail"/"details" (13 medidos, no los 10 de la spec porque el árbol cambió desde el
challenge; el patrón es el mismo):

```
$ grep -rn "tail" Global/_canonical/ | grep -vE "\| *tail\b" | wc -l
13
```

Dirección 2 — el patrón anclado `\| *tail\b` sobre `Global/_canonical/` y `PROYECTO/` da cero
hoy (prevención confirmada, AC-09/F-05 — nunca vivió en archivo versionado):

```
$ grep -rnE "\| *tail\b" Global/_canonical/ PROYECTO/
(sin salida)
```

Y en el propio test (`test_the_tail_pipe_antipattern_never_lands_in_a_versioned_brief_or_template`,
`tests/test_harness.py:9060-9070`) el mismo patrón se prueba contra fixtures sintéticas en ambas
direcciones: no dispara con `"...internal detail to clients"`/`"implementation details"`/`"full
detail only in server logs"` (dirección 1, no demasiado amplio), y sí dispara con
`"cmd | tail -3"`, `"cmd 2>&1 | tail -20"`, `"cmd|tail -f"`, `"long_cmd  |   tail -n 5"`
(dirección 2, no demasiado angosto — cuatro formas reales del pipe, con y sin espacios, con y
sin `2>&1` antes).

## 4. Mordida por test (neutralizar, rojo, revertir)

Las tres pruebas nuevas de este paquete, cada una neutralizada, confirmada en rojo, y revertida
con `cp` (nunca `git`):

**AC-06** — comenté la condición que emite el latido (`if False and silent_for >= interval:` en
`ai/scripts/heartbeat-run.py:65`):

```
$ python3 -m unittest -v tests.test_harness.HarnessTests.test_heartbeat_run_never_goes_more_than_the_interval_without_emitting
FAIL: ... AssertionError: 0 not greater than or equal to 2 : ['start', 'after-gap-one', 'after-gap-two']
Ran 1 test in 2.067s
FAILED (failures=1)
```
Restaurado con `cp` desde el backup pre-mutación; `diff` confirmó bytes idénticos; test vuelve a
`ok`.

**AC-09** — planté el patrón prohibido en un archivo real y versionado
(`Global/_canonical/agents/orchestrator.md`, apéndice con un comentario HTML citando
`python3 -m unittest discover -s tests -v 2>&1 | tail -3`):

```
$ python3 -m unittest -v tests.test_harness.HarnessTests.test_the_tail_pipe_antipattern_never_lands_in_a_versioned_brief_or_template
FAIL: ... AssertionError: Lists differ: ['Global/_canonical/agents/orchestrator.md:762'] != []
Ran 1 test in 0.011s
FAILED (failures=1)
```
Nombra el archivo y la línea correctos. Restaurado con `cp` desde el backup; `diff` confirmó
bytes idénticos; test vuelve a `ok`.

**AC-07/AC-08** — borré la frase clave de `TIPS-USO.md:88` (reemplazada por
`MUTATION-BITE-AC-07-AC-08`):

```
$ python3 -m unittest -v tests.test_harness.HarnessTests.test_tips_uso_and_adr0041_document_the_corrected_root_cause_and_the_watchdog_boundary
FAIL: ... AssertionError: 'Never pipe a long-running gate through `| tail -N`' not found in '...'
Ran 1 test in 0.002s
FAILED (failures=1)
```
Restaurado con `cp` desde el backup; `diff` confirmó bytes idénticos; test vuelve a `ok`.

Ningún backup usó `git checkout`/`git restore`/`git stash` — todos vía `cp` hacia/desde
`/var/tmp/claude/.../scratchpad/`.

## 5. Gates

Completado al final de la implementación — ver mensaje de cierre del implementer para la corrida
completa de la suite (972+3=975 esperados: base 972 + 3 tests nuevos de este paquete),
`./ai/scripts/verify.sh`, `./build.sh --check`, `py_compile`, y `git diff --check`.

## 6. AC-07 (relanzamiento acotado) — dónde vive la doctrina positiva y por qué ahí

Contexto de este relanzamiento: la instancia anterior había dejado AC-06/AC-08/AC-09 hechos y
verificados (arriba, §1-5), y había escrito la doctrina de `TIPS-USO.md:86-110` (fila AC-07 de la
tabla §1) — pero esa doctrina vive fuera de `Global/_canonical/`, así que documenta para quien la
lee a mano y **no propaga a un encargo nuevo**. El propio orquestador señaló esto al relanzar:
`Global/_canonical/` seguía sin tocar. No se rehizo nada de lo anterior; este paquete solo agrega
la pieza que faltaba.

### Dónde y por qué

`Global/_canonical/skills/spawn-prompt/SKILL.md` — no un nuevo archivo, no los 28 briefs de rol.
Justificación (superficie mínima elegida entre los dos candidatos del context pack): el propio
frontmatter del archivo se autodescribe como "The orchestrator's fixed spawn-message template
(ADR-0026) ... Load when composing ANY subagent spawn message" — es literalmente el único lugar
que el orquestador carga para redactar CUALQUIER encargo, incluidos los que corren un gate largo.
Los briefs de gate-runner/local-gate-runner (`Global/_canonical/agents/gate-runner.md`,
`local-gate-runner.md`) no calificaban: ejecutan exactamente los comandos que el orquestador les
da y tienen prohibido "invent commands" — no son quien compondría un `| tail -N`, es quien lo
recibiría ya escrito en TAREA/PRESUPUESTO. La fuente del patrón es siempre la redacción del
spawn, así que ahí es donde se corta.

Bullet agregado en la sección `## Rules`, `Global/_canonical/skills/spawn-prompt/SKILL.md:47-54`:

```
- **Never write a `tail -N` pipe into a long-running command in TAREA/PRESUPUESTO** (ADR-0041): without
  `-f`, `tail` cannot emit anything before EOF regardless of the upstream's own buffering — `stdbuf` does
  not fix this (measured: an explicitly-flushed writer piped through `stdbuf -oL` still emits nothing
  until the child exits). A worker watching that pipe looks stalled for the whole run, which is how agents
  died mid-session to the runtime's own stall watchdog. Name `ai/scripts/heartbeat-run.py --interval N --
  <command>` instead, or a redirect to a file read afterward, or raw unpiped output; a buffering tool, if
  named at all, must be portable (`python3 -u`/`PYTHONUNBUFFERED=1` — `stdbuf` is GNU coreutils and does
  not exist on macOS/BSD CI).
```

Los cuatro elementos pedidos están: (1) qué no hacer — el pipe a `tail -N`; (2) por qué —
`tail` sin `-f` no puede emitir antes de EOF y `stdbuf` no lo arregla (medido, la misma medición
que ya está en §2 de este documento y en el ADR); (3) qué hacer en cambio —
`heartbeat-run.py --interval N -- <command>`, redirect a archivo, o salida cruda sin pipe; (4)
portabilidad — `python3 -u`/`PYTHONUNBUFFERED=1`, nunca `stdbuf` (GNU coreutils, ausente en
macOS/BSD, donde corre CI). El texto describe el antipatrón en prosa ("a `tail -N` pipe"), nunca
lo escribe como pipe literal — verificado, ver mordida abajo.

Referencia agregada en `docs/adr/0041-build-check-verifies-global.md:191-197` (dentro del punto 2
del Addendum ya escrito por el relanzamiento anterior; no se creó sección nueva, no se tocó
ninguna de las frases que el test de AC-07/AC-08 ya verificaba) apuntando a esta ubicación y
explicando por qué `TIPS-USO.md` sola no alcanzaba.

### Propagación verificada a los cuatro árboles

```
$ ./build.sh
CHECK_PASS: generated and validated profile go-zen
Generated tracked artifacts for go-zen.

$ grep -n "Never write a" Global/opencode/skills/spawn-prompt/SKILL.md Global/claude-code/skills/spawn-prompt/SKILL.md Global/codex/skills/spawn-prompt/SKILL.md Global/pi/skills/spawn-prompt/SKILL.md
Global/opencode/skills/spawn-prompt/SKILL.md:47:- **Never write a `tail -N` pipe into a long-running command in TAREA/PRESUPUESTO** (ADR-0041): without
Global/claude-code/skills/spawn-prompt/SKILL.md:47:- **Never write a `tail -N` pipe into a long-running command in TAREA/PRESUPUESTO** (ADR-0041): without
Global/codex/skills/spawn-prompt/SKILL.md:47:- **Never write a `tail -N` pipe into a long-running command in TAREA/PRESUPUESTO** (ADR-0041): without
Global/pi/skills/spawn-prompt/SKILL.md:47:- **Never write a `tail -N` pipe into a long-running command in TAREA/PRESUPUESTO** (ADR-0041): without

$ ./build.sh --check
SELF_SCAFFOLD_SYNC_OK files=2
GLOBAL_TREE_SYNC_OK profile=go-zen harnesses=4
BUILD_CHECK_PASS
```

Confirmado por `managed-files.txt` en los cuatro harnesses (`grep -n spawn-prompt`): las cuatro
copias de `skills/spawn-prompt/SKILL.md` están declaradas y sincronizadas.

### El test nuevo, con su mordida

`tests/test_harness.py:9113`
`test_spawn_prompt_skill_tells_the_orchestrator_not_to_pipe_gates_through_tail` — lee
`Global/_canonical/skills/spawn-prompt/SKILL.md` (la fuente canónica, no una copia generada) y
asserta, en fragmentos cortos porque la prosa envuelve en columna (mismo patrón que el test de
AC-07/AC-08 de la instancia anterior, comentado inline por la misma razón): la frase prohibitiva
completa, `stdbuf` does / not fix this (measured — partido por el salto de línea real del
archivo, verificado con `grep -n` antes de escribirlo), `ai/scripts/heartbeat-run.py --interval
N`, `` `python3 -u`/`PYTHONUNBUFFERED=1` ``, y GNU coreutils and does / not exist on macOS/BSD CI
(mismo partido). Cierra con un `assertIsNone` sobre el patrón exacto de AC-09
(`\| *tail\b`) aplicado al propio archivo: la guía que prohíbe el antipatrón no puede
contenerlo como pipe literal.

Mordida (neutralizar → rojo → `cp` → verde), con el mismo protocolo que las tres de la instancia
anterior — nunca `git checkout`/`git restore`/`git stash`:

```
$ cp Global/_canonical/skills/spawn-prompt/SKILL.md /var/tmp/.../scratchpad/SKILL.md.backup
```
Reemplacé la línea 47 por `- **MUTATION-BITE-AC-07** (ADR-0041): without` (dejando el resto del
párrafo intacto):
```
$ python3 -m unittest -v tests.test_harness.HarnessTests.test_spawn_prompt_skill_tells_the_orchestrator_not_to_pipe_gates_through_tail
FAIL: ... AssertionError: 'Never write a `tail -N` pipe into a long-running command in TAREA/PRESUPUESTO' not found in '...'
Ran 1 test in 0.002s
FAILED (failures=1)
```
Restaurado con `cp` desde el backup; `diff` confirmó bytes idénticos (`DIFF_EMPTY_CONFIRMED`);
`ok` de nuevo:
```
$ python3 -m unittest -v tests.test_harness.HarnessTests.test_spawn_prompt_skill_tells_the_orchestrator_not_to_pipe_gates_through_tail
ok
```

### Incidente propio — autoaplicación fallida, corregida en el momento

Reporto esto en detalle porque la advertencia de proceso de este relanzamiento es explícita sobre
afirmaciones que no resisten la re-ejecución, y porque es exactamente el defecto que este AC
existe para prevenir. Mi primer comando de la corrida completa fue:

```
ai/scripts/heartbeat-run.py --interval 5 -- python3 -m unittest discover -s tests 2>&1 | tail -15
```

Eso es el antipatrón, cometido por mí, en la tarea sobre el antipatrón. `heartbeat-run.py`
funcionó — emitió sus latidos sintéticos cada 5s — pero el `| tail -15` que agregué alrededor de
todo el pipeline volvió a bloquear cualquier emisión real de contenido hasta EOF, que es
exactamente lo que `heartbeat-run.py` no puede arreglar porque el problema está un nivel más
afuera. Maté el proceso a los ~3 minutos, confirmé que el archivo de salida solo tenía las 15
líneas de latido (nunca el progreso real de la suite), y para el resto de esta tarea usé
`run_in_background: true` de la herramienta Bash + `Read`/`wc -l` sobre el archivo de salida —
sin ningún pipe — para toda corrida larga.

### Incidente de proceso — falso rojo por mutación concurrente

La primera corrida completa de la suite (lanzada en background con el patrón correcto ya
corregido) dio `FAILED (failures=1, errors=1, skipped=2)` en
`test_check_and_native_codex_agents` y `test_build_check_detects_global_drift_and_names_the_file`
— ambos tests invocan `./build.sh --check` internamente. La causa: mientras esa corrida estaba
viva, hice la mordida de arriba (neutralizar `SKILL.md` → confirmar rojo → `cp` de vuelta) sobre
el mismo archivo canónico que esos dos tests regeneran y comparan — una carrera de mi propia
autoría, no una regresión real. Confirmado con el diff que el propio test imprimió: mostraba
exactamente `MUTATION-BITE-AC-07` en `Global/<harness>/skills/spawn-prompt/SKILL.md` contra la
versión sin mutar recién regenerada — la ventana de la mordida, capturada en pleno. Verifiqué el
estado limpio (`grep -n "Never write a"` con la frase real presente, `./build.sh --check` →
`BUILD_CHECK_PASS`) y relancé la suite completa sin ninguna mutación concurrente esta vez.

### Gates finales (corrida limpia, sin mutaciones concurrentes)

```
$ python3 -m unittest discover -s tests -v
...
Ran 977 tests in 431.332s

OK (skipped=2)
```
977 = 976 base (973 + AC-06/AC-08/AC-09) + 1 (AC-07, este relanzamiento). Cero failures, cero
errors, 2 skips (los mismos preexistentes gateados por `SET_AGENTS_PI_E2E`, no tocados).

```
$ ./build.sh --check
SELF_SCAFFOLD_SYNC_OK files=2
GLOBAL_TREE_SYNC_OK profile=go-zen harnesses=4
BUILD_CHECK_PASS

$ python3 -m py_compile ai/scripts/*.py ai/scripts/routing_core/*.py ai/scripts/feature_state_lib/*.py PROYECTO/ai/scripts/feature_state_lib/*.py tests/*.py
PYCOMPILE_OK

$ git diff --check
DIFF_CHECK_CLEAN
```

```
$ ./ai/scripts/verify.sh
...
Ran 977 tests in 431.898s

OK (skipped=2)
...
GLOBAL_PORTABILITY_OK
CANONICAL_PATHS_OK
FEATURE_STATE_OK
VERIFY_PASS
```

Todos los cuatro comandos de la sección Validación de la tarea corrieron y dieron el resultado
esperado, ninguno pipeado a `tail`. Archivos tocados por este relanzamiento (AC-07 exclusivamente
— nada de AC-06/AC-08/AC-09 se modificó):

- `Global/_canonical/skills/spawn-prompt/SKILL.md` (+8 líneas, bullet nuevo)
- `tests/test_harness.py` (+21 líneas, test nuevo)
- `docs/adr/0041-build-check-verifies-global.md` (+6 líneas, referencia dentro del punto 2 ya
  existente del Addendum)
- `Global/opencode/`, `Global/claude-code/`, `Global/codex/`, `Global/pi/` (regenerados por
  `./build.sh`, no editados a mano)
