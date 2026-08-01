# P3-graph-view abre el tracking de la feature 006 sin backfillear P1/P2

<!-- notas:auto -->
- fecha: 2026-07-30 · actor: implementer
- alcance: [[features/006-execution-graph|006-execution-graph]] · [[features/006-execution-graph/P3-graph-view|P3-graph-view]]

## Contexto

006-execution-graph shipped P1/P2 fuera de la maquina de estados (decision feature-006-delivered-outside-state-machine, 2026-07-28) y quedo waived en check-feature-state.py. P3-graph-view es el primer paquete de 006 trackeado: init 006-execution-graph solo declara AC-20..AC-29 (las ACs de P3), nunca AC-01..AC-19. AC-07 de docs/specs/009-self-application/spec.md:129-132 ya documenta explicitamente que la feature 006 no se backfillea.

## Decisión

No se fabrica historia retroactiva para P1/P2: el archivo de estado de 006-execution-graph arranca en su propio primer evento (init de P3), igual que la decision anterior establecio para toda la feature. Consecuencia de proceso, no de codigo: 006 se queda en PACKAGE_ACCEPTED tras aceptar P3 y el orquestador nunca invoca 'transition DONE' para esta feature mientras AC-01..AC-19 sigan fuera de la maquina de estados -- done_ready() lo permitiria tecnicamente (P3 seria el unico paquete registrado y estaria accepted), pero hacerlo afirmaria que las 27 ACs completas del contrato se entregaron bajo tracking cuando solo las 9 de P3 lo estuvieron. El waiver '006-execution-graph' en check-feature-state.py se retira en el mismo cambio que crea ai/state/features/006-execution-graph.json (AC-28), nunca uno sin el otro.

## Consecuencias

check-feature-state.py ya no necesita el waiver 006-execution-graph (WAIVED queda vacio). STATUS.md y docs/notas/features/006-execution-graph.md ahora existen y reflejan el estado real de P3 unicamente. Un lector que busque P1/P2 de 006 en la maquina de estados no los va a encontrar -- siguen documentados solo en spec.md, ADR-0009 y los 12 commits originales, tal como establecio la decision feature-006-delivered-outside-state-machine.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
