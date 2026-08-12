# P1-digest-no-esconde — evidencia del repair (review independiente → `repair_required`)

Ciclo único (retry budget: 1/1 consumido). Tres findings: F-01 (`high`, propio), F-02
(`medium`, propio), F-03 (`medium`, del orquestador — solo verificación, sin tocar estado).

## F-01 (`high`) — el tope de dos menciones no se cumplía

**Causa confirmada**: `cmd_digest`, sección `## Qué falta`
(`ai/scripts/feature_state_lib/cli_reporting.py:228-235` antes del repair) volcaba **todos**
los bits de `_pending_bits` sin filtrar, incluido el bit `⛔ bloqueo: ...` — que es
duplicación literal (mismo texto, mismo truncado por `_short`) del titular ya emitido en
`## Necesita tu decisión`.

**Reparación aplicada** (decidida por el orquestador, ejecutada sin re-litigar): para una
feature ya headlineada (`model.open_blocker(data) is not None`), se omite en "Qué falta"
**únicamente** el bit que empieza con `"⛔ bloqueo:"`; los demás bits (hallazgos abiertos,
tareas pendientes) se conservan intactos.

`ai/scripts/feature_state_lib/cli_reporting.py:228-241` (después del repair):

```python
    lines += ["", "## Qué falta", ""]
    pending_any = False
    for data in live:
        # AC-03 (F-01 repair, tope de dos menciones): a feature already headlined above in
        # "## Necesita tu decisión" repeats its `⛔ bloqueo:` bit here verbatim -- same text,
        # same truncation, zero new information (3rd mention). Every OTHER bit
        # (`_pending_bits` also renders open findings / pending tasks) is new information
        # and stays: only the literal blocker-duplicate line is dropped, never the feature.
        headlined = model.open_blocker(data) is not None
        for bit in _pending_bits(data):
            if headlined and bit.startswith("⛔ bloqueo:"):
                continue
            lines.append(f"- **{data.get('feature_id')}** {bit}")
            pending_any = True
    if not pending_any:
```

Mismo cambio espejado a mano en `PROYECTO/ai/scripts/feature_state_lib/cli_reporting.py`
(mismas líneas, mismo contenido — confirmado `diff` sin salida más abajo), y propagado a
`Global/*/hooks/feature_state_lib/cli_reporting.py` vía `./build.sh`.

### Verificación — antes/después literal, revirtiendo y restaurando el fix

Para capturar un antes/después limpio (no reciclado de la evidencia del implementer),
reverti temporalmente el filtro en `ai/scripts/feature_state_lib/cli_reporting.py`, corrí
`digest`, capturé, restauré el fix, corrí `digest` de nuevo:

```
$ python3 ai/scripts/feature-state.py digest   # -- con el filtro revertido (bug F-01) --
DIGEST_WRITTEN file=/home/federico/SET-AGENTES/docs/notas/BUENOS-DIAS.md since=2026-08-11T02:07:06
{...}

$ grep -c "002-adaptive-pi-orchestration" docs/notas/BUENOS-DIAS.md
3
$ grep -c "011-quota-failover" docs/notas/BUENOS-DIAS.md
3
$ grep -n "002-adaptive-pi-orchestration\|011-quota-failover" docs/notas/BUENOS-DIAS.md
8:- **002-adaptive-pi-orchestration** — HUMAN_DECISION_REQUIRED: user-authorized third repair cycle failed final review; five high findings remain and P1 exhau… (hace 18 días)
9:- **011-quota-failover** — HUMAN_DECISION_REQUIRED: AC-06 exige una suscripción Anthropic controlada y genuinamente agotada junto a un proveedor a… (hace 12 días)
26:- **002-adaptive-pi-orchestration** ⛔ bloqueo: HUMAN_DECISION_REQUIRED: user-authorized third repair cycle failed final review; five high findings remain and P1 exhau…
27:- **002-adaptive-pi-orchestration** 5 hallazgos abiertos
30:- **011-quota-failover** ⛔ bloqueo: HUMAN_DECISION_REQUIRED: AC-06 exige una suscripción Anthropic controlada y genuinamente agotada junto a un proveedor a…
31:- **011-quota-failover** tareas pendientes en P1-quota-failover: additive schema/migration and invariants, narrow classifier + Pi terminal plumbing, BEGIN IMMEDIATE close/exhaust/authorize idempotent transition + selection exclusion, deterministic routing/migration/concurrency tests, credential-gated real exhausted-provider E2E runner/evidence
```

```
$ python3 ai/scripts/feature-state.py digest   # -- con el fix restaurado --
DIGEST_WRITTEN file=/home/federico/SET-AGENTES/docs/notas/BUENOS-DIAS.md since=2026-08-11T02:07:15
{...}

$ grep -c "002-adaptive-pi-orchestration" docs/notas/BUENOS-DIAS.md
2
$ grep -c "011-quota-failover" docs/notas/BUENOS-DIAS.md
2
$ grep -n "002-adaptive-pi-orchestration\|011-quota-failover" docs/notas/BUENOS-DIAS.md
8:- **002-adaptive-pi-orchestration** — HUMAN_DECISION_REQUIRED: user-authorized third repair cycle failed final review; five high findings remain and P1 exhau… (hace 18 días)
9:- **011-quota-failover** — HUMAN_DECISION_REQUIRED: AC-06 exige una suscripción Anthropic controlada y genuinamente agotada junto a un proveedor a… (hace 12 días)
26:- **002-adaptive-pi-orchestration** 5 hallazgos abiertos
29:- **011-quota-failover** tareas pendientes en P1-quota-failover: additive schema/migration and invariants, narrow classifier + Pi terminal plumbing, BEGIN IMMEDIATE close/exhaust/authorize idempotent transition + selection exclusion, deterministic routing/migration/concurrency tests, credential-gated real exhausted-provider E2E runner/evidence
```

Antes = 3/3, después = 2/2, para las dos features exactamente como pide el criterio de
verificación. La línea `⛔ bloqueo:` desapareció de "Qué falta"; "5 hallazgos abiertos" y
"tareas pendientes en P1-quota-failover: ..." — la información nueva — se conservan. Cero
líneas de información perdidas, tal como predijo la reparación decidida por el
orquestador.

Después de restaurar, confirmado `ai/scripts/feature_state_lib/cli_reporting.py` idéntico a
`PROYECTO/ai/scripts/feature_state_lib/cli_reporting.py` (`diff`, sin salida — ver sección
de espejos más abajo).

### ADR-0040 — línea de precisión agregada (no reescrita)

La tabla de la sección 3 (`## Qué falta` → `bit ⛔ bloqueo: ... vía _pending_bits`) describía
el diseño donde ese bit siempre aparece — quedó desactualizada por este repair. Agregué un
párrafo de precisión inmediatamente después (`docs/adr/0040-honest-digest-shared-liveness-predicate.md`,
sección "3. Necesita tu decisión...", después de la tabla) explicando por qué el tope de dos
se sostiene incluso cuando `_pending_bits` devuelve más de un bit (el caso real de `002`/`011`),
y aclarando que `_hub_body` no aplica este filtro porque no tiene sección "Necesita tu
decisión" de la que el bloqueo sea duplicado. No se tocó ninguna otra sección del ADR.

## F-02 (`medium`) — el test decorativo de este paquete

**Causa confirmada**: `tests/test_digest.py::HonestPredicateTests::test_digest_caps_a_blocked_feature_at_two_mentions_and_marks_the_stale_one`
nunca contaba menciones (solo `assertIn`/`assertNotIn` por sección), y su fixture
`003-blocked` tenía `"packages": []` — con eso, `_pending_bits` solo puede devolver el bit
`⛔ bloqueo:` (no hay findings que sumar, no hay `current_package_id`/tareas que listar, y
`next_transition` da `next: None` para fase `BLOCKED`, terminal). El escenario que rompe el
tope de dos (una feature bloqueada con **más de un** bit accionable) era estructuralmente
irrepresentable con ese fixture.

**Reparación**: `tests/test_digest.py:130-167` (`_scaffold_honesty_fixtures`) — `003-blocked`
ahora carga un package con un finding abierto (mismo shape que el estado real de
`002-adaptive-pi-orchestration`, que es por qué el digest real muestra "5 hallazgos
abiertos" para esa feature). `tests/test_digest.py:217-247` (el test) — nueva aserción que
cuenta el total de menciones de `003-blocked` en **todo el documento** y lo capa en 2
(`assertEqual(total_mentions, 2, ...)`), más `assertIn("hallazgos abiertos", falta)` (la
información nueva sobrevive) y `assertNotIn("⛔", falta)` (el bit duplicado no).

### Rojo contra el código con el bug de F-01 (revertido temporalmente, mismo mecanismo que arriba)

```
$ python3 -m unittest tests.test_digest.HonestPredicateTests.test_digest_caps_a_blocked_feature_at_two_mentions_and_marks_the_stale_one -v
test_digest_caps_a_blocked_feature_at_two_mentions_and_marks_the_stale_one (tests.test_digest.HonestPredicateTests.test_digest_caps_a_blocked_feature_at_two_mentions_and_marks_the_stale_one)
AC-03: a blocked feature is exempt from 'Qué se está haciendo' entirely (a 3rd ... FAIL

======================================================================
FAIL: test_digest_caps_a_blocked_feature_at_two_mentions_and_marks_the_stale_one (tests.test_digest.HonestPredicateTests.test_digest_caps_a_blocked_feature_at_two_mentions_and_marks_the_stale_one)
AC-03: a blocked feature is exempt from 'Qué se está haciendo' entirely (a 3rd
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/home/federico/SET-AGENTES/tests/test_digest.py", line 241, in test_digest_caps_a_blocked_feature_at_two_mentions_and_marks_the_stale_one
    self.assertNotIn("⛔", falta)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^
AssertionError: '⛔' unexpectedly found in '\n\n- **003-blocked** ⛔ bloqueo: HUMAN_DECISION_REQUIRED: necesita autorizacion\n- **003-blocked** 1 hallazgos abiertos\n- **005-stale** → `INTEGRATION` — all packages accepted\n\n'

----------------------------------------------------------------------
Ran 1 test in 0.091s

FAILED (failures=1)
```

(Neutralización: quité el bloque `headlined = ...` / `if headlined and bit.startswith(...)`
de `PROYECTO/ai/scripts/feature_state_lib/cli_reporting.py`, que es la copia que ejecuta la
suite de `tests/test_digest.py` vía `FEATURE_STATE = ROOT / "PROYECTO/ai/scripts/feature-state.py"`.)

### Verde con el fix restaurado

```
$ python3 -m unittest tests.test_digest -v
test_digest_is_idempotent_across_reruns ... ok
test_digest_preserves_a_preexisting_handwritten_file ... ok
test_digest_renders_window_sections_and_marks_closed_features_honestly ... ok
test_milestone_narration_is_doctrine_in_all_shared_files ... ok
test_resume_feature_reads_the_living_notes ... ok
test_session_open_reads_hub_without_vault ... ok
test_sync_notes_hub_skips_final_state_features_in_pending ... ok
test_digest_caps_a_blocked_feature_at_two_mentions_and_marks_the_stale_one ... ok
test_digest_names_a_blocked_feature_even_though_it_carries_final_state ... ok
test_hub_lists_the_blocked_feature_in_que_falta ... ok

----------------------------------------------------------------------
Ran 10 tests in 0.700s

OK
```

Confirmado `PROYECTO/ai/scripts/feature_state_lib/cli_reporting.py` idéntico (`diff`, sin
salida) a `ai/scripts/feature_state_lib/cli_reporting.py` tras restaurar la neutralización.

## F-03 (`medium`, orquestador) — `owned_paths` desactualizado

**No mutado** (fuera de mi alcance: mutar estado de feature es del orquestador). Solo
verificación, para dejar constancia del "antes":

```
$ python3 ai/scripts/check-owned-paths.py --state-file ai/state/features/020-honest-dashboard.json --package-id P1-digest-no-esconde --baseline HEAD
[... changed_files: lista larga, incluye entre otros ...
  "ai/scripts/feature_state_lib/model.py",
  "ai/scripts/feature_state_lib/cli_lifecycle.py",
  "tests/test_digest.py",
  ...]
{
  "owned_paths": [
    "ai/scripts/feature_state_lib/cli_reporting.py",
    "ai/scripts/feature_state_lib/render_notes.py",
    "ai/scripts/feature-state.py",
    "tests/test_harness.py",
    "docs/adr/0040-honest-dashboard.md"
  ],
  "package_id": "P1-digest-no-esconde",
  "read_only_paths": [],
  "read_only_violations": []
}
OWNERSHIP_FAIL   (rc=2)
```

Confirmado programáticamente (no solo por lectura):
- `render_notes.py` está declarado en `owned_paths` pero **no aparece** en `changed_files`
  (ningún diff lo toca): `"render_notes.py" in changed_files` → `False`.
- `model.py`, `cli_lifecycle.py` y `tests/test_digest.py` **sí** aparecen en
  `changed_files` pero **no** están declarados en `owned_paths`.
- `docs/adr/0040-honest-dashboard.md` no existe: `ls docs/adr/ | grep 0040` →
  `0040-honest-digest-shared-liveness-predicate.md` (nombre real, distinto del declarado).

Salida completa guardada en
`/var/tmp/claude/.../scratchpad/f03-owned-paths-check.json` (sesión de repair) por si hace
falta el detalle íntegro de `changed_files`. Queda para que el orquestador corrija
`ai/state/features/020-honest-dashboard.json` con el "antes" documentado arriba.

## Conteo de tests — antes/después del repair

Base declarada en el brief: **943 OK / 3 skips**. El repair no agrega tests nuevos (repara
uno existente), así que el conteo total no cambia — nunca baja, y no tenía por qué subir:

```
$ python3 -m unittest discover -s tests
Ran 943 tests in 424.523s

OK (skipped=3)
```

Cero failures, cero errors, 3 skips (igual a la base). Corrida completa, sin `-p`/`-k`.

## Gates finales

```
$ ./ai/scripts/verify.sh
...
GLOBAL_PORTABILITY_OK
CANONICAL_PATHS_OK
FEATURE_STATE_OK
VERIFY_PASS

$ ./build.sh
CHECK_PASS: generated and validated profile go-zen
Generated tracked artifacts for go-zen.

$ ./build.sh --check
CHECK_PASS: generated and validated profile go-zen
SELF_SCAFFOLD_SYNC_OK files=2

$ git diff --check
(sin salida, exit 0)
```

## Los 5 espejos — `md5sum` final

```
$ md5sum ai/scripts/feature_state_lib/cli_reporting.py Global/claude-code/hooks/feature_state_lib/cli_reporting.py Global/codex/hooks/feature_state_lib/cli_reporting.py Global/opencode/hooks/feature_state_lib/cli_reporting.py PROYECTO/ai/scripts/feature_state_lib/cli_reporting.py
79b0b6c1d286a8a9f182147233f0e07e  ai/scripts/feature_state_lib/cli_reporting.py
79b0b6c1d286a8a9f182147233f0e07e  Global/claude-code/hooks/feature_state_lib/cli_reporting.py
79b0b6c1d286a8a9f182147233f0e07e  Global/codex/hooks/feature_state_lib/cli_reporting.py
79b0b6c1d286a8a9f182147233f0e07e  Global/opencode/hooks/feature_state_lib/cli_reporting.py
79b0b6c1d286a8a9f182147233f0e07e  PROYECTO/ai/scripts/feature_state_lib/cli_reporting.py
```

Los 5 hashes coinciden — sin drift.

## Alcance respetado

No se tocó nada de `019` (el árbol trae esa feature entera sin commitear, preexistente a
esta sesión, confirmado no tocado). No se tocó `P2-anclas-verificables` (no empezó). No se
relajó, salteó ni borró ningún test — el test de F-02 se corrigió en su fixture y sus
aserciones, nunca se debilitó (la aserción nueva es estrictamente más exigente que las que
reemplaza). No se mutó `ai/state/features/020-honest-dashboard.json` (F-03 queda para el
orquestador, con el "antes" documentado arriba).

## Cierre

`status: repaired`. Los tres findings quedan con cambio + verificación evidenciados
(F-01/F-02 con cambio de código/test; F-03 solo con verificación, sin cambio, por
diseño). Listo para `DELTA_REVIEW`.
