# R3: enmienda del threat model de routing-v2

<!-- notas:auto -->
- fecha: 2026-07-25 · actor: orchestrator
- alcance: [[features/003-trusted-routing-pi-runtime|003-trusted-routing-pi-runtime]] · [[features/003-trusted-routing-pi-runtime/P1R-trusted-routing|P1R-trusted-routing]]

## Contexto

La delta review final dejo FD-001..FD-010 abiertos. FD-001 (critico) y las mitades 'inyectable' de FD-004/FD-006 exigen permits no forjables y composicion no construible contra codigo in-process, algo imposible en Python puro y contradictorio con design.md:296-298, que ya declara al proceso malicioso same-UID fuera del threat model. El documento 'focused delta scope' del reviewer nunca se persistio.

## Decisión

El adversario in-process/same-UID queda explicitamente fuera de scope. La garantia exigible es fail-closed ante accidente (corrupcion, drift de schema, reemplazo involuntario) y ante atacantes sin el UID del usuario. FD-001/FD-004/FD-006 se reparan solo en su parte factible (composicion sellada con seam privado de tests, binding recomputado desde catalogo en disco, root derivado de pwd inmune a HOME); la parte imposible (permit no forjable in-process, clasificacion statfs de filesystem, traversal descriptor-relative completo, re-probe por autorizacion) se registra como excepcion aprobada del paquete. FD-009 se cierra con matriz pragmatica: crash, concurrencia, retencion, privacidad, CLI; sin tests que fijen output exacto de CLIs de terceros.

## Consecuencias

Desbloquea la convergencia de P1R en un unico ciclo R3 autorizado. Las excepciones quedan auditables en el estado del paquete y en esta decision. Cualquier endurecimiento futuro contra same-UID requiere nueva feature con threat model propio.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
