# Context pack — P2-opencode-lane (feature 004, contract 1.1.0)

Objetivo: que el orquestador elija **modelo por tarea** al delegar en el runtime OpenCode. Como ningún
runtime acepta `model` en el spawn (ni `task` de OpenCode, ni `Task` de Claude, ni `subagent_run` de Pi
v1.4.1), la elección dinámica se materializa con **variantes generadas por tier**: para cinco roles caros
se emiten agentes OpenCode adicionales `<role>@fast`, `<role>@balanced`, `<role>@frontier`, y el
orquestador spawnea la variante cuyo modelo coincide con la decisión de `--route-decide`. Esta es la
traducción honesta del "fork de gentle-ai": gentle-ai NO elige modelo en runtime (binding estático,
el humano cambia perfiles con Tab); acá el orquestador consume el cerebro de ruteo (P1) y elige la
variante por spawn. La elección **cross-provider real por spawn** llega en P3 (pi-lane); P2 entrega la
elección de tier dentro de la familia openai-codex que el catálogo curó, y **degrada honestamente** al
agente base cuando la decisión no es honrable por el lane.

## Leé primero
- `docs/specs/004-adaptive-dispatch/spec.md` (AC-06/07/08; §Tier model; §"OpenCode lane")
- `docs/specs/004-adaptive-dispatch/acceptance.md` (escenarios P2, líneas AC-06/07/08)
- `docs/adr/0006-adaptive-dispatch-cache-and-facts.md` (AM-1/AM-2, ya aceptado)
- `ai/catalogs/routes.v1.toml` (catálogo v2, 6 filas = 2 proveedores × 3 tiers) — **fuente de verdad del
  binding tier→modelo**; los tiers NO viven en models.toml
- Código base:
  - `ai/scripts/generate.py` — `generate()` (285-381), emisión de agente OpenCode por rol (296-312,
    binding `model: {row['opencode_model']}` en 298), `oc_permissions` (116-226; rama coord-ro 169-200;
    rama writer 224-225), `ORCHESTRATOR_TASK_ALLOW` (19-47) + emisión del `task:` allowlist (186-192),
    `validate()` con igualdad de conjunto de roles (398-404), chequeo de delegación (405-408)
  - `ai/scripts/models_config.py` — `MODEL_TIERS=("fast","balanced","frontier")` (L30, hoy **constante
    muerta**), `AREA_FIELDS` (L28), `resolve_role` (224-248, punto de merge role-sobre-area; rechaza
    claves fuera de `AREA_FIELDS`), `load_roles` (251-289, valida catálogo+regex+subscription+separación
    de familias), `subscription_of` (205-210)
  - `ai/scripts/install.py` — targets (29-33), `managed_files()` (75-82), prune por manifiesto
    (195-228, 246-251, 323-328) — **el prune ya cubre archivos nuevos/removidos sin cambios**
  - `Global/_canonical/agents/orchestrator.md` — doctrina: "Delegation flow" (104-174), "record-spawn"
    (69-73, ANTES de cada delegación), "Narración" (259-315, registros Cliente/Ingeniería + persistencia
    via `record-spawn`/`log-narrative`), "Question policy" (247-248, "nunca preguntar modelos")
  - `ai/scripts/coord_policy.py` — `SAFE` allowlist coord-ro (8-28, única mutación hoy: feature-state.py)
  - `ai/scripts/set_agents_app.py` — `cmd_route_decide` (230-298; claves permitidas del descriptor L231;
    devuelve `data.tier`, `data.role_class`, modelo decidido), `cmd_route_dispatched` (313-316),
    `cmd_route_terminal` (322-339); argparse (1286-1294)
  - `tests/test_harness.py` — helpers `run`, `_import`, `_models_fixture`/`_repo_models_variant`,
    `test_install_prunes_orphaned_managed_files_but_keeps_user_files` (1455-1488, **espejo para prune de
    variantes**), `test_repo_go_zen_routes_hot_path_to_fast_variants...` (186-202)

## El punto de diseño central — proyección lane↔catálogo (leer con cuidado)

El catálogo nombra los modelos `gpt-5.6-luna|sol|terra` (openai-codex) y `haiku|sonnet|opus` (anthropic).
El lane OpenCode usa otro namespace: `openai/<modelo>` o `opencode/<modelo>`. Hoy el área `implement`
go-zen usa `openai/gpt-5.6-fast`, que **NO existe en el catálogo** — por eso el gate de coherencia (AC-06)
debe FALLAR si una tabla de tier declara un modelo que no proyecta a exactamente una fila.

Proyección canónica (pura, offline, sin probes): un modelo OpenCode `openai/<M>` proyecta a la fila del
catálogo `(provider=openai-codex, model=<M>)`. Los modelos `opencode/<M>` (agregador zen: glm/kimi/
deepseek/nemotron) y cualquier `openai/<M>` con `<M>` fuera del catálogo NO proyectan a ninguna fila de un
proveedor habilitado. El único proveedor del catálogo alcanzable desde OpenCode es **openai-codex**
(anthropic corre por el runtime claude-code, no por OpenCode).

Consecuencia de diseño para las tablas de tier de los 5 roles: cada `(role, tier, lane)` declara un modelo
OpenCode que proyecta a **exactamente una** fila del catálogo de ese tier, opencode-compatible y
role-compatible (rol ∈ `row.roles`). En la práctica, para los tres lanes:
`fast → openai/gpt-5.6-luna`, `balanced → openai/gpt-5.6-sol`, `frontier → openai/gpt-5.6-terra`
(proyectan a las filas openai-codex fast/balanced/frontier respectivamente). Declarar un `opencode/...`
o un `openai/gpt-5.6-fast` en una tabla de tier ⇒ el build FALLA (cero matches). Esto es intencional: las
variantes tiered SON el carril openai-codex del catálogo hecho spawneable.

## Mapa de cambios por tarea

- **T-201 — tablas de tier por rol (`models.toml` + `models_config.py`)**
  - `models.toml`: para los 5 roles declarados (`security-auditor`, `package-reviewer`, `delta-reviewer`,
    `implementer`, `debugger`) agregar una tabla de tier lane-aware. Estructura propuesta:
    `[roles.<role>.tiers.<tier>]` con un mapa `opencode = { "go-zen"=..., "zen"=..., "local"=... }` por
    tier ∈ {fast,balanced,frontier}. El agente BASE sigue resolviendo como hoy (área/override actual, sin
    cambios). Los tiers SOLO afectan el lane OpenCode (effort es solo-Codex; claude no tiene variantes en
    P2).
  - `models_config.py`: activar `MODEL_TIERS`; parsear/validar las tablas de tier sin romper `resolve_role`
    (que valida `AREA_FIELDS` para el merge base — la tabla `tiers` es una estructura separada, no un
    campo de área). Nuevo camino tipo `load_role_tiers(config, profile) -> {role: {tier: opencode_model}}`
    para el lane activo, validado igual que todo modelo: catálogo/regex + `subscription_of` (misma
    validación de subscription que cualquier otro modelo de rol). Cobertura de lanes obligatoria (los tres
    lanes o un default explícito). Roles SIN tabla ⇒ no aparecen en el resultado (emiten exactamente un
    agente base).
  - Precedente de estructura: los `[roles.<role>]` actuales ya son overrides campo-a-campo del área;
    `debugger` ya tiene `[roles.debugger]` (flat) — la tabla de tier es aditiva sobre eso.

- **T-202 — emisión de variantes + gate de coherencia + validate/prune (`generate.py`, `install.py`)**
  - `generate.py`: para cada uno de los 5 roles con tabla de tier, emitir `out/opencode/agents/
    <role>@<tier>.md` — **cuerpo/permisos/steps idénticos al base**, cambiando SOLO `model:` por el modelo
    de la tabla de tier del lane activo. Variantes **aditivas y solo-OpenCode**: el agente base
    `<role>.md` se sigue emitiendo sin cambios, y Claude/Codex NO reciben variantes. `@` es válido en
    nombre de archivo en Linux y como clave literal del matcher de permisos.
  - Allowlist del orquestador: agregar cada nombre `<role>@<tier>` al `task:` allowlist OpenCode
    (`ORCHESTRATOR_TASK_ALLOW` + emisión 186-192) y a la lista `Agent(...)` de claude-code (232-234) —
    si no, `"*": deny` bloquea el spawn. (Los agentes base siguen permitidos.)
  - `validate()`: la igualdad de conjunto de roles (398-404) debe aprender el fan-out — `expected` para
    OpenCode ahora incluye `{<role>@<tier>}` de las tablas de tier. Codex/claude-code siguen con el
    conjunto base.
  - **Gate de coherencia (build-time, puro, sin probes)** — el primer puente entre generate y el catálogo
    de ruteo: para cada `(role, tier)` variante emitida, el modelo declarado debe proyectar (ver §arriba)
    a **exactamente una** fila de `routes.v1.toml` con `tier` igual y `role ∈ row.roles`. Cero o ambiguo ⇒
    `RuntimeError`/build FALLA. "Full-inventory assumption": el gate asume inventario completo, NO probea.
    Ubicalo en `validate()` o en una función dedicada invocada por `validate()` (que corre en cada
    generate y en `build.sh --check`).
  - `install.py`: **verificar** (no necesariamente cambiar) que las nuevas `<role>@<tier>.md` fluyen por
    `managed-files.txt` → install + prune automático. Si el prune ya las cubre (lo hace por manifiesto),
    no toques install.py salvo para un fence explícito si hiciera falta.

- **T-203 — doctrina del orquestador (`orchestrator.md`) + superficie de permisos (`coord_policy.py`,
  `generate.py` rama coord-ro)**
  - `orchestrator.md`: insertar el protocolo decide→spawn en "Delegation flow". Reglas exactas (AC-07):
    1. Antes de delegar un rol tiered, correr `python3 ai/scripts/set_agents_app.py --route-decide <desc>`
       (descriptor con `role`, `task_class`, `risk`, `feature_id`/`package_id`, y para reviewers
       `review_of_run_id`).
    2. **Matchear por el MODELO DECIDIDO, no por el tier**: mapear el modelo decidido al nombre de variante
       (`openai/gpt-5.6-luna→@fast`, `sol→@balanced`, `terra→@frontier`) y spawnear `<role>@<tier>`.
    3. **Model-mismatch** (la decisión eligió un modelo que ninguna variante del lane honra — típicamente
       anthropic como fallback): cerrar el run como `abandoned`
       (`--route-terminal <run_id> failure`) y entrar en **modo degradado con el agente BASE** `<role>`.
    4. **Router no disponible** (`ROUTING_UNAVAILABLE`/exit≠0): modo degradado con el agente BASE, sin
       reintentar en loop.
    5. La narración del spawn (bloque Cliente/Ingeniería, `record-spawn`/`log-narrative`) debe incluir el
       `route_id`/`run_id` de la decisión.
    6. **Reviewers**: solo se rutean con un `review_of_run_id` verificado, tomado del estado del paquete o
       de `--routing-recent-writers`; sin identidad verificada ⇒ decisión no ejecutable (P1 ya devuelve
       `REVIEW_IDENTITY_UNVERIFIED`), se spawnea el reviewer base.
  - Permisos (dos superficies simétricas):
    - Coord read-only para `--route-decide`: agregar el patrón a `coord_policy.py::SAFE` (8-28) y a la
      rama coord-ro de `generate.py::oc_permissions` (junto a la excepción feature-state.py, ~199-200).
      Documentar la CLI de ruteo como **excepción explícitamente MUTATING-capable** del coord (AC-07): el
      coord puede además cerrar runs (`--route-dispatched`/`--route-terminal`) narrado en el uso.
  - "Question policy" (247-248): mantener — el orquestador NUNCA pregunta el modelo; ahora lo DECIDE via
    `--route-decide`.

- **T-204 — test hermético de ciclo de vida del lane + doctrina de muerte del worker (`test_harness.py`)**
  - Ciclo feliz (AC-08): con un routing root temporal (`SET_AGENTS_ROUTING_TEST_ROOT`),
    decide(writer)→dispatched→terminal via CLI ⇒ exits 0 y `--routing-report` muestra los contadores de la
    ruta.
  - Muerte del worker (AC-08): un spawn que murió sin terminal ⇒ aplicar doctrina de muerte
    (`--route-terminal <id> failure`) cierra el run y el report refleja el `failure`.
  - Emisión de variantes: build ⇒ existen `<role>@fast/@balanced/@frontier` para los 5 roles, con cuerpo/
    permisos/steps idénticos al base y `model:` del tier; el orquestador los tiene en su `task:` allowlist;
    roles sin tabla emiten exactamente un agente. Espejar
    `test_install_prunes_orphaned_managed_files...` para probar prune de una variante removida.
  - Gate de coherencia: un modelo de tabla de tier que NO proyecta ⇒ build falla (test negativo).

## Invariantes que NO se tocan
- El núcleo de ruteo (P1: `routing_core/**`, `set_agents_app.py` zonas routing, `routes.v1.toml`,
  `tests/test_routing.py`) es **read-only** para P2 salvo agregar nombres al `roles` de las filas si
  hiciera falta (no hace falta: los 5 roles ya están en las 6 filas). AM-1/AM-2 intactos.
- Agentes base de los 5 roles: **sin cambios** (variantes aditivas, solo-OpenCode). Claude/Codex sin
  variantes.
- Separación de deberes: reviewers read-only con `review_of_run_id` verificado; el implementer no
  aprueba lo suyo.
- Drift check de `verify.sh`: `Global/` trackeado debe igualar un generate fresco — las variantes nuevas
  se commitean en `Global/opencode/agents/`.
- Redacción: nunca loguear secretos/tokens; el descriptor de `--route-decide` es intención no confiable.

## Gates del paquete
`python3 -m unittest discover -s tests -v` (test_harness.py + test_routing.py, sin debilitar regresiones);
`./build.sh --check` (genera a staging + `validate()` incl. gate de coherencia); `py_compile`
(`ai/scripts/*.py ai/scripts/routing_core/*.py tests/*.py`); `git diff --check`; drift check de
`verify.sh` (Global == generate fresco); `./ai/scripts/verify.sh` VERIFY_PASS; ownership contra baseline
del paquete (`71abca1`).

## Propiedad (owned_paths)
`models.toml`, `ai/scripts/models_config.py`, `ai/scripts/generate.py`, `ai/scripts/install.py`,
`Global/_canonical/agents/orchestrator.md`, `ai/scripts/coord_policy.py`, `tests/test_harness.py`,
`docs/specs/004-adaptive-dispatch/context/P2-opencode-lane.md`,
`docs/specs/004-adaptive-dispatch/evidence/P2-*`, y los artefactos generados en
`Global/opencode/agents/**`, `Global/claude-code/agents/orchestrator.md`, `Global/codex/**` (salida de
generate re-commiteada por el drift check).
Read-only: `ai/catalogs/routes.v1.toml`, `ai/scripts/routing_core/**`, `ai/scripts/set_agents_app.py`,
`roles.tsv`, `docs/specs/004-adaptive-dispatch/{spec,acceptance,plan,proposal}.md`.
