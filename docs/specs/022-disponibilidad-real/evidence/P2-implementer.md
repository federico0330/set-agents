# P2-techo-catalogo-tri-estado — evidencia del implementer

Estado: COMPLETO

## Baseline p50/p90 (ANTES, código sin tocar)

Medición en vivo de catálogos (antes de tocar nada), `opencode` real en el PATH:
```
$ opencode auth list --pure
●  OpenCode Go api / ●  OpenAI oauth / ●  GitHub Copilot oauth / ●  OpenCode Zen api  (4 credenciales)
$ opencode models opencode --pure | wc -l
61
$ opencode models opencode-go --pure | wc -l
18
```
`models.toml` curaba (y sigue curando, sin tocar esas dos listas) 60 de los 61 zen ids — drift
de un snapshot tomado en otro momento, no un defecto de este paquete.

Script (`/var/tmp/.../scratchpad/bench_snapshot.py`, no commiteado): config real
(`models.toml`), roster real (`roles.tsv`), `ai/catalogs/routes.v1.toml` real, `inventory`
sintetizado con los 60 zen + 18 go ids REALES curados hoy. 300 corridas.

```
$ python3 bench_snapshot.py   # ANTES, catalog.py sin modificar (commit previo a este paquete)
zen=60 go=18
routes=88 inferred=82 identities=100
build_effective_snapshot ms: p50=3.3830 p90=3.5721 n=300
sort-only ms: p50=0.0459 p90=0.0465 n=300
```

`sort-only` reproduce la forma EXACTA de la sort key de `service.py:382` (misma tupla de
campos, incluyendo `billing_rank`) sobre la lista completa de rutas ya construida por
`build_effective_snapshot` — nunca toca `service.py`, solo mide su costo con datos reales.

## Tabla AC → cambio → prueba

| AC | Cambio | `archivo:línea` | Prueba |
|---|---|---|---|
| AC-04 | `resolve_ceiling` reemplaza `_configured_models`, tri-estado puro | `ai/scripts/routing_core/catalog.py:221-274` | `test_adr0042_pkg2_ac04_resolve_ceiling_is_a_pure_tri_state_reflection_of_the_toml` (`tests/test_routing.py:3632`) |
| AC-04 sitio 1 | `_probe_pairs`: `if state == "veto": continue` reemplaza `if not allowed: continue` | `catalog.py:517-591` (chequeo en `:541-542`) | `test_adr0042_pkg2_ac04_probe_pairs_probes_a_provider_with_no_catalog_key_instead_of_skipping_it` (`tests/test_routing.py:3648`) — MORDIDO |
| AC-04 sitio 2 (el más fácil de romper) | `_read_probe_cache`: bifurca `veto`→descarta, `auto`→conserva sin reintersectar, `curated`→reintersecta como antes | `catalog.py:433-480` (bifurcación en `:470-476`) | `test_adr0042_pkg2_ac04_read_probe_cache_auto_mode_never_goes_permanently_empty` (`tests/test_routing.py:3673`) — MORDIDO |
| AC-04 sitio 3 | `build_snapshot`: `configured_models = {p: resolve_ceiling(config, p) for p in PROVIDERS}` (ya no hardcodea la tupla de 4 proveedores) | `catalog.py:720` | Cubierto por el AC-06 test + `test_ac04_site3_configured_models_comprehension_is_load_bearing` preexistente (sigue verde) |
| AC-04 (models_config) | `[]` explícito ya no muere; ausencia sigue siendo válida | `ai/scripts/models_config.py:160-167` | `test_adr0042_pkg2_ac04_models_config_accepts_empty_list_veto_and_round_trips_it` (`tests/test_routing.py:3792`) — MORDIDO |
| AC-05 capa 1 (auditado) | Sin cambio de código — reverificado: `probe_inventory` filtra por `_PAIR_COMMANDS` antes de llamar a `_probe_pairs` | `catalog.py:640` (`selected = [pair for pair in pairs if pair in _PAIR_COMMANDS]`) | Aserción dentro de `test_adr0042_pkg2_ac04_probe_pairs_...` (`tests/test_routing.py:3648`) — MORDIDO (ver abajo) |
| AC-05 capa 2 (auto nunca curado) | El chequeo de AC-06 en `build_snapshot` + prueba positiva de que sólo llega por la vía sintetizada | `catalog.py:743-745` (negativo) + `catalog.py:940-990` `build_effective_snapshot` (positivo) | `test_adr0042_pkg2_ac05_layer2_auto_ceiling_reaches_only_the_synthesized_path` (`tests/test_routing.py:3712`) — MORDIDO |
| AC-05 capa 3 (billing fail-closed) | Sin cambio de código (`billing_rank`, preexistente ADR-0035) — reverificado explícitamente que el estado de techo no lo toca | `catalog.py:191-202` | `test_adr0042_pkg2_ac05_layer3_billing_rank_still_fails_closed_expensive_under_auto` (`tests/test_routing.py:3737`) — MORDIDO |
| AC-05 capa 4a (cap) | `_DISCOVERED_ROUTE_CAP_PER_PROVIDER = 80`, truncación alfabética post-filtro | `catalog.py:911-923` (constante) + `catalog.py:968-975` (aplicación) | `test_adr0042_pkg2_ac05_layer4_discovered_route_cap_bounds_the_pool_deterministically` (`tests/test_routing.py:3751`) — MORDIDO |
| AC-05 capa 4b (`provider:*`) | `(provider, "*") in exclusions` vetea el proveedor entero en la vía sintetizada | `catalog.py:968-969` | `test_adr0042_pkg2_ac05_layer4_exclude_provider_wildcard_vetoes_the_entire_provider` (`tests/test_routing.py:3772`) — MORDIDO |
| AC-06 | `RoutingError("CATALOG_CEILING_REQUIRED")`, nombrado y distinto de `CATALOG_INVALID` | `catalog.py:734-749` (chequeo) + `catalog.py:763-772` (repair del `except` que lo tragaba) | `test_adr0042_pkg2_ac06_curated_row_against_auto_or_veto_ceiling_raises_the_named_error` (`tests/test_routing.py:3691`) — MORDIDO |
| Comentario `[catalog]` | Reescrito para describir el contrato tri-estado, no el viejo | `models.toml:16-33` | Lectura directa; `python3 -c "import models_config; models_config.load_config()"` sigue cargando sin morir |
| ADR-0042 | Extendido con sección PKG-2 (no se creó uno nuevo) | `docs/adr/0042-provider-registry-single-source.md:157-232` | Lectura directa |

## Los tres consumidores migrados — con la prueba específica del caché

Los tres sitios que el context pack nombra (`_probe_pairs:487-489`, `_read_probe_cache:429`,
`build_snapshot:652-653`, numeración PRE-edición) migraron a `resolve_ceiling`. La prueba
específica de que el caché **no** queda siempre vacío en modo auto:

```
$ python3 -m unittest tests.test_routing.RoutingTests.test_adr0042_pkg2_ac04_read_probe_cache_auto_mode_never_goes_permanently_empty -v
test_adr0042_pkg2_ac04_read_probe_cache_auto_mode_never_goes_permanently_empty ... ok
Ran 1 test in 0.003s
OK
```

Bite confirmado (ver sección "Mordidas" abajo): con la reintersección ingenua restaurada
(`set(models) & (ceiling or set())`), el mismo test da:
```
AssertionError: {} != {('opencode', 'opencode-zen'): {'some-live-only-zen-model'}}
```
— exactamente el "caché siempre vacío en modo auto" que el context pack advierte como el
defecto más fácil de introducir.

## Las cuatro capas de AC-05 — cada una con su test (y su mordida)

1. **Auditado** (`_PAIR_COMMANDS`): sin cambio de código en este paquete; reverificado con
   `("opencode", "not-an-audited-provider")` pasado a `probe_inventory` — nunca llega a
   `_probe_pairs`. Mordida: neutralizar el filtro `pair in _PAIR_COMMANDS` en `probe_inventory`
   → `KeyError: ('opencode', 'not-an-audited-provider')` (rojo vía excepción, no solo
   aserción — la guarda evita exactamente ese crash en producción).
2. **Auto nunca entra al snapshot curado**: probado en dos direcciones dentro del mismo test —
   negativo (`build_snapshot` con fila curada + techo auto → `CATALOG_CEILING_REQUIRED`) y
   positivo (`build_effective_snapshot` con el mismo techo auto → ruta sintetizada, `route_id`
   presente en el `frozenset` de `inferred`).
3. **Billing desconocido ⇒ rank caro**: `billing_rank("opencode-zen", ...)` → `1` sin importar
   el estado de techo (`PROVIDER_BILLING_KIND` no lee config). Mordida: `billing_rank` forzado a
   `return 0` siempre → `AssertionError: 0 != 1`.
4. **Cap + `exclude` extendido**: cap mordido con `for model in candidates:` (sin slice) → 240
   rutas en vez de 80; `provider:*` mordido quitando la condición → el modelo vetado aparece en
   el snapshot.

## `CATALOG_CEILING_REQUIRED` disparando de verdad

```
$ python3 -m unittest tests.test_routing.RoutingTests.test_adr0042_pkg2_ac06_curated_row_against_auto_or_veto_ceiling_raises_the_named_error -v
test_adr0042_pkg2_ac06_curated_row_against_auto_or_veto_ceiling_raises_the_named_error ... ok
Ran 1 test in 0.008s
OK
```

Repair encontrado implementando esto (documentado en el ADR): `RoutingError` hereda de
`ValueError` (`routing_core/domain.py:9`), así que el `except (KeyError, TypeError, ValueError):
raise RoutingError("CATALOG_INVALID")` de `build_snapshot` atrapaba mi propio
`CATALOG_CEILING_REQUIRED` (recién lanzado dentro del mismo `try`) y lo degradaba en silencio al
genérico — confirmado con el mordisco: sacando el `except RoutingError: raise` que agregué antes
del `except` amplio, el mismo test da:
```
AssertionError: "CATALOG_CEILING_REQUIRED" does not match "CATALOG_INVALID" : auto
```
De paso esto también repara `CATALOG_COLLISION` (`catalog.py:759`), que por el mismo motivo
nunca había sido alcanzable ni ejercitado por ningún test existente — no hay ningún test en el
repo que lo verifique, así que no hay riesgo de regresión, y el fix es estrictamente el mismo
guard que AC-06 necesita (mismo `except`, misma línea).

## Números p50/p90 antes y después

Pool real (60 zen + 18 go, `build_effective_snapshot`, 300 corridas cada uno):

| | p50 (ms) | p90 (ms) |
|---|---|---|
| ANTES (catalog.py sin tocar) | 3.3830 | 3.5721 |
| DESPUÉS (con `resolve_ceiling` + cap 80) | 3.3817 | 3.4744 |
| `sort-only` ANTES (misma forma que `service.py:382`) | 0.0459 | 0.0465 |
| `sort-only` DESPUÉS | 0.0464 | 0.0469 |

Con el catálogo real de hoy la diferencia está dentro del ruido de medición — **el cap no mueve
la aguja hoy porque 60/18 ya están debajo de 80**. Lo digo explícito, sin disimularlo: la
protección es contra el crecimiento sin techo en modo `"auto"` (un proveedor futuro sin lista
curada, o un catálogo upstream que crezca), no una optimización medible con los datos de hoy. El
sort en sí (`service.py:382`, nunca tocado) tarda ~0.046 ms con las 88 rutas reales — el costo
real está en construir `StaticRoute`/identidades por modelo, no en ordenarlas.

Corrida de estrés (sintética, 6× el cap = 480 ids zen ofrecidos, 100 corridas), para mostrar que
el cap sí importa fuera del caso de hoy:

```
$ python3 bench_stress.py
WITH cap=80: pool_offered=480 routes_added=80
WITH cap ms: p50=3.5847 p90=3.6840 n=100
WITHOUT cap (patched a un techo mayor que el pool): pool_offered=480 routes_added=480
WITHOUT cap ms: p50=15.8116 p90=16.0073 n=100
```

Con 6× el pool, sin cap el tiempo crece ~4.4× (15.81 ms vs 3.58 ms) — casi lineal con la
cantidad de rutas sintetizadas, confirmando que el cap acota tanto el conteo como el costo.

## Mordidas — resumen literal (revertidas todas, `cp`/`cp`, nunca `git checkout`)

Cada mordida: backup con `cp` a scratchpad → edición quirúrgica que neutraliza exactamente el
cambio nuevo → corrida del test específico → confirmar rojo (pegado arriba, literal) → `cp` de
vuelta desde el backup → confirmar verde de nuevo. Las ocho mordidas hechas:

1. `_read_probe_cache` auto→reintersección ingenua: rojo confirmado, restaurado, verde.
2. `except RoutingError: raise` en `build_snapshot`: rojo confirmado (2 tests), restaurado, verde.
3. `_probe_pairs` `if not allowed` (pre-tri-state): rojo confirmado, restaurado, verde.
4. `models_config.py` rechazo de `[]`: rojo confirmado (`die()`, aún más contundente que una
   aserción), restaurado, verde.
5. Cap de `_DISCOVERED_ROUTE_CAP_PER_PROVIDER` quitado: rojo confirmado (240 != 80), restaurado, verde.
6. `provider:*` quitado del chequeo de exclusión: rojo confirmado, restaurado, verde.
7. `billing_rank` forzado a `return 0`: rojo confirmado, restaurado, verde.
8. Filtro `pair in _PAIR_COMMANDS` de `probe_inventory` quitado (capa 1): rojo confirmado vía
   `KeyError`, restaurado, verde.

Tras cada restauración corrí `diff` contra el backup guardado para confirmar bit-a-bit que el
archivo volvió exactamente al estado bueno (no solo "los tests pasan"):
```
$ diff catalog.py.good ai/scripts/routing_core/catalog.py && echo "IDENTICAL - restored correctly"
IDENTICAL - restored correctly
```

## Gates — salida literal

Gate 1:
```
$ ai/scripts/heartbeat-run.py --interval 20 -- python3 -m unittest discover -s tests
...
----------------------------------------------------------------------
Ran 990 tests in 804.385s

OK (skipped=3)
```
Base era 981 OK / 3 skips; 990 = 981 + los 9 tests nuevos de este paquete. 0 failures, 0 errors,
mismos 3 skips que la base (los e2e credential-gated, sin cambios).

Gate 2:
```
$ ai/scripts/heartbeat-run.py --interval 20 -- ./ai/scripts/verify.sh
... (build.sh --check, unittest discover -v completo, py_compile, git diff --check,
     comparación Global/ contra un build limpio, chequeos de portabilidad)
GLOBAL_PORTABILITY_OK
CANONICAL_PATHS_OK
FEATURE_STATE_OK
VERIFY_PASS
```
`verify.sh` corre `build.sh --check` y la suite completa (`-v`) de nuevo por dentro — ambos
verdes, exit code 0.

Gate 3:
```
$ ./build.sh --check
SELF_SCAFFOLD_SYNC_OK files=2
GLOBAL_TREE_SYNC_OK profile=go-zen harnesses=4
BUILD_CHECK_PASS
```

Gate 4:
```
$ git diff --check
$ echo "EXIT_CODE=$?"
EXIT_CODE=0
```
Salida vacía, exit 0 — sin errores de whitespace en el diff.

## Fuera de alcance — confirmado, no tocado

`service.py:382` (sort key) — no editado, sólo medido con su misma forma de clave.
`routes.v1.toml` — no se agregaron filas curadas; el catálogo real (`ai/catalogs/routes.v1.toml`)
sólo se LEYÓ en tests/benchmarks, nunca escrito. `providers.toml`, `--provider-*`, de-auth,
firma de credencial, Copilot, `check-owned-paths.py`: no tocados. Alcance final: exactamente los
cinco archivos declarados (`ai/scripts/routing_core/catalog.py`, `ai/scripts/models_config.py`,
`models.toml`, `tests/test_routing.py`, `docs/adr/0042-provider-registry-single-source.md`).
Ningún sexto archivo apareció.
