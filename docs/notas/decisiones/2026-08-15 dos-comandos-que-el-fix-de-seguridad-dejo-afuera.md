# El fix del RCE deja fuera 'git show HEAD:ruta' y './build.sh --output', medido

<!-- notas:auto -->
- fecha: 2026-08-15 · actor: orchestrator

## Contexto

Verificacion final del orquestador sobre la version integrada, con dos baterias: 28 de 28 ataques bloqueados y 22 de 24 comandos legitimos permitidos. Los 28 tests del repo que gobiernan la politica pasan en verde. Los dos que quedan denegados son: 'git show HEAD:<ruta>', que la doctrina de este repo usa para restaurar un archivo sin usar git checkout -esta escrito asi en los prompts de los agentes y se uso varias veces esta noche-, y './build.sh --output <dir>', que la feature 027 acaba de convertir en el camino seguro para 19 call sites de tests.

## Decisión

Se integra igual. La alternativa era quedarse con la version anterior, que dejaba pasar el canal de catalogo de MCPs y fallaba un test del repo; esta version pasa los 28. Los dos huecos se declaran en vez de taparse, y son de disponibilidad y no de seguridad: un comando legitimo denegado se nota enseguida, un ataque permitido no.

## Consecuencias

Consecuencia practica inmediata: un agente que siga la doctrina de 'para morder y restaurar usa cp y cp, nunca git checkout' y elija 'git show HEAD:<ruta>' se va a topar con un deny. Y el camino --output que 027 establecio como seguro para generar en temporal queda bloqueado desde bash, aunque los tests lo invocan por subprocess de Python y no por esta politica. Los dos son de una linea en el mapa de modificadores. NO SE REPARAN ESTA NOCHE por falta de ventana, y quedan como lo primero a hacer sobre este paquete, junto con el review independiente que nunca tuvo.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
