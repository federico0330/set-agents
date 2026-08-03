# 014-model-preference-policy · P1-model-preference-policy

<!-- notas:auto -->
## Motivo

- objetivo: Role-class-scoped model/provider preference: taxonomy+resolver, sibling config+CLI, one sort-key integration point in RoutingService.route(), RouteDecision observability, and the design ADR
- ruteo: Edits the live primary-dispatch sort key + new atomic config surface + CLI with fail-closed validation; architecture-cr… → implementer (None)
- complejidad: high
- riesgo: Sort-key element misplaced vs tier/independence boundary silently degrades reviewer-independence ordering: mitigated by…
- riesgo: Sibling-file writer reusing flat serializer or silent-parse-swallow corrupts config: mitigated by dedicated atomic writ…
- riesgo: Live-effect tests against synthetic missing-pair fixture would prove a post-015 falsehood: mitigated by fixture-that-wo…
- riesgo: SHARED FILES with 016-P2-hygiene (service.py, test_routing.py): implementation strictly sequenced after P2 lands
- paths: `ai/scripts/routing_core/service.py`, `ai/scripts/routing_core/domain.py`, `ai/scripts/set_agents_app.py`, `tests/test_routing.py`, `docs/adr/README.md`, `docs/adr/0018-model-preference-policy.md`

## Tareas

- [x] Role-class taxonomy + single resolver (AC-01, AC-05): partition test over 28 roles, tiers cross-check, 4-file doctrine-consistency test (completed) · python3 -m unittest tests.test_routing (229 tests, OK)
- [x] Sibling config file: schema, atomic TOML writer/loader, shared validators, fail-closed die(), round-trip isolation test (AC-02, AC-03) (completed) · python3 -m unittest tests.test_routing (229 tests, OK); py_compile clean; manual CLI smoke
- [x] CLI --model-preference-set/-role-override/-show wired to shared validators, MODEL_PREFERENCE_NOTE scoped to genuinely-inert classes, argparse rejections (AC-02) (completed) · python3 -m unittest tests.test_routing (229 tests, OK); py_compile clean; manual CLI smoke
- [x] RoutingService.route() sort-key insertion at position 3, exclusion loop and _effective_runtime untouched; point-5 tripwire test pinning 5-tuple (AC-04) (completed) · python3 -m unittest tests.test_routing (229 tests, OK); py_compile clean; manual CLI smoke
- [x] RouteDecision.bias_class/preference_configured + to_dict + cmd_route_decide envelope, non-collision test, 5-refusal-site population test (AC-08) (completed) · python3 -m unittest tests.test_routing (229 tests, OK); py_compile clean; manual CLI smoke
- [x] Regression suite: mechanism-correctness synthetic inventory + live-effect proofs for grunt 4 + build 2 tiered roles against real (claude-code,anthropic) inventory + AC-06 negatives (completed) · python3 -m unittest tests.test_routing (229 tests, OK); py_compile clean; manual CLI smoke
- [x] ADR (re-check next free number live, expect 0018) + README row (AC-09) (completed) · python3 -m unittest tests.test_routing (229 tests, OK); py_compile clean; manual CLI smoke

## Hallazgos

- SEC14-01 [low] closed — 
- RF14-01 [medium] closed — 
- RF14-02 [low] closed — 
- RF14-03 [medium] closed — 
- RF14-04 [low] closed — 
- RF14-05 [low] closed — 
- RF14-06 [low] closed — 
- RF14-07 [low] closed — 

## Recorrido

- review: repair_required (8 hallazgos)
- verificación: 0 refutados, 8 sostenidos
- repair: SEC14-01, RF14-01, RF14-02, RF14-03, RF14-04, RF14-05, RF14-06, RF14-07 → 5 archivos
- delta review: pass
- testing: pass
- runtime QA: pass
- gate `feature-014-gates`: pass

context pack: `docs/specs/014-model-preference-policy/context/P1-model-preference-policy.md`

↩ [[features/014-model-preference-policy|014-model-preference-policy]]
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
