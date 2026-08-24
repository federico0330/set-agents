# 043 — mutate lock and verification ceilings

- **Estado:** Shipped (2026-08-24).
- **Modo:** scoped · closes 016 PR-06/PR-11 (partial).

## Alcance

- File lock around `mutate()` read-modify-write (PR-11).
- Separate `max_verification_waivers_per_package` budget (PR-06).
- `package_is_retired` + superseded feature closure path.

## Criterios

- **AC-01** Concurrent-sensitive ops documented; `--expect-revision` CAS when provided.
- **AC-02** Waiver counter uses `max_verification_waivers_per_package`.
- **AC-03** Tests for stale revision and retired-package DONE path.

## ## Supersedes

- none
