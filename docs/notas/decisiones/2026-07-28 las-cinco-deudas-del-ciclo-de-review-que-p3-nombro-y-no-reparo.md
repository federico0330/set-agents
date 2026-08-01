# Lo que quedo abierto en el ciclo de review despues de panel-integrity

<!-- notas:auto -->
- fecha: 2026-07-28 · actor: orchestrator
- alcance: [[features/009-self-application|009-self-application]] · [[features/009-self-application/P3-panel-integrity|P3-panel-integrity]]

## Contexto

Trazar el grafo de llamadas para AC-08/09/10 expuso cinco defectos preexistentes que no son parte de los criterios del paquete. Nombrarlos y dejarlos es mejor que arreglarlos de contrabando: cada uno cambia conducta de comandos que todo paquete en vuelo usa.

## Decisión

1) cmd_record_review es la unica puerta hacia PACKAGE_TESTING que no chequea has_open_findings, a diferencia de finalize-review-panel y record-delta-review: record-review pass con un hallazgo high abierto deja el paquete en PACKAGE_TESTING. Es la raiz de F-03, que se reparo solo en su afirmacion falsa. 2) record-delta-review --new-finding nunca setea source_role, asi que un hallazgo de delta review no tiene autor y el guard anti-autorrefutacion no puede dispararse sobre el; el blacklist de F-02 impide forjarlo pero no lo estampa. 3) record_event devuelve False en replay y los llamadores sin cortocircuito propio ignoran el retorno, asi que escriben estado con revision incrementada y sin entrada de historia; los cuatro verbos que si cortocircuitan quedaron cubiertos por replayed(), la clase sobrevive en el resto. 4) next_transition recomienda DELTA_REVIEW desde PACKAGE_REPAIR con verifications no vacio aunque no haya nada que reparar. 5) finalize-review-panel --allow-missing es todo-o-nada: no puede expresar 'cerra sin el rezagado pero segui exigiendo los otros dos', que es justo lo que hace falta cuando un panel se extendio.

## Consecuencias

Ninguna bloquea una entrega hoy. Las dos que valen paquete propio son la 1 y la 2, porque debilitan garantias que el arnes ya declara tener. Y queda una limitacion que no tiene arreglo posible por test, dicha explicitamente: un comentario que miente no tiene guard. F-05 fue exactamente eso -- el arreglo de F-01 dejo adentro un comentario afirmando la conducta previa a la reparacion -- y lo unico fijable es la propiedad que el comentario describia, no el comentario. test_replay_detection_has_exactly_one_definition hace eso y nada mas.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
