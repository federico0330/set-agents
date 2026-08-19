# 034 — tareas (pre-planificación)

Ordenadas. El package-planner puede reagrupar; no puede borrar un AC.
Ownership de código es pista, no asignación. Local validation = lo que
el implementer corre **por tarea**, no el gate de paquete.

Leyenda de paquetes tentativos: **A** orgánico · **B** escritor barato ·
**C** techo + métrica · **D** pins Cursor.

## PKG-A — ruteo orgánico enforceable

| ID | Trabajo | AC | Validación local | Checkpoint |
|---|---|---|---|---|
| T-A01 | Alinear `request-triage` y `orchestrator.md`: default 1–3 = quick-fix; tabla no llama `scoped` "default" para ese caso; el 3 sigue cruzado con ADR-0020. Tercera superficie: error `RISK_SIGNAL_REQUIRED` (AC-A.3) | AC-A.1 | `./build.sh --check` (skills se emiten a los 5 targets) | — |
| T-A02 | Persistir señal de riesgo en `init` (verbo `feature-state.py`). Lista cerrada de tokens. Sin señal, `scoped`/`feature` → `RISK_SIGNAL_REQUIRED`. `init --mode quick-fix` sigue legal | AC-A.3, AC-A.6, AC-X.2 | unittest: init scoped sin señal → `RISK_SIGNAL_REQUIRED`; `init --mode quick-fix` ok; `user-asked-full-pipeline` → ok | Schema: architecture nombra el campo (UNVERIFIED) |
| T-A03 | Test de mordida: fixture 1–3 archivos / copy / sin señal que **falla** si el modo queda `scoped`/`feature`. No-init = éxito. `init --mode quick-fix` no pinta de rojo | AC-A.2, AC-A.6 | ver el test rojo con un `init --mode scoped` sucio; restaurar; verde | Obligatorio ver RED |
| T-A04 | Confirmar `log-quickfix` intacto (flags `:1194-1201`); doctrina de cierre sigue mandatoria | AC-A.4 | los tests existentes de `log-quickfix` siguen verdes | No aflojar asserts |
| T-A05 | Precedencia 033 AC-6.1 + gate rojo en quick-fix: no salvage; reintento local o escala con señal | AC-A.5 | grep/doctrina; un test que quick-fix no llama context pack ni salvage | No tocar código 033 |

Ownership A: `Global/_canonical/skills/request-triage/SKILL.md`,
`Global/_canonical/agents/orchestrator.md`, `ai/scripts/feature-state.py`,
`ai/scripts/feature_state_lib/cli_lifecycle.py` (init), tests.

## PKG-B — escritor barato + salvage + test `-fast`

| ID | Trabajo | AC | Validación local | Checkpoint |
|---|---|---|---|---|
| T-B01 | Elegir el default barato/free que **cumple tools**. Actualizar `[areas.implement]` y overrides `code-rw`. Feature nueva = BASE, **no** `writer_tier="fast"` / `implementer@fast`. `billing_rank` no se reescribe | AC-B.1 | probe vivo + unittest: paquete 1 no despacha `@fast` | UNVERIFIED: ¿`deepseek-v4-flash-free` sirve de implementer? |
| T-B02 | Reescribir `test_repo_go_zen_routes_hot_path_to_fast_variants_and_keeps_reviewers_apart` (`:733-766`): sacar `product-analyst` del loop `-fast`; asertar barato/free en `implementer` + un segundo `code-rw`; conservar independencia `:750-766`. Comentario con la razón nueva (patrón ADR-0044) | AC-B.2, AC-B.3, AC-B.7 | mordida: romper el pin barato → ROJO; restaurar → VERDE | Architecture enmienda ADR-0044 (fuera de este rol) |
| T-B03 | Recorrer la suite por otros anclajes `-fast` de `implementer`/`product-analyst`; reescribir conservando invariante | AC-B.7 | `rg -- '-fast' tests/` acotado; conteo de asserts de independencia no baja | — |
| T-B04 | Un salvage por paquete vía **override de invocación** (pin `repair-agent` sigue barato). Sin override medido → `HUMAN_DECISION_REQUIRED`. Segundo gate rojo → humano. Distinguir de ADR-0011 D2 | AC-B.4, AC-B.5, AC-D.1 | unittest de ciclo con doble rojo; frontmatter repair-agent = barato | Schema salvage UNVERIFIED |
| T-B05 | Contador: máximo +1 por paquete si el barato no fue green-on-first-attempt; salvage-rojo no suma. 2 paquetes → próximo con override más pesado (Cursor: no `@tier`). Feature nueva = BASE | AC-B.6 | unittest: cheap-rojo+salvage-rojo = 1; tres paquetes sintéticos | No usar un % |

Ownership B: `models.toml`, `ai/scripts/models_config.py`,
`tests/test_harness.py`, `feature-state.py` + lib, doctrina repair en
`orchestrator.md`.

## PKG-C — techo frontier + % green-on-first-attempt

| ID | Trabajo | AC | Validación local | Checkpoint |
|---|---|---|---|---|
| T-C01 | Contador `frontier_used/cap` (4/paquete, 16/feature) mutado por `feature-state.py`. `MODE_BUDGETS` byte-igual en scoped=8 | AC-C.1, AC-C.2, AC-X.2 | unittest: spawn barato no incrementa; salvage y reviewer pesado sí; P001 no | Architecture nombra el campo |
| T-C02 | Rechazo nombrado al exceder; no se toca `max_spawns`. Status/narración muestran usados/techo | AC-C.3 | el 5º frontier de un paquete muere | — |
| T-C03 | Precedencia: techo > salvage y techo > auto-promotion | AC-C.4 | unittest de cupo lleno + salvage/promote | — |
| T-C04 | `cost-report.py` Sección 2: `% green-on-first-attempt` + frontier. Universo AC-C.6. No sumar S1+S2 | AC-C.5, AC-C.6 | fixture salvage-verde **no** sube el numerador (mordida) | — |

Ownership C: `feature_state_lib/model.py`, `cli_lifecycle.py`,
`render_status.py`, `ai/scripts/cost-report.py`, tests.

## PKG-D — pins Cursor (enmienda 032)

| ID | Trabajo | AC | Validación local | Checkpoint |
|---|---|---|---|---|
| T-D01 | `generate.py` emite `model:` por rol. `code-rw` incl. `repair-agent` → pin barato; jueces → otra familia; `product-analyst`/`architect` pueden frontier. No pinnear repair pesado. Promoción/salvage = override de invocación (o humano) | AC-D.1, AC-D.2 | `./build.sh --output`; frontmatter repair-agent = barato | Medir slugs Cursor vivos; sin override → no fallback pesado |
| T-D02 | Independencia de pins o degradación ruidosa (evidencia no vacía) | AC-D.3 | test de familias; caso degradado exige `--evidence` | `family()` vs tabla Cursor: UNVERIFIED |
| T-D03 | Reescribir `validate_cursor_target` y `test_no_cursor_agent_pins_a_model` (no borrar). Readonly y roster 032 intactos | AC-D.4, AC-D.5 | mordida: pin ausente → die; inherit universal → test rojo | — |
| T-D04 | Doctrina Cursor: regla, `AGENTS.md`, `CURSOR_DELEGATION_OVERRIDE`. Sigue prohibido `--route-decide`. Sigue sin `hooks.json` | AC-D.6, AC-D.5 | `./build.sh --check`; grep de "No model is pinned" = 0 en target cursor | No reabrir 032 AC-07 |

Ownership D: `ai/scripts/generate.py`, `tests/test_harness.py`
(`CursorRuntimeTargetTests`), `Global/_canonical` doctrina Cursor,
`Global/cursor/AGENTS.md`.

## Transversal

| ID | Trabajo | AC | Validación local |
|---|---|---|---|
| T-X01 | Owned_paths de cada paquete **excluyen** tui/wizard/lanes/CI skip-ceiling de 033 | AC-X.1 | `check-owned-paths` |
| T-X02 | Cero código Engram / MCP Engram nuevo | AC-X.3 | grep en el diff del feature |
| T-X03 | Gate de paquete: `./build.sh --check`, `verify.sh`, `git diff --check`; aserciones netas no bajan | todos | gate-runner |

## Primera tarea a implementar

**T-A01** (doctrina unificada). Sin eso, A.2 se apoya en un texto que
todavía se contradice. El guarda (T-A02/T-A03) sigue en el mismo
paquete.

## Riesgo que pide checkpoint humano (no pregunta de producto)

Ninguno de producto: el slice está decidido. Architecture debe **medir**
(no preguntar de nuevo) el slug Cursor y el id barato-con-tools antes de
pinnear. Si el catálogo Cursor no ofrece dos familias, D degrada ruidoso
(DEC ya escrita), no se frena el feature.
