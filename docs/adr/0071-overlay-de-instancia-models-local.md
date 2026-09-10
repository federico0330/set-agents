# ADR-0071 — Overlay de instancia `models.local.toml`: el gusto del usuario nunca ensucia el árbol

- Estado: **Accepted** (2026-08-26). Feature `045-consola-viva-e-instancia`, PKG-B (AC-B.1, AC-B.2,
  AC-B.3) y la mitad de persistencia de PKG-C/PKG-D.
- **Enmienda ADR-0048** (024 C2): `[subscriptions]` deja de ser la única sección de `models.toml` con
  overlay por máquina. La cláusula de 0048 que dice que `[areas.*]`/`[roles.*]` "stay in the tracked
  file by design" (`ai/scripts/models_config.py:295-302`) queda superseded **para la escritura del
  wizard**, no para el archivo trackeado. El tri-estado de suscripciones (ADR-0029/0048) no se toca y
  `subscriptions.local.toml` sigue siendo su propio archivo.
- **Extiende ADR-0003**: `models.toml` sigue siendo la fuente de verdad de fábrica. Este ADR agrega una
  segunda capa por máquina, nunca un segundo archivo trackeado.
- No supersede ADR-0063 (`cursor` ya está en `AREA_FIELDS`, `models_config.py:39`), ni ADR-0018 (el
  overlay no es un segundo decision-maker), ni ADR-0041 (`build.sh --check`, que este ADR existe en
  parte para no romper).

## Contexto

Medido en este árbol, 2026-08-26:

1. **El wizard reescribe el archivo trackeado en cada guardado.** `setup_models.py:694` llama
   `models_config.emit_atomic(models_out, config)` sobre `models.toml`, y `--set` hace lo mismo en
   `:883`. `tree_clean()` es literalmente `git status --porcelain == ""`, así que cualquier edición de
   gusto (área, rol, effort, `cursor`) deja el árbol sucio y `--update` bloqueado hasta un commit
   manual. Es exactamente el defecto que ADR-0048 nombró y arregló para **una** sección.
2. **ADR-0048 declaró la frontera por sección, y la frontera real es otra.** Su texto
   (`models_config.py:295-302`) separa "hecho de credenciales de una máquina" de "decisión curatorial
   del repo". La distinción sirve, pero el eje que importa no es la sección: es **quién escribe**. Un
   humano que edita `models.toml` y commitea está curando; el wizard escribiendo en nombre de una
   máquina está fijando gusto de instancia. La misma celda `[areas.implement].codex` es curación cuando
   la commiteás y gusto cuando la elegís en el picker.
3. **La alternativa que 0048 rechazó sigue siendo correcta en su parte dura.** Rechazó "fusión campo a
   campo dentro de `load_config`, transparente para todo caller" porque volvería no determinístico
   cualquier build de `Global/`. Eso no cambió, y hoy tiene dos anclas medidas:
   `build.sh:93-99` regenera y hace `diff -ruN` contra `Global/<harness>` (ADR-0041), y `build.sh:115-119`
   copia una generación **dentro** de `Global/`. Un merge transparente en `load_config` hornearía el
   gusto de una máquina en el árbol commiteado y pondría `./build.sh --check` en rojo en cualquier
   máquina con overlay — que es el propio AC-E.1 de 045.

Las dos mitades tienen que convivir: el gusto de instancia debe ser efectivo (AC-B.1) y el árbol
trackeado debe seguir siendo reproducible por cualquiera (AC-E.1). Todo este ADR es esa reconciliación.

## Decisión

### 1. Fábrica sigue siendo fábrica

`models.toml` trackeado no se migra, no se neutraliza y no pierde ninguna celda. Un clon nuevo se
comporta exactamente como dice el repo (no-goal explícito de 045). El overlay es aditivo o no existe.

### 2. Vista efectiva = fábrica ∪ overlay, celda por celda

El overlay vive en `STATE_DIR / "models.local.toml"` — el mismo directorio privado por usuario que
`MODEL_PREFERENCE_PATH` (`set_agents_app.py:109`), `subscriptions.local.toml` (ADR-0048) y
`providers.toml` (ADR-0042, 022 PKG-4) ya habitan. Ausente == sin overlay == valor de fábrica.

### 3. Cuatro funciones, la forma de ADR-0048 sin reinventarla

Espejo exacto de `subscriptions_overlay_path` (`models_config.py:305`), `load_subscriptions_overlay`
(`:320`), `write_subscription_overlay` (`:336`) y `effective_subscriptions` (`:370`):

- `models_overlay_path()` — resuelve `set_agents_app.STATE_DIR / "models.local.toml"` con **import
  diferido dentro de la función**, nunca a nivel de módulo (`set_agents_app` ya importa
  `models_config` incondicionalmente en su propio nivel de módulo: el import al revés sería el ciclo
  real) y **nunca redeclarando el directorio como un segundo literal**. El tripwire de ADR-0043
  (`tests/test_routing.py::test_adr0043_ac10_no_call_site_still_passes_the_legacy_state_dir_shaped_root`)
  existe justamente para eso y ya cazó en vivo el intento anterior.
- `load_models_overlay(path=None)` — lectura best-effort: `OSError`/`tomllib.TOMLDecodeError` degradan
  a `{}`, igual que `load_subscriptions_overlay` (`:326-329`). Filtra a los ámbitos y campos legales
  (§4) y descarta lo demás sin morir.
- `write_models_overlay_field(scope, field, value, path=None)` — escritura atómica
  (`tempfile.mkstemp` + `os.replace`, misma disciplina que `emit_atomic`). `scope` es
  `("areas", <duty>)` o `("roles", <role>)`; `value=None` borra la clave y vuelve al valor de fábrica.
  Devuelve el overlay completo resultante, como su hermana de 0048.
- `effective_models_config(config)` — vista de sólo lectura con el overlay aplicado. Nunca muta el
  `config` recibido ni lo que `emit()` serializa, así que un "Guardar" posterior no puede filtrar el
  overlay de vuelta al archivo trackeado (la misma garantía que `effective_subscriptions`, `:375-377`).

### 4. Esquema del overlay: dos familias de tablas, campos cerrados

Sólo `[areas.<duty>]` y `[roles.<role>]`, con campos restringidos a `AREA_FIELDS`
(`models_config.py:39`: `claude`, `codex`, `codex_effort`, `opencode`, `cursor`) más cualquier miembro
`<lane>_effort` que ADR-0073 admita más adelante. Valores string.

Queda **afuera**, con razón escrita:

- `TIER_FIELD` (`tiers`, `models_config.py:43`): tabla anidada, sólo de roles, con su propio contrato
  tri-estado en `load_role_tiers` (ADR-0048) y con un gate de coherencia de catálogo
  (`generate.py:695`). No es gusto de instancia.
- `[catalog]`, `[routing]`, `[session]`, `[permissions]`, `[families]`, `[providers]`: superficies
  auditadas. `[catalog]` es el allowlist contra el que **todo lo demás** valida (`load_roles`
  `:636-643`, `catalog.build_snapshot` `:1004-1009`); un allowlist por máquina haría que el mismo
  `models.toml` valide en una máquina y muera en otra.
- `[subscriptions]`: sigue en su propio archivo (ADR-0048), con su propio esquema y su propio escritor.

Una clave desconocida o un archivo malformado **no** matan: se ignoran y la celda cae a fábrica
(AC-B.2).

### 5. Precedencia: el overlay gana por celda, la especificidad sigue siendo de ADR-0003

El overlay gana por **(ámbito, campo)** — la generalización literal de la regla "el overlay gana por
clave" de 0048 (`:370-377`). Después de fusionar las tablas, corre el merge rol > área que ya existe
(`resolve_role`, `models_config.py:592-613`).

Consecuencia deliberada: un `[roles.X].codex` **de fábrica** le gana a un `[areas.Y].codex` **del
overlay**. El overlay reemplaza valores de celda; no es un segundo decision-maker sobre especificidad
(lo que ADR-0018 rechazó). Para pisar un pin de rol de fábrica se escribe el overlay en ámbito de rol —
que es exactamente lo que hace la UI de Overrides al editar un rol.

### 6. Invariante R: el que genera para `Global/` lee fábrica; sólo el que genera para `$HOME` puede leer efectivo

`load_config` sigue devolviendo **fábrica sola**. La vista efectiva es *opt-in explícito del caller*,
nunca transparente. En concreto:

- `generate.py` gana un flag explícito (`--effective`) y sigue siendo fábrica por defecto. Su
  `argparse` (`generate.py:858-863`) es puro flag, sin contrato de orden: agregarlo es aditivo.
- `build.sh` lo pasa **sólo** en modo `install`, en su único call site de generación (`build.sh:53`).
  `--check` (`:93`), `--diff` y el `generate` que escribe `Global/` (`:115-119`) nunca lo pasan.
- `resolve_role` no cambia de firma: lee el `config` que le den. Ese es todo el punto de que la vista
  efectiva sea un `config`, no un modo global.
- `check-drift.sh:19` **también** pasa `--effective`. Sin eso, la pregunta que ese script hace ("¿mi
  instalación quedó atrás del repo?") se responde comparando una instalación legítimamente efectiva
  contra una generación de fábrica, y da `DRIFT_DETECTED` para siempre en cualquier máquina con
  overlay — dejando en rojo permanente la línea "drift: la instalación quedó atrás del repo"
  (`set_agents_app.py:3760-3761`) de la misma consola que 045 viene a hacer honesta. El cambio es una
  línea y es parte del mismo paquete, no un seguimiento.

Efecto neto: una edición de gusto llega a los árboles instalados en `$HOME` vía `./build.sh --install`,
y **nunca** al repo.

### 7. Lado de escritura: qué deja de tocar el archivo trackeado, y qué no

- El wizard (áreas, roles, effort, `cursor`) y `--set` cuya dirección resuelve a una celda de
  `[areas.*]`/`[roles.*]` escriben **sólo** el overlay, de inmediato — mismo contrato "efectivo ya, no
  requiere Guardar" que 0048 le dio a Suscripciones y ADR-0032 a los pins.
- `emit_atomic` **no se borra**. Sobrevive para (a) el camino de plumbing (`--models`/`--output-models`,
  `setup_models.py:820-821`), que es otro archivo por definición, y (b) `--add-model`, que muta
  `[catalog]` — el allowlist auditado, hecho curatorial y no gusto de instancia. Que AC-B.1 sea verde
  no significa que este símbolo desaparezca.

### 8. Validación: malformado degrada, fuera-de-catálogo falla cerrado

Dos casos distintos que un implementador confundiría si no quedan escritos:

- **Archivo malformado o clave desconocida** → se ignora, la celda cae a fábrica, sin traceback y sin
  aplicación parcial (AC-B.2).
- **Clave legal con un valor fuera de `[catalog]`** → intención curada equivocada, no ruido. Se valida
  **en la escritura** contra el mismo camino de catálogo que ya usaba la escritura trackeada (AC-C.2),
  así que el overlay nunca persiste un valor que `load_roles` mataría después. Si igual aparece uno
  (edición a mano del archivo), falla cerrado en validación con un mensaje que **nombra el path del
  overlay** — misma disciplina que `ModelPreferenceError` y `ProvidersRegistryError`.

### 9. Orden contra `model-preference.toml` y `subscriptions.local.toml`: no compiten

No se inventa ninguna regla de precedencia porque no hay conflicto que resolver:
`model-preference.toml` (`[model_pin]`, bias) es una preferencia de **routing**, consumida por
`service.route()` vía `_config_with_model_preference`; `models.local.toml` son **celdas de fallback
curado**, consumidas por `generate.py`/`resolve_role`. Ejes distintos, consumidores distintos.
`subscriptions.local.toml` sigue siendo su propio archivo, con su propio esquema y sus propios tests.

## Alternativas rechazadas

- **Fusión transparente dentro de `load_config`.** Es la misma alternativa que 0048 rechazó, y hoy se
  rechaza con dos mediciones nuevas: `build.sh:93-99` (`--check` comparando contra `Global/`) y
  `build.sh:115-119` (la generación que **escribe** `Global/`). Además contaminaría los tests herméticos
  que llaman `models_config.load_config` directo con el overlay real de la máquina que corre la suite.
- **Un solo overlay que absorba `subscriptions.local.toml`.** Ese archivo tiene esquema cerrado,
  escritor propio y tests propios (ADR-0048); fusionarlos cuesta una migración a cambio de nada.
- **Migrar las celdas trackeadas de hoy al overlay.** No-goal explícito de 045: un clon nuevo tiene que
  seguir comportándose como dice el repo, y una migración convertiría el default del repo en un
  snapshot congelado de esta máquina — que es la crítica original de 0048, todavía vigente.
- **Overlay con `[catalog]` / `[routing]` / `tiers`.** El allowlist por máquina rompe la propiedad de que
  `models.toml` valida igual en todas partes; `tiers` es anidado y ya tiene contrato propio más un gate
  de coherencia de catálogo.
- **El overlay gana como capa entera (área del overlay le gana a rol de fábrica).** Invierte en silencio
  el merge rol > área de ADR-0003 y convierte al overlay en un segundo decision-maker sobre
  especificidad.
- **Generar siempre efectivo y aceptar que `Global/` quede sucio.** Rompe AC-E.1, ADR-0041 y la
  propiedad de árbol commiteado reproducible por cualquiera (ADR-0008: `Global/**` no lleva nada
  específico de una máquina).

## Enmienda (2026-08-31, feature 048)

**La escritura del overlay valida el config EFECTIVO antes de tocar el disco.**

Mover el gusto por área/rol a `models.local.toml` sacó esa escritura del único camino que corría
`validate()` — y ahí vive la separación de deberes. Medido, no supuesto:
`setup-models.sh --set audit.codex=<el modelo del implementador>` devolvía `0`, escribía el
overlay, dejaba `models.toml` limpio y `--check` en verde (sólo mira el archivo de fábrica), y el
config que el router lee quedaba con el auditor corriendo el modelo de quien escribió. La opción
"Preferir un modelo" del wizard usa la misma función, así que la TUI tenía el mismo agujero.

`setup_models.write_overlay_cell()` es ahora la única puerta: arma el overlay candidato en
memoria, corre `validate()` sobre `effective_models_config(factory, candidato)`, y sólo entonces
escribe. Un valor ilegal nunca llega al disco — la misma cláusula fail-closed que este ADR ya
declaraba para un valor fuera de `[catalog]`, extendida a la regla que el harness no puede
perder. Cubierto por `test_setup_models_rejects_separation_violation` y
`test_setup_models_check_rejects_opencode_separation_violation`, que estaban en rojo señalando
exactamente esto.

## Consecuencias

- Editar un área, un rol, un effort o `cursor` deja `git diff --name-only -- models.toml` vacío;
  `tree_clean()` sigue verde y `--update` deja de bloquearse (AC-B.1).
- `./build.sh --check` sigue verde en cualquier máquina, con o sin overlay (AC-E.1). Es la razón de
  existir del punto 6.
- Los árboles instalados en `$HOME` pueden diferir legítimamente de `Global/`. `check-drift.sh` mide
  contra la misma vista efectiva; sin ese cambio el badge de drift queda en rojo permanente.
- ADR-0073 no necesita tocar el esquema del overlay: cualquier `<lane>_effort` que se agregue a
  `AREA_FIELDS` ya es aceptado por §4.
- `provider_registry.py` no participa: el overlay es de `models_config`, y esa separación es la que
  mantiene el registro de proveedores con cero dependencias (ADR-0042, `provider_registry.py:10-16`).

## Evidencia

`ai/scripts/models_config.py:39`, `:43`, `:295-302`, `:305-377`, `:592-613`, `:636-643`.
`ai/scripts/setup_models.py:613`, `:694`, `:820-821`, `:883`.
`ai/scripts/set_agents_app.py:47`, `:109`, `:3760-3761`.
`ai/scripts/generate.py:551`, `:858-863`. `build.sh:53`, `:93-99`, `:115-119`, `:123-137`.
`ai/scripts/check-drift.sh:19`. `ai/scripts/routing_core/catalog.py:1004-1009`.
Contratos: `docs/specs/045-consola-viva-e-instancia/{spec,design,acceptance}.md`.

## Destilado (dominio: architecture)

- La frontera "qué va al repo y qué a la instancia" no es por sección de `models.toml`: es por
  **escritor** (humano que commitea vs. wizard de una máquina). ADR-0048 la trazó por sección y por eso
  la cerró sobre una sola.
- Toda generación cuyo destino sea `Global/` tiene que leer fábrica: `build.sh:93-99` la compara y
  `:115-119` la escribe. Un merge transparente en `load_config` rompe ADR-0041 y AC-E.1 a la vez.
- `check-drift.sh` compara instalación contra una generación propia: cualquier vista que cambie lo
  instalado tiene que cambiar también esa generación, o el badge de drift miente para siempre.
