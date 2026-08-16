# Defecto vivo: un spawn hijo atribuye su trabajo al proyecto del padre, no al que se le pidio

<!-- notas:auto -->
- fecha: 2026-08-16 · actor: orchestrator

## Contexto

Root-cause de una contaminacion entre tests que resulto ser un defecto de produccion. Cadena de tres eslabones, medida: set_agents_app.py:4141 exporta SET_AGENTS_PROJECT al os.environ del proceso cuando main() resuelve la raiz -correcto para un CLI real, donde muere con el proceso-; set_agents_spawn.py:363 hace full_env = dict(os.environ) al lanzar el hijo; y project_identity.py:56 le da a esa variable PRECEDENCIA sobre el descubrimiento por cwd. Resultado: route_and_spawn recibe spawn_cwd justamente para que el hijo descubra el proyecto del usuario, y el hijo lo ignora porque hereda la variable del padre. El diff de estado observable a traves del test contaminador fue de UN solo delta: SET_AGENTS_PROJECT de None a la raiz del repo. Por eso el manifiesto de disco, sys.modules y los globals de modulo daban todos limpios.

## Decisión

Arreglo autorizado en produccion, opcion mas especifica gana: cuando route_and_spawn recibe spawn_cwd explicito, _run_app_cli saca SET_AGENTS_PROJECT del env del hijo o la fija a la raiz descubierta desde ese cwd. Se descarto la alternativa de que main() deje de escribir en os.environ global: es mas limpia conceptualmente pero toca superficie compartida por todo el harness y no habia ventana para revisar ese radio. Del lado de los tests, el arreglo va en el test que ensucia -patch.dict sobre os.environ mas una asercion propia-, no en la victima, para que la proxima regresion se reporte en el archivo culpable y no en una asercion tres modulos despues.

## Consecuencias

El escenario de falla en produccion es concreto y silencioso: cualquier orquestador que tenga SET_AGENTS_PROJECT exportado -cosa que su propio main() provoca al correr un comando de routing- hace que TODOS sus spawns hijos persistan la identidad del proyecto del padre. Corrompe el project_key de las filas de dispatches, que es justo lo que el test victima existe para proteger. Y la leccion de metodo: tres capas de sonda -disco, sys.modules, globals de modulo- dieron limpio porque el canal era el entorno heredado, que ninguna miraba. Un diff de os.environ completo tendria que ser parte del kit basico de diagnostico de aislamiento, junto al de sys.modules que ADR-0051 ya establecio.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
