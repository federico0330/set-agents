# Context pack — PKG-C techo-frontier-y-metrica

Spec hash `539a4ff6…d9721`. **AC-C.1–AC-C.6**. Después de PKG-B (necesita “barato” y `package.salvage`). HOW: ADR-0061. Enmienda ADR-0039 (`counter.scope` gana `frontier`).

**Objetivo.** Cupo de modelos pesados distinto de `max_spawns`: 4/paquete, 16/feature, visible, chocable. `% green-on-first-attempt` del implementer-barato en `cost-report.py` Sección 2. Salvage-verde **no** es first-attempt.

## Paths

- `ai/scripts/feature_state_lib/model.py:123-128` — `MODE_BUDGETS.scoped.max_spawns_per_package == 8` **byte-igual**. Constantes **fuera** de ese dict: `FRONTIER_CAP_PER_PACKAGE = 4`, `FRONTIER_CAP_PER_FEATURE = 16`. Caps no se duplican en el JSON.
- `model.py` `base_state` / `compact_package` — aditivo `.get()`: feature `frontier_used`; package `frontier_used` (salvage / `writer_rung` / `cheap_strike_recorded` ya los puso B).
- `ai/scripts/feature-state.py:399+` `cmd_record_spawn` — clasifica frontier cuando **todas**: `--model` presente, modelo ≠ default barato de B, rol ≠ `local-gate-runner`, spawn ≠ P001. Jueces pesados **sí**. Salvage **sí**. `--model` ausente: no incrementa (aditivo). Chequeo de techo **antes** de aceptar salvage o spawn no-barato. Error: `FRONTIER_CAP_EXHAUSTED`.
- `ai/scripts/feature_state_lib/cli_lifecycle.py:444-460` `block_with_reason` — tercer shape: `{"scope": "frontier", "key": "used", "grain": "package"|"feature"}`. `reopen` resetea exactamente ese contador. No meter `frontier_used` dentro de `attempts`.
- `ai/scripts/feature_state_lib/render_status.py` — mostrar `frontier_used/cap` (lee la constante).
- `ai/scripts/cost-report.py:14-24`, `:417-448` — S2: `% green-on-first-attempt` por feature + total del filtro, más `frontier_used/cap`. **No** sumar S1+S2 (`:26-30` intacto). El % se **deriva** (no se persiste): numerador = gate verde **y** `salvage is None`; denominador = implementer-barato que llegó a gate; paquete sin ese spawn o sin gate → **fuera** (no 0%, no 100%).

## ADRs / invariantes

- ADR-0061 — techo ≠ `attempts.spawns`. DEC-PRECEDENCE-CEILING: techo gana a salvage (B) y a auto-promotion (B).
- ADR-0039 — vocabulario de `counter.scope` cerrado; ahora tres valores.
- 033 AC-6.2 — P001 / `local-gate-runner` no cuentan frontier.
- 023 AC-04 — S1 y S2 no se suman.

## Validación local

```
python3 -m unittest tests.test_harness   # tests nuevos AC-C + igualdad MODE_BUDGETS scoped=8
python3 ai/scripts/cost-report.py --project /home/federico/SET-AGENTES --since 2026-08-10
git diff --check
```

Unittest: spawn barato no incrementa; salvage y reviewer pesado sí; P001 no; 5º frontier del paquete muere; cupo lleno + salvage/promote → `HUMAN_DECISION_REQUIRED`.

## Reviewers / runtime / tests

- `required_reviewers`: `["package-reviewer", "security-auditor"]` — cupo de cuota.
- `runtime_surface`: **false**. test owner: **implementer**. `strict_tdd`: **false**.
- `selected_role`/`model`: implementer / inherit.

## Fuera de alcance

Subir `max_spawns` · pins Cursor · `billing_rank` · 033 · Engram · campo precomputado del % en el JSON · JSON editado a mano.

## Mordida

Marcar un gate verde **después** del salvage como first-attempt → test ROJO. 5º frontier de un paquete → `FRONTIER_CAP_EXHAUSTED`.
