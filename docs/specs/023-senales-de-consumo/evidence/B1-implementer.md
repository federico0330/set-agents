# Evidencia — B1-registro-que-no-miente (implementer)

Estado: COMPLETO

## Tabla AC -> cambio -> prueba

| AC | Cambio (archivo:línea) | Prueba |
|---|---|---|
| AC-01 | `Global/_canonical/agents/orchestrator.md:315-351` (paso 8 nuevo, imperativo, comando `--route-terminal ... --usage '...'` pegado literal por runtime: Claude Code, OpenCode, Codex, Pi). Propagado por `./build.sh` a `Global/{claude-code,opencode,pi}/agents/orchestrator.md` y `Global/codex/agents/orchestrator.toml`. | `tests/test_harness.py::HarnessTests::test_orchestrator_doctrine_demands_usage_on_every_direct_route_terminal_close` — grepea los cuatro comandos pegados y las claves `ADR-0045`/`routing_core/usage.py` en las cuatro copias generadas. Mordida/rojo/revert documentado abajo. |
| AC-02 | `ai/scripts/routing_core/usage.py` (nuevo, 196 líneas): `normalize_pi`/`normalize_claude_code`/`normalize_opencode`/`normalize_codex` + `normalize(runtime, raw)`, con la muestra real de cable por runtime pegada en el docstring del módulo. `ai/scripts/routing_core/store.py:150-160,188-198` (`_usage_row` endurecido: un dict no vacío sin ningún campo reconocido pasa a `invalid`; docstring extendido citando ADR-0045). | `tests/test_routing.py::RoutingTests::test_usage_row_nonempty_unrecognized_dict_is_invalid_not_ok`, `test_usage_row_absent_vs_invalid_boundary_is_emptiness_not_recognition`, `test_usage_row_still_ok_for_every_previously_valid_sparse_shape`, `test_usage_normalize_*` (4 normalizadores + propagación + dispatch table). Mordida/rojo/revert documentado abajo. |
| AC-03 | Mismos tests de arriba (columnas no-NULL por runtime) + `tests/test_routing.py::RoutingTests::test_report_status_counts_before_and_after_on_a_fixture_store_per_runtime` (`store.report()["tokens"]["status_counts"]` antes y después, sobre un `RoutingStore` de fixture, cerrando un run real por cada uno de los 4 runtimes + un `absent` genuino + un `invalid` genuino). | Mismo archivo, corrida y mordida documentadas abajo. |

`docs/adr/0045-consumo-vocabulario-en-el-borde.md` (nuevo) + `docs/adr/README.md` (índice, fila 0045).

## La muestra real del cable por runtime

Medidas en vivo el 2026-08-13, con el modelo más barato alcanzable y un prompt de una palabra. Comandos y capturas completas (sin recortar) — también citadas en el docstring de `ai/scripts/routing_core/usage.py`:

**pi** — ya medido y citado en `store.py:111-118` (spawn real, 2026-07-29), reusado tal cual, no remedido en esta sesión:
```
{"input":3321,"output":5,"reasoning":0,"totalTokens":3326,"cacheRead":0,"cacheWrite":0,"cost":{...}}
```

**claude-code** — `claude --print --model haiku --output-format json --no-session-persistence "Reply with exactly one word: hi"`:
```
{"is_error":false,"duration_api_ms":2199,"num_turns":1,"stop_reason":"end_turn","session_id":"209fc52b-730b-451a-a356-fa438d513596","total_cost_usd":0.027181100000000003,"usage":{"input_tokens":10,"cache_creation_input_tokens":12573,"cache_read_input_tokens":18101,"output_tokens":43,"output_tokens_details":{"thinking_tokens":36},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_tokens":12573,"ephemeral_5m_input_tokens":0},"inference_geo":"not_available","iterations":[{"input_tokens":10,"output_tokens":43,"cache_read_input_tokens":18101,"cache_creation_input_tokens":12573,"cache_creation":{"ephemeral_5m_input_tokens":0,"ephemeral_1h_input_tokens":12573},"type":"message"}],"speed":"standard"},"modelUsage":{"claude-haiku-4-5-20251001":{"inputTokens":10,"outputTokens":43,"cacheReadInputTokens":18101,"cacheCreationInputTokens":12573,"webSearchRequests":0,"costUSD":0.027181100000000003,"contextWindow":200000,"maxOutputTokens":32000,"canonicalModel":"claude-haiku-4-5","provider":"firstParty"}},"permission_denials":[],"terminal_reason":"completed","fast_mode_state":"off","fast_mode_disabled_reason":"sdk_opt_in_required","subtype":"success","api_error_status":null,"result":"hi","ttft_ms":2130,"ttft_stream_ms":1764,"time_to_request_ms":51,"type":"result","duration_ms":2260,"uuid":"ca336fd7-47b6-41fd-bf39-51e5ed9c4284"}
```
La forma que `claude_code_spawn.py:452-457` ya extrae de esto (`total_cost_usd` + `modelUsage`) es lo que `normalize_claude_code`/la doctrina traducen. `reasoning`/`totalTokens` quedan **sin mapear**: no hay campo de razonamiento en `modelUsage`, y no hay un total independiente contra el cual verificar una suma derivada — marcado explícitamente en el docstring, no supuesto.

**opencode** — `opencode run -m opencode/nemotron-3.5-lightning-free --format json "Reply with exactly one word: hi"` (el `step_finish` final, evento JSONL completo):
```
{"type":"step_finish","timestamp":1786635846012,"sessionID":"ses_00434aaedffeVgUMyoz3YBfTL7","part":{"id":"prt_ffbcb816d001v7CnW0QpKaCrN6","reason":"stop","snapshot":"1e1b8da4d54e934faee260b3ea3746478e2a46ec","messageID":"msg_ffbcb5e80001OUZEZtfe1WD98Q","sessionID":"ses_00434aaedffeVgUMyoz3YBfTL7","type":"step-finish","tokens":{"total":30493,"input":30322,"output":0,"reasoning":197,"cache":{"write":0,"read":0}},"cost":0}}
```
Medido: `tokens.total` (30493) **no** es igual a la suma de `input+output+reasoning+cache.read+cache.write` (30519) — por eso `normalize_opencode` nunca produce `totalTokens`: pasarlo tal cual haría que `_usage_row` descarte el reporte como `invalid` por el chequeo de suma. Este es el hallazgo medido que motiva esa decisión, no una suposición.

**codex** — `codex exec --ephemeral --sandbox read-only --color never --skip-git-repo-check -m gpt-5.6-luna -c model_reasoning_effort=low --json "Reply with exactly one word: hi"` (stream completo):
```
{"type":"thread.started","thread_id":"019ffbce-a676-7363-82b2-04ea4deab13d"}
{"type":"turn.started"}
{"type":"item.completed","item":{"id":"item_0","type":"agent_message","text":"hi"}}
{"type":"turn.completed","usage":{"input_tokens":16057,"cached_input_tokens":8960,"cache_write_input_tokens":0,"output_tokens":5,"reasoning_output_tokens":0}}
```
`cached_input_tokens`/`cache_write_input_tokens` quedan **sin verificar y sin mapear**: no hay referencia de esquema consultada esta sesión, y la única muestra en vivo no desambigua si son aditivos a `input_tokens` o ya están incluidos en él. No hay `cost` en ningún punto de este stream. También se confirma en vivo que `codex_spawn.py` no adjunta `--usage` en absoluto hoy (hallazgo colateral, nombrado en el ADR, fuera de `ALCANCE`).

Ningún runtime quedó "sin verificar" en su totalidad — cada uno tiene al menos `input`/`output` mapeados con confianza; los campos individuales sin verificar están nombrados explícitamente arriba, en el ADR y en el docstring del módulo (nunca supuestos).

## `status_counts` antes y después (store de fixture)

`tests/test_routing.py::RoutingTests::test_report_status_counts_before_and_after_on_a_fixture_store_per_runtime`:
- **Antes** (store recién creado, ningún run cerrado): `svc.store.report()["tokens"]["status_counts"] == {}`.
- Se autorizan y despachan 5 runs (mismo rol/runtime `implementer`/`codex` — sólo importa el `usage_status`, no la ruta): se cierran con `usage=normalize_claude_code(muestra)`, `normalize_opencode(muestra)`, `normalize_codex(muestra)` (3 × `ok`), un cierre con `usage=None` sobre un run genuinamente nunca reportado (1 × `absent`), y un cierre con un dict no vacío sin campos reconocidos, `{"junk": 1}` (1 × `invalid`).
- **Después**: `status_counts == {"ok": 3, "absent": 1, "invalid": 1}` — confirmado, corrida real más abajo (`Ran 1092 tests ... OK`).

## La prueba de que un `absent` legítimo sigue siendo `absent`

- `test_usage_row_treats_missing_or_empty_usage_as_absent_not_invalid` (test PREEXISTENTE, no tocado) sigue verde: `_usage_row(None)` y `_usage_row({})` siguen devolviendo `(None,None,None,None,None,None,"absent")`.
- `test_usage_row_absent_vs_invalid_boundary_is_emptiness_not_recognition` (nuevo, este paquete): pone los dos casos lado a lado en el mismo test — `_usage_row({})` → `absent`, `_usage_row({"anything": 1})` → `invalid` — para que un futuro edit que fusione las dos ramas se note ahí mismo, no sólo en tests separados.
- `test_usage_normalize_genuinely_empty_input_stays_absent` (nuevo): los 4 normalizadores, ante `{}`/`None`, devuelven `{}`, y `_usage_row({})` sigue siendo `absent` — el traductor nuevo no cambia esa frontera.
- `test_close_run_records_absent_when_no_usage_is_given` y `test_close_run_forces_absent_on_abandon_regardless_of_usage_passed` (PREEXISTENTES, no tocados) siguen verdes con el endurecimiento de `_usage_row` aplicado — el abandono sigue forzando `absent` sin importar qué se pase.

## Tests nuevos: neutralizar -> rojo -> revertir -> pegar prueba

Backups vía `cp` (nunca `git checkout`/`stash`) a
`/var/tmp/claude/claude-1000/-home-federico-SET-AGENTES/d40ea0e0-c4b6-4bd0-a488-a584f10bc6c4/scratchpad/backup/{store.py,usage.py,orchestrator.md}.bak`.

**1) `_usage_row` (AC-02/AC-03).** Se removió el bloque
```python
if not tokens and total_tokens is None and "cost" not in usage:
    return all_null + ("invalid",)
```
dejando el `return ... "ok"` original. Corridos los 4 tests que dependen de él:
```
FAIL: test_usage_row_nonempty_unrecognized_dict_is_invalid_not_ok
  AssertionError: Tuples differ: (None, None, None, None, None, None, 'ok') != (..., 'invalid')
FAIL: test_usage_row_absent_vs_invalid_boundary_is_emptiness_not_recognition
  AssertionError: (..., 'ok') != (..., 'invalid') : {'anything': 1}
FAIL: test_usage_normalize_propagates_unrecognized_nonempty_input_as_invalid
  AssertionError: 'ok' != 'invalid' : {'modelUsage': {'m': {'someWeirdField': 5}}}
FAIL: test_report_status_counts_before_and_after_on_a_fixture_store_per_runtime
  AssertionError: {'absent': 1, 'ok': 4} != {'ok': 3, 'absent': 1, 'invalid': 1}
Ran 4 tests in 0.496s
FAILED (failures=4)
```
Revertido con `cp` desde el backup; `diff` contra el backup, idéntico. Los 11 tests nuevos vuelven a `OK` (ver corrida abajo).

**2) `usage.py` (AC-02/AC-03).** Se insertó `return {}  # NEUTRALIZED` como primera línea ejecutable de las 4 funciones `normalize_*`, antes de su lógica real. Corridos los 8 tests que dependen de ellas:
```
FAIL: test_usage_normalize_claude_code_real_sample_yields_nonnull_columns  -- {} != {'input': 10, ...}
FAIL: test_usage_normalize_opencode_real_sample_yields_nonnull_columns    -- {} != {'input': 30322, ...}
FAIL: test_usage_normalize_codex_real_sample_yields_nonnull_columns       -- {} != {'input': 16057, ...}
FAIL: test_usage_normalize_pi_is_identity_and_still_ok                   -- {} != {'input': 3321, ...}
FAIL: test_usage_normalize_propagates_unrecognized_nonempty_input_as_invalid -- {} is not true
FAIL: test_report_status_counts_before_and_after_on_a_fixture_store_per_runtime
  AssertionError: {'absent': 4, 'invalid': 1} != {'ok': 3, 'absent': 1, 'invalid': 1}
Ran 8 tests in 0.531s
FAILED (failures=6)
```
(los otros 2 de los 8 -- `test_usage_normalize_genuinely_empty_input_stays_absent` y `..._dispatch_table_covers_all_four_runtimes` -- pasan igual porque prueban el caso vacío/la tabla de despacho, no afectados por la neutralización). Revertido con `cp`; `diff` contra el backup, idéntico.

**3) Doctrina del orquestador (AC-01).** Se removió el paso 8 completo (`8. **Usage travels...**` hasta antes de `### Decide siempre`, 3909 caracteres) de `Global/_canonical/agents/orchestrator.md`, se corrió `./build.sh` para propagar la mordida a las 4 copias generadas, y se corrió el test de doctrina:
```
FAIL: test_orchestrator_doctrine_demands_usage_on_every_direct_route_terminal_close
  AssertionError: 'ADR-0045' not found in '---\nname: orchestrator\n...'
```
Revertido con `cp` desde el backup; `diff` contra el backup, idéntico. Se corrió `./build.sh` de nuevo (`CHECK_PASS`) y `./build.sh --check` (`BUILD_CHECK_PASS`) para confirmar que la reversión dejó el árbol generado exactamente como estaba, y el test de doctrina vuelve a `OK`.

Corrida verde de los 12 tests nuevos, todos juntos, tras cada reversión (última corrida, la definitiva, es la suite completa de abajo):
```
test_usage_row_nonempty_unrecognized_dict_is_invalid_not_ok ... ok
test_usage_row_absent_vs_invalid_boundary_is_emptiness_not_recognition ... ok
test_usage_row_still_ok_for_every_previously_valid_sparse_shape ... ok
test_usage_normalize_claude_code_real_sample_yields_nonnull_columns ... ok
test_usage_normalize_opencode_real_sample_yields_nonnull_columns ... ok
test_usage_normalize_codex_real_sample_yields_nonnull_columns ... ok
test_usage_normalize_pi_is_identity_and_still_ok ... ok
test_usage_normalize_propagates_unrecognized_nonempty_input_as_invalid ... ok
test_usage_normalize_genuinely_empty_input_stays_absent ... ok
test_usage_normalize_dispatch_table_covers_all_four_runtimes ... ok
test_report_status_counts_before_and_after_on_a_fixture_store_per_runtime ... ok
Ran 11 tests in 0.528s
OK
test_orchestrator_doctrine_demands_usage_on_every_direct_route_terminal_close ... ok
Ran 1 test in 0.555s
OK
```

## Gates (literales)

`ai/scripts/heartbeat-run.py --interval 20 -- python3 -m unittest discover -s tests` (corrida final, log completo en
`/var/tmp/claude/claude-1000/-home-federico-SET-AGENTES/d40ea0e0-c4b6-4bd0-a488-a584f10bc6c4/scratchpad/unittest_full.log`):
```
----------------------------------------------------------------------
Ran 1092 tests in 731.824s

OK (skipped=3)
```
(1080 base + 12 nuevos = 1092; 3 skips, igual que la base — ninguno nuevo).

`ai/scripts/heartbeat-run.py --interval 20 -- ./ai/scripts/verify.sh` (log completo en
`/var/tmp/claude/claude-1000/-home-federico-SET-AGENTES/d40ea0e0-c4b6-4bd0-a488-a584f10bc6c4/scratchpad/verify.log`):
```
GLOBAL_TREE_SYNC_OK profile=go-zen harnesses=4
BUILD_CHECK_PASS
...
Ran 1092 tests in 739.322s

OK (skipped=3)
...
GLOBAL_PORTABILITY_OK
CANONICAL_PATHS_OK
FEATURE_STATE_OK
VERIFY_PASS
```

`./build.sh && ./build.sh --check` (corrida final post-reversión):
```
CHECK_PASS: generated and validated profile go-zen
Generated tracked artifacts for go-zen.
SELF_SCAFFOLD_SYNC_OK files=2
GLOBAL_TREE_SYNC_OK profile=go-zen harnesses=4
BUILD_CHECK_PASS
```

`git diff --check` (archivos tocados por este paquete): sin salida, exit 0.

## Alcance tocado (exacto)

`Global/_canonical/agents/orchestrator.md` (+ los 4 árboles `Global/{claude-code,opencode,codex,pi}/agents/orchestrator.*` regenerados por `./build.sh`, ningún otro archivo de `Global/` cambió — verificado con `git status --porcelain | grep '^ M Global/'`, exactamente 5 líneas) · `ai/scripts/routing_core/usage.py` (nuevo) · `ai/scripts/routing_core/store.py` · `docs/adr/0045-consumo-vocabulario-en-el-borde.md` (nuevo) · `docs/adr/README.md` · `tests/test_routing.py` · `tests/test_harness.py`.

`ai/scripts/set_agents_app.py` estaba habilitado por `ALCANCE` pero **no se tocó**: `cmd_route_terminal`/`parse_usage` ya funcionan correctamente para el vocabulario plano tal como está (verificado con los tests preexistentes `test_route_terminal_usage_flows_from_the_cli_into_the_stored_row` y `test_route_terminal_large_but_valid_usage_still_closes_the_run`, ambos siguen verdes); no hacía falta ningún cambio ahí para que AC-01/AC-02/AC-03 queden satisfechos.

## Hallazgo fuera de alcance, nombrado para el futuro (no reparado aquí)

`claude_code_spawn.py:602-605` y `opencode_spawn.py:318-321` ya intentan adjuntar `--usage` automáticamente en sus rutas de dispatch, pero en una forma que `_usage_row` no reconoce (`{"total_cost_usd":..., "modelUsage":{...}}` y `{"tokens":{...}}` respectivamente — ninguna con las claves planas que `_usage_row` valida). Documentado en `docs/adr/0045-consumo-vocabulario-en-el-borde.md` §Contexto y §Decisión-2, con la recomendación explícita de que un futuro paquete (candidato: B2) importe `ai/scripts/routing_core/usage.py` para cerrarlo, en vez de re-derivar el mapeo. Ninguno de esos tres archivos está en el `ALCANCE` de B1, así que no se tocaron.
