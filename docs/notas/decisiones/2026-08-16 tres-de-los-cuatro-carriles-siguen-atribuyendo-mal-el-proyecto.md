# El arreglo de SET_AGENTS_PROJECT quedo solo en el carril de pi; faltan los otros tres

<!-- notas:auto -->
- fecha: 2026-08-16 · actor: orchestrator

## Contexto

El debugger reparo el defecto en set_agents_spawn.py -carril pi- y encontro que _run_app_cli esta DUPLICADO VERBATIM en los otros tres, con el mismo full_env = dict(os.environ) y el mismo patron routing_cwd: claude_code_spawn.py:574 y :637, codex_spawn.py:300 y :324, opencode_spawn.py:323 y :350. No los toco porque habia un review de seguridad corriendo sobre *_spawn.py, y avisar en vez de tocar fue la decision correcta. Verificado por el orquestador: grep de SET_AGENTS_PROJECT da 3 en set_agents_spawn.py y 0 en los otros tres.

## Decisión

El parche es identico y de tres lineas por archivo, y queda encolado para aplicarse cuando termine la reparacion de D5, que esta trabajando en esos mismos archivos ahora. No se aplica en paralelo: dos agentes editando los cuatro spawners a la vez es como se pierde trabajo. La forma elegida por el debugger se replica tal cual: pasar None en el env para significar 'desasigna esta variable en el hijo', que no cambia la firma de _run_app_cli y por lo tanto no rompe los fakes de tests/test_pi_effort.py y otros modulos fuera de alcance que la mockean con firma exacta.

## Consecuencias

Mientras tanto el harness rutea por cuatro carriles y solo uno atribuye bien: si el orquestador tiene SET_AGENTS_PROJECT en su ambiente -cosa que su propio main() provoca al correr cualquier comando de routing- los spawns por claude-code, codex y opencode siguen persistiendo la identidad del proyecto del padre en vez de la del spawn_cwd. Es el mismo escenario silencioso, en tres cuartas partes de la superficie. El debugger tambien dejo respaldo documental de que el arreglo restaura intencion ya escrita y no inventa semantica: docs/notas/decisiones/2026-07-27 p1-pi-project-cwd-propagation.md dice que el mecanismo de export por entorno es solo compatibilidad y ya no se depende de el, y ADR-0008:275-281 describe el routing_cwd explicito como el cambio minimo para que dispatches.project_key pertenezca al proyecto del usuario.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
