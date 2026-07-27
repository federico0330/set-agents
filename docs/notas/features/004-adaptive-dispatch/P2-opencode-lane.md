# 004-adaptive-dispatch · P2-opencode-lane

<!-- notas:auto -->
## Motivo

- objetivo: Tiered OpenCode agent variants <role>@<tier> consumed by the orchestrator per --route-decide; build-time variant↔catalog coherence gate; degraded-mode doctrine
- ruteo: Build-pipeline + orchestrator-doctrine work touching permission surfaces; in-session Claude implementer for speed per u… → implementer (claude-in-session)
- complejidad: high
- paths: `models.toml`, `ai/scripts/models_config.py`, `ai/scripts/generate.py`, `ai/scripts/install.py`, `Global/_canonical/agents/orchestrator.md`, `ai/scripts/coord_policy.py`, `tests/test_harness.py`, `docs/specs/004-adaptive-dispatch/context/P2-opencode-lane.md`, `docs/specs/004-adaptive-dispatch/evidence/P2-*`, `Global/opencode/agents/**`, `Global/claude-code/agents/orchestrator.md`, `Global/codex/**`

## Tareas

- [x] T-201 (completed) · Per-role tier tables [roles.<role>.tiers.<tier>] for 5 roles; MODEL_TIERS/TIER_FIELD active; load_role_tiers lane+subscription validated; resolve_role ignores tiers; emit() round-trips tiers; base agents unchanged
- [x] T-202 (completed) · generate.py emits additive OpenCode-only <role>@<tier>.md (identical body/perms/steps, model per tier); orchestrator task-allowlist extended; validate() per-harness set equality exact; pure-offline check_variant_catalog_coherence in validate(); install prune covers variants unchanged; build --check CHECK_PASS
- [x] T-203 (completed) · orchestrator.md decide->spawn doctrine (match by decided model; mismatch/unavailable -> degraded base; worker-death; run_id in narration; reviewer review_of_run_id from state/recent-writers); coord_policy.py SAFE + oc_permissions coord-ro gain --route-decide; routing CLI documented mutating-capable
- [x] T-204 (completed) · test_harness.py +5: variant emission, prune-of-removed-variant, hermetic decide->dispatched->terminal lifecycle, worker-death closure, negative coherence x2; 150/150 OK; verify.sh VERIFY_PASS

## Hallazgos

- PKG-N01 [low] closed — correctness
- PKG-N02 [low] closed — correctness
- SEC-A01 [medium] closed — security
- SEC-A02 [low] accepted — security

## Recorrido

- review: repair_required (4 hallazgos)
- repair: SEC-A01, PKG-N01, PKG-N02 → 7 archivos
- delta review: pass
- testing: pass
- runtime QA: pass
- gate `p2-package-gates`: pass
- gate `r1-post-repair-verification`: pass

context pack: `docs/specs/004-adaptive-dispatch/context/P2-opencode-lane.md`

↩ [[features/004-adaptive-dispatch|004-adaptive-dispatch]]
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
