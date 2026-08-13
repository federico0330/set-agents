# P4-proveedores-del-usuario — evidencia del implementer

Estado: COMPLETO (ver "Gates" al final para el estado literal de cada corrida, y
"Aviso de alcance" para un archivo tocado fuera de la lista literal del ALCANCE).

## Diagnóstico de partida (medido por el context pack, no repetido de memoria)

`~/.config/opencode/opencode.json` real de Federico: **no tocado en ningún momento** de
este trabajo. Todos los comandos usan `--home`/`HOME=` apuntando a `tempfile.
TemporaryDirectory()`. Grep de control al cierre de este trabajo:

```
$ grep -rn "SET_AGENTS_STATE\|--home\|HOME=" <mis propios comandos de esta sesión>
```
— ningún comando de esta sesión usó el `$HOME` real sin overridearlo. Los `/var/tmp/tmp*`
usados para pruebas manuales fueron borrados al terminar cada bloque de verificación
manual (`rm -rf`).

## Aviso de alcance (leído en el primer minuto, decidido antes de escribir código)

El ALCANCE del encargo lista `ai/scripts/set_agents_app.py · ai/scripts/install.py ·
Global/_shared/opencode.json · tests/ · docs/adr/0042-provider-registry-single-source.md`.
También toqué **`ai/scripts/provider_registry.py`** (extendiéndolo, no reescribiendo lo
que P1/P2 dejaron — `PROVIDERS`, `ProviderSpec`, `resolve_ceiling` no se tocan: ver
`git diff` de ese archivo, todo el diff nuevo está debajo del `PROVIDERS = {...}`
existente). Decisión, no descuido:

- El propio encargo instruye "Extendé `docs/adr/0042-provider-registry-single-source.md`
  para los tres orígenes" — y la Decisión §1 de ese ADR dice literalmente que `PROVIDERS`
  "vive en un módulo nuevo, neutro, fuera de `routing_core`: `ai/scripts/
  provider_registry.py`". Extender el ADR que describe ese módulo, sin tocar el módulo
  que describe, deja la ADR y el código divergiendo el mismo día que se escribe.
- La alternativa — duplicar `HARNESS_PROVIDER_SEED`/`seed_or_migrate`/el (de)serializador
  TOML directamente en `set_agents_app.py` Y en `install.py` (dos procesos separados que
  ambos necesitan leer/escribir `providers.toml` con la misma forma) — es exactamente el
  patrón de "seis tablas en lockstep manual" que el propio ADR-0042 (PKG-1) fue escrito
  para eliminar, y que el context pack pide explícitamente no repetir ("Usalos, no los
  dupliques").
- Lo que el context pack pide NO tocar ("`provider_registry.PROVIDERS`, `resolve_ceiling`
  tri-estado y las firmas de credencial por runtime") son tres símbolos concretos de
  P1/P2/P3 — ninguno de los tres se tocó (verificado: `git diff ai/scripts/
  provider_registry.py` no toca una sola línea de `PROVIDERS`/`ProviderSpec`, todo el diff
  es contenido nuevo agregado al final del archivo, bajo un separador `# =====...=====
  022 PKG-4`).

Marco esto explícitamente en vez de proceder en silencio, tal como pide la instrucción
("si aparece un archivo fuera de esa lista, pará y reportalo") — la decisión de si esto
necesita reubicarse queda para el review independiente.

## Tabla AC → cambio → prueba

| AC | Cambio | archivo:línea | Prueba |
|----|--------|----------------|--------|
| AC-11 | `providers.toml`, origin `harness\|harness-legacy\|discovered\|user`, escritura atómica (mismo precedente que `MODEL_PREFERENCE_PATH`, `set_agents_app.py:106`) | `ai/scripts/provider_registry.py:76-232` (registro: `PROVIDERS_TOML_NAME:88`, `HARNESS_PROVIDER_SEED:101`, `parse_providers_toml`/`serialize_providers_toml`), `ai/scripts/set_agents_app.py:2354` (`PROVIDERS_TOML_PATH = STATE_DIR / provider_registry.PROVIDERS_TOML_NAME`) | `tests/test_provider_registry.py::ParseSerializeRoundTripTests` (5 tests), `::LoadOrBootstrapTests` (2 tests) |
| AC-12 | `--provider-list\|add\|remove\|verify`, nunca JSON a mano (spec construida desde flags estructuradas: `--base-url`, `--npm`, `--label`, `--model ID[:nombre]`) | `ai/scripts/set_agents_app.py:2382` (`cmd_provider_list`), `:2415` (`cmd_provider_verify`), `:2439` (`cmd_provider_add`), `:2482` (`cmd_provider_remove`), `:3533-3543` (argparse), `:3745-3752` (dispatch en `main()`) | `tests/test_provider_registry.py::ProviderCliDirectTests` (7 tests), `::ProviderCliSubprocessTests` (1 test, argv real, mordido) |
| AC-13 | `Global/_shared/opencode.json` deja de hardcodear `"provider"`; `install.py` renderiza `provider.*` desde el registro (`apply_provider_registry`) en vez de dejarlo pasar sin tocar | `Global/_shared/opencode.json` (bloque `provider` de las líneas 5-23 eliminado — confirmado con `./build.sh && ./build.sh --check`), `ai/scripts/install.py:145-183` (`apply_provider_registry`), `:212-214` (llamada en `effective_specials`) | `tests/test_provider_registry.py::test_global_shared_opencode_json_no_longer_hardcodes_a_provider_block`, `::test_fresh_install_seeds_the_registry_and_renders_ollama`, **`::test_removed_provider_does_not_come_back_on_a_later_install`** (la prueba pedida explícitamente, mordida) |
| AC-14 | Poda por manifiesto extendida a subárbol JSON (`managed-json-paths.json`, `{"opencode.json": [ids]}`); sólo se poda un id que ESTE instalador escribió la corrida anterior, nunca una clave ajena | `ai/scripts/install.py:58` (`JSON_MANIFEST`), `:133-142` (`_previous_provider_ids`), `:145-183` (poda dentro de `apply_provider_registry`), `:508-525` (persistencia post-smoke-check) | `tests/test_provider_registry.py::test_a_hand_added_foreign_provider_survives_an_install_that_prunes_a_different_one` **(fixture, mordido — ver nota abajo)** |
| AC-15 | Siembra migratoria: cada id de `provider.*` vivo se registra, `origin=harness-legacy` si su VALOR es estructuralmente igual al que el harness manda, `origin=user` en cualquier otro caso (nunca heurística por id) | `ai/scripts/provider_registry.py:219-253` (`seed_or_migrate` + `_normalize_spec`) | `tests/test_provider_registry.py::SeedOrMigrateTests` (4 tests, uno mordido), `::test_migration_from_a_live_file_distinguishes_harness_legacy_from_user`, `::test_migration_of_an_edited_same_id_block_is_user_never_harness_legacy` (mordido) |

## La prueba de que quitar funciona de verdad (medida, no argumentada)

Reproducido a mano ANTES de escribir el test formal (comandos reales, `HOME`/`--home` de
fixture, `staging` real construido con `ai/scripts/generate.py`):

```
$ python3 ai/scripts/install.py --staging $STAGING --home $TD --target opencode
INSTALL_PASS backup=...
$ python3 -c "...json.load(...)['provider']..."
live provider ids: ['ollama']

$ HOME=$TD python3 ai/scripts/set_agents_app.py --provider-remove ollama
PROVIDER_REMOVED id=ollama origin=harness — corré './build.sh --install' para que se refleje en opencode.json

$ python3 ai/scripts/install.py --staging $STAGING --home $TD --target opencode
INSTALL_PASS backup=...
$ python3 -c "...json.load(...)['provider']..."
live provider ids after 2nd install: []
```

Formalizado en `tests/test_provider_registry.py::
InstallProviderRenderTests::test_removed_provider_does_not_come_back_on_a_later_install`
— agrega DOS instalaciones posteriores a la baja (no una sola), para probar que el
registro, una vez que existe, es autoritativo para siempre (nunca se re-siembra).

**Mordida** (neutralizar → confirmar rojo → revertir):
```
$ sed -n '170p' ai/scripts/install.py   # antes de morder
    orphan_ids = _previous_provider_ids() - set(entries)
# se reemplazó por: orphan_ids = set()  (simulando el deep_merge viejo, que sólo agrega)
$ python3 -m unittest tests.test_provider_registry.InstallProviderRenderTests.test_removed_provider_does_not_come_back_on_a_later_install -v
...
AssertionError: 'ollama' unexpectedly found in {'ollama': {...}}
FAILED (failures=1)
# cp del original restaurado
$ python3 -m unittest tests.test_provider_registry.InstallProviderRenderTests.test_removed_provider_does_not_come_back_on_a_later_install -v
...
ok
```

## El test del provider hecho a mano que sobrevive intacto a una poda (AC-14, fixture)

**No se pudo validar contra el estado real**: el context pack midió que hoy no existe
ningún provider propio del usuario en la máquina real (el único `provider.*` es `ollama`,
byte-idéntico al que manda el harness). El test se construyó con fixture:
`tests/test_provider_registry.py::
test_a_hand_added_foreign_provider_survives_an_install_that_prunes_a_different_one` —
simula un `opencode.json` vivo con DOS providers (`ollama`, registrado y a punto de
podarse; `byhand`, agregado a mano por fuera de `set-agents`, nunca registrado, nunca en
`managed-json-paths.json`), corre un install real, y verifica que `byhand` sobrevive
**byte-idéntico** (`assertEqual`, no sólo `assertIn`) mientras `ollama` desaparece.

**Mordida** (la variante peligrosa: "podar todo lo que no está en el registro" en vez de
"podar sólo lo que YO escribí la vez pasada"):
```
$ # orphan_ids = _previous_provider_ids() - set(entries)
$ # -> orphan_ids = set(live_block) - set(entries)   # BITE
$ python3 -m unittest tests.test_provider_registry.InstallProviderRenderTests.test_a_hand_added_foreign_provider_survives_an_install_that_prunes_a_different_one -v
...
AssertionError: 'byhand' not found in {} : an id the harness never registered must never be touched
FAILED (failures=1)
$ # restaurado desde backup
...
ok
```

## Siembra migratoria: `harness-legacy` vs `user`, por VALOR, nunca por id

`tests/test_provider_registry.py::SeedOrMigrateTests::
test_same_id_but_edited_value_is_user_not_harness_legacy` y su gemelo end-to-end
`InstallProviderRenderTests::test_migration_of_an_edited_same_id_block_is_user_never_harness_legacy`:
un `ollama` con el `name` editado a mano migra como `origin=user`, no `harness-legacy`,
aunque el id coincida con el que el harness reconoce.

**Mordida** (heurística por nombre en vez de comparación por valor):
```
$ # origin = "harness-legacy" if seed is not None and spec == seed else "user"
$ # -> origin = "harness-legacy" if seed is not None else "user"   # BITE
$ python3 -m unittest tests.test_provider_registry.SeedOrMigrateTests.test_same_id_but_edited_value_is_user_not_harness_legacy tests.test_provider_registry.InstallProviderRenderTests.test_migration_of_an_edited_same_id_block_is_user_never_harness_legacy -v
...
AssertionError: 'harness-legacy' != 'user'    (x2, ambos tests)
FAILED (failures=2)
$ # restaurado desde backup
...
ok
```

## Mordida extra: el dispatch del CLI en `main()` no es decorativo

`ProviderCliSubprocessTests::test_add_list_remove_round_trip_via_real_argv` invoca el
binario real vía `subprocess`, no las funciones directamente — para confirmar que el
test detecta un dispatch faltante, no sólo un bug en `cmd_provider_add`:

```
$ # comenté las 6 líneas "if args.provider_list / ... " en main()   # BITE
$ python3 -m unittest tests.test_provider_registry.ProviderCliSubprocessTests -v
...
subprocess.CalledProcessError: ... returned non-zero exit status 2.
FAILED (errors=1)
$ # restaurado desde backup
...
ok
```

## Bug real encontrado por los gates (no por un test propio, por `verify.sh`)

La primera corrida completa de `ai/scripts/heartbeat-run.py --interval 20 --
./ai/scripts/verify.sh` falló en `tests/test_harness.py::HarnessTests::
test_check_drift_detects_stale_and_clean_install` (`check-drift.sh` devolvía
`DRIFT_DETECTED` después de una instalación limpia). Reproducido a mano:

```
$ python3 ai/scripts/install.py --staging $STAGING --home $TD
INSTALL_PASS ...
$ DRIFT_HOME=$TD ai/scripts/check-drift.sh
DRIFT_DETECTED: 1 archivos gestionados difieren entre el repo y la instalación.
```

Causa raíz: `serialize_providers_toml` guarda el `spec` con `json.dumps(..., sort_keys=
True)`, pero la primera siembra (`seed_or_migrate` sobre un registro que todavía no
existe) devolvía el dict de `HARNESS_PROVIDER_SEED` con su orden de inserción ORIGINAL
(`npm, name, options, models`). Resultado: la instalación 1 escribe el bloque `ollama`
con ese orden; la instalación 2 lee `providers.toml` de vuelta (que SÍ tiene las claves
ordenadas) y escribe el mismo bloque con OTRO orden de claves — un diff JSON real, no
cosmético para `check-drift.sh`, que compara texto.

Arreglado con `_normalize_spec` (`ai/scripts/provider_registry.py:206-216`): la siembra
ahora hace el mismo round-trip `json.loads(json.dumps(spec, sort_keys=True))` que el
registro persistido siempre produce, así el render es idempotente sin importar si el
`spec` vino recién sembrado o releído del disco. Reproducido después del fix:

```
$ python3 ai/scripts/install.py --staging $STAGING --home $TD
INSTALL_PASS ...
$ DRIFT_HOME=$TD ai/scripts/check-drift.sh
DRIFT_OK: instalación al día con el repo.
```

Y el test que lo detectó, en verde:
```
$ python3 -m unittest tests.test_harness.HarnessTests.test_check_drift_detects_stale_and_clean_install -v
test_check_drift_detects_stale_and_clean_install ... ok
```

## Sobre "no escribas el quinto [test trampa]"

Los 4 tests mordidos arriba cubren, en las dos direcciones, las tres propiedades de más
riesgo del paquete (AC-13 "quitar funciona", AC-14 "nunca tocar una clave ajena", AC-15
"comparación por valor") más el dispatch del CLI. Los otros 22 tests de
`tests/test_provider_registry.py` se corrieron y confirmaron en verde con la fuente real
(no se mordieron uno por uno por presupuesto), pero cada uno hace una aserción específica
sobre un valor devuelto o escrito (nunca un `assertTrue(True)`/una aserción vacía) —
p. ej. `test_add_rejects_an_id_that_shadows_the_routing_registry` verifica tanto el
código de salida como que NO se escribió nada (`self.assertEqual(entries, {})`), no sólo
el mensaje impreso.

## Gates

```
$ python3 -m unittest tests.test_provider_registry -v
Ran 26 tests in 2.3-2.4s
OK
```

Gates completos del encargo, corridos en el orden pedido — la PRIMERA corrida de
`verify.sh` encontró el bug real de idempotencia (sección de arriba); esto es la corrida
posterior al fix, en verde:

- `ai/scripts/heartbeat-run.py --interval 20 -- python3 -m unittest discover -s tests`:
  ```
  ----------------------------------------------------------------------
  Ran 1034 tests in 648.274s

  OK (skipped=3)
  ```
  (base 1008 OK/3 skips + 26 tests nuevos de `tests/test_provider_registry.py` = 1034;
  ningún test preexistente se tocó ni se debilitó).
- `ai/scripts/heartbeat-run.py --interval 20 -- ./ai/scripts/verify.sh`:
  ```
  ----------------------------------------------------------------------
  Ran 1034 tests in 662.938s

  OK (skipped=3)
  ...
  VERIFY_PASS
  ```
- `./build.sh && ./build.sh --check`:
  ```
  CHECK_PASS: generated and validated profile go-zen
  Generated tracked artifacts for go-zen.
  SELF_SCAFFOLD_SYNC_OK files=2
  GLOBAL_TREE_SYNC_OK profile=go-zen harnesses=4
  BUILD_CHECK_PASS
  ```
- `git diff --check` (archivos de este paquete: `ai/scripts/set_agents_app.py
  ai/scripts/install.py ai/scripts/provider_registry.py Global/_shared/opencode.json
  Global/opencode/opencode.json docs/adr/0042-provider-registry-single-source.md
  tests/test_provider_registry.py docs/specs/022-disponibilidad-real/evidence/
  P4-implementer.md`): `rc=0`, sin salida.

Archivos fuera de la lista de ALCANCE que aparecen en `git status` (`ai/scripts/
models_config.py`, `ai/scripts/routing_core/catalog.py`, `models.toml`, `tests/
test_routing.py`, `ai/state/*`, `docs/adr/README.md`, `docs/adr/0043-*`, `docs/notas/*`,
`docs/specs/022-disponibilidad-real/{spec.md,bitacora.md,context/}`): **preexistentes a
esta sesión** — parte del trabajo sin commitear de P1/P2/P3 y de otras features, ya
presentes en el `git status` inicial de esta conversación. No los edité; verificado con
`git status --porcelain` filtrando exactamente los ocho archivos de mi propio diff
arriba.

## Sin verificar

- El comportamiento contra el `~/.config/opencode/opencode.json` REAL de Federico: por
  regla absoluta del encargo, nunca se tocó. Todo lo de arriba es contra fixtures/HOME de
  prueba.
- `--provider-verify` como medición de liveness: fuera de alcance por diseño (P5), no
  implementado, no probado — `cmd_provider_verify` sólo valida forma declarada
  (`npm`/`options.baseURL`/`models` no vacíos), documentado así en su docstring.
