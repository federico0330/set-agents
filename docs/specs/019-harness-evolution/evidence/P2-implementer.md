# P2-billing-aware-ordering — evidencia del implementer

Feature 019, PKG-2 (ADR-0035). Estado: COMPLETO (AC-12..AC-16 implementados y con test dedicado).

## 0. Defecto vivo (reproducido antes de tocar nada)

```
$ python3 -c "
import sys;sys.path.insert(0,'ai/scripts')
import models_config, setup_models
c=models_config.load_config('models.toml'); r=models_config.load_roster('roles.tsv')
print([l for l in setup_models._panel_lines(c,r,'go-zen') if 'descubiertos' in l])"
['proveedores descubiertos rutables: a, u, t, o']
```

Causa: `ai/scripts/setup_models.py:156`/`:364` (antes del fix) hacían
`config.get("routing", {}).get("discovered_providers", [])` y luego, cuando ese valor era
el string `"auto"` (default nuevo de ADR-0034), `if discovered:` era verdadero (string no
vacío) y `', '.join(discovered)` iteraba el string carácter a carácter. Corregido —
verificación después del fix, misma sesión:

```
$ python3 -c "... print('\n'.join([l for l in setup_models._panel_lines(c,r,'go-zen') if 'descubiertos' in l]))"
proveedores descubiertos rutables: auto → anthropic (suscripción), openai-codex (suscripción), opencode-go (suscripción), opencode-zen (metered)
```

## 1. ADR-0035

`docs/adr/0035-billing-aware-ordering.md` — escrito ANTES del código (verifiqué con
`ls docs/adr/` que 0035 estaba libre justo antes de crear el archivo: la lista iba hasta
`0034-auto-adopted-providers.md`). Indexado en `docs/adr/README.md:42`, mismo formato que
las filas existentes (fila 0034 arriba, sin Supersedes/Superseded).

## 2. Tabla AC → cambio → prueba

| AC | Cambio (`archivo:línea`) | Prueba |
|---|---|---|
| AC-12 | `catalog.py:172` `PROVIDER_BILLING_KIND` completo (4 providers); `catalog.py:180` `billing_rank(provider, model)` puro, `_FREE_MODEL_SUFFIX` reusa el patrón de `_FAST_HINTS` | `tests/test_routing.py::test_ac08_subscription_metered_map_is_provider_keyed_not_a_row_field` (mapa completo), `test_ac12_billing_rank_pure_function` (4 casos + free-suffix + provider desconocido) |
| AC-13 | `service.py:382` inserción de `billing_rank(x[0].provider, x[0].model)` en la tupla, entre `TIER_ORDER[x[0].tier]` y `_bias_rank(...)`; comentario `service.py:367-381` actualizado citando ADR-0035; bucle de exclusiones (`service.py:293-355`) sin tocar | `test_sort_key_tripwire_pins_five_element_tuple_shape` (posición exacta vía regex sobre el source), `test_ac13_zen_wins_when_it_is_the_only_one_satisfying_tier`, `test_ac13_zen_wins_when_it_is_the_only_one_giving_reviewer_independence`, `test_ac13_control_subscription_wins_at_equal_tier` |
| AC-14 | `service.py:415-421` reason code aditivo `BILLING_RANK provider=X rank=N`, siempre presente, nunca reemplaza/reordena; `routing_cli.py:68-84` `_decide_status` lo filtra igual que `RUNTIME_REDIRECTED` (informativo, nunca decide ok/exit) | `test_decide_status_helper_matrix` (4 casos nuevos con `BILLING_RANK`), más 6 tests de `test_routing.py` actualizados con la aserción del código nuevo (ver §3), y confirmado en vivo en `decisions-v1.jsonl` (§5) |
| AC-15 | `catalog.py:714` `route_doctor(config, cache_root, timeout, now)`, read-only, `pairs=` bypassa el cache siempre; `set_agents_app.py:488` `cmd_route_doctor`, flag `--route-doctor` (`:2501-2502`, `:2587-2593`, `:2643-2644`) mismo envelope que `--routing-report`/`--route-decide` | `test_ac15_route_doctor_reports_m1_github_copilot_as_detected_unlistable`, `test_ac15_route_doctor_reports_auth_models_and_billing_per_pair`, `test_ac15_route_doctor_never_writes_the_probe_cache`, `test_ac15_route_doctor_cache_diagnostic_reports_key_mismatch_and_expiry`; salida real en vivo §5 |
| AC-16 | `setup_models.py:32-46` `_resolve_live_discovered`; `setup_models.py:196-212` panel resuelve `"auto"` contra el inventario vivo con billing anotado, lista explícita se muestra tal cual, rótulo `DEFAULTS CURADOS` y línea de política citan ADR-0034/0035; `setup_models.py:397-442` wizard opción 7 rediseñada `auto / lista manual / ninguno`, candidatos manuales de `models_config.DISCOVERABLE_PROVIDERS` (nunca tupla literal) | `test_auto_resolves_the_live_inventory_never_iterates_the_string`, `test_auto_with_nothing_live_says_so_instead_of_iterating`, `test_auto_probe_failure_degrades_to_an_explicit_message`, `test_discovered_providers_surface_when_configured` (lista explícita sin cambios), `test_discovered_provider_toggle_round_trips` (reescrito, ver §3), `test_discovered_provider_auto_and_none_policies` (nuevo) |

## 3. Enumeración test-por-test de cada aserción de contrato modificada

Todos citan ADR-0035 en el propio comentario del test (verificable con
`grep -n "ADR-0035" tests/test_routing.py tests/test_models_wizard_ui.py`).

### `tests/test_routing.py`

1. **`test_ac08_subscription_metered_map_is_provider_keyed_not_a_row_field`** — decía
   `PROVIDER_BILLING_KIND == {"opencode-zen": "metered", "opencode-go": "subscription"}`
   (solo los dos providers OpenCode-lane, porque nada leía el mapa todavía). Ahora dice el
   mapa completo de 4 providers. Justificación: AC-12 exige completar el mapa; el día en
   que `billing_rank` empieza a leerlo es exactamente este.
2. **`test_sort_key_tripwire_pins_five_element_tuple_shape`** — decía que la tupla tenía
   `independence < tier < bias < is_inferred < curated_priority < route_id`. Ahora exige
   además `billing_rank(` estrictamente entre `tier` y `bias`, vía el mismo mecanismo
   (regex sobre el source real de `service.py`, nunca reimplementando el sort). Justifica
   AC-13: la tupla final que deja ADR-0035.
3. **`test_ac10_shape_a...` / `test_ac10_shape_b_redirect_observability...` /
   `test_ac05_service_shape_3b_step0_verified_review...`** (los tres tests con
   `len(review.reason_codes)==1` sobre un `RUNTIME_REDIRECTED`) — decían "1 código, el
   redirect". Ahora dicen "2 códigos: el redirect y `BILLING_RANK provider=anthropic
   rank=0`" — porque AC-14 hace que `BILLING_RANK` sea SIEMPRE aditivo, en cualquier
   decisión que llegue al `while True:` de selección.
4. **`test_unverified_review_reports_tier_without_execution`** y
   **`test_ac05_benign_unverified_review_path_unchanged_and_claude_axis_residual_withdrawn`**
   — decían `reason_codes == ("REVIEW_IDENTITY_UNVERIFIED",)`. Ahora piden
   `reason_codes[0] == "REVIEW_IDENTITY_UNVERIFIED"` y `reason_codes[1].startswith("BILLING_RANK ")`
   — mismo motivo, AC-14.
5. **`test_route_decide_cli_hermetic_matrix`** (4 aserciones dentro de un mismo test:
   writer, "other", unverified reviewer, verified reviewer) — decían
   `reason_codes == []` (o `["REVIEW_IDENTITY_UNVERIFIED"]`). Ahora piden longitud 1 (o 2)
   con el último elemento `startswith("BILLING_RANK ")` — AC-14, vía CLI real (subprocess),
   no solo la capa `RoutingService`.
6. **`test_route_decide_script_uses_explicit_project_context`** — fallaba con
   `returncode=1`/`ok=false` porque `_decide_status` (routing_cli.py) trataba
   `BILLING_RANK` como código de fallo (no estaba en la tabla cerrada
   `_DECIDE_OK_NON_EXECUTABLE_REASONS`). Arreglado filtrando `BILLING_RANK ` igual que
   `RUNTIME_REDIRECTED` (mismo patrón, `routing_cli.py:68-84`) — sin este fix, CADA
   decisión con reviewer no ejecutable habría pasado de `ok=true` a `ok=false`, una
   regresión real de comportamiento, no solo de test. Este es el hallazgo más importante
   del paquete: la ADR dice explícitamente "nunca cambia success" y el código sin este
   filtro lo violaba.
7. **`test_decide_status_helper_matrix`** — se agregaron 4 casos nuevos (`BILLING_RANK`
   solo, junto a `REVIEW_IDENTITY_UNVERIFIED`, junto a un redirect, y junto a un código de
   fallo real) que prueban exhaustivamente el mismo filtro de (6).
8. **Nuevos, no reescrituras**: `test_ac12_billing_rank_pure_function`,
   `test_ac13_zen_wins_when_it_is_the_only_one_satisfying_tier`,
   `test_ac13_zen_wins_when_it_is_the_only_one_giving_reviewer_independence`,
   `test_ac13_control_subscription_wins_at_equal_tier`,
   `test_ac15_route_doctor_reports_m1_github_copilot_as_detected_unlistable`,
   `test_ac15_route_doctor_reports_auth_models_and_billing_per_pair`,
   `test_ac15_route_doctor_never_writes_the_probe_cache`,
   `test_ac15_route_doctor_cache_diagnostic_reports_key_mismatch_and_expiry`.

### `tests/test_models_wizard_ui.py`

Marcadores de texto por grep — el que cada test pinea:

1. **`test_discovered_providers_surface_when_configured`** (sin cambios de comportamiento,
   verificado que sigue pasando) — pinea el marcador `"opencode-zen"` en el texto del panel
   cuando `discovered_providers` es una LISTA explícita `["opencode-zen"]`. No se movió: la
   ADR dice explícitamente que una lista explícita se sigue mostrando tal cual.
2. **`test_auto_resolves_the_live_inventory_never_iterates_the_string`** (nuevo) — pinea el
   marcador `"proveedores descubiertos rutables: auto → opencode-zen (metered), opencode-go
   (suscripción)"` y `assertNotIn("a, u, t, o", text)` — el marcador que prueba que el
   defecto de §0 no vuelve.
3. **`test_auto_with_nothing_live_says_so_instead_of_iterating`** / 
   **`test_auto_probe_failure_degrades_to_an_explicit_message`** (nuevos) — pinean
   `"auto → ninguno vivo ahora"` / `"auto → no verificable ahora"`.
4. **`test_discovered_provider_toggle_round_trips`** — antes pineaba `Selected(6)` (menú)
   seguido directo de `Selected(0)` (toggle directo de `opencode-zen`, primero de la tupla
   hardcodeada `("opencode-zen", "opencode-go")`). Ahora pinea `Selected(6)` → `Selected(1)`
   ("Lista manual") → `Selected(3)` (posición de `opencode-zen` en
   `sorted(models_config.DISCOVERABLE_PROVIDERS)` == `["anthropic", "openai-codex",
   "opencode-go", "opencode-zen"]`) → `Selected(4)` (salir). El marcador final
   `discovered_providers == ["opencode-zen"]` y la presencia de `MODEL_METADATA_INFERRED`
   en la salida no cambiaron. Movido porque AC-16 exige que la opción 7 sea un picker de 3
   políticas, no el toggle directo de antes.
5. **`test_discovered_provider_auto_and_none_policies`** (nuevo) — pinea
   `discovered_providers == "auto"` tras elegir la opción 0, y `== []` tras elegir la
   opción 2, con el marcador de texto `"discovered_providers = auto"` en la salida.

### `tests/test_menu_ui.py`

No se tocó — no pinea ningún marcador relacionado con `discovered_providers`/billing
(verificado: `grep -n "descubiertos\|DEFAULTS CURADOS" tests/test_menu_ui.py` no devuelve
nada).

### `tests/test_harness.py`

No se tocó — ningún marcador doctrinal ahí referencia `discovered_providers`, billing, o
`--route-doctor`.

## 4. La tupla final del sort key (escrita explícitamente)

```
(same_provider_as_writer, pin_rank, TIER_ORDER, billing_rank, _bias_rank, is_inferred,
 curated_priority, route_id)
```

Línea real (`service.py:382`):

```python
candidates.sort(key=lambda x: ((x[0].provider == writer.provider) if writer else False, 0 if pin and (x[0].provider, x[0].model) == pin else 1, TIER_ORDER[x[0].tier], billing_rank(x[0].provider, x[0].model), _bias_rank(x[0].provider, bias_preference), 1 if x[0].route_id in self._inferred_ids else 0, x[0].curated_priority, x[0].route_id))
```

## 5. Salidas reales

### `python3 -m unittest discover -s tests` (dos corridas independientes, mismo resultado)

Antes del paquete (contexto pack): 819 tests OK, 3 skips preexistentes.

Después (esta sesión, corrida 1):
```
Ran 831 tests in 574.810s
OK (skipped=3)
```
Corrida 2 (independiente, mismos resultados, confirma no-flake):
```
Ran 831 tests in 586.985s
OK (skipped=3)
```
El conteo subió de 819 a 831 (+12, los tests nuevos: `test_ac12_billing_rank_pure_function`,
3× `test_ac13_*`, 4× `test_ac15_route_doctor_*`, `test_auto_with_nothing_live_...`,
`test_auto_probe_failure_...`, `test_discovered_provider_auto_and_none_policies`, y
`test_auto_resolves_the_live_inventory_...` = 12), nunca bajó. Los 3 skips preexistentes se
mantienen (`test_ac10_p2_local_live_parity_gate`-tipo credential-gated, y
`test_route_decide_envelope_reports_selection_path` que sigue saltando por
`NO_ELIGIBLE_ROUTE` en esta máquina, sin relación con este paquete).

### `./ai/scripts/verify.sh`

```
...
Ran 831 tests in 460.386s
OK (skipped=3)
...
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

Sin salida, exit 0 (limpio).

### `./set-agents --route-doctor` (probes frescos, en vivo, muestra M-1)

```json
{"command": "route-doctor", "data": {"cache": {"age_seconds": 214.99675941467285, "key_current": true, "reason": "OK", "used": true}, "providers": [{"authenticated": false, "billing": "subscription", "detected_unlistable": false, "models_listable": 0, "provider": "anthropic", "runtime": "opencode"}, {"authenticated": true, "billing": "subscription", "detected_unlistable": false, "models_listable": 6, "provider": "openai-codex", "runtime": "opencode"}, {"authenticated": true, "billing": "subscription", "detected_unlistable": false, "models_listable": 18, "provider": "opencode-go", "runtime": "opencode"}, {"authenticated": true, "billing": "metered", "detected_unlistable": false, "models_listable": 60, "provider": "opencode-zen", "runtime": "opencode"}, {"authenticated": true, "billing": "unknown", "detected_unlistable": true, "models_listable": 0, "provider": "github copilot", "runtime": "opencode"}]}, "ok": true, "reason_codes": [], "schema_version": 2, "warnings": []}
```

`github copilot` sale con `authenticated=true, detected_unlistable=true, models_listable=0`
— exactamente M-1, diagnosticable sin leer código. `anthropic` sale `authenticated=false`
en esta máquina/sesión (drift real de credenciales frente a la medición de ADR-0034, no un
bug: `route-doctor` reporta lo que el probe observa AHORA).

### Panel renderizado (perfil `go-zen`, en vivo)

```
lane: go-zen (auto)    suscripciones: anthropic=✓pin ollama=✗off openai=✓pin zen=✓pin
routing dinámico: el router decide por spawn para TODOS los roles (ADR-0030; --route-explain) · variantes @tier: 6 roles
política: Automático (recomendado) — sin pins; fijá un modelo con 'Routing: fijar modelo'
proveedores descubiertos rutables: auto → anthropic (suscripción), openai-codex (suscripción), opencode-go (suscripción), opencode-zen (metered)
DEFAULTS CURADOS (fallback cuando el lane no aplica la decisión; ADR-0034/ADR-0035):
AREA       CLAUDE   CODEX          EFFORT  OPENCODE[go-zen]
...
```

### `--route-decide --fresh-probes` + `--routing-decisions --limit 5`

```
$ echo '{"role":"implementer","task_class":"implementation","risk":"low","selected_runtime":"opencode"}' | ./set-agents --route-decide - --fresh-probes
{"command": "route-decide", "data": {..., "provider": "openai-codex", "model": "gpt-5.6-sol", "reason_codes": ["BILLING_RANK provider=openai-codex rank=0"], "execution_enabled": true, ...}, "ok": true, "reason_codes": ["BILLING_RANK provider=openai-codex rank=0"], "schema_version": 2, ...}

$ ./set-agents --routing-decisions --limit 5
{"command": "routing-decisions", "data": {"decisions": [..., {"decision_id": "dec1_0e26b0e2...", "reason_codes": ["BILLING_RANK provider=openai-codex rank=0"], "provider": "openai-codex", "model": "gpt-5.6-sol", "execution_enabled": true, ...}]}, "ok": true, ...}
```

`BILLING_RANK provider=openai-codex rank=0` queda persistido en
`decisions-v1.jsonl` (AC-14, confirmado en vivo) y `ok=true`/`execution_enabled=true` no se
vieron afectados (el filtro de `routing_cli._decide_status` funciona en producción, no solo
en test).

### `models.toml` — refresh de `[catalog].opencode_zen`/`opencode_go`

**No se re-escribió.** Re-medí en vivo antes de tocar nada:

```
$ opencode models opencode --pure | wc -l   # 60
$ opencode models opencode-go --pure | wc -l  # 18
```

`models.toml:26` ya tenía 60 ids para `opencode_zen` y `models.toml:27` ya tenía 18 para
`opencode_go`, con el comentario de arriba fechado `2026-08-10` (la misma fecha de la
medición del context pack). Diff carácter a carácter contra la salida en vivo (ordenada):
sin diferencias — las 4 faltantes que el context pack citaba (`ling-3.0-tiny-free`,
`longcat-2.0-free`, `mimo-v2.5-free`, `qwen3.5-plus`) ya estaban presentes, y los 2 ids
muertos citados (`claude-opus-4-1`, `ling-3.0-flash-free`) ya estaban ausentes. Conclusión:
la excepción de ownership aprobada para `models.toml` no tuvo trabajo pendiente — alguien
(probablemente P1, en su propio ciclo) ya hizo este refresh antes de que este paquete
empezara. No se escribió el archivo.

## 6. Nota de scope: `ai/scripts/routing_cli.py`

Este archivo NO está en `owned_paths` ni `shared_paths` de P2 en el state de la feature
(verificado con `python3 -c "import json; ..."` contra
`ai/state/features/019-harness-evolution.json`), y tampoco estaba en los de P1. Lo edité de
todas formas porque es estructuralmente necesario para AC-14: `_decide_status` es la única
función que clasifica `ok`/`exit_code` a partir de `reason_codes`, y sin el mismo filtro que
ya existía para `RUNTIME_REDIRECTED` (`routing_cli.py:68-84`), el nuevo código aditivo
`BILLING_RANK` — SIEMPRE presente desde este ADR — habría convertido cada decisión no
ejecutable en `ok=false`/exit 1, una regresión de comportamiento real (confirmada en rojo
por `test_route_decide_script_uses_explicit_project_context` antes del fix). Dejo esto
anotado explícitamente para que el reviewer lo audite con la misma vara que si fuera un
archivo owned, y para que el orchestrator considere agregar `routing_cli.py` a
`shared_paths` de P2 en el registro de decisiones (`log-decision`).

## 7. Lo que no pude verificar

- El conteo base "819 tests OK, 3 skips" del context pack es tal cual me lo dieron; no
  volví a correr la suite en el commit anterior a mis cambios para confirmarlo yo mismo
  (hubiera exigido un stash/checkout intermedio fuera de mi alcance como implementer) —
  marcado "sin verificar" en ese sentido puntual; sí verifiqué que el conteo actual (831)
  es consistente en dos corridas independientes.
- `test_route_decide_envelope_reports_selection_path` sigue en skip por
  `NO_ELIGIBLE_ROUTE` en esta máquina — preexistente, no relacionado con este paquete (no
  lo investigué a fondo, "sin verificar" si es un problema de credenciales locales o de
  otra causa).

## 8. Riesgos y deudas anotadas

- `routing_cli.py` tocado fuera de owned/shared_paths — ver §6, requiere decisión del
  orchestrator (agregar a `shared_paths` o revisar por separado).
- `route_doctor`'s reporte de `models_listable` para `openai-codex` bajó a 6 en esta sesión
  (13 medidos en ADR-0034, 2026-08-10 también) — drift real de la cuenta OAuth de ChatGPT,
  no un defecto de este paquete; queda como evidencia de que `--route-doctor` reporta el
  presente, no una foto vieja.
