# 003-trusted-routing-pi-runtime · P1R-trusted-routing

<!-- notas:auto -->
## Motivo

- objetivo: Trusted routing-v2: immutable catalog, trusted facts, private SQLite lifecycle, and simulated operator visibility
- ruteo: Hosted implementation required for security-critical trust boundaries, SQLite atomic lifecycle, crash/concurrency behav… → implementer (openai/gpt-5.6-terra)
- complejidad: high
- riesgo: untrusted request/catalog/auth/identity claims
- riesgo: SQLite concurrency, crash recovery, and duplicate dispatch
- riesgo: private filesystem, symlink, corruption, and legacy-state handling
- riesgo: privacy/redaction and incompatible CLI/config behavior
- paths: `ai/catalogs/routes.v1.toml`, `ai/scripts/routing_core/**`, `ai/scripts/routing.py`, `ai/scripts/models_config.py`, `ai/scripts/setup_models.py`, `models.toml`, `tests/test_routing.py`, `tests/test_harness.py`, `docs/specs/003-trusted-routing-pi-runtime/context/P1R-trusted-routing.md`, `docs/specs/003-trusted-routing-pi-runtime/evidence/P1R-*`

## Tareas

- [x] T-001 (completed) · trusted facts/catalog/static ID focused suite PASS
- [x] T-002 (completed) · run identity and independent review focused suite PASS
- [x] T-003 (completed) · SQLite lifecycle/concurrency/crash focused suite PASS
- [x] T-004 (completed) · CLI envelope/simulation/legacy/retention focused suite PASS
- [x] T-005 (completed) · focused+hermetic+setup_models+py_compile+verify reported PASS; independent rerun pending

## Hallazgos

- PKG-001 [critical] closed — data-integrity
- PKG-002 [high] closed — data-integrity
- PKG-003 [high] closed — integration
- PKG-004 [high] closed — correctness
- PKG-005 [high] closed — data-integrity
- PKG-006 [high] closed — data-integrity
- PKG-007 [high] closed — correctness
- PKG-008 [high] closed — scalability
- PKG-009 [high] closed — testing
- PKG-010 [medium] closed — integration
- SEC-001 [high] closed — security
- SEC-002 [high] closed — security
- SEC-003 [high] closed — security
- SEC-004 [high] closed — security
- SEC-005 [high] closed — security
- SEC-006 [high] closed — security
- SEC-007 [medium] closed — security
- SEC-008 [medium] closed — security
- DR-001 [critical] closed — security
- DR-002 [high] closed — security
- DR-003 [high] closed — integration
- DR-004 [high] closed — security
- DR-005 [high] closed — stability
- DR-006 [high] closed — security
- DR-007 [high] closed — correctness
- DR-008 [high] closed — scalability
- DR-009 [high] closed — testing
- DR-010 [medium] closed — integration
- FD-001 [critical] closed — security
- FD-002 [high] closed — security
- FD-003 [high] closed — integration
- FD-004 [high] closed — security
- FD-005 [high] closed — stability
- FD-006 [high] closed — security
- FD-007 [high] closed — correctness
- FD-008 [high] closed — scalability
- FD-009 [high] closed — testing
- FD-010 [medium] closed — integration

## Recorrido

- review: repair_required (18 hallazgos)
- review: repair_required (10 hallazgos)
- review: repair_required (10 hallazgos)
- repair: PKG-001, PKG-002, PKG-003, PKG-004, PKG-005, PKG-006, PKG-007, PKG-008, PKG-009, PKG-010, SEC-001, SEC-002, SEC-003, SEC-004, SEC-005, SEC-006, SEC-007, SEC-008 → 9 archivos
- repair: DR-001, DR-002, DR-003, DR-004, DR-005, DR-006, DR-007, DR-008, DR-009, DR-010 → 8 archivos
- repair: FD-001, FD-002, FD-003, FD-004, FD-005, FD-006, FD-007, FD-008, FD-009, FD-010 → 9 archivos
- delta review: blocked
- delta review: blocked
- delta review: pass
- testing: pass
- runtime QA: pass
- gate `compile-and-focused-tests`: pass
- gate `ownership-exact-tree`: pass
- gate `git-diff-check`: pass
- gate `full-verify-and-gatespec`: pass
- gate `post-repair-full-verification`: pass
- gate `r2-final-verification`: pass
- gate `r3-final-verification`: pass

context pack: `docs/specs/003-trusted-routing-pi-runtime/context/P1R-trusted-routing.md`

↩ [[features/003-trusted-routing-pi-runtime|003-trusted-routing-pi-runtime]]
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
