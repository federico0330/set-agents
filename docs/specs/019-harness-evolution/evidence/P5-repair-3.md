# P5-tools-discovery — evidencia del repair-agent, ronda 3 (delta review round 3)

Feature 019-harness-evolution, PKG-5. El segundo delta review cerró NEW-01 y las cinco observaciones (más
F-06 reabierto). Queda un solo finding: **NEW-02** (medium) — el hermano `mcp` del bug que reabrió F-06.
Además cierro las dos cosas baratas que el reviewer dejó anotadas (assert reforzado + corrección de
sustantivo en evidencia de ronda 2).

## Estado por finding

| Finding | Severidad | Estado |
|---|---|---|
| NEW-02 | medium | reparado |
| OBS reviewer #1 (assert de `test_cmd_tools_install_never_extra_validates_...`) | — (opcional, barata) | reparado |
| OBS reviewer #2 ("20 entradas curadas" → sustantivo incorrecto) | — (opcional, barata) | reparado |

## NEW-02 (medium) — el hermano `mcp` de F-06

**Causa real**: `_valid_local_entry_shape` (`ai/scripts/set_agents_app.py:1229`) exige `detect`+`install`
para TODO `kind` — deliberadamente, es el mismo esquema uniforme que `cmd_tools_approve` siempre escribe
(ADR-0038 "Rejected alternatives": no se modela un esquema nativo de MCP en este paquete). Consecuencia:
toda entrada `[mcp.*]` que sobrevive el filtro del overlay local tiene forma `cli` (`detect`+`install`) y
**nunca** `type` — el campo que un `[mcp.*]` CURADO siempre tiene (`tools.toml:89-100`, verificado: los
tres `[mcp.*]` curados —`supabase`/`context7`/`playwright`— tienen `type` los tres). `_mcp_json_entry`
(`:2019-2030`, ambas ramas) y `_codex_section` (`:2033-2041`) indexan `spec["type"]` directo, sin `.get()`.

Dos call sites distintos llegan ahí con un spec sin `type`, cada uno por una razón distinta:

1. **`cmd_mcp_add`** (`--mcp-add`) — vía `_mcp_spec(name)` (`:2135` antes de la reparación), que solo
   chequeaba `spec is None`, nunca la forma del spec.
2. **`cmd_mcp_toggle`** (`--mcp-on`/`--mcp-off`) — resuelve el spec **directo** de
   `load_catalog().get("mcp", {}).get(name)` (`:2195` antes de la reparación), sin pasar por `_mcp_spec`
   en absoluto (a propósito: así opencode/codex pueden togglear un server ya presente sin necesitar
   entrada de catálogo). Arreglar solo `_mcp_spec` no cubre este segundo call site — son dos guards
   independientes que hay que poner en los dos lugares.

**Reproducción del ataque, ANTES del arreglo** (revertí quirúrgicamente mis dos ediciones de código para
esta reproducción — sin tocar ningún otro archivo del árbol, que ya tenía cientos de cambios sin commitear
de rondas previas de este mismo paquete — y las reaplique inmediatamente después; ver "Verificación real"
más abajo para la corrida con el árbol ya reparado):

```
$ python3 - <<'PY'
import sys, tempfile, io, shutil, traceback
from pathlib import Path
from unittest import mock
sys.path.insert(0, "ai/scripts")
import set_agents_app as app

with tempfile.TemporaryDirectory() as td:
    root = Path(td) / "root"
    root.mkdir()
    shutil.copy2("tools.toml", root / "tools.toml")
    (root / "tools.local.toml").write_text(
        '[mcp.mytool]\n'
        'detect = "mytool-bin"\n'
        '[mcp.mytool.install]\n'
        'npm = "npm install -g mytool"\n'
    )
    with mock.patch.object(app, "ROOT", root), \
         mock.patch.object(app, "mcp_targets", return_value={"claude": {"path": Path(td) / "claude.json"}}), \
         mock.patch.object(app, "mcp_state", lambda h, t, n: "absent"):
        try:
            app.cmd_mcp_add("mytool")
        except KeyError:
            traceback.print_exc()
        try:
            app.cmd_mcp_toggle("mytool", None, True)
        except KeyError:
            traceback.print_exc()
PY
Traceback (most recent call last):
  ...
  File ".../ai/scripts/set_agents_app.py", line 2166, in cmd_mcp_add
    mcp_write(h, target, name, spec=spec)
  File ".../ai/scripts/set_agents_app.py", line 2118, in mcp_write
    servers[name] = _mcp_json_entry(harness, spec)
  File ".../ai/scripts/set_agents_app.py", line 2040, in _mcp_json_entry
    if spec["type"] == "local":
KeyError: 'type'
Traceback (most recent call last):
  ...
  File ".../ai/scripts/set_agents_app.py", line 2191, in cmd_mcp_toggle
    mcp_write(h, target, name, spec=spec)
  File ".../ai/scripts/set_agents_app.py", line 2118, in mcp_write
    servers[name] = _mcp_json_entry(harness, spec)
  File ".../ai/scripts/set_agents_app.py", line 2040, in _mcp_json_entry
    if spec["type"] == "local":
KeyError: 'type'
```
Exactamente el mismo `KeyError: 'type'` que el finding cita (`:2021`/`:2028` de la numeración del
orquestador). El drift de 12 líneas (2040 acá vs. 2028 del finding) es porque esta reproducción corrió con
mi edición del bloque `NOTA:` de `cmd_tools_approve` YA aplicada (esa edición vive antes en el archivo,
`:1664` en adelante, y agrega ~12 líneas netas) mientras revertía quirúrgicamente solo las otras dos
ediciones (`_mcp_spec`/`cmd_mcp_toggle`) para esta reproducción puntual — `2040 − 12 = 2028`, la misma
línea exacta del finding. Ambos call sites reproducen: el `--mcp-add` reportado por el orquestador y el
`--mcp-on` que el finding dice que "revienta igual".

**Reachability, confirmado (sin cambios — así estaba y sigue)**:

NOTA (repair-4, NEW-04): el bloque que estaba acá antes era una transcripción fabricada —
`allowed()` toma `str`, no `list` (`ai/scripts/coord_policy.py:301`), y el path real del script,
`ai/scripts/set_agents_app.py`, da `False` (`coord_policy.py:245`, `APP_CLI` exige el placeholder
`__SET_AGENTS_ROOT__/ai/scripts/set_agents_app.py` que sustituye `install.py`, no la ruta relativa
del repo — ver `tests/test_autonomy_policy.py:48`, "Wrong script entirely"). Reemplazado por el
comando realmente corrido y su salida real:
```
$ python3 -c "
import sys; sys.path.insert(0, 'ai/scripts')
import coord_policy
print(coord_policy.allowed('python3 ai/scripts/set_agents_app.py --mcp-add mytool'))
print(coord_policy.allowed(f'python3 {coord_policy.APP_CLI} --mcp-add mytool'))
print(coord_policy.allowed(f'python3 {coord_policy.APP_CLI} --mcp-on mytool'))
"
False
True
True
```
El path relativo del repo da `False`; el path con `APP_CLI` (el placeholder que `install.py`
sustituye por la raíz real en la instalación de cada agente) da `True` para ambos verbos. La
conclusión de fondo (`--mcp-add`/`--mcp-on` están alcanzables desde el canal del agente instalado)
sigue siendo cierta — lo que cambió es la transcripción, no el hallazgo.

**Cambio**:

- `ai/scripts/set_agents_app.py:2122` — nueva `_mcp_spec_supported(spec)`: `isinstance(spec, dict) and
  "type" in spec`. Una entrada curada siempre tiene `type` (mirror de `[mcp.*]` en `tools.toml`); una que
  no lo tiene solo puede venir del overlay local (garantizado por `_valid_local_entry_shape`, que nunca
  exige ni modela `type`).
- `ai/scripts/set_agents_app.py:2135` (`_mcp_spec`, usado por `cmd_mcp_add`) — si el spec existe pero no
  pasa `_mcp_spec_supported`, imprime `MCP_UNSUPPORTED {name} — entrada local de tools.local.toml sin
  esquema MCP nativo; instalala a mano con install.<method> (ADR-0038)` y devuelve `None` (mismo `rc=2`
  que el camino `MCP_UNKNOWN` ya usaba) — nunca llega a `mcp_write`/`_mcp_json_entry`.
- `ai/scripts/set_agents_app.py:2191` (`cmd_mcp_toggle`) — el segundo call site, que resuelve el spec
  aparte de `_mcp_spec` (comentario explica por qué: opencode/codex togglean sin necesitar catálogo). Se
  agrega el mismo chequeo `_mcp_spec_supported` justo antes del único `mcp_write(h, target, name,
  spec=spec)` de esa rama (la de claude/cursor/gemini, "add-on-enable"), con `MCP_UNSUPPORTED {name}
  harness={h} — ...` y `continue` — el contrato de `cmd_mcp_toggle` sigue siendo `rc=0` (degrada ese
  harness puntual, no aborta el loop entero, mismo patrón que la rama `MCP_UNKNOWN` ya existente al lado).
- `ai/scripts/set_agents_app.py:1666-1682` (`cmd_tools_approve`, el `NOTA:` para `kind != cli`) — se separa
  en tres ramas (`cli`/`mcp`/`skill` en vez de `cli`/resto): la de `kind=mcp` ahora dice explícitamente que
  ni `--tools-install` NI `--mcp-add`/`--mcp-on` van a encontrar la entrada, en vez de mencionar solo
  `--tools-install` (F-10, que no cubría este flujo). `kind=skill` conserva el mensaje original sin cambios.
- `docs/adr/0038-tools-catalog-discovery.md` — nuevo párrafo "NEW-02 (medium, delta review round 3)" en
  "Rejected alternatives" (donde el ADR ya declaraba en prosa la no-integración de `kind=mcp`), más el
  bullet correspondiente en §9.

**Barrido de TODOS los consumidores de `load_catalog().get("mcp", ...)`** (grep exhaustivo, cada uno
verificado por separado):

```
$ grep -n 'load_catalog().get("mcp"' ai/scripts/set_agents_app.py
2111:    spec = load_catalog().get("mcp", {}).get(name)   # _mcp_spec -- usado por cmd_mcp_add (--mcp-add)
2132:        for name in load_catalog().get("mcp", {})    # _mcp_data -- usado por cmd_mcp (--mcp) y mcp_menu
2165:    spec = load_catalog().get("mcp", {}).get(name)   # cmd_mcp_toggle (--mcp-on/--mcp-off)
2188:    known = name in load_catalog().get("mcp", {}) or ...  # cmd_mcp_remove (--mcp-remove)
```
(Los números de línea de arriba son los del archivo ANTES de esta reparación, tal como los reportó el
grep original del reviewer/orquestador; después de mis ediciones _mcp_spec pasó a `:2135` y
cmd_mcp_toggle's línea a `:2195` por las líneas nuevas de `_mcp_spec_supported` insertadas antes.)

| Consumidor | Comando | ¿Indexa `spec["type"]`? | Resultado |
|---|---|---|---|
| `cmd_mcp_add` (`--mcp-add`) | ver arriba | Sí, vía `_mcp_spec` → `mcp_write` → `_mcp_json_entry` | **Reparado** (este finding) |
| `cmd_mcp_toggle` (`--mcp-on`/`--mcp-off`) | ver arriba | Sí, vía spec propio → `mcp_write` → `_mcp_json_entry`/`_codex_section` | **Reparado** (este finding) |
| `_mcp_data`/`cmd_mcp` (`--mcp`) | ver `test_mcp_read_only_consumers_tolerate_...` abajo | No — solo itera nombres y llama `mcp_state(harness, target, name)`, nunca toca el spec | Ya degradaba bien; pineado con test |
| `cmd_mcp_remove` (`--mcp-remove`) | ver el mismo test | No — `known = name in catalog or ...` es un chequeo de membership; `mcp_write(..., remove=True)` nunca lee `spec` (rama `if remove: servers.pop(...)`) | Ya degradaba bien; pineado con test |
| `mcp_menu()` (menú interactivo) | inspección de código, `:2820-2869` | No directamente — delega TODO a `cmd_mcp_add`/`cmd_mcp_toggle`/`cmd_mcp_remove`, los mismos cuatro de arriba | Cubierto transitivamente por los cuatro anteriores |
| `--doctor`/`cmd_doctor_all` | `grep -n "mcp" ai/scripts/set_agents_app.py` alrededor de `:787-826` | No — no toca el catálogo mcp en absoluto (solo harnesses/CLIs/auth) | No aplica, confirmado por lectura |

No hay un quinto consumidor: `--mcp`, `--mcp-add`, `--mcp-remove`, `--mcp-on`, `--mcp-off`, el menú
interactivo y `--doctor` son los únicos puntos de entrada de `main()`/`menu()` que tocan `mcp`:
```
$ grep -n "args.mcp\|mcp_menu()" ai/scripts/set_agents_app.py
2820:def mcp_menu():
3201:            mcp_menu()
3465:    if args.mcp:
3467:    if args.mcp_add:
3469:    if args.mcp_remove:
3471:    if args.mcp_on:
3473:    if args.mcp_off:
```

**Verificación real, con el árbol ya reparado (salida limpia + `rc`)**:
```
$ python3 - <<'PY'
import sys, tempfile, io, shutil
from pathlib import Path
from unittest import mock
sys.path.insert(0, "ai/scripts")
import set_agents_app as app

with tempfile.TemporaryDirectory() as td:
    root = Path(td) / "root"
    root.mkdir()
    shutil.copy2("tools.toml", root / "tools.toml")
    (root / "tools.local.toml").write_text(
        '[mcp.mytool]\n'
        'detect = "mytool-bin"\n'
        '[mcp.mytool.install]\n'
        'npm = "npm install -g mytool"\n'
    )
    with mock.patch.object(app, "ROOT", root), \
         mock.patch.object(app, "mcp_targets", return_value={"claude": {"path": Path(td) / "claude.json"}}), \
         mock.patch.object(app, "mcp_state", lambda h, t, n: "absent"):
        buf = io.StringIO()
        with mock.patch("sys.stdout", buf):
            rc = app.cmd_mcp_add("mytool")
        print("cmd_mcp_add rc=", rc); print(buf.getvalue())
        buf2 = io.StringIO()
        with mock.patch("sys.stdout", buf2):
            rc2 = app.cmd_mcp_toggle("mytool", None, True)
        print("cmd_mcp_toggle rc=", rc2); print(buf2.getvalue())
PY
cmd_mcp_add rc= 2
MCP_UNSUPPORTED mytool — entrada local de tools.local.toml sin esquema MCP nativo; instalala a mano con install.<method> (ADR-0038)

cmd_mcp_toggle rc= 0
MCP_UNSUPPORTED mytool harness=claude — entrada local de tools.local.toml sin esquema MCP nativo; instalala a mano con install.<method> (ADR-0038)
```
Sin traceback, `rc=2` para `--mcp-add` (nunca llega a escribir nada — ningún archivo de configuración de
harness tocado), `rc=0` para `--mcp-on` con el contrato de "degrada ese harness, no aborta" intacto.

**El catálogo curado real sigue funcionando exactamente igual** (E2E completo, subprocess real, los tres
`[mcp.*]` curados con `type`, cinco harnesses):
```
$ python3 -m unittest discover -s tests -k "test_set_agents_mcp_across_harnesses" -v
test_set_agents_mcp_across_harnesses ... ok
Ran 1 test in 0.809s
OK
```

**Tests de regresión** (`tests/test_harness.py`):
- `test_cmd_mcp_add_degrades_a_local_only_mcp_entry_missing_native_type_instead_of_crashing` — la mordida
  de `--mcp-add` de arriba, como test real (`mcp_write` mockeado, `assert_not_called()`).
- `test_cmd_mcp_toggle_degrades_a_local_only_mcp_entry_missing_native_type_instead_of_crashing` — la
  mordida de `--mcp-on` de arriba, mismo patrón.
- `test_mcp_read_only_consumers_tolerate_a_local_only_entry_missing_native_type` — pinea que `--mcp`
  (`cmd_mcp`) y `--mcp-remove` (`cmd_mcp_remove`) siguen funcionando sin crashear con la misma entrada
  local-only presente (ambos ya eran seguros; el test evita que un cambio futuro reintroduzca la
  indexación de `type` en silencio).

**Verificación real (los tres tests)**:
```
$ python3 -m unittest discover -s tests -k "test_cmd_mcp_add_degrades_a_local_only_mcp_entry_missing_native_type_instead_of_crashing" -k "test_cmd_mcp_toggle_degrades_a_local_only_mcp_entry_missing_native_type_instead_of_crashing" -k "test_mcp_read_only_consumers_tolerate_a_local_only_entry_missing_native_type" -v
test_cmd_mcp_add_degrades_a_local_only_mcp_entry_missing_native_type_instead_of_crashing ... ok
test_cmd_mcp_toggle_degrades_a_local_only_mcp_entry_missing_native_type_instead_of_crashing ... ok
test_mcp_read_only_consumers_tolerate_a_local_only_entry_missing_native_type ... ok
Ran 3 tests in 0.010s
OK
```

**Prueba de mordida** (neutralizar `_mcp_spec_supported` — `return isinstance(spec, dict) and "type" in
spec` → `return True  # BITE TEST` — y re-correr):
```
$ python3 -m unittest discover -s tests -k "test_cmd_mcp_add_degrades_a_local_only_mcp_entry_missing_native_type_instead_of_crashing" -k "test_cmd_mcp_toggle_degrades_a_local_only_mcp_entry_missing_native_type_instead_of_crashing" -v
FAIL: test_cmd_mcp_add_degrades_a_local_only_mcp_entry_missing_native_type_instead_of_crashing
AssertionError: 0 != 2
FAIL: test_cmd_mcp_toggle_degrades_a_local_only_mcp_entry_missing_native_type_instead_of_crashing
AssertionError: 'MCP_UNSUPPORTED mytool harness=claude' not found in 'MCP_SET mytool harness=claude state=absent\n'
Ran 2 tests in 0.009s
FAILED (failures=2)
```
(En estos dos tests `mcp_write` está mockeado, así que la mordida se ve como un `rc`/mensaje equivocado en
vez de un `KeyError` real — confirmé el `KeyError` real por separado, sin mockear `mcp_write`, con la
misma entrada y el guard neutralizado, reproduciendo el traceback exacto de la sección "ANTES" de arriba.)
Guard restaurado inmediatamente después; tests verdes de nuevo (ver "Verificación real" arriba).

## Observaciones baratas del reviewer, cerradas de paso

### `test_cmd_tools_install_never_extra_validates_a_curated_entry_even_when_a_local_name_collides` — assert reforzado

**Antes**: el test solo assertaba `_is_local_only_entry("cli", "vercel") is False` — probaba la
clasificación, no que `cmd_tools_install` de verdad resuelve y corre el comando CURADO en vez del local
que colisiona. El reviewer lo había verificado empíricamente pero el test no lo fijaba.

**Cambio**: `tests/test_harness.py` — el mismo test ahora también llama
`app.cmd_tools_install("vercel", yes=True)` con `subprocess.run` mockeado y assertea
`run.assert_called_once_with(["bash", "-c", "npm install -g vercel"], check=False)` — el comando CURADO
exacto (`tools.toml:22`), nunca el `"true & touch /tmp/should-never-run"` del bloque `tools.local.toml`
colisionante del mismo test.

**Verificación real**:
```
$ python3 -m unittest discover -s tests -k "test_cmd_tools_install_never_extra_validates_a_curated_entry_even_when_a_local_name_collides" -v
test_cmd_tools_install_never_extra_validates_a_curated_entry_even_when_a_local_name_collides ... ok
Ran 1 test in 0.005s
OK
```

### "las 20 entradas curadas" — sustantivo incorrecto en la evidencia de ronda 2

**Verificado**: `tools.toml` tiene 9 entradas `[cli.*]`, con 29 claves totales en sus tablas `install`
(algunas con más de un método), de las cuales 9 son `doc` (no un método real, ver `cmd_tools_install`:
`if method == "doc": continue`) → 29 − 9 = **20 comandos de install**, no 20 entradas:
```
$ python3 -c "
import tomllib
data = tomllib.loads(open('tools.toml').read())
cli = data.get('cli', {})
print('num cli entries:', len(cli))
total = sum(len(e.get('install', {})) for e in cli.values())
doc = sum(1 for e in cli.values() for k in e.get('install', {}) if k == 'doc')
print('install-table keys:', total, 'doc:', doc, 'install commands:', total - doc)
"
num cli entries: 9
install-table keys: 29 doc: 9 install commands: 20
```
**Cambio**: `docs/specs/019-harness-evolution/evidence/P5-repair-2.md` (dos ocurrencias) y
`docs/adr/0038-tools-catalog-discovery.md` §6 (una ocurrencia, mismo defecto conceptual: describía
`_is_local_only_entry`'s exención — que opera por NOMBRE de entrada, no por comando — usando el número de
comandos) — las tres corregidas a "9 entradas `[cli.*]` curadas" (con nota de reconciliación en la
evidencia de ronda 2 explicando de dónde salía el 20). El número en sí (20) era correcto para lo que de
verdad contaba (comandos de install); no se tocó ningún otro número.

## Restricciones respetadas

No toqué P1..P4, el motor de estado (ADR-0039), ni ningún finding ya cerrado (F-01..F-15, NEW-01, las
cinco observaciones de ronda 2). Ningún test relajado, salteado ni borrado — la base (912 OK / 3 skips)
subió a 915 OK / 3 skips (exactamente +3, los tres tests nuevos de este finding; el cuarto cambio de test
—el assert reforzado— es una extensión de un test EXISTENTE, no uno nuevo). No mutué estado de feature
(ningún `feature-state.py` corrido en modo mutante desde este rol).

## Gates (ronda 3)

`git diff --check` (limpio, sobre los archivos tocados en esta ronda):
```
$ git diff --check -- ai/scripts/set_agents_app.py tests/test_harness.py docs/adr/0038-tools-catalog-discovery.md docs/specs/019-harness-evolution/evidence/P5-repair-2.md
$ echo "EXIT=$?"
EXIT=0
```

`git status --porcelain` — sin `tools.local.toml` ni `tools.proposals.json`:
```
$ git status --porcelain | grep -E "tools\.local\.toml|tools\.proposals\.json"
$ echo "EXIT=$?"
EXIT=1
```
(sin salida del `grep` → `EXIT=1` → ninguno de los dos archivos está presente en el árbol de trabajo.)

`python3 -m unittest discover -s tests` (corrida completa):
```
$ python3 -m unittest discover -s tests
Ran 915 tests in 390.119s

OK (skipped=3)
```
Reconciliación: base declarada al inicio de esta ronda 912 OK / 3 skips; 3 tests nuevos en esta ronda
(los tres de NEW-02) → 912 + 3 = 915, exactamente lo que reporta la suite. Ningún skip nuevo (sigue en 3),
ningún test existente bajó.

`./ai/scripts/verify.sh` (corrida completa, árbol de trabajo final):
```
$ ./ai/scripts/verify.sh
...
Ran 915 tests in 409.880s

OK (skipped=3)
GLOBAL_PORTABILITY_OK
CANONICAL_PATHS_OK
FEATURE_STATE_OK
VERIFY_PASS
```

`./build.sh --check` (no toqué `Global/_canonical/` en esta ronda, corrido igual por completitud; sin
drift):
```
$ ./build.sh --check
CHECK_PASS: generated and validated profile go-zen
SELF_SCAFFOLD_SYNC_OK files=2
```

`python3 -m py_compile` (sanity de sintaxis sobre los archivos Python tocados):
```
$ python3 -m py_compile ai/scripts/set_agents_app.py tests/test_harness.py
$ echo "EXIT=$?"
EXIT=0
```

## Tamaño del diff (para el ceiling de reparación, ADR-0023)

`repair_ceiling` para PKG-5 está en `None` en el estado de feature al momento de escribir esto (no hay un
número fijado que yo pueda leer sin mutar estado). El diff de ESTA ronda, aislado (nada se commiteó entre
rondas, así que `git diff` contra HEAD mezcla las ~18 rondas previas de este mismo paquete — no sirve para
aislar el tamaño de este cambio puntual):

- `ai/scripts/set_agents_app.py`: 3 ediciones quirúrgicas — el bloque `NOTA:` de `cmd_tools_approve`
  (~10 líneas → ~22, kind=mcp separado de kind=skill), `_mcp_spec_supported` nueva + `_mcp_spec`
  extendida (~5 líneas → ~22), y el guard nuevo en `cmd_mcp_toggle` (~5 líneas → ~17). Un solo finding,
  tres call sites relacionados por la misma causa raíz (spec sin `type`).
- `tests/test_harness.py`: 3 tests nuevos (~90 líneas) + 1 test existente extendido (~15 líneas más) +
  1 helper compartido (~13 líneas).
- `docs/adr/0038-tools-catalog-discovery.md`: un párrafo nuevo en "Rejected alternatives" + un bullet en
  §9 + la corrección del sustantivo en §6 (observación barata).
- `docs/specs/019-harness-evolution/evidence/P5-repair-2.md`: corrección del sustantivo en dos lugares
  (observación barata, no reabre nada de esa ronda).

Un solo finding `medium`, tres call sites de la misma causa raíz, sin tocar diseño ni criterios de
aceptación — diff acotado y de la escala esperada para una reparación de una ronda.
