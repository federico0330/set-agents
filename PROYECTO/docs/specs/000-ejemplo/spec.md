# Spec 000 — <Título de la feature> (EJEMPLO)

## Problema
<Qué problema de negocio resolvemos y por qué importa ahora.>
Ejemplo: el equipo de operaciones necesita confirmar el pago de una reserva de asiento sin que queden
estados inconsistentes ni dobles ventas bajo concurrencia.

## Usuarios y situaciones
<Quién lo usa y en qué momento.>

## Reglas de negocio / invariantes
- Confirmar un pago toca varias entidades (asiento→Vendido, reserva→Pagada, AuditLog): todas o ninguna.
- Antes de cobrar: la reserva existe (si no, 404), no está pagada (409) y no está vencida (409).
- Cada intento de reserva (exitoso o fallido por concurrencia) queda auditado.
- Si dos usuarios compiten por el asiento, exactamente uno gana; el otro recibe 409 Conflict.

## En alcance
<Lista mínima de lo que entra en este slice.>

## Fuera de alcance (no-goals)
<Lo que explícitamente NO se hace ahora: OCR, sync bancario, exportes, etc.>

## Primer slice entregable
<La porción más chica que aporta valor y se puede testear de punta a punta.>
