# Propuesta — Despacho adaptativo (el "fork funcional" de gentle-ai)

## El problema, en una frase

El arnés ya sabe QUÉ modelo conviene para cada tarea (núcleo de ruteo aceptado en la feature 003), pero el
orquestador delega con modelos fijos por rol: una auditoría chica cuesta lo mismo que una grande y una tarea
crítica no puede subir de modelo sola.

## Qué vamos a construir

Que las delegaciones de los roles caros pasen por el cerebro de ruteo: la tarea se clasifica (clase +
riesgo, con derivación mecánica donde se puede y riesgo que solo puede SUBIR), el router elige nivel
(rápido / balanceado / frontera) y modelo dentro del catálogo curado, y el subagente se lanza con ese
modelo — con cada despacho de escritura autorizado y registrado en el ciclo SQLite existente.

Investigamos gentle-ai a fondo: upstream NO elige modelos en runtime (fija modelo por agente en la
instalación; el humano cambia perfiles a mano). Nuestro diseño toma su matriz costo/calidad curada y sus
variantes por nivel, y agrega la elección automática por tarea.

## Alcance honesto (qué toca y qué no)

- **Runtimes afectados**: OpenCode (carril P2, tu entorno diario de orquestación) y Pi (carril P3). Claude
  Code y Codex mantienen sus modelos estáticos por rol — sin cambios en esta feature.
- **Roles ruteados**: los cinco caros — security-auditor, package-reviewer, delta-reviewer, implementer,
  debugger. El resto conserva su modelo fijo.
- **Nivel barato**: en esta feature usa solo proveedores ya auditados (gpt-5.4-mini / gpt-5.6-luna /
  haiku). Sumar los proveedores realmente baratos (glm/kimi/deepseek vía Zen-Go) es una feature corta
  posterior — decisión tuya del 26/07.
- **Velocidad**: las decisiones de solo-lectura tardan <1s con el cache de autenticación caliente (hoy
  ~14s siempre); la primera decisión de la sesión, o tras 5 minutos, paga los probes frescos. Las
  decisiones que AUTORIZAN escritura siempre re-verifican en fresco al proveedor elegido — eso cuesta
  unos segundos por despacho de writer, a cambio de nunca autorizar con una sesión vencida.
- **Benchmarks**: fuera de alcance; la curación del catálogo es manual con telemetría del
  `--routing-report`.

## Las tres entregas

1. **Cerebro consumible (P1)** — ADR de las dos enmiendas aprobadas, catálogo por niveles, selección
   sensible al riesgo, CLI de despacho (`--route-decide` / `--route-dispatched` / `--route-terminal` /
   `--routing-open-runs`) con cache de probes.
2. **Carril OpenCode (P2)** — variantes `@fast/@balanced/@frontier` de los cinco roles, generadas desde la
   config con un gate de build que garantiza que la variante ejecuta EXACTAMENTE el modelo decidido; el
   orquestador consulta la decisión y elige la variante (modo degradado explícito si el router no está).
3. **Carril Pi (P3, condicionado a un spike)** — la elección dinámica real: extensión propia sobre el SDK
   de Pi que lanza el subagente con el modelo/esfuerzo exactos por llamada. Antes de implementarlo, un
   spike corto verifica las tres incógnitas (auth observable, effort por sesión, mapeo de modelos); si
   algo da NO, volvemos con la evidencia y decidís.

## Qué NO cambia

SDD→BDD→implementar⇄auditar→regresión, gates deterministas, estado durable, narración, separación de
deberes y presupuestos quedan intactos. El ruteo decide el MODELO de cada instancia; las reglas de calidad
siguen siendo las de siempre.

## Riesgos honestos

- Ningún runtime de spawn acepta modelo por parámetro: P2 usa variantes con nombre; P3 una extensión
  propia sobre el SDK de Pi (documentado upstream, verificado por el spike antes de construir).
- Catálogo mal curado = decisiones malas; se mitiga con telemetría y ediciones de 1 archivo.
- El cache de autenticación se limita a filtrar candidatos; la autorización siempre verifica en fresco al
  proveedor elegido.
