# C1-estado-fuera-del-producto — evidencia del implementer

Paquete más delicado de 024: mueve el estado real del harness, en vivo, en la máquina
donde se implementa. Ver ADR-0047 (`docs/adr/0047-el-estado-no-es-el-producto.md`) para la
decisión completa; esto es la prueba de que se ejecutó sin pérdida.

## Tabla AC → cambio → prueba

| AC | Cambio | archivo:línea | Prueba |
|---|---|---|---|
| AC-01 (`git mv`) | `git mv ai/state docs/historia/estado-2026-08` | (operación de git, no una línea de código) | `git status` muestra los 29 pares como `renombrados:`, no como archivo nuevo + borrado — ver sección "git mv preservó historia" abajo. |
| AC-01 (gitignore) | `.gitignore` gana `/ai/state/` | `.gitignore:53` | `git check-ignore -v ai/state/STATUS.md` → `.gitignore:53:/ai/state/ ai/state/STATUS.md`; `git ls-files ai/state \| wc -l` → `0`. |
| AC-01 (semilla) | `ai/state.seed/` (esqueleto trackeado, vacío) + `ai/scripts/seed-state.py` (`seed_state()`, guarda por ausencia) | `ai/scripts/seed-state.py:45-58` | `test_seed_state_only_populates_an_absent_ai_state` (`tests/test_harness.py:5445`) — corrida dos veces, manifiesto byte a byte idéntico; caso de no-pisado con datos "reales" preexistentes. Rojo/verde abajo. |
| AC-02 (pregunta acotada) | `baseline_sha()` ancla en el commit más antiguo que agrega `ai/state.seed/`; `delivery_commits()` usa `{baseline}..HEAD` en vez de todo el historial | `ai/scripts/check-feature-state.py:101-109` (`baseline_sha`), `:119-159` (`delivery_commits`) | `test_feature_state_gate_baseline_excludes_pre_move_deliveries_but_not_new_ones` (`tests/test_harness.py:5386`). Rojo/verde abajo. |
| AC-02 (degradado ruidoso conservado) | `baseline is None` → `FEATURE_STATE_UNCHECKED reason=baseline-unknown` (mismo patrón que `shallow-clone` preexistente); caso especial: `ai/state.seed/` presente en el árbol de trabajo pero sin commit todavía → ventana vacía, no "unusable" | `ai/scripts/check-feature-state.py:148-151` | `test_feature_state_gate_mid_migration_uncommitted_seed_is_not_unusable` (`tests/test_harness.py:5492`). Rojo/verde abajo. Encontrado por un test **preexistente** que rompió de verdad: ver sección dedicada. |
| ADR-0047 | Decisión completa documentada | `docs/adr/0047-el-estado-no-es-el-producto.md` (nuevo), indexado en `docs/adr/README.md:54` | `test_every_adr_on_disk_has_a_row_in_the_index` y `test_the_adr_index_never_lists_a_file_that_is_not_there` — ambos verdes (ver corrida de suite completa abajo). |

## `git mv` preservó historia (no `cp` + `rm`)

```
$ git status
Cambios a ser confirmados:
	renombrados:     ai/state/STATUS.md -> docs/historia/estado-2026-08/STATUS.md
	renombrados:     ai/state/bitacora/sin-feature.md -> docs/historia/estado-2026-08/bitacora/sin-feature.md
	renombrados:     ai/state/decisions-log.jsonl -> docs/historia/estado-2026-08/decisions-log.jsonl
	... (29 pares en total, los 23 features + STATUS.md + bitacora/ + los tres *-log.jsonl + project.json)
```

29 pares, todos `renombrados:`, cero `nuevo archivo:` + `borrado:` sueltos. `git diff --cached --stat -M`
confirma cada uno con `0 insertions(+), 0 deletions(-)` (contenido bit a bit idéntico, sólo cambió la
ruta).

## Las 23 features siguen legibles en `docs/historia/estado-2026-08/`

```
$ python3 - <<'PY'
import json
from pathlib import Path
d = Path("docs/historia/estado-2026-08/features")
files = sorted(d.glob("*.json"))
print("count:", len(files))
ok = 0
for f in files:
    doc = json.loads(f.read_text())
    assert doc.get("feature_id"), f"no feature_id in {f}"
    ok += 1
print("all parsed with feature_id:", ok)
PY
count: 23
all parsed with feature_id: 23
```

## El `ai/state/` en runtime de esta máquina sigue teniendo lo de Federico, no la semilla vacía

Backup tomado ANTES de tocar nada (`cp -a ai/state/. <scratchpad>/ai-state-backup/`, 29 archivos,
`diff -rq` limpio contra el original). Después del `git mv` + `.gitignore` + restauración manual
(`cp -a docs/historia/estado-2026-08 ai/state`):

```
$ diff -rq ai/state <scratchpad>/ai-state-backup && echo MATCHES_ORIGINAL_BACKUP_EXACTLY
MATCHES_ORIGINAL_BACKUP_EXACTLY
$ find ai/state -type f | wc -l
29
```

Bit a bit idéntico al estado real de Federico antes de que este paquete tocara nada. La regla que
lo protege — "la siembra sólo puebla un `ai/state/` ausente, nunca pisa uno existente"
(`ai/scripts/seed-state.py:53-54`) — es la misma guarda que, corrida después, encuentra este
`ai/state/` ya poblado y no hace nada (`STATE_SEED_SKIP_EXISTING`, probado en la sección
siguiente con datos reales, no sólo con la restauración de arriba).

## Siembra: idempotencia y no-pisado (corrida dos veces)

`test_seed_state_only_populates_an_absent_ai_state` (`tests/test_harness.py:5445-5490`), tres
escenarios en fixtures aisladas (nunca contra el `ai/state/` real):

1. **Ausente → poblado.** `ai/state/` no existe; primera corrida imprime `STATE_SEEDED`;
   `ai/state/features/.gitkeep` y `ai/state/bitacora/.gitkeep` quedan presentes.
2. **Poblado → no-op, dos veces.** Manifiesto (ruta → bytes) tomado después de la primera
   corrida; segunda corrida imprime `STATE_SEED_SKIP_EXISTING`; manifiesto after == manifiesto
   before, comparación byte a byte, no sólo el código de salida.
3. **Datos "reales" preexistentes, nunca pisados.** `ai/state/features/999-real-work.json` con
   contenido arbitrario, sin ningún archivo de la semilla adentro; la corrida imprime
   `STATE_SEED_SKIP_EXISTING`; el archivo real queda byte a byte igual; `.gitkeep` de la semilla
   NUNCA aparece (prueba que no es un merge parcial).

### Rojo/verde (AC-01, siembra)

Neutralizado (`ai/scripts/seed-state.py:53` → `if False:` en vez de `if _present(target):`, y
`copytree(..., dirs_exist_ok=True)` para que no explote):

```
FAIL: test_seed_state_only_populates_an_absent_ai_state
AssertionError: 'STATE_SEED_SKIP_EXISTING' not found in 'STATE_SEEDED\n'
```

Revertido a la versión real, verde de nuevo:

```
test_seed_state_only_populates_an_absent_ai_state ... ok
```

## AC-02: comportamiento nuevo en un clon limpio

`test_feature_state_gate_baseline_excludes_pre_move_deliveries_but_not_new_ones`
(`tests/test_harness.py:5386-5443`). Fixture que reproduce exactamente la forma de un clon
nuevo: un commit de entrega vieja (`Feature 010 P1...`) **antes** de que `ai/state.seed/`
empiece a existir, sin `ai/state/features/010-delivered.json` en ningún lado (la misma forma
que tiene el `ai/state/` recién sembrado y vacío de un tercero). Resultado: `FEATURE_STATE_OK`,
sin mencionar `010-delivered` — cero falsos positivos. Un commit de entrega **nuevo**
(`Feature 011 P1...`), después del baseline, sigue atrapado: `FEATURE_STATE_MISSING
id=011-new` — el degradado ruidoso no se apagó, se acotó.

### Rojo/verde (AC-02, pregunta acotada)

Neutralizado (`ai/scripts/check-feature-state.py:157` → `git(root, "log", "--format=%h %s")`
sin el rango `{baseline}..HEAD`, exactamente el comportamiento viejo):

```
FAIL: test_feature_state_gate_baseline_excludes_pre_move_deliveries_but_not_new_ones
AssertionError: 1 != 0 : FEATURE_STATE_MISSING id=010-delivered evidence=f714fe6 'Feature 010 P1-first-slice: deliver the first package'
  remedy: python3 ai/scripts/feature-state.py init 010-delivered ...
FEATURE_STATE_MISSING count=1
```

Exactamente el falso positivo que el AC existe para cerrar. Revertido, verde de nuevo:

```
test_feature_state_gate_baseline_excludes_pre_move_deliveries_but_not_new_ones ... ok
```

## Hallazgo real durante la implementación: el caso "migración sin commit todavía"

`test_guest_copy_scaffolds_and_verifies_portably` (preexistente, AC-09, `tests/test_harness.py:3470`)
rompió de verdad la primera vez que corrí `verify.sh` completo — no un test nuevo mío, uno que ya
existía y pasaba antes de este paquete. Copia el checkout entero (con `.git`, sin commitear nada)
a un directorio "guest" y corre `verify.sh` ahí adentro. Como este paquete todavía no tiene su
propio commit (lo hace el orquestador en INTEGRATION), `ai/state.seed/` existe en el árbol de
trabajo pero en ningún commit — `baseline_sha()` no encuentra nada, y sin manejar ese caso
`delivery_commits()` degradaba a `FEATURE_STATE_UNCHECKED reason=baseline-unknown` en vez de
`FEATURE_STATE_OK`, rompiendo la aserción del test.

Arreglo: cuando no hay baseline en el historial PERO `ai/state.seed/` existe en el árbol de
trabajo, la ventana es vacía (nada puede estar "después" de un commit que todavía no se hizo) →
`FEATURE_STATE_OK`, no "no puedo responder" (`ai/scripts/check-feature-state.py:148-151`). Nuevo
test dedicado: `test_feature_state_gate_mid_migration_uncommitted_seed_is_not_unusable`
(`tests/test_harness.py:5492-5527`).

### Rojo/verde (caso mid-flight)

Neutralizado (`ai/scripts/check-feature-state.py:150` → `if False:` en vez de
`if (root / "ai" / "state.seed").is_dir():`):

```
FAIL: test_feature_state_gate_mid_migration_uncommitted_seed_is_not_unusable
AssertionError: 'FEATURE_STATE_OK' not found in ''
```

Revertido, verde de nuevo:

```
test_feature_state_gate_mid_migration_uncommitted_seed_is_not_unusable ... ok
```

Y el test preexistente que originalmente lo encontró, verde de nuevo:

```
test_guest_copy_scaffolds_and_verifies_portably ... ok
```

## Tests preexistentes ajustados (no debilitados)

`test_feature_state_gate_fails_when_a_delivered_feature_has_no_state_file`
(`tests/test_harness.py:5242`) construye fixtures de git sintéticas. Con la pregunta acotada a
"desde mi baseline", cada fixture necesita su propio commit que establece el baseline
(`ai/state.seed/.gitkeep`) ANTES de los commits que el test siempre probó — mismo comportamiento
que siempre afirmó, ahora sobre una historia con forma post-ADR-0047. Sin este ajuste el test
fallaba en la primera línea (`FEATURE_STATE_OK not found in ''`) porque no había baseline que
encontrar; confirmado corriendo el test contra el código nuevo ANTES de tocar el fixture.

## Gates

**Suite completa** (`ai/scripts/heartbeat-run.py --interval 20 -- python3 -m unittest discover -s tests`,
corrida limpia, sin pipear a `tail`, redirigida a archivo):

```
Ran 1110 tests in 495.079s

OK (skipped=3)
```

Base 1107 OK / 3 skips + 3 tests nuevos (`test_feature_state_gate_baseline_excludes_pre_move_deliveries_but_not_new_ones`,
`test_seed_state_only_populates_an_absent_ai_state`,
`test_feature_state_gate_mid_migration_uncommitted_seed_is_not_unusable`) = 1110 OK / 3 skips.
Mismos 3 skips que la base (no se salteó nada nuevo).

**`verify.sh`**:

```
Ran 1110 tests in 493.540s

OK (skipped=3)
...
GLOBAL_PORTABILITY_OK
CANONICAL_PATHS_OK
FEATURE_STATE_OK
VERIFY_PASS
```

**`build.sh --check`**:

```
SELF_SCAFFOLD_SYNC_OK files=2
GLOBAL_TREE_SYNC_OK profile=go-zen harnesses=4
BUILD_CHECK_PASS
```

**`check-drift.sh`**:

```
DRIFT_DETECTED: 5 archivos gestionados difieren entre el repo y la instalación.
  → corré: cd /home/federico/SET-AGENTES && ./build.sh --install
  (una instalación atrasada ya costó una semana de cuota: revisores huérfanos caros + MCP prendido.)
```

**Preexistente, no causado por este paquete** — confirmado con `install.py --preview`: los 5
archivos son `agents/orchestrator.md`/`.toml` de los cuatro harnesses + `opencode.json` (cambio
de proveedor Ollama/npm), ninguno relacionado con `ai/state`, `check-feature-state.py` ni
`seed-state.py`. Ya aparecían modificados sin commitear en `Global/*/agents/orchestrator.*` desde
antes de que este paquete empezara (visible en el `git status` inicial de la sesión — trabajo de
otro paquete en curso en este mismo checkout). No se tocó nada bajo `Global/` para no salir del
alcance de C1 (`models.toml` y el overlay de usuario son C2; `Global/` ni figura en el alcance de
C1). Flageado para el orquestador.

**`git diff --check`**:

```
$ git diff --check; echo $?
0
$ git diff --cached --check; echo $?
0
```

Limpio, sin errores de espacios en blanco, tanto en lo no-stageado como en lo stageado
(`git add -A` corrido antes de las corridas finales de gates).

## Archivos tocados

- `.gitignore` — `/ai/state/` (línea 53).
- `ai/scripts/check-feature-state.py` — `baseline_sha()`, `delivery_commits()` acotado al rango
  post-baseline, caso mid-flight.
- `ai/scripts/seed-state.py` — nuevo.
- `ai/state.seed/README.md`, `ai/state.seed/features/.gitkeep`, `ai/state.seed/bitacora/.gitkeep` — nuevos.
- `docs/adr/0047-el-estado-no-es-el-producto.md` — nuevo.
- `docs/adr/README.md` — fila 0047 indexada.
- `tests/test_harness.py` — 3 tests nuevos + 2 fixtures preexistentes ajustadas al baseline.
- `ai/state/` → `docs/historia/estado-2026-08/` vía `git mv` (29 archivos, historia preservada).

## Fuera de alcance / flags para el orquestador

- El `DRIFT_DETECTED` de `check-drift.sh` es preexistente (`Global/*/agents/orchestrator.*` +
  `opencode.json`, provider Ollama) — no tocado, no es de este paquete.
- No se invocó `ai/scripts/seed-state.py` en ningún punto de entrada automático (`verify.sh`,
  `build.sh`, primer arranque). El contexto pack asigna "el primer arranque y
  `ROUTING_UNCONFIGURED`" a C3 — dejo el mecanismo listo, probado, e idempotente, pero la
  decisión de CUÁNDO invocarlo automáticamente (onboarding interactivo) queda para ese paquete,
  tal como lo define el "fuera de alcance" del propio context pack.
