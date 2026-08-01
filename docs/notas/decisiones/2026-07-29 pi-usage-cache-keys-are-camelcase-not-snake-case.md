# El usage real de Pi manda cacheRead/cacheWrite en camelCase, no cache_read/cache_write

<!-- notas:auto -->
- fecha: 2026-07-29 · actor: orchestrator
- alcance: [[features/007-quota-visibility|007-quota-visibility]] · [[features/007-quota-visibility/P2-spawn-accounting|P2-spawn-accounting]]

## Contexto

El spawn en vivo requerido por la verificacion del paquete (role=implementer, task_class=mechanical) devolvio {"input":3321,"output":5,"reasoning":0,"totalTokens":3326,"cacheRead":0,"cacheWrite":0,"cost":{...}}. USAGE_TOKEN_FIELDS asumia snake_case parejo (cache_read/cache_write) para las cinco claves, copiado del vocabulario de cost-report.py:FIELDS sin verificar contra el JSON real que Pi manda por cable. _usage_row buscaba usage['cache_read'] y nunca encontraba nada bajo ese nombre.

## Decisión

_usage_row gana _USAGE_FIELD_ALIASES: para cache_read/cache_write se prueban las dos grafias (snake_case primero, camelCase como alias), input/output/reasoning/totalTokens quedan sin alias porque el JSON real ya los manda planos. Pinned por test_usage_row_accepts_pis_actual_camelcase_cache_keys sobre el payload real observado, mutacion verificada (sacar el alias tira el test).

## Consecuencias

Sin este alias, usage_cache_read/usage_cache_write habrian quedado SIEMPRE NULL en produccion aun cuando Pi reporta 0 explicito -- indistinguible de que Pi nunca los manda, exactamente la confusion NULL-vs-0 que AC-08 existe para prevenir, un nivel mas arriba en el parseo. Encontrado por la propia verificacion en vivo que el plan del paquete exige, no por lectura de codigo: el reporte 004-P3 solo tenia una muestra sin cache reportado, asi que nada anterior habia ejercitado esta rama con datos reales.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
