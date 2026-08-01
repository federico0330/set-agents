# 3 hallazgos low derivados de la ronda 4 de repair quedan como deuda, no reparados

<!-- notas:auto -->
- fecha: 2026-07-30 · actor: orchestrator
- alcance: [[features/006-execution-graph|006-execution-graph]] · [[features/006-execution-graph/P3-graph-view|P3-graph-view]]

## Contexto

El delta-reviewer final (pass) encontró D-07 (el degradado de D-04 puede emitir un grafo.md parcial/contradictorio para una feature con TypeError dentro del walk, en vez de abortar limpio esa feature -- y render_notes pierde el rastro en render-failures.log porque el except lo intercepta antes), D-08 (el except de D-04 incluye AttributeError/KeyError que un fuzz de 90 casos probó inalcanzables desde datos malformados -- solo taparían bugs de programación propios del módulo, contradiciendo la postura explícita de render_mermaid/cmd_graph de que un bug del propio generador debe salir ruidoso, nunca silencioso), D-09 (informativo: la revalidación de D-03 puede fallar con un --root degenerado tipo espacio-solo, pero devuelve JSON legible ok:false + exit 2, nunca traceback -- no accionable).

## Decisión

No se reparan ahora. El propio delta-reviewer recomendó explícitamente no abrir una quinta ronda de repair por estos tres, todos low, ninguno toca seguridad ni contratos públicos, y el costo marginal de otro ciclo supera el beneficio después de 4 rondas ya corridas sobre este paquete.

## Consecuencias

D-08 es la más barata de resolver si se retoma (una línea: acotar el except a solo TypeError, ya verificado seguro por el fuzz). D-07 requiere ~6 líneas (construir cada feature en un _GraphState descartable, mergear solo al éxito). Candidatas naturales para un P3.1 futuro o para cuando se implemente --caused-by-spawn.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
