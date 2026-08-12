# P2-anclas-verificables — evidencia del implementer

Feature: `020-honest-dashboard`. Paquete: `P2-anclas-verificables`. P1 aceptado.

**Relanzamiento**: instancia anterior murió por stall de infraestructura (600s sin
progreso) sin dejar artefactos. Este archivo se crea en el primer minuto y se guarda a
disco después de cada AC, código+test+fila incluidos, para que un corte deje lo anterior
completo y verificable.

## Línea base verificada

`docs/modules/consola.md` dice `set_agents_app.py:2510` → `main()`. Confirmar la línea real
del `main()` en el árbol es el primer paso (ver tabla de AC-10).

## Tabla AC → cambio → prueba

| AC | Estado | Cambio (`archivo:línea`) | Prueba |
|---|---|---|---|
| AC-06 | hecho | `ai/scripts/feature_state_lib/check_anchors.py` (288 líneas tras el repair de F-01/F-02, ver `P2-repair.md`): gramática de dos formas (`COMPLETE_TOKEN_RE`/`ABBREV_TOKEN_RE`, `:58-59`), resolución por basename acotada al módulo (`_resolve_basename`, `:110-133`; `_expand_module_files`, `:83-107`) | `tests/test_check_anchors.py::GrammarAndResolutionTests` (25 tests tras el repair) |
| AC-07 | hecho | `check_anchors()` (`check_anchors.py:259-288`) + `cmd_check_anchors` (`cli_modules.py:119-132`, nuevo) + subcomando `check-anchors --module` en `feature-state.py` (`build_parser`, junto a `module-impact-detect`) | `tests/test_check_anchors.py::CliCheckAnchorsTests` (5 tests) + corrida real más abajo |
| AC-11 | hecho | mismo módulo; casos "línea fuera de rango" y "símbolo movido" | `test_ac11_out_of_range_line_is_reported_broken`, `test_ac11_moved_symbol_is_reported_broken` (ambos con doc adversario sintético, no contra los docs reales) |
| AC-08 | hecho, acotado | `_adjacent_symbol`/`_semantic_check` (`check_anchors.py:136-165`): solo backticks inmediatamente adyacentes, misma línea, comparación de texto en ventana ±2; ranges/comodines/prosa-separados excluidos explícitamente en `_build_entry` (`:168-203`) | `test_range_anchor_in_bounds_passes_even_with_a_wrong_adjacent_symbol`, `test_wildcarded_adjacent_symbol_is_never_semantically_checked`, `test_symbol_separated_from_anchor_by_prose_is_not_semantically_checked` — cobertura real acotada por diseño, ver corrección post-review más abajo |
| AC-09 | hecho | `_warn_check_anchors_never_raises` (`cli_reporting.py:120-136`), enganchada al final de `cmd_sync_notes` (llamada en `:160`); nunca gate (contrato explícito en docstring y en el spec) | `tests/test_check_anchors.py::SyncNotesNeverRaisesTests` (2 tests) + mordida 6 abajo |
| AC-10 | hecho | ver tabla de correcciones más abajo (`consola.md`, `generacion-arboles.md`, `estado.md`, `routing.md`, `narracion-notas.md`) | `check-anchors` antes (rc=1, 7 rotas) → después (rc=0) |

## check-anchors — antes (con las rotas de hoy)

Corrida real, literal, contra el árbol tal como estaba antes de las correcciones de AC-10
(`python3 ai/scripts/feature-state.py check-anchors`, rc real verificado por separado
con `echo $?` tras una corrida sin pipe, para no perder el código de salida en el `tee`):

```
$ python3 ai/scripts/feature-state.py check-anchors
ANCHOR_BROKEN docs/modules/consola.md:26 `ai/scripts/set_agents_app.py:2510` -> symbol 'main' not found near ai/scripts/set_agents_app.py:2510 (checked lines 2508-2512)
ANCHOR_BROKEN docs/modules/generacion-arboles.md:29 `ai/scripts/generate.py:707` -> symbol 'main' not found near ai/scripts/generate.py:707 (checked lines 705-709)
ANCHOR_BROKEN docs/modules/generacion-arboles.md:40 `generate.py:367` -> symbol 'generate_pi_prompts' not found near ai/scripts/generate.py:367 (checked lines 365-369)
ANCHOR_BROKEN docs/modules/generacion-arboles.md:42 `generate.py:648` -> symbol 'validate_pi_target' not found near ai/scripts/generate.py:648 (checked lines 646-650)
ANCHOR_BROKEN docs/modules/narracion-notas.md:30 `:151-174` -> unresolvable: no file named earlier in this list item/paragraph
ANCHOR_BROKEN docs/modules/narracion-notas.md:34 `:154` -> unresolvable: no file named earlier in this list item/paragraph
ANCHOR_BROKEN docs/modules/routing.md:32 `ai/scripts/set_agents_app.py:452-488` -> no file named 'set_agents_app.py' inside this module's declared paths (modules.toml)
{
  "anchor_count": 41, "ok": false, "form_counts": {"abbreviated": 22, "complete": 19},
  "checked_docs": ["consola.md", "estado.md", "generacion-arboles.md", "narracion-notas.md", "routing.md"]
}

$ python3 ai/scripts/feature-state.py check-anchors >/dev/null 2>&1; echo "rc=$?"
rc=1
```

7 rotas reportadas. Dos motivos distintos, ambos por diseño (SC-01/AC-08), no bugs:
- **Semántica (AC-08)**: `main`/`generate_pi_prompts`/`validate_pi_target` no aparecen en
  la ventana de la línea citada — el defecto insignia (`consola.md:26`, `main()` a +742
  líneas) cae acá.
- **Resolución cruzada de módulo (SC-01, bloqueante ya resuelto)**: `narracion-notas.md`
  cita `feature-state.py`/`cli_reporting.py` (dueños del módulo `estado`, no de
  `narracion-notas`) y `routing.md` cita `set_agents_app.py` (dueño del módulo `consola`).
  SC-01 exige resolver el basename **solo dentro de los `paths` del módulo que se está
  chequeando** — una cita entre módulos no se puede expresar como ancla verificable sin
  violar esa regla (o inventar una búsqueda global, prohibida explícitamente). Corregido en
  la tabla de AC-10 más abajo (bajando el número de línea, dejando el puntero al módulo
  dueño en prosa) y documentado como consecuencia de diseño en ADR-0040 sección 5.

**Anclas rotas de hoy que el checker NO puede ver, verificadas aparte por `grep -n`
directo contra el código real** (drift conocido, corregido igual en AC-10 porque AC-10 es
una corrección de hechos, no solo "lo que el comando detecta"):
- `estado.md` `:190`/`:277` (orden símbolo-antes-de-ancla, fuera del alcance acotado de
  AC-08) y `:788` (separado por prosa "en") — los tres pasan el chequeo de rango en
  silencio (están dentro del archivo) pero apuntan a contenido equivocado.
- `generacion-arboles.md:27` `generate.py:441` — el símbolo adyacente
  (`` `generate(out, profile, ...)` ``) se corta a mitad del token por el wrap de línea del
  markdown (el backtick de cierre cae en la línea siguiente); sin símbolo adyacente
  detectable, solo chequeo de rango, que pasa en silencio.
- `generacion-arboles.md:42` `generate.py:669` (`validate`) — **falso negativo real**: la
  ventana de ±2 líneas alrededor de la línea 669 vieja cae dentro del docstring de
  `validate_pi_target`, que menciona "`validate()`" en prosa (línea 667 real,
  "...distinct from, and not duplicated by, the two `validate()` loops...") — coincidencia
  textual que hace pasar la comparación de texto aunque la línea esté mal. Limitación
  documentada de la ventana chica de AC-08 (comparación de texto, no AST), no un bug.

## AC-10 — correcciones aplicadas (grep directo contra el código real, no supuesto)

Cada línea real verificada con `grep -n "^def "` (o el `def` correspondiente) contra el
árbol actual — comando y salida en la sección "Línea base verificada" y en el bloque de
la corrida `check-anchors` "antes". Tabla completa de correcciones:

| Doc:línea | Antes | Después | Motivo |
|---|---|---|---|
| `consola.md:26` | `set_agents_app.py:2510` | `:3252` | `main()` real (+742, el defecto insignia de la spec) |
| `consola.md:34` | `set_agents_app.py:452-819` | `:454-821` | cluster `cmd_route_*`/`cmd_routing_*`/`cmd_doctor*`, +2 uniforme (verificado extremo a extremo: `cmd_route_explain` real en 454, `cmd_doctor_all` real en 821) |
| `consola.md:36` | `set_agents_app.py:325-412` | `:327-414` | cluster `cmd_model_preference_*`/`cmd_model_pin_*`, +2 (`cmd_model_preference_set`=327, `cmd_model_pin_clear`=414) |
| `consola.md:38` | `set_agents_app.py:1087` | `:1089` | `cmd_status` real, +2 |
| `generacion-arboles.md:27` | `generate.py:441` | `:450` | `generate()` real, +9 — el checker NO lo detecta (símbolo cortado por wrap de línea markdown), corregido por grep directo |
| `generacion-arboles.md:29` | `generate.py:707` | `:716` | `main()` real, +9 — detectado por el checker (semántica) |
| `generacion-arboles.md:40` | `generate.py:367` | `:376` | `generate_pi_prompts` real, +9 — detectado por el checker |
| `generacion-arboles.md:42` | `generate.py:648` | `:657` | `validate_pi_target` real, +9 — detectado por el checker |
| `generacion-arboles.md:42` | `generate.py:669` | `:678` | `validate` real, +9 — **falso negativo real** (ver sección "antes"), corregido por grep directo |
| `estado.md:27` | `feature-state.py` … `:788` | `:797` | `build_parser()` real, +9 |
| `estado.md:35` | `model.py` … `:190` | `:260` | `compact_package` real, +70 — **regresión nueva de PKG-1** (agregó el predicado compartido en `model.py`, corriendo todo lo de abajo); orden símbolo-antes-de-ancla, fuera del alcance semántico de AC-08, corregido por grep directo |
| `estado.md:36` | `model.py` … `:277` | `:347` | `validate_state` real, +70, misma causa |
| `routing.md:31-32` | `set_agents_app.py:452-488` | sin línea, "módulo `consola`" | cita entre módulos (SC-01): `set_agents_app.py` no es de `routing.paths`, irresoluble por diseño — no un número a corregir |
| `narracion-notas.md:30` | `` `:151-174` `` | sin línea, "módulo `estado`" | cita entre módulos: `feature-state.py` no es de `narracion-notas.paths` |
| `narracion-notas.md:34` | `` `:154` `` | sin línea, "módulo `estado`" | cita entre módulos: `cli_reporting.py` no es de `narracion-notas.paths` |

No tocado (ya correctos, verificado real=doc): `routing.py`/`routing_core/*.py` (todos los
9 anchors, `routing.md` completo salvo la cita cruzada de arriba), `render_notes.py`,
`render_status.py` (todos los de `narracion-notas.md` salvo las dos citas cruzadas),
`transitions.py` (`:17`/`:54`), `feature-state.py:82-105` (rango, sigue exacto),
`feature-state.py:151-174`/`mutate()` (exacto, pero solo verificable en `estado.md`,
dueño real — la cita del mismo rango en `narracion-notas.md` es la cruzada de arriba),
`generate.py:55`/`:129` (`load_roles`/`oc_permissions`, antes de la inserción de +9).

## check-anchors — después (rc=0)

Literal, corrida real tras aplicar todas las correcciones de arriba:

```
$ python3 ai/scripts/feature-state.py check-anchors
ANCHORS_OK checked=5 anchors=38
{
  "anchor_count": 38,
  "broken": [],
  "checked_docs": ["consola.md", "estado.md", "generacion-arboles.md", "narracion-notas.md", "routing.md"],
  "form_counts": {"abbreviated": 20, "complete": 18},
  "ok": true
}

$ python3 ai/scripts/feature-state.py check-anchors --module consola
ANCHORS_OK checked=1 anchors=4
{"anchor_count": 4, "broken": [], "checked_docs": ["consola.md"], "form_counts": {"abbreviated": 0, "complete": 4}, "ok": true}

$ python3 ai/scripts/feature-state.py check-anchors >/dev/null 2>&1; echo "rc=$?"
rc=0

$ python3 ai/scripts/feature-state.py sync-notes
NOTES_SYNCED n=0
{"notes_dir": "/home/federico/SET-AGENTES/docs/notas", "ok": true, "written": []}
```

`anchor_count` bajó de 41 a 38 (las 3 anclas de cita cruzada dejaron de ser anclas: pasaron
a prosa con puntero de módulo, no un número que la herramienta no puede respaldar).

## Falsos positivos (ambas direcciones, con doc adversario — no contra los docs reales)

`tests/test_check_anchors.py::GrammarAndResolutionTests`:
- `test_false_positives_produce_zero_anchors_and_never_appear_broken` — doc con
  `` `localhost:8080` ``, `` `12:30` ``, `` `http://x:80` ``, `` `10-20` `` (los 4 casos de
  AC-06/SC-02) → `anchor_count == 0`, `ok == True`: ninguno se reconoce como ancla
  (dirección 1: no debe haber falsos positivos).
- `test_false_positives_do_not_hide_a_real_broken_anchor_in_the_same_doc` — mismos 4
  casos MÁS un `` `foo.py:9999` `` real y roto en el mismo documento → `anchor_count == 1`
  (solo el real se cuenta), y aparece en `broken` con motivo "out of range" (dirección 2:
  los falsos positivos no deben opacar un ancla real).

## Conteo de anclas detectadas por forma (prueba de que se cubren las dos, no la mitad)

Sobre los 5 módulos reales, después de las correcciones: **18 completas + 20 abreviadas =
38** (ver JSON de arriba, `form_counts`). Antes de las correcciones: 19 completas + 22
abreviadas = 41 (3 menos después porque las 3 citas cruzadas dejaron de ser anclas
verificables, no porque el checker dejó de contarlas). Ambas formas están representadas en
las decenas, no en un caso aislado — `tests/test_check_anchors.py::
test_both_forms_are_counted_not_just_the_complete_one` lo prueba también contra el doc
sintético.

## Corrección post-review (repair F-02) — cobertura semántica real, no solo "38 anclas"

El review independiente marcó que el conteo de arriba (**38 anclas, 18+20**) mide anclas
**reconocidas**, no anclas con **chequeo semántico activo** — y que presentado solo así
sobreestima cuánto protege `rc=0`. Corrección, medida directamente (no de memoria):
contando cuántas de las 38 entradas de `_scan_doc` traen la clave `symbol` (es decir,
tuvieron un backtick inmediatamente adyacente y por lo tanto corrieron `_semantic_check`):

```
$ python3 - <<'EOF'
import sys; sys.path.insert(0, "ai/scripts")
from pathlib import Path
from feature_state_lib import check_anchors as ca
from feature_state_lib.render_modules import load_modules_toml, MODULES_TOML
root = Path(".")
modules_dir = root / "docs" / "modules"
modules = load_modules_toml(modules_dir / MODULES_TOML)
total = with_symbol = 0
by_form = {"complete": {"total": 0, "symbol": 0}, "abbreviated": {"total": 0, "symbol": 0}}
for slug in sorted(modules):
    doc_path = modules_dir / f"{slug}.md"
    if not doc_path.is_file():
        continue
    file_index = ca._expand_module_files(root, modules[slug]["paths"])
    for r in ca._scan_doc(root, doc_path, file_index, f"docs/modules/{slug}.md"):
        total += 1
        by_form[r["form"]]["total"] += 1
        if "symbol" in r:
            with_symbol += 1
            by_form[r["form"]]["symbol"] += 1
print(total, with_symbol, by_form)
EOF
38 12 {'complete': {'total': 18, 'symbol': 10}, 'abbreviated': {'total': 20, 'symbol': 2}}
```

**Solo 12 de 38 anclas (32%) reciben verificación semántica activa** — 10 de las 18
completas, 2 de las 20 abreviadas (la forma abreviada casi nunca trae un símbolo entre
backticks pegado al `` `:N` ``, así que la mayoría se queda en chequeo de rango). Las otras
26 pasan porque la línea existe dentro del archivo, no porque el símbolo se haya
verificado. Prueba concreta de que esto es real y no un tecnicismo: `` `foo.py:8` es
`alpha()` `` con la línea 8 real diciendo `beta` → `ok=True` (el conector "es" apaga la
adyacencia) — fijado como test,
`tests/test_check_anchors.py::GrammarAndResolutionTests::
test_prose_connector_lets_a_genuinely_false_claim_about_a_real_symbol_pass`.

`rc=0` de `check-anchors` significaba, sin esta aclaración, "38 anclas, dos formas
cubiertas" de un modo que un lector razonablemente asume como "38 anclas verificadas". El
significado correcto es: "ninguna de las 38 está fuera de rango, y de las que además
tienen símbolo adyacente (12), ninguna está semánticamente mal". Ver ADR-0040 sección 5
para la misma cifra puesta en el lugar donde vive la decisión de diseño, y F-03 más abajo
para la magnitud medida del margen de falso negativo dentro de esas 12.

## Corrección post-review (repair F-03) — magnitud medida de la ventana ±2

El review también marcó que el falso negativo documentado más arriba
(`generacion-arboles.md:42` → `validate`, coincidencia con un docstring cercano) no está
presentado como lo que es: una propiedad estructural de la ventana, no un caso aislado.
Medido directamente sobre las 12 anclas con chequeo activo, simulando un corrimiento de
±1 a ±20 líneas sobre la línea real citada (40 posiciones por ancla, usando
`_semantic_check` real, no una reimplementación):

```
$ python3 - <<'EOF'  # (mismo import que arriba, omitido por brevedad)
offsets = list(range(-20, 0)) + list(range(1, 21))  # 40
overall_pass = overall_total = 0
per_anchor = []
for doc, line_no, resolved, symbol in anchors_with_symbol:  # las 12 de F-02
    total_lines = len((root / resolved).read_text(errors="replace").splitlines())
    p = v = 0
    for off in offsets:
        shifted = line_no + off
        if not (1 <= shifted <= total_lines):
            continue
        v += 1
        ok, _ = ca._semantic_check(root, resolved, shifted, symbol)
        p += ok
    overall_pass += p; overall_total += v
    per_anchor.append((doc, line_no, symbol, p, v))
print(overall_pass, overall_total)
EOF
17 480
```

17 de 480 posiciones corridas (≈3.5%) — cifra que se reportó como "siguen pasando por
coincidencia textual" en la primera versión de este repair.

**Corrección post-delta-review (F-05) — esa cifra (17/480) tenía un bug de medición, no
solo una discrepancia de metodología con el reviewer.** El script de arriba usa
`line_no = r["line"]`, pero esa clave (`check_anchors.py:173`, dentro de `_build_entry`) es
**la fila del ancla dentro del `.md`**, no la línea citada en el archivo destino — esa
existe internamente como `target_start` (`check_anchors.py:178`) pero **nunca se guarda**
en el dict que `_scan_doc` devuelve. El resultado: la simulación de arriba corrió los
corrimientos de ±1..±20 alrededor de, por ejemplo, la **fila 26 de `consola.md`** (donde
vive el ancla en el Markdown) en vez de la **línea 3252 de `set_agents_app.py`** (la línea
que esa ancla realmente cita) — midiendo drift sobre una zona de archivo sin relación con
`main()`. Corregido extrayendo la línea real desde `r["raw"]` (regex `` :(\d+)`$ `` sobre
el texto entre backticks; seguro porque toda entrada con `symbol` activo es de línea única
por construcción — `_build_entry` nunca corre el chequeo semántico sobre un rango). Script
corregido, corrida real ahora mismo:

```
$ python3 - <<'EOF'
import sys; sys.path.insert(0, "ai/scripts")
import re
from pathlib import Path
from feature_state_lib import check_anchors as ca
from feature_state_lib.render_modules import load_modules_toml, MODULES_TOML

root = Path(".")
modules_dir = root / "docs" / "modules"
modules = load_modules_toml(modules_dir / MODULES_TOML)

TARGET_LINE_RE = re.compile(r":(\d+)`$")  # F-05 fix: parse the real target line out of
# the raw anchor text instead of using r["line"] (the .md doc row -- see note above)

anchors_with_symbol = []
for slug in sorted(modules):
    doc_path = modules_dir / f"{slug}.md"
    if not doc_path.is_file():
        continue
    file_index = ca._expand_module_files(root, modules[slug]["paths"])
    for r in ca._scan_doc(root, doc_path, file_index, f"docs/modules/{slug}.md"):
        if "symbol" in r and r["ok"]:
            m = TARGET_LINE_RE.search(r["raw"])
            target_line = int(m.group(1))
            anchors_with_symbol.append((r["doc"], target_line, r["resolved"], r["symbol"]))

offsets = list(range(-20, 0)) + list(range(1, 21))  # 40
overall_pass = overall_total = 0
rows = []
for doc, line_no, resolved, symbol in anchors_with_symbol:
    total_lines = len((root / resolved).read_text(errors="replace").splitlines())
    p = v = 0
    for off in offsets:
        shifted = line_no + off
        if not (1 <= shifted <= total_lines):
            continue
        v += 1
        ok, _ = ca._semantic_check(root, resolved, shifted, symbol)
        p += ok
    overall_pass += p; overall_total += v
    rows.append((doc, line_no, symbol, p, v))
print(f"{overall_pass}/{overall_total} = {100*overall_pass/overall_total:.3f}%")
for doc, line_no, symbol, p, v in rows:
    print(doc.split("/")[-1], line_no, symbol, f"{p}/{v}", f"{100*p/v:.1f}%")
EOF
75/479 = 15.658%
consola.md 3252 main 10/40 25.0%
consola.md 1089 cmd_status 9/40 22.5%
generacion-arboles.md 716 main 7/39 17.9%
generacion-arboles.md 55 load_roles 6/40 15.0%
generacion-arboles.md 129 oc_permissions 4/40 10.0%
generacion-arboles.md 376 generate_pi_prompts 4/40 10.0%
generacion-arboles.md 657 validate_pi_target 4/40 10.0%
generacion-arboles.md 678 validate 10/40 25.0%
narracion-notas.md 51 merge_note 9/40 22.5%
narracion-notas.md 67 write_note 4/40 10.0%
narracion-notas.md 37 notes_root 4/40 10.0%
narracion-notas.md 70 render_status 4/40 10.0%
```

**Cifra correcta: 75 de 479 posiciones corridas (≈15.7%) siguen pasando por coincidencia
textual — casi cinco veces la cifra anterior (17/480, 3.5%).** No hay ninguna ancla por
debajo de 4/40 (10%); el máximo es 10/40 (25%), en `main`@consola.md:3252 y
`validate`@generacion-arboles.md:678 — **una de cada cuatro** posiciones corridas pasa en
la ancla peor cubierta. Esto **no** es una propiedad concentrada en un puñado de
identificadores cortos: las 12 anclas medidas están todas en el rango 10%-25%, ninguna en
0%. La cifra corregida (75/479, 15.7%) reproduce casi exacto el número que citó el reviewer
original ("entre 4 y 10 de las 40 posiciones, 10%-25%") — confirma que no era una diferencia
de metodología de simulación (como asumió la nota de honestidad de la versión anterior de
este documento), era este bug. Caracterización correcta: el margen de falso negativo de la
ventana ±2 **no es bajo** — es de orden 1-en-4 en el peor caso y ~1-en-6 en agregado. Ver
ADR-0040 sección 5 para el mismo dato junto a la decisión de diseño, y
`docs/specs/020-honest-dashboard/evidence/P2-repair-2.md` para el repair de F-05 completo.

## Mordida por test (rojo confirmado → revertido → prueba pegada)

Igual que P1: por invariante real, no assertion por assertion (6 mutaciones cubren los 6
invariantes de diseño reales del módulo, no las 25 aserciones una por una). Cada mutación
aplicada con un script Python sobre el archivo real, corrida en rojo, después restaurada
desde una copia de respaldo (`cp`, nunca `git checkout`) y reverificada en verde.

```
# Mutación 1: _semantic_check siempre devuelve (True, "") -- neutraliza AC-08
$ python3 -m unittest tests.test_check_anchors.GrammarAndResolutionTests.test_ac11_moved_symbol_is_reported_broken -v
FAIL: AssertionError: True is not false
# revertido (cp desde backup) -> OK

# Mutación 2: _resolve_basename ignora 0/ambigüedad, resuelve lo primero que encuentra -- neutraliza SC-01
$ python3 -m unittest tests.test_check_anchors.GrammarAndResolutionTests.test_zero_matches_inside_module_paths_is_broken_even_if_the_file_exists_elsewhere tests.test_check_anchors.GrammarAndResolutionTests.test_ambiguous_basename_inside_module_paths_is_broken -v
FAIL (las 2)
# revertido -> OK

# Mutación 3: no resetea last_file en un bullet nuevo -- neutraliza el límite de ítem/párrafo (SC-02)
$ python3 -m unittest tests.test_check_anchors.GrammarAndResolutionTests.test_new_list_item_resets_context_even_after_a_prior_item_named_a_file -v
FAIL: AssertionError: True is not false
# revertido -> OK

# Mutación 4: aplica la verificación semántica también a rangos -- neutraliza la exclusión de AC-08
$ python3 -m unittest tests.test_check_anchors.GrammarAndResolutionTests.test_range_anchor_in_bounds_passes_even_with_a_wrong_adjacent_symbol -v
FAIL: AssertionError: False is not true : [...'reason': "symbol 'beta' not found near src/demo/foo.py:4 (checked lines 2-6)"]
# revertido -> OK

# Mutación 5: FILE_RE_PART sin extensión obligatoria -- reabre los falsos positivos de AC-06/SC-02
$ python3 -m unittest tests.test_check_anchors.GrammarAndResolutionTests.test_false_positives_produce_zero_anchors_and_never_appear_broken -v
FAIL: AssertionError: False is not true : [...'localhost'... '12'... 'x'...]
# revertido -> OK

# Mutación 6: quita el try/except de _warn_check_anchors_never_raises -- neutraliza AC-09
$ python3 -m unittest tests.test_check_anchors.SyncNotesNeverRaisesTests -v
ERROR: RuntimeError: boom (se propaga, sync-notes NO completa)
# revertido -> OK
```

Tras cada revert: `diff -q` contra la copia de respaldo, sin diferencias, y
`python3 -m unittest tests.test_check_anchors` completo en verde (25/25) antes de seguir.

## Gates

`./build.sh` (regenera los 4 árboles de `Global/` desde `ai/scripts/`) + copia manual a
`PROYECTO/ai/scripts/feature_state_lib/` (sin generador propio, ADR-0040 sección
"Consecuencias") + `./build.sh --check`:

```
$ ./build.sh
CHECK_PASS: generated and validated profile go-zen
Generated tracked artifacts for go-zen.

$ ./build.sh --check
CHECK_PASS: generated and validated profile go-zen
SELF_SCAFFOLD_SYNC_OK files=2
```

`md5sum` de los 5 espejos (`ai/scripts/feature_state_lib/`, `Global/claude-code/hooks/
feature_state_lib/`, `Global/opencode/hooks/feature_state_lib/`, `Global/codex/hooks/
feature_state_lib/`, `PROYECTO/ai/scripts/feature_state_lib/`) — 17 archivos `.py` cada
uno (sin `__pycache__`), comparados por (basename, hash), verificado tras las 6 mordidas
y su revert:

```
$ for dir in ai/scripts/feature_state_lib Global/claude-code/hooks/feature_state_lib \
    Global/opencode/hooks/feature_state_lib Global/codex/hooks/feature_state_lib \
    PROYECTO/ai/scripts/feature_state_lib; do
    find "$dir" -name "*.py" -not -path "*__pycache__*" -printf "%f\n" | sort \
      | xargs -I{} md5sum "$dir/{}" | awk '{print $1, $2}' | sed "s#$dir/##"
  done | sort -u | wc -l
17
```

17 pares (archivo, hash) distintos, cada uno presente exactamente 5 veces (uno por árbol)
— confirmado con `sort | uniq -c` (cada línea aparece con count 5) — los 5 espejos son
byte-idénticos. Cero hunks perdidos (el episodio de P1 no se repitió).

Suite completa, literal:

```
$ python3 -m unittest discover -s tests
...
Ran 968 tests in 416.756s

OK (skipped=3)
```

968 = 943 (base declarada en el contrato) + 25 tests nuevos de
`tests/test_check_anchors.py`. Cero failures, cero errors, 3 skips (igual que la base) —
sube, nunca baja.

`./ai/scripts/verify.sh` (incluye `./build.sh --check`, la suite completa otra vez,
`py_compile`, `git diff --check`, portabilidad de `Global/`, `check-canonical-paths.py`,
`check-feature-state.py`), literal:

```
$ ./ai/scripts/verify.sh
CHECK_PASS: generated and validated profile go-zen
SELF_SCAFFOLD_SYNC_OK files=2
...
Ran 968 tests in 421.361s

OK (skipped=3)
...
GLOBAL_PORTABILITY_OK
CANONICAL_PATHS_OK
FEATURE_STATE_OK
VERIFY_PASS
```

Segunda corrida de la suite (adentro de `verify.sh`, entorno real de la máquina, sin
mocks de credenciales): mismos 968/OK/skipped=3 — un test que dependía de
`route-decide` decidible en esta máquina cambió de "ok" (corrida standalone) a "skipped"
(`NO_ELIGIBLE_ROUTE`, condición de la máquina, no del paquete) sin afectar el total
(igual 3 skips netos). Cero failures, cero errors en las dos corridas.

`git diff --check` final (post-`verify.sh`) y `check-anchors` final, ambos re-verificados
después de que terminó `verify.sh` (por si algún subproceso de la suite tocara algo):

```
$ git diff --check; echo "rc=$?"
rc=0
$ python3 ai/scripts/feature-state.py check-anchors >/dev/null 2>&1; echo "rc=$?"
rc=0
```

Los 5 espejos re-verificados por última vez (mismo método de `md5sum` por (basename,
hash) de la sección Gates): **17** pares distintos, cada uno 5 veces — sin drift tras la
corrida completa de `verify.sh`.

## Assumptions / known risks

- El umbral semántico de AC-08 (ventana ±2 líneas, comparación de texto con
  `\bidentificador\b`) puede dar **falso negativo** cuando el símbolo aparece
  mencionado en prosa cerca de la línea citada (caso real documentado arriba,
  `generate.py:669`→`validate`). Es una limitación aceptada del diseño acotado, no un
  bug — corregida por conocimiento externo (grep directo) en AC-10, no por el checker.
- La resolución acotada al módulo (SC-01) hace **irresoluble por diseño** cualquier cita
  entre módulos futura, no solo las dos de hoy. Si un doc nuevo cita un archivo de otro
  módulo con línea, `check-anchors` la va a reportar rota — es el comportamiento
  correcto (falla cerrado ante ambigüedad potencial de basename), pero un autor humano
  que no conozca la regla puede sorprenderse. Documentado en el docstring del módulo, en
  el ADR y en esta evidencia.
- `check-anchors` no es gate — un ancla nueva rota en un futuro paquete no bloquea nada
  hasta que alguien corra el comando a mano o lea el `ANCHORS_WARN` de `sync-notes`. Es
  el no-goal explícito de la spec, no un descuido de este paquete.
- No se tocó el schema de `docs/modules/` ni la partición de ADR-0036: las correcciones
  de AC-10 editaron solo prosa humana (debajo de `<!-- /notas:auto -->`), nunca el
  bloque `<!-- notas:auto -->` ni `modules.toml`.
- `render_modules.py` y `cli_modules.py` seguían sin trackear en git desde 019/P3 (no
  creados por este paquete); `check_anchors.py` se suma al mismo estado untracked del
  árbol — no es un problema de este paquete, es el estado real del repo al momento de
  arrancar (confirmado con `git status` al inicio).

## Cierre

`status: implemented`. Listo para `PACKAGE_GATES`/review independiente. No se tocaron
los blockers de `002`/`011`, el schema de `docs/modules/`, ni nada de P1 (ya aceptado)
más allá de corregir el drift de líneas que P1 introdujo en `model.py` como efecto
colateral de agregar el predicado compartido (AC-10, `estado.md:35-36`).
