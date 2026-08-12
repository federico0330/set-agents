# P1-provider-auto-adoption — evidencia de reparación (repair-agent)

Review previa: PASS_CON_HALLAZGOS. Se repararon 4 hallazgos (F-01, F-03, F-04, F-05) en una sola
pasada; F-06 ya estaba resuelto por el orquestador, fuera de este scope.

**F-02** se reasignó primero a P2 y luego volvió a P1 (el hallazgo se repara en el paquete que lo
levantó — ver `ai/state/decisions-log.jsonl`). Reparado en una pasada separada, bajo excepción de
ownership aprobada que habilita tocar exclusivamente `[catalog].opencode_zen`/`opencode_go` y su
comentario en `models.toml` (fuera de los owned_paths normales de este paquete).

## Tabla hallazgo → cambio → verificación

| Hallazgo | Archivo:línea | Cambio | Verificación |
|---|---|---|---|
| **F-02** (medio) — `[catalog].opencode_zen`/`opencode_go` medidas 2026-07-30 y desactualizadas; `_configured_models` (`ai/scripts/routing_core/catalog.py:157`) intersecta el probe contra ese techo, así que `discovered_providers = "auto"` (ADR-0034) no podía routear modelos vivos ausentes de la lista | `models.toml:16-27` (comentario + ambas listas) | Re-medición en vivo 2026-08-10 (`opencode models opencode --pure` → 60 ids; `opencode models opencode-go --pure` → 18 ids), reemplazando ambas listas por lo medido (ordenadas, formato/convención sin cambios). Cambios de contenido: `opencode_zen` pierde `claude-opus-4-1` (ya no listado) y `ling-3.0-flash-free` (renombrado a `ling-3.0-tiny-free`), gana `longcat-2.0-free`; `opencode_go` gana `gpt-5.6-luna` y `qwen3.8-max`. Comentario reescrito: la fecha pasa a 2026-08-10 y se corrige la afirmación ya falsa de "probeable only… NOT routable… all four selectability gates, none opened here" — ahora describe que ADR-0034 abrió `"auto"` sobre este mismo techo auditado (`resolve_discovered_providers` nunca lo excede) y que la vía curada (`routes.v1.toml`/`enabled_providers`/`ROUTING_PROVIDERS`) sigue cerrada. Ningún otro campo de `models.toml` tocado (confirmado con `git diff models.toml`, ver reporte del repair-agent). No se omitió ningún id vivo: las 60+18 ids medidas entran completas, sin exclusión de riesgo. | `git diff models.toml` acotado a esas líneas; round-trip `load_config → emit → load_config` estable (`cfg1 == cfg2` y `emit(cfg1) == emit(cfg2)`); `python3 -m unittest tests.test_routing` → `OK` (248 tests); `./build.sh --check` → `CHECK_PASS`; `git diff --check` limpio; en vivo `--route-decide --fresh-probes` para `implementer/opencode`: pool pasa de 22 candidatos/21 exclusiones (medición previa) a 25 candidatos/24 exclusiones (todas `TIER_INSUFFICIENT`, ganador sin cambios: `openai-codex/gpt-5.6-sol`, `independence_verified=false` sin cambios) — el `auto` ahora ve 3 candidatos adicionales que el techo viejo excluía. |
| **F-01** (medio) — falta test positivo del beneficio-titular AC-02/AC-06 (un escenario `REVIEWER_INDEPENDENCE_UNAVAILABLE` se resuelve con provider descubierto) | `tests/test_routing.py:3663` `test_adr0034_ac02_ac06_discovered_reviewer_resolves_reviewer_independence_unavailable`; `tests/test_routing.py:3738` `test_adr0034_ac06_same_vendor_stem_inferred_reviewer_never_serves_a_same_stem_writer` | Dos tests nuevos, seam hermético `RoutingService._for_tests`: (a) writer curado `openai-codex/gpt-5.6-sol` + único candidato curado en conflicto (mismo family/provider) → sin discovery, `REVIEWER_INDEPENDENCE_UNAVAILABLE` (reproduce el halt real); con discovery, reviewer inferido `opencode-zen/kimi-k3` seleccionado (`independence_verified=True`, `MODEL_METADATA_INFERRED tier=balanced family=kimi-k3` en `reason_codes`) y su hermano inferido `opencode-zen/gpt-5.1-codex` excluido por `REVIEW_FAMILY_CONFLICT` (mismo stem `gpt` que el writer); (b) caso negativo simétrico del spec: zen `claude-3-tiny` inferido NUNCA revisa a un writer `anthropic/opus` (mismo stem `claude`) → `REVIEWER_INDEPENDENCE_UNAVAILABLE` + exclusión `REVIEW_FAMILY_CONFLICT` sobre la ruta inferida. | `python3 -m unittest tests.test_routing.RoutingTests.test_adr0034_ac02_ac06_discovered_reviewer_resolves_reviewer_independence_unavailable tests.test_routing.RoutingTests.test_adr0034_ac06_same_vendor_stem_inferred_reviewer_never_serves_a_same_stem_writer -v` → `OK` (ver salida abajo). |
| **F-03** (bajo) — `occurrences` calculado y nunca asserteado en `test_adr0034_ac02_...`; el literal buscado no matchea la llamada real del `recheck` | `tests/test_routing.py:3594-3608` (dentro de `test_adr0034_ac02_composition_and_recheck_derive_discovery_through_the_same_path`) | Se eliminó la variable muerta `occurrences` (el literal multilínea que buscaba nunca aparece en el código real, así que la aserción decorativa nunca hubiera fallado ni pasado de verdad). En su lugar se agregó una aserción real: `build_snapshot(catalog_path, roster, config), frozenset()` aparece **exactamente una vez** en `service.py` y esa única aparición vive dentro de la rama `else:` de `discovery_configured` (verificado con `source.split("        else:\n", 1)[1]`, único `else:` a esa indentación en el archivo — confirmado con grep). | `python3 -m unittest tests.test_routing.RoutingTests.test_adr0034_ac02_composition_and_recheck_derive_discovery_through_the_same_path -v` → `OK`. |
| **F-04** (bajo) — el candidato descartado por el reprobe no deja rastro (ni exclusión ni reason code) | `ai/scripts/routing_core/service.py:454-465` (bloque de reprobe rejection dentro de `route()`); ADR actualizado en `docs/adr/0034-auto-adopted-providers.md` punto 8 | Se agrega `exclusions.append({"route_id": selected.route_id, "reason": f"REPROBE_REJECTED {selected.provider}/{selected.model}"})` justo antes de `candidates = candidates[1:]` — aditivo puro, misma disciplina que `RUNTIME_REDIRECTED`/`MODEL_PIN_UNAVAILABLE`: nunca reemplaza/reordena un código existente, nunca cambia `success`/`runtime`/`identity`/`fallback`. Test nuevo `tests/test_routing.py:3805` `test_adr0034_f04_repair_reprobe_rejection_leaves_an_exclusion_trace`, sobre el mismo fixture del test AC-08 existente: la decisión ganadora sigue siendo `gpt-5.6-sol` (candidato no top-ranked) y ahora `decision.exclusions` contiene `{"route_id": <route de gpt-5.6-luna>, "reason": "REPROBE_REJECTED openai-codex/gpt-5.6-luna"}`. | `python3 -m unittest tests.test_routing.RoutingTests.test_adr0034_f04_repair_reprobe_rejection_leaves_an_exclusion_trace tests.test_routing.RoutingTests.test_adr0034_ac08_reprobe_rejection_reranks_to_the_next_candidate -v` → `OK` (el test AC-08 preexistente sigue verde sin modificarse). |
| **F-05** (bajo) — `_effective_preference_providers()` prueba subprocess (hasta 20s por comando) en cada `--model-pin-set`/`--model-preference-set` para una unión que hoy es un no-op demostrable (`live ⊆ DISCOVERABLE_PROVIDERS == _MODEL_PREFERENCE_PROVIDERS`, AC-10 lockstep) | `ai/scripts/set_agents_app.py:111-142` (`_effective_preference_providers`, docstring y corto-circuito en `:137-138`) | Corto-circuito barato antes del probe: `if set(models_config.DISCOVERABLE_PROVIDERS) <= set(_MODEL_PREFERENCE_PROVIDERS): return _MODEL_PREFERENCE_PROVIDERS`. Docstring actualizado explicando que la unión solo tiene efecto observable el día que `_PAIR_COMMANDS` (vía `DISCOVERABLE_PROVIDERS`) supere al set base — hoy no lo hace. No cambia ningún comportamiento de validación observable (los tests AC-09 preexistentes, que mockean `_effective_preference_providers` directamente o pasan `valid_providers` explícito, siguen verdes sin tocarlos). | Test `tests/test_routing.py:3843` `test_adr0034_f05_repair_effective_providers_short_circuits_when_base_covers_discoverable`: la primera mitad usa `mock.patch("routing_core.catalog.probe_inventory", return_value={}) as probe` + `probe.assert_not_called()` (mismo patrón que la segunda mitad del test, que ya lo usaba correctamente) — corrige **D-01**, el hallazgo del delta-reviewer de que el centinela previo (`side_effect=AssertionError("must not probe")`) era decorativo: `_effective_preference_providers` envuelve el probe en `except Exception: return _MODEL_PREFERENCE_PROVIDERS`, y `AssertionError` es un `Exception`, así que el centinela se tragaba silenciosamente sin que el test mordiera. Verificado empíricamente por el repair-agent: quitando temporalmente el corto-circuito de `:137-138`, el test ahora **falla** (`AssertionError: Expected 'probe_inventory' to not have been called. Called 1 times.`); restaurado el archivo exactamente como estaba (`git diff --check` limpio) el test vuelve a `OK`. La segunda mitad (mock de `DISCOVERABLE_PROVIDERS` ampliado + `probe.assert_called_once()`) prueba que el corto-circuito es condicional real, no una desactivación permanente. `python3 -m unittest tests.test_routing.RoutingTests.test_adr0034_f05_repair_effective_providers_short_circuits_when_base_covers_discoverable tests.test_routing.RoutingTests.test_adr0034_ac09_write_cli_validates_pins_against_the_effective_set_not_just_the_constant -v` → `OK`. |

## Archivos tocados

- `ai/scripts/routing_core/service.py` (F-04)
- `ai/scripts/set_agents_app.py` (F-05)
- `tests/test_routing.py` (F-01, F-03, F-04, F-05)
- `docs/adr/0034-auto-adopted-providers.md` (nota aditiva en el punto 8, documentando F-04)
- `models.toml` (F-02, bajo excepción de ownership — únicamente `[catalog].opencode_zen`/
  `opencode_go` y el comentario que las precede, `models.toml:16-27`)

`ai/scripts/setup_models.py`, `routes.v1.toml` y `ai/state/` no se tocaron.

## Gates — salida real

### `python3 -m unittest discover -s tests`

```
----------------------------------------------------------------------
Ran 819 tests in 384.551s

OK (skipped=3)
```

(3 skips preexistentes, no nuevos — mismo conteo que antes de la reparación; el conteo de tests subió
en 4, por los tests nuevos de F-01/F-04/F-05.)

### `./ai/scripts/verify.sh`

```
GLOBAL_PORTABILITY_OK
CANONICAL_PATHS_OK
FEATURE_STATE_OK
VERIFY_PASS
```

### `./build.sh --check`

```
CHECK_PASS: generated and validated profile go-zen
SELF_SCAFFOLD_SYNC_OK files=2
```

### `git diff --check`

```
(sin salida — exit code 0, sin espacios en blanco al final de línea ni conflictos)
```

## Trazabilidad hallazgo → test específico corrido

```
python3 -m unittest \
  tests.test_routing.RoutingTests.test_adr0034_ac02_ac06_discovered_reviewer_resolves_reviewer_independence_unavailable \
  tests.test_routing.RoutingTests.test_adr0034_ac06_same_vendor_stem_inferred_reviewer_never_serves_a_same_stem_writer \
  tests.test_routing.RoutingTests.test_adr0034_ac02_composition_and_recheck_derive_discovery_through_the_same_path \
  tests.test_routing.RoutingTests.test_adr0034_f04_repair_reprobe_rejection_leaves_an_exclusion_trace \
  tests.test_routing.RoutingTests.test_adr0034_ac08_reprobe_rejection_reranks_to_the_next_candidate \
  tests.test_routing.RoutingTests.test_adr0034_f05_repair_effective_providers_short_circuits_when_base_covers_discoverable \
  tests.test_routing.RoutingTests.test_adr0034_ac09_write_cli_validates_pins_against_the_effective_set_not_just_the_constant \
  -v
```

Resultado: 7/7 `ok`, 0 fallas, 0 errores — corrido de forma aislada antes de la corrida completa de la
suite (819 tests, `OK (skipped=3)`) para aislar cada reparación de posibles interacciones de fixtures.

## Estado

`repair_required` → reparado. No se aceptaron findings de scope nuevo, no se debilitó ni borró ninguna
aserción de regresión existente (los tests AC-02/AC-06/AC-08/AC-09 preexistentes quedan intactos salvo
la corrección puntual de F-03, que solo reemplaza una aserción decorativa muerta por una real sobre la
misma afirmación que el comentario del test ya prometía). Nada marcado como `PACKAGE_ACCEPTED` — esa
decisión es del orquestador/reviewer, no de este repair-agent.

## F-02 — pasada separada (excepción de ownership sobre `models.toml`)

### `git diff models.toml` (diff completo, acotado a la excepción)

```diff
diff --git i/models.toml w/models.toml
index f20085f..777e521 100644
--- i/models.toml
+++ w/models.toml
@@ -15,16 +15,16 @@ codex = ["gpt-5.4", "gpt-5.4-mini", "gpt-5.5", "gpt-5.6-luna", "gpt-5.6-sol", "g
 codex_effort = ["high", "low", "medium", "xhigh"]
 # 012 discovered-inventory AC-04: declared allowlist ceiling for the two new probeable
 # OpenCode-lane pairs (routing_core/catalog.py's `_PAIR_COMMANDS`, AC-01) — bare model ids
-# (no provider prefix, same convention as claude/codex above), re-measured live 2026-07-30
+# (no provider prefix, same convention as claude/codex above), re-measured live 2026-08-10
 # against `opencode models opencode --pure` (60 ids) / `opencode models opencode-go --pure`
-# (16 ids). Probeable only (AC-01..AC-06); NOT routable — no routes.v1.toml row exists for
-# either provider (contract 012's non-goals paragraph, "no curated routes.v1.toml
-# rows for the new models" -- corrected 012 repair F-07, this is NOT AC-11, which
-# is the cache/decision-trail AC and says nothing about routes.v1.toml rows), and
-# neither is in [routing].enabled_providers or
-# models_config.ROUTING_PROVIDERS (AC-05, all four selectability gates, none opened here).
-opencode_zen = ["big-pickle", "claude-fable-5", "claude-haiku-4-5", "claude-opus-4-1", "claude-opus-4-5", "claude-opus-4-6", "claude-opus-4-7", "claude-opus-4-8", "claude-opus-5", "claude-sonnet-4", "claude-sonnet-4-5", "claude-sonnet-4-6", "claude-sonnet-5", "deepseek-v4-flash", "deepseek-v4-flash-free", "deepseek-v4-pro", "gemini-3-flash", "gemini-3.1-pro", "gemini-3.5-flash", "gemini-3.5-flash-lite", "gemini-3.6-flash", "glm-5", "glm-5.1", "glm-5.2", "gpt-5", "gpt-5-codex", "gpt-5-nano", "gpt-5.1", "gpt-5.1-codex", "gpt-5.1-codex-max", "gpt-5.1-codex-mini", "gpt-5.2", "gpt-5.2-codex", "gpt-5.3-codex", "gpt-5.3-codex-spark", "gpt-5.4", "gpt-5.4-mini", "gpt-5.4-nano", "gpt-5.4-pro", "gpt-5.5", "gpt-5.5-pro", "gpt-5.6-luna", "gpt-5.6-sol", "gpt-5.6-terra", "grok-4.5", "grok-build-0.1", "kimi-k2.5", "kimi-k2.6", "kimi-k2.7-code", "kimi-k3", "laguna-s-2.1-free", "ling-3.0-flash-free", "mimo-v2.5-free", "minimax-m2.5", "minimax-m2.7", "minimax-m3", "nemotron-3-ultra-free", "north-mini-code-free", "qwen3.5-plus", "qwen3.6-plus"]
-opencode_go = ["deepseek-v4-flash", "deepseek-v4-pro", "glm-5.1", "glm-5.2", "grok-4.5", "hy3", "kimi-k2.6", "kimi-k2.7-code", "kimi-k3", "mimo-v2.5", "mimo-v2.5-pro", "minimax-m2.7", "minimax-m3", "qwen3.6-plus", "qwen3.7-max", "qwen3.7-plus"]
+# (18 ids). ADR-0034 opened `[routing].discovered_providers = "auto"`, which derives its
+# candidate set from the live probe intersected against exactly this ceiling
+# (`catalog._configured_models`) — so this allowlist is the audited ceiling from which
+# "auto" may route, never a wider universe (`resolve_discovered_providers` cannot exceed
+# it). The curated path stays closed regardless: neither provider is in
+# `routes.v1.toml`, `[routing].enabled_providers`, or `models_config.ROUTING_PROVIDERS`.
+opencode_zen = ["big-pickle", "claude-fable-5", "claude-haiku-4-5", "claude-opus-4-5", "claude-opus-4-6", "claude-opus-4-7", "claude-opus-4-8", "claude-opus-5", "claude-sonnet-4", "claude-sonnet-4-5", "claude-sonnet-4-6", "claude-sonnet-5", "deepseek-v4-flash", "deepseek-v4-flash-free", "deepseek-v4-pro", "gemini-3-flash", "gemini-3.1-pro", "gemini-3.5-flash", "gemini-3.5-flash-lite", "gemini-3.6-flash", "glm-5", "glm-5.1", "glm-5.2", "gpt-5", "gpt-5-codex", "gpt-5-nano", "gpt-5.1", "gpt-5.1-codex", "gpt-5.1-codex-max", "gpt-5.1-codex-mini", "gpt-5.2", "gpt-5.2-codex", "gpt-5.3-codex", "gpt-5.3-codex-spark", "gpt-5.4", "gpt-5.4-mini", "gpt-5.4-nano", "gpt-5.4-pro", "gpt-5.5", "gpt-5.5-pro", "gpt-5.6-luna", "gpt-5.6-sol", "gpt-5.6-terra", "grok-4.5", "grok-build-0.1", "kimi-k2.5", "kimi-k2.6", "kimi-k2.7-code", "kimi-k3", "laguna-s-2.1-free", "ling-3.0-tiny-free", "longcat-2.0-free", "mimo-v2.5-free", "minimax-m2.5", "minimax-m2.7", "minimax-m3", "nemotron-3-ultra-free", "north-mini-code-free", "qwen3.5-plus", "qwen3.6-plus"]
+opencode_go = ["deepseek-v4-flash", "deepseek-v4-pro", "glm-5.1", "glm-5.2", "gpt-5.6-luna", "grok-4.5", "hy3", "kimi-k2.6", "kimi-k2.7-code", "kimi-k3", "mimo-v2.5", "mimo-v2.5-pro", "minimax-m2.7", "minimax-m3", "qwen3.6-plus", "qwen3.7-max", "qwen3.7-plus", "qwen3.8-max"]

 [session]
 opencode_small_model = { "go-zen" = "opencode/north-mini-code-free", "zen" = "opencode/north-mini-code-free", "local" = "opencode/north-mini-code-free" }
```

Confirmado: única diferencia es la ficha del comentario (fecha + narrativa corregida) y el contenido
de las dos listas — ninguna otra clave de `models.toml` (`[routing]`, `[areas.*]`, `[roles.*]`,
`claude`, `codex`, `codex_effort`) se tocó.

### Round-trip `load_config → emit → load_config`

```
round-trip stable: True   # emit(cfg1) == emit(cfg2)
cfg1 == cfg2 -> True       # el config parseado es idéntico tras un ciclo completo
```

### `python3 -m unittest tests.test_routing`

```
Ran 248 tests in 236.334s

OK
```

### `python3 -m unittest tests.test_harness`

72 errores + 1 falla preexistentes, no relacionados con este cambio: reproducidos de forma idéntica
(`errors=72, skipped=2`, mismo `KeyError: 'set_agents_app'` en
`test_vault_registry_keys_by_full_path_and_degrades_on_corruption`) corriendo la suite sobre el árbol
de trabajo **sin** el cambio de F-02 (`git stash` → misma falla exacta → `git stash pop`). Es un
problema de aislamiento de import (`sys.modules.setdefault`) al correr `test_harness` como módulo
aislado en vez de vía `discover`, preexistente al repair de F-02 y fuera de su scope.

### `./build.sh --check`

```
CHECK_PASS: generated and validated profile go-zen
SELF_SCAFFOLD_SYNC_OK files=2
```

### `git diff --check`

Sin salida, exit code 0.

### En vivo — pool de candidatos antes/después del refresh

`echo '{"role":"implementer","task_class":"implementation","risk":"low","selected_runtime":"opencode"}' | ./set-agents --route-decide - --fresh-probes`

- **Antes** (techo 2026-07-30, según el orquestador): 22 candidatos, 21 exclusiones
  `TIER_INSUFFICIENT`.
- **Después** (techo 2026-08-10, esta reparación): **25 candidatos, 24 exclusiones**, todas
  `TIER_INSUFFICIENT`. El ganador no cambia: `openai-codex/gpt-5.6-sol`
  (`independence_verified=false`, igual que antes — el hallazgo no afecta identidad/independencia).
  El `"auto"` ahora ve 3 candidatos vivos adicionales que el techo desactualizado excluía
  silenciosamente (p. ej. `opencode-go/gpt-5.6-luna`, `opencode-go/qwen3.8-max` y
  `opencode-zen/longcat-2.0-free`, todos nuevos en la medición 2026-08-10).

## Estado final

`repair_required` (F-02) → reparado. Excepción de ownership usada exclusivamente para las dos claves
autorizadas de `models.toml`; ninguna otra clave tocada (verificado con `git diff models.toml`
completo arriba). Nada marcado como `PACKAGE_ACCEPTED` — esa decisión es del orquestador/reviewer.
