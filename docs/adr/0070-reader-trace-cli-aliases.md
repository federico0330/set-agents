# ADR-0070: --reader / --trace CLI aliases (042)

## Status

Accepted (2026-08-24)

## Context

037 deliberately kept `--client`/`--tech` flag names. Operators asked for plainer names
(`--reader` / `--trace`) while vault labels `Cliente:`/`Ingeniería:` stay per ADR-0068.

## Decision

- `record-spawn` and `log-narrative` accept `--reader` and `--trace` as aliases.
- Persisted JSON keys remain `client` and `tech` for one release; `--client`/`--tech` stay valid.
- Conflicting pairs (`--client` + `--reader` with different text) raise `StateError`.

## Consequences

- 037 spec gains a `## Supersedes` note on the no-rename clause.
- Tests lock alias → JSON key mapping.
