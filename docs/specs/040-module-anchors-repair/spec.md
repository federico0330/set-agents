# 040 — Module anchor repair

- **Estado:** Shipped (2026-08-24).
- **Modo:** scoped · quick-fix signal.

## Alcance

Update eight stale `file:line` anchors in `docs/modules/`; `check-anchors` passes; not a gate.

## Criterios

- **AC-01** `feature-state.py check-anchors` returns `ok: true`.
- **AC-02** `log-quickfix` records the repair.

## ## Supersedes

- none
