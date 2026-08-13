# 022-disponibilidad-real · P4-proveedores-del-usuario

<!-- notas:auto -->
## Motivo

- objetivo: Administrar proveedores propios desde set-agents, sin editar JSON, y que quitar funcione de verdad
- complejidad: high
- paths: `ai/scripts/set_agents_app.py`, `ai/scripts/generate.py`, `ai/scripts/install.py`, `Global/_shared/opencode.json`, `tests`
- depende de: P3-liveness-real

## Tareas

- [x] providers.toml en STATE_DIR con origin por entrada (AC-11) (completed) · unittest discover -s tests: 1034 OK / 3 skips; verify.sh: VERIFY_PASS; build.sh + --check: GLOBAL_TREE_SYNC_OK + BUILD_CHECK_PASS; git diff --check limpio
- [x] Comandos --provider-list add remove verify (AC-12) (completed) · unittest discover -s tests: 1034 OK / 3 skips; verify.sh: VERIFY_PASS; build.sh + --check: GLOBAL_TREE_SYNC_OK + BUILD_CHECK_PASS; git diff --check limpio
- [x] El bloque provider de opencode.json pasa a renderizarse (AC-13) (completed) · unittest discover -s tests: 1034 OK / 3 skips; verify.sh: VERIFY_PASS; build.sh + --check: GLOBAL_TREE_SYNC_OK + BUILD_CHECK_PASS; git diff --check limpio
- [x] Poda por manifiesto extendida a subarboles JSON, sin tocar lo que el harness no puso (AC-14) (completed) · unittest discover -s tests: 1034 OK / 3 skips; verify.sh: VERIFY_PASS; build.sh + --check: GLOBAL_TREE_SYNC_OK + BUILD_CHECK_PASS; git diff --check limpio
- [x] Siembra migratoria que registra TODO, lo del usuario como origin=user (AC-15) (completed) · unittest discover -s tests: 1034 OK / 3 skips; verify.sh: VERIFY_PASS; build.sh + --check: GLOBAL_TREE_SYNC_OK + BUILD_CHECK_PASS; git diff --check limpio

## Recorrido

- review: pass (0 hallazgos)
- testing: pass
- runtime QA: pass
- gate `unittest-suite`: pass
- gate `verify-sh`: pass
- gate `build-check`: pass
- gate `git-diff-check`: pass

## Spawns

- SPAWN-001 implementer · modelo anthropic/opus · effort medium · route run1_f193bfbdbee43aeee46473235a70b1b8
- SPAWN-002 package-reviewer · modelo openai-codex/gpt-5.6-terra · effort high

context pack: `docs/specs/022-disponibilidad-real/context/P4-proveedores-del-usuario.md`

↩ [[features/022-disponibilidad-real|022-disponibilidad-real]]
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
