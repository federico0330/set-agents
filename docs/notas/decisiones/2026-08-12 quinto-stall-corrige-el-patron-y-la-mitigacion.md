# Quinto stall: el patron no era 'agentes mutadores' y nombrar la herramienta no alcanza

<!-- notas:auto -->
- fecha: 2026-08-12 · actor: orchestrator
- alcance: [[features/021-gates-que-no-mienten-ni-callan|021-gates-que-no-mienten-ni-callan]]

## Contexto

El package-reviewer de 021/P2 murio con 'no progress for 600s' revisando justamente el paquete anti-stall, y esperando la suite -- la condicion exacta que heartbeat-run.py existe para evitar. Sus ultimas palabras fueron 'sigo esperando... chequeo el progreso de la suite sin abusar del polling'. El encargo YA le decia que usara heartbeat-run.py o escribiera a archivo.

## Decisión

DOS CORRECCIONES a caracterizaciones previas del orquestador. (1) El patron NO es 'agentes mutadores de corrida larga': este era read-only. Lo comun a los cinco stalls es ESPERAR UN COMANDO LARGO SIN EMITIR, sea el agente mutador o no. La caracterizacion anterior, registrada en el slug cuarto-stall-de-la-sesion-patron-de-infraestructura, era incorrecta. (2) Nombrar la herramienta en el encargo NO alcanza: el agente la tenia nombrada y aun asi hizo polling. La instruccion tiene que ser imperativa y concreta -- 'corre la suite ASI', con el comando exacto pegado -- no una opcion entre varias.

## Consecuencias

Evidencia a favor del paquete: el problema es real y recurrente, y ahora esta medido en un rol distinto. Evidencia en contra de darlo por resuelto: AC-07 pone la doctrina en spawn-prompt/SKILL.md, que la carga el orquestador al REDACTAR; no hay nada que se la imponga al agente que la recibe. Queda como limitacion conocida a nombrar en el ADR, no como defecto de P2 -- imponerselo al receptor seria otra feature.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
