# record-repair --skip-delta despues de un delta review repair_required deja el paquete imposible de aceptar

<!-- notas:auto -->
- fecha: 2026-07-28 · actor: orchestrator
- alcance: [[features/009-self-application|009-self-application]]

## Contexto

Encontrado el 2026-07-28 entregando 008-P1. Secuencia: el delta review devuelve repair_required con hallazgos nuevos, se reparan, y como todos son <= medium se usa record-repair --skip-delta, que es la salida que el propio comando ofrece (feature-state.py:1899 solo exige que ningun hallazgo reparado sea critical o high). Eso mueve la fase a PACKAGE_TESTING sin registrar un delta review nuevo, asi que delta_reviews[-1].verdict sigue siendo repair_required. Pero package_accept_ready:443 exige que el ultimo delta review sea pass. Y LEGAL_TRANSITIONS:41-54 no tiene ninguna arista de PACKAGE_TESTING ni de PACKAGE_RUNTIME_QA hacia DELTA_REVIEW. El paquete queda en un estado donde accept-package falla siempre.

## Decisión

Se sale por el unico camino legal que existe: PACKAGE_RUNTIME_QA -> PACKAGE_REPAIR -> DELTA_REVIEW -> registrar el delta review que pasa -> PACKAGE_TESTING -> PACKAGE_RUNTIME_QA -> aceptar. Funciona, pero es un rodeo que fabrica una transicion a reparacion sin reparacion. Se registra como hallazgo de 009-self-application: es la misma clase que los otros -el arnes ofrece un atajo y no soporta su consecuencia-.

## Consecuencias

009 crece de nuevo: o --skip-delta registra ademas un delta review que pasa con la justificacion del atajo, o package_accept_ready deja de mirar el ultimo delta review cuando la reparacion posterior fue waived (el campo delta_waived ya existe y se usa en :442 para otra cosa). Mientras tanto, todo paquete que use --skip-delta despues de un delta review con hallazgos paga el rodeo.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
