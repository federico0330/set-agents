# CORRECCION: la nota que decia que setup_models.py seguia funcionando sin tocarlo era falsa

<!-- notas:auto -->
- fecha: 2026-08-12 · actor: orchestrator
- alcance: [[features/021-gates-que-no-mienten-ni-callan|021-gates-que-no-mienten-ni-callan]] · [[features/021-gates-que-no-mienten-ni-callan/P1-check-que-verifica|P1-check-que-verifica]]

## Contexto

Al registrar la decision del perfil fijo (slug check-compara-con-perfil-canonico-fijo) escribi, siguiendo el analisis del spec-challenger, que con perfil canonico fijo install.sh y setup_models.py seguian funcionando sin tocarlos. El implementer de P1 NO le creyo a la nota: corrio el comando de produccion de verdad, sin mocks, y encontro que setup_models.py:397 y :570 SI rompian -- no por el perfil, sino porque llaman a --check inmediatamente despues de escribir un models.toml nuevo, antes de que nada regenere Global/. Con la semantica nueva, cualquier cambio de modelo real daba GLOBAL_TREE_DRIFT y BUILD_CHECK_FAIL rc=1.

## Decisión

La afirmacion queda RECTIFICADA, no borrada. El arreglo es _generate_smoke_test (setup_models.py:107-120): reutiliza build.sh --output para el smoke test de 'genera sin explotar' que --check daba antes como efecto colateral, sin comparar contra Global/. Separa dos preguntas que eran la misma solo por accidente.

## Consecuencias

Es la sexta afirmacion de esta sesion que no resiste la re-ejecucion, y la primera que es MIA y no de un subagente. Refuerza la leccion de RDD: un recibo se re-ejecuta, no se hereda de una nota previa por mas que la haya escrito el orquestador. El implementer hizo exactamente lo correcto al desconfiar del documento y medir.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
