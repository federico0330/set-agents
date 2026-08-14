# 024-listo-para-terceros · C4-higiene-de-repo-publico

<!-- notas:auto -->
## Motivo

- objetivo: Lo que un repo publico necesita, y una matriz de soporte medida en vez de asumida
- complejidad: small
- paths: `LICENSE`, `CONTRIBUTING.md`, `CHANGELOG.md`, `SECURITY.md`, `docs`, `ai/scripts`, `tests`
- depende de: C3-primer-arranque-honesto

## Tareas

- [x] LICENSE, CONTRIBUTING, CHANGELOG, SECURITY, y HANDOFF fuera de la raiz (AC-09) (completed) · unittest: 1117 OK / 3 skips (orquestador); verify.sh VERIFY_PASS; build.sh --check BUILD_CHECK_PASS
- [x] Ejemplos sin el nombre del cliente real (AC-10) (completed) · unittest: 1117 OK / 3 skips (orquestador); verify.sh VERIFY_PASS; build.sh --check BUILD_CHECK_PASS
- [x] Matriz de soporte MEDIDA, incluida la de roles subagent en opencode (AC-11) (completed) · unittest: 1117 OK / 3 skips (orquestador); verify.sh VERIFY_PASS; build.sh --check BUILD_CHECK_PASS
- [x] Update re-apuntable: hoy origin/main hardcodeado rompe un fork (AC-12) (completed) · unittest: 1117 OK / 3 skips (orquestador); verify.sh VERIFY_PASS; build.sh --check BUILD_CHECK_PASS

## Recorrido

- gate `unittest-suite`: pass
- gate `verify-sh`: pass
- gate `build-check`: pass
- gate `git-diff-check`: pass

## Spawns

- SPAWN-001 implementer · modelo anthropic/haiku · effort low · route run1_fdc3d20dd2d072f82ef5fa8dad23d137

context pack: `docs/specs/024-listo-para-terceros/context/C4-higiene-de-repo-publico.md`

↩ [[features/024-listo-para-terceros|024-listo-para-terceros]]
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
