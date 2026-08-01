# Colisión de id cross-nivel en modo whole-repo del grafo queda fail-closed, no resuelta

<!-- notas:auto -->
- fecha: 2026-07-30 · actor: orchestrator
- alcance: [[features/006-execution-graph|006-execution-graph]] · [[features/006-execution-graph/P3-graph-view|P3-graph-view]]

## Contexto

PR-03 desambigua colisiones de id dentro de un mismo nivel (dos paquetes, o dos features), vía disambiguated_norm con scope ('feature',) / ('package', fid). Pero una colisión CRUZADA de nivel (ej. feature 'a-b' vs feature 'a' + paquete 'b', que normalizan al mismo sg_a_b) no está cubierta por ningún scope. Verificado por el delta-reviewer: el oráculo la detecta (duplicate subgraph id) y render_mermaid levanta StateError -- fail-closed y ruidoso, nunca un documento corrupto. Inalcanzable en modo single-feature (el que usa render_notes siempre) y ausente en los 8 feature ids reales de hoy.

## Decisión

No se resuelve ahora: el modo whole-repo de --graph queda inutilizable (no degradado, sino con error explícito) ante esa combinación específica de nombres, en vez de invertir esfuerzo en un desambiguador de 3 niveles para un caso sin instancia real.

## Consecuencias

Si en el futuro se agrega una feature/paquete cuyo id colisione cross-nivel con otro, --graph sin --feature-id fallará con StateError hasta que se resuelva. record-late-review o un paquete futuro puede ampliar disambiguated_norm a un scope global si esto deja de ser hipotético.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
