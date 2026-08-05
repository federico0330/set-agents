# ADR-0032 — Materialización en el spawn para opencode/codex y pins de modelo del usuario

- **Status**: Accepted
- **Date**: 2026-08-05
- **Relates to**: ADR-0018 (model preference / bias_class), ADR-0030 (decide siempre),
  ADR-0031 (observabilidad por spawn), ADR-0007 (pi lane), spec 015 (claude-code lane).

## Context

ADR-0030 estableció una decisión de routing por spawn para los 28 roles, pero dejó un hueco
declarado: en los lanes opencode y codex solo los 6 roles tiered materializaban la decisión (vía
variantes `<role>@<tier>`); los ~22 restantes spawneaban el agente base con su default curado y
registraban `MODEL_STATIC_FALLBACK` como camino NORMAL. Los lanes pi
(`set_agents_spawn.py: pi --model provider/id --thinking <effort>`) y claude-code
(`claude_code_spawn.py --model data.model`) ya aplicaban la decisión en el spawn.

Evidencia de CLI (ADR-0026, verificada en vivo esta sesión contra los binarios instalados):

- **opencode 1.18.10**: `opencode run -m provider/model` por invocación (`--help` +
  ejecución real); `--variant <effort>` aceptado por invocación (ejecución real con
  `--variant xhigh` sobre un modelo free, completó normal — advisory: un variant que el
  modelo no define no falla el run). El stream `--format json` (step_start/text/step_finish)
  NO ecoa el modelo servido → este lane no tiene clasificación post-hoc de model_mismatch
  (límite documentado, `detail["model_verified"] = False`).
- **codex-cli 0.146.0**: `codex exec -m <model>`, `-c model_reasoning_effort=<e>` (header
  `reasoning effort: low` observado) y `-c developer_instructions="…"` (el child devolvió el
  codeword de la instrucción) — los tres knobs honrados por invocación. `codex exec --agent`
  NO existe (error verificado), por eso el prompt de rol viaja como `developer_instructions`
  (patrón ADR-0007 de pi `--append-system-prompt`, adaptado).

Además, el wizard de Modelos seguía pidiendo asignar modelos por rol/área como si fuera la
fuente de verdad, cuando desde ADR-0030 la tabla curada es solo fallback.

## Decision

1. **Dos CLIs de spawn nuevos**, `ai/scripts/opencode_spawn.py` y `ai/scripts/codex_spawn.py`
   (precedente estructural `claude_code_spawn.py`, nunca un call into): componen
   `opencode run -m <ref> [--variant <effort>] --agent <role> --format json` (task por
   STDIN — verificado en vivo; nunca un positional: F-01 del review de este feature,
   `MAX_ARG_STRLEN` de 128 KiB por argumento y exposición en `/proc/<pid>/cmdline`) y
   `codex exec --ephemeral --sandbox <mode> -m <model> [-c model_reasoning_effort=<e>]
   -c developer_instructions=<role.md> -o <file> -` respectivamente. Tres modos por
   `role_class`: `--dispatch-writer` (consume el `run_id` ya autorizado; dispatched→spawn→
   terminal; nunca re-decide), `--dispatch-review` (cero bookkeeping; `--supplementary`
   nonce-fenced), `--dispatch-simulate` (SOLO `role_class == "other"`; cero bookkeeping;
   rechaza writer/review — "Never fabricate enforcement" queda verdadero por construcción).
   Mapeo catálogo→CLI: `openai-codex → openai/<model>` (opencode) / `<model>` verbatim
   (codex); `opencode-zen → opencode/<model>`, `opencode-go → opencode-go/<model>`
   (alcanzables solo vía rutas descubiertas ADR-0029); `anthropic` falla cerrado en ambos
   (el redirect claude-code la sirve). Effort: conjunto cerrado {low, medium, high, xhigh},
   advisory — ausente/desconocido omite el flag, nunca falla un spawn.
2. **Precedencia pin > dinámico > fallback curado.** `model-preference.toml` (infra ADR-0018
   reusada, nunca un mecanismo nuevo) gana una tercera tabla `[model_pin]`:
   `role = "provider/model"`, con `"*"` como pin global. Las clases de ADR-0018 no alcanzan
   porque el pin fija una IDENTIDAD (provider+modelo), no un orden de proveedores — de ahí la
   tabla nueva en el MISMO archivo, con la misma disciplina fail-closed y el mismo canal
   interno `_model_preference` hacia `RoutingService`. El pin es un override BLANDO a nivel
   sort: nunca saltea una exclusión dura (auth, independencia de reviewer, piso de tier);
   pinneado y elegible gana incluso cruzando tiers; no elegible degrada al pick dinámico.
   Reason codes aditivos: `MODEL_PINNED p/m` (el pin fue lo seleccionado) /
   `MODEL_PIN_UNAVAILABLE p/m` (pin configurado pero no elegible). CLI:
   `--model-pin-set ROLE PROVIDER/MODEL`, `--model-pin-clear ROLE`,
   `--model-preference-show` extendido.
3. **Observabilidad (ADR-0031 extendido).** Cada decisión registra `selection_path`
   (`"pin"` | `"dynamic"`) en el envelope y en `decisions-v1.jsonl`. El tercer camino, el
   fallback estático curado, existe solo en la materialización y se registra en el spawn
   (`record-spawn --tech` + `MODEL_STATIC_FALLBACK`), como siempre.
4. **`MODEL_STATIC_FALLBACK` pasa a degrade RESIDUAL**: solo cuando el CLI del lane está
   ausente/crasheó o el modelo decidido está fuera del inventario probeado del lane. Nunca
   más el camino normal de los roles no tiered. Las variantes `@tier` y la delegación
   in-process SIGUEN existiendo (el roster tiered queda en 6, contrato congelado) — esto
   agrega un camino dinámico, no las borra.
5. **Wizard de Modelos (Objetivo UX).** El panel declara la política vigente — "Automático
   (recomendado)" (default, sin pedirle nada al usuario) o los pins existentes con su valor —
   y de dónde sale cada valor (decisión dinámica vs pin, registradas en el log; la tabla
   curada solo como fallback, marcadores "DEFAULTS CURADOS" y "ADR-0030" conservados).
   Acción nueva "Routing: fijar modelo / automático" (por rol o global `*`), que escribe vía
   el CLI sancionado con efecto inmediato.
6. **Visibilidad en pantalla por subagente.** Cada subagente instanciado muestra su
   modelo y effort en pantalla, en todo lane: el template narrado gana el bracket
   `▸ Instancio <role> [<provider>/<model> · effort <effort>]`; los spawns no narrados
   lo muestran vía la invocación del CLI de spawn (`--model/--effort` visibles y
   ecoados en el JSON de resultado, campo `effort` incluido) o, en delegación
   in-process (variantes `@tier`, pi interactivo), vía UNA línea de provenance
   `↳ <role> · <provider>/<model> · effort <e>` antes de la llamada (ADR-0027 intacto:
   línea, no bloque). En pi interactivo, además, cada `subagent()` pasa la decisión con
   el override por llamada `model: "<provider>/<id>[:<effort>]"` (param `model` del
   schema de pi-subagents, sufijo `:<thinking>` parseado por `splitKnownThinkingSuffix`
   — verificado contra la extensión instalada), porque el panel de pi-subagents no
   muestra el modelo.
7. **Superficie de permisos.** `coord_policy.SAFE_ARGV` gana dos entradas enumeradas (una por
   CLI, gramática de flags exhaustiva, disciplina DR-02: el mapa debe igualar el `main()`
   real de cada módulo); `generate.py::oc_permissions` lleva las líneas pareadas del lane
   OpenCode (disciplina DR-01). Doctrina "Decide siempre" actualizada en el canonical y
   regenerada a los espejos con `./build.sh`.

## Límites documentados (no inventar flags)

- opencode no ecoa el modelo servido en `--format json` → sin verificación post-hoc de
  modelo en ese lane; un `-m` inválido falla el run (exit != 0 → `failure`).
- `--variant` es advisory por diseño del CLI (un variant inexistente para el modelo no
  falla); el effort decidido queda igualmente registrado (`record-spawn --effort`).
- codex verifica modelo solo si el header `model:` aparece en stdout; ausente →
  `model_verified: false`, clasificación por exit code + last-message.
- El rail de quota-failover durable (ADR-0029/011) reconoce firmas anthropic; un
  agotamiento openai-codex en estos lanes cierra `failure` normal (sin replacement
  automático en el módulo) — el orquestador aplica su retry budget.

## Consequences

- 28/28 roles ejecutan el modelo decidido (o pinneado) en los cuatro lanes; "¿qué modelo
  corrió SPAWN-NNN y por qué?" se responde desde estado: `selection_path` +
  `MODEL_PINNED`/`MODEL_PIN_UNAVAILABLE` en el log de decisiones, `MODEL_STATIC_FALLBACK`
  residual en el spawn record.
- Contratos congelados intactos: roster tiered = 6, frase de doctrina verbatim, DDL de
  routing.db sin cambios, `load_model_preference` conserva su shape público de dos claves
  (los pins cargan por `load_model_pin`, mismo archivo).
- `simulate` sigue sin autorizar nada durable; `--dispatch-simulate` lo garantiza por
  construcción (cero bookkeeping, rechazo de writer/review).

## Verification

`tests/test_spawn_materialization.py` (argv por lane, estilo `test_pi_effort.py`; precedencia
pin/dinámico; `selection_path`; panel nuevo; allowlist), más las suites existentes
(`test_decide_always`, `test_routing` model-preference intactas) y `ai/scripts/verify.sh`.
