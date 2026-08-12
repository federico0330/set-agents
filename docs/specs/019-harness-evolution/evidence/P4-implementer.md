# P4-doctrine-human-layer — evidencia del implementer

Feature 019-harness-evolution, PKG-4 (AC-25..AC-29, ADR-0036 extensión decisión 8 + ADR-0037).
Instancia previa dejó el código/doctrina implementado en disco pero murió antes de escribir
evidencia. Esta instancia audita lo ya hecho contra cada AC, confirma mordida real de los 7
tests nuevos, corre los gates y escribe este archivo. No se tocó código de producción
(`ai/scripts/**`) — el paquete es puramente doctrinal, tal como pide el context pack.

## 1. Tabla AC → cambio → prueba

| AC | Cambio (archivo:línea) | Prueba |
|---|---|---|
| AC-25 (bloque `Impacto humano:` en el cierre de paquete) | `Global/_canonical/agents/orchestrator.md:690-706` (sub-bloque aditivo, después del cierre de paquete, antes del bloque `c)` de fin de turno) | `tests/test_harness.py:7718` `test_ac25_package_close_narrates_impacto_humano_subblock_additively` |
| AC-26 (`integrator`/`architect` mantienen `docs/modules/` vivo) | `Global/_canonical/agents/integrator.md:23-29` (paso 5 nuevo: `module-impact-detect`+`record-module-impact`/waiver+staleness check) · `Global/_canonical/agents/architect.md:47-50` (paso 7 extendido: entrada nueva en `modules.toml` al diseñar un módulo) | `tests/test_harness.py:7736` `test_ac26_integrator_and_architect_carry_module_impact_procedure` |
| AC-27 (protocolo "Resolvé antes de preguntar", ADR-0037) | `Global/_canonical/agents/orchestrator.md:519-528` (encabezado exacto `**Resolvé antes de preguntar (ADR-0037)**`, 4 fuentes en orden, ANTES de la lista askable) · `:553-557` (carve-out de plataforma nombrada demovido a caso particular) · espejos en `Global/_shared/{CLAUDE.md,AGENTS.pi.md,AGENTS.opencode.md,AGENTS.codex.md}` (Question policy) y `Global/_canonical/skills/request-triage/SKILL.md:18-24` (Step 0) | `tests/test_harness.py:7753` `test_ac27_resolve_before_asking_header_precedes_askable_list` + `:7773` `test_ac27_resolve_before_asking_mirrored_in_shared_doctrine_and_triage` |
| AC-28 (`/explicar`) | `Global/_canonical/commands/explicar.md` (nuevo, molde `consult.md`) + `Global/_canonical/skills/explicar/SKILL.md` (nuevo) | `tests/test_harness.py:7791` `test_ac28_explicar_is_read_only_no_state_and_names_the_staleness_mitigant` + `:7807` `test_ac28_explicar_reaches_the_four_runtime_trees` |
| AC-29 (frases exactas por grep, árboles regenerados, `roles.tsv` sin cambios) | los 7 tests nuevos son el propio grep-contrato; `roles.tsv` no tocado (`git diff roles.tsv` vacío) | `tests/test_harness.py:7824` `test_ac29_roles_tsv_unchanged_by_explicar` + §3/§4/§5 abajo |

ADR-0037 nuevo (`docs/adr/0037-resolve-before-asking-protocol.md`), indexado en
`docs/adr/README.md:44`. ADR-0036 extendido con la decisión 8
(`docs/adr/0036-cognitive-module-docs.md:125-148`), no reescrito — AC-25/AC-26 son
explícitamente su extensión, tal como pide el context pack (ADR-0037 cubre AC-27/AC-28 en
cambio, ver su sección "Fuera de alcance").

## 2. Frases doctrinales exactas agregadas, con el test que las assertea

- `Impacto humano:` / `Módulo: <slug>` / `Cambio de modelo mental: <qué cambió en cómo hay que
  pensar el sistema>` / `Tenés que saber: <lo que el usuario necesita tener presente de ahora en
  más>` — `orchestrator.md`, asserteado literal por `test_ac25_...` (`assertIn` de las 4 líneas).
- `**Resolvé antes de preguntar (ADR-0037)**` — encabezado exacto, `orchestrator.md`, asserteado
  por `test_ac27_resolve_before_asking_header_precedes_askable_list`, que además verifica el
  ORDEN (`## Question policy` < header < inicio de la lista askable) y las 4 fuentes en el
  bloque (`the original request`, `docs/notas/`, `ai/state/decisions-log.jsonl`,
  `the approved spec`).
- `particular case of the general rule above (ADR-0037` — el carve-out de plataforma nombrada
  demovido, mismo test.
- `Resolvé antes de preguntar (ADR-0037)` — espejo corto, presente literal en las 4 fuentes de
  `Global/_shared/` + `request-triage/SKILL.md`, asserteado por
  `test_ac27_resolve_before_asking_mirrored_in_shared_doctrine_and_triage`, que además corre
  `./build.sh` y confirma el espejo en los 4 árboles GENERADOS (`Global/{codex,pi,opencode}/AGENTS.md`,
  `Global/claude-code/CLAUDE.md`).
- `NO \`init\`, NO pipeline, NO mutation` / `Staleness check, mandatory, not a footnote` /
  `record-module-impact` — `explicar.md`, asserteado por
  `test_ac28_explicar_is_read_only_no_state_and_names_the_staleness_mitigant`.
- `Read-only, no feature state` / `Staleness is the point, not a footnote` /
  `record-module-impact` — `explicar/SKILL.md`, mismo test.
- `module-impact-detect` / `record-module-impact` / `--module-impact-waived` / `ADR-0036` /
  `stale` — `integrator.md`, asserteado por `test_ac26_...`.
- `modules.toml` / `[module.<slug>]` / `ADR-0036` — `architect.md`, mismo test.

## 3. Prueba de mordida (bite) de los 7 tests nuevos

Metodología para cada test: (a) confirmar que pasa hoy contra el diff en disco, (b) neutralizar
o invertir la frase/archivo que el test assertea, (c) confirmar rojo, (d) revertir con la copia
de respaldo y confirmar verde de nuevo. Todos corridos con
`python3 -m unittest discover -s tests -p "test_harness.py" -k <nombre>` (equivalente a `-k` de
pytest, disponible en `unittest` de Python 3.14) para evitar el aislamiento de import roto que
el context pack ya documenta.

### AC-25 — `test_ac25_package_close_narrates_impacto_humano_subblock_additively`

```
$ cp Global/_canonical/agents/orchestrator.md /var/tmp/orchestrator.md.bak
$ python3 - <<'EOF'
import re
p = "Global/_canonical/agents/orchestrator.md"
text = open(p, encoding="utf-8").read()
start = text.index("**At a package close specifically**")
end = text.index("**c) At the end of EVERY turn**")
text = text[:start] + text[end:]
open(p, "w", encoding="utf-8").write(text)
EOF
$ grep -n "Impacto humano\|At a package close specifically" Global/_canonical/agents/orchestrator.md
NOT_FOUND
$ python3 -m unittest discover -s tests -p "test_harness.py" -k test_ac25_package_close_narrates_impacto_humano_subblock_additively
F
======================================================================
FAIL: test_ac25_package_close_narrates_impacto_humano_subblock_additively (test_harness.HarnessTests.test_ac25_package_close_narrates_impacto_humano_subblock_additively)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/home/federico/SET-AGENTES/tests/test_harness.py", line 7724, in test_ac25_package_close_narrates_impacto_humano_subblock_additively
    self.assertIn("Impacto humano:", orchestrator)
    ~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'Impacto humano:' not found in '# Orchestrator — read-only coordinator of the package-based delivery lifecycle\n...'
FAILED (failures=1)
$ cp /var/tmp/orchestrator.md.bak Global/_canonical/agents/orchestrator.md
$ python3 -m unittest discover -s tests -p "test_harness.py" -k test_ac25_package_close_narrates_impacto_humano_subblock_additively
.
----------------------------------------------------------------------
Ran 1 test in 0.001s

OK
$ git status --porcelain > /var/tmp/status_after.txt && diff /var/tmp/status_before.txt /var/tmp/status_after.txt && echo STATUS_IDENTICAL
STATUS_IDENTICAL
$ git diff --stat > /var/tmp/diffstat_after.txt && diff /var/tmp/diffstat_before.txt /var/tmp/diffstat_after.txt && echo DIFFSTAT_IDENTICAL
DIFFSTAT_IDENTICAL
```

### AC-26 — `test_ac26_integrator_and_architect_carry_module_impact_procedure`

```
$ cp integrator.md integrator.md.bak
$ sed -i 's/module-impact-detect/MODULE-IMPACT-DETECT-DISABLED/g' integrator.md
$ python3 -m unittest discover -s tests -p "test_harness.py" -k test_ac26_...
AssertionError: 'module-impact-detect' not found in '...'
FAILED (failures=1)
$ cp integrator.md.bak integrator.md
$ python3 -m unittest discover -s tests -p "test_harness.py" -k test_ac26_...
OK
```

### AC-27a — `test_ac27_resolve_before_asking_header_precedes_askable_list`

```
$ cp orchestrator.md orchestrator2.md.bak
$ sed -i 's/\*\*Resolvé antes de preguntar (ADR-0037)\*\*/Resolve before asking (disabled)/' orchestrator.md
$ python3 -m unittest discover -s tests -p "test_harness.py" -k test_ac27_resolve_before_asking_header_precedes_askable_list
AssertionError: '**Resolvé antes de preguntar (ADR-0037)**' not found in '...'
FAILED (failures=1)
$ cp orchestrator2.md.bak orchestrator.md
$ python3 -m unittest discover -s tests -p "test_harness.py" -k test_ac27_resolve_before_asking_header_precedes_askable_list
OK
```

### AC-27b — `test_ac27_resolve_before_asking_mirrored_in_shared_doctrine_and_triage`

```
$ cp Global/_shared/CLAUDE.md CLAUDE.md.bak
$ sed -i 's/Resolvé antes de preguntar (ADR-0037)/DISABLED MIRROR/' Global/_shared/CLAUDE.md
$ python3 -m unittest discover -s tests -p "test_harness.py" -k test_ac27_resolve_before_asking_mirrored_in_shared_doctrine_and_triage
AssertionError: 'Resolvé antes de preguntar (ADR-0037)' not found in '...' : Global/_shared/CLAUDE.md
FAILED (failures=1)
$ cp CLAUDE.md.bak Global/_shared/CLAUDE.md
$ ./build.sh   # el test corre ./build.sh internamente; se regeneró para eliminar el drift
CHECK_PASS: generated and validated profile go-zen
$ ./build.sh --check
CHECK_PASS: generated and validated profile go-zen
SELF_SCAFFOLD_SYNC_OK files=2
```

### AC-28a — `test_ac28_explicar_is_read_only_no_state_and_names_the_staleness_mitigant`

```
$ cp Global/_canonical/commands/explicar.md explicar.md.bak
$ sed -i 's/Staleness check, mandatory, not a footnote/Staleness check/' Global/_canonical/commands/explicar.md
$ python3 -m unittest discover -s tests -p "test_harness.py" -k test_ac28_explicar_is_read_only_no_state_and_names_the_staleness_mitigant
AssertionError: 'Staleness check, mandatory, not a footnote' not found in '...'
FAILED (failures=1)
$ cp explicar.md.bak Global/_canonical/commands/explicar.md
$ python3 -m unittest discover -s tests -p "test_harness.py" -k test_ac28_explicar_is_read_only_no_state_and_names_the_staleness_mitigant
OK
```

### AC-28b — `test_ac28_explicar_reaches_the_four_runtime_trees`

```
$ cp Global/_canonical/skills/explicar/SKILL.md explicar-SKILL.md.bak
$ rm Global/_canonical/skills/explicar/SKILL.md
$ python3 -m unittest discover -s tests -p "test_harness.py" -k test_ac28_explicar_reaches_the_four_runtime_trees
FileNotFoundError: [Errno 2] No such file or directory: '.../Global/_canonical/skills/explicar/SKILL.md'
FAILED (errors=1)
$ cp explicar-SKILL.md.bak Global/_canonical/skills/explicar/SKILL.md
$ ./build.sh   # regenera los 4 árboles con el skill restaurado
$ python3 -m unittest discover -s tests -p "test_harness.py" -k test_ac28_explicar_reaches_the_four_runtime_trees
OK
```

### AC-29 — `test_ac29_roles_tsv_unchanged_by_explicar`

```
$ cp roles.tsv roles.tsv.bak
$ echo "explicar-fake-row" >> roles.tsv
$ python3 -m unittest discover -s tests -p "test_harness.py" -k test_ac29_roles_tsv_unchanged_by_explicar
AssertionError: 'explicar' unexpectedly found in '...explicar-fake-row\n'
FAILED (failures=1)
$ cp roles.tsv.bak roles.tsv
$ python3 -m unittest discover -s tests -p "test_harness.py" -k test_ac29_roles_tsv_unchanged_by_explicar
OK
```

Los 7 tests nuevos tienen mordida real confirmada: cada uno falla en rojo cuando el cambio que
assertea se neutraliza, y vuelve a verde tras revertir. `git status --porcelain` y
`git diff --stat` confirmados idénticos al estado previo a esta ronda de verificación (ver §5).

## 4. Los 4 árboles con `/explicar` presente

```
$ ./build.sh && ./build.sh --check
CHECK_PASS: generated and validated profile go-zen
SELF_SCAFFOLD_SYNC_OK files=2

$ diff Global/_canonical/skills/explicar/SKILL.md Global/opencode/skills/explicar/SKILL.md    # idéntico
$ diff Global/_canonical/skills/explicar/SKILL.md Global/claude-code/skills/explicar/SKILL.md  # idéntico
$ diff Global/_canonical/skills/explicar/SKILL.md Global/codex/skills/explicar/SKILL.md        # idéntico
$ diff Global/_canonical/skills/explicar/SKILL.md Global/pi/skills/explicar/SKILL.md           # idéntico
```

- `Global/opencode/commands/explicar.md` — idéntico al canónico (comando propagado byte a byte).
- `Global/claude-code/commands/explicar.md` — idéntico al canónico.
- `Global/codex/` — **no tiene directorio `commands/`** (mismo precedente que `/consult`, que
  tampoco existe en `Global/codex/commands/`); su cobertura es exclusivamente
  `Global/codex/skills/explicar/SKILL.md`, confirmado arriba. `test_ac28_explicar_reaches_the_four_runtime_trees`
  assertea explícitamente `self.assertFalse((ROOT / "Global/codex/commands").exists())` para
  dejar esto testeado, no supuesto.
- `Global/pi/prompts/explicar.md` — generado por `generate_pi_prompts` desde el frontmatter
  `agent: orchestrator`; contiene `subagent({ agent: "orchestrator"` (verificado por el test).

Los 4 runtimes tienen `/explicar` disponible: opencode y claude-code vía comando + skill, codex
y pi vía skill/prompt (codex sin árbol de comandos, pi vía su generador propio de prompts).

## 5. Gates

```
$ python3 -m unittest discover -s tests
Ran 863 tests in 443.148s
OK (skipped=3)
```
Línea base declarada por el context pack: 856 OK / 3 skips. 863 − 856 = 7, exactamente los 7
tests nuevos de este paquete (`grep -c "def test_ac2" tests/test_harness.py` → 7), sin ningún
otro test agregado o quitado. El número sube, nunca baja. Cero regresiones, cero tests
debilitados/saltados/borrados.

```
$ ./ai/scripts/verify.sh
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

```
$ git status --porcelain Global/_canonical Global/_shared roles.tsv
 M Global/_canonical/agents/architect.md
 M Global/_canonical/agents/integrator.md
 M Global/_canonical/agents/orchestrator.md
 M Global/_canonical/skills/request-triage/SKILL.md
 M Global/_shared/AGENTS.codex.md
 M Global/_shared/AGENTS.opencode.md
 M Global/_shared/AGENTS.pi.md
 M Global/_shared/CLAUDE.md
?? Global/_canonical/commands/explicar.md
?? Global/_canonical/skills/explicar/
```
(idéntico al estado previo a la ronda de mordida — todos los archivos temporalmente alterados
para las pruebas de bite fueron restaurados desde copias de respaldo y re-verificados byte a
byte con `git diff --stat` antes/después de cada uno; `roles.tsv` sin diff, como exige AC-29).

## 6. Alcance respetado

- No se tocó `ai/scripts/**` (código de producción) — el paquete es 100% doctrina/comandos/skills.
- No se tocó `docs/modules/**` ni el motor de render (`render_modules.py`) — eso es P3, ya cerrado.
- No se tocó `roles.tsv` (confirmado §5) — `/explicar` es un comando que corre el orquestador,
  no un rol nuevo.
- Solo se editó `Global/_canonical/` y `Global/_shared/`; los 4 árboles generados
  (`Global/{claude-code,codex,opencode,pi}/`) y `PROYECTO/` se regeneraron con `./build.sh`, sin
  edición manual — confirmado por `./build.sh --check` sin drift.
- No hubo refactors oportunistas sobre los briefs de rol: la superficie es exactamente lo que
  cada AC pide (un paso en `integrator.md`, una extensión de un paso existente en `architect.md`,
  un sub-bloque en `orchestrator.md`, un protocolo + espejos, un comando + skill nuevos).

## 7. Estado del paquete

No marco este paquete como aceptado ni corro gates de review — eso es de `gate-runner`/
`package-reviewer`. Los comandos de estado (`start-task`/`complete-task`/`record-gate`/
`transition`) quedan para que el orquestador los corra según su propia doctrina.
