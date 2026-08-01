# 009-self-application · P1-knowledge-home

<!-- notas:auto -->
## Motivo

- objetivo: Que la capa de conocimiento exista en el arnes en los dos niveles que los prompts nombran, que verify.sh falle si un prompt canonico apunta a una ruta que no resuelve, y que lo que el escritor escribe sea lo que el lector lee, en ruta y en formato
- complejidad: medium
- riesgo: El nivel cross-proyecto tiene un solo consumidor (sync-project.sh:84) y un test vivo que lo verifica de punta a punta; …
- riesgo: AC-03 es un ratchet sobre prosa: cualquier prompt futuro que nombre una ruta que todavia no existe rompe el gate de tod…
- paths: `knowledge/*`, `docs/ai/knowledge/*`, `ai/scripts/verify.sh`, `ai/scripts/sync-project.sh`, `ai/scripts/save_memory.py`, `Global/_canonical/agents/memory-scribe.md`, `Global/_canonical/agents/local-gate-runner.md`, `Global/opencode/*`, `Global/claude-code/*`, `Global/codex/*`, `docs/specs/009-self-application/*`, `ai/state/features/009-self-application.json`, `ai/state/STATUS.md`, `ai/state/narrative-log.jsonl`, `ai/state/decisions-log.jsonl`, `docs/notas/*`

## Tareas

- [x] Guard en verify.sh que falla si un prompt canonico nombra una ruta literal que no resuelve, con waivers motivados (completed) · SET_AGENTS_GUEST_VERIFY=1 ./ai/scripts/verify.sh -> exit 1, CANONICAL_DANGLING_PATH count=27 across 10 canonical prompts, before any fix. Adversarial proof that the guard catches the defect it was written for; the full suite runs at the package gate., Waiver set is 3 entries, each with its reason inline: ai/state/verify.log, docs/adr/NNNN-slug.md, docs/project/architecture.md. 60 literal references checked, 16 templated forms skipped.
- [x] Test que parsea los prompts y prueba que lo que memory-scribe escribe es subconjunto de lo que los lectores leen (completed) · python3 -m unittest tests.test_harness.HarnessTests.{test_knowledge_write_and_read_targets_agree,test_save_memory_writes_the_format_the_scribe_declares,test_domain_knowledge_is_wired_through_the_canon} -> FAILED (failures=2, errors=1) on the unfixed tree. AC-04 fails on docs/ai/knowledge/_global/algorithms.md not existing; AC-12 errors because save_memory.py has no --section/--knowledge-dir yet; the pre-existing canon test fails on the strengthened disk assertion., The AC-04 test parses the prompts (brace expansion included) instead of assertIn on literals, and asserts subset rather than equality because every reader also declares the _global tier the scribe is forbidden to write.
- [x] Mudar el nivel cross-proyecto a docs/ai/knowledge/_global y sembrar el nivel de proyecto del arnes desde la plantilla (completed) · git mv of the five cross-project files preserves history; knowledge/ no longer exists; find docs/ai -type f lists exactly 10 files, five per tier., The project tier is a verbatim copy of PROYECTO/docs/ai/knowledge/ - the same seed bootstrap_project.py:132-138 gives every scaffolded project. No content was invented, which the contract excludes explicitly.
- [x] Repuntar sync-project.sh y memory-scribe.md al domicilio nuevo y reparar la referencia muerta de local-gate-runner (completed) · SET_AGENTS_GUEST_VERIFY=1 ./ai/scripts/verify.sh -> CANONICAL_PATHS_OK, GLOBAL_PORTABILITY_OK, VERIFY_PASS, exit 0. The same guard that listed 27 dangling sites now reports none., local-gate-runner.md no longer hardcodes one feature's state file; it uses ai/state/features/<feature_id>.json, the templated form every other canonical prompt already uses, which the guard skips by design.
- [x] Alinear el formato de escritura de save_memory.py --domain con el contrato de seccion y prefijo que declara memory-scribe (completed) · The three previously failing tests now pass, plus test_memory_fallback_does_not_block (the general --log path is untouched), test_sync_project_copies_generic_scripts_and_guards_active_state (distribution survived the move) and test_bootstrap_preserves_existing_content_and_is_idempotent. Ran 6 tests, OK., --section is required with --domain rather than defaulted: guessing which section an entry belongs to is the same silent-wrong-behaviour class this package exists to remove. An unknown section is UNKNOWN_SECTION and a missing domain file is MISSING_KNOWLEDGE_FILE; neither appends anywhere.

## Hallazgos

- F-01 [high] refuted —  · refutado por finding-verifier: The blind spot is real but the risk it names is covered, by measurement rather than assertion. AC-03 as approved states… [docs/specs/009-self-application/spec.md:92-94 states the skip rule; scratch rep…]
- F-03 [medium] closed — 
- F-05 [medium] refuted —  · refutado por finding-verifier: Describes a hypothetical future edit, not a defect in the delivered code. [ai/scripts/verify.sh:69-73 holds three non-empty reasons; ai/scripts/verify.sh:…]
- F-02 [high] closed — 
- F-04 [medium] closed — 
- F-06 [medium] refuted —  · refutado por finding-verifier: A pre-existing property of the ownership tool misattributed to this package, whose proposed repair is affirmatively har… [git log --oneline -- ai/scripts/check-owned-paths.py returned f32a033 from feat…]
- F-07 [medium] refuted —  · refutado por finding-verifier: Imposes an obligation neither the approved contract nor the repo convention contains. No P1 criterion requires an ADR, … [docs/specs/009-self-application/spec.md:83-110 contains no ADR requirement in a…]
- F-08 [low] refuted —  · refutado por finding-verifier: Pre-existing and out of the criterion scope. The hand-edit permission is in the pre-image of the diff, so the package d… [git diff bdf2a2b2 -- Global/_canonical/agents/memory-scribe.md shows the pre-im…]

## Recorrido

- review: repair_required (8 hallazgos)
- verificación: 0 refutados, 1 sostenidos
- verificación: 1 refutados, 1 sostenidos
- verificación: 4 refutados, 1 sostenidos
- repair: F-02, F-03, F-04 → 4 archivos
- delta review: pass
- testing: pass
- runtime QA: pass (waived)
- gate `verify`: pass
- gate `self-scaffold-sync`: pass
- gate `whitespace`: pass
- gate `ownership`: pass
- gate `canonical-paths`: pass

↩ [[features/009-self-application|009-self-application]]
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
