# P5-tools-discovery — evidencia del repair-agent (relanzamiento)

Feature 019-harness-evolution, PKG-5. **Esta es la segunda instancia de este repair.** La primera murió por
stall de infraestructura (`no progress for 600s`) sin dejar nada en disco (verificado por el orquestador:
no existía este archivo, ADR-0038 conservaba timestamp original, los tres bloqueantes seguían vivos). Esta
instancia escribe a disco después de cada finding, incrementalmente — ver
`ai/state/decisions-log.jsonl` slug `p5-repair-stall-relanzamiento`.

Orden de trabajo (bloqueantes primero): F-01 → F-04 → F-03 → F-02 → F-08 → F-05 → F-06 → F-09 → F-10 →
F-07 → F-11 → F-12 → F-13 → F-14 → F-15.

Decisiones ya tomadas por el orquestador (`decisions-log.jsonl` slug `p5-repair-excepciones-y-diseno`),
ejecutadas sin re-litigar: excepción de ownership sobre `cmd_tools_install:1544` (F-03), variante elegida
para F-02 (re-impresión completa + confirmación interactiva, patrón de `cmd_tools_install:1549-1555`), y
F-11 documenta alcance real sin rediseñar a per-project.

## Estado por finding

| Finding | Severidad | Estado |
|---|---|---|
| F-01 | critical | reparado |
| F-04 | high | reparado |
| F-03 | high | reparado |
| F-02 | critical | reparado |
| F-08 | medium | reparado |
| F-05 | medium | reparado |
| F-06 | medium | reparado |
| F-09 | medium | reparado |
| F-10 | medium | reparado |
| F-07 | medium | reparado |
| F-11 | medium | reparado |
| F-12 | low | reparado |
| F-13 | low | reparado |
| F-14 | low | reparado |
| F-15 | low | reparado |

## Detalle (se completa incrementalmente, uno por uno)

(Cada entrada abajo sigue el formato: finding → cambio (archivo:línea) → verificación (comando pegado +
salida real) → test de regresión. Para F-01/F-02/F-03/F-04 además la reproducción del ataque fallando
después del arreglo.)

### F-01 (critical) — `&` y salto de línea no estaban en el denylist → ejecución arbitraria

**Cambio**: `ai/scripts/set_agents_app.py` — `_validate_install_command` reemplaza el denylist de
metacaracteres recordados (`_SHELL_METACHAR_RE`/`_REDIRECT_RE`) por un **allowlist de caracteres**
(`_ALLOWED_CMD_CHARS_RE = re.compile(r"^[A-Za-z0-9 @+,\-./:=_~|]+$")`): todo carácter fuera del set se
rechaza por construcción, incluidos `&`, `;`, backtick, `$`, `(`, `)`, `<`, `>` y todo carácter de control
ASCII (newline incluido). `ai/scripts/coord_policy.py` — `FORBIDDEN_SYNTAX` ganó una alternativa `&` suelta
y `[\x00-\x1f\x7f]` (control chars), y el docstring de `_tools_propose_allowed` (antes afirmaba falsamente
que todo metacaracter real ya estaba cubierto) se corrigió para reflejar el fix, no solo describirlo.

**Reproducción del ataque, falla después del arreglo**:
```
$ python3 -c "
import sys; sys.path.insert(0, 'ai/scripts')
import set_agents_app as app, coord_policy
print(app._validate_install_command('true & touch /tmp/set-agents-p5-f01-marker'))
print(coord_policy.allowed('python3 __SET_AGENTS_ROOT__/ai/scripts/set_agents_app.py --tools & touch /tmp/pwned'))
"
comando con caracteres no permitidos — solo se aceptan letras, números, espacios y - . / : = _ ~ @ + , | (allowlist, ADR-0038 §3)
False
```
(antes del arreglo devolvía `None` / `True` respectivamente — el review lo reprodujo end-to-end con un
archivo marcador real).

**Ambas direcciones (lo real de `tools.toml` sigue pasando)**:
```
$ python3 -c "
import sys; sys.path.insert(0, 'ai/scripts')
import set_agents_app as app
print(app._validate_install_command('curl -sSL https://sdk.cloud.google.com | bash'))
"
None
```

**Test de regresión**: `tests/test_harness.py::test_validate_install_command_rejects_a_bare_ampersand_shell_separator`,
`tests/test_harness.py::test_validate_install_command_rejects_control_characters`,
`tests/test_autonomy_policy.py::ToolsChannelPolicyTests::test_a_bare_ampersand_shell_separator_is_denied`
— escritos mirando la amenaza (qué hace `bash -c` con `&`/control chars), no la implementación anterior.

**Verificación real**:
```
$ python3 -m unittest discover -s tests -k "test_validate_install_command" -k "test_a_bare_ampersand_shell_separator_is_denied" -v
test_a_bare_ampersand_shell_separator_is_denied ... ok
test_validate_install_command_rejects_a_bare_ampersand_shell_separator ... ok
test_validate_install_command_rejects_control_characters ... ok
test_validate_install_command_rejects_privilege_escalators_by_resolved_basename ... ok
test_validate_install_command_rejects_sudo_and_hidden_pipes_but_allows_the_curated_shape ... ok
Ran 5 tests in 0.008s
OK
```

### F-03 (high) — rechazo de sudo era un regex de palabra suelta; escalador con path lo saltea

**Cambio**: `ai/scripts/set_agents_app.py` — nueva `_PRIVILEGE_ESCALATORS = frozenset({"sudo", "doas",
"pkexec", "su", "runas"})` y `_cmd_privilege_escalator(cmd)`: tokeniza con `shlex.split` y compara el
**basename** de cada token contra el denylist, en toda posición (no solo el primer token). Usado en
`_validate_install_command` (rechaza en propose/approve) y — **excepción de ownership aprobada por el
orquestador** (`ai/state/decisions-log.jsonl` slug `p5-repair-excepciones-y-diseno`) — en
`cmd_tools_install` (antes `command.startswith("sudo ")`, ahora `_cmd_privilege_escalator(command)`),
endureciendo la postura existente (sigue mostrando el comando completo y preguntando, aun con `--yes`) sin
relajar nada de su cuerpo.

**Reproducción del ataque, falla después del arreglo**:
```
$ python3 -c "
import sys; sys.path.insert(0, 'ai/scripts')
import set_agents_app as app
for cmd in ('/usr/bin/sudo apt install evil', 'doas apt install evil', 'pkexec apt install evil', 'su -c \"apt install evil\"'):
    print(cmd, '->', app._validate_install_command(cmd))
"
/usr/bin/sudo apt install evil -> 'sudo' no está permitido en un comando propuesto — la escalación de privilegios siempre queda manual
doas apt install evil -> 'doas' no está permitido en un comando propuesto — la escalación de privilegios siempre queda manual
pkexec apt install evil -> 'pkexec' no está permitido en un comando propuesto — la escalación de privilegios siempre queda manual
su -c "apt install evil" -> 'su' no está permitido en un comando propuesto — la escalación de privilegios siempre queda manual
```
(antes del arreglo los cuatro devolvían `None` — el review lo reprodujo en vivo).

**Ambas direcciones**: `npm install -g vercel` y `curl -sSL https://sdk.cloud.google.com | bash` siguen
devolviendo `None` (ver bloque de F-01 arriba, mismo comando).

**Test de regresión**: `tests/test_harness.py::test_validate_install_command_rejects_privilege_escalators_by_resolved_basename`
(ambas direcciones) y `tests/test_harness.py::test_cmd_tools_install_rejects_a_path_qualified_sudo_the_same_as_a_bare_one`
(la excepción de ownership sobre `cmd_tools_install`, verifica que sigue mostrando el comando completo y
preguntando en vez de correr nada).

**Verificación real**: ver el bloque de comandos de F-01 arriba — misma corrida cubre los 5 tests
(incluye estos dos).

### F-04 (high) — un salto de línea en `--why` destruía silenciosamente todo el catálogo local

**Cambio**: `ai/scripts/set_agents_app.py` — (1) `_toml_str` ahora escapa TODO carácter TOML-significativo
(`\\`, `"`, y los control chars con nombre `\b \t \n \f \r`, el resto vía `\uXXXX`), no solo `\\`/`"`; (2)
`cmd_tools_propose` rechaza `--why`/`--detect` que contengan cualquier carácter de control (`_CONTROL_CHAR_RE`),
fail-closed en el origen, no solo saneado en la escritura; (3) `_load_local_catalog` ya no traga el
`TOMLDecodeError`/`OSError` en silencio — imprime un `WARNING` a stderr con la ruta y la razón antes de
degradar a `{}` (la validación de forma completa —claves escalares, listas— es F-06, más abajo).

**Reproducción del ataque, falla después del arreglo**:
```
$ python3 -c "
import sys, tomllib; sys.path.insert(0, 'ai/scripts')
import set_agents_app as app
s = app._toml_str('a\nb')
print(repr(s))
print(tomllib.loads(f'x = {s}\n'))
"
'\"a\\\\nb\"'
{'x': 'a\nb'}
```
(antes del arreglo `_toml_str('a\nb')` devolvía `'"a\nb"'` — una basic string TOML sin terminar).

Y el rechazo en el origen:
```
$ python3 -c "
import sys, tempfile, shutil; from pathlib import Path
sys.path.insert(0, 'ai/scripts')
import set_agents_app as app
with tempfile.TemporaryDirectory() as td:
    root = Path(td) / 'root'; root.mkdir(); shutil.copy2('tools.toml', root / 'tools.toml')
    app.ROOT = root
    rc = app.cmd_tools_propose('newtool', 'cli', 'newtool-bin', 'npm', 'npm install -g newtool', 'linea1\nlinea2')
    print('rc=', rc, 'proposals.json existe:', (root / 'tools.proposals.json').exists())
"
TOOLS_PROPOSE_REJECTED newtool — --why no puede contener caracteres de control (saltos de línea, tabs, etc.) — usá un motivo de una sola línea
rc= 2 proposals.json existe: False
```
(antes del arreglo: `rc=0`, `TOOLS_PROPOSE_OK` impreso, y un approve posterior habría escrito el TOML roto).

**Test de regresión**: `tests/test_harness.py::test_toml_str_escapes_control_characters_instead_of_producing_a_broken_string`
(round-trip real contra `tomllib.loads`, varios control chars), `test_cmd_tools_propose_rejects_control_characters_in_why_and_detect_without_staging`
(fail-closed en el origen, nada queda en disco), `test_load_local_catalog_warns_instead_of_silently_swallowing_a_parse_error`
(el warning a stderr, no más silencio).

**Verificación real**:
```
$ python3 -m unittest discover -s tests -k "test_toml_str_escapes" -k "test_cmd_tools_propose_rejects_control_characters" -k "test_load_local_catalog_warns" -v
test_cmd_tools_propose_rejects_control_characters_in_why_and_detect_without_staging ... ok
test_load_local_catalog_warns_instead_of_silently_swallowing_a_parse_error ... ok
test_toml_str_escapes_control_characters_instead_of_producing_a_broken_string ... ok
Ran 3 tests in 0.005s
OK
```

### F-02 (critical) — el approve se ataba al NOMBRE, no a lo que el humano leyó

Reparado junto con F-05 (re-validación de todos los campos), F-10 (aviso mcp/skill) y F-12
(timeout/captura del subprocess de `log-decision`): las cuatro caen dentro de la misma función
`cmd_tools_approve`/`_log_tool_decision`, comparten causa y archivo (regla "repare juntos cuando comparten
archivo/causa" del skill de repair). Cada uno tiene su propio test y verificación abajo.

**Cambio**: `ai/scripts/set_agents_app.py:cmd_tools_approve` — variante elegida por el orquestador
(`ai/state/decisions-log.jsonl` slug `p5-repair-excepciones-y-diseno`): antes de escribir nada, **re-imprime
el bloque completo** de la propuesta (`kind`/`detect`/`install.<method>`/`why`) y exige **confirmación
interactiva** (`_safe_input` + `tui.suspend_terminal()`, mismo patrón que `cmd_tools_install` ya usa para
sudo), con la misma negativa sin TTY (`TOOLS_APPROVE_MANUAL`, `rc=1`, no escribe nada). La gramática de
`--tools-approve <name>` (solo el nombre, AC-31) no cambia — lo que cambia es qué pasa una vez que ese
nombre resuelve a una propuesta.

**Reproducción del ataque, falla después del arreglo** (payload swap en `tools.proposals.json` entre
propose y approve — el intercambio que el review reprodujo end-to-end):
```
$ python3 -m unittest discover -s tests -k "test_cmd_tools_approve_shows_a_tampered_payload_before_confirming" -v
test_cmd_tools_approve_shows_a_tampered_payload_before_confirming ... ok
Ran 1 test in 0.006s
OK
```
El test tampera `cmd`/`why` en el archivo de staging después de un `--tools-propose` legítimo y confirma
que el bloque re-impreso muestra el payload TAMPERADO completo antes de pedir confirmación (antes del
arreglo, el approve solo imprimía `TOOLS_APPROVE_OK {name} kind={kind}` — el humano nunca veía el swap).

**Test de regresión**: `test_cmd_tools_approve_full_round_trip_...` (actualizado: ahora simula
`isatty=True` + `input()->"y"`, y assertea que el bloque completo se re-imprime antes del `OK`),
`test_cmd_tools_approve_without_a_tty_refuses_and_writes_nothing`,
`test_cmd_tools_approve_declined_at_the_confirmation_writes_nothing`,
`test_cmd_tools_approve_shows_a_tampered_payload_before_confirming`.

**Verificación real**:
```
$ python3 -m unittest discover -s tests -k "test_cmd_tools_approve" -k "test_log_tool_decision" -v
test_cmd_tools_approve_declined_at_the_confirmation_writes_nothing ... ok
test_cmd_tools_approve_full_round_trip_reaches_load_catalog_and_tools_install ... ok
test_cmd_tools_approve_refuses_to_shadow_a_curated_name ... ok
test_cmd_tools_approve_revalidates_every_field_not_just_cmd_and_kind ... ok
test_cmd_tools_approve_shows_a_tampered_payload_before_confirming ... ok
test_cmd_tools_approve_warns_instead_of_suggesting_a_dead_tools_install_for_mcp_and_skill ... ok
test_cmd_tools_approve_without_a_pending_proposal_is_rejected ... ok
test_cmd_tools_approve_without_a_tty_refuses_and_writes_nothing ... ok
test_log_tool_decision_actually_runs_and_writes_the_real_decisions_log ... ok
test_log_tool_decision_warns_but_does_not_raise_on_a_nonzero_returncode ... ok
test_log_tool_decision_warns_on_timeout_without_raising ... ok
Ran 11 tests in 0.122s
OK
```

### F-05 (medium) — el approve solo re-validaba `cmd` y `kind`

**Cambio**: `ai/scripts/set_agents_app.py` — nueva `_validate_proposal(name, kind, detect, method, cmd,
why)`, factorizada de las validaciones que antes vivían solo en `cmd_tools_propose`. Usada por
`cmd_tools_propose` (input fresco) **y** `cmd_tools_approve` (re-chequeo de la copia staged, defensa en
profundidad contra `tools.proposals.json` editado a mano) — los dos caminos ya no pueden divergir.

**Test de regresión**: `test_cmd_tools_approve_revalidates_every_field_not_just_cmd_and_kind` — escribe
`tools.proposals.json` directamente (sin pasar por `cmd_tools_propose`) con un `method` inválido y con un
`detect` con carácter de control; ambos casos son rechazados por `cmd_tools_approve` antes de escribir
`tools.local.toml`. Verificación real: ver el bloque de F-02 arriba (misma corrida).

### F-10 (medium) — `kind=mcp`/`kind=skill` sugerían un `--tools-install` que no puede funcionar

**Cambio**: `ai/scripts/set_agents_app.py:cmd_tools_approve` — la cola del mensaje de éxito ahora
distingue por `kind`: para `cli` sigue sugiriendo `--tools-install <name>`; para `mcp`/`skill` imprime un
`NOTA:` explícito diciendo que la entrada queda catalogada pero sin instalación automática (ADR-0038 §7),
y **no** sugiere el comando que fallaría con `TOOL_UNKNOWN`.

**Test de regresión**: `test_cmd_tools_approve_warns_instead_of_suggesting_a_dead_tools_install_for_mcp_and_skill`
(ambos kinds, `mcp` y `skill`, vía `subTest`). Verificación real: ver el bloque de F-02 arriba.

### F-12 (low) — `log-decision` podía fallar/colgarse y el approve igual reportaba éxito

**Cambio**: `ai/scripts/set_agents_app.py:_log_tool_decision` — `timeout=30`, `capture_output=True,
text=True` (ya no hereda stdout: el JSON crudo de `feature-state.py` dejó de filtrarse a la salida de
`--tools-approve`), y un `returncode` no-cero o un `TimeoutExpired` se reportan como `WARNING` a stderr
(nunca hacen fallar `cmd_tools_approve`, cuyo catálogo ya quedó escrito).

**Test de regresión**: `test_log_tool_decision_warns_but_does_not_raise_on_a_nonzero_returncode`,
`test_log_tool_decision_warns_on_timeout_without_raising` (ambos mockean `subprocess.run` directamente,
sin parchear `_log_tool_decision`, así se ejercita el código real de manejo de error). Verificación real:
ver el bloque de F-02 arriba.

### F-08 (medium) — el deny explícito era evitable un flag más a la izquierda

**Cambio**: `ai/scripts/coord_policy.py` — nueva `_contains_tools_approve(argv)`, chequeada en `allowed()`
**antes** de `_argv_allowed`/`_tools_channel_allowed` (mismo lugar y disciplina que
`_transition_blocks_integration`): si `--tools-approve` aparece en cualquier posición del argv, se
deniega, sin importar qué entrada de `SAFE_ARGV` haya matcheado `argv[2]`. Es un guard **acotado a este
único flag** — el bug más general ("`modifiers=None` no inspecciona el resto del argv") es preexistente
(no introducido por P5) y no se toca acá, tal como indicó el orquestador; se repara solo para
`--tools-approve` porque toda la invariante de este paquete depende de que ese flag nunca sea alcanzable.

**Reproducción del ataque, falla después del arreglo**:
```
$ python3 -c "
import sys; sys.path.insert(0, 'ai/scripts')
import coord_policy
APP = '__SET_AGENTS_ROOT__/ai/scripts/set_agents_app.py'
print(coord_policy.allowed(f'python3 {APP} --routing-report --tools-approve foo'))
print(coord_policy.allowed(f'python3 {APP} --route-doctor --tools-approve foo'))
print(coord_policy.allowed(f'python3 {APP} --routing-report'))
"
False
False
True
```
(antes del arreglo las dos primeras devolvían `True` — el orquestador lo re-verificó en vivo antes de
asignar el repair; la tercera, una invocación de routing legítima sin nada colgando, sigue en `True`).

**Test de regresión**: `tests/test_autonomy_policy.py::ToolsProposeChannelPolicyTests::test_tools_approve_cannot_ride_along_a_routing_invocation`.

**Verificación real**:
```
$ python3 -m unittest tests.test_autonomy_policy -v
...
test_tools_approve_cannot_ride_along_a_routing_invocation ... ok
...
Ran 16 tests in 0.006s
OK
```
También corridos sin regresión: `test_integration_hook`, `claude_ask_guard`-relacionados (11 tests, ver
abajo) — el nuevo guard no afecta ninguna otra ruta de `allowed()`.
```
$ python3 -m unittest discover -s tests -k "coord_policy" -k "test_integration_hook" -k "claude_ask_guard"
Ran 11 tests in 6.110s
OK
```

### F-06 (medium) — el contrato never-fails era falso ante entrada bien formada pero de forma equivocada

**Cambio**: `ai/scripts/set_agents_app.py` — `_load_local_catalog` y `_read_tools_proposals` ahora validan
**forma** además de sintaxis: `isinstance(dict)` en cada nivel indexado (top-level, sección, entrada); todo
lo que no matchea `{kind: {name: {...}}}` (TOML) o no es un objeto JSON con valores-objeto (proposals) se
descarta en vez de crashear. `_read_tools_proposals` también atrapa `OSError`/`UnicodeDecodeError` ahora
(antes solo `OSError`/`JSONDecodeError` — ya cubría `OSError`, se agrega `UnicodeDecodeError` para
simetría con `_load_local_catalog`).

**Test de regresión**: `test_load_local_catalog_degrades_shape_mismatches_instead_of_crashing` (clave
escalar de nivel superior `oops = 1`, y entrada escalar de sección `[cli] x = 1`, ambos casos verificados
tanto en `_load_local_catalog` como en `load_catalog()` — el repro real que llegaba a `AttributeError`),
`test_read_tools_proposals_degrades_a_bare_json_list_instead_of_crashing` (lista JSON en vez de objeto,
y el `cmd_tools_approve` downstream que antes hubiera reventado).

**Verificación real**:
```
$ python3 -m unittest discover -s tests -k "test_load_local_catalog_degrades" -k "test_read_tools_proposals_degrades" -v
test_load_local_catalog_degrades_shape_mismatches_instead_of_crashing ... ok
test_read_tools_proposals_degrades_a_bare_json_list_instead_of_crashing ... ok
Ran 2 tests in 0.006s
OK
```
Corrida ampliada (todo lo de tools/coord_policy hasta ahora, sin regresión):
```
$ python3 -m unittest discover -s tests -k "tools" -k "test_log_tool_decision" -k "test_load_local_catalog" -k "test_read_tools_proposals" -k "test_validate_install_command"
Ran 54 tests in 2.963s
OK
```

### F-15 (low) — serialización de `tools.proposals.json` duplicada

**Cambio**: `ai/scripts/set_agents_app.py` — nueva `_save_tools_proposals(proposals)` (el mismo
`atomic_write` + `json.dumps(..., indent=2, sort_keys=True)` que antes vivía literal en
`_write_tools_proposal` y de nuevo, inline, en `cmd_tools_approve`). Ambos call sites (línea ~1344,
staging de una propuesta nueva, y línea ~1580, consumo/borrado tras un approve) llaman ahora a la misma
función — implementado como parte del mismo cluster de cambios que F-02/F-05/F-10/F-12 (comparten
`cmd_tools_approve`).

**Verificación**: `grep -n "_save_tools_proposals" ai/scripts/set_agents_app.py` muestra la definición
única y los dos call sites; no queda ningún `atomic_write(ROOT / "tools.proposals.json", ...)` fuera de
esa función. Cubierto transitivamente por toda la suite de `tools.proposals.json` (round-trip, tampering,
colisión) ya corrida arriba — un fallo en la extracción hubiera roto cualquiera de esos tests.

### F-09 (medium) — los tests de `cmd_tools_approve` mockeaban `_log_tool_decision` entera; el bug real
llegó a runtime, no a CI

**Nota (OBS-6, delta review round 2): esta sección faltaba en la evidencia original** — F-09 estaba
marcado "reparado" en la tabla de arriba y su test se corrió como parte del bloque de F-02 (línea ~221) y
se citó de nuevo en F-11, pero nunca tuvo su propia entrada cambio→verificación→test. Se completa acá,
sin reescribir lo que ya estaba (el hallazgo y su reparación son reales y ya estaban implementados; lo que
faltaba era la sección dedicada).

**Cambio**: ningún cambio de código de producción — F-09 es un hallazgo sobre COBERTURA de test, no sobre
comportamiento. Los tres tests originales de `cmd_tools_approve` (round-trip, sin TTY, declinado en la
confirmación) parcheaban `_log_tool_decision` por completo (`mock.patch.object(app,
"_log_tool_decision")`), así que la función real nunca corría en la suite — exactamente el punto ciego
que dejó pasar a runtime, en vez de a CI, el `AttributeError` de la primera versión de esta función (ver
la "Nota de implementación verificada en vivo" en `docs/adr/0038-tools-catalog-discovery.md` §1: el
primer intento importaba directo `feature_state_lib.cli_reporting.cmd_log_decision`, que revienta con
`AttributeError: module 'feature_state_lib.model' has no attribute 'render_notes'` fuera de un proceso que
corrió `feature-state.py` como `__main__`). La reparación es el test nuevo:
`tests/test_harness.py::test_log_tool_decision_actually_runs_and_writes_the_real_decisions_log`, que
invoca `_log_tool_decision` REAL (subprocess real a `feature-state.py`, sin mockear la función misma —
solo `ROOT` apunta a una raíz aislada) y assertea la entrada real que aparece en
`<ROOT>/ai/state/decisions-log.jsonl`.

**Verificación real**:
```
$ python3 -m unittest discover -s tests -k "test_log_tool_decision_actually_runs_and_writes_the_real_decisions_log" -v
test_log_tool_decision_actually_runs_and_writes_the_real_decisions_log ... ok
Ran 1 test in 0.090s
OK
```

**Test de regresión**: `test_log_tool_decision_actually_runs_and_writes_the_real_decisions_log` (el propio
fix — sin este test, un futuro cambio a `_log_tool_decision`/`feature-state.py log-decision` que rompa el
subprocess real seguiría en verde mientras todo lo demás siga mockeando la función).

### F-07 (medium) — la invariante "el approve no entra al canal del agente" solo rige para `coord-ro`

**Cambio**: (1) `ai/scripts/set_agents_app.py:cmd_tools_propose` — el mensaje impreso "Requiere una
persona -- un agente no puede correr esto (ADR-0038)" (afirmación técnica falsa para roles writer) pasa
a "el approve nunca es tuyo para correr, sea cual sea tu rol (ADR-0038 §2)" (norma doctrinal, no una
afirmación técnica universal). (2) `docs/adr/0038-tools-catalog-discovery.md` §2 — nuevo párrafo que
documenta qué clase de capability liga la restricción técnica (`coord-ro`, solo el orquestador) y por qué
los writers (implementer, cualquier lane: OpenCode `"*": allow` sin deny de `--tools-approve`, Codex
`workspace-write` no `read-only`, Pi sin policy) quedan fuera del alcance de cualquier allowlist de CLI —
se decide NO extender un deny técnico a los writers (cambio de diseño más amplio, fuera de este repair) y
se documenta como decisión explícita, no como omisión. (3) `docs/specs/019-harness-evolution/evidence/
P5-implementer.md` — la afirmación "nunca entra al canal del agente en ningún lane" (línea 273) recibe un
bloque de CORRECCIÓN explícito que la marca falsa y remite a esta reparación, en vez de reescribir la
evidencia histórica en silencio.

**Verificación real**:
```
$ python3 -c "
import sys, tempfile, shutil; from pathlib import Path
sys.path.insert(0, 'ai/scripts')
import set_agents_app as app
with tempfile.TemporaryDirectory() as td:
    root = Path(td) / 'root'; root.mkdir(); shutil.copy2('tools.toml', root / 'tools.toml')
    app.ROOT = root
    app.cmd_tools_propose('newtool', 'cli', 'newtool-bin', 'npm', 'npm install -g newtool', 'motivo')
" 2>&1 | tail -3
Requiere una persona -- el approve nunca es tuyo para correr, sea cual sea tu rol
(ADR-0038 §2). Para aprobar:
  python3 ai/scripts/set_agents_app.py --tools-approve newtool
```
Doctrina y evidencia verificadas por `grep`:
```
$ grep -n "capability.*coord-ro\|CORRECCIÓN (repair, F-07" docs/adr/0038-tools-catalog-discovery.md docs/specs/019-harness-evolution/evidence/P5-implementer.md
docs/adr/0038-tools-catalog-discovery.md:106:**Qué clase de capability liga esta restricción, y por qué (reparación F-07)**. Todo lo de arriba —
docs/specs/019-harness-evolution/evidence/P5-implementer.md:279:  **CORRECCIÓN (repair, F-07, ver `P5-repair.md`)**: la afirmación de arriba es FALSA para roles writer.
```
Suite de doctrina, sin regresión (ya corrida arriba, ver F-08/F-14): `test_tool_catalog_doctrine_covers_the_open_catalog_flow ... ok`.

### F-11 (medium) — el catálogo es por clon del harness, no per-project; el log de decisiones por CWD

**Cambio**: (1) `.gitignore:40-45` — comentario corregido, ya no dice "per-project" (falso). (2)
`docs/adr/0038-tools-catalog-discovery.md` §2 — nuevo párrafo documentando el alcance real (harness-global,
defendible, misma granularidad que `tools.toml` curado) y corrigiendo "Consecuencias" (que también decía
"por proyecto"). (3) `ai/scripts/set_agents_app.py:_log_tool_decision` — `cwd=str(ROOT)` explícito en el
subprocess de `log-decision` (antes heredaba el CWD del proceso llamador, inconsistente con el catálogo
que siempre vive en `ROOT`) — **código, no solo documentación**: hace consistentes los dos artefactos, tal
como pedía el finding. No se rediseñó a per-project (excluido explícitamente por el orquestador).

**Verificación real**: el mismo test real de F-09 (`test_log_tool_decision_actually_runs_and_writes_the_real_decisions_log`)
prueba esto directamente — `ROOT` mockeado a un directorio temporal, y la entrada aparece en
`<ROOT>/ai/state/decisions-log.jsonl`, no en el CWD real del proceso de test:
```
$ python3 -m unittest discover -s tests -k "test_log_tool_decision_actually_runs" -v
test_log_tool_decision_actually_runs_and_writes_the_real_decisions_log ... ok
Ran 1 test in 0.092s
OK
```

### F-13 (low) — el guard de AC-34 es un substring, no un mecanismo

**Cambio**: documentación únicamente, tal como pide el finding (no se endurece el regex — endurecerlo no
cerraría la brecha real). `docs/adr/0038-tools-catalog-discovery.md` §7 — nuevo párrafo "Qué es este guard,
honestamente": describe `_CANONICAL_TARGET_RE` como un alambre de aviso para el caso literal obvio, y
aclara que la contención real hoy es la AUSENCIA de instalador de skills, no el regex; si algún día se
construye uno, la contención real tendría que ser un chequeo de path resuelto en tiempo de instalación.
De paso (mejora trivial, sin cambiar el criterio de fondo): el regex pasó a case-insensitive
(`re.IGNORECASE`) para no perder el caso obvio `GLOBAL/_CANONICAL`.

**Verificación**: `grep -n "alambre de aviso" docs/adr/0038-tools-catalog-discovery.md` confirma el
párrafo. Cubierto por el test ya existente (`test_validate_install_command_rejects_sudo_and_hidden_pipes_but_allows_the_curated_shape`,
caso `Global/_canonical/skills/...`), que sigue en verde tras el `re.IGNORECASE` (ver corrida de F-01/F-03
arriba).

### F-14 (low) — los dos verbos no aparecen en `--help`; la doctrina prometía un canal inexistente

**Cambio**: (1) `ai/scripts/set_agents_app.py:main` — el `epilog` del parser ahora menciona
`--tools-propose`/`--tools-approve` en prosa (nunca como argumentos reales de `argparse`, para no
reabrir F-08). (2) `Global/_canonical/agents/orchestrator.md` — el bullet que decía "Only the user, or
you after their explicit yes and on your own separate channel, ever runs `--tools-approve`" (promete un
canal que no existe: `coord_policy` lo niega siempre) se reescribe a "Only the user ever runs
`--tools-approve` — hand them the exact command; you never run it yourself... there is no 'separate
channel'". Regenerado a los 4 árboles con `./build.sh`.

**Verificación real**:
```
$ python3 ai/scripts/set_agents_app.py --help 2>&1 | tail -6
Primera vez: leé README.md — explica qué vas a ver según tu sistema operativo.
Dos verbos más (ADR-0038, interceptados antes de este parser, no listados
arriba): --tools-propose <name> --kind cli|mcp|skill --detect <bin>
--install-<method> "<cmd>" --why "<motivo>" (valida y imprime la pregunta
consolidada, nunca instala) y --tools-approve <name> (la aprobación humana --
nunca la corre un agente, sea cual sea su rol).
```
**Test de regresión**: `test_help_epilog_documents_the_two_intercepted_tools_verbs` (invoca `--help` real,
captura el `SystemExit` de argparse), y `test_tool_catalog_doctrine_covers_the_open_catalog_flow` extendido
con dos asserts nuevos (la frase vieja "after their explicit yes and on your own separate channel" no
está más; "never run it yourself" sí).
```
$ python3 -m unittest discover -s tests -k "test_help_epilog" -k "test_tool_catalog_doctrine" -v
test_tool_catalog_doctrine_covers_the_open_catalog_flow ... ok
test_help_epilog_documents_the_two_intercepted_tools_verbs ... ok
Ran 2 tests in 0.004s
OK
```
`./build.sh` / `./build.sh --check` re-corridos tras el cambio a `Global/_canonical/agents/orchestrator.md`
— sin drift (ver la corrida completa de gates de esta ronda más abajo).

## Gates (ronda 1)

**Nota (OBS-6, delta review round 2): esta sección faltaba** — la línea de arriba remitía a "el bloque de
gates al final de este archivo", que nunca existió. Se completa acá con la corrida real de gates de la
ronda 1 (`build.sh`/`build.sh --check` tras el cambio de F-14 a `orchestrator.md`); la corrida de gates de
la RONDA 2 (los dos findings de esta reparación: NEW-01 y F-06 reabierto) vive en su propio archivo,
`docs/specs/019-harness-evolution/evidence/P5-repair-2.md`, sección "Gates (ronda 2)".

```
$ ./build.sh
CHECK_PASS: generated and validated profile go-zen
Generated tracked artifacts for go-zen.

$ ./build.sh --check
CHECK_PASS: generated and validated profile go-zen
SELF_SCAFFOLD_SYNC_OK files=2
```

(Corrida en la ronda 2, sobre el árbol de trabajo actual — que sigue conteniendo el cambio de F-14 a
`Global/_canonical/agents/orchestrator.md` sin modificar desde entonces — así que confirma retroactivamente
que ese cambio de ronda 1 nunca generó drift.)
