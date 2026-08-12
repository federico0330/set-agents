# 021-gates-que-no-mienten-ni-callan · P1-check-que-verifica

<!-- notas:auto -->
## Motivo

- objetivo: Que build.sh --check compare de verdad contra Global/ y que la suite deje de enmascarar el drift
- complejidad: medium
- paths: `build.sh`, `ai/scripts/verify.sh`, `tests/test_harness.py`, `docs/adr/0041-gates-que-no-mienten-ni-callan.md`

## Tareas

- [x] build.sh --check compara STAGING contra los 4 arboles y falla con rc distinto de cero (AC-01) (completed) · Verificado en vivo por el orquestador: con Global/ sucio ./build.sh --check da rc=1 y GLOBAL_TREE_DRIFT nombrando el archivo; restaurado da rc=0. Suite 972 (base 970, +2).
- [x] Salida que distingue las dos verificaciones (AC-02) (completed) · Verificado en vivo por el orquestador: con Global/ sucio ./build.sh --check da rc=1 y GLOBAL_TREE_DRIFT nombrando el archivo; restaurado da rc=0. Suite 972 (base 970, +2).
- [x] Test que ensucia Global/ y exige que --check falle; rojo contra el build.sh de hoy (AC-03) (completed) · Verificado en vivo por el orquestador: con Global/ sucio ./build.sh --check da rc=1 y GLOBAL_TREE_DRIFT nombrando el archivo; restaurado da rc=0. Suite 972 (base 970, +2).
- [x] La suite deja de corregir drift preexistente en silencio (AC-04) (completed) · Verificado en vivo por el orquestador: con Global/ sucio ./build.sh --check da rc=1 y GLOBAL_TREE_DRIFT nombrando el archivo; restaurado da rc=0. Suite 972 (base 970, +2).
- [x] Anotar que probaban realmente los gates de 019 y 020 (AC-05) + ADR-0041 (completed) · Verificado en vivo por el orquestador: con Global/ sucio ./build.sh --check da rc=1 y GLOBAL_TREE_DRIFT nombrando el archivo; restaurado da rc=0. Suite 972 (base 970, +2).

## Recorrido

- gate `verify`: pass
- gate `build-check`: pass
- gate `diff-check`: pass

## Spawns

- SPAWN-001 implementer · modelo openai-codex/gpt-5.6-sol · effort medium · route run1_bd77f9269e4366144ea3ed0e20ef8df8
- SPAWN-002 package-reviewer · modelo anthropic/sonnet · effort medium · route dec1_527da951eb57a79094e8efe0285db1f3

context pack: `docs/specs/021-gates-que-no-mienten-ni-callan/context/P1-check-que-verifica.md`

↩ [[features/021-gates-que-no-mienten-ni-callan|021-gates-que-no-mienten-ni-callan]]
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
