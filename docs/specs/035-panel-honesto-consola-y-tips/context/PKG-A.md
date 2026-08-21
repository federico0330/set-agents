# Context pack — PKG-A · Panel honesto (CLI de estado)

Spec: `docs/specs/035-panel-honesto-consola-y-tips/spec.md`
(hash `296e051fccfd0cea2f222cc7061987f6b66507d9ed2b10539d7e58ea3169331c`).
Aceptación: `acceptance.md` § PKG-A. Tareas: `tasks.md` T-001..T-010.
**ACs:** AC-A.1 … AC-A.9. Primer corte entregable (`spec.md:447-450`).

**Objetivo.** Un paquete cuyo panel resuelto es `FULL_REVIEW_PANEL` no puede cerrar su
review con un `record-review` suelto (rechazo `REVIEW_PANEL_REQUIRED`, alcanza a los **tres**
verdicts — DEC-DOOR), y `record-review pass` deja de saltar por encima de un finding
bloqueante abierto (`BLOCKING_FINDING_OPEN`). `small`+`low` **no cambia**. El cambio es
contrato público: viaja con ADR `Accepted` + doctrina enmendada en el mismo paquete.

## Paths (qué tocar y por qué)

- `ai/scripts/feature_state_lib/cli_review.py:21-63` — `cmd_record_review`: hoy no lee
  `required_reviewers` ni `has_open_findings`; `:46` incrementa `deep_review_cycles` en
  cada llamada (**un rechazo no puede cobrar un ciclo**, AC-A.1); `:54-56` pone
  `PACKAGE_TESTING` en `pass`. Aquí vive el defecto.
- `ai/scripts/feature_state_lib/cli_review.py:158-160` — `finalize-review-panel` ya usa
  `has_open_findings(package, {"critical","high","medium"})`. **Mismo predicado y mismas
  severidades** para AC-A.4; no se inventa uno nuevo.
- `ai/scripts/feature_state_lib/cli_review.py:66-89` — envelope del rechazo (`StateError` →
  `{"ok": false, "error": ...}`, exit 2). Es la forma que todo test parsea.
- `ai/scripts/feature_state_lib/model.py:565-575` — `required_reviewers_for`: `small`+`low`
  → `SINGLE_REVIEW_PANEL` (`:95`); cualquier eje `medium`/`high` → `FULL_REVIEW_PANEL`
  (`:96`); `complexity` `None` → fail-safe `medium` (`:571`), **se conserva**.
  `resolve_package_risk` (`:548-562`) y `persist_review_requirements` (`:578-583`).
- `ai/scripts/feature_state_lib/model.py:819-822` — `package_accept_ready` pide "un review
  con verdict pass", nunca quién revisó. Candidato al predicado compartido (HOW libre).
- `ai/scripts/feature-state.py:569-587` — el enforcement completo, hoy solo en
  `start-review-panel` (rechaza escritores `:570-575`, rol faltante `:576-583`, panel
  inflado en `small`+`low` `:584-587`). La asimetría a corregir.
- `ai/scripts/feature_state_lib/transitions.py:96-109` — la rama advisora y el
  comentario-deuda (`:106-107`). **No se borra y no se declara inalcanzable** (T-007).
- `ai/scripts/feature_state_lib/cli_lifecycle.py:334`, `:377` — dónde se persiste
  `required_reviewers`; explica por qué un fixture hecho con `create-package` engaña.
- `tests/test_harness.py` — golden suite (15 025 líneas). **Corre el CLI del template**:
  `FEATURE_STATE = ROOT / "PROYECTO/ai/scripts/feature-state.py"` (`:32`). Un cambio solo
  en `ai/scripts/` **no lo ve ningún test**.
- `PROYECTO/ai/scripts/feature_state_lib/**` + `PROYECTO/ai/scripts/feature-state.py` —
  la copia espejo, gateada por `build.sh:67-82` (`SELF_SCAFFOLD_DRIFT`, `cmp -s` archivo a
  archivo, y `checked >= 23`).
- `Global/_canonical/agents/orchestrator.md:102-108` — la doctrina que respalda el defecto:
  `:103` lista `record-review` en el ciclo normal, `:105-108` presenta el panel como lo que
  se usa "when multiple specialist reviewers are useful". **Superficie de PKG-A** (AC-A.9).
- `docs/adr/<nuevo>.md` — ADR de enmienda de contrato. Máximo hoy: `0064` (`ls docs/adr/`),
  así que el próximo libre es **0065**; si `architect` decide dos documentos, `0065`+`0066`.
- **Propagación (re-medida, más precisa que el spec):** `generate.py:663-668` es el
  `copytree` de `feature_state_lib` a `Global/{claude-code,opencode,codex,cursor}/hooks/`.
  `orchestrator.md` se **renderiza** desde el canónico en el loop `generate.py:508-583` →
  `Global/{opencode,claude-code,pi,cursor}/agents/orchestrator.md` **y**
  `Global/codex/agents/orchestrator.toml` (verificado con `ls`): el `rg` de AC-A.9 tiene que
  incluir el `.toml`. `generate.py` **no se modifica** (no-goal 13).

## ADRs / invariantes que constriñen

- **DEC-DOOR** (`spec.md:152`): el verbo se **rechaza**, no se endurece. Razón medida:
  cada llamada gasta un `deep_review_cycles` y el techo es 2 (`model.py:123-127`).
- **DEC-LEGACY** (`spec.md:154`): la negativa dispara en el verbo que muta. Ni un paquete
  `accepted`/`superseded` ni una feature `DONE` se re-juzgan (AC-A.6).
- **DEC-SKIP-DELTA-OUT** (no-goal 12): `record-repair --skip-delta`
  (`cli_repair.py:246-253`, `:274-282`) **no se toca**. Por eso la rama advisora sigue
  siendo alcanzable y su comentario nuevo tiene que nombrar **esa** puerta, citando
  `docs/notas/decisiones/2026-08-20 035-skip-delta-fuera-del-slice.md`.
- **Invariante 6 / no-goal 10:** ningún test se afloja, se saltea ni se borra, y **nunca**
  se baja un `--complexity medium` a `small` para esquivar el guarda.
- `MODE_BUDGETS` (`model.py:123-128`) intacto; `NON_ACCEPTING_ACTORS` (`:90`),
  `REFUTING_ACTORS` (`:109`) y `RISK_SIGNAL_REQUIRED` (ADR-0064) no cambian.
- `feature-state.py` sigue siendo el único escritor de `ai/state/features/*.json`.

## Validación local

```
python3 -m unittest tests.test_harness
python3 -m unittest tests.test_honest_predicate tests.test_narracion_contrato
./build.sh --check && ./ai/scripts/verify.sh
rg -n "record-review is outside this package" ai/scripts PROYECTO/ai/scripts Global
rg -n "when multiple specialist reviewers are useful" Global/
```

`pytest` no existe en este repo. **strict-TDD (ADR-0022) está ON**: cada guarda se escribe
test-first (RED con el árbol limpio → GREEN con el guarda), y las **dos** corridas van a la
evidencia. Restaurar con `cp` del módulo, nunca `git checkout`/`restore`/`stash`.

## Reviewers / runtime / tests

- `required_reviewers`: **`["package-reviewer", "security-auditor"]`**. No es una elección
  de gusto: `complexity=high` + `risk=high` → `FULL_REVIEW_PANEL` (`model.py:565-575`).
  `high` porque el paquete **enmienda un contrato público** (invocaciones que hoy funcionan
  dejan de funcionar) y toca el camino de autorización del review de todo paquete en vuelo.
  Declararlo `small`+`low` sería mentir sobre la superficie. Efecto colateral querido: el
  cap de diff de reparación queda en 200 líneas (`cli_repair.py:214-221`), que es lo que las
  7 reescrituras del golden suite pueden llegar a necesitar.
- `runtime_surface`: **false** — waiver declarado. No hay UI ni superficie de red; el
  observable es el exit code de un CLI, y el golden suite corre **el binario real del
  template** (`tests/test_harness.py:32`), o sea que la prueba de runtime la produce
  `gate-runner`, no un `runtime-verifier`. Además el techo de 8 despachos no deja lugar
  (AC-A.8: chocarlo es `HUMAN_DECISION_REQUIRED`, no un techo más grande).
- test owner: **implementer** (tests focalizados + reescritura de las mordidas). No hay
  `test-writer` en este slice. La evidencia del paquete (incluidas las corridas ROJO/VERDE)
  va a `docs/specs/035-panel-honesto-consola-y-tips/evidence/` — convención medida en 034.
- `selected_role` / `selected_model`: `implementer` / `composer-2.5`. Pin de host Cursor
  (034/ADR-0063), **no** una lane de routing: `--route-decide` sigue prohibido.

## Fuera de alcance (aunque tiente) — `read_only_paths` declarados

`ai/scripts/generate.py` (no-goal 13) · `build.sh` · `ai/scripts/set_agents_app.py` (PKG-B)
· `TIPS-USO.md` y `docs/COMO-FUNCIONA.md` (PKG-C). Tampoco: `record-repair --skip-delta` ·
partir `tests/test_harness.py` · subir `MODE_BUDGETS` · editar a mano las copias de
`Global/*` (se regeneran) · un tercer camino de review (verbo/fase/panel nuevo) · reabrir
032/033/034 como producto · migrar a mano los tres paquetes vivos de `ai/state/features/`.

## Mordida (7 sitios de 20 invocaciones reales; enumerados en `acceptance.md`)

Membresía (AC-A.1, los cinco `--complexity medium`): `tests/test_harness.py:8580`, `:10170`,
`:12399`, `:12451`, `:13006` → se reescriben **al camino del panel**
(`start-review-panel` + `record-subreview` ×2 + `finalize-review-panel`), conservando la
aserción que cada test protege.
Finding abierto (AC-A.4): `:9032`
(`test_next_does_not_blame_a_late_review_that_never_happened`, `:9024-9039`) **se parte en
dos** escenarios coherentes (AC-A.5), y `:11048`
(`test_accept_package_rejects_open_findings_and_bad_actors`) arma su setup por una vía legal
conservando sus **dos** aserciones. Sin estos siete vistos ROJOS antes y VERDES después,
PKG-A no se implementó: se documentó. Si aparece un octavo sitio (T-006), se **registra**
antes de reescribirlo; si el barrido se vuelve un paquete propio, se para y se dice.
