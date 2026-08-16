# El fix del RCE queda commiteado pero NO instalado: esa decision es de Federico

<!-- notas:auto -->
- fecha: 2026-08-15 · actor: orchestrator

## Contexto

Tras commitear 8091b0b, check-drift.sh reporta 12 archivos gestionados que difieren entre el repo y la instalacion en ~. Entre ellos estan coord_policy.py, claude_local_gate_guard.py y claude_release_guard.py, o sea la politica de comandos nueva. Instalar cerraria el RCE en la maquina de Federico ahora mismo.

## Decisión

NO se instala. Instalar escribe en ~ una politica de seguridad que NO tuvo review independiente -la cuota se agoto antes-, y que ademas ya tiene dos huecos de disponibilidad conocidos y medidos: git show HEAD:<ruta> y ./build.sh --output quedan denegados. Es una mutacion del entorno del usuario, basada en codigo sin revisar, hecha mientras duerme. El RCE lleva meses vivo en el repo publico, asi que unas horas mas no cambian el riesgo de forma material, y el costo de equivocarse instalando es que Federico se despierte con herramientas rotas y sin saber por que.

## Consecuencias

Queda como la primera decision de la manana, y tiene tres caminos: instalar tal cual y aceptar los dos huecos; pedir el review independiente primero y despues instalar; o reparar los dos huecos -son una linea cada uno en el mapa de modificadores- antes de instalar. El comando es ./build.sh --install --yes, y deja backup con rotacion. Mientras tanto la instalacion vigente sigue teniendo la politica vulnerable, lo cual esta declarado y no disimulado.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
