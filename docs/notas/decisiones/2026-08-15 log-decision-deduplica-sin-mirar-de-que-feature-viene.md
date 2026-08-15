# Defecto: la clave de idempotencia de log-decision no incluye feature_id

<!-- notas:auto -->
- fecha: 2026-08-15 · actor: orchestrator

## Contexto

Encontrado por el spec-challenger de 029 al evaluar si un registro estructurado por eje podia montarse sobre log-decision. cli_reporting.py:92-99 deduplica por la terna (slug, title, decision) y feature_id NO esta en la clave. Si hay duplicado no escribe nada y devuelve la entrada vieja (:107-113), con el feature_id de la OTRA feature.

## Decisión

No se monta ningun registro estructurado y repetitivo sobre log-decision hasta que la clave incluya su discriminante. Para la feature 029 se resuelve con un JSONL propio (ai/state/axes-log.jsonl) en vez de tocar log-decision, que ademas evita inflar docs/notas/decisiones/ y la seccion de decisiones del digest. El defecto queda registrado aparte para que lo repare quien sea dueno de cli_reporting.py.

## Consecuencias

Cualquier registro repetitivo montado sobre este comando es incorrecto por construccion: dos features que registren el mismo texto de decision colisionan y la segunda recibe deduped:true SIN escribir fila. El modo de falla es el peor posible -el comando informa exito y no hizo nada-, y aguas abajo produce un rechazo que el usuario no puede corregir repitiendo el comando. Es la misma familia que los seis defectos de 027: algo que informa OK sobre algo que no hizo.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
