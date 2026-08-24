# 042 — --reader / --trace aliases

- **Estado:** Shipped (2026-08-24).
- **Modo:** scoped · señal `public-contract`.
- **ADRs:** 0070 (nuevo); partial supersedes 037 no-rename clause.

## Alcance

`record-spawn` and `log-narrative` accept `--reader`/`--trace` as aliases; JSON keys stay `client`/`tech`.
`--client`/`--tech` remain for one release.

## Criterios

- **AC-01** `--reader`/`--trace` write `client`/`tech` in JSONL/state.
- **AC-02** Conflicting alias pairs raise `StateError`.
- **AC-03** Vault labels `Cliente:`/`Ingeniería:` unchanged (ADR-0068).

## ## Supersedes

- 037 spec clause deferring rename of `--client`/`--tech`
