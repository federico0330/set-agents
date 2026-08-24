# 039 — Honest ledger and index closures

- **Estado:** Shipped (2026-08-24).
- **Modo:** scoped · señal `public-contract`.

## Alcance

Close stale ledger/index drift: 002 superseded by 003, 011 Shipped with AC-06 live blocked,
032/033 Shipped, index rows aligned, digest stops listing dead blockers.

## Criterios

- **AC-01** 002 `DONE`; index remains `Superseded by 003`.
- **AC-02** 011 `DONE`; index `Shipped (AC-06 live blocked)`; hub notes Copilot ≠ Anthropic/Pi.
- **AC-03** 032/033 `DONE`; index `Shipped`.
- **AC-04** `test_spec_index_matches_disk_and_project_notes` green.

## ## Supersedes

- none
