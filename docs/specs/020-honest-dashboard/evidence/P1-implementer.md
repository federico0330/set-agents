# P1-digest-no-esconde — evidencia del implementer

Estado: IMPLEMENTADO — listo para gates/review.

## Tabla AC → cambio → prueba

| AC | Cambio | `archivo:línea` | Prueba |
|---|---|---|---|
| AC-01 | Sección `## Necesita tu decisión`, primera del digest, días desde el último blocker sin `resolved_at` | `ai/scripts/feature_state_lib/cli_reporting.py` `cmd_digest` (bloque tras `lines = [...]`) | `tests/test_digest.py::HonestPredicateTests::test_digest_names_a_blocked_feature_even_though_it_carries_final_state` |
| AC-02 | Predicado único `feature_is_live`/`open_blocker` en `model.py`, consumido por los tres artefactos | `ai/scripts/feature_state_lib/model.py:76-137` (aprox., bloque "honest-dashboard") | las 5 pruebas nuevas de esta tabla ejercitan el predicado indirectamente; `feature_is_live`/`open_blocker` no tienen unit test propio aislado (cubiertas end-to-end vía digest/hub/status) |
| AC-03 | `## Qué se está haciendo` excluye bloqueadas (tope 2 menciones) y marca `⚠️ estancada hace N días` en las vivas no bloqueadas | `cli_reporting.py` `cmd_digest`, sección `## Qué se está haciendo` | `tests/test_digest.py::HonestPredicateTests::test_digest_caps_a_blocked_feature_at_two_mentions_and_marks_the_stale_one` |
| AC-04 | `cmd_status` suma `blocked_days`/`stale_days` al JSON | `ai/scripts/feature_state_lib/cli_lifecycle.py::cmd_status` | `tests/test_harness.py::HarnessTests::test_status_reports_blocked_days_from_the_last_unresolved_blocker` y `::test_status_reports_stale_days_for_a_live_unblocked_feature` |
| AC-05 | Digest nombra una feature `BLOCKED` (roja contra el código de hoy) | `cli_reporting.py::cmd_digest` | `tests/test_digest.py::HonestPredicateTests::test_digest_names_a_blocked_feature_even_though_it_carries_final_state` |
| AC-12 | `_hub_body` deja de saltear `final_state` truthy; usa `feature_is_live` | `ai/scripts/feature-state.py::_hub_body` (filtro de `## Qué falta`) | `tests/test_digest.py::HonestPredicateTests::test_hub_lists_the_blocked_feature_in_que_falta` |

Todos los cambios espejados a mano en `PROYECTO/ai/scripts/` (mismo mecanismo sin
generador propio que ADR-0039 documenta) y propagados a `Global/opencode`, `Global/codex`,
`Global/claude-code` vía `./build.sh` (los tres `hooks/feature_state_lib/` verificados
`diff -q` idénticos a `ai/scripts/feature_state_lib/` después de la regeneración).

**Nota de alcance sobre el `git status` de esta sesión:** el árbol de trabajo ya traía una
cantidad grande de cambios sin commitear de trabajo previo no relacionado (ADR-0036/P3,
ADR-0038/P5, ADR-0039, visibles en `ai/scripts/feature_state_lib/cli_repair.py`,
`cli_review.py`, y cientos de líneas de tests nuevos en `tests/test_harness.py` de
019-P5-tools-discovery) — nada de eso lo tocó este paquete. Confirmado con
`git diff ai/scripts/feature-state.py` (mi único hunk es el de `_hub_body`) y
`git diff tests/test_harness.py | grep test_status_reports` (mis dos tests están ahí,
en medio de un diff mucho más grande que ya existía antes de empezar). Correr `./build.sh`
(regenerar `Global/*`, obligatorio tras tocar `feature_state_lib/`) trajo consigo esa
deriva preexistente a los árboles `Global/*/hooks/feature_state_lib/` porque el generador
vuelca el estado completo de `ai/scripts/feature_state_lib/`, no un diff acotado a mi
paquete — esperable y no es scope creep mío.

## Baseline (antes de tocar nada)

Comando corrido literal:

```
$ python3 ai/scripts/feature-state.py digest
DIGEST_WRITTEN file=/home/federico/SET-AGENTES/docs/notas/BUENOS-DIAS.md since=2026-08-11T00:00:55
{
  "decisions": 11,
  "file": "/home/federico/SET-AGENTES/docs/notas/BUENOS-DIAS.md",
  "finished": 5,
  "ok": true,
  "quickfixes": 0,
  "since": "2026-08-11T00:00:55"
}

$ grep -n "002-adaptive\|011-quota" docs/notas/BUENOS-DIAS.md
(sin salida, exit code 1 -- confirma el bug: 002 y 011 no aparecen en el digest)

$ grep -n "002-adaptive\|011-quota" "docs/notas/00 - Proyecto.md"
6:- [[features/002-adaptive-pi-orchestration|002-adaptive-pi-orchestration]] — fase `BLOCKED` · paquetes 0/1 · **BLOCKED**
15:- [[features/011-quota-failover|011-quota-failover]] — fase `BLOCKED` · paquetes 0/1 · **BLOCKED**
79:  **011-quota-failover** llegue a `accepted`. 011 a su vez está `BLOCKED` esperando un agotamiento real
81:- **002-adaptive-pi-orchestration** — sigue `BLOCKED`, retirada formalmente como superseded por 003
```

Confirmado: el hub SI las nombra en `## Features` (con etiqueta BLOCKED) pero NO en `## Qué falta`
(headers de la nota: `## Features`(4), `## Qué falta`(24), `## Quick-fixes recientes`(31), `## Decisiones`(38),
`## Referencias`(49), `## Notas propias`(57) -- confirmado por `grep -n "^## "`).

### Digest ANTES (BUENOS-DIAS.md completo, secciones relevantes)

```
## Qué se está haciendo

- **006-execution-graph** — fase `PACKAGE_ACCEPTED`
- **010-spawn-provenance** — fase `PACKAGE_ACCEPTED`
- **020-honest-dashboard** — fase `PACKAGE_IMPLEMENTATION`

## Qué falta

- **006-execution-graph** → `PACKAGE_ACCEPTED` — P3-graph-view: module impact required (record-module-impact) or waived (--module-impact-waived --reason)
- **010-spawn-provenance** → `PACKAGE_ACCEPTED` — P1-spawn-provenance: module impact required (record-module-impact) or waived (--module-impact-waived --reason)
- **020-honest-dashboard** → `PACKAGE_IMPLEMENTATION` — continue local implementation
- **020-honest-dashboard** tareas pendientes en P2-anclas-verificables: ...
```


## Notas de exploración (para no perderlas si hay stall)

- `feature_is_live` va en `model.py` (no imports internos de `feature_state_lib`, evita el
  ciclo que documenta `cli_integration.py:1-13`): lo consumen `cli_reporting.py` (cmd_digest),
  `feature-state.py` (_hub_body) y `cli_lifecycle.py` (cmd_status) -- los tres ya importan
  `from feature_state_lib import model`.
- `data["blockers"]` (top-level, NO `package["blockers"]`) es donde `block_with_reason` y
  `fail-task` escriben: `{"package_id", "reason", "at", opcional "resolved_at"}`. Confirmado
  contra 002 (dos entradas, una resuelta) y 011 (una entrada, sin resolver) en
  `ai/state/features/*.json`.
- `next_transition` ya devuelve `{"next": None, "reason": "terminal"}` para fase BLOCKED (está
  en `TERMINAL`), así que `_pending_bits` sobre una feature bloqueada solo aporta el bit
  `⛔ bloqueo: ...` (mas hallazgos/tareas abiertas del paquete si los hubiera) -- nunca un bit
  `→` de próximo paso. Esto es lo que hace segura la ampliación de AC-02 sin URL de ruido extra.
- Tope de 2 menciones (AC-03): "Qué se está haciendo" en el digest usa un subconjunto SIN
  bloqueadas (`open_blocker(d) is None`); "Qué falta" del digest y del hub usan el conjunto
  vivo COMPLETO (`feature_is_live`), así una bloqueada aparece en "Necesita tu decisión"
  (titular) + "Qué falta" (bit ⛔) = 2, nunca en "Qué se está haciendo".
- Fixture pre-existente `tests/test_digest.py::_scaffold` usa `"final_state": "done"`
  (minúscula) para 001-vieja -- valor que el código real NUNCA produce (`to_phase` siempre
  viene de `PHASES`, todo mayúsculas; `TERMINAL = {"DONE", "BLOCKED"}`). AC-02 exige
  `final_state == "DONE"` (comparación exacta, no truthy). Con el predicado nuevo, "done"
  minúscula pasaría a ser "viva" y ROMPERÍA
  `test_digest_renders_window_sections_and_marks_closed_features_honestly` y
  `test_sync_notes_hub_skips_final_state_features_in_pending` (ambas assertNotIn
  "001-vieja"). Corrijo el fixture a `"DONE"` mayúscula -- mismas aserciones, mismo
  invariante probado (feature genuinamente cerrada excluida), valor de entrada corregido
  para calzar con el vocabulario cerrado real del schema. No es debilitar el test.

## ADR-0040

`docs/adr/0040-honest-digest-shared-liveness-predicate.md`, indexado en `docs/adr/README.md`.

## Tests en rojo contra el código de hoy (AC-01, AC-03, AC-05, AC-12)

Agregados en `tests/test_digest.py` (clase `HonestPredicateTests`), más la corrección de
`_scaffold`'s `"final_state": "done"` (minúscula, valor que ningún código real produce) a
`"DONE"` para que `test_digest_renders_window_sections_and_marks_closed_features_honestly` y
`test_sync_notes_hub_skips_final_state_features_in_pending` sigan probando el mismo
invariante bajo el nuevo predicado exacto (`final_state == "DONE"`, AC-02).

Corrida literal contra el código de HOY (antes de tocar `cli_reporting.py`/`feature-state.py`):

```
$ python3 -m unittest tests.test_digest -v
test_digest_is_idempotent_across_reruns ... ok
test_digest_preserves_a_preexisting_handwritten_file ... ok
test_digest_renders_window_sections_and_marks_closed_features_honestly ... ok
test_milestone_narration_is_doctrine_in_all_shared_files ... ok
test_resume_feature_reads_the_living_notes ... ok
test_session_open_reads_hub_without_vault ... ok
test_sync_notes_hub_skips_final_state_features_in_pending ... ok
test_digest_caps_a_blocked_feature_at_two_mentions_and_marks_the_stale_one ... FAIL
test_digest_names_a_blocked_feature_even_though_it_carries_final_state ... FAIL
test_hub_lists_the_blocked_feature_in_que_falta ... FAIL

FAIL: test_digest_caps_a_blocked_feature_at_two_mentions_and_marks_the_stale_one
AssertionError: 'estancada' not found in '\n\n- **005-stale** — fase `PACKAGE_ACCEPTED`\n\n'

FAIL: test_digest_names_a_blocked_feature_even_though_it_carries_final_state
AssertionError: '## Necesita tu decisión' not found in '# Buenos días — digest del proyecto...'

FAIL: test_hub_lists_the_blocked_feature_in_que_falta
AssertionError: '003-blocked' not found in '\n\n- **005-stale** → `INTEGRATION` — all packages accepted\n\n'

Ran 10 tests in 0.696s
FAILED (failures=3)
```

Confirma AC-05/AC-12 en rojo exactamente como pide el contrato: 6 pre-existentes en verde
(incluidas las dos que dependían del fixture corregido), 3 nuevas en rojo por el defecto real.

Próximo paso (checkpoint, por si hay stall): implementar `feature_is_live`/`open_blocker`/
`days_since`/`blocked_days`/`stale_days`/`feature_is_stale`/`STALE_THRESHOLD_DAYS` en
`ai/scripts/feature_state_lib/model.py`; consumirlos en `cli_reporting.cmd_digest` (sección
nueva + secciones existentes), `feature-state._hub_body`, `cli_lifecycle.cmd_status`; copiar
a `PROYECTO/ai/scripts/` a mano; `./build.sh` + `./build.sh --check`; test AC-04 sobre
`cmd_status` (blocked_days/stale_days) en `tests/test_harness.py` o `tests/test_digest.py`.

## Implementación

- `ai/scripts/feature_state_lib/model.py` — `STALE_THRESHOLD_DAYS`, `feature_is_live`,
  `open_blocker`, `days_since`, `blocked_days`, `stale_days`, `feature_is_stale` (AC-02).
- `ai/scripts/feature_state_lib/cli_reporting.py::cmd_digest` — sección `## Necesita tu
  decisión` primero (AC-01); `## Qué se está haciendo` usa `working` (vivas sin blocker,
  con marca `⚠️ estancada hace N días` vía `feature_is_stale`, AC-03); `## Qué falta` usa
  `live` completo (AC-02).
- `ai/scripts/feature-state.py::_hub_body` — filtro `if not model.feature_is_live(data):
  continue` reemplaza `if data.get("final_state"): continue` (AC-02/AC-12).
- `ai/scripts/feature_state_lib/cli_lifecycle.py::cmd_status` — agrega `blocked_days`/
  `stale_days` al JSON (AC-04), sin tocar `output_state` (usado por ~20 comandos más).
- Espejado a mano en `PROYECTO/ai/scripts/` (mismo mecanismo que ADR-0039 documenta: sin
  generador propio, paridad byte a byte verificada con `diff -rq`).

## Prueba de mordida — tests nuevos de `cmd_status` (AC-04)

Escritos DESPUÉS de implementar `cmd_status` (a diferencia de AC-01/03/05/12, que ya
quedaron rojo→verde por el orden natural TDD arriba). Neutralicé el cambio (revertí
`cmd_status` a `return output_state(data, False, path)`), confirmé rojo, reverti la
neutralización (restauré el fix), confirmé verde:

```
$ python3 -m unittest tests.test_harness.HarnessTests.test_status_reports_blocked_days_from_the_last_unresolved_blocker tests.test_harness.HarnessTests.test_status_reports_stale_days_for_a_live_unblocked_feature -v
# -- CON cmd_status neutralizado (return output_state(data, False, path)) --
test_status_reports_blocked_days_from_the_last_unresolved_blocker ... ERROR
test_status_reports_stale_days_for_a_live_unblocked_feature ... ERROR
ERROR: test_status_reports_blocked_days_from_the_last_unresolved_blocker
KeyError: 'blocked_days'
ERROR: test_status_reports_stale_days_for_a_live_unblocked_feature
KeyError: 'stale_days'
Ran 2 tests in 0.432s
FAILED (errors=2)

# -- con el fix restaurado --
test_status_reports_blocked_days_from_the_last_unresolved_blocker ... ok
test_status_reports_stale_days_for_a_live_unblocked_feature ... ok
Ran 2 tests in 0.430s
OK
```

`ai/scripts/feature_state_lib/cli_lifecycle.py` y su copia en `PROYECTO/` verificadas
idénticas (`diff -q`) después de restaurar.

## Prueba viva contra el repo real (antes/después)

Comando pedido en el context pack, corrido literal DESPUÉS de la implementación:

```
$ python3 ai/scripts/feature-state.py digest
DIGEST_WRITTEN file=/home/federico/SET-AGENTES/docs/notas/BUENOS-DIAS.md since=2026-08-11T00:30:34
{...}

$ python3 ai/scripts/feature-state.py sync-notes
{... "written": ["00 - Proyecto.md"] ...}

$ grep -n "002-adaptive\|011-quota\|Necesita tu decisión" docs/notas/BUENOS-DIAS.md
8:- **002-adaptive-pi-orchestration** — HUMAN_DECISION_REQUIRED: user-authorized third repair cycle failed final review; five high findings remain and P1 exhau… (hace 18 días)
9:- **011-quota-failover** — HUMAN_DECISION_REQUIRED: AC-06 exige una suscripción Anthropic controlada y genuinamente agotada junto a un proveedor a… (hace 12 días)
26:- **002-adaptive-pi-orchestration** ⛔ bloqueo: HUMAN_DECISION_REQUIRED: user-authorized third repair cycle failed final review; five high findings remain and P1 exhau…
27:- **002-adaptive-pi-orchestration** 5 hallazgos abiertos
30:- **011-quota-failover** ⛔ bloqueo: HUMAN_DECISION_REQUIRED: AC-06 exige una suscripción Anthropic controlada y genuinamente agotada junto a un proveedor a…
31:- **011-quota-failover** tareas pendientes en P1-quota-failover: ...

$ grep -n "002-adaptive\|011-quota" "docs/notas/00 - Proyecto.md"
6:- [[features/002-adaptive-pi-orchestration|002-adaptive-pi-orchestration]] — fase `BLOCKED` · paquetes 0/1 · **BLOCKED**
15:- [[features/011-quota-failover|011-quota-failover]] — fase `BLOCKED` · paquetes 0/1 · **BLOCKED**
26:- **002-adaptive-pi-orchestration** ⛔ bloqueo: HUMAN_DECISION_REQUIRED: user-authorized third repair cycle failed final review; five high findings remain and P1 exhau…
...
30:- **011-quota-failover** ⛔ bloqueo: HUMAN_DECISION_REQUIRED: AC-06 exige una suscripción Anthropic controlada y genuinamente agotada junto a un proveedor a…
```

Sección `## Necesita tu decisión` completa (primera del documento, antes de "Qué quedó
listo"):

```
## Necesita tu decisión

- **002-adaptive-pi-orchestration** — HUMAN_DECISION_REQUIRED: user-authorized third repair cycle failed final review; five high findings remain and P1 exhau… (hace 18 días)
- **011-quota-failover** — HUMAN_DECISION_REQUIRED: AC-06 exige una suscripción Anthropic controlada y genuinamente agotada junto a un proveedor a… (hace 12 días)
```

Sección `## Qué se está haciendo` (002/011 ausentes -- tope de dos menciones, AC-03; 006/010
marcadas estancadas):

```
## Qué se está haciendo

- **006-execution-graph** — fase `PACKAGE_ACCEPTED` — ⚠️ estancada hace 9 días
- **010-spawn-provenance** — fase `PACKAGE_ACCEPTED` — ⚠️ estancada hace 9 días
- **020-honest-dashboard** — fase `PACKAGE_IMPLEMENTATION`
```

`cmd_status` coherente con el digest (mismo predicado/constante, AC-04):

```
$ python3 ai/scripts/feature-state.py status --state-file ai/state/features/002-adaptive-pi-orchestration.json | python3 -c "import json,sys; d=json.load(sys.stdin); print('blocked_days', d['blocked_days']); print('stale_days', d['stale_days'])"
blocked_days 18
stale_days None

$ python3 ai/scripts/feature-state.py status --state-file ai/state/features/011-quota-failover.json | python3 -c "import json,sys; d=json.load(sys.stdin); print('blocked_days', d['blocked_days']); print('stale_days', d['stale_days'])"
blocked_days 12
stale_days None
```

18/12 días coincide exactamente con "hace 18 días"/"hace 12 días" del digest -- mismo
predicado, mismo cómputo, tres artefactos de acuerdo (criterio de cierre de la spec).

Nota: `docs/notas/BUENOS-DIAS.md` y `docs/notas/00 - Proyecto.md` quedaron regenerados de
verdad en disco por esta corrida (permitido por el contrato: "correr digest y sync-notes
para verificar" no es una transición de fase). Diffs completos guardados en el scratchpad
de esta sesión (23 y 6 líneas respectivamente) si hace falta inspeccionarlos.

## Gates corridos

```
$ python3 -m unittest discover -s tests
Ran 922 tests in 424.601s

OK (skipped=3)
```

Base declarada en el contrato: 917 OK / 3 skips. Ahora 922 (917 + 5 tests nuevos: 3 en
`HonestPredicateTests` + 2 en `HarnessTests`) / 3 skips, cero failures/errors — sube, nunca
baja.

```
$ ./ai/scripts/verify.sh
...
CHECK_PASS: generated and validated profile go-zen
SELF_SCAFFOLD_SYNC_OK files=2
...
GLOBAL_PORTABILITY_OK
CANONICAL_PATHS_OK
FEATURE_STATE_OK
VERIFY_PASS
```

```
$ ./build.sh
CHECK_PASS: generated and validated profile go-zen
Generated tracked artifacts for go-zen.

$ ./build.sh --check
CHECK_PASS: generated and validated profile go-zen
SELF_SCAFFOLD_SYNC_OK files=2
```

```
$ git diff --check
(sin salida, exit 0)
```

`Global/opencode/hooks/feature_state_lib/`, `Global/codex/hooks/feature_state_lib/`,
`Global/claude-code/hooks/feature_state_lib/` verificados `diff -q` idénticos a
`ai/scripts/feature_state_lib/` (`model.py`, `cli_reporting.py`, `cli_lifecycle.py`) tras
la regeneración — sin salida en los tres, cero drift.

## Assumptions / known risks

- El umbral de estancamiento (`STALE_THRESHOLD_DAYS = 7`) es el mismo supuesto de producto
  documentado en la spec (SC-10) y en ADR-0040 — no medido, reversible en una línea.
- `feature_is_stale`/`stale_days` no distinguen una feature pausada a propósito (`006`,
  `010`, esperando `record-module-impact`) de una estancada por accidente — limitación
  conocida y documentada (SC-11), no resuelta a propósito: ambas quedan marcadas
  `⚠️ estancada` en el digest real (confirmado en la corrida en vivo de arriba).
- AC-02's `feature_is_live`/`open_blocker` no tienen un test unitario aislado propio
  (llaman directo a `model.py`); quedan cubiertos end-to-end por las pruebas de
  digest/hub/status, que es donde el comportamiento observable importa. Si el reviewer
  prefiere un test unitario directo contra `model.py`, es una adición chica y de bajo
  riesgo para un repair.

## Cobertura unitaria directa agregada (no pedida por ningún AC puntual, cierra el gap señalado arriba)

`tests/test_honest_predicate.py` (nuevo, 21 tests): `feature_is_live`, `open_blocker`,
`days_since`, `blocked_days`, `stale_days`, `feature_is_stale` en aislamiento —
vocabulario cerrado exacto (no truthy), último blocker sin resolver (no el primero),
timestamps naive tratados como UTC, límite exacto del umbral de 7 días, exención de
bloqueadas en `stale_days`/`feature_is_stale`.

Mordida verificada con 3 mutaciones representativas aplicadas UNA POR VEZ contra
`ai/scripts/feature_state_lib/model.py` (no las 21 aserciones una por una: son variantes
del mismo puñado de invariantes; las tres mutaciones cubren los tres invariantes de
diseño reales del ADR-0040 -- comparación exacta, último-no-primero, exención de
bloqueadas):

```
# Mutación 1: feature_is_live -> `not data.get("final_state")` (el bug viejo, truthy)
$ python3 -m unittest tests.test_honest_predicate.FeatureIsLiveTests -v
test_blocked_is_live ... FAIL (AssertionError: False is not true)
test_comparison_is_exact_not_truthy ... FAIL (AssertionError: False is not true)
test_done_is_not_live ... ok
test_no_final_state_is_live ... ok
FAILED (failures=2)

# Mutación 2: open_blocker -> `open_ones[0]` (primero, no último)
$ python3 -m unittest tests.test_honest_predicate.OpenBlockerTests -v
test_returns_the_last_unresolved_not_the_first_when_two_are_open ... FAIL
  AssertionError: 'primer bloqueo' != 'segundo bloqueo'
(las otras 4 de la clase, ok)
FAILED (failures=1)

# Mutación 3: stale_days pierde `or open_blocker(data) is not None`
$ python3 -m unittest tests.test_honest_predicate.BlockedDaysAndStaleDaysTests -v
test_stale_days_none_when_blocked ... FAIL (AssertionError: 30 is not None)
test_feature_is_stale_false_for_a_blocked_feature_no_matter_how_old ... FAIL (AssertionError: True is not false)
(las otras 3 de la clase, ok)
FAILED (failures=2)
```

Cada mutación revertida contra la copia de respaldo (`model.py.fixed` en el scratchpad) y
confirmada verde antes de seguir. `ai/scripts/feature_state_lib/model.py` verificado
`diff`-idéntico a la copia de respaldo tras el último revert (sin diff neto, ya estaba
sincronizado con `PROYECTO/`).

## Gates finales (con `tests/test_honest_predicate.py` incluido)

```
$ python3 -m unittest discover -s tests
Ran 943 tests in 411.732s

OK (skipped=3)
```

943 = 917 (base declarada) + 26 tests nuevos (3 `HonestPredicateTests` + 2 `HarnessTests`
de `cmd_status` + 21 `test_honest_predicate.py`). Cero failures, cero errors, 3 skips
(igual que la base).

```
$ ./ai/scripts/verify.sh
...
GLOBAL_PORTABILITY_OK
CANONICAL_PATHS_OK
FEATURE_STATE_OK
VERIFY_PASS

$ ./build.sh --check
CHECK_PASS: generated and validated profile go-zen
SELF_SCAFFOLD_SYNC_OK files=2

$ git diff --check
(sin salida, exit 0)
```

## Cierre

`status: implemented`. Listo para `PACKAGE_GATES`/review independiente. Nada de lo hecho
resuelve los blockers de `002`/`011` (fuera de alcance, hacerlos visibles era el trabajo).
No se tocó `docs/modules/`, el verificador de anclas (P2), ni routing/tools discovery.
