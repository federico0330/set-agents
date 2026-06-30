# Criterios de aceptación — Spec 000 (EJEMPLO)

Cada criterio es testeable (Given/When/Then) con resultado/estado esperado.

## AC-1 — Pago atómico
- Given una reserva válida no pagada y no vencida
- When se confirma el pago
- Then asiento=Vendido, reserva=Pagada y se escribe AuditLog, **en una sola transacción**
- And si el proceso falla a mitad, no queda ningún cambio aplicado (rollback total).

## AC-2 — Concurrencia
- Given dos requests simultáneos sobre el mismo asiento libre
- When ambos intentan reservar
- Then exactamente uno gana (200) y el otro recibe **409 Conflict** (no 500 ni 400).

## AC-3 — Auditar el intento fallido
- Given un intento que pierde la carrera de concurrencia
- When se descarta
- Then queda registrado en AuditLog (con su propio commit, fuera de la transacción que hizo rollback).

## AC-4 — Validaciones previas
- Reserva inexistente → 404 · ya pagada → 409 · vencida → 409 (no se puede pagar/revender una reserva vencida).

## AC-5 — Frontend
- Given que otro usuario gana el asiento
- When llega el 409
- Then se muestra un toast propio ("Ese asiento ya no está disponible") y el mapa se refresca solo
  (sin `alert()`, sin recargar a mano).
