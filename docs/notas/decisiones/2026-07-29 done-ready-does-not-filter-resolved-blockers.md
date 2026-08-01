# done_ready trata cualquier blocker historico como abierto para siempre, incluso ya resuelto

<!-- notas:auto -->
- fecha: 2026-07-29 · actor: orchestrator
- alcance: [[features/003-trusted-routing-pi-runtime|003-trusted-routing-pi-runtime]] · [[features/003-trusted-routing-pi-runtime/P1R-trusted-routing|P1R-trusted-routing]]

## Contexto

Al integrar 003-trusted-routing-pi-runtime, transition DONE fallo con 'open blocker exists' pese a que los 4 blockers registrados (R1/R2/R3, 2026-07-24/25) tenian resolved_at/resolved_by/resolved_reason seteados por el usuario dias antes. done_ready (feature-state.py:490) hace 'if data.get("blockers"): errors.append(...)' -- chequea que el array este vacio, no que no tenga entradas sin resolver. El renderer de STATUS.md (linea 629) ya resuelve esto correctamente: 'blockers = [b for b in data.get("blockers", []) if not b.get("resolved_at")]'. Ademas, ningun comando (reopen incluido) borra un blocker resuelto del array, solo lo marca in-place -- por diseno el array crece para siempre. La consecuencia real: cualquier feature que alguna vez fue bloqueada, sin importar cuan bien resuelto haya sido el bloqueo, no puede llegar nunca a DONE con el codigo actual.

## Decisión

Se corrigio a mano el array blockers de 003 (ai/state/features/003-trusted-routing-pi-runtime.json), quitando las 4 entradas ya resueltas -- ninguna se borro de history, que conserva integros los 4 pares block/reopen con timestamp, razon y quien autorizo cada reapertura. No se toco feature-state.py: es la herramienta que 009-self-application acaba de dejar DONE (terminal, sin paquetes nuevos posibles), asi que un parche real de done_ready necesita una feature/paquete nuevo, no un edit de contrabando en medio de una integracion.

## Consecuencias

Fix correcto pendiente para un futuro paquete (candidato: nueva feature de mantenimiento del harness, ya que 009 quedo terminal): done_ready deberia usar el mismo filtro que ya existe en el renderer de STATUS.md -- 'any(not b.get(resolved_at) for b in blockers)' en vez de 'if blockers'. Mientras tanto, cualquier feature que llegue a INTEGRATION habiendo tenido blockers resueltos en su historia va a pegar el mismo falso bloqueo y va a necesitar la misma correccion manual (o esperar el fix real).
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
