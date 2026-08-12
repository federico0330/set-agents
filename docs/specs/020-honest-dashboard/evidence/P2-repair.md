# P2-anclas-verificables — evidencia del repair

Feature: `020-honest-dashboard`. Paquete: `P2-anclas-verificables`. Ciclo de repair único
(review independiente → `repair_required`, 4 findings, `docs/adr/0023-*.md`: `candidate_identity`
nunca se congeló para este paquete — `repair_ceiling` es `None` en el estado, así que el
techo numérico no aplica, pero el diff se mantuvo chico de todos modos: 4 archivos tocados,
~180 líneas netas entre código+test+documentación).

Confirmado por el review antes de este repair (no se re-litiga): las 3 citas cruzadas
convertidas a prosa en AC-10 son diseño legítimo (SC-01 las hace irresolubles a propósito),
y no hay tests decorativos entre los 25 originales.

## Tabla finding → cambio → verificación

| Finding | Severidad | Archivo:línea (después del repair) | Cambio | Verificación |
|---|---|---|---|---|
| F-01 | medium | `ai/scripts/feature_state_lib/check_anchors.py:118-132` (`_resolve_basename`) | Hint estático agregado al mensaje de "no file named": nombra la posibilidad de cita cruzada de módulo y remite a ADR-0040 §5, sin búsqueda global (SC-01 intacto) | `tests/test_check_anchors.py::GrammarAndResolutionTests::test_zero_matches_reason_names_the_cross_module_citation_possibility` (nuevo) + mordida 1 abajo |
| F-02 | medium | `ai/scripts/feature_state_lib/check_anchors.py:136-147` (`_adjacent_symbol`, docstring) + `docs/adr/0040-*.md` sección 5 + `docs/specs/020-honest-dashboard/evidence/P2-implementer.md` | Docstring nuevo con el ejemplo concreto (`` `foo.py:8` es `alpha()` `` con línea 8 real = `beta`) + fracción real (12/38, 32%) declarada en ADR-0040 §5 y en la evidencia del implementer, con conteo por forma (10/18 completas, 2/20 abreviadas) | `tests/test_check_anchors.py::GrammarAndResolutionTests::test_prose_connector_lets_a_genuinely_false_claim_about_a_real_symbol_pass` (nuevo) + mordida 2 abajo + medición real pegada más abajo |
| F-03 | low | `docs/adr/0040-*.md` sección 5 + `docs/specs/020-honest-dashboard/evidence/P2-implementer.md` | Orden de magnitud medido del falso negativo estructural de la ventana ±2: ~~17/480~~ **75/479 (≈15.7%)** posiciones corridas (±1..±20 sobre las 12 anclas con chequeo activo) pasan por coincidencia — cifra corregida por el delta-review (F-05), ver `P2-repair-2.md`; la original tenía un bug de medición, no un caso aislado ni una diferencia de metodología | Medición real pegada más abajo, con la nota de corrección de F-05 (sin cambio de código: es documental, SC-03 ya acotó AC-08 a propósito) |
| F-04 | low | — | **No tocado**, fuera de alcance de P2 (confirmado por el orquestador antes de este repair) | N/A |

## F-01 — el mensaje no distingue "no existe" de "cita cruzada"

**Cambio** (`ai/scripts/feature_state_lib/check_anchors.py:118-132`, dentro de
`_resolve_basename`):

```python
    if not matches:
        # F-01 (P2 repair, static hint -- no global search, that would violate SC-01):
        # this reason fires for two very different causes that look identical from here
        # -- (a) the file genuinely does not exist anywhere, and (b) the file exists but
        # is owned by a DIFFERENT module, i.e. a cross-module citation, which SC-01 makes
        # unresolvable by design (see ADR-0040 sect. 5 and the module docstring above).
        # We cannot tell which one it is without a global search, so the message names
        # both possibilities instead of guessing.
        return None, (
            f"no file named {base!r} inside this module's declared paths (modules.toml) "
            "-- if this file exists but belongs to a DIFFERENT module, this is a "
            "cross-module citation, unresolvable by design (SC-01, see ADR-0040 sect. 5): "
            "drop the line number and name the owning module in prose instead, as AC-10 "
            "did for the two real cases in today's docs"
        )
```

Es un hint **estático**: no busca el archivo en otros módulos (eso violaría SC-01, que
exige que la resolución sea determinística y acotada al módulo que se chequea). Solo
nombra la posibilidad y apunta al mismo mecanismo que AC-10 ya usó para las dos citas
cruzadas reales de hoy.

**Test nuevo** (`tests/test_check_anchors.py:204-224`,
`test_zero_matches_reason_names_the_cross_module_citation_possibility`): reusa el mismo
fixture de `test_zero_matches_inside_module_paths_is_broken_even_if_the_file_exists_elsewhere`
(un `bar.py` que existe de verdad, pero en el módulo `other`, no en `demo`) y verifica que
la razón contenga `"cross-module"` y `"ADR-0040"`.

**Mordida 1** (rojo confirmado → revertido → verde), literal:

```
# Mutación: revertir el hint de F-01 al mensaje original de una línea
$ python3 -m unittest tests.test_check_anchors.GrammarAndResolutionTests.test_zero_matches_reason_names_the_cross_module_citation_possibility -v
FAIL: AssertionError: 'cross-module' not found in "no file named 'bar.py' inside this
module's declared paths (modules.toml)"
# revertido (cp desde backup, nunca git checkout) -> diff -q backup real: sin diferencias
$ python3 -m unittest tests.test_check_anchors.GrammarAndResolutionTests.test_zero_matches_reason_names_the_cross_module_citation_possibility -v
ok
```

## F-02 — cobertura semántica real: 12 de 38 (32%), no "38 anclas cubiertas"

**Cambio de código** (`ai/scripts/feature_state_lib/check_anchors.py:136-150`, docstring
nuevo de `_adjacent_symbol`, ningún cambio de comportamiento):

```python
def _adjacent_symbol(line: str, pos: int) -> str | None:
    """F-02 (P2 repair): "adjacent" means ONLY horizontal whitespace between the anchor's
    closing backtick and this symbol's opening backtick -- a connector word, a verb, or
    even a comma right there silently turns AC-08's semantic check off (resolution+range
    checks still run, but the identifier is never compared). Concrete, measured case: in
    "`foo.py:8` es `alpha()`", `pos` lands right after `:8` `'s closing backtick, on the
    space before "es"; `_SYMBOL_RE` needs a backtick immediately after that (only) space,
    finds the letter "e" instead, and never matches -- so this returns None and the claim
    passes (`ok=True`) even when line 8 is genuinely `beta`, not `alpha`. Measured on this
    repo's own docs/modules/*.md (P2 repair evidence, ADR-0040 sect. 5): only 12 of 38
    anchors (32%) have an active semantic check today; the other 26 read fine to a human
    but are never compared against the target line's real content.
    """
    m = _SYMBOL_RE.match(line, pos)
    return m.group(1) if m else None
```

**Cambio documental**: ADR-0040 sección 5 ganó un párrafo nuevo ("Cobertura real, medida,
no solo posible") con la fracción y el desglose por forma; `P2-implementer.md` ganó una
sección "Corrección post-review (repair F-02)" con el mismo dato y el comando real que lo
midió (ver abajo).

**Medición real, corrida ahora mismo, contra los 5 módulos reales** (no de memoria — ADR-0026):

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
print("total anchors:", total)
print("with active semantic check:", with_symbol)
print(by_form)
EOF
total anchors: 38
with active semantic check: 12
{'complete': {'total': 18, 'symbol': 10}, 'abbreviated': {'total': 20, 'symbol': 2}}
```

12/38 = 32%. Desglose: 10 de 18 completas (56%), 2 de 20 abreviadas (10%) — la forma
abreviada casi nunca trae un símbolo entre backticks pegado al `` `:N` ``.

**Test nuevo** (`tests/test_check_anchors.py:173-180`,
`test_prose_connector_lets_a_genuinely_false_claim_about_a_real_symbol_pass`): el ejemplo
exacto del reviewer — `` `foo.py:8` es `alpha()` `` con la línea 8 real de `beta` — pasa
(`ok=True`) porque el conector "es" apaga la adyacencia.

**Mordida 2** (rojo confirmado → revertido → verde), literal:

```
# Mutación: ensanchar _SYMBOL_RE para que también trague "es "/"define " antes del backtick
$ python3 -m unittest tests.test_check_anchors.GrammarAndResolutionTests.test_prose_connector_lets_a_genuinely_false_claim_about_a_real_symbol_pass -v
FAIL: AssertionError: False is not true : [{'doc': 'docs/modules/demo.md', 'line': 1,
'raw': '`foo.py:8`', 'form': 'complete', 'resolved': 'src/demo/foo.py', 'symbol': 'alpha',
'ok': False, 'reason': "symbol 'alpha' not found near src/demo/foo.py:8 (checked lines 6-9)"}]
# revertido (cp desde backup) -> diff -q backup real: sin diferencias
$ python3 -m unittest tests.test_check_anchors.GrammarAndResolutionTests.test_prose_connector_lets_a_genuinely_false_claim_about_a_real_symbol_pass -v
ok
```

(La mutación de la mordida 2 demuestra el punto al revés: si `_adjacent_symbol` SÍ mirara
más allá del espacio en blanco, el chequeo semántico correría y detectaría correctamente
que la línea 8 real es `beta`, no `alpha` — confirma que la exclusión de AC-08, y no un
bug, es la causa de que hoy pase.)

## F-03 — la ventana ±2 tiene falsos negativos estructurales, magnitud medida

Sin cambio de código (SC-03 ya acotó AC-08 a propósito; no es un bug). Cambio documental
en ADR-0040 §5 ("Magnitud de la ventana ±2, medida") y en `P2-implementer.md`.

**Medición real**: sobre las 12 anclas con chequeo semántico activo (las de F-02), se
simuló un corrimiento de ±1 a ±20 líneas alrededor de la línea real citada (40 posiciones
por ancla, usando `_semantic_check` real del módulo, no una reimplementación), contando
cuántas posiciones corridas siguen "pasando" (falso negativo: la línea está mal pero el
símbolo aparece igual en la ventana por coincidencia):

```
$ python3 - <<'EOF'
import sys; sys.path.insert(0, "ai/scripts")
from pathlib import Path
from feature_state_lib import check_anchors as ca
from feature_state_lib.render_modules import load_modules_toml, MODULES_TOML

root = Path(".")
modules_dir = root / "docs" / "modules"
modules = load_modules_toml(modules_dir / MODULES_TOML)

anchors_with_symbol = []
for slug in sorted(modules):
    doc_path = modules_dir / f"{slug}.md"
    if not doc_path.is_file():
        continue
    file_index = ca._expand_module_files(root, modules[slug]["paths"])
    for r in ca._scan_doc(root, doc_path, file_index, f"docs/modules/{slug}.md"):
        if "symbol" in r and r["ok"]:
            anchors_with_symbol.append((r["doc"], r["line"], r["resolved"], r["symbol"]))

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

print(f"{overall_pass}/{overall_total}")
for r in rows:
    print(r)
EOF
17/480
('docs/modules/consola.md', 26, 'main', 0, 40)
('docs/modules/consola.md', 38, 'cmd_status', 0, 40)
('docs/modules/generacion-arboles.md', 29, 'main', 0, 40)
('docs/modules/generacion-arboles.md', 35, 'load_roles', 3, 40)
('docs/modules/generacion-arboles.md', 37, 'oc_permissions', 0, 40)
('docs/modules/generacion-arboles.md', 40, 'generate_pi_prompts', 0, 40)
('docs/modules/generacion-arboles.md', 42, 'validate_pi_target', 0, 40)
('docs/modules/generacion-arboles.md', 42, 'validate', 0, 40)
('docs/modules/narracion-notas.md', 41, 'merge_note', 5, 40)
('docs/modules/narracion-notas.md', 42, 'write_note', 4, 40)
('docs/modules/narracion-notas.md', 45, 'notes_root', 5, 40)
('docs/modules/narracion-notas.md', 47, 'render_status', 0, 40)
```

17 de 480 posiciones corridas (≈3.5%) — así se reportó en la versión original de este
repair, con la lectura "pasan por coincidencia, concentradas en 4 de las 12 anclas".

**Corrección post-delta-review (F-05, 2026-08-12) — esa medición tenía un bug real, no una
diferencia de metodología con el reviewer.** Mirá la línea `anchors_with_symbol.append((r["doc"],
r["line"], r["resolved"], r["symbol"]))` del script de arriba, y las líneas del `print` que
le siguen: `26, 38, 29, 35, 37, 40, 42, 42, 41, 42, 45, 47` — todas de una cifra chica, en el
rango donde viven los encabezados de sección de `docs/modules/*.md`, no en el rango donde
viven `main()`/`cmd_status()`/etc. en `set_agents_app.py`/`generate.py` (líneas en los
cientos o miles). Eso es la pista: `r["line"]` (asignada en `check_anchors.py:173`, dentro
de `_build_entry`) es **la fila del ancla dentro del `.md`**, no la línea citada en el
archivo destino — esa existe internamente como `target_start` (`check_anchors.py:178`) pero
**nunca se guarda** en el dict que `_scan_doc` devuelve. El script de arriba centró la
ventana de ±20 alrededor de, por ejemplo, la **fila 26 de `consola.md`** (donde vive el
ancla en el Markdown) en vez de la **línea 3252 de `set_agents_app.py`** (la línea que esa
ancla realmente cita) — midió drift sobre una zona de archivo sin relación con `main()`.

Corregido extrayendo la línea real desde `r["raw"]` (regex `` :(\d+)`$ `` sobre el texto
entre backticks; seguro porque toda entrada con `symbol` activo es de línea única por
construcción — `_build_entry` nunca corre el chequeo semántico sobre un rango). Script
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

TARGET_LINE_RE = re.compile(r":(\d+)`$")  # F-05 fix: parse the real target line out of the
# raw anchor text instead of using r["line"] (the .md doc row -- see note above)

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

**Cifra correcta: 75 de 479 posiciones corridas (≈15.7%) pasan por coincidencia** — casi
cinco veces la cifra anterior. Ninguna de las 12 anclas baja de 4/40 (10%); el máximo es
10/40 (25%), en `main` y `validate`. No está concentrado en 4 anclas de identificador corto
como decía la versión anterior: **las 12 están todas en el rango 10%-25%**, ninguna en 0%.

La "nota de honestidad" de la versión anterior de este documento decía que la cifra propia
(17/480) "no reproduce el número exacto que citó el reviewer ('entre 4 y 10 de las 40
posiciones'), posiblemente por una metodología de simulación distinta". Esa conjetura era
incorrecta: la cifra corregida (75/479, un mínimo de 4/40 y un máximo de 10/40 por ancla)
**sí reproduce casi exacto** el rango que citó el reviewer — no había dos metodologías, había
una medición con un bug y otra sin él. Caracterización correcta, para reemplazar "bajo pero
no despreciable" (ADR-0040 §5 y en otros lugares de esta evidencia que citaban la cifra
vieja): el margen de falso negativo de la ventana ±2 **no es bajo** — en el peor caso es
**una de cada cuatro** posiciones corridas, y en agregado ronda **una de cada seis**.

## F-04 — no tocado

Confirmado como fuera de alcance de P2 y ya re-verificado por el orquestador antes de este
repair (el árbol de `Global/*` quedó estable en 6047 líneas y `CHECK_PASS` tras
`./build.sh`). Este repair no tocó `tests/test_harness.py` ni `build.sh`.

## Archivos tocados por este repair

- `ai/scripts/feature_state_lib/check_anchors.py` (264 → 288 líneas: hint de F-01 en
  `_resolve_basename`, docstring de F-02 en `_adjacent_symbol`; sin cambios de
  comportamiento, confirmado por `rc=0` de `check-anchors` antes y después, idéntico)
- Sus 4 espejos (`Global/claude-code`, `Global/opencode`, `Global/codex` vía `./build.sh`;
  `PROYECTO/ai/scripts/feature_state_lib/` copiado a mano, sin generador propio, igual que
  hizo el implementer) — los 5 verificados byte-idénticos por `md5sum` abajo.
- `tests/test_check_anchors.py` (369 → 404 líneas: 2 tests nuevos,
  `test_zero_matches_reason_names_the_cross_module_citation_possibility` y
  `test_prose_connector_lets_a_genuinely_false_claim_about_a_real_symbol_pass`)
- `docs/adr/0040-honest-digest-shared-liveness-predicate.md` (sección 5 ampliada con la
  cobertura real medida de F-02 y la magnitud medida de F-03; una línea agregada en
  "Consecuencias" para no dejar el `rc=0` original sin matizar)
- `docs/specs/020-honest-dashboard/evidence/P2-implementer.md` (dos secciones de
  corrección post-review agregadas — append, no se borró ni reescribió lo ya escrito — más
  la corrección de 4 referencias `archivo:línea` que habían quedado corridas por los
  propios cambios de este repair, la misma clase de defecto que P2 existe para prevenir)

No se tocó `docs/modules/*.md`, `modules.toml`, ni ningún archivo de P1, 019, o
`Global/_canonical`.

## Gates

```
$ ./build.sh
CHECK_PASS: generated and validated profile go-zen
Generated tracked artifacts for go-zen.

$ cp ai/scripts/feature_state_lib/check_anchors.py PROYECTO/ai/scripts/feature_state_lib/check_anchors.py
$ ./build.sh --check
CHECK_PASS: generated and validated profile go-zen
SELF_SCAFFOLD_SYNC_OK files=2
```

`md5sum` de los 5 espejos (mismo método que P1/P2-implementer: por (basename, hash), 17
archivos `.py` cada uno, sin `__pycache__`), verificado dos veces — antes y después de la
suite completa y de `verify.sh` (por si algún subproceso tocara algo):

```
$ for dir in ai/scripts/feature_state_lib Global/claude-code/hooks/feature_state_lib \
    Global/opencode/hooks/feature_state_lib Global/codex/hooks/feature_state_lib \
    PROYECTO/ai/scripts/feature_state_lib; do
    find "$dir" -name "*.py" -not -path "*__pycache__*" -printf "%f\n" | sort \
      | xargs -I{} md5sum "$dir/{}" | awk '{print $1, $2}' | sed "s#$dir/##"
  done | sort -u | wc -l
17
$ ... | sort | uniq -c | awk '{print $1}' | sort -u
5
```

17 pares (archivo, hash) distintos, cada uno presente exactamente 5 veces — los 5 espejos
son byte-idénticos, antes y después de la suite completa.

Suite completa, literal (corrida real, redirigida a archivo para no perder el resumen final
detrás del volcado de stdout bufferizado que algunos tests imprimen — un error de esta
misma sesión: la primera corrida usó `| tail -20` y se comió el resumen, quedó descartada y
no se cita):

```
$ python3 -m unittest discover -s tests > suite_run1.log 2>&1
$ grep -n "^Ran \|^OK\|^FAILED\|^ERROR:\|^FAIL:" suite_run1.log
Ran 970 tests in 419.445s
OK (skipped=3)
```

970 = 968 (base declarada por el implementer: 943 + 25 de `test_check_anchors.py`) + 2
tests nuevos de este repair. Cero failures, cero errors, 3 skips (igual que la base) — sube,
nunca baja.

`./ai/scripts/verify.sh` (incluye `./build.sh --check`, la suite completa otra vez en modo
verbose, `py_compile`, `git diff --check`, portabilidad de `Global/`,
`check-canonical-paths.py`, `check-feature-state.py`), literal:

```
$ ./ai/scripts/verify.sh > verify_run1.log 2>&1
$ grep -n "CHECK_PASS\|SELF_SCAFFOLD_SYNC_OK\|^Ran \|^OK\|GLOBAL_PORTABILITY_OK\|CANONICAL_PATHS_OK\|FEATURE_STATE_OK\|VERIFY_PASS" verify_run1.log
CHECK_PASS: generated and validated profile go-zen
SELF_SCAFFOLD_SYNC_OK files=2
Ran 970 tests in 429.187s
OK (skipped=3)
GLOBAL_PORTABILITY_OK
CANONICAL_PATHS_OK
FEATURE_STATE_OK
VERIFY_PASS
```

Segunda corrida de la suite (adentro de `verify.sh`): mismos 970/OK/skipped=3. Cero
failures, cero errors en las dos corridas completas.

`git diff --check` y `check-anchors` finales, re-verificados después de que terminó
`verify.sh`:

```
$ git diff --check; echo "rc=$?"
rc=0
$ python3 ai/scripts/feature-state.py check-anchors >/dev/null 2>&1; echo "rc=$?"
rc=0
$ python3 ai/scripts/feature-state.py check-anchors
ANCHORS_OK checked=5 anchors=38
{"anchor_count": 38, "broken": [], "checked_docs": ["consola.md", "estado.md",
"generacion-arboles.md", "narracion-notas.md", "routing.md"],
"form_counts": {"abbreviated": 20, "complete": 18}, "ok": true}
```

`anchor_count=38`, `form_counts` idénticos a antes del repair (F-01/F-02 solo cambiaron
mensajes/docstrings, nunca la gramática ni la resolución) — confirma que el repair no
introdujo ni removió ninguna ancla real.

## Suite de tests del módulo, después del repair

```
$ python3 -m unittest tests.test_check_anchors -v
... (27 tests, todos ok, incluyendo los 2 nuevos)
Ran 27 tests in 0.548s
OK
```

## Cierre

Los 3 findings de código/doc quedaron reparados: F-01 con hint estático + test, F-02 con
docstring + fracción real declarada en ADR y evidencia + test que fija el ejemplo exacto
del review, F-03 con la magnitud medida documentada donde vive la decisión de diseño (ADR)
y en la evidencia. F-04 no se tocó, por instrucción explícita — está fuera de alcance de
P2 y ya fue re-verificado por el orquestador antes de este repair.

Ningún test existente se relajó, saltó, ni borró. La base se mantuvo y subió: 968 → 970.
Ningún cambio de comportamiento observable en `check_anchors()` — mismo `rc=0`, mismo
`anchor_count=38`, mismos `form_counts` antes y después; los tres cambios de código/doc
son mensajes, docstrings y documentación, no lógica.

**Addendum (F-05, repair posterior, ver `P2-repair-2.md`):** la medición de F-03 pegada en
este documento tenía un bug real (usaba la fila del ancla en el `.md` en vez de la línea
citada en el archivo destino) que subestimaba el hallazgo ~4.5x (17/480 ≈3.5% medido vs.
75/479 ≈15.7% real). Las secciones de arriba (tabla, `## F-03`) quedaron anotadas en el
lugar donde estaba el error, con la cifra corregida a continuación — no se borró la
medición original, para dejar trazabilidad de qué se corrió y qué estaba mal en eso.

`status: repaired`, listo para `DELTA_REVIEW`.
