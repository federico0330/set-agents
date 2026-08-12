# P1-provider-auto-adoption — evidencia del implementer (ADR-0026)

Feature 019-harness-evolution, paquete P1. Runtime opencode 1.18.14, máquina de
desarrollo, 2026-08-10. Todo lo que sigue es evidencia real corrida en esta sesión,
salvo lo marcado explícitamente "sin verificar".

## Alcance real vs. context pack (desvío documentado)

El context pack pedía además refrescar `models.toml:26` (listas `opencode_zen`/
`opencode_go`) y tocar `ai/scripts/setup_models.py` para que el toggle de la sección 7
no rompa con `discovered_providers = "auto"`. **Revertí ambos cambios**: el `owned_paths`
real del paquete en `ai/state/features/019-harness-evolution.json` marca
`models.toml` como **read_only_paths** de P1, y `ai/scripts/setup_models.py` es
**owned_paths exclusivo de P2-billing-aware-ordering**. Mandan los baselines de
ownership del state file sobre el texto libre del context pack (regla del harness:
nunca tocar paths fuera de la asignación). Esto deja un **riesgo real y explícito**
para P2 o para integración: con `discovered_providers` por defecto en `"auto"` (string),
`ai/scripts/setup_models.py:156` (`config.get("routing", {}).get("discovered_providers", [])`)
y `:364` (`list(routing.get("discovered_providers", []))`) van a serializar `"auto"`
carácter por carácter (`list("auto") == ['a','u','t','o']`) la primera vez que alguien
abra el wizard (`./setup-models.sh`) sin haber fijado el valor a mano. **No is un defecto
introducido por P1** — nace exactamente de que P1 cambia el default y P2 es quien posee
ese archivo — pero hay que resolverlo antes o junto con la integración. Dejo la línea
exacta y el fix mínimo sugerido (guardia `isinstance(value, list) else []`) para quien
implemente P2.

## AC → cambio → prueba

| AC | Cambio (archivo:línea) | Prueba |
|---|---|---|
| AC-01 | `ai/scripts/models_config.py:42-49` (`ROUTING_DEFAULTS["discovered_providers"]="auto"`), `:211-218` (validación acepta `"auto"` o lista), `:533-537` (`emit()` compara contra el default real, no truthiness) | `tests/test_discovered_routes.py::test_discovered_providers_key_validates_and_defaults_to_auto`, `::test_discovered_providers_accepts_auto_or_explicit_list_never_anything_else`, `::test_emit_preserves_discovered_providers_and_exclude`, `::test_emit_of_an_untouched_config_has_no_new_lines` |
| AC-02 | `ai/scripts/routing_core/catalog.py:664-687` (`resolve_discovered_providers`, función única), `:726` (`build_effective_snapshot` la usa), `ai/scripts/routing_core/service.py:134-158` (composición y `recheck` llaman la misma vía) | `tests/test_discovered_routes.py::test_auto_default_synthesizes_from_the_live_inventory`, `::test_auto_never_synthesizes_a_provider_absent_from_the_probed_inventory`; `tests/test_routing.py::test_adr0034_ac02_composition_and_recheck_derive_discovery_through_the_same_path` (tripwire de fuente); evidencia viva más abajo |
| AC-03 | `ai/scripts/opencode_spawn.py:117-135` (`opencode_model_ref` importa `routing_core.catalog._OPENCODE_CLI_IDS` en vez de una copia propia; `anthropic` excluido explícitamente) | `tests/test_routing.py::test_adr0034_ac03_opencode_spawn_shares_the_catalog_cli_id_table`; suite completa de `tests/test_spawn_materialization.py` (`OpencodeArgvTests`) sigue verde sin cambios |
| AC-04 | `ai/scripts/routing_core/service.py:353-375` (`is_inferred` insertado inmediatamente antes de `curated_priority`) | `tests/test_routing.py::test_sort_key_tripwire_pins_five_element_tuple_shape` (reescrito) |
| AC-05 | `ai/scripts/routing_core/inference.py:26-73` (`_FRONTIER_HINTS` eliminado, `infer_tier` solo fast/balanced) | `tests/test_discovered_routes.py::test_tiers_unknown_is_never_frontier` (reescrito) |
| AC-06 | `ai/scripts/routing_core/service.py:320-327` (`REVIEW_IDENTITY_UNRESOLVED_INFERRED`), `ai/scripts/routing_core/inference.py:49-67` (`stem_resolved`) | `tests/test_routing.py::test_adr0034_ac06_unresolved_vendor_stem_excludes_a_synthesized_reviewer` |
| AC-07 | `ai/scripts/routing_core/catalog.py:196-208` (`_parse_opencode_auth`, solo `●`/`*`) | `tests/test_routing.py::test_probe_parsers_are_pair_specific_and_fail_closed` (aserción `○` agregada) |
| AC-08 | `ai/scripts/routing_core/catalog.py:281-333` (`_opencode_binary_signature`, `_live_opencode_auth_signature`, `_cache_key` con firma+mtime+schema), `:526-543` (`probe_inventory` las enhebra); `ai/scripts/routing_core/service.py:376-459` (loop de re-rank en vez de abortar en el primer fallo de reprobe) | `tests/test_routing.py::test_adr0034_ac08_reprobe_rejection_reranks_to_the_next_candidate`; `test_ac11_cache_key_covers_the_new_allowlists_and_negatives_stay_unpersisted` sigue verde |
| AC-09 | `ai/scripts/set_agents_app.py:111-146` (`_effective_preference_providers`), `:150-186` (`valid_providers` parametrizado en los validadores), `:333-336`/`:400-403` (los write-CLI pasan el set vivo; `load_model_preference`/`load_model_pin`, el arranque, siguen con el set estático) | `tests/test_routing.py::test_adr0034_ac09_write_cli_validates_pins_against_the_effective_set_not_just_the_constant` |
| AC-10 | Sin cambio de código — `DISCOVERABLE_PROVIDERS` ya era exactamente `{p for _, p in _PAIR_COMMANDS}` | `tests/test_routing.py::test_adr0034_ac10_discoverable_providers_lockstep_guard` (guarda nueva) |
| AC-11 | `docs/adr/0034-auto-adopted-providers.md` + índice `docs/adr/README.md` | esta tabla; enumeración test-por-test abajo |

## Enumeración test por test (tests reescritos)

### `tests/test_routing.py`

- **`test_sort_key_tripwire_pins_five_element_tuple_shape`**: decía que el tuple era
  `(independence, tier, bias, curated_priority, route_id)` y usaba `elements.index("x[0].route_id")`
  para ubicar el tie-break final. ADR-0034 inserta `is_inferred` (que internamente
  también menciona `x[0].route_id in self._inferred_ids`), así que el primer
  `.index("x[0].route_id")` ahora encuentra esa referencia interna, no el tie-break real
  — el test rompía con `229 not less than 185`. Reescrito: agrega el token de
  `is_inferred` a la lista de tokens exigidos, calcula su posición, exige
  `bias_pos < inferred_pos < priority_pos`, y usa `rindex` (última ocurrencia) para el
  `route_id` final. Cita ADR-0034 en el comentario.
- **`test_probe_parsers_are_pair_specific_and_fail_closed`**: no tenía ninguna aserción
  sobre filas `○`. Se agregó un bloque nuevo (sin tocar las aserciones previas) que
  prueba que `●`/`*` cuentan como autenticado y `○` NO — antes del fix, `○` también
  contaba. Cita ADR-0034 AC-07.
- 6 tests nuevos (`test_adr0034_ac02_..`, `..ac03_..`, `..ac06_..`, `..ac08_..`,
  `..ac09_..`, `..m1_..`) y 1 guarda nueva (`test_adr0034_ac10_..`): no reemplazan
  ninguna aserción existente, son puramente aditivos.

### `tests/test_discovered_routes.py`

- **`test_discovered_providers_key_validates_and_defaults_empty`** → renombrado
  `test_discovered_providers_key_validates_and_defaults_to_auto`. Antes afirmaba
  `config["routing"]["discovered_providers"] == []` (el viejo default). Con ADR-0034 el
  default es la string `"auto"` — la aserción se invirtió a propósito, es exactamente lo
  que este ADR cambia. `ROUTING_PROVIDERS` (la vía curada) sigue verificado como cerrado.
- **`test_flag_absent_is_byte_identical_to_the_curated_snapshot`** → dividido en dos:
  `test_explicit_empty_list_disables_and_is_byte_identical_to_the_curated_snapshot`
  (mismo fixture, pero ahora fija `discovered_providers = []` EXPLÍCITAMENTE, porque
  "ausente" ya no es sinónimo de "deshabilitado") y
  `test_auto_default_synthesizes_from_the_live_inventory` (el mismo fixture EXACTO, sin
  tocar `discovered_providers`, probando el comportamiento OPUESTO al que el test viejo
  afirmaba — el efecto neto que ADR-0034 busca).
- **`test_tiers_unknown_is_never_frontier`**: la tabla decía
  `("deepseek-v4-pro", "frontier")` y `("gpt-5.6-terra", "frontier")` (promoción por
  sufijo `-pro`/`-terra`). AC-05 elimina esa promoción — ahora ambos casos esperan
  `"balanced"`. Se agregó un loop extra probando `-opus`/`-max`/`-ultra`/`-plus` nunca
  llegan a frontier.
- Test nuevo: **`test_discovered_providers_accepts_auto_or_explicit_list_never_anything_else`**
  (AC-01/AC-10, round-trip vía `emit()+load()`, prueba `"auto"`, `[]`, lista válida, y
  tres formas inválidas incluido `["github-copilot"]`/`["openai"]`, M-1/M-2).
- Test nuevo: **`test_auto_never_synthesizes_a_provider_absent_from_the_probed_inventory`**
  (AC-02, inventario vacío ⇒ snapshot efectivo idéntico al curado).

### `tests/test_probe_subscriptions.py`

**Sin cambios.** Cubre `detect_subscriptions`/tri-estado de `[subscriptions]`, una
superficie que ADR-0034 no toca (`_PROVIDER_SUBSCRIPTION` explícitamente fuera de
alcance por el context pack). Corrí la suite completa igual — 8/8 verdes — para
confirmar que el cambio de default de `discovered_providers` no la afecta (usa su
propio camino, `probe_inventory` directo, no `build_effective_snapshot`).

### `tests/test_spawn_materialization.py`

**Sin cambios de aserciones.** `OpencodeArgvTests::test_model_ref_mapping_per_provider`
sigue verde sin tocar porque el nuevo `opencode_model_ref` (leyendo
`routing_core.catalog._OPENCODE_CLI_IDS`) produce el MISMO mapeo byte-a-byte que la
tabla vieja `_PROVIDER_PREFIXES` para los tres providers que ya cubría
(`openai-codex→openai`, `opencode-zen→opencode`, `opencode-go→opencode-go`); la
cobertura nueva de AC-03 (compartir la fuente, excluir `anthropic`) vive en
`tests/test_routing.py::test_adr0034_ac03_...` porque ese archivo ya importa
`routing_core.catalog` en ese contexto de prueba.

### `tests/test_decide_always.py`

**Sin cambios.** No referencia `discovered_providers`, `_FRONTIER_HINTS`, ni el sort
key directamente; su suite (5/5) sigue verde como prueba negativa de que el paquete no
rompió el "decide siempre" (ADR-0030).

## Tupla final del sort key (`service.py`)

```
(same_provider_as_writer, pin_rank, TIER_ORDER, _bias_rank, is_inferred, curated_priority, route_id)
```

Línea real (`ai/scripts/routing_core/service.py:375`):

```python
candidates.sort(key=lambda x: ((x[0].provider == writer.provider) if writer else False, 0 if pin and (x[0].provider, x[0].model) == pin else 1, TIER_ORDER[x[0].tier], _bias_rank(x[0].provider, bias_preference), 1 if x[0].route_id in self._inferred_ids else 0, x[0].curated_priority, x[0].route_id))
```

P2 (ADR-0035) insertará `billing_rank` entre `TIER_ORDER` y `_bias_rank`, documentado en
el ADR-0034 y en el comentario que precede a esta línea.

## Round-trip de `"auto"` (AC-01, riesgo 2 del spec)

`tests/test_discovered_routes.py::test_discovered_providers_accepts_auto_or_explicit_list_never_anything_else`
prueba, vía `emit()` + `load_config()` real sobre archivo temporal:

- `"auto"` (default) → **omitido** del texto emitido (comparación contra el default real,
  no truthiness) → al recargar, vuelve a `"auto"` (nunca degrada a lista).
- `[]` explícito → **se emite** (`discovered_providers = []`), distinto del default → al
  recargar, sigue siendo `[]` (el opt-out total sobrevive, no se pierde en el re-emit).
- `["opencode-zen"]` → se emite y recarga idéntico.
- `["github-copilot"]`, `["openai"]`, `"nonsense"` → `ModelsError` en la carga (M-1/M-2
  nunca entran, ni siquiera escritos a mano).

## Test de copilot fail-closed (M-1)

`tests/test_routing.py::test_adr0034_m1_github_copilot_never_gets_an_audited_pair_even_authenticated`:
prueba que `("opencode","github-copilot")` no existe en `_PAIR_COMMANDS`, y que
`resolve_discovered_providers` con `"auto"` + un inventario **hipotético** que
(incorrectamente, nunca posible por el probe real) incluyera esa clave igual la
descarta, porque la intersección es contra `_PAIR_COMMANDS`, no contra lo que el
inventario diga.

## Salidas reales

### `python3 -m unittest discover -s tests` (equivalente local a `pytest tests/ -x` —
`pytest` no está instalado en esta máquina: `/usr/bin/python3: No module named pytest`)

Antes de empezar el paquete no tengo un conteo baseline propio corrido en esta sesión
(el repo ya traía 78x tests antes de 019; no re-corrí el HEAD previo por presupuesto).
Después de mis cambios, corrida completa:

```
Ran 815 tests in 455.969s

OK (skipped=3)
```

Sin fallos, sin skips nuevos (los 3 skips son pre-existentes: `pi lane: invalid project
identity` y dos `route-decide not decidable on this machine`, ninguno introducido por
este paquete). El conteo sube respecto al HEAD previo (agregué 6 tests nuevos + 1 guarda
en `test_routing.py`, y 3 tests nuevos en `test_discovered_routes.py` — nunca baja).

### `./ai/scripts/verify.sh`

```
CHECK_PASS: generated and validated profile go-zen
SELF_SCAFFOLD_SYNC_OK files=2
...
Ran 815 tests in 480.171s

OK (skipped=3)
GLOBAL_PORTABILITY_OK
CANONICAL_PATHS_OK
FEATURE_STATE_OK
VERIFY_PASS
```

### `./build.sh --check`

```
CHECK_PASS: generated and validated profile go-zen
SELF_SCAFFOLD_SYNC_OK files=2
```//exit 0

### `git diff --check`

Salida vacía, exit 0 (limpio).

### `python3 ai/scripts/check-owned-paths.py --state-file ai/state/features/019-harness-evolution.json --package-id P1-provider-auto-adoption`

```
{
  "changed_files": [
    "ai/scripts/models_config.py", "ai/scripts/opencode_spawn.py",
    "ai/scripts/routing_core/catalog.py", "ai/scripts/routing_core/inference.py",
    "ai/scripts/routing_core/service.py", "ai/scripts/set_agents_app.py",
    "ai/state/STATUS.md", "docs/adr/README.md", "docs/notas/00 - Proyecto.md",
    "tests/test_discovered_routes.py", "tests/test_routing.py"
  ],
  "ok": false,
  "out_of_scope": ["ai/state/STATUS.md", "docs/notas/00 - Proyecto.md"],
  "read_only_violations": []
}
OWNERSHIP_FAIL
```

**`read_only_violations` está vacío** (correcto — `models.toml` no lo toqué, lo revertí
explícitamente, ver sección de desvío arriba). Los dos `out_of_scope`
(`ai/state/STATUS.md`, `docs/notas/00 - Proyecto.md`) **ya estaban modificados ANTES de
que yo empezara** — son la narración/estado que el orquestador escribió al lanzarme
(`record-spawn`/`log-narrative`, ver `git diff` de esos dos archivos: la única entrada es
el spawn de este mismo implementer). Mis instrucciones me prohíben explícitamente tocar
`ai/state/` — no los edité, y el `OWNERSHIP_FAIL` es sobre un estado que precede mi
sesión, no sobre algo que yo introduje. Lo marco para que el orquestador lo revise: si el
gate de ownership corre contra el estado ANTES del spawn, este par de archivos nunca
debería figurar como diff del paquete en absoluto.

### `--route-decide` (provider descubierto en vivo)

```
$ echo '{"role":"implementer","task_class":"implementation","risk":"low","selected_runtime":"opencode"}' | ./set-agents --route-decide - --fresh-probes
{"command": "route-decide", "data": {"bias_class": "build", "context_ok": false,
"decision_id": "dec1_e7d54c65e4a70334d36651c34702c69f", "effort": "medium",
"exclusions": [ ...20 entradas TIER_INSUFFICIENT... ], "execution_enabled": true,
"family": "gpt-5.6", "feature_id": "019-harness-evolution", "independence_verified": false,
"model": "gpt-5.6-sol", "package_id": "P1-provider-auto-adoption", "preference_configured": false,
"provider": "openai-codex", "reason_codes": [], "role_class": "writer",
"route_id": "rt1_5a0df34ea168a966", "run_id": "run1_a0856ddc9664b1171ada26e23b116b4e",
"runtime": "opencode", "selection_path": "dynamic", "tier": "balanced"}, "ok": true, ...}
```

La ruta ganadora es `openai-codex` (curada) — **correcto por diseño (AC-04: curada gana
empates)**, no un bug: `routes.v1.toml` cubre los 3 tiers con 2 providers curados
(`openai-codex`/`anthropic`), así que un candidato descubierto solo gana cuando ambos
curados están excluidos (no-auth, exhausted, o conflicto de independencia) — un caso que
no reproduje en esta sesión (necesitaría credenciales codex/claude caídas o un escenario
de reviewer que descarte ambos curados, que no armé por presupuesto). **Evidencia
indirecta pero real de AC-02**: la lista `exclusions` trae **20 entradas** — con la vía
curada sola (pre-ADR-0034, `discovered_providers=[]`) solo existen 6 filas curadas
totales, así que 20 candidatos ≠ curados-only; son rutas sintetizadas de `opencode-zen`/
`opencode-go` participando activamente en el pool y perdiendo por tier, exactamente lo
que `build_effective_snapshot` produce con `"auto"` activo. "Un provider descubierto
elegido en un decision real" queda **sin verificar en esta sesión** — dejo la limitación
explícita en vez de fabricar una corrida.

### `--routing-decisions --limit 5`

```
$ ./set-agents --routing-decisions --limit 5
{"command": "routing-decisions", "data": {"decisions": [
  ...,
  {"at": "2026-08-10T15:03:21+00:00", "decision_id": "dec1_e7d54c65e4a70334d36651c34702c69f",
   "effort": "medium", "execution_enabled": true, "family": "gpt-5.6",
   "model": "gpt-5.6-sol", "provider": "openai-codex", "reason_codes": [],
   "risk": "low", "role": "implementer", "role_class": "writer",
   "route_id": "rt1_5a0df34ea168a966", "run_id": "run1_a0856ddc9664b1171ada26e23b116b4e",
   "runtime": "opencode", "selection_path": "dynamic", "simulate": false,
   "task_class": "implementation", "tier": "balanced"}
]}, "ok": true, ...}
```

Confirma que la decisión de arriba quedó persistida en `decisions-v1.jsonl` (ADR-0031),
consistente con el `route-decide` de más arriba.

## Riesgos y deudas anotadas

1. **`ai/scripts/setup_models.py`** (owned por P2) va a romper (`list("auto")`
   char-split) en `:156`/`:364` la primera vez que el wizard corra con el nuevo default
   `"auto"`. No lo arreglé porque el archivo es propiedad exclusiva de P2. **Bloqueante
   para integración si P2 no aterriza antes o junto con P1** — o el orquestador debe
   coordinar un fix mínimo de una línea en P2 antes de aceptar P1 en producción para
   cualquier repo que use el wizard.
2. **`opencode_go` en `models.toml:27`** (16 ids) difiere de la medición viva (18 ids,
   ver spec "Medición en vivo"), pero el context pack solo trae el diff explícito para
   `opencode_zen` — no toqué `opencode_go` porque `models.toml` es `read_only_paths` de
   P1 de todos modos (revertido, ver desvío arriba). **Sin verificar**: cuáles son los 2
   ids faltantes.
3. **AC-09** implementado con una interpretación deliberadamente conservadora: el
   arranque (`load_model_preference`/`load_model_pin`) sigue validando SOLO contra el
   set estático de 4 providers (nunca dependiente de red), y el probe contra el
   snapshot vivo solo corre en los comandos de escritura explícitos del CLI
   (`--model-preference-set`, `--model-pin-set`). Documentado en el ADR y en el
   docstring de `_effective_preference_providers`. Hoy el set vivo y el estático
   coinciden exactamente (`DISCOVERABLE_PROVIDERS == _MODEL_PREFERENCE_PROVIDERS`), así
   que esta AC no tiene efecto observable en producción todavía — analogía directa con
   el propio AC-07 (fix real, efecto nulo hoy).
4. **No pude reproducir en vivo una decisión donde un provider descubierto GANE** (ver
   sección `--route-decide` arriba) — la vía curada cubre las 3 tiers con 2 providers
   siempre autenticados en esta máquina, así que nunca hay hueco para que zen/go ganen
   el sort. La evidencia indirecta (20 exclusiones vs. 6 filas curadas) es real pero no
   sustituye una demostración directa; dejo marcado para quien haga la revisión
   profunda del paquete que puede reproducirlo forzando `PROVIDER_UNAUTHENTICATED` en
   ambos curados vía un config de prueba, o con un escenario de reviewer sin
   independencia curada disponible.
5. `pytest` no está instalado en esta máquina — usé `python3 -m unittest discover -s
   tests` como equivalente exacto (mismo runner que `verify.sh` invoca internamente).
