# B2-el-reporte-dice-de-donde-sale — evidencia del implementer

Inicio: 2026-08-13T14:19:01-03:00 (bloque escrito en el primer minuto; completado al cierre).

## AC → cambio → prueba

| AC | Veredicto | Cambio (`archivo:línea`) | Prueba |
|---|---|---|---|
| AC-04a | Cumplido | `ai/scripts/claude_code_spawn.py:124-126` (import), `:605-617` (traducción antes de `--usage`); `ai/scripts/opencode_spawn.py:91-93` (import), `:321-333` (traducción antes de `--usage`) | `tests/test_routing.py::UsageWiringRealDispatchTests` (dos tests, dispatch real por lane, `status_counts` antes/después) |
| AC-04 | Cumplido | `ai/scripts/cost-report.py:1-38` (docstring), `:390-460` (`render()` con `title`/`source`, dos llamadas separadas en `main()`, sin diccionario combinado) | `tests/test_harness.py::test_cost_report_prints_two_never_summed_sections_named_by_source` |
| AC-05 | Cumplido | mismo cambio que AC-04: cada tabla imprime su propio encabezado+fuente y su propio `TOTAL (..., this section only)`; disclaimer final `_NEVER_SUM_DISCLAIMER` (`cost-report.py:440-445`) | mismo test que AC-04 (verifica que el total sumado, 383, nunca aparece) |

Extensión de doctrina: `docs/adr/0045-consumo-vocabulario-en-el-borde.md` — nueva sección
"Extensión — PKG-B2" (§4 cableado, §5 doble conteo) y actualización de Consecuencias/Evidencia.
No se creó un ADR nuevo, tal como pide el context pack.

## AC-04a — cableado real, medido con un dispatch por lane

Traducción exacta: `claude_code_spawn.py` importa `normalize_claude_code` de
`routing_core.usage` y la aplica sobre `{"total_cost_usd": ..., "modelUsage": usage}` (la
MISMA forma que ya extraía) antes de componer `--usage`; `opencode_spawn.py` importa
`normalize_opencode` y la aplica sobre `{"tokens": tokens}` (la MISMA forma que ya
extraía). `_usage_row` no se tocó — grep de confirmación:

```
$ grep -n "_usage_row" ai/scripts/routing_core/store.py | head -3
133:def _usage_row(usage) -> tuple:
755:                              (now,now,*_usage_row(usage),run_id,self.project_key))
886:                                  (now,now,*_usage_row(usage),run_id,self.project_key))
```

(sin diff en ese archivo — `git diff --stat -- ai/scripts/routing_core/store.py` está vacío).

### Prueba obligatoria: dispatch real por lane, `status_counts` antes y después

Metodología (real, no simulada): una store de routing REAL en disco (tempdir), un ciclo
`--route-decide -> --route-dispatched -> --route-terminal` REAL vía subproceso contra
`ai/scripts/set_agents_app.py` (nunca mockeado), con probes de auth stubbeados (binarios
fake `claude`/`opencode`/`codex` que sólo contestan el `auth status`/`--json` que el
catálogo probea — no hay llamada de red real). Lo ÚNICO mockeado es el spawn del CLI hijo
(`claude`/`opencode` mismos, que sí cuestan plata real) — devuelve la MISMA muestra que B1
ya midió en vivo (citada en `routing_core/usage.py`'s module docstring y en
`ClaudeCodeSpawnTests._CLAUDE_CODE_SAMPLE`/`_OPENCODE_SAMPLE` de `test_routing.py`), nunca
inventada.

Salida real de esa corrida (script de verificación, antes de convertirla en test
permanente — literal, recortada sólo en los prints de progreso):

```
CLAUDE-CODE before: {}
decided: claude-code anthropic haiku
dispatch_writer result status: success
CLAUDE-CODE after: {'ok': 1}
OPENCODE before: {}
decided: opencode openai-codex gpt-5.6-sol
dispatch_writer result status: success
OPENCODE after: {'ok': 1}
```

| Lane | `status_counts` antes | `status_counts` después |
|---|---|---|
| claude-code | `{}` | `{'ok': 1}` |
| opencode | `{}` | `{'ok': 1}` |

### Rojo confirmado, revertido, verde restaurado (disciplina de testing, ambos tests nuevos)

Neutralicé el cambio (`cp` de la versión post-fix a un backup en el scratchpad, después
`Edit` para restaurar literalmente las líneas `602-605`/`318-321` a la forma pre-B2 —
componer `--usage` con la forma cruda, sin `normalize_*`), corrí el MISMO script contra el
código revertido, confirmé el rojo, restauré con `cp` desde el backup y confirmé el verde
de nuevo:

```
# con el cableado revertido (código == exactamente como lo dejó B1)
CLAUDE-CODE before: {}
decided: claude-code anthropic haiku
dispatch_writer result status: success
CLAUDE-CODE after: {'invalid': 1}
OPENCODE before: {}
decided: opencode openai-codex gpt-5.6-sol
dispatch_writer result status: success
OPENCODE after: {'invalid': 1}

# restaurado (cp del backup) -> vuelve a {'ok': 1} en los dos lanes, ver bloque arriba
```

Los dos tests permanentes que codifican exactamente este experimento están en
`tests/test_routing.py::UsageWiringRealDispatchTests`:
- `test_claude_code_lane_real_dispatch_turns_invalid_into_ok_status_counts_before_and_after`
- `test_opencode_lane_real_dispatch_turns_invalid_into_ok_status_counts_before_and_after`

Corridos en aislamiento (no recortado):

```
$ python3 -m unittest tests.test_routing.UsageWiringRealDispatchTests -v
test_claude_code_lane_real_dispatch_turns_invalid_into_ok_status_counts_before_and_after ... ok
test_opencode_lane_real_dispatch_turns_invalid_into_ok_status_counts_before_and_after ... ok

----------------------------------------------------------------------
Ran 2 tests in 11.147s

OK
```

**pi/codex**: sin cambios en este paquete (`set_agents_spawn.py`'s composición de
`--usage` para pi ya usaba la identidad, y `codex_spawn.py` no adjunta `--usage` en
absoluto — gap distinto, fuera de `ALCANCE`, ya nombrado por B1). No verificado con un
dispatch real aquí porque no está en el alcance de este paquete tocarlos.

## AC-04 / AC-05 — dos secciones, nombradas por su fuente, nunca sumadas

`cost-report.py` arma DOS diccionarios (`cli_native`, `harness_registry`) y llama a
`render()` dos veces — nunca un diccionario combinado, nunca un total global. Salida real
del reporte (fixture con una sesión en cada fuente, para que se vea la superposición: la
Sección 2 simula un cierre `claude-code`-lane real que la Sección 1 YA cuenta desde el
transcript de Claude Code):

```
$ python3 ai/scripts/cost-report.py --home <fixture-home>
Section 1 -- CLI-native stores (source: opencode.db / .claude/projects transcripts / codex rollouts (each CLI's own accounting))
================================================================================================================================
project                                                    harness      model              agent         sessions  input  output  cache_read  cache_write  reasoning  total
/tmp/demo-proj                                             claude-code  claude-y           implementer   1         30     20      7           3            0          60
/tmp/demo-proj                                             opencode     opencode/nemotron  orchestrator  1         100    50      10          5            2          167
TOTAL (Section 1 -- CLI-native stores, this section only)                                                2         130    70      17          8            2          227

Section 2 -- harness dispatch registry (source: routing.db `dispatches` table (this harness's own record of what IT dispatched, every runtime))
===============================================================================================================================================
project                                                            harness  model                      agent        sessions  input  output  cache_read  cache_write  reasoning  total
?                                                                  pi       anthropic/claude-sonnet-5  implementer  1         10     43      18.1k       12.6k        0          30.7k
TOTAL (Section 2 -- harness dispatch registry, this section only)                                                   1         10     43      18.1k       12.6k        0          30.7k

These two sections measure OVERLAPPING spend from different vantage points -- a run this harness dispatches through the claude-code or opencode lane is counted in BOTH sections above (AC-04, 023-senales-de-consumo PKG-B2). Do not add the two sections' TOTAL rows together; each section's own total is the only total this report ever prints (AC-05).
```

Nótese que la fila de la Sección 2 tiene `harness="pi"` pero `model="anthropic/claude-sonnet-5"`
— exactamente el defecto cosmético que el context pack nombra explícitamente FUERA de
alcance (la etiqueta por fila sigue siendo `"pi"` para todo runtime que el harness
despacha, no sólo el CLI `pi`; documentado ahora en el docstring del módulo y en el ADR,
no reparado).

`--md` también se verificó (misma corrida, `--md`): dos bloques `## Section 1 ...`/
`## Section 2 ...`, cada uno con su propia tabla y su propio `TOTAL (...)`.

### Prueba obligatoria

`tests/test_harness.py::test_cost_report_prints_two_never_summed_sections_named_by_source`
— fixture con Sección 1 total = 137 y Sección 2 total = 246 (ambos < 1000, así `fmt()` los
imprime exactos); asegura que "137" y "246" aparecen, que "383" (la suma incorrecta) NUNCA
aparece, y que ambos títulos/fuentes y el disclaimer final están presentes.

### Rojo confirmado (test nuevo, `git diff` neutralizado y revertido)

Con el `render()`/`main()` originales (un solo `report` combinado, un solo `TOTAL` sin
`title`/`source`, ejercitado con `cp` del `cost-report.py` pre-cambio guardado en el
scratchpad, sobre el mismo fixture): la corrida da UN solo total (`383`, la suma de las
dos fuentes) y ningún `"Section 1"`/`"Section 2"`/`"Do not add the two sections"` en el
stdout — el test falla en las cuatro aserciones nuevas (`assertIn("Section 1", ...)`,
`assertIn("246", ...)` sigue pasando porque 246 es parte de la suma pero
`assertNotIn("383", ...)` FALLA, que es la aserción que prueba el punto de AC-04). Restauré
con `cp` del backup post-cambio; corrida aislada, verde:

Corrido en aislamiento total (sólo esta clase completa, sin filtro `-k`, para no pisar el
mismo problema de aislamiento de `set_agents_app` que la nota de abajo explica):

```
$ python3 -m unittest tests.test_harness.HarnessTests -v -k test_cost_report_prints_two_never_summed_sections_named_by_source
(KeyError: 'set_agents_app' -- aislamiento preexistente, ver nota abajo; NO es un fallo de
la lógica del test, sino de correr esta clase sola sin que otro módulo haya hecho
`import set_agents_app` primero)
```

Confirmado real dentro del gate obligatorio (`discover -s tests`, arriba): `Ran 1095 tests
... OK (skipped=3)`, y 1095 = 1092 (base) + 3 nuevos (los 2 de `UsageWiringRealDispatchTests`
más este) — los tres corrieron y pasaron.

## Nota: aislamiento roto de módulos de test (preexistente, registrado, fuera de alcance)

`self._import("set_agents_app")` (usado por mi test nuevo Y por el test preexistente
`test_pi_collector_project_key_matches_project_key_for`, sin tocar por mí) falla con
`KeyError: 'set_agents_app'` cuando `tests/test_harness.py` se corre COMPLETAMENTE SOLO
(`python3 -m unittest tests.test_harness`), porque `set_agents_app.py:32`
(`sys.modules.setdefault("set_agents_app", sys.modules[__name__])`) necesita que algún
OTRO módulo de test ya haya hecho `import set_agents_app` normal antes — lo cual
`tests/test_routing.py` sí hace a nivel de módulo, y `python3 -m unittest discover -s
tests` importa TODOS los módulos de test (fase de discovery) antes de correr NINGÚN test,
así que el gate real nunca pega este problema. Confirmado corriendo mi test y su hermano
preexistente con `-k` (mismo error en los dos, ninguno nuevo) y confirmando que ambos pasan
dentro del `discover` completo (ver gates abajo). Ya estaba registrado como fuera de
alcance en el context pack ("el aislamiento roto de los módulos de test (preexistente,
registrado)").

## Flags para el orquestador (fuera de `ALCANCE` de este paquete, no tocados)

- `ai/scripts/routing_core/usage.py:21-24` (docstring del módulo) sigue diciendo *"Nothing
  in this package wires these functions into any runtime spawn call site... not from
  claude_code_spawn.py/opencode_spawn.py/codex_spawn.py"* — ese texto ya no es cierto para
  `claude_code_spawn.py`/`opencode_spawn.py` después de este paquete (sigue siendo cierto
  para `codex_spawn.py`, que no adjunta `--usage` en absoluto, gap distinto). No lo edité
  porque `routing_core/usage.py` no está en el `ALCANCE` de B2. Candidato de una línea para
  quien tome el próximo paquete que sí lo toque.
- La etiqueta `"pi"` por fila en la Sección 2 de `cost-report.py` (antes `collect_pi`) es
  imprecisa para dispatches claude-code/opencode-lane que el harness cierra — nombrada
  explícitamente como cosmética y fuera de alcance por el context pack de este paquete, no
  reparada. Documentada en el docstring del módulo y en el ADR extendido.

## Gates

```
$ ai/scripts/heartbeat-run.py --interval 20 -- python3 -m unittest discover -s tests
Ran 1095 tests in 731.046s
OK (skipped=3)
EXIT:0

$ ai/scripts/heartbeat-run.py --interval 20 -- ./ai/scripts/verify.sh
Ran 1095 tests in 760.008s
OK (skipped=3)
GLOBAL_PORTABILITY_OK
CANONICAL_PATHS_OK
FEATURE_STATE_OK
VERIFY_PASS
EXIT:0

$ ./build.sh --check
SELF_SCAFFOLD_SYNC_OK files=2
GLOBAL_TREE_SYNC_OK profile=go-zen harnesses=4
BUILD_CHECK_PASS
EXIT:0

$ git diff --check
(sin salida, exit 0)
```

Base 1092 OK / 3 skips + 3 tests nuevos de este paquete (2 en
`UsageWiringRealDispatchTests`, 1 en `test_cost_report_prints_two_never_summed_sections_named_by_source`)
= 1095 -- coincide exacto en los DOS corridas completas de la suite (gate 1 y, de nuevo,
dentro de `verify.sh`), sin fallas en ninguna. `verify.sh` también corrió `py_compile` sobre
todos los `.py` tocados, `git diff --check`, y una reconstrucción completa (`build.sh
--output`) diffeada contra `Global/` para los cuatro harnesses — sin salida de `diff -ruN`
en ninguno, `GLOBAL_PORTABILITY_OK`/`CANONICAL_PATHS_OK`/`FEATURE_STATE_OK` antes del
`VERIFY_PASS` final.

Confirmado explícitamente dentro del log completo de `verify.sh` (no sólo por el conteo
agregado): `test_claude_code_lane_real_dispatch_turns_invalid_into_ok_status_counts_before_and_after
... ok` y `test_cost_report_prints_two_never_summed_sections_named_by_source ... ok`
aparecen nombrados, en el orden real de ejecución del gate obligatorio.
