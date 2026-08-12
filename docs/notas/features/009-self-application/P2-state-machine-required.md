# 009-self-application · P2-state-machine-required

<!-- notas:auto -->
## Motivo

- objetivo: Que entregar una feature por fuera de la maquina de estados sea un error y no silencio, en las dos direcciones: sin registro y con un registro que declara una aprobacion que nunca ocurrio
- complejidad: medium
- riesgo: AC-05 sale del paquete con el mecanismo sin decidir; las tres opciones tienen semanticas incompatibles y una de ellas (…
- riesgo: AC-13 toca cmd_init, que es la puerta de entrada de toda feature: un guard mal calibrado deja al arnes sin poder abrir …
- riesgo: Comparte feature-state.py con P3 y verify.sh con P1; el contrato exige orden estricto porque no hay deteccion de colisi…
- paths: `ai/scripts/feature-state.py`, `PROYECTO/ai/scripts/feature-state.py`, `docs/specs/009-self-application/*`, `ai/state/features/009-self-application.json`, `ai/state/STATUS.md`, `ai/state/narrative-log.jsonl`, `ai/state/decisions-log.jsonl`, `docs/notas/*`

## Tareas

- [x] Decidir y escribir el punto de aplicacion del gate, con su consecuencia asumida (completed) · Decision registrada con log-decision, slug el-gate-de-estado-obligatorio-vive-en-verify-sh: el gate vive solo en verify.sh, con la consecuencia asumida por escrito (no bloquea un commit local). El dato que decide contra pre-commit es que .git/hooks/ no se versiona, asi que no existe en un clon nuevo ni en el runner del CI; el post-commit existente termina en '|| true' (build.sh:37-49) y no puede fallar nada., Prueba adversarial del gate ANTES de cualquier waiver: python3 ai/scripts/check-feature-state.py . -> exit 1, FEATURE_STATE_MISSING id=006-execution-graph evidence=02ed998, con la linea de remedio completa. No dispara sobre 001-harness-evolution, que no produce ningun commit 'Feature 001 P<n>': AC-06 medido y no afirmado., Prueba adversarial de AC-13 sobre el arbol de hoy: init 010-fake docs/specs/010-fake/spec.md deadbeef -> ok, y el estado queda afirmando hash 'deadbeef' con from=USER_APPROVAL, contra un archivo cuyo sha256 real es 6d8d335b. Ese es el defecto.
- [x] Gate que exige ai/state/features/<id>.json cuando el trabajo llego a entrega, sin disparar en el ciclo previo a la aprobacion, nombrando el comando remedio (completed) · ai/scripts/check-feature-state.py con un solo waiver motivado (006-execution-graph, citando AC-07 en spec.md:129-132 y el slug feature-006-delivered-outside-state-machine). Sin el waiver salia 1 sobre el defecto vivo; con el, FEATURE_STATE_OK. Enganchado en verify.sh despues de check-canonical-paths.py: SET_AGENTS_GUEST_VERIFY=1 ./ai/scripts/verify.sh -> GLOBAL_PORTABILITY_OK, CANONICAL_PATHS_OK, FEATURE_STATE_OK, VERIFY_PASS, exit 0., test_feature_state_gate_fails_when_a_delivered_feature_has_no_state_file maneja el camino de falla contra un repo de prueba: entrega sin estado -> exit 1 + FEATURE_STATE_MISSING + el remedio con el sha256 real del spec; feature solo redactada (commit sin token P<n>) -> FEATURE_STATE_OK, que es AC-06 medido y no afirmado; sin historia de git -> FEATURE_STATE_UNCHECKED por stderr y exit 0, ruidoso y fijado por el test en vez de degradar a no-op silencioso. El guest-verify ademas fija FEATURE_STATE_OK por nombre, asi que borrar el guard ya no deja la suite verde.
- [x] init deja de poder afirmar una aprobacion que nadie verifico (completed) · cmd_init verifica sha256(spec_path) contra el hash recibido y se niega con SPEC_HASH_MISMATCH o SPEC_NOT_FOUND sin escribir el archivo de estado; --approved-by pasa a ser requerido, con el precedente de reopen --authorized-by que ya lo exige. El evento de historia lleva spec_hash_verified y approved_by: la evidencia, no solo la afirmacion. Mismo cambio en PROYECTO/ai/scripts/feature-state.py, ./build.sh --check -> SELF_SCAFFOLD_SYNC_OK files=2., test_init_refuses_to_attest_a_spec_it_did_not_verify fallaba sobre el arbol previo y ahora pasa: hash equivocado, spec ausente y falta de atribucion son los tres rechazos, y en los tres el archivo de estado no existe. Las 19 llamadas a init de la suite migraron al helper init_state, que escribe un spec real y lo hashea, asi que ningun test puede volver a pasar un nombre y una ficcion. test_sync_notes_renders_hub_feature_and_package_notes se reapunto al digest real en vez de la cadena 'hash-abc': misma asercion, misma fuerza., Superficie de prompts alineada con el CLI: Global/_canonical/commands/feature-batch.md y PROYECTO/prompt.md documentan --approved-by y que el hash se verifica; Global/ regenerado con ./build.sh (opencode y claude-code reciben feature-batch; codex no publica commands). Dos residuos registrados con log-decision en vez de arreglados de contrabando: LEGAL_TRANSITIONS sigue sin las cuatro fases previas, y las 4 derivas de hash vivas no se convierten en gate porque endurecer validate dejaria a sync-project.sh sin poder sincronizar proyectos.

## Hallazgos

- F-02 [high] closed
- F-04 [medium] refuted · refutado por finding-verifier: The claimed cost cannot occur: the failing assertion carries the guard's own output, so the failure self-diagnoses at t… [tests/test_harness.py:989 asserts returncode 0 with verified.stdout + verified.…]
- F-05 [low] refuted · refutado por finding-verifier: AC-13 promises that init cannot assert an approval that never happened by way of the spec sha256; it says nothing about… [docs/specs/009-self-application/spec.md:133-141 states AC-13 in terms of the sp…]
- F-06 [medium] refuted · refutado por finding-verifier: Re-raises a recorded, reasoned exclusion, and its premise that the debt is invisible from the artifacts is false: it is… [ai/state/decisions-log.jsonl:31 holds the slug cuatro-archivos-de-estado-afirma…]
- F-07 [low] refuted · refutado por finding-verifier: It describes no defect and says so in its own text. Every enforceable property it examined is implemented and exercised… [check-feature-state.py:150-153 refuses an empty reason with WAIVER_WITHOUT_REAS…]
- F-01 [high] closed
- F-03 [high] closed
- F-08 [medium] closed
- F-09 [low] refuted · refutado por finding-verifier: The explicit --mode feature is required rather than wrong: the CLI default is scoped and full SDD budgets are opt-in, s… [ai/scripts/feature-state.py:2427 sets --mode default scoped with the adjacent c…]

## Recorrido

- review: repair_required (9 hallazgos)
- verificación: 5 refutados, 4 sostenidos
- repair: F-01, F-02, F-03, F-08 → 3 archivos
- delta review: pass
- testing: pass
- runtime QA: pass (waived)
- gate `verify`: pass
- gate `self-scaffold-sync`: pass
- gate `whitespace`: pass
- gate `ownership`: pass
- gate `feature-state`: pass
- gate `canonical-paths`: pass

↩ [[features/009-self-application|009-self-application]]
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
