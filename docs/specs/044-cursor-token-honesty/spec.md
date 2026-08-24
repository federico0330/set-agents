# 044 — Cursor token honesty

- **Estado:** Shipped (2026-08-24).
- **Modo:** scoped · additive to 023.

## Alcance

Section 1 of `cost-report.py` prints `Cursor: not measured` when no CLI-native token store exists.
Never invent zero token rows. Spawn JSON unchanged (038 AC-04).

## Criterios

- **AC-01** Footer line present; no Cursor rows with zero tokens invented.
- **AC-02** Sections 1 and 2 still never summed.

## ## Supersedes

- none
