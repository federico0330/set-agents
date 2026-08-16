# D1 se reporto integrado sin estarlo: el exit code se leyo de head y la medicion se hizo en el lugar equivocado

<!-- notas:auto -->
- fecha: 2026-08-16 · actor: orchestrator

## Contexto

El orquestador aplico el parche de 025/D1 con 'git apply --3way $S/d1.patch 2>&1 | grep ... | head -5' y leyo 'resultado: 0'. Ese $? era el de head, no el de git apply: el parche NO se aplico a los archivos existentes -solo entraron los archivos nuevos, de donde salio el .smoketest que despues hubo que borrar-. El commit 8091b0b no contiene set_agents_app.py, ni tests/test_harness.py, ni docs/adr/0050. Verificado despues: 68 flags visibles, 10 emoji en el menu, ADR-0050 inexistente. Es la TERCERA vez en la misma sesion que el orquestador lee el exit code de un pipe en vez del comando que le importa -paso tambien con el guard fail-closed y con la primera medicion del techo de reparacion-.

## Decisión

D1 recuperado del parche que sobrevivio en el scratchpad, reaplicado con el exit code leido correctamente -exit=0, cero conflictos-, y verificado POR COMPORTAMIENTO sobre el arbol integrado: 41 flags visibles contra 71 con --avanzado, cero items de menu con no-ASCII, ADR-0050 presente, --json en los prompts. Dos reglas nuevas para el orquestador: nunca leer $? despues de un pipe -usar PIPESTATUS o redirigir a archivo-, y medir SIEMPRE sobre el arbol integrado y despues de integrar, nunca en el worktree del agente.

## Consecuencias

La leccion de fondo es peor que el error: la verificacion de D1 de anoche fue CORRECTA y no sirvio, porque midio el worktree del agente -donde el trabajo si estaba- y se asumio que integrar era mecanico. Una medicion hecha en el lugar equivocado da verde y no prueba nada. Junto con el caso de D5, que nunca produjo codigo y se dio por implementado, queda claro que al orquestador le faltaba un paso: despues de integrar, verificar el ARTEFACTO en el arbol final, con una medicion de comportamiento y no con un grep del reporte.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
