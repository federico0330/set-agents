# CRITICO: coord_policy.allowed() es un prefix match, y desde el rol read-only se ejecuta codigo arbitrario

<!-- notas:auto -->
- fecha: 2026-08-15 · actor: orchestrator

## Contexto

Auditoria de seguridad pedida por Federico, con PoC EJECUTADO que creo archivos reales. coord_policy.py:321 hace re.fullmatch(pattern + r'.*', command), asi que cada una de las 23 entradas de SAFE se convierte en 'este prefijo y despues lo que sea'. FORBIDDEN_SYNTAX solo bloquea metacaracteres de shell, no flags. Varios binarios permitidos ejecutan comandos por flag. Verificado creando archivos: 'fd . -X touch pwned_fd', 'bat --pager "sh -c ..."', 'find . -exec touch ... +', 'rg --hostname-bin ./hb.sh', y 'find . -delete'. Los guardas existentes fallan por tres razones medidas: --exec exige doble guion y find usa uno; -x no tiene IGNORECASE y fd usa -X; y --pager y --hostname-bin no estan en ninguna lista. SEC-002 es peor: curl acepta multiples URLs y multiples -o en una invocacion, y --output esta prohibido pero -o NO. PoC ejecutado: 'curl -s http://localhost:1/ file:///etc/hostname -o /dev/null -o exfil.txt' leyo /etc/hostname. Con la misma forma pasan la exfiltracion de ~/.claude/.credentials.json a un host externo y la SOBRESCRITURA de ~/.claude/hooks/coord_policy.py, o sea el agente puede reescribir la guarda que lo contiene. Todo esto desde el rol coord-ro, que el repo documenta como read-only y deny-by-default, sin escape a ask: claude_bash_guard es un deny binario, asi que lo que la politica acepta se ejecuta EN SILENCIO.

## Decisión

Se abre feature 030 de seguridad y se repara esta noche, con paquete y review independiente. No se parchea agregando -X, --pager y --hostname-bin a FORBIDDEN_OPTIONS: eso seria exactamente la guarda falsa-verde numero doce, porque el defecto no son esos tres flags sino el prefix match. El arreglo es eliminar el '+ r".*"' y hacer que SAFE camine argv completo con modificadores enumerados por comando, que es la disciplina que SAFE_ARGV ya aplica. Un comando cuyo conjunto de flags no se puede enumerar -find, fd, bat, rg, curl- no pertenece a una allowlist de ejecucion silenciosa.

## Consecuencias

El repo es PUBLICO y esta pensado para que terceros lo instalen. La cadena completa es: una nota del vault, o el reporte de un subagente comprometido, llega al prompt del orquestador -que por doctrina lee contenido no confiable en cada turno via --context- y de ahi a ejecucion de codigo en la maquina de quien instalo el harness. Contramedida de deteccion que hoy no existe: allowed() no deja rastro de un ALLOW, solo de un deny, asi que un comando aceptado es invisible en narrative-log.jsonl.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
