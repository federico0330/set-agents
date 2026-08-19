# Context pack — PKG-B escritor-barato-y-salvage

Spec hash `539a4ff6…d9721`. **AC-B.1–AC-B.7**. Después de PKG-A (`orchestrator.md` y `feature-state.py` en común). HOW: ADR-0060 + ADR-0062. Enmienda razón ADR-0044.

**Objetivo.** Default de todo rol `code-rw` = lo más barato/gratis del catálogo vivo que cumpla tools (`read`+`shell`+`write`). Test `-fast` se **reescribe**, no se borra. Un salvage pesado por paquete (override, pin `repair-agent` sigue barato); segundo gate rojo = `HUMAN_DECISION_REQUIRED`. Auto-promotion: +1 consecutivo máx. por paquete; 2 → próximo rung más pesado. Feature nueva = `base`, **nunca** `fast`/`@fast`.

## Paths

- `models.toml:109-113` — `[areas.implement].opencode` hoy `openai/gpt-5.6-fast`. Celda BASE barata. **No** meter `opencode/*` en `tiers.*` (no proyecta, `generate.py:667-677`; el build muere).
- `models.toml:237-238`, `:271-273` — overrides spark de `frontend-engineer` / `refactor-specialist`: **borrar** para heredar el barato de área.
- `models.toml:240-247` — tiers luna/sol/terra se quedan (escalera `@tier` OpenCode). No son el default del paquete 1.
- `ai/scripts/routing_core/catalog.py:196-207` — `billing_rank` **read-only**. No se mueve.
- `tests/test_harness.py:733-766` — `test_repo_go_zen_routes_hot_path_to_fast_variants_and_keeps_reviewers_apart`: sacar `product-analyst` del loop `-fast`; `implementer` + `debugger` o `frontend-engineer` asertan barato/free (`billing_rank==0`); `:750-766` independencia **conservada**. Comentario cita 034/0060.
- `ai/scripts/feature-state.py:399+` — `record-spawn --salvage` una vez; segundo → `SALVAGE_ALREADY_USED`.
- `ai/scripts/feature_state_lib/model.py` — `package.salvage`, `writer_rung`, `cheap_strike_recorded`; feature `writer_promotion.{cheap_consecutive_failures,next_rung}` (`next_rung` default `"base"`, nunca `"fast"`).
- `ai/scripts/feature_state_lib/cli_repair.py:22-52` — `record-gate`: +1 consecutivo **una vez** por paquete si el barato no fue green-on-first; si `salvage` ya existe, no otra vez; green-on-first (verde **y** `salvage is None`) resetea a 0.
- `Global/_canonical/agents/orchestrator.md:523-524` — un repair consolidado **más**: esa instancia, si es salvage, va en modelo pesado y no se repite. Cursor: override o `HUMAN_DECISION_REQUIRED`; no pin pesado.

**V-B01 (antes de pinnear):** ¿el `-free` candidato (`models.toml:250` `opencode/deepseek-v4-flash-free` u otro vivo) edita + corre validación local? Si no hay ninguno con tools y rank 0 → `HUMAN_DECISION_REQUIRED` con inventario, no inventar id.

Barato = tools floor + `billing_rank==0`; entre varios 0 preferir sufijo `-free`. Cero list prices.

## ADRs / invariantes

- ADR-0060 — default `code-rw` barato/free; `product-analyst` es juicio (ADR-0018, `roles.tsv:4`).
- ADR-0062 — un salvage; convive con techo de líneas ADR-0023; **no** es D2 de ADR-0011 (exhaustion ≠ gate rojo).
- ADR-0035 — `billing_rank` se queda. ADR-0011 — independencia se conserva en el test.
- Techo frontier (AC-C / 0061) **aún no existe**; no adelantar el contador. Precedencia techo>salvage la implementa PKG-C.

## Validación local

```
python3 -m unittest tests.test_harness.HarnessTests.test_repo_go_zen_routes_hot_path_to_fast_variants_and_keeps_reviewers_apart
rg -- '-fast' tests/   # otros anclajes implementer/product-analyst: reescribir, no borrar
./build.sh --check     # coherencia de variantes: no poner -free en tiers.*
git diff --check
```

Mordida B.2: romper el pin barato → ROJO; restaurar (`cp`, no `git checkout`) → VERDE. Unittest ciclo: cheap-rojo+salvage-rojo = 1 consecutivo, no 2; segundo salvage rechazado.

## Reviewers / runtime / tests

- `required_reviewers`: `["package-reviewer", "security-auditor"]` — ruteo / cuota / default de gasto.
- `runtime_surface`: **false**. test owner: **implementer**. `strict_tdd`: **false**.
- `selected_role`/`model`: implementer / inherit.

## Fuera de alcance

`--risk-signal` (A) · techo 4/16 y `cost-report` S2 (C) · pins Cursor / `generate.py` (D) · `billing_rank` · `MODE_BUDGETS` · 033 · Engram · aflojar tests · agentes `@tier` en Cursor.

## Mordida

Pin barato roto → test hot-path ROJO. Doble `--salvage` → `SALVAGE_ALREADY_USED`. Feature nueva no despacha `implementer@fast`.
