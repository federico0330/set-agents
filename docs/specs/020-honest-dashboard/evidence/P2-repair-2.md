# P2-anclas-verificables — evidencia del repair 2 (F-05)

Feature: `020-honest-dashboard`. Paquete: `P2-anclas-verificables`. Segundo ciclo de repair,
**un solo finding, puramente documental** (F-05, `medium`, del delta-review). No se tocó
`check_anchors.py`, ningún test de comportamiento, ni `docs/modules/*.md`.

## F-05 — el bug de medición de F-03, reproducido y corregido

**El bug, con evidencia propia (no solo la del finding):** el script de medición de F-03
(`docs/specs/020-honest-dashboard/evidence/P2-repair.md:167-206`, versión anterior a este
repair) construía `anchors_with_symbol` con `r["line"]` como línea del archivo destino:

```python
anchors_with_symbol.append((r["doc"], r["line"], r["resolved"], r["symbol"]))
```

Pero `r["line"]` se asigna en `check_anchors.py:173`, dentro de `_build_entry` — más
precisamente en `_scan_doc` (`check_anchors.py:206-256`), que llama a `_build_entry` pasando
`lineno` (la variable de `enumerate(text.splitlines(), start=1)` sobre el **`.md`**, no sobre
el archivo destino). `_build_entry` sí calcula la línea real citada
(`target_start = int(line_s)`, `check_anchors.py:178`), pero nunca la agrega al dict que
devuelve — el dict solo trae `entry["line"] = lineno` (la fila del ancla en el Markdown).
Confirmado leyendo el código fuente:

```
$ grep -n '"line"\|target_start' ai/scripts/feature_state_lib/check_anchors.py
168: repo_root: Path, doc: str, lineno: int, token: str, form: str,
173:    entry: dict[str, Any] = {"doc": doc, "line": lineno, "raw": f"`{token}`", "form": form}
178:    target_start = int(line_s)
```

`target_start` (línea 178) nunca vuelve a aparecer en el archivo después de esa asignación —
se usa localmente para el chequeo de rango y el chequeo semántico, y se descarta.

**Efecto medible del bug**, corriendo el script viejo tal cual (la salida real ya pegada en
`P2-repair.md`, reproducida acá para que quede junto a la causa):

```
('docs/modules/consola.md', 26, 'main', 0, 40)
('docs/modules/consola.md', 38, 'cmd_status', 0, 40)
```

`26` y `38` son las filas de esas dos anclas **dentro de `consola.md`** (donde vive la
sección "consola" del doc), no `3252` y `1089` (las líneas reales que esas anclas citan en
`set_agents_app.py`). El script simuló un corrimiento de ±1..±20 alrededor de la fila 26 del
Markdown — una zona sin relación con `main()` — y por eso midió 0/40 en ambas: no es que la
ventana ±2 sea perfecta ahí, es que la simulación completa apuntaba al archivo/zona
equivocados para esas dos filas.

## Script corregido, corrida real ahora mismo

Extrae la línea real desde `r["raw"]` (el texto entre backticks del ancla, p. ej.
`` `set_agents_app.py:2510` `` o `` `:2510` ``) con la regex `` :(\d+)`$ ``. Es segura porque
toda entrada con `"symbol"` en el dict es de línea única por construcción — `_build_entry`
solo corre `_adjacent_symbol`/`_semantic_check` cuando `end_s is None`, es decir, nunca para
un rango (`check_anchors.py:193-201`).

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

# F-05 fix: r["line"] (check_anchors.py:173, _build_entry) is the ANCHOR's row inside the
# .md doc, never the target line inside the destination file -- that value (target_start,
# check_anchors.py:178) is computed but never stored on the returned dict. The only place
# the real target line survives is the raw anchor text itself ("`file.py:N`" or "`:N`"), so
# we parse it from there. Every entry that has "symbol" is single-line by construction
# (_build_entry only runs the symbol check when end_s is None, i.e. never for a range), so
# this regex is safe: exactly one trailing ":<digits>" right before the closing backtick.
TARGET_LINE_RE = re.compile(r":(\d+)`$")

anchors_with_symbol = []
for slug in sorted(modules):
    doc_path = modules_dir / f"{slug}.md"
    if not doc_path.is_file():
        continue
    file_index = ca._expand_module_files(root, modules[slug]["paths"])
    for r in ca._scan_doc(root, doc_path, file_index, f"docs/modules/{slug}.md"):
        if "symbol" in r and r["ok"]:
            m = TARGET_LINE_RE.search(r["raw"])
            assert m, r["raw"]
            target_line = int(m.group(1))  # was: r["line"] (WRONG -- doc row, not this)
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
    pct = 100 * p / v if v else 0.0
    print(f"{doc.split('/')[-1]:24s} {line_no:5d} {symbol:22s} {p:2d}/{v:<3d} {pct:5.1f}%")
EOF
75/479 = 15.658%
consola.md               3252 main                   10/40   25.0%
consola.md               1089 cmd_status              9/40   22.5%
generacion-arboles.md     716 main                    7/39   17.9%
generacion-arboles.md      55 load_roles              6/40   15.0%
generacion-arboles.md     129 oc_permissions          4/40   10.0%
generacion-arboles.md     376 generate_pi_prompts     4/40   10.0%
generacion-arboles.md     657 validate_pi_target      4/40   10.0%
generacion-arboles.md     678 validate               10/40   25.0%
narracion-notas.md         51 merge_note              9/40   22.5%
narracion-notas.md         67 write_note              4/40   10.0%
narracion-notas.md         37 notes_root              4/40   10.0%
narracion-notas.md         70 render_status           4/40   10.0%
```

**75 de 479 posiciones corridas (≈15.7%) pasan por coincidencia** — 479, no 480, porque una
posición (`main`@generacion-arboles.md:716, offset +20 → línea 736) cae fuera de
`generate.py` (735 líneas) y se descarta, igual que la lógica original ya hacía. Ninguna de
las 12 anclas baja de **4/40 (10%)**; el máximo es **10/40 (25%)**, en dos anclas
(`main`@consola.md:3252, `validate`@generacion-arboles.md:678).

Esta cifra **reproduce casi exacto** el rango que citó el reviewer original del review
independiente ("entre 4 y 10 de las 40 posiciones, 10%-25%") — confirmando lo que dice el
finding: no era una diferencia de denominador (posiciones-por-ancla vs. total), era que la
medición del repair anterior apuntaba a la zona de archivo equivocada.

## Los tres archivos actualizados

| Archivo | Qué cambió |
|---|---|
| `docs/adr/0040-honest-digest-shared-liveness-predicate.md` §5 (párrafo "Magnitud de la ventana ±2, medida") | Cifra corregida a 75/479 (≈15.7%), tabla completa de las 12 anclas con línea destino real, mínimo 4/40 (10%) y máximo 10/40 (25%) explícitos, caracterización reescrita ("no es un margen bajo"). Párrafo nuevo "Nota de corrección (F-05...)" con la causa del bug, sin borrar la mención al número viejo (queda nombrado y marcado como corregido). También la línea de "Consecuencias" que citaba el margen de F-03. |
| `docs/specs/020-honest-dashboard/evidence/P2-implementer.md` (~216-260, sección "Corrección post-review (repair F-03)") | El script y la salida viejos (`17 480`) quedan intactos como registro de lo que se corrió entonces; la prosa de análisis que le seguía se reemplazó por una nota "Corrección post-delta-review (F-05)" que explica el bug, pega el script corregido con su salida real, y da la cifra y caracterización correctas. |
| `docs/specs/020-honest-dashboard/evidence/P2-repair.md` (~155-235, sección "F-03") + tabla finding→cambio (línea 19) + "Cierre" | Mismo patrón: script/salida original intactos, nota de corrección con causa + script corregido + salida real + cifra correcta; la "nota de honestidad" original (que atribuía la discrepancia a "una metodología de simulación distinta") queda citada y corregida explícitamente, porque esa conjetura también era incorrecta. Tabla resumen con `~~17/480~~ **75/479**` tachado. Addendum al final del documento apuntando a este repair. |

Ningún archivo se reescribió en silencio: en los tres, el número viejo sigue legible, con una
nota inmediatamente al lado explicando por qué estaba mal y cuál es el correcto — la misma
postura de "recortá y dejá constancia" que el resto de este paquete usa en todos lados.

## Caracterización — por qué "bajo pero no despreciable" no sirve más

La versión anterior de ADR-0040 §5 cerraba con "un margen de falso negativo medido, bajo
pero no despreciable". Con la cifra corregida eso ya no describe el dato: **10%-25% por
ancla, agregado ≈15.7%, sin ninguna ancla por debajo del 10%** no es un margen bajo — es un
peor caso de **una posición corrida de cada cuatro** pasando como si la línea citada fuera
correcta. Reemplazado en los tres documentos por una frase que dice eso directamente (ver
tabla arriba); ADR-0040 §5 y la sección "Consecuencias" quedan con el número explícito en vez
de un adjetivo que lo suavizaba.

## Decisión: no se agrega `target_start` al dict de `_build_entry`

Se evaluó, como sugiere el pedido, si vale la pena que `_build_entry` guarde la línea del
destino (`target_start`, hoy calculada y descartada en `check_anchors.py:178`) en el dict que
devuelve, para que un script de medición futuro no pueda repetir este bug por falta del dato
correcto.

**Decisión: no, en este repair.** Razones:

1. **Está fuera del mandato explícito de este repair.** La instrucción que abre esta tarea
   dice, literalmente, "No toca `check_anchors.py` ni ningún comportamiento" y las
   Restricciones repiten "Solo F-05... `check-anchors` tiene que seguir dando `rc=0`,
   `anchor_count=38` y los mismos `form_counts`". F-05 en sí es "puramente documental". Tocar
   `_build_entry` es tocar el módulo que el propio pedido excluye, incluso si el cambio fuera
   aditivo y no rompiera ningún test existente.
2. **No es aditivo sin efecto observable.** `check_anchors()` no filtra las claves del dict
   antes de devolverlo — `cmd_check_anchors` (`cli_modules.py:130`) llama a `print_json(result)`
   con el `result` completo, y `result["broken"]` son las mismas entradas que produce
   `_build_entry`. Agregar `entry["target_line"] = target_start` cambiaría el JSON que imprime
   el comando real (`check-anchors`) para toda ancla rota que llegó a resolver un archivo antes
   de fallar (p. ej. "línea fuera de rango") — un cambio de esquema de salida, no solo un dato
   interno nuevo. Eso es exactamente la clase de "cambio de comportamiento" que las
   Restricciones prohíben en este ciclo, aun siendo una mejora razonable en otro contexto.
3. **El dato correcto ya quedó disponible donde hace falta.** Este repair documenta el patrón
   de extracción seguro (`` :(\d+)`$ `` sobre `r["raw"]`) en los tres lugares que un futuro
   script de medición leería primero (ADR-0040 §5, ambas evidencias) — el próximo que necesite
   la línea destino real tiene la receta correcta a mano, sin tocar el módulo.

Si en algún momento se decide que vale la pena (por ejemplo, si aparece un tercer consumidor
de esta medición, o si se evalúa convertir `check-anchors` en gate y hace falta reportar la
línea real en el mensaje de error), es un cambio de una línea con un test que fije que
`target_line` == la línea parseada de `raw` — pero es una decisión de código, de otro ciclo,
no de este repair documental.

## Gates

Suite completa, literal (redirigida a archivo, resumen tomado con `grep`, no con `tail`, para
no perderlo detrás de salida bufferizada):

```
$ python3 -m unittest discover -s tests > suite_run1.log 2>&1
$ grep -n "^Ran \|^OK\|^FAILED\|^ERROR:\|^FAIL:" suite_run1.log
Ran 970 tests in 399.687s
OK (skipped=3)
```

970/OK/skipped=3 — idéntico a la base de 970 que dejó el repair anterior (F-01/F-02/F-03/F-04).
No se agregaron ni se borraron tests: F-05 es documental, no toca `tests/`.

`./ai/scripts/verify.sh` (incluye `./build.sh --check`, la suite completa otra vez, `py_compile`,
`git diff --check`, portabilidad de `Global/`, `check-canonical-paths.py`,
`check-feature-state.py`), literal:

```
$ ./ai/scripts/verify.sh > verify_run1.log 2>&1
$ grep -n "CHECK_PASS\|SELF_SCAFFOLD_SYNC_OK\|^Ran \|^OK\|GLOBAL_PORTABILITY_OK\|CANONICAL_PATHS_OK\|FEATURE_STATE_OK\|VERIFY_PASS" verify_run1.log
CHECK_PASS: generated and validated profile go-zen
SELF_SCAFFOLD_SYNC_OK files=2
Ran 970 tests in 409.079s
OK (skipped=3)
GLOBAL_PORTABILITY_OK
CANONICAL_PATHS_OK
FEATURE_STATE_OK
VERIFY_PASS
```

`./build.sh --check` corrido aparte también (no estrictamente necesario: este repair no tocó
`feature_state_lib/`, así que no hay nada que regenerar; se corre igual porque la validación
local lo pide):

```
$ ./build.sh --check
CHECK_PASS: generated and validated profile go-zen
SELF_SCAFFOLD_SYNC_OK files=2
```

`git diff --check` y `check-anchors`, re-verificados después de `verify.sh`, `rc` medido sin
pipear a `tail`:

```
$ git diff --check; echo "rc=$?"
rc=0
$ python3 ai/scripts/feature-state.py check-anchors >/dev/null 2>&1; echo "rc=$?"
rc=0
$ python3 ai/scripts/feature-state.py check-anchors
ANCHORS_OK checked=5 anchors=38
{
  "anchor_count": 38,
  "broken": [],
  "checked_docs": ["consola.md", "estado.md", "generacion-arboles.md", "narracion-notas.md", "routing.md"],
  "form_counts": {"abbreviated": 20, "complete": 18},
  "ok": true
}
```

`anchor_count=38`, `form_counts` idénticos (18 completas, 20 abreviadas) a antes de este
repair — confirma que F-05, siendo documental, no cambió la gramática ni la resolución del
checker. No se corrió `md5sum` de los 5 espejos ni `./build.sh` (modo generate): este repair
no tocó `feature_state_lib/` en ninguno de los 5 árboles, así que no hay drift posible que
verificar ahí.

## Archivos tocados por este repair

- `docs/adr/0040-honest-digest-shared-liveness-predicate.md` (§5, la línea de "Consecuencias"
  sobre el margen de F-03)
- `docs/specs/020-honest-dashboard/evidence/P2-implementer.md` (sección "Corrección
  post-review (repair F-03)")
- `docs/specs/020-honest-dashboard/evidence/P2-repair.md` (sección "F-03", tabla
  finding→cambio, "Cierre")
- `docs/specs/020-honest-dashboard/evidence/P2-repair-2.md` (este archivo, nuevo)

Ningún otro archivo. No se tocó `check_anchors.py` (ni sus 5 espejos), `tests/test_check_anchors.py`,
ni `docs/modules/*.md`.

## Cierre

F-05 reparado: el bug de medición está identificado con `file:línea` real
(`check_anchors.py:173` vs. `:178`), reproducido con evidencia propia, y corregido con un
script que extrae la línea real del ancla en vez de la fila del `.md`. La cifra correcta
(75/479 ≈15.7%, 10%-25% por ancla, mínimo 4/40) reemplaza a la incorrecta (17/480 ≈3.5%) en
los tres lugares pedidos, con la corrección dejada visible y explicada, no en silencio. La
caracterización "bajo pero no despreciable" fue reemplazada por una que refleja el peor caso
real (una de cada cuatro). Se evaluó y se decidió no tocar `_build_entry`/`check_anchors.py`
para agregar `target_start` al dict, por estar fuera del mandato de este repair y porque
cambiaría el JSON observable de `check-anchors` — decisión documentada arriba, no silenciosa.

`check-anchors` sigue en `rc=0`, `anchor_count=38`, mismos `form_counts`. Suite: 970/OK,
sin cambios. `git diff --check` limpio. `status: repaired`, listo para `DELTA_REVIEW`.

No se mutó estado de feature (`ai/state/features/020-honest-dashboard.json` no fue tocado por
este repair-agent).
