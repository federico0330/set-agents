# start-review-panel devuelve ok sin agregar roles cuando se le pasa un panel-id existente

<!-- notas:auto -->
- fecha: 2026-07-28 · actor: orchestrator
- alcance: [[features/007-quota-visibility|007-quota-visibility]] · [[features/007-quota-visibility/P0-role-affinity|P0-role-affinity]]

## Contexto

Al abrir el panel de P0 llame a start-review-panel sin --role y quedo declarado con un solo miembro (package-reviewer), aunque habia lanzado dos revisores concurrentes. record-subreview rechazo correctamente al architect con 'role architect is not part of active review panel'. El intento de corregirlo con start-review-panel --panel-id RP-01 --role package-reviewer --role architect devolvio ok:true y NO agrego el rol: los roles del panel siguieron siendo ['package-reviewer'].

## Decisión

Se registra como defecto del arnes, no se repara en la 007 (esta fuera del alcance de sus tres paquetes). Son dos defectos distintos: (1) start-review-panel sin --role no falla, deja un panel declarado con menos miembros de los que el orquestador va a usar, y el error recien aparece cuando el subreview vuelve, o sea despues de haber gastado el spawn; (2) start-review-panel con un panel-id existente es un no-op que reporta exito, que es la peor combinacion posible en un comando mutante -- el llamador cree que corrigio algo.

## Consecuencias

Los hallazgos del architect entran por record-review en vez de por el panel, lo que consume el segundo ciclo de review profundo del paquete. Es contabilidad honesta pero no refleja el proceso real: los dos revisores corrieron concurrentes en un solo batch, que por la regla 006-P1 es UN ciclo, no dos. La reparacion natural es que start-review-panel exija --role explicito y que un panel-id ya existente sea un error, no un no-op.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
