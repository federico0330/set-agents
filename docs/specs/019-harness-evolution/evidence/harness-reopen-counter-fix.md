# Arreglo del motor de estado: `reopen` resetea el contador que lo bloqueó

No es un AC de la feature 019 — es la herramienta que quedó bloqueando el cierre de `P5-tools-discovery`.
Autorizado explícitamente por Federico (opción A, `ai/state/decisions-log.jsonl`, slug
`reopen-resetea-contadores-opcion-A-autorizada`). ADR-0039 (`docs/adr/0039-reopen-directed-counter-reset.md`)
documenta el diseño completo; este archivo es la evidencia de implementación.

## 1. El defecto, reproducido (no teórico)

`ai/state/features/019-harness-evolution.json`, paquete `P5-tools-discovery`, ANTES de este arreglo:

```
$ python3 -c "
import json
data = json.load(open('ai/state/features/019-harness-evolution.json'))
pkg = next(p for p in data['packages'] if p['package_id'] == 'P5-tools-discovery')
print('attempts:', pkg['attempts'])
print('status:', pkg['status'])
"
attempts: {'deep_review_cycles': 1, 'repair_batches': 10, 'spawns': 3, 'subdivisions': 0, 'verification_waivers': 0, 'verifications': 6}
status: delta_review_required
```

`max_verifications_per_package=6` (`ai/state/features/019-harness-evolution.json` → `budgets`). La séptima
llamada a `record-verification` (una por finding, error de proceso del orquestador, no del paquete) agotó el
budget. `_apply_verdicts` (`ai/scripts/feature-state.py:699`, antes del fix) bloquea **antes** de registrar
el veredicto — así que el finding nunca quedó verificado. `cmd_reopen` limpió el blocker y devolvió la
feature a `PACKAGE_PLANNING`, pero **no tocaba `package["attempts"]`**, que seguía en `verifications: 6`.
`require_verified` (`cli_review.py:277-289`) exige un `verified_verdict` para cerrar cualquier finding por
encima de `low`, y las dos únicas puertas de salida — `record-repair` (`cli_repair.py:220`) y
`record-delta-review --closed-finding` (`cli_repair.py:285`) — pasan por ahí. Resultado real: cinco findings
(`F-07..F-11`, todos `medium`) reparados en el árbol, imposibles de registrar como cerrados, y
`package_accept_ready` (`model.py:441`) rechazando la aceptación mientras esos `medium` siguieran abiertos.
`--skip-reason` tampoco era salida: exige que **todos** los findings abiertos sean `low`.

**Reproducción directa del mecanismo** (no depende del JSON de 019, que este arreglo no toca): la regresión
de abajo exhibe exactamente esta secuencia — agotar `max_verifications_per_package`, confirmar el bloqueo,
`reopen`, confirmar que record-verification vuelve a aceptar un veredicto — contra el harness real, vía
subprocess de `feature-state.py`.

## 2. El cambio (`archivo:línea`)

`ai/scripts/feature_state_lib/cli_lifecycle.py`:
- `block_with_reason` (línea 396) gana un parámetro opcional `counter: dict | None`. Cuando se pasa, se
  persiste tal cual en el blocker (`blocker["counter"] = counter`) — estructurado, nunca inferido del texto
  de `reason` (ver ADR-0039 §2, precedente SEC-001 de `coord_policy.py`).
- `_reset_blocker_counter` (línea 425, nueva): dado un blocker, si tiene una clave `counter` bien formada
  (`{"scope": "attempts", "key": <nombre>}` o `{"scope": "finding", "key": "repair_attempts", "finding_id":
  <id>}`), resetea EXACTAMENTE ese contador a `0`. Cualquier otra forma (ausente, malformada, paquete
  inexistente) es un no-op silencioso — fail-closed.
- `cmd_reopen` (línea 468): para cada blocker que esta llamada resuelve por primera vez (`"resolved_at" not
  in blocker`, comprobado ANTES del `setdefault` que lo marca resuelto), invoca `_reset_blocker_counter`.
  Docstring referencia ADR-0039.

Ocho llamadores de `block_with_reason` pasan ahora su `counter` (mapeo completo en ADR-0039 §3):

| Sitio | `counter` |
|---|---|
| `feature-state.py:396` (`cmd_record_spawn`) | `{"scope":"attempts","key":"spawns"}` |
| `feature-state.py:474` (`cmd_start_review_panel`) | `{"scope":"attempts","key":"deep_review_cycles"}` |
| `cli_review.py:33` (`cmd_record_review`) | `{"scope":"attempts","key":"deep_review_cycles"}` |
| `cli_repair.py:319` (`cmd_record_delta_review`) | `{"scope":"attempts","key":"deep_review_cycles"}` |
| `cli_repair.py:49` (`cmd_record_gate`) | `{"scope":"attempts","key":"gate_failures"}` |
| `feature-state.py:671` (`_apply_verification_waiver`) | `{"scope":"attempts","key":"verification_waivers"}` |
| `feature-state.py:703` (`_apply_verdicts`) | `{"scope":"attempts","key":"verifications"}` |
| `cli_repair.py:234` (`cmd_record_repair`) | `{"scope":"finding","key":"repair_attempts","finding_id":<id>}` |

Los otros siete llamadores (`cli_lifecycle.py:462` `cmd_block`; `cli_review.py:58` "package review blocked";
`cli_review.py:164` "review panel blocked"; `cli_repair.py:41` "repair exceeded its frozen line ceiling";
`cli_repair.py:328` "delta review blocked"; `cli_repair.py:369` "package testing blocked"; `cli_repair.py:401`
"runtime QA blocked") no pasan `counter` — no son agotamientos de presupuesto, son verdictos en texto libre;
`reopen` no resetea nada para ellos, igual que antes del fix.

Copias byte-idénticas propagadas a `PROYECTO/ai/scripts/{feature-state.py,feature_state_lib/*.py}` (a mano,
sin generador propio) y a `Global/{opencode,claude-code,codex}/hooks/feature_state_lib/` (vía `./build.sh`,
que las copia desde `ai/scripts/feature_state_lib/` — ver §5).

## 3. Test de regresión: el ciclo completo

`tests/test_harness.py::HarnessTests::test_reopen_resets_only_the_counter_that_produced_the_blocker`
(línea 6993). Agota `max_verifications_per_package` en PKG-01 (con `spawns=4`, `deep_review_cycles=1`,
`gate_failures=2`, `repair_batches=3` puestos a mano, distintos entre sí, para poder verificar que quedan
intactos) → confirma que `record-verification` bloquea y que el blocker lleva
`{"scope": "attempts", "key": "verifications"}` → `reopen` → confirma `attempts["verifications"] == 0` →
confirma que `spawns`/`deep_review_cycles`/`gate_failures`/`repair_batches` **no cambiaron** → confirma que
`record-verification` puede volver a registrar un veredicto (F-002 queda `verified_verdict: upheld`) →
confirma que los cuatro contadores ajenos siguen intactos incluso después de ese veredicto exitoso.

### Prueba de mordida (bite test): neutralizado → rojo → revertido → verde

**Mordida 1 — sin el reset en absoluto** (comentado el `_reset_blocker_counter(data, blocker)` de
`cmd_reopen`, dejando el resto del fix intacto):

```
$ python3 -m unittest tests.test_harness.HarnessTests.test_reopen_resets_only_the_counter_that_produced_the_blocker -v
test_reopen_resets_only_the_counter_that_produced_the_blocker ... FAIL

======================================================================
FAIL: test_reopen_resets_only_the_counter_that_produced_the_blocker
----------------------------------------------------------------------
Traceback (most recent call last):
  File "tests/test_harness.py", line 7034, in test_reopen_resets_only_the_counter_that_produced_the_blocker
    self.assertEqual(reopened["packages"][0]["attempts"]["verifications"], 0)
AssertionError: 6 != 0

Ran 1 test in 1.121s
FAILED (failures=1)
```

Revertido (`diff -q` contra la versión arreglada confirmó bytes idénticos tras el revert), vuelve a verde:

```
$ python3 -m unittest tests.test_harness.HarnessTests.test_reopen_resets_only_the_counter_that_produced_the_blocker -v
test_reopen_resets_only_the_counter_that_produced_the_blocker ... ok
Ran 1 test in 1.200s
OK
```

**Mordida 2 — el assert que prohíbe un reset general** (mutado `_reset_blocker_counter` para que, en el
scope `attempts`, ponga a CERO TODAS las claves de `attempts` en vez de solo `key`, simulando el refactor
que ADR-0039 §1 prohíbe explícitamente):

```
$ python3 -m unittest tests.test_harness.HarnessTests.test_reopen_resets_only_the_counter_that_produced_the_blocker -v
test_reopen_resets_only_the_counter_that_produced_the_blocker ... FAIL

======================================================================
FAIL: test_reopen_resets_only_the_counter_that_produced_the_blocker
----------------------------------------------------------------------
Traceback (most recent call last):
  File "tests/test_harness.py", line 7038, in test_reopen_resets_only_the_counter_that_produced_the_blocker
    self.assertEqual(other["spawns"], 4)
AssertionError: 0 != 4

Ran 1 test in 1.116s
FAILED (failures=1)
```

Revertido de nuevo (`diff -q` limpio contra la versión arreglada), vuelve a verde. Ambas mordidas se
corrieron contra `PROYECTO/ai/scripts/feature_state_lib/cli_lifecycle.py` — el árbol que
`tests/test_harness.py` realmente ejecuta vía subprocess (`FEATURE_STATE = ROOT /
"PROYECTO/ai/scripts/feature-state.py"`), no contra `ai/scripts/` en aislamiento.

**Reproducción del defecto original, sin ninguna mutación sintética**: antes de portar el fix a
`PROYECTO/ai/scripts/feature_state_lib/cli_lifecycle.py` (§5), correr este mismo test contra la copia
histórica pre-fix (todavía sin el parámetro `counter`) fallaba así — la prueba más directa de que el defecto
era real, no hipotético:

```
$ python3 -m unittest tests.test_harness.HarnessTests.test_reopen_resets_only_the_counter_that_produced_the_blocker -v
ERROR: test_reopen_resets_only_the_counter_that_produced_the_blocker
----------------------------------------------------------------------
Traceback (most recent call last):
  File "tests/test_harness.py", line 7020, in test_reopen_resets_only_the_counter_that_produced_the_blocker
    self.assertEqual(blocker["counter"], {"scope": "attempts", "key": "verifications"})
KeyError: 'counter'
Ran 1 test in 1.022s
FAILED (errors=1)
```

## 4. Suite dirigida y suite completa

Tests dirigidos (reopen + verificación + budgets), todos verdes:

```
$ python3 -m unittest -v \
  tests.test_harness.HarnessTests.test_reopen_moves_blocked_back_to_planning_and_allows_new_package \
  tests.test_harness.HarnessTests.test_reopen_requires_reason_and_authorization \
  tests.test_harness.HarnessTests.test_reopen_rejected_outside_blocked_phase \
  tests.test_harness.HarnessTests.test_reopen_resets_only_the_counter_that_produced_the_blocker \
  tests.test_harness.HarnessTests.test_upheld_is_sticky_and_verification_has_a_physical_budget \
  tests.test_harness.HarnessTests.test_verification_is_required_in_code_not_only_in_prose \
  tests.test_harness.HarnessTests.test_refuting_a_leftover_finding_never_clears_a_red_gate \
  tests.test_harness.HarnessTests.test_verification_rejects_bad_shapes_and_replays_idempotently \
  tests.test_harness.HarnessTests.test_apply_verification_waiver_pinned_with_budget_available \
  tests.test_harness.HarnessTests.test_apply_verification_waiver_pinned_with_budget_exhausted \
  tests.test_harness.HarnessTests.test_apply_verdicts_pinned_refuted_empties_open_findings \
  tests.test_harness.HarnessTests.test_apply_verdicts_pinned_upheld_does_not_empty_open_findings \
  tests.test_harness.HarnessTests.test_apply_verdicts_pinned_rejection_paths_raise_exact_state_errors \
  tests.test_harness.HarnessTests.test_verification_budget_survives_two_review_cycles \
  tests.test_harness.HarnessTests.test_done_ready_reaches_done_after_a_real_block_and_reopen_cycle \
  tests.test_harness.HarnessTests.test_transition_still_rejects_leaving_blocked
Ran 16 tests in 16.907s
OK
```

Suite completa (`python3 -m unittest discover -s tests`), ver §6 para el conteo final.

## 5. Gates

```
$ ./build.sh
CHECK_PASS: generated and validated profile go-zen
Generated tracked artifacts for go-zen.

$ ./build.sh --check
CHECK_PASS: generated and validated profile go-zen
SELF_SCAFFOLD_SYNC_OK files=2

$ diff -q ai/scripts/feature_state_lib/cli_lifecycle.py PROYECTO/ai/scripts/feature_state_lib/cli_lifecycle.py
$ diff -q ai/scripts/feature_state_lib/cli_lifecycle.py Global/claude-code/hooks/feature_state_lib/cli_lifecycle.py
$ diff -q ai/scripts/feature_state_lib/cli_lifecycle.py Global/codex/hooks/feature_state_lib/cli_lifecycle.py
$ diff -q ai/scripts/feature_state_lib/cli_lifecycle.py Global/opencode/hooks/feature_state_lib/cli_lifecycle.py
(sin salida en las cuatro — bytes idénticos; lo mismo confirmado para cli_review.py, cli_repair.py y
feature-state.py)

$ git diff --check
(sin salida, exit 0)

$ ./ai/scripts/verify.sh
... (suite completa -v, py_compile, git diff --check, diff Global/* vs STAGING generado, portability,
canonical paths, feature-state check) ...
GLOBAL_PORTABILITY_OK
CANONICAL_PATHS_OK
FEATURE_STATE_OK
VERIFY_PASS
```

`verify.sh` corre con `set -euo pipefail`: cualquier fallo en la suite completa (incluida la nueva
regresión) habría detenido el script antes de llegar a `VERIFY_PASS`. Terminó en `VERIFY_PASS`, exit 0.

## 6. Conteo de la suite completa

```
$ python3 -m unittest discover -s tests
----------------------------------------------------------------------
Ran 904 tests in 549.395s

OK (skipped=3)
```
(exit code 0; corrida por separado, redirigiendo stdout/stderr a archivos propios para evitar el
entrelazado con la salida impresa por algunos tests que invocan CLIs directamente — la misma corrida ya
había pasado, sin capturar el resumen, dentro de `verify.sh` en §5, con `set -euo pipefail` de por medio.)

Baseline declarado en el encargo: 883 OK / 3 skips. El conteo real es 904 OK / 3 skips — sube en 21 tests
respecto al baseline (WIP preexistente de otras sesiones sobre este mismo repo, no de este cambio; este
cambio agrega exactamente 1: `test_reopen_resets_only_the_counter_that_produced_the_blocker`) y nunca
baja. Ningún skip nuevo: los mismos 3 de siempre.

## 7. Alcance respetado

- `ai/state/features/019-harness-evolution.json`: sha256 idéntico antes y después de esta sesión
  (`fae80b61fec37e43bbf728d10b9fae2d0086c54869ec11d07021e71d29c4c4c2`), mtime anterior al inicio de la
  sesión — no tocado.
- Ningún archivo de los paquetes P1..P5 de 019 tocado.
- Ningún test existente relajado, saltado ni borrado — solo uno nuevo agregado.
- Sin refactors oportunistas en `feature_state_lib/`: el diff de cada archivo es exactamente la línea del
  parámetro `counter` en cada llamador mapeado, más `block_with_reason`/`_reset_blocker_counter`/`cmd_reopen`
  en `cli_lifecycle.py`.
- `docs/adr/0039-reopen-directed-counter-reset.md` escrito antes del test, el test antes del código (orden
  pedido); indexado en `docs/adr/README.md`.
