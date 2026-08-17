# Error de secuencia: despache un agente contra main y commitee sobre main mientras trabajaba

<!-- notas:auto -->
- fecha: 2026-08-17 · actor: orchestrator

## Contexto

Despache un implementer para cerrar cuatro pendientes de los spawners, con la instruccion 'empeza con git merge --ff-only main'. En ese momento main estaba en 2f199d5, SIN D5 integrado. Mientras el agente trabajaba, el orquestador commiteo bec3dcf, que integra D5 entero. El agente verifico con grep que D5 no existia -era cierto en su base- y lo reimplemento desde cero, ademas de sus cuatro arreglos. Resultado: dos implementaciones divergentes del mismo paquete, con ADR-0056 duplicado y disenos distintos -_fetch_vault_block por spawner en main contra context_pack.vault_block compartido en la suya-, y 728 lineas de trabajo que hay que reconciliar en vez de integrar.

## Decisión

La base de D5 de main se queda: ya paso review de seguridad y su fence resistio los ocho payloads. De la version del agente se portan sus cuatro arreglos, que es lo que main no tiene: scrub de SET_AGENTS_PROJECT en los tres carriles restantes, vault por stdin en pi, y doctrina compartida en Global/_shared. El cuarto -degradacion honesta- se REHACE sobre la arquitectura de main en vez de portarse, porque portarlo reemplazaria codigo ya revisado. El agente hizo lo correcto al parar y reportar la divergencia en vez de forzar un merge; el error fue del orquestador.

## Consecuencias

Regla que faltaba y queda escrita: NUNCA despachar un agente con instruccion de basarse en main si el orquestador planea commitear sobre main durante esa ventana. O se le da un commit fijo como base -git merge --ff-only <sha>-, o se espera a que el agente cierre antes de commitear. Lo segundo cuesta latencia; lo primero no cuesta nada y es lo que corresponde. El costo medido de no hacerlo fueron 728 lineas de trabajo correcto que hay que portar a mano en vez de aplicar, y un ADR duplicado.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
