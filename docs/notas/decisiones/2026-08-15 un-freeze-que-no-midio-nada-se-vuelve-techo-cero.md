# Defecto: freeze-candidate compara HEAD contra HEAD y el techo de reparacion queda en cero para siempre

<!-- notas:auto -->
- fecha: 2026-08-15 · actor: orchestrator
- alcance: [[features/027-controles-que-miran|027-controles-que-miran]] · [[features/027-controles-que-miran/P2-nada-escribe-afuera|P2-nada-escribe-afuera]]

## Contexto

Al correr check-repair-ceiling.py sobre 027/P2 dio REPAIR_CEILING_FAIL con budget_lines 0 y changed_lines 64076. La causa no es el repair: es el freeze. candidate_identity de P2 quedo con baseline_ref HEAD, candidate_ref HEAD, base_tree igual a candidate_tree, changed_lines 0 y paths_digest sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 -- que es literalmente el sha256 de la cadena VACIA, verificado. El freeze corrio mientras todo el trabajo estaba sin commitear en el working tree, asi que comparo HEAD contra HEAD y midio la nada. Despues cli_repair.py:189-199 derivo budget_lines = min(cap, ceil(0/2)) = 0, y model.py:417-421 hace fallar la aceptacion de cualquier repair posterior. Un techo de cero lineas es un paquete que no se puede reparar nunca.

## Decisión

Se restaura repair_ceiling a null para P2, que es lo que el propio ADR-0023 prescribe para un paquete sin medicion valida: 'Si candidate_identity no existe todavia, NO se congela ningun techo -- el mecanismo es aditivo, nunca retroactivo', y check-repair-ceiling.py trata un techo ausente como nada que chequear. No es relajar el control: es devolverle su comportamiento disenado para el caso 'no hay medicion'. El techo no se reconstruye retroactivamente porque no hay dato honesto con que hacerlo: el arbol ya mezcla P2, P3 y P4, y el freeze original nunca midio nada. La reparacion real de P2 midio 493 lineas (436 inserciones, 57 borrados, 3 archivos) para 7 hallazgos verificados, uno de ellos high; queda declarado en la evidencia en vez de simulado en el estado.

## Consecuencias

El defecto es de la misma familia que los seis que la feature 027 vino a reparar: un control que informa un numero que no midio. Y es peor que callar, porque el cero se propaga a una decision de bloqueo. El arreglo durable son dos lineas en dos lugares: cli_repair.py:189 debe tratar changed_lines == 0 como AUSENCIA de medicion y no como presupuesto cero, y freeze-candidate debe negarse a congelar -o marcarse como no-medido- cuando baseline y candidato resuelven al mismo arbol habiendo cambios sin commitear. Ninguno de los dos archivos esta en los owned_paths de un paquete de 027, asi que va al backlog de la auditoria en vez de repararse oportunistamente.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
