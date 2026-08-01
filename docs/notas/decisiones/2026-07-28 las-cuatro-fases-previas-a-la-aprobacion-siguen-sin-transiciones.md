# PHASES conserva cuatro fases que LEGAL_TRANSITIONS no conoce, y AC-13 no las convierte en transiciones reales

<!-- notas:auto -->
- fecha: 2026-07-28 · actor: orchestrator
- alcance: [[features/009-self-application|009-self-application]] · [[features/009-self-application/P2-state-machine-required|P2-state-machine-required]]

## Contexto

PHASES:22-39 contiene REQUIREMENTS, SPEC_DRAFT, SPEC_CHALLENGE y USER_APPROVAL. LEGAL_TRANSITIONS:41-54 no tiene entrada para ninguna, ni como clave ni como destino, asi que ninguna es alcanzable ni abandonable: un estado que las tuviera seria un callejon sin salida, y validate_state:247 igual las acepta porque solo chequea pertenencia a PHASES.

## Decisión

AC-13 no las convierte en transiciones reales. Volverlas alcanzables romperia todo flujo y todo test vigente, y no comprarian lo que aparentan: una transicion registrada a USER_APPROVAL es tan indemostrable como la etiqueta que ya estaba. Lo que se hizo en cambio es exigir la unica evidencia verificable que existe - el sha256 del spec aprobado - mas la atribucion obligatoria de --approved-by, con el precedente de reopen --authorized-by.

## Consecuencias

El ciclo previo a la aprobacion sigue viviendo fuera de la maquina de estados, en el spec y en el chat. Si algun dia se quiere adentro, el costo real no es agregar entradas al diccionario sino definir que artefacto prueba cada fase; sin eso solo se agregan mas afirmaciones sin evidencia, que es el defecto que este paquete existe para cerrar.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
