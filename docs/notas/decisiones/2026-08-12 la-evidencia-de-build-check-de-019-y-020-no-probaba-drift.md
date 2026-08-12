# Los gates de 019 y 020 que citaban 'build.sh --check -> CHECK_PASS' como prueba de sin-drift no probaban eso

<!-- notas:auto -->
- fecha: 2026-08-12 · actor: orchestrator
- alcance: [[features/021-gates-que-no-mienten-ni-callan|021-gates-que-no-mienten-ni-callan]] · [[features/021-gates-que-no-mienten-ni-callan/P1-check-que-verifica|P1-check-que-verifica]]

## Contexto

AC-05. Hasta ADR-0041, build.sh --check generaba los cuatro arboles en un STAGING temporal y NUNCA los comparaba contra Global/: solo cotejaba dos archivos de self-scaffold entre PROYECTO/ai/scripts/ y ai/scripts/. El CHECK_PASS que se leia lo imprime generate.py:730 al generar, o sea 'corri sin explotar'. Durante 019 y 020 se registraron decenas de gates citando esa linea como evidencia de ausencia de drift.

## Decisión

No se reabren 019 ni 020: su codigo esta revisado y sus suites verdes, y verify.sh SI hacia la comparacion real (:24-28) aunque despues de que la propia suite pisara el drift. Se deja constancia de que aquella evidencia probaba 'la generacion no explota' y 'los dos archivos de self-scaffold coinciden', NUNCA 'Global/ esta sincronizado con _canonical'. Quien lea esos gates tiene que leerlos con ese alcance.

## Consecuencias

Desde ADR-0041 la linea significa lo que dice: --check compara contra los cuatro arboles con perfil go-zen fijo y falla nombrando el archivo. Verificado por el orquestador: con un Global/ sucio da rc=1 y GLOBAL_TREE_DRIFT; restaurado, rc=0.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
