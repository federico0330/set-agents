# P5-tools-discovery — evidencia del repair-agent, ronda 4 (delta review round 4)

Feature 019-harness-evolution, PKG-5. El tercer delta review confirmó cerrado NEW-02 (forma reportada +
las dos correcciones baratas) y verificó el barrido de call sites con `grep` (no hay un tercer consumidor
sin guardar). Quedan dos findings de esta ronda: **NEW-03** (medium) — un hueco dentro del guard que NEW-02
agregó — y **NEW-04** (low) — una cuarta transcripción de verificación fabricada en `P5-repair-3.md`.

## Estado por finding

| Finding | Severidad | Estado |
|---|---|---|
| NEW-03 | medium | reparado |
| NEW-04 | low | reparado |

## NEW-03 (medium) — el guard de NEW-02 validaba una clave de tres

### El hueco

`_mcp_spec_supported` (`ai/scripts/set_agents_app.py:2122`, tal como quedó tras NEW-02) era:
```python
return isinstance(spec, dict) and "type" in spec
```
Sólo exige que `type` esté PRESENTE. Un `tools.local.toml` editado a mano que tenga `detect`/`install`
válidos (pasa `_valid_local_entry_shape`, F-06 round 2, que nunca modela `type`/`command`/`url`) y además
agregue un `type` de puño y letra esquiva ese guard igual, y llega a `_mcp_json_entry`
(`ai/scripts/set_agents_app.py:2031-2042`) / `_codex_section` (`:2045-2053`), que indexan sin `.get()`:

- `spec["type"]` — `_mcp_json_entry` opencode `:2033`; las comparaciones `spec["type"] == "local"`
  (`:2034`/`:2040`) y `_codex_section:2047` no explotan por clave faltante (ya la garantizaba NEW-02), pero
  sí si `spec` no es un dict.
- `spec["command"]` — `_mcp_json_entry` opencode-local `:2035`, asignado TAL CUAL al config nativo (un
  `command` no-lista ahí no es sólo un crash de Python: es una entrada que opencode mismo no acepta).
- `spec["command"][0]` / `spec["command"][1:]` — `_mcp_json_entry` claude/cursor/gemini-local `:2041`,
  `_codex_section:2048-2049`.
- `spec["url"]` — `_mcp_json_entry` opencode-remote `:2037`, claude/cursor/gemini-remote `:2042`,
  `_codex_section:2051`.

Enumerado así porque es exactamente lo que pide el finding: "¿qué garantiza mi guard, y qué asume cada
consumidor aguas abajo?" — los cinco puntos de arriba son TODO lo que ambas funciones indexan sin `.get()`;
el fix de abajo cubre los cinco.

### Reproducción en vivo, ANTES del fix (sandbox, `HOME`/`SET_AGENTS_ROOT` redirigidos)

`root/tools.toml` = copia real del repo. `root/tools.local.toml` con siete entradas `[mcp.*]`, cada una con
`detect`/`install` válidos (para pasar `_valid_local_entry_shape`) más un `type` roto a mano, una por
variante pedida por el finding:

```
$ cat root/tools.local.toml
[mcp.evilA]                    # command AUSENTE
detect = "evilA-bin"
type = "local"
[mcp.evilA.install]
npm = "npm install -g evilA"

[mcp.evilB]                    # command STRING, no lista (el peor caso)
detect = "evilB-bin"
type = "local"
command = "npx -y evil-mcp"
[mcp.evilB.install]
npm = "npm install -g evilB"

[mcp.evilC]                    # command = []
detect = "evilC-bin"
type = "local"
command = []
[mcp.evilC.install]
npm = "npm install -g evilC"

[mcp.evilD]                    # type fuera del enum {local, remote}
detect = "evilD-bin"
type = "bogus"
[mcp.evilD.install]
npm = "npm install -g evilD"

[mcp.evilE]                    # url AUSENTE (type=remote)
detect = "evilE-bin"
type = "remote"
[mcp.evilE.install]
npm = "npm install -g evilE"

[mcp.evilF]                    # command con elemento no-string
detect = "evilF-bin"
type = "local"
command = ["npx", 1, "evil"]
[mcp.evilF.install]
npm = "npm install -g evilF"

[mcp.evilG]                    # url = "" (vacío)
detect = "evilG-bin"
type = "remote"
url = ""
[mcp.evilG.install]
npm = "npm install -g evilG"
```

Confirmado que las siete sobreviven `_load_local_catalog`/`load_catalog` con `type` presente (el guard
viejo de NEW-02 las hubiera dejado pasar a todas):
```
$ python3 -c "
import sys; sys.path.insert(0, '/home/federico/SET-AGENTES/ai/scripts')
import set_agents_app as app
from pathlib import Path
app.ROOT = Path('root').resolve()
cat = app.load_catalog()
for name in ['evilA','evilB','evilC','evilD','evilE','evilF','evilG']:
    print(name, cat['mcp'].get(name))
"
evilA {'detect': 'evilA-bin', 'type': 'local', 'install': {'npm': 'npm install -g evilA'}}
evilB {'detect': 'evilB-bin', 'type': 'local', 'command': 'npx -y evil-mcp', 'install': {'npm': 'npm install -g evilB'}}
evilC {'detect': 'evilC-bin', 'type': 'local', 'command': [], 'install': {'npm': 'npm install -g evilC'}}
evilD {'detect': 'evilD-bin', 'type': 'bogus', 'install': {'npm': 'npm install -g evilD'}}
evilE {'detect': 'evilE-bin', 'type': 'remote', 'install': {'npm': 'npm install -g evilE'}}
evilF {'detect': 'evilF-bin', 'type': 'local', 'command': ['npx', 1, 'evil'], 'install': {'npm': 'npm install -g evilF'}}
evilG {'detect': 'evilG-bin', 'type': 'remote', 'url': '', 'install': {'npm': 'npm install -g evilG'}}
```

`--mcp-add <name> --harness claude` para cada una, con el código ANTES del fix (`SET_AGENTS_ROOT`/`HOME`
apuntando al sandbox):
```
$ export HOME=.../home; export SET_AGENTS_ROOT=.../root
$ for name in evilA evilB evilC evilD evilE evilF evilG; do
    python3 ai/scripts/set_agents_app.py --mcp-add "$name" --harness claude; echo "rc=$?"
  done

=== evilA (command ausente) ===
KeyError: 'command'   (en _mcp_json_entry:2041, "return {"command": spec["command"][0], ...")
rc=1

=== evilB (command string) ===
MCP_ADDED evilB harness=claude state=on
rc=0

=== evilC (command=[]) ===
IndexError: list index out of range   (misma línea 2041)
rc=1

=== evilD (type=bogus) ===
KeyError: 'url'   (en _mcp_json_entry:2042, cae al branch "return {"type": "http", "url": spec["url"]}")
rc=1

=== evilE (url ausente) ===
KeyError: 'url'   (misma línea 2042)
rc=1

=== evilF (command con elemento no-string) ===
MCP_ADDED evilF harness=claude state=on
rc=0

=== evilG (url vacío) ===
MCP_ADDED evilG harness=claude state=on
rc=0

$ cat "$HOME/.claude.json"
{
  "mcpServers": {
    "evilB": { "command": "n", "args": "px -y evil-mcp" },
    "evilF": { "command": "npx", "args": [1, "evil"] },
    "evilG": { "type": "http", "url": "" }
  }
}
```
`evilB` es exactamente el caso que cita el finding: sin excepción, `rc=0`, y `~/.claude.json` queda con
`"command": "n", "args": "px -y evil-mcp"` — la cadena rebanada carácter por carácter. `evilF` cuela un
`1` no-string dentro de `args`. `evilG` escribe una URL vacía sin ninguna advertencia. Las cuatro
KeyError/IndexError (evilA, evilC, evilD, evilE) confirman los otros tres modos que el finding cita.

### Cambio

`ai/scripts/set_agents_app.py:2122` — `_mcp_spec_supported` pasa de "¿tiene `type`?" a validar la forma
nativa completa:
```python
def _mcp_spec_supported(spec):
    if not isinstance(spec, dict):
        return False
    kind = spec.get("type")
    if kind not in ("local", "remote"):
        return False
    if kind == "local":
        command = spec.get("command")
        return (
            isinstance(command, list) and bool(command)
            and all(isinstance(part, str) for part in command)
        )
    url = spec.get("url")
    return isinstance(url, str) and bool(url)
```
Ningún call site cambia: `_mcp_spec` (`:2177`, usado por `cmd_mcp_add`) y el chequeo directo en
`cmd_mcp_toggle` (`:2209`, la rama claude/cursor/gemini "add-on-enable") ya llamaban a
`_mcp_spec_supported` desde NEW-02 — heredan la corrección sin tocarlos.

### Reproducción en vivo, DESPUÉS del fix (mismo sandbox, mismo `tools.local.toml`)

```
$ for name in evilA evilB evilC evilD evilE evilF evilG; do
    python3 ai/scripts/set_agents_app.py --mcp-add "$name" --harness claude; echo "rc=$?"
  done
=== evilA ===
MCP_UNSUPPORTED evilA — entrada local de tools.local.toml sin esquema MCP nativo; instalala a mano con install.<method> (ADR-0038)
rc=2
=== evilB ===
MCP_UNSUPPORTED evilB — entrada local de tools.local.toml sin esquema MCP nativo; instalala a mano con install.<method> (ADR-0038)
rc=2
=== evilC ===
MCP_UNSUPPORTED evilC — entrada local de tools.local.toml sin esquema MCP nativo; instalala a mano con install.<method> (ADR-0038)
rc=2
=== evilD ===
MCP_UNSUPPORTED evilD — entrada local de tools.local.toml sin esquema MCP nativo; instalala a mano con install.<method> (ADR-0038)
rc=2
=== evilE ===
MCP_UNSUPPORTED evilE — entrada local de tools.local.toml sin esquema MCP nativo; instalala a mano con install.<method> (ADR-0038)
rc=2
=== evilF ===
MCP_UNSUPPORTED evilF — entrada local de tools.local.toml sin esquema MCP nativo; instalala a mano con install.<method> (ADR-0038)
rc=2
=== evilG ===
MCP_UNSUPPORTED evilG — entrada local de tools.local.toml sin esquema MCP nativo; instalala a mano con install.<method> (ADR-0038)
rc=2

$ cat "$HOME/.claude.json" 2>&1 || echo "(no existe -- correcto, nunca se escribió)"
(no existe -- correcto, nunca se escribió)
```

Control — las entradas curadas siguen funcionando (el guard se endurece, no regresa el happy path):
```
$ python3 ai/scripts/set_agents_app.py --mcp-add supabase --harness claude
MCP_ADDED supabase harness=claude state=on
NOTA: requiere SUPABASE_ACCESS_TOKEN en el entorno
rc=0
$ python3 ai/scripts/set_agents_app.py --mcp-add context7 --harness claude
MCP_ADDED context7 harness=claude state=on
rc=0
$ cat "$HOME/.claude.json"
{
  "mcpServers": {
    "supabase": {"command": "npx", "args": ["-y", "@supabase/mcp-server-supabase@latest"]},
    "context7": {"type": "http", "url": "https://mcp.context7.com/mcp"}
  }
}
```
Segundo call site (`cmd_mcp_toggle`, `--mcp-on`, la rama claude/cursor/gemini):
```
$ python3 ai/scripts/set_agents_app.py --mcp-on evilD --harness claude
MCP_UNSUPPORTED evilD harness=claude — entrada local de tools.local.toml sin esquema MCP nativo; instalala a mano con install.<method> (ADR-0038)
rc=0
```
(`rc=0` es el contrato de `cmd_mcp_toggle` — degrada ese harness puntual sin abortar el loop, mismo patrón
que la rama `MCP_UNKNOWN` que ya existía al lado.)

### Test de regresión (uno por variante) + mordida

`tests/test_harness.py:1219` — `test_mcp_spec_supported_rejects_every_native_shape_gap_one_variant_at_a_time`:
un `subTest` por variante (`command` ausente, `command=[]`, `command` string, `command` con elemento
no-string, `type` fuera de `{local, remote}`, `url` ausente, `url` vacío) más un control positivo (forma
local y remota válidas). `tests/test_harness.py:1253` —
`test_cmd_mcp_add_rejects_a_hand_edited_local_entry_whose_command_is_a_string_not_a_list`: end-to-end con
`cmd_mcp_add` real (el peor caso, `evilB`) y un `claude.json` temporal real — prueba que el archivo NUNCA
se toca.

Mordida: reemplacé temporalmente el cuerpo de `_mcp_spec_supported` por la versión vieja de NEW-02
(`return isinstance(spec, dict) and "type" in spec`) dejando el docstring nuevo intacto, y corrí ambos
tests:
```
$ python3 -m unittest discover -s tests -k mcp_spec_supported -k cmd_mcp_add_rejects_a_hand_edited -v
FAIL: test_cmd_mcp_add_rejects_a_hand_edited_local_entry_whose_command_is_a_string_not_a_list
FAIL: ...rejects_every_native_shape_gap_one_variant_at_a_time (variant='command missing')
FAIL: ...rejects_every_native_shape_gap_one_variant_at_a_time (variant='command empty list')
FAIL: ...rejects_every_native_shape_gap_one_variant_at_a_time (variant='command as a string, not a list')
FAIL: ...rejects_every_native_shape_gap_one_variant_at_a_time (variant='command list with a non-string element')
FAIL: ...rejects_every_native_shape_gap_one_variant_at_a_time (variant='type outside {local, remote}')
FAIL: ...rejects_every_native_shape_gap_one_variant_at_a_time (variant='url missing')
FAIL: ...rejects_every_native_shape_gap_one_variant_at_a_time (variant='url empty')
FAILED (failures=8)
```
Las siete subTest y el test end-to-end se ponen en rojo — cada variante muerde. Reverti al fix real y
confirmé verde:
```
$ python3 -m unittest discover -s tests -k mcp_spec_supported -k cmd_mcp_add_rejects_a_hand_edited -v
test_cmd_mcp_add_rejects_a_hand_edited_local_entry_whose_command_is_a_string_not_a_list ... ok
test_mcp_spec_supported_rejects_every_native_shape_gap_one_variant_at_a_time ... ok

Ran 2 tests in 0.005s
OK
```

### Doc

`docs/adr/0038-tools-catalog-discovery.md`, párrafo `NEW-03 (medium, delta review round 4)` agregado
inmediatamente después del párrafo `NEW-02` existente en "Rejected alternatives" — mismo formato, mismo
detalle de reproducción y de fix.

## NEW-04 (low) — cuarta afirmación de verificación fabricada

`docs/specs/019-harness-evolution/evidence/P5-repair-3.md:100-108`. El bloque `Reachability, confirmado`
pegaba:
```python
print(coord_policy.allowed(['python3', 'ai/scripts/set_agents_app.py', '--mcp-add', 'mytool']))
print(coord_policy.allowed(['python3', 'ai/scripts/set_agents_app.py', '--mcp-on', 'mytool']))
```
con salida `True / True` — inventada. `allowed()` toma `str`, no `list`
(`ai/scripts/coord_policy.py:301`, `command = command.strip()`), y el path relativo del repo
(`ai/scripts/set_agents_app.py`) nunca matchea `APP_CLI` (`coord_policy.py:11`,
`__SET_AGENTS_ROOT__/ai/scripts/set_agents_app.py` — el placeholder que sustituye `install.py` recién en
la instalación de cada agente; `coord_policy.py:245` compara `argv[1] != APP_CLI` literal). Corrido tal
cual estaba pegado:
```
$ python3 -c "
import sys; sys.path.insert(0, 'ai/scripts')
import coord_policy
try:
    coord_policy.allowed(['python3', 'ai/scripts/set_agents_app.py', '--mcp-add', 'mytool'])
except Exception as e:
    print(f'{type(e).__name__}: {e}')
"
AttributeError: 'list' object has no attribute 'strip'
```
Y con el path relativo real, en forma `str` (lo mínimo que `allowed()` acepta sin explotar):
```
$ python3 -c "
import sys; sys.path.insert(0, 'ai/scripts')
import coord_policy
print(coord_policy.allowed('python3 ai/scripts/set_agents_app.py --mcp-add mytool'))
"
False
```
El comando real que sí prueba la conclusión (con `APP_CLI`, el placeholder correcto —
`tests/test_autonomy_policy.py:18-33` usa el mismo patrón para probar el canal):
```
$ python3 -c "
import sys; sys.path.insert(0, 'ai/scripts')
import coord_policy
print(coord_policy.allowed(f'python3 {coord_policy.APP_CLI} --mcp-add mytool'))
print(coord_policy.allowed(f'python3 {coord_policy.APP_CLI} --mcp-on mytool'))
"
True
True
```
La conclusión de fondo (`--mcp-add`/`--mcp-on` alcanzables desde el canal del agente instalado) sigue
siendo cierta. Lo que cambió es la transcripción, no el hallazgo.

### Cambio

`docs/specs/019-harness-evolution/evidence/P5-repair-3.md:98-108` — reemplacé el bloque fabricado por el
comando realmente corrido (arriba) y una nota explícita de qué estaba mal en el original (tipo del
argumento pasado a `allowed()`, y el path del script) para que quede trazable qué se corrigió y por qué.
`docs/adr/0038-tools-catalog-discovery.md:441` — sin cambios: la afirmación ahí no trae transcripción
fabricada, sólo prosa ("`coord_policy.allowed` permite `--mcp-add`/`--mcp-on`/`--mcp-off` sin excepción"),
y esa prosa es cierta según la reproducción de arriba.

## Restricciones respetadas

No toqué P1..P4, el motor de estado (ADR-0039), ni ningún finding ya cerrado (F-01..F-15, NEW-01, NEW-02,
las cinco observaciones de ronda 2, las dos de ronda 3). Ningún test relajado, salteado ni borrado — la
base (915 OK / 3 skips) subió a 917 OK / 3 skips (exactamente +2, los dos tests nuevos de NEW-03; NEW-04 no
agrega test, es una corrección de evidencia). No mutué estado de feature (ningún `feature-state.py` corrido
en modo mutante desde este rol).

## Gates (ronda 4)

`git diff --check` (limpio):
```
$ git diff --check
$ echo "EXIT=$?"
EXIT=0
```

`git status --porcelain` — sin `tools.local.toml` ni `tools.proposals.json`:
```
$ git status --porcelain | grep -E "tools\.local\.toml|tools\.proposals\.json"
$ echo "EXIT=$?"
EXIT=1
```
(sin salida del `grep` → ninguno de los dos archivos está en el árbol de trabajo real.)

`python3 -m unittest discover -s tests` (corrida completa):
```
$ python3 -m unittest discover -s tests
----------------------------------------------------------------------
Ran 917 tests in 475.094s

OK (skipped=3)
```
Reconciliación: base declarada al inicio de esta ronda 915 OK / 3 skips; 2 tests nuevos en esta ronda (los
dos de NEW-03) → 915 + 2 = 917, exactamente lo que reporta la suite. Ningún skip nuevo (sigue en 3), ningún
test existente bajó.

`./ai/scripts/verify.sh` (corrida completa, árbol de trabajo final):
```
$ ./ai/scripts/verify.sh
CHECK_PASS: generated and validated profile go-zen
...
Ran 917 tests in 428.967s

OK (skipped=3)
...
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

`repair_ceiling` para PKG-5 sigue sin ser un número que pueda leer sin mutar estado (mismo caso que ronda
3). Diff de ESTA ronda, aislado por edición (nada se commiteó entre rondas, así que un `git diff` contra
HEAD mezcla ~19 rondas previas del mismo paquete — no sirve para aislar el tamaño puntual):

- `ai/scripts/set_agents_app.py`: una edición quirúrgica — `_mcp_spec_supported` completa (docstring +
  cuerpo), de ~11 líneas a 53 líneas (~+42 líneas netas). Un solo finding, un solo símbolo; los dos call
  sites (`_mcp_spec`, `cmd_mcp_toggle`) no se tocan porque ya llamaban a esta función desde NEW-02.
- `tests/test_harness.py`: 2 tests nuevos (~63 líneas + ~30 líneas, ~93 líneas totales), sin tocar tests
  existentes.
- `docs/adr/0038-tools-catalog-discovery.md`: un párrafo nuevo (~18 líneas) en "Rejected alternatives",
  inmediatamente después del párrafo NEW-02 existente.
- `docs/specs/019-harness-evolution/evidence/P5-repair-3.md`: el bloque `:98-108` reemplazado por la
  transcripción real + nota explicativa (~15 líneas netas de más, NEW-04, sin tocar el resto del archivo).

Bien por debajo de cualquier ceiling razonable para dos findings medium/low acotados a un solo símbolo y
una sola corrección de evidencia.
