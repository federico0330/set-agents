# Cuarto stall de infraestructura de la sesion: el patron es de agentes mutadores de corrida larga, no de un encargo puntual

<!-- notas:auto -->
- fecha: 2026-08-12 · actor: orchestrator
- alcance: [[features/020-honest-dashboard|020-honest-dashboard]] · [[features/020-honest-dashboard/P2-anclas-verificables|P2-anclas-verificables]]

## Contexto

run1_c5214efc4b0d73beea87d3e922b6ec85 (implementer de P2) murio con 'Agent stalled: no progress for 600s' sin dejar nada: verificado que no existen ni check_anchors.py ni el archivo de evidencia, y git status no muestra nada nuevo. Es el CUARTO de la sesion -- antes murieron el implementer de 019/P5 (relanzado, completo), el repair de 019/P5 (relanzado, completo) y otro repair. Los cuatro fueron agentes mutadores de corrida larga; ninguno reintento fallo por la tarea en si.

## Decisión

Se relanza una vez, como en los casos anteriores, con la mitigacion que ya funciono dos veces: escribir el archivo de evidencia en el primer minuto y guardar a disco despues de cada tramo, para que un corte deje algo utilizable. Pero se registra el patron como observacion de infraestructura del harness, no como accidente: cuatro stalls en una sesion sobre agentes mutadores largos es senal, no ruido. Si este relanzamiento tambien muere, P2 se parte en dos encargos mas chicos (gramatica+comando por un lado, enganche+correccion de anclas por otro) en vez de intentar un tercero completo.

## Consecuencias

P2 tiene un relanzamiento disponible. El patron queda anotado para que Federico lo vea: puede ser un limite del entorno de ejecucion que convenga mirar aparte de esta feature.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
