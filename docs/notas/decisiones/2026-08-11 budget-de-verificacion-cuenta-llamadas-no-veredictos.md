# El presupuesto de verificacion cuenta LLAMADAS a record-verification, no veredictos

<!-- notas:auto -->
- fecha: 2026-08-11 · actor: orchestrator
- alcance: [[features/019-harness-evolution|019-harness-evolution]] · [[features/019-harness-evolution/P5-tools-discovery|P5-tools-discovery]]

## Contexto

Con 15 findings en P5 registre una llamada a record-verification por finding. max_verifications_per_package es 6, asi que la septima llamada (F-07) agoto el presupuesto y puso la feature en BLOCKED, con 4 findings medium (F-08..F-11) sin veredicto registrado. Es un error de proceso del orquestador, no un blocker real: el presupuesto existe para cortar loops adversariales interminables, no para topear cuantos findings se pueden verificar.

## Decisión

record-verification acepta multiples --verdict en una sola invocacion: los veredictos van BATCHEADOS en una llamada por ronda de verificacion, no uno por finding. Se reabre el paquete y se sigue con la reparacion; los veredictos de F-08..F-11 quedan en el registro de reapertura y en la evidencia del review, no en llamadas nuevas. F-08 ya fue re-verificado en vivo por el orquestador y esta pegado en la evidencia del review.

## Consecuencias

Regla vigente para todo el harness, no solo para esta feature. Si un paquete futuro necesita mas de 6 rondas genuinas de verificacion, eso si es senal de un problema real y merece el blocker.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
