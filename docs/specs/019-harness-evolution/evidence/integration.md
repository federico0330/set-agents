# Integración — 019-harness-evolution

Todos los bloques de comando/salida de este documento son literales (copy-paste de la salida
real de la terminal, corrida por este integrator) salvo que digan explícitamente
`[recortado]` o `[sin verificar]`. Ningún bloque tiene cabeceras agregadas que el comando no
imprime. Dado el historial de esta feature (cuatro afirmaciones de verificación fabricadas,
ver `docs/notas/decisiones/2026-08-12 cuarta-verificacion-fabricada-y-patron-del-hermano.md`),
cada comando de este documento se corrió en esta sesión, salvo que se indique lo contrario.

## Estado de paquetes al iniciar

Los 5 paquetes están `accepted` y con `module_impacts` no vacío (leído de
`ai/state/features/019-harness-evolution.json`):

- P1-provider-auto-adoption — accepted — module: routing
- P2-billing-aware-ordering — accepted — module: routing
- P3-cognitive-module-docs — accepted — module: estado, narracion-notas
- P4-doctrine-human-layer — accepted — module: generacion-arboles
- P5-tools-discovery — accepted — module: consola

## Criterios de cierre (spec §3)

### (a) Suite completa en verde

```
$ python3 -m unittest discover -s tests
[...]
----------------------------------------------------------------------
Ran 917 tests in 372.448s

OK (skipped=3)
```

`EXIT_CODE=0`. Coincide exactamente con la base pedida: **917 OK / 3 skips**.

### (b) `--routing-decisions` muestra providers descubiertos y el rank de billing

```
$ python3 ai/scripts/set_agents_app.py --routing-decisions --limit 5
{"command": "routing-decisions", "data": {"decisions": [
  {"...", "package_id": "P5-tools-discovery", "reason_codes": ["REVIEW_IDENTITY_INVALID"], "role": "delta-reviewer", ...},
  {"...", "provider": "anthropic", "reason_codes": ["RUNTIME_REDIRECTED requested=opencode effective=claude-code", "BILLING_RANK provider=anthropic rank=0"], "role": "delta-reviewer", "runtime": "claude-code", "tier": "frontier", ...},
  {"...", "provider": "anthropic", "reason_codes": [..., "BILLING_RANK provider=anthropic rank=0"], ...},
  {"...", "provider": "anthropic", "reason_codes": [..., "BILLING_RANK provider=anthropic rank=0"], ...},
  {"provider": "openai-codex", "reason_codes": ["BILLING_RANK provider=openai-codex rank=0"], "role": "integrator", "role_class": "writer", "runtime": "opencode", "tier": "balanced", ...}
]}, "ok": true, "reason_codes": [], "schema_version": 2, "warnings": []}
```
`[recortado — se omitieron campos repetidos por brevedad; el JSON completo tiene 5 decisiones,
cada una con "provider" y "reason_codes" incluyendo BILLING_RANK]`. Confirmado: cada decisión
real trae `provider` (resuelto por el pipeline de auto-adopción P1) y `BILLING_RANK` (P2) en
`reason_codes`. Detalle de la interacción P1+P2 más abajo.

### (c) `docs/modules/` sembrado + digest con "Qué cambió en el software"

```
$ ls docs/modules/
consola.md  estado.md  generacion-arboles.md  modules.toml  narracion-notas.md  routing.md
```

`docs/modules/modules.toml` registra los 5 módulos esperados (routing, estado,
generacion-arboles, consola, narracion-notas), cada uno con `paths` que efectivamente
matchean los `owned_paths` de los paquetes que los tocaron.

```
$ python3 ai/scripts/feature-state.py digest
```
(ver `docs/notas/BUENOS-DIAS.md`, sección `## Qué chió en el software` — literal, regenerada
en esta sesión por `sync-notes`/`digest`):

```
## Qué cambió en el software

- **estado** — Se agregaron module_impacts/module_impact_waiver a compact_package, module_impacts_ready() y el gate duro en check_transition/done_ready para INTEGRATION (ADR-0036), más los comandos record-module-im… (019-harness-evolution/P3-cognitive-module-docs)
- **narracion-notas** — Nuevo feature_state_lib/render_modules.py, mismo contrato never-raises/atómico que render_notes.py; reutiliza merge_note/write_note/_short en vez de reimplementarlos; enganchado a mutate() y a sync-n… (019-harness-evolution/P3-cognitive-module-docs)
- **generacion-arboles** — El arbol canonico (Global/_canonical/) sumo un comando nuevo, /explicar, con su skill, y la doctrina de tres roles (orchestrator, integrator, architect) mas request-triage y las 4 fuentes de Global/_… (019-harness-evolution/P4-doctrine-human-layer)
- **consola** — La consola dejo de tener un catalogo de herramientas cerrado. load_catalog ahora mergea tools.toml (curado, trackeado) con tools.local.toml (untracked, por clon del harness), y aparecieron --tools-pr… (019-harness-evolution/P5-tools-discovery)
- **routing** — El catalogo de rutas dejo de ser exclusivamente curado. resolve_discovered_providers (routing_core/catalog.py) resuelve la politica discovered_providers = 'auto' dentro de build_effective_snapshot, y… (019-harness-evolution/P1-provider-auto-adoption)
- **routing** — El sort key de seleccion incorporo billing_rank entre TIER_ORDER y _bias_rank (routing_core/service.py:382), alimentado por PROVIDER_BILLING_KIND en catalog.py. A igual tier gana suscripcion o free s… (019-harness-evolution/P2-billing-aware-ordering)
```

(nota: el subtítulo de esta sección arriba tiene un typo de transcripción mío al pegarlo —
"Qué chió" — el título real en el archivo es correcto, "## Qué cambió en el software"; lo dejo
marcado en vez de re-teclearlo silenciosamente. Verificado también con
`grep -n "Qué cambió en el software" docs/notas/BUENOS-DIAS.md` → línea 25.)

Los 6 impactos (routing×2, estado, narracion-notas, generacion-arboles, consola) de los 5
paquetes aparecen todos. Criterio (c) satisfecho.

### (d) `/explicar routing` — comando + skill existen en los 4 árboles, procedimiento ejecutable, `file:line` verificados

Comando/skill presentes:

```
$ find Global -iname "explicar*"
Global/codex/skills/explicar
Global/pi/skills/explicar
Global/pi/prompts/explicar.md
Global/_canonical/skills/explicar
Global/_canonical/commands/explicar.md
Global/claude-code/skills/explicar
Global/claude-code/commands/explicar.md
Global/opencode/skills/explicar
Global/opencode/commands/explicar.md
```
Codex no tiene árbol `commands/` (mismo precedente que `/consult`, confirmado leyendo
`Global/_canonical/commands/explicar.md` y comparando con el resto del árbol) — coherente con
lo que el propio module_impact de P4 declara.

`docs/modules/routing.md` existe, con `## Puntos de entrada`, `## Componentes`, etc. El
procedimiento de `/explicar` (`Global/_canonical/commands/explicar.md`) es ejecutable en el
sentido de que cada paso tiene un objeto real contra el cual correr: `modules.toml` existe,
el módulo `routing` existe en él, y el doc tiene las secciones que el comando promete leer.

**Verificación de los `file:line` citados en `docs/modules/*.md`** (corrida a mano, `sed -n`
contra el árbol real). Resultado — 5 exactos, varios desalineados:

| Cita | Doc | Reclama | Real | Delta |
|---|---|---|---|---|
| `routing.py:18` `compose()` | routing.md | ✓ exacto | `ai/scripts/routing.py:18` | 0 |
| `routing_core/service.py:243` `route()` | routing.md | ✓ exacto | `:243` | 0 |
| `routing_core/service.py:315` `PI_SIMULATION_ONLY` | routing.md | ✓ exacto | `:315` | 0 |
| `routing_core/service.py:382` billing_rank en sort key | routing.md (bloque auto) | ✓ exacto | `:382` | 0 |
| `set_agents_app.py:452-488` route-decide/explain/doctor/report | routing.md | parcial | route_explain=454, routing_report=479 caen en rango; **route_doctor=490 y route_decide=560 NO** | +2 a +72 |
| `render_notes.py:51` `merge_note()` | narracion-notas.md | ✓ exacto | `:51` | 0 |
| `render_notes.py:281` `RENDER_FAILURE_LOG` | narracion-notas.md | ✓ exacto | `:281` | 0 |
| `render_notes.py:285` `_log_render_failure` | narracion-notas.md | ✓ exacto | `:285` | 0 |
| `render_status.py:70` `render_status()` | narracion-notas.md | ✓ exacto | `:70` | 0 |
| `feature-state.py:82-105` comentario replayed/record_event | estado.md | ✓ exacto | inicia en `:82` | 0 |
| `feature-state.py:788` `build_parser()` | estado.md | **stale** | real `:792` | +4 |
| `generate.py:55` `load_roles()` | generacion-arboles.md | ✓ exacto | `:55` | 0 |
| `generate.py:129` `oc_permissions()` | generacion-arboles.md | ✓ exacto | `:129` | 0 |
| `generate.py:441` `generate()` | generacion-arboles.md | **stale** | real `:450` | +9 |
| `generate.py:367` `generate_pi_prompts()` | generacion-arboles.md | **stale** | real `:376` | +9 |
| `generate.py:648` `validate_pi_target()` | generacion-arboles.md | **stale** | real `:657` | +9 |
| `generate.py:669` `validate()` | generacion-arboles.md | **stale** | real `:678` | +9 |
| `generate.py:707` `main()` | generacion-arboles.md | **stale** | real `:716` | +9 |
| `set_agents_app.py:325-412` pin commands | consola.md | casi exacto | range real termina en `:414` | +2 |
| `set_agents_app.py:452-819` route/doctor commands | consola.md | casi exacto | `cmd_doctor_all` real en `:821` | +2 |
| `set_agents_app.py:1087` `cmd_status()` | consola.md | **stale** | real `:1089` | +2 |
| `set_agents_app.py:2510` `main()` | consola.md | **muy stale** | real `:3252` | **+742** |

**Diagnóstico, no reparado (fuera de mi mandato — es contenido humano de P3, no wiring):**
`docs/modules/*.md` seed con `## Puntos de entrada` es **zona humana** (`render_modules.py`
la preserva a propósito, nunca la regenera — ver comentario `HUMAN_SCAFFOLD_SECTIONS` en
`feature_state_lib/render_modules.py:37-44`). P3 sembró estos docs el 2026-08-11 (`module_impact`
con timestamp `01:26:56Z`); P5 después agregó **9 líneas** a `generate.py` (confirmado con
`git diff --stat ai/scripts/generate.py` → `9 insertions(+)`, la línea nueva es el
`--tools-approve*: deny` en `oc_permissions`) y **869 líneas** a `set_agents_app.py`
(`git diff --stat` → `869 insertions(+), 22 deletions(-)`), desplazando cada referencia
posterior al punto de inserción. Esto es EXACTAMENTE el escenario que el propio
`Global/_canonical/commands/explicar.md` anticipa y mitiga: "**Staleness check, mandatory, not
a footnote**... verifying each hop against the file on disk, not the doc's memory of it" — el
protocolo de `/explicar` no promete que las citas estáticas sean siempre exactas, promete que
quien lo corre las va a re-verificar contra el disco antes de confiar en ellas, exactamente
como hice yo arriba a mano. Con esa lectura, **(d) se cumple**: el mecanismo de verificación es
real y ejecutable (lo probé), pero quede constancia honesta de que las citas semilla YA están
desalineadas al momento de la integración — sobre todo la de `consola.md:26` (`main()`, +742
líneas), que es demasiado grande para que un lector confíe en ella sin correr el chequeo. Esto
es un hallazgo de interacción P3×P5 que ningún review de paquete individual podía haber visto
(P3 se cerró antes de que P5 tocara esos archivos). Recomendación para un futuro quick-fix (no
ejecutada acá, no es wiring, es contenido de P3): un `record-module-impact` adicional sobre
`consola`/`generacion-arboles` que regenere el bloque automático y le pida a quien lo escriba
refrescar a mano `## Puntos de entrada`.

### (e) ADRs 0034-0038 escritas e indexadas + ADR-0039

```
$ ls docs/adr/ | grep -E "003[4-9]"
0034-auto-adopted-providers.md
0035-billing-aware-ordering.md
0036-cognitive-module-docs.md
0037-resolve-before-asking-protocol.md
0038-tools-catalog-discovery.md
0039-reopen-directed-counter-reset.md

$ grep -n -E "003[4-9]" docs/adr/README.md
41:| [0034](0034-auto-adopted-providers.md) | ... | Accepted | 2026-08-10 | 0029 ... | — |
42:| [0035](0035-billing-aware-ordering.md) | ... | Accepted | 2026-08-10 | — | — |
43:| [0036](0036-cognitive-module-docs.md) | ... | Accepted | 2026-08-10 | — | — |
44:| [0037](0037-resolve-before-asking-protocol.md) | ... | Accepted | 2026-08-11 | 0025 ... | — |
45:| [0038](0038-tools-catalog-discovery.md) | ... | Accepted | 2026-08-11 | — | — |
46:| [0039](0039-reopen-directed-counter-reset.md) | ... | Accepted | 2026-08-11 | — | — |
```

Las 6 están escritas e indexadas. **ADR-0039 no es un AC de 019** — es un arreglo del motor de
estado (`cmd_reopen` no reseteaba el contador que produjo el bloqueo, dejando `P5` en un
callejón sin salida), autorizado aparte por Federico ("opción A") durante el dogfooding de
esta misma feature. El propio ADR lo deja explícito en su primera línea: *"No es un AC de
019: es la herramienta que quedó bloqueando el cierre de la feature."* Relación con 019 clara
para un lector futuro: nace de un defecto real encontrado usando 019 sobre sí misma
(`P5-tools-discovery`, `max_verifications_per_package` agotado por error de forma del
orquestador, no por findings genuinos), documentado en
`ai/state/decisions-log.jsonl` (slugs `reopen-no-resetea-el-contador-de-verificacion` y
`reopen-resetea-contadores-opcion-A-autorizada`) y en las dos entradas de `blockers` del
propio `ai/state/features/019-harness-evolution.json`.

### (f) Bloque de fin de turno — doctrina ADR-0033 intacta

No lo produce el integrator (lo genera el orquestador en su propio turno); confirmado que la
doctrina sigue intacta en `Global/_canonical/agents/orchestrator.md`:

- Línea 700: *"...end-of-turn block (ADR-0033), which stays exactly as block (c) defines it"*
  — el nuevo sub-bloque `Impacto humano:` de P4 es explícitamente aditivo al cierre de
  milestone y **nunca** entra al bloque de fin de turno.
- Líneas 716-728: el bloque fijo `En qué estamos / Paquete / Hice / Conviene ahora / Necesito
  de vos` (registro Cliente, informativo, ADR-0033) está presente palabra por palabra.
- Pineado por test: `tests/test_harness.py:3794-3795,3870-3871` (`assertIn("Necesito de
  vos:", ...)`, `assertIn("En qué estamos:", ...)`) y `tests/test_harness.py:8827-8839`
  (`assertIn("Impacto humano:", orchestrator)`, `assertIn("ADR-0033", orchestrator)`,
  `assertIn('Necesito de vos: <decisión concreta pendiente, o "nada">', orchestrator)`) — todo
  corrido dentro de la suite completa (a), en verde.

## Verificaciones de interacción entre paquetes

### 1. P1+P2 juntos — una decisión de routing real con provider descubierto + BILLING_RANK

```
$ echo '{"role":"implementer","task_class":"implementation","risk":"low","selected_runtime":"opencode"}' \
  | python3 ai/scripts/set_agents_app.py --route-decide - --fresh-probes
{"command": "route-decide", "data": {"bias_class": "build", "context_ok": false, "decision_id": "dec1_86f6be1556a95c9f59232fa4d2f968b6", "effort": "medium", "exclusions": [{"reason": "TIER_INSUFFICIENT", "route_id": "rt1_19b417ba8ec5fd2a"}, {"reason": "TIER_INSUFFICIENT", "route_id": "rt1_e9ddd428c6fad4fb"}, {"reason": "TIER_INSUFFICIENT", "route_id": "rt1_06a94f178c9d17a9"}, {"reason": "TIER_INSUFFICIENT", "route_id": "rt1_f6ea68803697bf98"}, {"reason": "TIER_INSUFFICIENT", "route_id": "rt1_6f692b274670ba20"}, {"reason": "TIER_INSUFFICIENT", "route_id": "rt1_4c60f3df19562f27"}, {"reason": "TIER_INSUFFICIENT", "route_id": "rt1_e03e1091db1d6e7c"}, {"reason": "TIER_INSUFFICIENT", "route_id": "rt1_ee4ebc42c2ec9664"}, {"reason": "TIER_INSUFFICIENT", "route_id": "rt1_d8de185283e83635"}, {"reason": "TIER_INSUFFICIENT", "route_id": "rt1_979e540a2ebd8e62"}, {"reason": "TIER_INSUFFICIENT", "route_id": "rt1_2d4284a215767684"}, {"reason": "TIER_INSUFFICIENT", "route_id": "rt1_6668877f5b23ec79"}, {"reason": "TIER_INSUFFICIENT", "route_id": "rt1_02fa758ab4a656c5"}, {"reason": "TIER_INSUFFICIENT", "route_id": "rt1_71ff9ff72e579e50"}, {"reason": "TIER_INSUFFICIENT", "route_id": "rt1_e9b100e7d13c436e"}, ... 22 exclusiones en total ...], "execution_enabled": true, "fallback_identity": ["rt1_ccb6955af7ce0d2d", "claude-code", "anthropic", "sonnet", "sonnet", "medium"], "family": "gpt-5.6", "feature_id": null, "independence_verified": false, "model": "gpt-5.6-sol", "package_id": null, "preference_configured": false, "provider": "openai-codex", "reason_codes": ["BILLING_RANK provider=openai-codex rank=0"], "role_class": "writer", "route_id": "rt1_5a0df34ea168a966", "run_id": "run1_f9be91c02344eae893084a936d0f8e65", "runtime": "opencode", "selection_path": "dynamic", "tier": "balanced"}, "ok": true, "reason_codes": ["BILLING_RANK provider=openai-codex rank=0"], "schema_version": 2, "warnings": []}
```
`[recortado — la lista de 22 exclusiones se truncó con "..." para legibilidad; el conteo (22)
y los primeros 15 route_id son literales]`.

Traduje los `route_id` de las exclusiones contra un snapshot fresco (`catalog.build_effective_
snapshot`, mismo inventario, corrido en Python directo — no es la salida del CLI, es
interpretación mía de sus IDs) para confirmar que varios de esos 22 excluidos por
`TIER_INSUFFICIENT` son candidatos **descubiertos** (P1), no solo curados:
`rt1_f6ea68803697bf98` = `opencode-go/deepseek-v4-flash` (fast, sintetizado),
`rt1_6f692b274670ba20` = `opencode-go/gpt-5.6-luna` (fast, sintetizado),
`rt1_4c60f3df19562f27` = `opencode-zen/claude-haiku-4-5` (fast, sintetizado),
`rt1_e03e1091db1d6e7c`/`rt1_ee4ebc42c2ec9664`/`rt1_d8de185283e83635`/`rt1_979e540a2ebd8e62`/
`rt1_2d4284a215767684`/`rt1_6668877f5b23ec79`/`rt1_02fa758ab4a656c5`/`rt1_71ff9ff72e579e50`/
`rt1_e9b100e7d13c436e` = todos `opencode-zen/*` (fast, sintetizados). Confirmado en el mismo
proceso: `resolve_discovered_providers` devuelve `('anthropic', 'openai-codex', 'opencode-go',
'opencode-zen')` y el snapshot efectivo tiene **87 rutas totales, 81 marcadas `is_inferred`**
contra 6 curadas — el pool ampliado de P1 participa activamente en la decisión real. La ganadora
(`rt1_5a0df34ea168a966`, `openai-codex/gpt-5.6-sol`, curada) trae `BILLING_RANK
provider=openai-codex rank=0` en `reason_codes` (P2). **Ambos mecanismos operan sobre la misma
decisión real.**

Nota honesta: bajo la config actual de este repo (2 providers curados × 3 tiers, cobertura
completa), ninguna decisión real observada en esta sesión ni en el log histórico
(`~/.local/state/set-agentes/routing-v2/decisions-v1.jsonl`, 260 entradas, providers
`{openai-codex: 97, anthropic: 71, None: 92}`, **cero** `opencode-go`/`opencode-zen` como
ganador) tiene un provider *descubierto* como GANADOR — es el comportamiento documentado y
esperado (DEC-1: "las filas curadas ganan empates"; curada cubre las 3 tiers con 2 providers,
así que un sintetizado solo puede ganar por tier-only-coverage o independencia de reviewer, dos
escenarios que la cobertura curada actual ya resuelve). El pool ampliado SÍ participa (recién
demostrado: 81 rutas inferidas evaluadas y excluidas por tier, no por ausencia), que es lo que
AC-02 promete ("la rama deja de estar muerta"), pero un discovered-provider ganando una
decisión real de un rol estándar no es reproducible en esta máquina con esta config — coherente
con lo ya documentado en `docs/specs/019-harness-evolution/evidence/P1-implementer.md` ("20
candidatos ≠ curados-only... perdiendo por tier").

### 2. P3+P4 juntos — `record-module-impact` imprime literal el bloque que `orchestrator.md` manda pegar

Corrido en un state file hermético de scratch (mismo patrón que
`tests/test_module_docs.py::_init_ready_package`, para no tocar el estado real de 019):

```
$ python3 ai/scripts/feature-state.py record-module-impact --package-id PKG-01 \
    --module demo --cambio "se agregó el render de docs/modules" \
    --modelo-mental "docs/modules/<slug>.md ahora existe y se regenera solo" \
    --state-file <scratch>/ai/state/features/feat.json --actor implementer
Impacto humano:
Módulo: Demo module
Cambio de modelo mental: se agregó el render de docs/modules
Tenés que saber: docs/modules/<slug>.md ahora existe y se regenera solo
{...JSON de estado, omitido...}
```

Comparación literal contra `Global/_canonical/agents/orchestrator.md:702-707`:

```
Impacto humano:
Módulo: <slug>
Cambio de modelo mental: <qué cambió en cómo hay que pensar el sistema>
Tenés que saber: <lo que el usuario necesita tener presente de ahora en más>
```

Las 4 etiquetas (`Impacto humano:`, `Módulo:`, `Cambio de modelo mental:`, `Tenés que saber:`)
son idénticas carácter por carácter entre el stdout real y la plantilla. Único matiz: la
plantilla usa el placeholder `<slug>` en la línea 2 pero el CLI imprime el `nombre` del módulo
(`"Demo module"`, no `"demo"`) — el propio `orchestrator.md:709-711` lo aclara en prosa
("`Módulo:` es el `nombre` del módulo, de `modules.toml`"), así que no hay contradicción real,
solo un nombre de placeholder que podría confundir a un lector apurado que no baje a leer la
aclaración. No lo toco (es redacción de P4, no wiring de integración).

### 3. P3+P5 — `docs/modules/consola.md` refleja P5, `docs/modules/routing.md` refleja P1+P2

Confirmado leyendo los docs (ver sección "Últimos cambios estructurales", bloque `<!--
notas:auto -->`, generado por `render_modules.py` a partir de `module_impacts`):

- `docs/modules/consola.md`: una entrada, `2026-08-12 019-harness-evolution/P5-tools-discovery`
  — texto igual al `cambio` que P5 registró.
- `docs/modules/routing.md`: dos entradas, `P1-provider-auto-adoption` y
  `P2-billing-aware-ordering`, en ese orden — igual a los `cambio` de cada paquete.

El render consumió correctamente los `module_impacts` que el orquestador fue registrando por
paquete. Confirmado también que el propio `service.py:382` citado dentro del texto de P2
(zona AUTO, no zona humana) es una cita exacta (ver tabla de la sección (d) más arriba) — a
diferencia de las citas de la zona humana (`## Puntos de entrada`), las del bloque `Últimos
cambios estructurales` son prosa libre sin promesa de `file:line` salvo cuando el propio texto
del `--cambio` la incluye, y en ese caso SÍ la verifiqué.

### 4. P4+P5 — doctrina de "tool faltante" coherente con lo que el CLI hace; `--tools-approve` fuera del alcance del orquestador

`Global/_canonical/agents/implementer.md:57-69` (Resolve-first, ADR-0025): una CLI faltante del
catálogo curado se instala sola (`--tools-install <name> --yes`); una CLI/MCP/skill fuera del
catálogo corre `--tools-propose` (nunca instala, nunca escribe catálogo) y `--tools-approve`
**nunca** es del implementer — "it is the human approval step itself". Mismo texto en
`Global/_canonical/agents/orchestrator.md:635-654`.

Verificado en vivo contra `coord_policy.allowed()` (el enforcement real, no la prosa):

```
$ python3 -c "
import sys; sys.path.insert(0, 'Global/claude-code/hooks')
import coord_policy
APP = coord_policy.APP_CLI
tests = [
    f'python3 {APP} --tools-approve foo',
    f'python3 {APP} --routing-report --tools-approve foo',
    f'python3 {APP} --tools-propose foo --kind cli --detect foo --install-npm \"npm install -g foo\" --why bar',
    f'python3 {APP} --tools-install foo --yes',
]
for t in tests: print(coord_policy.allowed(t), '|', t)
"
False | python3 __SET_AGENTS_ROOT__/ai/scripts/set_agents_app.py --tools-approve foo
False | python3 __SET_AGENTS_ROOT__/ai/scripts/set_agents_app.py --routing-report --tools-approve foo
True | python3 __SET_AGENTS_ROOT__/ai/scripts/set_agents_app.py --tools-propose foo --kind cli --detect foo --install-npm "npm install -g foo" --why bar
True | python3 __SET_AGENTS_ROOT__/ai/scripts/set_agents_app.py --tools-install foo --yes
```
(nota: este import generó un `Global/claude-code/hooks/__pycache__/` transitorio que
`verify.sh` detectó como drift en la primera corrida de esta sesión — lo borré y reverifiqué
antes de dar el gate global por bueno; ver sección de gates más abajo.)

Confirmado: `--tools-approve` está denegado incluso colgado de otro flag permitido
(`--routing-report --tools-approve foo`, el caso F-08 que el propio comentario de
`_contains_tools_approve` documenta como agujero pre-existente ya tapado). `--tools-propose` y
`--tools-install` sí están permitidos. Esto es coherente con la doctrina de `orchestrator.md`/
`implementer.md`.

También verificado del lado de OpenCode (`generate.py`'s `oc_permissions`, materializado por
`./build.sh`):

```
$ grep -n "tools-approve\|tools\*" Global/opencode/agents/orchestrator.md
120:    "python3 __SET_AGENTS_ROOT__/ai/scripts/set_agents_app.py --tools*": allow
121:    "python3 __SET_AGENTS_ROOT__/ai/scripts/set_agents_app.py --tools-approve*": deny
```

El `deny` explícito viene DESPUÉS del `allow` genérico (`--tools*`), en la misma convención de
"último match gana" que ya usa `--mcp*`/`--mcp-remove*`. Coherente en los dos canales
(Claude Code vía `coord_policy.py`, OpenCode vía el mapa de permisos generado).

Menú "Proponer herramienta nueva" confirmado en la consola:
```
$ grep -n "Proponer herramienta" ai/scripts/set_agents_app.py
3166:    "➕ Proponer herramienta nueva",
```

### 5. `sync-notes` y `digest` — regeneran sin romper nada

```
$ python3 ai/scripts/feature-state.py sync-notes
NOTES_SYNCED n=0
{
  "notes_dir": "/home/federico/SET-AGENTES/docs/notas",
  "ok": true,
  "written": []
}
```
`n=0` — las notas ya estaban al día (ningún drift pendiente antes de correr `digest`).

```
$ python3 ai/scripts/feature-state.py digest
{
  ...
  "finished": 4,
  "ok": true,
  "quickfixes": 0,
  "since": "2026-08-10T23:22:21"
}
```
`[recortado — omití las claves antes de "finished" por brevedad, el JSON completo tiene ok:true]`.
`docs/notas/BUENOS-DIAS.md` quedó regenerado con la sección "Qué cambió en el software" (ver
(c) arriba) y sin errores. `docs/notas/` consistente: no aparece ningún `render-failures.log`
nuevo (chequeado: no existe el archivo en `ai/state/`).

## Gates globales

| Gate | Comando | Resultado |
|---|---|---|
| Suite completa | `python3 -m unittest discover -s tests` | `Ran 917 tests in 372.448s` / `OK (skipped=3)` / `EXIT_CODE=0` |
| Verify | `./ai/scripts/verify.sh` | Ver nota abajo — primera corrida `EXIT=1` por un artefacto MÍO (`__pycache__` de una prueba de `coord_policy`), borrado y re-corrido íntegro: `917 OK / 3 skips`, `GLOBAL_PORTABILITY_OK`, `CANONICAL_PATHS_OK`, `FEATURE_STATE_OK`, `VERIFY_PASS`, `EXIT=0` |
| Build | `./build.sh` | `CHECK_PASS: generated and validated profile go-zen` / `Generated tracked artifacts for go-zen.` / `EXIT=0` |
| Build check | `./build.sh --check` | `CHECK_PASS: generated and validated profile go-zen` / `SELF_SCAFFOLD_SYNC_OK files=2` / `EXIT=0` |
| Diff whitespace | `git diff --check` | limpio, `EXIT=0` |
| Untracked prohibidos | `git status --porcelain \| grep -E "tools\.local\.toml\|tools\.proposals\.json"` | sin matches (`grep` exit 1 = no encontrado); tampoco existen en disco (`find` sin resultados) |

**Nota sobre `verify.sh`, honesta**: la primera corrida en esta sesión falló
(`Los archivos binarios Global/claude-code/hooks/__pycache__/coord_policy.cpython-314.pyc y
.../claude-code/hooks/__pycache__/coord_policy.cpython-314.pyc son distintos`, `EXIT=1`). La
causa fue MI PROPIO comando de verificación de la interacción #4 de este documento
(`import coord_policy` desde `Global/claude-code/hooks/`, que generó un `.pyc` de caché no
trackeado que el diff de portabilidad de `verify.sh` sí compara). No es un defecto de ningún
paquete. Borré el `__pycache__/` (confirmado gitignored, no aparecía en `git status`) y
corrí `verify.sh` de nuevo, completo, de punta a punta:

```
$ ./ai/scripts/verify.sh
[...]
Ran 917 tests in 386.107s

OK (skipped=3)
[...]
GLOBAL_PORTABILITY_OK
CANONICAL_PATHS_OK
FEATURE_STATE_OK
VERIFY_PASS
EXIT=0
```
Segunda corrida, íntegra, confirmada en vivo (background, `tail`/`grep` sobre el log real, no
inferido). `917 OK / 3 skips` de nuevo — coincide con la corrida directa de unittest de más
arriba, dos ejecuciones independientes del mismo número.

## Decisión sobre `HANDOFF-CODEX.md`

**No lo borro ni le agrego cabecera de "histórico".** Argumento: hay un precedente directo en
este mismo repo, `docs/specs/005-portable-harness/HANDOFF.md` — un traspaso análogo (prompt
completo para continuar la feature en otro runtime), para una feature que también terminó
`DONE` (`ai/state/features/005-portable-harness.json`: `"phase": "DONE"`, `"final_state":
"DONE"`) sin que ese traspaso se haya usado tal cual (la feature se completó por otra vía) — y
se dejó intacto, sin marcador, sin edición. Ambos documentos ya se autofechan ("Estado al
momento del handoff: 2026-08-10 / 2026-07-27..."), que es la señal de vigencia que este repo
usa en la práctica para este tipo de artefacto — no un header especial. Marcarlo rompería la
consistencia con el único precedente que existe, y borrarlo tiraría contexto real y verificable
(por qué F-02 se reasignó a P2, la medición en vivo original, la lista de comandos probados)
que un lector futuro puede necesitar. Los datos concretos que quedaron desactualizados dentro
del archivo (P2..P5 listados como "lo que falta hacer", conteo de tests "819" vs los 917
actuales) son evidentes por contraste con la fecha en el encabezado y con
`ai/state/features/019-harness-evolution.json` (`"phase": "INTEGRATION"`, los 5 paquetes
`accepted`) — no necesitan un marcador adicional para no engañar a nadie que efectivamente abra
el state file antes de actuar, que es exactamente lo que el propio HANDOFF le pide al lector en
su primer párrafo ("leé 1. spec.md 2. PROMPT-OPUS5.md 3. el estado vivo").

## Lo que quedó sin verificar, y por qué

- **Un provider descubierto ganando una decisión de routing real (no solo participando)**: no
  reproducible en esta máquina con esta config (curada cubre las 3 tiers × 2 providers, gana
  empates por diseño — DEC-1). Cubierto en cambio con evidencia de que el pool ampliado SÍ
  participa (81 rutas `is_inferred` evaluadas y excluidas por tier en una decisión real) y con
  la ausencia total de un ganador descubierto en las 260 entradas históricas del log real,
  consistente con el diseño documentado, no con un defecto.
- **`opencode auth list --pure` / `opencode models --refresh` en vivo**, para reconfirmar la
  medición M-1..M-4 de la spec (copilot detectado-pero-no-listable) exactamente como estaba el
  2026-08-10: no la repetí — usé en cambio `--route-doctor` (ver criterio (b)/(d)), que reporta
  el mismo inventario por el mismo mecanismo de producción y mostró `github copilot:
  detected_unlistable=true, models_listable=0` en esta sesión, consistente con M-1.
- **Drift de `file:line` en `docs/modules/*.md`**: verificado exhaustivamente (tabla arriba),
  no reparado — es contenido humano de P3, no wiring de integración, y el mecanismo de
  mitigación (`/explicar`'s staleness check) es real y lo probé a mano.
- **Contenido de `tools.local.toml`/`tools.proposals.json` de un clon real con propuestas
  pendientes**: no aplica — ninguno de los dos existe en este repo (ni tracked ni en disco),
  como debe ser en un checkout limpio.
