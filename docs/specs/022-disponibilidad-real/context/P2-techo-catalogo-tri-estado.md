# Context pack — P2-techo-catalogo-tri-estado

Spec: `docs/specs/022-disponibilidad-real/spec.md`, **AC-04, AC-05, AC-06**. Depende de **P1**,
que ya está `accepted`: existe `ai/scripts/provider_registry.py` con `PROVIDERS`, y
`_CATALOG_KEYS` (`catalog.py:218`) deriva de ahí el mapa provider → clave de `[catalog]`.

## El defecto en una línea

`_probe_pairs` (`catalog.py:487-489`) hace `allowed = _configured_models(config, provider)` y
después `if not allowed: continue`. Un proveedor sin clave en `[catalog]` **se saltea entero**.
Hoy sumar un proveedor sí requiere editar config, que es exactamente lo que el pedido de Federico
quiere eliminar.

## Medición que te ahorra media exploración: el tri-estado YA está a medias

No arranques asumiendo que hay que construirlo desde cero. Medido hoy:

| Estado | Validación (`models_config.py`) | `catalog.py` |
|---|---|---|
| lista | válida (`:156-160`) | techo curado, funciona |
| **ausente** | **YA es válida** — `if values is not None and (...)` | colapsa a `set()` ⇒ se saltea |
| **`[]` vacía** | **muere** — `not values` ⇒ `die` | colapsa a `set()` ⇒ se saltea |

Y `emit` (`:509-512`) **ya round-trippea la ausencia** sin inventar una lista vacía.

O sea el trabajo real es:

1. **`catalog.py`**: distinguir *ausente* de *presente-pero-vacía*, que hoy son el mismo `set()`.
   Ahí está el 80% del paquete.
2. **`models_config.py:156-160`**: aceptar `[]` explícita, que hoy mata. Ese es el veto.
3. **`models.toml`**: actualizar el comentario del bloque `[catalog]`, que hoy describe el
   contrato viejo.

`_configured_models` se reemplaza por
`resolve_ceiling(config, provider) -> ("curated", set) | ("auto", None) | ("veto", set())`.

## Los TRES consumidores. Los tres, o el paquete no cierra.

| Sitio | Línea de hoy | Por qué importa |
|---|---|---|
| `_probe_pairs` | `catalog.py:487-489` | el `if not allowed: continue` — el defecto |
| `_read_probe_cache` | `catalog.py:429` | `intersected = set(models) & _configured_models(...)` |
| `build_snapshot` | `catalog.py:652-653` | además tiene la lista de proveedores **hardcodeada** |

**Ojo con `_read_probe_cache:429-431`**: re-intersecta contra el techo al leer, y descarta el par
si la intersección queda vacía. En modo `auto` una intersección ingenua deja el **caché siempre
vacío**, y probeás en cada decisión. Es el defecto más fácil de introducir acá.

Sobre `build_snapshot:652-653`: el reviewer de P1 argumentó —con la spec en la mano, AC-01 vs
AC-04— que ese literal hardcodeado es **alcance tuyo**, no de P1. Te toca.

## Las tres decisiones ya tomadas. Ejecutalas, no las re-litigues.

### 1. El tri-estado es SOLO para `opencode_zen` y `opencode_go`
Decisión de Federico (2026-08-12). `[catalog].claude` y `[catalog].codex` **siguen siendo listas
obligatorias no vacías**. Razón medida: `models_config.py:147-150` las exige con `die`;
`load_roles:366-371` hace `catalog["claude"]`/`catalog["codex"]`/`catalog["codex_effort"]`
**sin fallback**; `:212` indexa `config["catalog"]["codex"]` para el check de Sol de pi; y son las
únicas con filas curadas en `routes.v1.toml` — si pasaran a auto, cada fila curada existente
dispararía el `CATALOG_CEILING_REQUIRED` de AC-06.

**`codex_effort` queda explícitamente afuera**: es una lista de efforts, no un techo de
proveedor. Que la redacción genérica "`<key>`" lo incluyera fue un error de la primera spec.

### 2. Del precedente de `[subscriptions]` se toma la FORMA, no el manejo de error
`models_config.py:375-397` es el precedente de tri-estado. Pero ahí "ausente" degrada a `WARN` y
sigue, porque es validación de build. **Acá alimenta el filtrado en vivo del snapshot de ruteo, y
AC-06 exige que el caso malo falle fuerte y nombrado.** Importar esa mansedumbre contradice AC-06.

### 3. AC-06: `CATALOG_CEILING_REQUIRED`, no el genérico
Una fila curada de `routes.v1.toml` que apunte a un proveedor en auto/veto falla con su propio
código. Hay precedente de diferenciar: `CATALOG_FAMILY_COLLISION` (`catalog.py:618-620`) existe
justamente porque el genérico `CATALOG_INVALID` no decía nada.

## AC-05 — cuatro capas, cada una con su test

Sin esto, "auto" es una puerta abierta. Las cuatro:

1. El par tiene que estar **auditado** (`_PAIR_COMMANDS`).
2. Lo auto **nunca** entra al snapshot curado — sólo por la vía sintetizada, con
   `MODEL_METADATA_INFERRED`.
3. Billing desconocido ⇒ rank caro (ya lo hace `billing_rank`, `catalog.py:186-191`: fail-closed
   hacia lo caro). Verificá que sigue siendo cierto con proveedores en auto.
4. Cap determinístico por proveedor + `[catalog].exclude` extendido a `provider:*`.

**Riesgo medido a vigilar**: zen lista **58-61 modelos** (`opencode models opencode --pure`, medido
hoy). Sin cap, el pool de rutas sintetizadas se infla y el sort se hace más lento. Medí p50/p90
antes y después y pegá los números; si el cap no alcanza, decilo en vez de disimularlo.

## Alcance declarado por adelantado

`owned_paths` del paquete son `catalog.py`, `models.toml` y `tests/test_routing.py`. Al preparar
este pack se identificó —**antes** de implementar— que el trabajo también toca
`ai/scripts/models_config.py` (aceptar `[]`) y `docs/adr/` (extender ADR-0042). El orquestador ya
registró las `approved_exceptions`. **No agregues archivos más allá de esos cinco**; si aparece un
sexto, paralo y reportalo en vez de tocarlo.

Y sabelo: `check-owned-paths.py:40-42` usa `git diff --name-only`, así que **no ve archivos
nuevos**. Que no te avise no significa que estés en alcance — la disciplina la ponés vos.

## Restricciones

- **Extendé `docs/adr/0042-provider-registry-single-source.md`**, no crees uno nuevo: la spec
  asigna a 0042 el registro + el techo tri-estado + los tres orígenes.
- **Sin refactors oportunistas.** No toques el sort key (`service.py:382`). No agregues filas
  curadas a `routes.v1.toml`. No probees dentro de `route()`.
- **No uses `git checkout`, `git restore` ni `git stash`.** Para morder y restaurar: `cp` y `cp`.
- No relajes, saltees ni borres tests.

## Validación

`python3 -m unittest discover -s tests` (**`pytest` NO está instalado**; base **981 OK / 3 skips**)
· `./ai/scripts/verify.sh` → `VERIFY_PASS` · `./build.sh --check` → `GLOBAL_TREE_SYNC_OK` +
`BUILD_CHECK_PASS` · `git diff --check` limpio.

**Corré los comandos largos exactamente así:**

```
ai/scripts/heartbeat-run.py --interval 20 -- python3 -m unittest discover -s tests
```

No los pipees a `tail`: sin `-f` no emite un byte hasta EOF, la suite tarda 7-10 minutos y el
watchdog del runtime te mata a los 600 s (ADR-0041). No es una opción entre varias: es el comando.

## Evidencia

`docs/specs/022-disponibilidad-real/evidence/P2-implementer.md`, escrito **en el primer minuto**:
tabla AC → cambio (`archivo:línea`) → prueba; los tres consumidores migrados, con la prueba
específica de que el caché **no** queda siempre vacío en modo auto; las cuatro capas con su test;
`CATALOG_CEILING_REQUIRED` disparando; los números p50/p90 antes y después; y los gates.

**Por cada test nuevo: neutralizá el cambio, confirmá el rojo, revertí, pegá la prueba.** El review
de P1 encontró que la guarda nueva pasaba en **verde** con la fuente rota, y al verificarlo apareció
que el refactor había vuelto tautológica otra guarda que sí funcionaba. Dos de tres controles
decían OK sobre algo que no miraban. **Mordé todo lo que escribas, en las dos direcciones.**

**Cada bloque que pegues es literal, o está marcado como recortado.** Si no lo corriste, "sin
verificar".

## Checkpoint

Si sentís que te acercás al límite de ejecución, escribí progreso parcial **y los próximos pasos
exactos** en el archivo de evidencia antes de parar.

## Fuera de alcance

La firma de credencial y el de-auth (P3) · `providers.toml` y `--provider-*` (P4) · altas y bajas
automáticas (P5) · el sort key · agregar Copilot · unificar las dos cachés de probe (es **AC-10**,
P3) · arreglar `check-owned-paths.py` · features 023-025.
