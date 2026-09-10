# Bitácora — 038-tokens-literacy-and-project-label

_Generado por `feature-state.py`. Cada entrada trae la lectura para el cliente y la justificación de ingeniería. No editar a mano._

Actualizado: 2026-09-10T17:52:49+00:00

[2026-08-24T15:41:36+00:00] PKG-1 · implementer · started · modelo cursor/grok-4.6 · effort high · spawns 1/8
Cliente: Se implementó la etiqueta libre del proyecto, se achicó la doctrina que se carga siempre, se pidió que el plan nombre la función madre, y el informe de costo ahora cuenta sesiones por encargo sin inventar tokens.
Ingeniería: PKG-1: sanitize_project_label + write_app_config; merge_note hub H1; always-on capped with ADR-0069 pointer; orchestrator/architect Code literacy; collect_engagements/render_engagements; tests in test_harness.py. Restored spawn visibility template after DoctrineTests fail.

[2026-08-24T15:41:51+00:00] PKG-1 · package-reviewer · started · modelo openai/gpt-5.6-sol · effort high · spawns 2/8
Cliente: Una revisión aparte mira si el paquete cumple lo pedido, sin tocar código.
Ingeniería: Read-only package-reviewer vs AC-01..05, ADR-0069, working-tree diff vs HEAD. Writer was cursor/grok-4.6; reviewer uses gpt-5.6-sol (different family). Record degradation if pin differs.

[2026-08-24T15:46:04+00:00] PKG-1 · finding-verifier · started · modelo openai/gpt-5.6-sol · effort high · spawns 3/8
Cliente: Antes de tocar tests, otra mirada intenta tirar abajo los tres huecos que marcó la revisión.
Ingeniería: finding-verifier vs PKG1-TEST-01/02/03. Medium finding PKG1-TEST-02 is the one that requires a verdict. Writer grok-4.6, reviewer gpt-5.6-sol; verifier should be a different pass (gpt-5.6-sol still, record if same family).

[2026-08-24T15:48:00+00:00] PKG-1 · repair-agent · started · spawns 4/8
Cliente: Se reforzaron las pruebas: la etiqueta vacía vuelve al nombre de carpeta, Cursor no puede perder las frases de doctrina, y el arquitecto tiene que pedir flujo y pseudocódigo.
Ingeniería: PKG1-TEST-01/02/03: extended test_project_label_renames_hub_title (empty --project-label), test_always_on_doctrine (phrases including cursor), test_orchestrator_code_literacy (architect flow+pseudocode+file:line and spawn visibility template). unittest 3 tests OK.

[2026-08-24T15:48:14+00:00] PKG-1 · delta-reviewer · started · modelo openai/gpt-5.6-sol · effort medium · spawns 5/8
Cliente: Una revisión corta mira sólo los tests que se reforzaron, no todo el paquete otra vez.
Ingeniería: DELTA_REVIEW: tests/test_harness.py only. Confirm empty project_label, cursor phrase pins, architect flow+pseudocode+file:line. Do not re-review 036/037. Writer grok-4.6; delta uses gpt-5.6-sol.

[2026-08-24T15:49:33+00:00] PKG-1 · orchestrator · done
Cliente: Quedó cerrado el encargo 038. Podés ponerle un nombre libre al proyecto (se ve en las notas), la doctrina que se carga siempre es más corta, el plan tiene que nombrar la función madre con archivo y línea, y el informe de costo cuenta sesiones por encargo sin inventar tokens. No hay commit todavía.
Ingeniería: 038 DONE. PKG-1 accepted after package-reviewer repair_required (3 test gaps), finding-verifier upheld all three (independence degraded: same GPT family as reviewer), repair in tests/test_harness.py, delta-reviewer pass. Gates: verify 1377 fail=0 skip=4 VERIFY_PASS, BUILD_CHECK_PASS, OWNERSHIP_PASS. runtime_surface=false waived. No commit.
Aprendimos: Compactar always-on no alcanza con un techo de líneas: hay que pinnear las frases en los mismos archivos del techo, porque Cursor no estaba en los tests viejos de doctrina. El reset vacío de project_label funciona y ahora tiene test.
Conviene ahora: Nada de implementación: el paquete está aceptado. El commit y el push quedan para cuando lo pidas.
Por qué ahora: Cerrar el estado ahora evita un digest mentiroso; commitear sin que lo pidas rompería la regla de git del repo.
