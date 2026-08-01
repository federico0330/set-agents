# vault-doctor's basename fallback for an unregistered project still lets two never-registered repos collide

<!-- notas:auto -->
- fecha: 2026-07-29 · actor: orchestrator
- alcance: [[features/005-portable-harness|005-portable-harness]] · [[features/005-portable-harness/P2-vault-mandatory|P2-vault-mandatory]]

## Contexto

ADR-0012 DEC-6 says the registry, read 'before ANY action', means 'no entry -> unregistered, reported, never guessed at, never auto-repaired' -- and Consecuencias repeats 'it refuses any unregistered project, the registry is a hard prerequisite for any repair action, never inferred from directory shape'. The ACTUAL implementation (before AND after this repair round) never matched that: cmd_vault_doctor's per-project pass has always fallen back to a basename-derived vault-side path (vault/Proyectos/<name>) when the project isn't registered, and treats the FIRST successful --repair as the moment of registration (write_vault_registry_entry runs at the end of apply_vault_migration -> cmd_vault_link). This is P2's actual, load-bearing, tested design for migrating the four real, never-yet-registered ~/iey/ projects -- the feature's whole reason to exist -- so a literal 'refuse any unregistered project' would break the core use case, not just an edge case.

## Decisión

The security-auditor's SEC-004 finding (demonstrated with clientA REGISTERED, clientB unregistered) is fixed: _vault_side_for_doctor now refuses when a DIFFERENT registered repo already claims the same conventional vault-side path. The delta-reviewer's DR-003 found the narrower residual: when NEITHER repo is registered, the collision is still undetectable from the registry alone, since nothing distinguishes 'my own never-yet-migrated project' from 'someone else's never-yet-migrated project that happens to share a basename' without new state. Closing this fully needs new design (e.g. an explicit anchor/claim step at scaffold or first-link time, before any file ever touches the vault side) that is out of proportion for a same-day security-repair round on top of an already-large package. Left as-is for this package: the two-step --dry-run (shows the exact file list) then a fresh --repair marker (single-use, 15-minute TTL post SEC-008) remains the only safeguard for the never-registered-vs-never-registered case, and it requires the operator to actually read the dry-run output before confirming.

## Consecuencias

Real-world exposure on THIS harness's actual use (the operator's own known ~/iey/ projects, run by the operator themself) is low: basename collisions between the user's own projects are unlikely and the operator already reviews the dry-run. The exposure is real in a hypothetical multi-tenant or shared-vault scenario, which this harness does not currently target. A future package (candidate: 005-P3 or a dedicated vault-registry-hardening package) should design an explicit registration/anchor step so 'unregistered' truly means 'never touched', matching ADR-0012 DEC-6's stated intent, and add a test that reproduces the never-registered-vs-never-registered collision.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
