# ADR-0042 — Un único `PROVIDERS` del que se derivan las siete tablas de proveedores, el
# techo `[catalog]` tri-estado que consume su `catalog_key`, y el registro `providers.toml`
# de proveedores locales del usuario con sus tres (cuatro) orígenes

- Estado: Accepted (2026-08-12, extendido 2026-08-13). Feature 022-disponibilidad-real,
  PKG-1 (`P1-registro-de-proveedores`), PKG-2 (`P2-techo-catalogo-tri-estado`) y PKG-4
  (`P4-proveedores-del-usuario`).
  Corrige en parte una afirmación de ADR-0034 (Rejected alternatives) — no lo supersede: ADR-0034 sigue
  vigente en todo lo demás.

## Contexto

Medición en vivo sobre el estado actual del repo (antes de este paquete), `grep -rn` de cada símbolo:

| Símbolo | Ubicación | Qué codifica |
|---|---|---|
| `_OPENCODE_PROVIDER_KEYS` | `routing_core/catalog.py:116-117` | provider → texto de credencial que `opencode auth list --pure` imprime |
| `_OPENCODE_CLI_IDS` | `catalog.py:125-126` | provider → argumento CLI de `opencode models <id>` |
| `_PAIR_COMMANDS` | `catalog.py:154-161` | el universo auditado runtime×provider; su mitad `opencode` **ya** deriva de `_OPENCODE_CLI_IDS` (comprehension, no literal) desde 012/F-05 |
| `PROVIDER_BILLING_KIND` | `catalog.py:172-173` | provider → `subscription`\|`metered` |
| key map de `_configured_models` | `catalog.py:215-216` (dentro del cuerpo de la función) | provider → clave de `[catalog]` en `models.toml` |
| `DISCOVERABLE_PROVIDERS` | `models_config.py:41` | el `set` de providers elegibles para `"auto"` (ADR-0034) |
| `_MODEL_PREFERENCE_PROVIDERS` | `set_agents_app.py:94` | la `tuple` **ordenada** que valida pins/preferencias de modelo (ADR-0018/ADR-0034 AC-09) |

Siete símbolos, medidos. **Seis** de ellos son duplicados *manuales* — hoy, agregar un proveedor
exige tocar las seis tablas a mano y nada las liga entre sí salvo la disciplina humana. El séptimo,
`_PAIR_COMMANDS`, ya era una excepción parcial: su mitad `opencode` deriva de `_OPENCODE_CLI_IDS`
desde el repair F-05 de la feature 012 (`catalog.py:149-152`), así que no suma un duplicado nuevo —
pero sigue siendo uno de los siete lugares que un proveedor nuevo toca, porque sus dos pares no-opencode
(`codex`/`openai-codex`, `claude-code`/`anthropic`) usan los ids de provider como claves literales de
dict. Esto resuelve la discrepancia de conteo entre la spec (que llama "seis" en la narrativa de
`docs/specs/022-disponibilidad-real/spec.md` — "de seis entradas en lockstep manual a una fila" — y
sin embargo nombra los siete en la tabla del context pack): **"seis" cuenta los duplicados
verdaderamente manuales; "siete" cuenta todos los símbolos que este paquete mide y dejan de poder
divergir entre sí**, uno de los cuales (`_PAIR_COMMANDS`) ya no era manual antes de este ADR.

### La guarda que decía proteger el sexto duplicado no protegía nada

`tests/test_routing.py:3965` (dentro de `test_adr0034_ac09_write_cli_validates_pins_against_the_
effective_set_not_just_the_constant`, cuyo propósito real es otro: probar que el path de escritura
degrada al set base cuando el probe vivo falla) hace
`self.assertEqual(app._MODEL_PREFERENCE_PROVIDERS, ("openai-codex", "anthropic", "opencode-zen",
"opencode-go"))` — compara contra un literal hardcodeado DENTRO de un `mock.patch` de otro test, no
contra la fuente real. `tests/test_routing.py:3191-3200` (`test_adr0034_ac10_discoverable_providers_
lockstep_guard`) sí es una guarda real, pero solo cubre `DISCOVERABLE_PROVIDERS` — nunca menciona
`_MODEL_PREFERENCE_PROVIDERS`, a pesar de que el comentario de `set_agents_app.py:131-133` afirma
que "AC-10's lockstep test" la cubre también. Es falso: la guarda falta exactamente en el símbolo
que vive en otro archivo.

### El no-goal de `set_agents_app.py:90-94` es más angosto que su propia redacción

Texto literal (antes de este paquete):

```
# The closed, four-provider universe `_PAIR_COMMANDS` already probes
# (`routing_core/catalog.py:133-140`) -- defined independently here, never importing or
# referencing the catalog module's own billing-kind classification table (AC-06 non-goal).
```

La razón nombrada explícitamente (`AC-06 non-goal`, ADR-0018/019 PKG-2 — nunca dejar que la
clasificación *billing-kind* decida qué proveedores son válidos para pins/preferencias, un eje sin
relación) es real y **no cambia** con este paquete: `_MODEL_PREFERENCE_PROVIDERS` sigue sin leer
`PROVIDER_BILLING_KIND` en ningún punto de su derivación. Lo que la redacción generaliza de más es
"never importing" — leído literalmente, prohíbe cualquier import compartido con el módulo de
catálogo, no solo el de billing-kind. Y `:113-114` afirmaba además que el valor es "byte-identical
to `models_config.DISCOVERABLE_PROVIDERS`" en un sentido que nunca fue literalmente cierto: uno es
`set` (sin orden) y el otro una `tuple` ordenada — los VALORES coinciden, el tipo no.

### Dónde puede vivir `PROVIDERS` — restricción dura medida

- `catalog.py` no importa `models_config` en ningún punto (`grep -rn "models_config" routing_core/`
  solo encuentra comentarios).
- `models_config.py` importa `routing_core.catalog` **solo de forma perezosa, adentro de
  funciones** (`detect_subscriptions:257`, `auto_profile:275`), con el docstring explícito
  "Lazy import (no routing_core dependency at module load)".
- Medido: `routing_core/__init__.py` hace `from .service import RoutingService` y `from .store
  import RoutingStore` de forma incondicional — es decir, importar CUALQUIER submódulo de
  `routing_core` (aunque sea uno hoja, sin relación con service/store) ejecuta primero ese
  `__init__.py`, que carga `sqlite3`, `subprocess` (vía `catalog.py`, que `service.py` también
  importa) y el resto de la maquinaria de rutina. Poner `PROVIDERS` dentro de `routing_core`
  (aunque fuera un submódulo nuevo, hoja, sin relación con service/store) y hacer que
  `models_config.py` lo importe a nivel de módulo paga exactamente ese costo en cada `import
  models_config` — el mismo costo que la disciplina de `:250-251` existe para evitar.

## Decisión

1. **`PROVIDERS: dict[str, ProviderSpec]` vive en un módulo nuevo, neutro, fuera de
   `routing_core`**: `ai/scripts/provider_registry.py`. Cero imports de `models_config` ni de
   `routing_core` — solo `dataclasses` de la librería estándar. Es importable a nivel de módulo por
   los tres consumidores sin pagar el costo de `routing_core/__init__.py` ni introducir una
   dependencia de `routing_core` hacia el módulo de configuración de aplicación.
   `ProviderSpec` tiene cuatro campos, uno por eje que hoy vive disperso:
   `opencode_auth_key` (map 1, `_OPENCODE_PROVIDER_KEYS`), `opencode_cli_id` (map 2,
   `_OPENCODE_CLI_IDS`), `billing_kind` (`PROVIDER_BILLING_KIND`), `catalog_key` (la clave de
   `[catalog]` que hoy vive inline en `_configured_models`). El orden de inserción del dict es
   **el contrato de orden** para `_MODEL_PREFERENCE_PROVIDERS`:
   `("openai-codex", "anthropic", "opencode-zen", "opencode-go")`, preservado explícitamente
   porque `tuple(dict)` sí respeta orden de inserción, mientras que `DISCOVERABLE_PROVIDERS`
   (un `set`) nunca podría haberlo dado de forma determinística.
2. **`catalog.py` deriva sus cuatro tablas de `PROVIDERS`** (`_OPENCODE_PROVIDER_KEYS`,
   `_OPENCODE_CLI_IDS`, `PROVIDER_BILLING_KIND`, y un nuevo `_CATALOG_KEYS` module-level que
   reemplaza el dict inline de `_configured_models`) — mismos valores, ahora una sola fuente.
   `_PAIR_COMMANDS` no cambia de código: su mitad `opencode` ya derivaba de `_OPENCODE_CLI_IDS`
   (que ahora, transitivamente, deriva de `PROVIDERS`).
3. **`models_config.DISCOVERABLE_PROVIDERS = set(provider_registry.PROVIDERS)`** — mismo valor,
   ahora derivado, tipo `set` sin cambios (nada que lo consume espera orden).
4. **`set_agents_app._MODEL_PREFERENCE_PROVIDERS = tuple(provider_registry.PROVIDERS)`** — mismo
   valor, mismo orden, ahora derivado en vez de una segunda tupla hardcodeada.
5. **Guarda real nueva** (`tests/test_routing.py`, nueva función,
   `test_adr0042_ac01b_model_preference_providers_is_guarded_against_the_real_source`): compara
   `set_agents_app._MODEL_PREFERENCE_PROVIDERS` contra `_PAIR_COMMANDS`'s propio set de providers
   (`{provider for _, provider in _PAIR_COMMANDS}`, el mismo universo auditado que la guarda de
   `DISCOVERABLE_PROVIDERS` ya usa) **y** contra `tuple(provider_registry.PROVIDERS)` — la fuente
   real, nunca un literal hardcodeado en otro test. `tests/test_routing.py:3965` no se toca: sigue
   pasando (misma tupla, ahora derivada en vez de literal) como prueba incidental adicional, no
   como la guarda.
6. **Se supersede explícitamente la redacción general de `set_agents_app.py:90-94`** ("defined
   independently here, never importing or referencing") por la más angosta que este ADR confirma:
   `_MODEL_PREFERENCE_PROVIDERS` puede (y ahora sí) compartir fuente con el resto de las tablas de
   proveedores, siempre que esa fuente nunca sea la clasificación billing-kind. El comentario se
   reescribe para decir eso, no lo contrario. La afirmación de `:113-114` ("byte-identical to
   `models_config.DISCOVERABLE_PROVIDERS`") se corrige a "mismos valores, misma fuente, tipos
   distintos por diseño (tupla ordenada vs. set)".
7. **Corrige `ADR-0034` "Rejected alternatives"** (`:124-126`): esa sección afirma que un futuro
   `opencode models --refresh` que liste Copilot "activará la adopción automática sin tocar
   código". Es inexacto incluso hoy: sin este paquete, activar Copilot habría exigido tocar las
   seis tablas manuales medidas arriba. Con este paquete, exige exactamente **una** fila nueva en
   `PROVIDERS` (`provider_registry.py`) — de la que las seis tablas se derivan solas — pero **no
   es cero-touch**: sigue habiendo un ProviderSpec por escribir, con sus cuatro campos medidos a
   mano (nunca inferidos), y `_PAIR_COMMANDS`, `routes.v1.toml` y el resto del universo auditado
   igual exigen su propia validación explícita antes de que Copilot sea *routable* (fuera de
   alcance de este paquete: eso es "probeable", no "routable", ADR-0029). No se edita ADR-0034
   retroactivamente — esta sección deja la corrección por escrito y `docs/adr/README.md` marca la
   relación.

## Alternativas rechazadas

- **`PROVIDERS` dentro de `routing_core/catalog.py` (o un submódulo nuevo de `routing_core`)**:
  rechazado por la medición de arriba — cualquier import de un submódulo de `routing_core` ejecuta
  `routing_core/__init__.py`, que carga `service.py`/`store.py` (sqlite3, subprocess) — exactamente
  lo que `models_config.py:250-251`/`:275` existen para evitar en su import a nivel de módulo. Esto
  no es una preferencia estética: es la razón medida y escrita que la disciplina ya documentaba
  antes de este paquete.
- **`PROVIDERS` dentro de `models_config.py`**: rechazado porque `routing_core` se declara
  explícitamente "no CLI imports" (`routing_core/__init__.py:1`) y `models_config.py` es, en la
  práctica, un módulo de aplicación (lee `models.toml` de disco, `die()` en error) — hacer que
  `catalog.py` importe `models_config` invierte la dirección de dependencia que el propio paquete
  declara, y no ganaría nada frente a un módulo neutro.
- **Derivar `_MODEL_PREFERENCE_PROVIDERS` de `models_config.DISCOVERABLE_PROVIDERS`** en vez de la
  fuente común: rechazado porque `DISCOVERABLE_PROVIDERS` es un `set` — derivar una tupla ordenada
  de un `set` produce orden no determinístico entre corridas, y el orden de hoy
  (`openai-codex, anthropic, opencode-zen, opencode-go`) llega a superficie de usuario (mensajes de
  validación de pins).
- **Editar `_PAIR_COMMANDS` para que sus dos pares no-opencode también deriven "más" de
  `PROVIDERS`**: fuera de alcance — ya deriva lo que tenía que derivar (la mitad opencode, desde
  012/F-05) y no es un duplicado manual; tocar su forma es el tipo de refactor oportunista que este
  paquete evita (`catalog.py` no se reorganiza más allá de las cuatro tablas nombradas en AC-01).

## Consecuencias

- Agregar un proveedor nuevo pasa de tocar seis tablas manuales a agregar una fila `ProviderSpec` a
  `PROVIDERS` — las cuatro tablas de `catalog.py`, `DISCOVERABLE_PROVIDERS` y
  `_MODEL_PREFERENCE_PROVIDERS` se actualizan solas. `_PAIR_COMMANDS` sigue necesitando sus propios
  argv auditados a mano para pares nuevos runtime×provider (nunca inferidos — fuera del alcance de
  "derivar", que es sobre identidad de proveedor, no sobre comandos de probe).
- Ningún comportamiento cambia: los siete valores derivados son byte-idénticos a los literales
  previos (test de caracterización, PKG-1 AC-02).
- `set_agents_app.py:90-94`/`:113-114` quedan reescritos para no contradecir al código.
- `ADR-0034` no se edita; esta sección corrige su afirmación con la medición.

## PKG-2 — El techo `[catalog]` tri-estado que consume `catalog_key`

### Contexto

`_CATALOG_KEYS` (derivado de `PROVIDERS.catalog_key`, PKG-1 arriba) alimentaba una función
`_configured_models(config, provider) -> set[str]` que colapsaba dos formas de TOML genuinamente
distintas al mismo valor: la clave `[catalog].<key>` **ausente** del todo, y la clave presente
como **`[]`** explícito, ambas devolvían `set()`. El único consumidor que miraba ese `set()`
(`_probe_pairs`, `catalog.py:487-489` pre-PKG-2) hacía `if not allowed: continue` — así que un
proveedor sin clave dedicada en `[catalog]` se saltea **entero**, lo que en la práctica exige
editar `models.toml` para que un proveedor nuevo participe. Es exactamente lo que el pedido
original de Federico (spec 022, sección "Estado") quiere eliminar: *"que el harness... se dé
cuenta de los modelos disponibles actualmente... sin configuración de por medio"*.

Medido en vivo antes de este paquete (`opencode auth list --pure`, `opencode models opencode
--pure` / `opencode models opencode-go --pure`, 2026-08-12): `opencode-zen` lista 61 modelos,
`opencode-go` 18. `models.toml` curaba 60 de los 61 (drift de un snapshot, no un defecto).

### Decisión

1. **`resolve_ceiling(config, provider) -> ("curated", set) | ("auto", None) | ("veto", set())`**
   (`routing_core/catalog.py`) reemplaza `_configured_models`. Tres estados, reflejo puro de la
   forma TOML literal bajo `[catalog].<key>`:
   - clave ausente (o `provider` sin `catalog_key` dedicado en absoluto — un proveedor futuro
     agregado a `PROVIDERS` sin uno) ⇒ `("auto", None)`: sin techo, el resultado del probe en
     vivo ES el conjunto ruteable, sin filtrar.
   - clave presente como `[]` ⇒ `("veto", set())`: curado, "nunca rutear este proveedor",
     aunque el probe en vivo lo muestre autenticado con modelos reales.
   - clave presente como lista no vacía ⇒ `("curated", set-de-ids)`: el techo auditado (el único
     comportamiento de antes de este paquete, sin cambios).
2. **Tri-estado solo para `opencode-zen`/`opencode-go`** (decisión de Federico, 2026-08-12, no
   re-litigable). `[catalog].claude`/`.codex`/`.codex_effort` siguen siendo listas obligatorias
   no vacías — `models_config.load_config` sigue muriendo si están ausentes o vacías
   (`load_roles` las indexa sin fallback, y son las únicas con filas curadas en
   `routes.v1.toml`). `resolve_ceiling` en sí mismo es agnóstico de proveedor y no impone esa
   restricción — vive en la capa de validación (`models_config.py`), misma separación que este
   ADR ya documenta para el resto del registro (billing-kind nunca sangra a identidad de
   proveedor; acá, "qué proveedores llegan a auto/veto" nunca sangra a "qué significa una forma
   TOML dada").
3. **Los tres consumidores migran**, los tres, o el defecto persiste a medias:
   - `_probe_pairs`: `if state == "veto": continue` reemplaza `if not allowed: continue` — un
     proveedor `"auto"` ya no se saltea; se prueba igual, y el resultado es el listado crudo del
     runtime sin intersección contra ningún techo.
   - `_read_probe_cache` (**el punto más fácil de romper**, medido y confirmado con test mordido
     — ver Evidencia): re-intersectar ingenuamente contra `set()` en modo `"auto"` deja el caché
     **siempre vacío** en cada lectura, y el decisor termina probeando en cada decisión (hasta
     `PI_PROBE_MIN_TIMEOUT_SECONDS`, 60 s, en pi). La lectura ahora bifurca: `"veto"` descarta el
     par; `"auto"` conserva los modelos cacheados tal cual (no hay techo contra el que
     reintersectar); `"curated"` reintersecta como antes.
   - `build_snapshot`: el diccionario `configured_models` pasa de un `for provider in
     ("openai-codex", "anthropic", "opencode-zen", "opencode-go")` **hardcodeado** a
     `for provider in PROVIDERS` (el registro de PKG-1) — un proveedor futuro agregado al
     registro ya queda cubierto sin un segundo edit a este archivo.
4. **AC-06**: una fila curada de `routes.v1.toml` (o de cualquier catálogo con esa forma) que
   nombra un proveedor cuyo techo resuelve a `"auto"`/`"veto"` falla con
   `RoutingError("CATALOG_CEILING_REQUIRED")`, nombrado y distinto del `CATALOG_INVALID`
   genérico — mismo precedente que `CATALOG_FAMILY_COLLISION` (`catalog.py:594-620`). El chequeo
   corre **antes** de mirar `enabled_providers`: "no hay techo contra el cual curar" es el
   diagnóstico más específico, incluso cuando "este proveedor no está habilitado" también sería
   cierto.
   **Repair encontrado implementando esto**: `RoutingError` hereda de `ValueError`
   (`routing_core/domain.py:9`), así que el `except (KeyError, TypeError, ValueError): raise
   RoutingError("CATALOG_INVALID")` que envuelve el parseo de cada fila **atrapaba su propio
   `CATALOG_CEILING_REQUIRED`** (y, latente desde antes de este paquete, nunca ejercitado por
   ningún test, también `CATALOG_COLLISION`) y lo degradaba en silencio al genérico. Un `except
   RoutingError: raise` antes del `except` amplio deja que un `RoutingError` nombrado se
   propague como sí mismo; solo un fallo de forma genuino (`KeyError`/`TypeError`/`ValueError`
   plano) se convierte en `CATALOG_INVALID`.
5. **AC-05, cuatro capas, cada una con su test** (ver Evidencia para el detalle mordido de cada
   una):
   - Capa 1 — el par debe estar **auditado** (`_PAIR_COMMANDS`): sin cambios de este paquete,
     pero reverificado — un par ausente de `_PAIR_COMMANDS` nunca se prueba, `"auto"` o no
     (estructuralmente, vía el filtro de `probe_inventory`).
   - Capa 2 — lo `"auto"` **nunca** entra al snapshot curado, solo a la vía sintetizada
     (`build_effective_snapshot`), marcado en el `frozenset` de `inferred` que
     `service.py` lee como `MODEL_METADATA_INFERRED`.
   - Capa 3 — billing desconocido ⇒ rank caro (`billing_rank`, ya existente, ADR-0035):
     verificado que sigue siendo cierto con el proveedor en `"auto"` — `billing_rank` está keyed
     únicamente por el string de proveedor (`PROVIDER_BILLING_KIND`), nunca por config ni por
     estado de techo, así que no puede cambiar entre `"curated"` y `"auto"`.
   - Capa 4 — **cap determinístico por proveedor** (`_DISCOVERED_ROUTE_CAP_PER_PROVIDER = 80`,
     truncación alfabética tras filtrar curados/excluidos — nunca orden de iteración de dict/set)
     y **`[catalog].exclude` extendido a `"provider:*"`** (veta el proveedor completo de la vía
     sintetizada, junto al `"provider:model"` preexistente, sin interferir entre sí).
6. **`models_config.py:155-160` acepta `[]`** para `opencode_zen`/`opencode_go`: antes moría con
   `die()` (el caso que se vuelve el veto). Absent sigue sin tocar (continúa siendo válido, sin
   cambios); `[]` ahora es una forma válida y distinta, y `emit()` la round-trippea sin
   inventarla ni perderla (ya lo hacía para la ausencia; ahora también para `[]`).

### Riesgo medido: el pool sin techo

`opencode-zen` lista 58-61 modelos en vivo. Sin cap, el pool de rutas sintetizadas
(`build_effective_snapshot`) crecería sin límite en modo `"auto"` — a diferencia del techo
curado de hoy, que por accidente ya lo acota a lo que un humano curó. Medido antes/después
(`build_effective_snapshot` sobre el catálogo real, 60 zen + 18 go, 300 corridas):

| | p50 (ms) | p90 (ms) |
|---|---|---|
| Antes (sin `resolve_ceiling`, techo curado real) | 3.38 | 3.57 |
| Después (con `resolve_ceiling` + cap 80, mismo catálogo real) | 3.38 | 3.47 |

Con el catálogo real de hoy (60/18, ambos bajo el cap de 80), el cap **no cambia** el
comportamiento observado (diferencia dentro del ruido de medición) — su función es acotar el
crecimiento futuro (un proveedor en `"auto"` sin techo curado, o un catálogo upstream que crezca
con el tiempo), no optimizar el caso de hoy. El sort en sí (`service.py:382`, medido con la misma
forma de clave, nunca tocado por este paquete) tarda ~0.046 ms incluso sin cap con el pool real
de 88 rutas — el cap protege contra el crecimiento del pool sintetizado en sí (construcción de
`StaticRoute`/identidades), no es una optimización de sort medible hoy. Corrida sintética de
estrés (6× el cap, 480 ids zen ofrecidos): CON cap, 80 rutas agregadas, p50=3.58 ms; SIN cap
(parcheado a un techo mayor que el pool), 480 rutas agregadas, p50=15.81 ms — casi 5× más lento,
confirmando que el cap sí importa fuera del caso de hoy. Detalle completo en la evidencia de
PKG-2.

## PKG-4 — `providers.toml`: el registro de proveedores locales del usuario, con origen

### Contexto

Una axis DISTINTA de la de PKG-1/PKG-2: `PROVIDERS` (arriba) es identidad de RUTEO — los
cuatro proveedores que `routing_core` prueba y audita (`_PAIR_COMMANDS`). El bloque
`provider.*` de `opencode.json` (hoy: `ollama`) nunca fue parte de ese universo — no se
prueba, no se rutea, no aparece en `_PAIR_COMMANDS`. Es un eje aparte: endpoints
locales/custom que OpenCode usa directamente, hasta ahora **hardcodeados** en
`Global/_shared/opencode.json:5-23` y fusionados al archivo vivo por `deep_merge`
(`install.py:49-56`), que **sólo agrega**: si el usuario borraba el bloque a mano, el
próximo install se lo reponía. Medido en la máquina real de Federico (context pack, P4):
su único provider (`ollama`) es **byte-idéntico** al que el harness manda, contra un
endpoint muerto — el defecto no era "el usuario agregó algo y se perdió", era "el harness
imponía algo que no se podía sacar".

### Decisión

1. **Un segundo registro, mismo módulo neutro** (`provider_registry.py`, cero imports de
   `models_config`/`routing_core`, igual que `PROVIDERS`): `HARNESS_PROVIDER_SEED`, el
   bloque que el harness solía hardcodear, ahora su único lugar de origen — usado sólo
   para (a) sembrar una máquina nueva sin `opencode.json` vivo de referencia, y (b) como
   valor de comparación de la migración (punto 4).
2. **`~/.local/state/set-agentes/providers.toml`** (AC-11), mismo precedente exacto de
   forma y escritura atómica que `set_agents_app.MODEL_PREFERENCE_PATH`
   (`set_agents_app.py:106`): una tabla TOML por id de proveedor, con dos claves —
   `origin` (uno de `harness | harness-legacy | discovered | user`) y `spec` (el bloque
   JSON completo que va a `opencode.json["provider"][id]`, opaco para este registro,
   codificado como STRING). El truco de codificación: `json.dumps` y la gramática de
   TOML basic string coinciden carácter a carácter en su set de escapes
   (`\", \\, \n, \t, \r, \b, \f, \uXXXX`) — `json.dumps(json.dumps(spec, sort_keys=True))`
   produce un literal TOML válido sin escritor TOML genérico de propósito general (mismo
   argumento de esquema-cerrado que `set_agents_app._serialize_model_preference` ya
   documenta para su propio archivo hermano, ADR-0018 R2-F-04). Parseo fail-closed
   (`ProvidersRegistryError`, nunca un registro vacío silencioso).
3. **AC-13 — el render, no el merge pasivo.** `Global/_shared/opencode.json` deja de
   tener clave `"provider"` (se saca por completo). `install.py`'s
   `apply_provider_registry()` reemplaza el paso-pasivo que `deep_merge` le daba a esa
   clave: por cada id en el registro, escribe/sobrescribe `provider[id] = spec` en el
   archivo vivo — el registro es la fuente única para los ids que rastrea.
4. **AC-15 — siembra migratoria, comparación por VALOR, nunca por id.** Cuando
   `providers.toml` no existe todavía, `seed_or_migrate(live_provider_block)`:
   - `live_provider_block` vacío (máquina nueva, sin `opencode.json` previo): cada
     entrada de `HARNESS_PROVIDER_SEED` se registra como `origin=harness`.
   - `live_provider_block` con contenido: **cada id presente se registra** — "a nadie le
     desaparece nada" — con `origin=harness-legacy` si su valor es **estructuralmente
     igual** (`==`) a la entrada correspondiente de `HARNESS_PROVIDER_SEED`, o
     `origin=user` en cualquier otro caso — un id que el harness nunca mandó, **o uno que
     sí mandó pero cuyo valor divergió** (el usuario lo editó a mano). La comparación es
     por valor: un `ollama` editado por el usuario es `user`, no `harness-legacy`, aunque
     el id coincida — nunca una heurística por nombre (medido y mordido: ver evidencia).
   - Este bootstrap corre **una sola vez**: una vez que `providers.toml` existe (aunque
     quede vacío tras un `--provider-remove`), nunca se vuelve a sembrar — es lo que hace
     que una baja sobreviva a instalaciones futuras.
5. **AC-14 — la poda se extiende de archivos a subárboles JSON, con la misma regla dura
   que ya regía a nivel de archivo.** `MANIFEST` (`managed-files.json`) sólo borra un
   PATH que él mismo escribió la corrida anterior; el nuevo `managed-json-paths.json`
   aplica la MISMA disciplina a un nivel más fino: `{"opencode.json": [ids que install.py
   escribió la corrida anterior]}`. Un id que estaba ahí y el registro ya no tiene se
   borra (se sabe que es propio); cualquier otra clave viva bajo `provider.*` — una que
   este instalador nunca registró escribir, p. ej. un bloque que el usuario agregó a mano
   editando `opencode.json` directamente, por fuera de `set-agents` — **no se lee, no se
   compara, no se toca**. Deliberadamente un archivo SEPARADO de `MANIFEST` (nunca una
   entrada de forma mixta en esa lista plana de paths de archivo): un puntero de subárbol
   no es un path de filesystem.
6. **AC-12 — `--provider-list|add|remove|verify`, nunca JSON a mano.** Viven en
   `set_agents_app.py`, tocan sólo `providers.toml` — nunca `opencode.json` directamente
   (`install.py`, en la próxima corrida, es quien refleja el cambio; cada comando lo dice
   explícito en su salida). `--provider-add` construye el bloque desde flags
   estructuradas (`--base-url`, `--npm`, `--label`, `--model ID[:nombre]` repetible) —
   nunca un flag de JSON crudo — y rechaza un id que colisione con `provider_registry.
   PROVIDERS` (la identidad de ruteo), para que un proveedor local no pueda sombrear un
   id que `_probe_pairs`/`opencode auth list` ya audita. `--provider-verify` es
   deliberadamente sólo la superficie declarada (forma: `npm`/`options.baseURL`/`models`
   no vacíos) — nunca liveness (`GET {baseURL}/models`, eso es AC-18/P5).
7. **El wizard de `setup_models.py` no se toca.** Remapea `[subscriptions]`/modelos de
   `models.toml` (incluido el fallback manual `ollama/<modelo>` que
   `SUBSCRIPTION_BY_PREFIX["ollama"]` ya soporta desde antes de este paquete) — es un eje
   ortogonal a `providers.toml`, que sólo gobierna el bloque `provider.*` de
   `opencode.json`.

### Riesgo medido: no hay proveedor propio del usuario en ninguna máquina medida hoy

El test obligatorio de AC-14 (un provider agregado a mano sobrevive intacto a una poda)
se construye con **fixture**, no contra el estado real — el context pack lo dice
explícito y esta implementación lo respeta: no hay ningún `provider.*` en la máquina
medida que no sea `ollama`, y ese es byte-idéntico al que el harness manda. Ver
`docs/specs/022-disponibilidad-real/evidence/P4-implementer.md` para el detalle mordido
(cada test nuevo, neutralizado y confirmado en rojo antes de revertir).

## Evidencia

`docs/specs/022-disponibilidad-real/evidence/P1-implementer.md` (PKG-1).
`docs/specs/022-disponibilidad-real/evidence/P2-implementer.md` (PKG-2).
`docs/specs/022-disponibilidad-real/evidence/P4-implementer.md` (PKG-4).
