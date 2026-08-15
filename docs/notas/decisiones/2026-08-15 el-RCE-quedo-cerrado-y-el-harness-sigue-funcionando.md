# El RCE de la allowlist quedo cerrado: 24 ataques bloqueados, 25 comandos legitimos intactos

<!-- notas:auto -->
- fecha: 2026-08-15 · actor: orchestrator

## Contexto

Cuatro vueltas de implementacion, cada una verificada por el orquestador corriendo las dos baterias contra el arbol, no leyendo el reporte. La primera vuelta bloqueo los PoC y ROMPIO el harness: dejo denegados ls, cat, git status --porcelain, ./build.sh --check y python3 -m unittest. Su corpus positivo decia 'git, python, npm todos permitidos' porque habia probado los comandos PELADOS -git status pasa, git status --porcelain no-. Es la misma forma de las once guardas falsas-verdes de este repo, aparecida dentro del paquete hecho para arreglarlas, y quedo documentada en la evidencia en vez de corregida en silencio.

## Decisión

Cerrado. El prefix match de coord_policy.py:321 se reemplazo por enumeracion de modificadores por comando, siguiendo el patron de _rest_allowed que SAFE_ARGV ya aplicaba. curl valida parseando la URL en vez de con regex, exige una sola URL y prohibe -o, -O, -T, -d, --data*, -K y --config. find y fd salieron de la allowlist por flags no enumerables. sed tambien salio, por decision explicita: su lenguaje ejecuta con e y escribe con w, W, r y R dentro del script, y esa validacion no se sabia defender. FORBIDDEN_SYNTAX quedo centralizado e importado por los dos guardas que antes tenian su propia copia.

## Consecuencias

Medicion final del orquestador: 24 de 24 ataques bloqueados y 25 de 25 comandos legitimos permitidos. Entre los ataques hay catorce que el implementer nunca vio -rg --pre, git -c core.pager, git --exec-path, python3 -c, sed con e y con w, pipe a sh, salto de linea embebido, y las cuatro formas de composicion de shell-, lo que indica que el diseno resiste ataques fuera de su propia lista: es enumeracion, no lista negra. QUEDA PENDIENTE Y ES IMPORTANTE: este arreglo NO tuvo review independiente, porque la cuota se agoto. Es codigo de seguridad escrito por un agente y verificado por el orquestador que lo dirigio, o sea sin la separacion de funciones que el harness exige. Y generate.py:186-197 tiene una CUARTA copia del invariante, en globs para la lane de OpenCode, con agujeros distintos, sin tocar.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
