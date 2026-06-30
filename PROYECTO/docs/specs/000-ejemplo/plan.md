# Plan — Spec 000 (EJEMPLO)

## Secuencia
T-001 (Money) → T-002 (modelo+migración) → T-003 (pago atómico) → T-004 (concurrencia) →
T-005 (audit fallido) → T-006 (errores HTTP) → T-007 (frontend) → T-008 (listado paginado).

## Dependencias
- T-003..T-005 dependen de T-002. T-007 depende de T-006 (status 409 ya definido).

## Riesgos
- Concurrencia mal implementada (token que no incrementa) → doble reserva. Mitigación: T-004 con test de carrera real.
- Auditoría del intento fallido dentro del rollback → registro perdido. Mitigación: T-005 con unidad de trabajo propia.

## Puntos de decisión humana
- Cambios de modelo de datos que puedan reinterpretar plata o historial → ADR + confirmación.
