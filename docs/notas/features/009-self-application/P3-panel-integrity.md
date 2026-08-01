# 009-self-application · P3-panel-integrity

<!-- notas:auto -->
## Motivo

- objetivo: Cerrar los tres agujeros del ciclo de review que aparecieron al usarlo (panel sin miembros declarados, no-op silencioso, hallazgo tardio sin canal) y corregir la deriva de registro que aparecio al rastrearlos
- complejidad: medium
- riesgo: Cambiar la semantica de start-review-panel toca el camino que todo paquete usa para abrir su review; un error deja al a…
- riesgo: Comparte feature-state.py con P2; orden estricto
- paths: `ai/scripts/feature-state.py`, `PROYECTO/ai/scripts/feature-state.py`, `docs/adr/README.md`, `docs/specs/003-trusted-routing-pi-runtime/design.md`, `docs/specs/009-self-application/*`, `ai/state/features/009-self-application.json`, `ai/state/STATUS.md`, `ai/state/narrative-log.jsonl`, `ai/state/decisions-log.jsonl`, `docs/notas/*`

## Tareas

- [x] start-review-panel exige miembros declarados (completed) · test_start_review_panel_requires_declared_members: rojo antes (rc 0, roles ['package-reviewer'], ciclo gastado), verde despues
- [x] start-review-panel contra un panel-id existente es error, nunca no-op silencioso (completed) · 3 tests: duplicado, replay que no quema ciclo, y las 4 conductas de extend-review-panel. Los 7 mostrados en rojo antes
- [x] Canal sancionado para un hallazgo que llega despues de cerrado el panel, sin fase nueva (completed) · 5 tests nuevos mostrados en rojo antes; suite completa 232 OK (base 217), ninguno skipeado
- [x] Corregir la deriva de registro: fila de ADR-0009 ausente del indice y la asercion invertida en design.md:455 (completed) · 3 tests nuevos: 2 mostrados en rojo antes del arreglo (0009 sin fila; la asercion invertida presente), verdes despues

## Hallazgos

- F-01 [high] closed — correctness
- F-02 [high] closed — data-integrity
- F-03 [high] closed — false-claim
- F-04 [medium] refuted — dead-end-remedy · refutado por finding-verifier: La afirmacion portante del hallazgo -- que ninguna de las dos mitades del mensaje es un paso estructurado -- es falsa. … [ai/scripts/feature-state.py:471 (done_ready se niega a DONE con blockers) y :23…]
- F-05 [medium] closed — false-claim

## Recorrido

- review: repair_required (4 hallazgos)
- verificación: 1 refutados, 3 sostenidos
- verificación: 0 refutados, 1 sostenidos
- repair: F-01, F-02, F-03 → 4 archivos
- repair: F-05 → 3 archivos
- delta review: repair_required
- delta review: pass
- testing: pass
- runtime QA: pass (waived)
- gate `package verify`: pass
- gate `self-scaffold-sync`: pass
- gate `whitespace`: pass
- gate `ownership`: pass
- gate `adversarial-proof`: pass
- gate `package verify (post-repair)`: pass

context pack: `docs/specs/009-self-application/context/P3-panel-integrity.md`

↩ [[features/009-self-application|009-self-application]]
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
