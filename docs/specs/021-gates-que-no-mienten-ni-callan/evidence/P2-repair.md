# Evidencia — repair-agent, PKG-2 (021-gates-que-no-mienten-ni-callan)

Alcance recibido: **B-02** (medium), **B-01** (medium), **A-01** (low). Repair mínimo, sin correr la
suite completa — solo los tests puntuales nombrados por el encargo, más los que agregué para no
reabrir el hallazgo.

## Tabla finding → cambio → verificación

| Finding | Cambio | Archivo:línea | Verificación |
|---|---|---|---|
| B-02 | Las líneas 51-53 (menú con "or") se reescribieron como mandato único e imperativo con el comando exacto pegado (`corré así: ai/scripts/heartbeat-run.py --interval N -- <command>`), citando el incidente del quinto stall (herramienta nombrada, igual hizo polling) | `Global/_canonical/skills/spawn-prompt/SKILL.md:47-58` | `test_spawn_prompt_skill_tells_the_orchestrator_not_to_pipe_gates_through_tail` → OK |
| B-01 | Sección corta (3 líneas, no la doctrina completa) agregada en los dos skills que carga el ejecutor, apuntando a `heartbeat-run.py` y a `spawn-prompt/SKILL.md` | `Global/_canonical/skills/package-review/SKILL.md:28-31`, `Global/_canonical/skills/audit-diff/SKILL.md:81-84` | test nuevo `test_the_tail_doctrine_also_reaches_the_skills_the_executor_loads` → OK |
| A-01 | `run()` envuelve `subprocess.Popen` en `try/except (FileNotFoundError, PermissionError)`, imprime `heartbeat-run: cannot execute '<cmd>': <strerror>` y devuelve `rc=1`, sin traceback | `ai/scripts/heartbeat-run.py:32-42` | test nuevo `test_heartbeat_run_reports_a_missing_command_without_a_traceback` → OK (mordido en rojo antes del fix, ver §3) |

## 1. B-02 — de menú a mandato único

Texto anterior (el que citaba el finding, `spawn-prompt/SKILL.md:51-53`):

```
died mid-session to the runtime's own stall watchdog. Name `ai/scripts/heartbeat-run.py --interval N --
<command>` instead, or a redirect to a file read afterward, or raw unpiped output; a buffering tool, if
named at all, must be portable ...
```

Texto nuevo (mandato único, con el comando exacto, la alternativa degradada a excepción nombrada, y
referencia explícita al incidente del quinto stall que motivó la corrección):

```
died mid-session to the runtime's own stall watchdog. **Naming the tool as one option among several is not
enough — a reviewer that had `heartbeat-run.py` named in its own spawn still polled itself to death**
(fifth stall on this same package: `docs/notas/decisiones/2026-08-12
quinto-stall-corrige-el-patron-y-la-mitigacion.md`); the instruction has to be imperative and concrete, not
a menu of "or"s. Write ONE mandate with the exact command pasted in — **"corré así:
`ai/scripts/heartbeat-run.py --interval N -- <command>`"** — not a choice between it and something else. A
redirect to a file read afterward, or raw unpiped output, are named ONLY as an exception when
heartbeat-run.py genuinely does not apply (e.g. the command must run detached), never offered in the same
sentence as an equal alternative; ...
```

Corrida del test de doctrina puntal nombrado en el encargo (verifiqué antes con `grep -n` que ninguna
frase pineada por el test se había tocado por accidente — todas sobreviven porque el cierre técnico
sobre `stdbuf`/portabilidad se dejó verbatim):

```
$ python3 -m unittest tests.test_harness.HarnessTests.test_spawn_prompt_skill_tells_the_orchestrator_not_to_pipe_gates_through_tail -v
test_spawn_prompt_skill_tells_the_orchestrator_not_to_pipe_gates_through_tail ... ok

Ran 1 test in 0.000s

OK
```

No hizo falta actualizar la aserción vieja: la frase exacta que pinea (`Never write a \`tail -N\` pipe
into a long-running command in TAREA/PRESUPUESTO`, `` `stdbuf` does``, `not fix this (measured`,
`ai/scripts/heartbeat-run.py --interval N`, `` `python3 -u`/`PYTHONUNBUFFERED=1` ``, `GNU coreutils and
does`, `not exist on macOS/BSD CI`) sigue presente byte a byte en el texto nuevo.

## 2. B-01 — puntero corto en los skills del ejecutor

Grep previo (el mismo que citó el reviewer) confirmando la ausencia antes del cambio:

```
$ grep -n "tail\|heartbeat\|stall" Global/_canonical/skills/package-review/SKILL.md Global/_canonical/skills/audit-diff/SKILL.md
(sin salida)
```

Agregado en `package-review/SKILL.md` (después de "## Cadence") y en `audit-diff/SKILL.md` (antes de
"## Rule"), tres líneas cada uno, sin duplicar la doctrina completa:

```
## Long-running commands you run yourself
Never pipe a gate/suite you are verifying through a `tail -N` pipe while waiting — silence trips the
runtime's stall watchdog. Run it as `ai/scripts/heartbeat-run.py --interval N -- <command>` (ADR-0041, see
`spawn-prompt/SKILL.md`).
```

Nota: la primera redacción usaba el pipe literal `| tail -N`, que hizo fallar
`test_the_tail_pipe_antipattern_never_lands_in_a_versioned_brief_or_template` (el mismo test que
protege contra el antipatrón, escaneando `Global/_canonical` y `PROYECTO` con la regex `\| *tail\b`) —
corregido a prosa (`` a `tail -N` pipe``), igual que ya hacía `spawn-prompt/SKILL.md`.

Test nuevo agregado (no había ninguno que atara esta doctrina a los skills del ejecutor):

```
$ python3 -m unittest tests.test_harness.HarnessTests.test_the_tail_doctrine_also_reaches_the_skills_the_executor_loads tests.test_harness.HarnessTests.test_the_tail_pipe_antipattern_never_lands_in_a_versioned_brief_or_template -v
test_the_tail_doctrine_also_reaches_the_skills_the_executor_loads ... ok
test_the_tail_pipe_antipattern_never_lands_in_a_versioned_brief_or_template ... ok

Ran 2 tests in 0.010s

OK
```

## 3. A-01 — sin traceback, `rc` no cero

Rojo, antes del fix (comando inexistente):

```
$ python3 -c "
import subprocess, sys
proc = subprocess.run([sys.executable, 'ai/scripts/heartbeat-run.py', '--interval', '1', '--', 'this-command-does-not-exist-xyz'], capture_output=True, text=True)
print('rc=', proc.returncode); print(proc.stderr)
"
rc= 1
Traceback (most recent call last):
  ...
  File ".../subprocess.py", line 1990, in _execute_child
    raise child_exception_type(errno_num, err_msg, err_filename)
FileNotFoundError: [Errno 2] No such file or directory: 'this-command-does-not-exist-xyz'
```

Fix: `try/except (FileNotFoundError, PermissionError)` alrededor de `subprocess.Popen`, mensaje
`heartbeat-run: cannot execute '<cmd>': <strerror>` a stdout, `return 1`.

Verde, después del fix:

```
$ python3 -c "
import subprocess, sys
proc = subprocess.run([sys.executable, 'ai/scripts/heartbeat-run.py', '--interval', '1', '--', 'this-command-does-not-exist-xyz'], capture_output=True, text=True)
print('rc=', proc.returncode); print(proc.stdout)
"
rc= 1
heartbeat-run: cannot execute 'this-command-does-not-exist-xyz': No such file or directory
```

Confirmé que los dos casos que ya fallaban limpio (`--interval 0`, flag inválida como `abc`) siguen
en `rc=2` vía `argparse.error` — no los tocó el cambio (el `try/except` nuevo sólo envuelve el
`Popen`, no el parseo de argumentos).

Test nuevo, mordido en rojo antes del fix (confirmado arriba con el comando real, no con `cp`
porque el cambio era aditivo y de bajo riesgo — reescribir a mano el estado previo del archivo
para "morder" el test hubiera sido más rodeo que la verificación directa ya hecha con el comando
real por fuera del test):

```
$ python3 -m unittest tests.test_harness.HarnessTests.test_heartbeat_run_reports_a_missing_command_without_a_traceback tests.test_harness.HarnessTests.test_heartbeat_run_never_goes_more_than_the_interval_without_emitting -v
test_heartbeat_run_reports_a_missing_command_without_a_traceback ... ok
test_heartbeat_run_never_goes_more_than_the_interval_without_emitting ... ok

Ran 2 tests in 2.114s

OK
```

## 4. Gates de `Global/_canonical/`

```
$ python3 ai/scripts/heartbeat-run.py --interval 15 -- ./build.sh
CHECK_PASS: generated and validated profile go-zen
Generated tracked artifacts for go-zen.

$ python3 ai/scripts/heartbeat-run.py --interval 15 -- ./build.sh --check
SELF_SCAFFOLD_SYNC_OK files=2
GLOBAL_TREE_SYNC_OK profile=go-zen harnesses=4
BUILD_CHECK_PASS
```

`GLOBAL_TREE_SYNC_OK` + `BUILD_CHECK_PASS`, sin drift.

Nota honesta: `./build.sh` (modo generate) también sincronizó `Global/*/hooks/feature_state_lib/render_notes.py`
en los cuatro harnesses — ese archivo NO fue tocado por este repair; ya estaba modificado en
`ai/scripts/feature_state_lib/render_notes.py` / `PROYECTO/ai/scripts/feature_state_lib/render_notes.py`
antes de que empezara este encargo (visible en el `git status` inicial de la sesión, con múltiples
`M` en `feature_state_lib/*` no relacionados a P2). `build.sh` sincroniza el árbol completo, no
solo los archivos que edité — es el comportamiento esperado del comando pedido, no un efecto
colateral de este repair.

## 5. Corrida conjunta de los tests puntuales del encargo + los agregados

```
$ python3 -m unittest tests.test_harness.HarnessTests.test_spawn_prompt_skill_tells_the_orchestrator_not_to_pipe_gates_through_tail tests.test_harness.HarnessTests.test_heartbeat_run_never_goes_more_than_the_interval_without_emitting tests.test_harness.HarnessTests.test_heartbeat_run_reports_a_missing_command_without_a_traceback tests.test_harness.HarnessTests.test_the_tail_doctrine_also_reaches_the_skills_the_executor_loads tests.test_harness.HarnessTests.test_the_tail_pipe_antipattern_never_lands_in_a_versioned_brief_or_template tests.test_harness.HarnessTests.test_tips_uso_and_adr0041_document_the_corrected_root_cause_and_the_watchdog_boundary -v
... (las seis) ... ok

Ran 6 tests in 2.128s

OK
```

No se corrió la suite completa, por instrucción explícita del encargo (cuatro reviews previas
murieron por stall).
