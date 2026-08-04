# ADR-0029 — "El probe manda": inventario descubierto como fuente de verdad de modelos

- Estado: Accepted (2026-08-04). Feature 017. Quinta de cinco (0025-0029). Implementa lo que la spec 008
  dejó como P3 "scoped but not contracted". Extiende ADR-0016 (que hizo a los providers *probeables*)
  hasta *routables*; no lo supersede.

## Contexto

La selección de modelos era mayormente estática: routing dinámico solo para 6/28 roles, eligiendo entre
6 filas curadas a mano (`routes.v1.toml`); el probe de inventario solo podía RESTAR del catálogo manual
(`catalog.py::_configured_models`, `allowed & probed`), nunca agregar; el frontmatter generado pineaba
ids literales por lane; `[subscriptions]` era un flag manual cuya inconsistencia rompía el build
(`models_config.py`) o dejaba agentes muertos sin aviso; el failover por quota existía solo en el lane
Pi. La visión de producto exige lo contrario: dar de baja/alta suscripciones sin tocar nada, y que el
orquestador elija de los modelos QUE LA HERRAMIENTA TIENE, caro donde rinde y costo-rendimiento donde no.

Decisión de producto delegada al harness y resuelta así: **la curación no se borra — se invierte**. La
family curada es la señal que sostiene `REVIEW_FAMILY_CONFLICT` (independencia writer/reviewer,
ADR-0011) y el `route_id` re-validable es la espina de la auditoría (ADR-0005); eliminarlos sería peor
producto.

## Decisión

1. **Pipeline aditivo**: `probe_inventory` (existente) → `discovered_models()` (nuevo, en `catalog.py`)
   → `routing_core/inference.py::synthesize_routes()` (nuevo: StaticRoutes con tier/family INFERIDOS,
   marca `inferred`) → `build_effective_snapshot()` (nuevo wrapper: snapshot curado intacto ∪ rutas
   sintetizadas). `build_snapshot`, `_configured_models`, `load_roles`, `load_role_tiers` conservan
   firma y semántica — todo lo protegido por tests inmutables queda intacto.
2. **Precedencia**: fila curada con mismo `(provider, canonical_model)` GANA siempre; `[[exclusions]]`
   en `routes.v1.toml` veta un id descubierto; una sintetizada que colisiona en family con una curada se
   descarta con aviso.
3. **Inferencia conservadora**: family por vendor-stem grueso (`claude`, `gpt`, `kimi`, `deepseek`,
   `qwen`, `gemini`, `nemotron`, …), tier por sufijo (`-pro/-max` → frontier; `-mini/-nano/-flash` →
   fast; resto y desconocidos → balanced, nunca frontier). Regla de independencia: **lo inferido solo
   puede quitar independencia, nunca otorgarla** — con cualquiera de los dos lados inferido, el
   family-conflict compara por vendor-stem. Decisiones con ruta inferida llevan reason code
   `MODEL_METADATA_INFERRED` — auditable, nunca silencioso.
4. **Suscripciones tri-estado**: `[subscriptions]` `true` = pin curado; `false` = exclusión dura (sigue
   muriendo, test inmutable verde); **ausente = auto (el probe decide)**. `resolve_effective_config()`
   corre antes de `load_roles` en build: celda cuyo modelo requiere una suscripción probe-muerta se
   degrada a la mejor alternativa del mismo tier/duty con `WARN degraded`, re-verificando la separación
   writer/reviewer post-degradación (si no queda alternativa que la preserve: omitir `model:` + warning,
   nunca colisión silenciosa). El build nunca muere por suscripción ausente no-curada; `--strict` para CI.
5. **Frontmatter por lane**: claude-code emite solo aliases universales (`sonnet|opus|haiku`) u omite
   `model:` (un spawn ruteado ya pisa el frontmatter con `--model`, evidencia spec 015); opencode
   mantiene variantes `@tier` alimentadas por el ladder efectivo; codex estático con el mejor openai
   disponible; pi sin cambios (runtime puro).
6. **Failover cross-lane**: `_classify_result` de `claude_code_spawn.py` gana outcome `quota_exhausted`
   (segunda firma settled junto a la de Pi en `domain.py`), reusa
   `close_exhausted_and_authorize_replacement` y reintenta una vez (bounded) con el replacement durable.
7. **Cobertura por clase**: `required_tier` derivado de role-class ADR-0018 (`decision`→frontier,
   `unscoped`→balanced) cuando el descriptor no trae task_class fino; ladder global `[tiers.<tier>]` con
   fallback en `load_role_tiers`; `setup_models.py --sync-tiers` GENERA las tablas por rol para mover el
   lockstep doctrina↔tablas en un solo paquete.

## Rejected alternatives

- **Borrar `models.toml`/`routes.v1.toml`** ("cero curación"): pierde la señal de family para
  independencia y el route_id auditable; un modelo desconocido auto-clasificado como frontier podría
  terminar auditando su propia familia.
- **Invertir `_configured_models`** para que el probe amplíe el set curado: rompe el invariante testeado
  "a runtime can never widen the audited model set" (ADR-0016 d.3); el camino paralelo aditivo obtiene
  lo mismo sin tocar lo auditado.
- **Providers nuevos fuera de `_PAIR_COMMANDS`**: superficie no auditada (SEC-001); el closed set queda.

## Consecuencias

- Alta/baja de suscripción = re-correr `build.sh` (o nada, para el routing en vivo): sin ediciones TOML.
- Una misma tarea de implementación puede caer en sonnet, kimi, nemotron u opus según disponibilidad —
  decisión del orquestador vía routing, trazada con route_id y (si aplica) `MODEL_METADATA_INFERRED`.
- El "excel" pasa de obligatorio a opcional: quien quiera pinnear, pinnea; quien no toque nada, funciona.
