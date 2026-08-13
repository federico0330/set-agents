# P5 — altas-y-bajas-automaticas — evidencia implementer

Estado: **COMPLETO**

## Nota de continuidad de sesión

Esta instancia murió por un error de API justo antes de correr los gates finales. El
código y los tests de este paquete (AC-16..19) ya estaban implementados en el repo por
un turno anterior de esta MISMA sesión (mismo `session_id`, confirmado con backups en
`scratchpad` fechados entre la marca de "P5 started" en la bitácora y ahora). Al retomar,
en vez de rehacer el trabajo:

1. Leí el código y los tests ya escritos, línea por línea, para las 3 superficies y los
   4 AC.
2. Detecté un hueco real: `cmd_doctor_all` y `_estado_general_lines` (las dos superficies
   que NO son `route_doctor`) no tenían ningún test que probara el **contenido** de la
   línea impresa (`listed_by_provider=N usable_after_ceiling=M` / `listado=N usable=M`)
   con N≠M — solo había un test de plomería de `cache_root` (AC-10, pre-existente). Escribí
   los dos tests que faltaban.
3. Hice el mordisco (neutralizar → rojo → revertir → verde) para esos 2 tests nuevos Y,
   como muestreo de que el código pre-existente no es un "quinto test que dice cubrir algo
   que no mira" (la advertencia explícita del context pack), para 4 piezas más de la
   implementación ya escrita: AC-16 dirección 2 + trampa opencode-zen, AC-17 (memoria vs.
   caché), AC-18 dead/unreachable, AC-18 `--prune-dead` nunca borra `unreachable`.
4. Los gates (`unittest discover`, `verify.sh`, `build.sh --check`, `git diff --check`)
   los corrió el **orquestador**, no yo — los pego tal cual me los pasó, atribuidos. Yo
   corrí subconjuntos acotados de tests (los de este paquete) para las pruebas de mordida
   de abajo, siempre con salida literal.
5. Al escribir esta evidencia, corriendo `--route-doctor`/`--doctor-all`/el panel en vivo
   para juntar la salida real de las tres superficies, until observé algo que el
   orquestador NO vio en su propia corrida minutos antes: `github copilot` pasó de
   `verified_cli_id=None` (su corrida) a `verified_cli_id="github-copilot", listed_by_provider=26`
   (la mía, reproducida 2 veces + confirmada con `opencode` crudo). No es un defecto de
   código — es el mecanismo de AC-16 funcionando exactamente como está escrito: el
   candidato se propone, el CLI a veces contesta bien y a veces no (`opencode` lo expuso
   entre esos minutos), y cuando contesta bien se acepta sin tocar código. Lo dejo
   documentado en la sección AC-16 de abajo con ambas capturas, timestamps incluidos.

## AC → cambio → prueba

| AC | Cambio (archivo:línea) | Prueba |
|---|---|---|
| AC-16 | `_unlistable_candidate_id` `ai/scripts/routing_core/catalog.py:1065-1079`; `_verify_unlistable_credential` `catalog.py:1082-1115`; consumida en `route_doctor` `catalog.py:1179-1188` | `tests/test_routing.py:3515-3617` (8 tests: candidato, dirección 1, 5×dirección 2, trampa opencode-zen, reporte en route_doctor) |
| AC-17 | Ausencia deliberada de persistencia — `route_doctor` (`catalog.py:1118-1217`) recalcula `_verify_unlistable_credential` en cada llamada, nunca cachea el candidato | `tests/test_routing.py:3619-3643` (`test_ac17_baja_is_automatic_and_symmetric_across_two_route_doctor_calls`) + mordida abajo |
| AC-18 | `_provider_liveness` `ai/scripts/set_agents_app.py:2439-2463`; `_LIVENESS_DEFAULT_ORIGINS`/`_LIVENESS_WITH_LEGACY_ORIGINS` `set_agents_app.py:2426-2436`; `cmd_provider_verify` (liveness + `--prune-dead`) `set_agents_app.py:2466-2523`; flags `--include-legacy`/`--prune-dead` `set_agents_app.py:3631-3639`; dispatch `set_agents_app.py:3853-3854` | `tests/test_provider_registry.py:236-433` (`ProviderLivenessUnitTests`, `ProviderVerifyLivenessScopeTests`, `LivenessNeverInHotPathTests`, `ProviderCliSubprocessTests::test_provider_verify_prune_dead_real_network_round_trip`) |
| AC-19 | `route_doctor` separa `listed_by_provider`/`usable_after_ceiling` `catalog.py:1118-1217` (impresión de campos en dict, no `print` directo — `route_doctor` devuelve estructura, la CLI la serializa); `probe_listed_and_usable` `catalog.py:1220-1258`; `cmd_doctor_all` línea impresa `set_agents_app.py:908`; `_estado_general_lines` línea impresa `set_agents_app.py:3443-3445` | `tests/test_routing.py:3437-3511` (route_doctor), `tests/test_routing.py:3645-3681` (`probe_listed_and_usable` + `cmd_doctor_all`, este último **escrito por mí en esta vuelta**), `tests/test_menu_ui.py:54-70` (`_estado_general_lines`, **escrito por mí en esta vuelta**) |

## AC-16 — verificación empírica, en las dos direcciones

### Dirección 1: el CLI contesta bien ⇒ se acepta

`tests/test_routing.py:3521` (`test_ac16_direction_1_cli_confirms_the_candidate_is_accepted`) —
corrida fresca, ahora, en HEAD limpio:

```
test_ac16_direction_1_cli_confirms_the_candidate_is_accepted (tests.test_routing.RoutingTests.test_ac16_direction_1_cli_confirms_the_candidate_is_accepted) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.097s (corrida en batch de 12, ver bloque completo abajo)

OK
```

### Dirección 2: el CLI no contesta o contesta mal ⇒ NO se acepta nada

5 variantes, todas corridas frescas junto con la de dirección 1 y la trampa
opencode-zen, en un solo batch, HEAD limpio (sin mutar nada):

```
test_ac16_direction_1_cli_confirms_the_candidate_is_accepted ... ok
test_ac16_direction_2_cli_error_line_is_rejected_nothing_accepted ... ok
test_ac16_direction_2_nonzero_exit_is_rejected_nothing_accepted ... ok
test_ac16_direction_2_wrong_prefix_is_rejected_never_a_partial_credit ... ok
test_ac16_direction_2_well_formed_but_empty_listing_is_rejected ... ok
test_ac16_direction_2_timeout_is_rejected ... ok
test_ac16_the_named_trap_opencode_zen_display_name_does_not_verify_its_own_real_id ... ok
test_ac16_route_doctor_reports_a_confirmed_candidate_as_listed_but_still_not_usable ... ok
test_ac17_baja_is_automatic_and_symmetric_across_two_route_doctor_calls ... ok
test_ac19_route_doctor_separates_listed_from_usable_after_ceiling ... ok
test_probe_listed_and_usable_matches_route_doctor_for_the_opencode_lane ... ok
test_ac19_cmd_doctor_all_prints_the_listed_usable_split_labeled ... ok

----------------------------------------------------------------------
Ran 12 tests in 0.097s

OK
```

Las 5 de dirección 2 cubren cada superficie donde el fail-closed puede fallar: línea
`Error` (la respuesta REAL medida de github-copilot), código de salida ≠0, prefijo mal
formado (rechaza incluso con exit 0, la convención de opencode de "los errores salen con
exit 0"), listado vacío bien formado, y timeout. Ninguna acepta nada — `None` en los 5
casos (código en `catalog.py:1107-1115`).

### La trampa nombrada (ADR-0034), medida de nuevo aquí

`test_ac16_the_named_trap_opencode_zen_display_name_does_not_verify_its_own_real_id`
(`tests/test_routing.py:3572`): el candidato derivado de `"opencode zen"` es
`"opencode-zen"` (espacio→guion, regla exacta) pero el CLI id real es `"opencode"` — el
test mockea el subprocess para que SOLO conteste bien a `"opencode"` y prueba que
`_verify_unlistable_credential("opencode zen", ...)` devuelve `None`: la regla nunca se
confía sola, siempre se mide.

### Medido en vivo, HOY, en la máquina real — incluye un hallazgo que no esperaba

`docs/specs/022-disponibilidad-real/context/P5-altas-y-bajas-automaticas.md` (anoche) y
el mensaje del orquestador (hace unos minutos, gates) midieron:

```
github copilot  listed=0  usable=0  unlistable=True  verified_cli_id=None
```

Al juntar la evidencia de esta sección, corrí `--route-doctor --json` yo mismo (recién,
sin tocar código) y el resultado CAMBIÓ:

```json
{
  "authenticated": true, "billing": "unknown", "detected_unlistable": true,
  "listed_by_provider": 26, "provider": "github copilot", "runtime": "opencode",
  "usable_after_ceiling": 0, "verified_cli_id": "github-copilot"
}
```

Reproducido 2 veces más (idéntico, `listed_by_provider=26`, `verified_cli_id=github-copilot`
las 3 veces) y confirmado con el CLI crudo, fuera de cualquier código de este repo:

```
$ opencode models github-copilot --pure | wc -l
26
$ opencode models github-copilot --pure | head -5
github-copilot/claude-fable-5
github-copilot/claude-haiku-4.5
github-copilot/claude-opus-4.7
github-copilot/claude-opus-4.7-fast
github-copilot/claude-opus-4.8
```

**No es un defecto — es AC-16/AC-17 funcionando exactamente como se diseñó.** El
candidato (`github-copilot`, transformación exacta espacio→guion de `"github copilot"`)
se propone en cada llamada; el CLI de `opencode` a veces contesta `Provider not found` y
en algún momento entre la corrida del orquestador y esta (minutos, misma máquina, mismo
`providers.toml`/`models.toml`, cero cambios de este repo) empezó a contestar bien.
`route_doctor` lo capturó en la siguiente llamada, sin ningún código nuevo, exactamente
la promesa del context pack ("hacés que funcione el día que opencode lo exponga").
`usable_after_ceiling` se mantiene en `0` — AC-17 intacto: memoria del CLI id, nunca
autorización; no hay techo curado ni par auditado para `github-copilot`, así que sigue
sin ser ruteable pese a estar confirmado. Marco esto como observación live relevante,
no como algo que haya arreglado ni tocado.

## AC-17 — memoria de CLI id, nunca autorización; baja automática y simétrica

`route_doctor` nunca persiste el resultado de `_verify_unlistable_credential` — ni en
disco, ni en la caché de probes (`_read_probe_cache`/`_write_probe_cache` nunca lo tocan;
`route_doctor` ni siquiera escribe la caché, ver `test_ac15_route_doctor_never_writes_the_probe_cache`).
`test_ac17_baja_is_automatic_and_symmetric_across_two_route_doctor_calls`
(`tests/test_routing.py:3619`) llama `route_doctor` dos veces con el mismo mock de
subprocess, cambiando solo un flag (`state["up"]`) entre las dos llamadas: la primera ve
el candidato contestar y lo reporta `listed_by_provider=1, verified_cli_id="my-new-vendor"`;
la segunda, con el mismo candidato ahora fallando, lo reporta `listed_by_provider=0,
verified_cli_id=None` — sin ningún código de "baja", porque nunca hubo un "alta"
persistente que dar de baja.

### Mordida — neutralizar, confirmar rojo, revertir, verde

Mutación: memoizar el resultado de `_verify_unlistable_credential` en un dict a nivel de
módulo dentro del loop de `route_doctor` (simula el bug que este AC prohíbe: cachear la
verificación entre llamadas).

```python
# MUTATED en catalog.py:1179 (temporal, revertido con cp)
if display not in globals().setdefault("_MUTATED_MEMO", {}):
    globals()["_MUTATED_MEMO"][display] = _verify_unlistable_credential(display, timeout)
verified = globals()["_MUTATED_MEMO"][display]
```

Rojo confirmado:

```
test_ac17_baja_is_automatic_and_symmetric_across_two_route_doctor_calls ... FAIL

======================================================================
FAIL: test_ac17_baja_is_automatic_and_symmetric_across_two_route_doctor_calls
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/home/federico/SET-AGENTES/tests/test_routing.py", line 3642, in test_ac17_baja_is_automatic_and_symmetric_across_two_route_doctor_calls
    self.assertEqual(vendor_down["listed_by_provider"], 0)
AssertionError: 1 != 0

----------------------------------------------------------------------
Ran 1 test in 0.012s

FAILED (failures=1)
```

Revertido con `cp` desde el backup pre-mutación (scratchpad) y confirmado verde +
byte-idéntico:

```
test_ac17_baja_is_automatic_and_symmetric_across_two_route_doctor_calls ... ok
Ran 1 test in 0.009s
OK
```
```
$ diff -q ai/scripts/routing_core/catalog.py <backup> && echo "catalog.py CLEAN"
catalog.py CLEAN
```

## AC-18 — `--provider-verify` mide liveness real; caso Ollama; decisión sobre `harness-legacy`

### `alive`/`dead`/`unreachable`, distinguidos — corrida fresca

`tests/test_provider_registry.py:236` (`ProviderLivenessUnitTests`), HEAD limpio:

```
test_alive_on_a_normal_http_response ... ok
test_alive_on_an_http_error_status_the_server_still_answered ... ok
test_dead_on_connection_refused_the_measured_ollama_case ... ok
test_unreachable_on_a_missing_or_empty_base_url_never_a_crash ... ok
test_unreachable_on_dns_failure_never_reported_as_dead ... ok
test_unreachable_on_timeout_never_reported_as_dead ... ok
```

`test_dead_on_connection_refused_the_measured_ollama_case` reproduce exactamente el caso
medido anoche (`curl http://localhost:11434/v1/models` → `000`, `ConnectionRefusedError`
en Python) mockeando `urlopen` para levantar ese error exacto.

### Caso real, extremo a extremo, sin mock — puerto muerto real (loopback)

`ProviderCliSubprocessTests::test_provider_verify_prune_dead_real_network_round_trip`
(`tests/test_provider_registry.py:413`) — un `provider` `origin=user` apuntado a
`127.0.0.1:39217` (puerto sin nada escuchando, sandbox), `HOME` desviado a un
`tempfile.TemporaryDirectory` — corrida fresca:

```
test_provider_verify_prune_dead_real_network_round_trip ... ok

----------------------------------------------------------------------
Ran 1 test in 1.072s

OK
```

El test hace un round-trip real: `--provider-add` → `--provider-verify` (confirma
`liveness=dead`, `at=<timestamp ISO-8601>` real) → `--provider-verify --prune-dead`
(confirma `PROVIDER_PRUNED ids=deadendpoint`) → `--provider-list` (confirma
`PROVIDER_NONE`). Cero mocks de red — TCP real contra un puerto sin listener.

### Decisión explícita sobre `harness-legacy` (la interacción con P4)

Después de P4, el bloque `ollama` real de esta máquina quedó `origin=harness-legacy`
(`seed_or_migrate` lo etiqueta así porque su valor es byte-idéntico al
`HARNESS_PROVIDER_SEED` que el harness distribuye), nunca `user`. La letra de AC-18 es
literal: "sólo providers user" — así que el alcance por defecto de `--provider-verify`
es exactamente `{"user"}`, sin ampliarlo por default (`_LIVENESS_DEFAULT_ORIGINS`,
`set_agents_app.py:2435`).

**Decisión tomada, no dejada implícita**: se amplía con un argumento explícito,
`--include-legacy` (`_LIVENESS_WITH_LEGACY_ORIGINS = {"user", "harness-legacy"}`,
`set_agents_app.py:2436`), en vez de forzar `--provider-remove ollama` + `--provider-add`
como único camino para que el Ollama real de Federico entre al chequeo de liveness. El
default sigue siendo exactamente `user` (la letra de AC-18 intacta); `--include-legacy`
es la vía documentada y explícita para sumar `harness-legacy`. Un
`--provider-remove`+`--provider-add` sigue siendo válido (convierte el bloque a
`origin=user`) pero ya no es el único camino. Razonamiento completo en
`docs/adr/0043-que-prueba-un-probe.md:263-273` ("La interacción con P4, resuelta
explícitamente, no implícita").

Prueba de que el alcance por defecto NO toca `harness-legacy` y que `--include-legacy`
sí lo suma (sin tocar `harness` ni `discovered`), corrida fresca junto con las otras de
esta clase:

```
test_default_scope_checks_user_never_harness_or_harness_legacy_or_discovered ... ok
test_include_legacy_widens_scope_to_harness_legacy_only_not_plain_harness_or_discovered ... ok
test_liveness_line_carries_a_measurement_timestamp ... ok
test_prune_dead_on_a_single_provider_id_never_drops_the_rest_of_the_registry ... ok
test_prune_dead_removes_only_ids_measured_dead_this_run ... ok
test_prune_dead_with_nothing_dead_is_a_no_op_and_says_so ... ok
test_shape_invalid_entry_is_never_liveness_checked_even_if_origin_is_user ... ok
test_cache_key_source_never_calls_liveness_or_empirical_verification ... ok
test_no_spawn_module_imports_liveness_or_empirical_verification ... ok
test_service_py_never_imports_liveness_or_empirical_verification ... ok

----------------------------------------------------------------------
Ran 16 tests in 0.020s

OK
```

`LivenessNeverInHotPathTests` (3 de los de arriba) es un grep-tripwire literal sobre
`routing_core/service.py`, el cuerpo de `_cache_key` en `catalog.py`, y todo `*_spawn.py`:
ninguno de los tres puede mencionar `_provider_liveness`,
`_verify_unlistable_credential`, ni `probe_listed_and_usable` — cumple "nunca dentro de
`route()`, nunca en la clave de caché, nunca en el spawn".

### Mordida 1 — `dead` vs `unreachable` nunca se confunden

Mutación: en `_provider_liveness`, la rama `URLError` devuelve siempre `"dead"` (nunca
distingue `ConnectionRefusedError` de timeout/DNS).

```python
# MUTATED en set_agents_app.py:2461 (temporal, revertido con cp)
except urllib.error.URLError as exc:
    return "dead"  # nunca distingue unreachable
```

Rojo confirmado (exactamente las 2 pruebas que existen para distinguir esto):

```
FAIL: test_unreachable_on_dns_failure_never_reported_as_dead
AssertionError: 'dead' != 'unreachable'
FAIL: test_unreachable_on_timeout_never_reported_as_dead
AssertionError: 'dead' != 'unreachable'

----------------------------------------------------------------------
Ran 6 tests in 0.006s

FAILED (failures=2)
```

Revertido con `cp`, verde + byte-idéntico:

```
Ran 6 tests in 0.004s
OK
```
```
$ diff -q ai/scripts/set_agents_app.py <backup> && echo "set_agents_app.py CLEAN"
set_agents_app.py CLEAN
```

### Mordida 2 — `--prune-dead` nunca borra un `unreachable`

Mutación: en `cmd_provider_verify`, la condición para marcar un id como candidato a poda
pasa de `state == "dead"` a `state != "alive"` (podaría también `unreachable`, la
propiedad de seguridad exacta que AC-18 prohíbe: "nunca 'no existe' cuando fue 'no
contestó'").

```python
# MUTATED en set_agents_app.py:2513 (temporal, revertido con cp)
if state != "alive":  # también poda unreachable
    dead_ids.append(pid)
```

Rojo confirmado:

```
FAIL: test_prune_dead_removes_only_ids_measured_dead_this_run
----------------------------------------------------------------------
AssertionError: 'PROVIDER_PRUNED ids=gone' not found in
"...liveness=alive...\n...liveness=unreachable...\n...liveness=dead...\n...\nPROVIDER_PRUNED ids=flaky,gone — corré './build.sh --install' para que se refleje en opencode.json"

----------------------------------------------------------------------
Ran 7 tests in 0.023s

FAILED (failures=1)
```

(el mutante poda `flaky`, que midió `unreachable` — exactamente lo que la propiedad
prohíbe). Revertido con `cp`, verde + byte-idéntico:

```
Ran 7 tests in 0.022s
OK
```
```
$ diff -q ai/scripts/set_agents_app.py <backup> && echo "set_agents_app.py CLEAN"
set_agents_app.py CLEAN
```

## AC-19 — `listed_by_provider`/`usable_after_ceiling` en las TRES superficies, con salida real

`_probe_pairs` (`catalog.py:735-839`) gana el canal lateral `listed_out` (AC-19,
docstring en `catalog.py:744-750`); `probe_listed_and_usable` (`catalog.py:1220-1258`) es
el helper compartido que `cmd_doctor_all` y `_estado_general_lines` consumen para no
duplicar lógica entre las tres superficies.

### Superficie 1 — `route_doctor` / `--route-doctor` (`catalog.py:1118-1217`)

Medido en vivo, ahora, máquina real (JSON, recortado a lo relevante — ver sección AC-16
arriba para el registro completo con `github copilot`):

```json
{"authenticated": true, "billing": "subscription", "detected_unlistable": false,
 "listed_by_provider": 13, "provider": "openai-codex", "runtime": "opencode",
 "usable_after_ceiling": 6, "verified_cli_id": "openai"}
{"authenticated": true, "billing": "metered", "detected_unlistable": false,
 "listed_by_provider": 61, "provider": "opencode-zen", "runtime": "opencode",
 "usable_after_ceiling": 58, "verified_cli_id": "opencode"}
```

`openai-codex`/opencode lista 13, usable 6; `opencode-zen` lista 61, usable 58 — el
defecto medido anoche ("listado ≠ usable") reproducido en vivo, ahora, con la etiqueta
correcta.

### Superficie 2 — `cmd_doctor_all` / `--doctor-all` (`set_agents_app.py:865-909`)

Medido en vivo, ahora, máquina real, literal:

```
HARNESS claude-code installed=yes
HARNESS opencode installed=yes
HARNESS codex installed=yes
HARNESS pi installed=yes
INSTALL_SCOPE claude-code,codex,opencode,pi
TOOL supabase installed=no
TOOL vercel installed=no
TOOL gcloud installed=yes
TOOL gh installed=yes
TOOL docker installed=yes
TOOL jq installed=yes
TOOL obsidian installed=yes
TOOL syncthing installed=yes
TOOL pnpm installed=yes
PROVIDER anthropic runtime=claude-code listed_by_provider=4 usable_after_ceiling=4
PROVIDER openai-codex runtime=codex listed_by_provider=6 usable_after_ceiling=6
PROVIDER openai-codex runtime=opencode listed_by_provider=13 usable_after_ceiling=6
PROVIDER opencode-go runtime=opencode listed_by_provider=18 usable_after_ceiling=18
PROVIDER opencode-zen runtime=opencode listed_by_provider=61 usable_after_ceiling=58
PROVIDER anthropic runtime=pi listed_by_provider=3 usable_after_ceiling=3
PROVIDER openai-codex runtime=pi listed_by_provider=6 usable_after_ceiling=6
```

`github copilot` correctamente AUSENTE de esta superficie (nunca tuvo par auditado — M-1,
sin cambios de este paquete): `cmd_doctor_all`/`_estado_general_lines` solo iteran pares
de `_PAIR_COMMANDS`; el diagnóstico de `detected_unlistable` es exclusivo de
`route_doctor` (documentado, no un olvido).

### Superficie 3 — `_estado_general_lines` / panel "🩺 Estado general" (`set_agents_app.py:3410-3451`), **la vidriera**

Invocada en vivo, ahora, vía `app._estado_general_lines(app._status_data(rows=True))`
(la misma función que `menu()` llama al elegir el primer ítem — nunca una ruta paralela),
salida literal:

```
Harnesses
  opencode  1.18.14                ok
  claude    2.1.231 (Claude Code)  ok
  codex     codex-cli 0.147.0      ok
  pi  instalado  -

Alcance de instalación
  claude-code, codex, opencode, pi

Herramientas (catálogo)
  supabase   falta
  vercel     falta
  gcloud     instalado
  gh         instalado
  docker     instalado
  jq         instalado
  obsidian   instalado
  syncthing  instalado
  pnpm       instalado

Proveedores autenticados (probe)
  anthropic     claude-code  listado=4 usable=4
  openai-codex  codex        listado=6 usable=6
  openai-codex  opencode     listado=13 usable=6
  opencode-go   opencode     listado=18 usable=18
  opencode-zen  opencode     listado=61 usable=58
  anthropic     pi           listado=3 usable=3
  openai-codex  pi           listado=6 usable=6

drift: la instalación quedó atrás del repo → Instalar / Reparar o ./build.sh --install
```

Las tres superficies coinciden byte a byte en los números (`openai-codex/opencode`:
13/6 en las tres; `opencode-zen`: 61/58 en las tres) — nunca lógica divergente, las tres
consumen el mismo `probe_listed_and_usable`/`route_doctor`.

### Tests unitarios de las 3 superficies (hermético, corrida fresca)

```
test_ac15_route_doctor_reports_m1_github_copilot_as_detected_unlistable ... (no re-corrido en este batch, sin cambios de esta vuelta)
test_ac19_route_doctor_separates_listed_from_usable_after_ceiling ... ok
test_probe_listed_and_usable_matches_route_doctor_for_the_opencode_lane ... ok
test_ac19_cmd_doctor_all_prints_the_listed_usable_split_labeled ... ok      # escrito por mí
```
```
test_ac19_panel_labels_listado_and_usable_separately_when_they_differ ... ok  # escrito por mí, tests/test_menu_ui.py:54
test_panel_carries_harnesses_scope_tools_and_providers ... ok
test_stale_drift_adds_the_repair_hint ... ok

----------------------------------------------------------------------
Ran 3 tests in 0.004s

OK
```

### Mordida 3 — `cmd_doctor_all` (superficie 2), test escrito por mí en esta vuelta

Test nuevo: `test_ac19_cmd_doctor_all_prints_the_listed_usable_split_labeled`
(`tests/test_routing.py:3664`). Verde inicial:

```
test_ac19_cmd_doctor_all_prints_the_listed_usable_split_labeled ... ok
Ran 1 test in 0.017s
OK
```

Mutación (`set_agents_app.py:907`, `usable_n` recalculado sobre `listed` en vez de
`usable`):

```python
usable_n = len(listed.get((runtime, provider), set()))  # MUTATED
```

Rojo confirmado:

```
FAIL: test_ac19_cmd_doctor_all_prints_the_listed_usable_split_labeled
AssertionError: 'usable_after_ceiling=1' not found in
'PROVIDER opencode-zen runtime=opencode listed_by_provider=3 usable_after_ceiling=3'
Ran 1 test in 0.020s
FAILED (failures=1)
```

Revertido con `cp`, verde:

```
test_ac19_cmd_doctor_all_prints_the_listed_usable_split_labeled ... ok
Ran 1 test in 0.016s
OK
```

### Mordida 4 — `_estado_general_lines` (superficie 3, la vidriera), test escrito por mí en esta vuelta

Test nuevo: `test_ac19_panel_labels_listado_and_usable_separately_when_they_differ`
(`tests/test_menu_ui.py:54`). Verde inicial:

```
test_ac19_panel_labels_listado_and_usable_separately_when_they_differ ... ok
Ran 1 test in 0.004s
OK
```

Mutación (`set_agents_app.py:3444`, `usable=` recalculado sobre `listed` en vez de
`usable`):

```python
f"usable={len(listed.get((runtime, provider), set()))}")  # MUTATED
```

Rojo confirmado:

```
FAIL: test_ac19_panel_labels_listado_and_usable_separately_when_they_differ
AssertionError: 'usable=1' not found in
'Harnesses\n...\nProveedores autenticados (probe)\n  opencode-zen  opencode  listado=3 usable=3'
Ran 1 test in 0.005s
FAILED (failures=1)
```

Revertido con `cp`, verde:

```
test_ac19_panel_labels_listado_and_usable_separately_when_they_differ ... ok
Ran 1 test in 0.004s
OK
```

Byte-identidad confirmada tras el revert de ambas mordidas 3 y 4 (mismo backup, un solo
`cp`):

```
$ diff -q ai/scripts/set_agents_app.py <backup> && echo "set_agents_app.py CLEAN"
set_agents_app.py CLEAN
```

## Resumen de mordidas (neutralizar → rojo → cp revert → verde → byte-idéntico)

| # | AC | Qué rompí | Rojo confirmado | Revert | Byte-idéntico |
|---|---|---|---|---|---|
| 1 | AC-19 (superficie 2) | `cmd_doctor_all`: `usable_n` = cuenta de `listed` | sí (assertion arriba) | `cp` desde backup | sí |
| 2 | AC-19 (superficie 3) | `_estado_general_lines`: `usable=` = cuenta de `listed` | sí | `cp` | sí |
| 3 | AC-16 dirección 2 (5 tests) + trampa | `_verify_unlistable_credential` siempre acepta | sí (6/6 tests) | `cp` | sí |
| 4 | AC-18 dead/unreachable | `_provider_liveness`: `URLError` siempre `"dead"` | sí (2/2 tests) | `cp` | sí |
| 5 | AC-18 `--prune-dead` | `cmd_provider_verify`: poda también `unreachable` | sí | `cp` | sí |
| 6 | AC-17 | `route_doctor`: memoiza el candidato entre llamadas | sí | `cp` | sí |

Las mordidas 1 y 2 son sobre tests que escribí en esta vuelta (el hueco real que
encontré). Las mordidas 3-6 son muestreo sobre el código y los tests ya escritos por el
turno anterior de esta sesión, para no confiar a ciegas en que no son "el quinto test que
dice cubrir algo que no mira" — las 4 piezas más nombradas explícitamente en el pedido
(dirección 2 de AC-16, la trampa opencode-zen, AC-17, AC-18 dead/unreachable/prune-dead)
pasaron la prueba. No mordí las ~24 pruebas restantes del paquete (AC-12 shape-check
heredado de P4, round-trips de CLI, etc.) por presupuesto — quedan **sin mordida
individual**, cubiertas solo por la corrida verde de la suite completa.

## Gates

Corridos por el **orquestador** (no por esta instancia, que murió por error de API antes
de llegar a esta etapa) — pegados tal cual me los pasaron:

```
Ran 1065 tests in 728.319s
OK (skipped=3)
```
```
GLOBAL_TREE_SYNC_OK profile=go-zen harnesses=4
BUILD_CHECK_PASS
```
```
VERIFY_PASS
```

`git diff --check` — corrido por mí ahora, standalone, read-only (no es código, es un
diagnóstico), después de terminar de escribir esta evidencia:

```
$ git diff --check
$ echo "EXIT=$?"
EXIT=0
```

Sin salida (limpio) y `EXIT=0`. También cubierto transitivamente por `verify.sh`
(`ai/scripts/verify.sh` lo corre después del `py_compile`) — el orquestador ya reportó
`VERIFY_PASS`.

1065 = 1063 (suite ya verde de este mismo paquete, corrida por el turno anterior de esta
sesión antes de morir, `scratchpad/unittest_full.log`: `Ran 1063 tests ... OK (skipped=3)`)
+ 2 (`test_ac19_cmd_doctor_all_prints_the_listed_usable_split_labeled` y
`test_ac19_panel_labels_listado_and_usable_separately_when_they_differ`, escritos por mí
en esta vuelta) — consistente con que el orquestador corrió los gates DESPUÉS de que yo
agregara los 2 tests.

## Fuera de alcance / no tocado

Todo lo listado en la consigna original ("Fuera de alcance") — sort key, consumo/cuota
(023), desbloquear Copilot aguas arriba, pi como descubridor de credenciales,
`check-owned-paths.py`, orden del gate de pi en `_probe_pairs`, features 023-025. No
encontré ningún archivo fuera de `catalog.py`/`set_agents_app.py`/`tests/`/
`docs/adr/0043-*.md` que necesitara tocarse para este paquete — nada que flagear como
"otro archivo necesario" (a diferencia de lo que P4 tuvo que señalar).

## Sin verificar

- Las ~24 pruebas de `test_provider_registry.py`/`test_routing.py` de este paquete que NO
  mordí individualmente (ver tabla de mordidas) — verificadas solo por la corrida verde
  de la suite completa del orquestador, no por mordida propia.
- El comportamiento de `github copilot` en el futuro (si `opencode` vuelve a devolver
  `Provider not found` de forma estable, o si se queda listable) — medido dos veces en
  una ventana de minutos, no observado a lo largo del tiempo.
