# ADR-0048 — `[subscriptions]` neutro con overlay por máquina, lane `local` renombrada

- Estado: Accepted (2026-08-14). Feature 024-listo-para-terceros, paquete
  C2-modelstoml-neutro (AC-03, AC-04, AC-05). No supersede nada.

## Contexto

`models.toml` es el archivo trackeado, único, que todo clon del harness comparte. Hasta este
paquete traía tres afirmaciones específicas de la máquina de Federico:

1. **`[subscriptions]` fijaba sus cuatro suscripciones reales** (`anthropic = true`,
   `ollama = false`, `openai = true`, `zen = true`). Un tercero que clonara heredaba esas
   cuatro afirmaciones sobre su propia máquina. Peor: los `true` explícitos **apagan la red
   tri-estado** que ADR-0029 construyó (`models_config.py`, `load_roles`) — con todo declarado,
   el probe de credenciales nunca decide nada; "ausente = auto" es donde vive esa red.
2. **El wizard reescribe el `models.toml` trackeado** en cada guardado. `tree_clean()`
   (`set_agents_app.py`) es literalmente `git status --porcelain == ""`, así que cualquiera que
   usara el wizard —aunque sólo tocara sus propias suscripciones— quedaba con `--update`
   bloqueado para siempre: el árbol nunca vuelve a estar limpio sin un commit manual.
3. **La lane `local` no ejecuta nada local.** `auto_profile()` la deriva como "ningún par
   OpenCode vivo" (ni `opencode-go` ni `opencode-zen`), y sus celdas son, sin excepción salvo
   la del `[areas.coord]`, modelos `openai/*` — confirmado en `COMO-CAMBIAR-MODELO.md`: "`local`
   usa sólo `openai/*`". Además, `[session].opencode_small_model` exigía Zen (`opencode/north-
   mini-code-free`) en las **tres** lanes, incluida ésta — una lane que no tiene Zen no puede
   depender de un modelo que sí lo requiere.

## Decisión

### 1. `[subscriptions]` pasa a ausente = auto por defecto (AC-03)

El tracked `models.toml` no declara ninguna suscripción. `models_config.load_config` deja de
exigir que `[subscriptions]` sea una tabla no vacía — sólo exige que la clave `[subscriptions]`
exista como tabla (puede estar vacía). Un `false` explícito **sigue siendo intención curada y
sigue muriendo** (el contrato inmutable de ADR-0029 no se toca); lo que cambia es que el default
del repo deja de ser una afirmación sobre una máquina ajena.

### 2. Overlay por máquina en `STATE_DIR`, nunca en el archivo trackeado (AC-05)

Precedente exacto de forma y escritura atómica: `MODEL_PREFERENCE_PATH`
(`set_agents_app.py`). `models_config.subscriptions_overlay_path()` resuelve
`set_agents_app.STATE_DIR / "subscriptions.local.toml"` — vía un **import diferido dentro de
la función**, nunca a nivel de módulo (`set_agents_app` ya importa `models_config`,
incondicional, en SU propio nivel de módulo; un import a nivel de módulo en el otro sentido
sería el ciclo real) y **nunca redeclarando el mismo directorio como un segundo literal**:
`ai/scripts/models_config.py` casi lo hace (un `STATE_DIR` de módulo, mismo valor por
construcción) y el propio guardián de ADR-0043
(`tests/test_routing.py::test_adr0043_ac10_no_call_site_still_passes_the_legacy_state_dir_shaped_root`)
lo capturó en vivo durante la implementación de este paquete — ese guardián existe
específicamente para que `models_config.py` nunca vuelva a traer una segunda raíz
independiente para el mismo directorio (la lección original era sobre la caché de probes;
aplica igual acá). La forma final reutiliza el único `STATE_DIR` que `set_agents_app` ya
calculó, en vez de agregar un segundo.

`models_config.write_subscription_overlay(subscription, value)` escribe atómico
(`tempfile.mkstemp` + `os.replace`, igual que `emit_atomic`); `value=True/False` fija/excluye,
`value=None` borra la clave (vuelve a auto). `models_config.load_subscriptions_overlay()` lee
best-effort (`{}` en archivo ausente o corrupto — nunca crashea al caller, misma disciplina que
`detect_subscriptions`). `models_config.effective_subscriptions(config)` es la vista de sólo
lectura que combina ambas capas (`{**tracked, **overlay}`, el overlay gana por clave) para
validación y display — `config["subscriptions"]` en sí (lo que `emit()` serializa) nunca se
toca por esta función, así que un "Guardar" posterior del wizard nunca puede filtrar el overlay
de vuelta al archivo trackeado.

`setup_models.py`:
- El wizard (opción "Suscripciones") ya **no** muta `config["subscriptions"]`. Escribe el
  overlay de inmediato (mismo contrato "efectivo ya, no requiere Guardar" que los pines de
  modelo, opción 8) y no marca `dirty`.
- `--add SUBSCRIPTION` / `--drop SUBSCRIPTION` (los flags scripteados documentados en
  `COMO-CAMBIAR-MODELO.md` bajo "¿Cambiaron tus suscripciones?") también escriben el overlay de
  inmediato, en vez de acumularse en el pipeline `mutated → validate → emit_atomic`. El guardia
  de `--drop` (`dropped_cells`, qué celdas usan esa suscripción) es idéntico — nunca dependió del
  valor booleano actual, sólo de qué modelos resuelven a ese proveedor.
- `_status_lines`/`_panel_lines` muestran `effective_subscriptions(config)`, no
  `config["subscriptions"]` a secas — si no, un tracked file neutro mostraría "auto" para una
  suscripción que el usuario curó explícitamente en su overlay.
- El universo de candidatos del picker interactivo (`_subscription_candidates`) deja de ser
  `sorted(config["subscriptions"])` (vacío en un tracked file neutro, nada para elegir) y pasa a
  ser el universo auditado de `SUBSCRIPTION_BY_PREFIX.values()`, extendido por cualquier
  `[providers]` del repo y por lo que la máquina ya declare (tracked u overlay).

**Qué NO se movió al overlay.** `[areas.*]`/`[roles.*]` (incluido `[areas.coord]`, el modelo del
orquestador) siguen viviendo — y guardándose — en el `models.toml` trackeado. No son estado de
credenciales de una máquina: son decisiones curatoriales sobre qué modelo usa cada duty/rol, del
mismo tipo que cualquier commit de este repo. `[subscriptions]` es la única sección que es un
hecho de credenciales, nunca una decisión de producto — por eso es la única que se mueve.

### 3. La lane `local` se renombra a `openai-only` (AC-04)

`models_config.LANES = ("go-zen", "zen", "openai-only")`. `auto_profile()` devuelve
`"openai-only"` en el caso "ningún par OpenCode vivo" (antes `"local"`). El rename toca toda
clave `"local" = "..."` en `models.toml` (35 sitios: `[session].opencode_small_model` y cada
`opencode = {...}` de `[areas.*]`/`[roles.*]`) y los dos comentarios que nombraban la lane en
prosa. `[session].opencode_small_model`'s lane `openai-only` deja de exigir Zen: pasa de
`opencode/north-mini-code-free` (namespace `opencode`, consume la suscripción `zen` vía
`SUBSCRIPTION_BY_PREFIX`) a `openai/gpt-5.4-mini` — el mismo modelo barato ya curado para cada
otra celda `openai-only` de este archivo.

**Límite honesto, no corregido por este paquete:** `[areas.coord].opencode."openai-only"` sigue
siendo `opencode/grok-4.5` (consume `zen`, no `openai`) — una excepción deliberada y ya
documentada (feature 026, "el coordinador deja de ser GPT") que el rename no toca ni pretende
resolver; el 95% restante de las celdas `openai-only` del archivo sí es, literalmente, sólo
`openai/*`.

### Efecto colateral encontrado y cerrado: `load_role_tiers` nunca tuvo la tolerancia tri-estado

`load_role_tiers` (las seis tablas `[roles.<role>.tiers.*]`) precede a ADR-0029 y, a diferencia
de `load_roles`, nunca ganó su tolerancia tri-estado (`ausente = auto`, probe de respaldo,
`WARN degraded` en vez de morir). Era invisible mientras `[subscriptions]` siempre declaraba
`true` cada proveedor usado. Con AC-03 (tracked file neutro), esa laguna se volvía un `die()`
incondicional en las seis lanes tiered, en cualquier máquina, en cada build — capturado en vivo
por `verify.sh` al validar este mismo paquete. Se cierra alineando `load_role_tiers` al mismo
contrato que `load_roles` ya tenía: `false` explícito muere, `SET_AGENTS_STRICT_MODELS=1` fuerza
el die histórico, ausente-y-detectado carga en silencio, ausente-y-no-detectado degrada a
`WARN degraded` sin morir.

## La trampa que este ADR existe para cerrar

La migración es parte del paquete, no un extra. Antes de neutralizar el archivo trackeado, las
cuatro declaraciones reales de esta máquina (`anthropic=true`, `ollama=false`, `openai=true`,
`zen=true`) se escribieron en su overlay (`~/.local/state/set-agentes/subscriptions.local.toml`,
vía `models_config.write_subscription_overlay`, con backup de `STATE_DIR` tomado antes de tocar
un byte). Probado con `--route-decide` para `orchestrator` e `implementer`, antes y después de
la migración + el rename + la neutralización del tracked file: mismo `route_id`, `provider`,
`model`, `family`, `tier`, `reason_codes` — evidencia completa en
`docs/specs/024-listo-para-terceros/evidence/C2-implementer.md`. (`[subscriptions]` resultó no
influir en ningún caso en el resultado de `--route-decide` — `routing.py`/`routing_core` no la
leen nunca; sólo gatea validación en `load_roles`/`load_role_tiers` y el display del wizard. La
migración igual se hizo, porque ese display y esa validación sí dependen de ella.)

## Alternativas rechazadas

- **Overlay de todo `models.toml` (áreas y roles incluidos), no sólo `[subscriptions]`**:
  rechazado — convertiría cada edición curatorial del wizard (opciones "Cambiar un área"/"Cambiar
  un rol") en un snapshot congelado por máquina que diverge silenciosamente del repo en cuanto
  éste evoluciona, sin necesidad real: esas ediciones ya están pensadas para commitearse (mismo
  contrato que editar el archivo a mano, documentado en `COMO-CAMBIAR-MODELO.md`).
- **Fusión campo a campo dentro de `load_config`, transparente para todo caller**: rechazado —
  contaminaría tests herméticos que llaman `models_config.load_config`/`load_roles` directo
  (sin pasar por `set_agents_app.py`/`setup_models.py`) con el overlay real de la máquina que
  corre la suite, y volvería no determinístico cualquier build de `Global/` corrido en una
  máquina con overlay propio — el árbol commiteado tiene que ser reproducible sin importar quién
  lo genera.
- **Dejar `local` como nombre**: rechazado — es literalmente falso (ningún modelo de esa lane
  corre en la máquina) y la propia documentación del repo (`COMO-CAMBIAR-MODELO.md`) ya lo
  describía como "openai/\* only"; el nombre nuevo es una lectura directa de esa descripción.

## Consecuencias

- Un clon nuevo no hereda ninguna suscripción ajena; el probe decide, y el primer
  `./build.sh`/`--route-decide` ni muere ni miente sobre una suscripción que nadie tiene.
- El wizard (Suscripciones) y `--add`/`--drop` dejan de ensuciar el árbol — `tree_clean()` sigue
  verde después de usarlos.
- La lane `openai-only` deja de exigir una suscripción que su propio nombre dice que no tiene.
- `[areas.*]`/`[roles.*]` (incluido el modelo del coordinador) permanecen tal cual, en el archivo
  trackeado — este paquete no los neutraliza ni los mueve.
- El primer arranque interactivo y `ROUTING_UNCONFIGURED` quedan fuera de este paquete — es C3
  de la misma feature.

## Evidencia

`docs/specs/024-listo-para-terceros/evidence/C2-implementer.md`.
