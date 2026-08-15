# MODEL_PIN_UNAVAILABLE y MODEL_METADATA_INFERRED siguen sin filtrar, y el patron es el defecto

<!-- notas:auto -->
- fecha: 2026-08-15 · actor: orchestrator
- alcance: [[features/027-controles-que-miran|027-controles-que-miran]] · [[features/027-controles-que-miran/P3-gates-que-preguntan-antes|P3-gates-que-preguntan-antes]]

## Contexto

El reviewer independiente de 027/P3 midio, contra el CLI real, que despues de P3 un package-reviewer con un pin obsoleto recibe exit 1 aunque el router selecciono una identidad valida y usable, mientras que el mismo rol con un model_request que no se pudo honrar sigue con exit 0. Dos situaciones identicas, resultados opuestos, decididos por que mecanismo pidio el modelo. service.py:503-509 declara textualmente que MODEL_PIN_UNAVAILABLE es 'purely additive to reason_codes, same discipline as RUNTIME_REDIRECTED', asi que la razon escrita para dejarlo afuera era falsa. Lo mismo con MODEL_METADATA_INFERRED (service.py:493-495, ADR-0029), medido: (False, 1) con una identidad valida en la mano. Ya son cuatro marcadores aditivos y tres filtros.

## Decisión

El comportamiento NO cambia en P3: filtrar MODEL_PIN_UNAVAILABLE excede el AC-07 aprobado (spec.md D-5 nombra solo MODEL_PINNED y MODEL_REQUEST_*) y necesitaria su propio review. Lo que P3 repara es el registro: el comentario de routing_cli.py, el del test y la evidencia pasan a decir la razon verdadera -queda fuera del alcance del AC aprobado, es un hueco conocido y medido- en vez de una afirmacion sobre la semantica del marcador que el codigo fuente desmiente. El hueco queda aca, con su medicion.

## Consecuencias

Queda pendiente para una feature que sea duena de service.py: el arreglo durable no es filtrar un cuarto codigo aguas abajo, es una lista nombrada de prefijos informativos declarada JUNTO a donde se emiten. La causa raiz es estructural y ya se repitio cuatro veces: cada vez que service.py agrega un reason code 'purely additive', _decide_status queda atras y una decision no ejecutable pero valida sale con exit 1, frenando una delegacion que deberia proceder. Mientras tanto, un rol de review con pin obsoleto o con metadata inferida sigue siendo denegado.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
