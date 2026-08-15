# 027-controles-que-miran · P4-owned-paths-matchea-directorios

<!-- notas:auto -->
## Motivo

- objetivo: Que owned_paths interprete directorios como directorios, sin falsos positivos ni relajacion del alcance
- complejidad: small
- riesgo: Un matcher demasiado amplio puede ocultar modificaciones fuera de alcance; probar directorio, barra final y prefijo tes…
- paths: `ai/scripts/check-owned-paths.py`, `PROYECTO/ai/scripts/check-owned-paths.py`, `tests`, `docs/adr`
- depende de: P3-gates-que-preguntan-antes

## Tareas

- [x] Un directorio declarado en owned_paths cubre sus descendientes (AC-08) (completed) · Matriz de 5 filas contra el script real via --changed-file, roja antes y verde despues: tests y tests/ cubren tests/test_harness.py, docs/adr cubre su ADR, y tests-extra/x.py mas outside/x.py siguen dando OWNERSHIP_FAIL exit 2., P4-F04 reparado: las grafias /tests, ./tests, docs//adr, tests// y tests\\sub pasan todas. Verificado por el orquestador en el arbol integrado, las cuatro en rc=0., Las dos copias del script byte-identicas (cmp exit 0) y ./build.sh --check en BUILD_CHECK_PASS.
- [x] Se preserva el fail-closed para archivos genuinamente fuera de alcance y prefijos (AC-09) (completed) · Trampa de prefijo cubierta con frontera real, startswith(directory + '/'), no startswith pelado: tests no matchea tests-extra/x.py. Mutantes del reviewer: prefijo pelado y prefijo sin barra ponen el test en rojo, o sea la guarda discrimina el arreglo correcto del ingenuo., P4-F01 reparado, y era una relajacion que el propio diff habia introducido: tests/../ai/scripts/pwn.py y tests/../../etc/passwd pasaban de FAIL a PASS. Con posixpath.normpath vuelven a OWNERSHIP_FAIL, y verificado por el orquestador que tests/real.py sigue en PASS y tests-extra/x.py sigue en FAIL., Precedencia de read-only preservada con test dedicado, y el efecto real del ensanchamiento de approved_exception -que cancela el read-only de todo el subarbol- ahora nombrado y testeado, en vez de justificado con una afirmacion falsa.

## Hallazgos

- P4-F01 [medium] closed — correctness
- P4-F02 [medium] closed — data-integrity
- P4-F03 [low] closed — testing
- P4-F04 [low] closed — correctness
- P4-F06 [low] closed — readability

## Recorrido

- review: repair_required (5 hallazgos)
- verificación: 0 refutados, 5 sostenidos
- repair: P4-F01, P4-F02, P4-F03, P4-F04, P4-F06 → 6 archivos
- delta review: pass
- testing: pass
- runtime QA: pass (waived)
- runtime QA: pass
- gate `unittest-suite`: pass
- gate `verify-sh`: pass
- gate `build-check`: pass
- gate `git-diff-check`: pass
- gate `ownership`: pass

## Spawns

- SPAWN-001 implementer · modelo anthropic/claude-sonnet-5 · effort medium
- SPAWN-002 package-reviewer · modelo anthropic/claude-opus-5 · effort high
- SPAWN-003 repair-agent · modelo anthropic/claude-sonnet-5 · effort medium

context pack: `docs/specs/027-controles-que-miran/context/P4-owned-paths-matchea-directorios.md`

↩ [[features/027-controles-que-miran|027-controles-que-miran]]
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
