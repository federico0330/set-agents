# AM-2: cache de probes filtering-only + re-probe fresco del seleccionado (enmienda a 003/ADR-0005)

<!-- notas:auto -->
- fecha: 2026-07-26 · actor: orchestrator
- alcance: [[features/004-adaptive-dispatch|004-adaptive-dispatch]]

## Contexto

Cada decision tarda ~14s por 4 subprocesos de probe (N-3 de P1R). La 003 exige fresh-per-invocation y ADR-0005 difirio todo cache. Challenge B2: un positivo stale puede autorizar un writer contra un proveedor deslogueado y quemar la corrida sin fallback.

## Decisión

Usuario (2026-07-26): cache TTL 300s con clave (uid + digest de [catalog]+[routing] + par) SOLO para filtrar candidatos; antes de autorizar un writer se re-probea fresco el par seleccionado (y el fallback si difiere). Cache bajo el root del store de routing, escritura atomica 0600, corrupto=>ignorado. ADR-0006 antes de P1.

## Consecuencias

Decision <1s con cache caliente sin autorizaciones stale. El cache nunca amplia el set de modelos ni autoriza por si mismo.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
