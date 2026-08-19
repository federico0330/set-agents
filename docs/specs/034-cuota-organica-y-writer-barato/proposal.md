# Propuesta ejecutiva — Gastar menos cuota en lo chico, reservar lo caro para juzgar

Documento para aprobar **como cliente**. El contrato técnico paralelo es
`spec.md`. Mismo alcance, misma lista de lo que no se hace; otro lector.

## El problema y el caso de negocio

Hoy un arreglo de dos archivos y una feature grande pagan el mismo peaje:
ceremonia pesada y el modelo más caro en quien escribe. Las suscripciones
alcanzan menos de lo que deberían, no porque cada pregunta sea enorme,
sino porque el sistema **multiplica** trabajo caro en cambios que no lo
piden.

Eso ya se midió en el trabajo anterior (menú que no congela, una sola
lista de modelos, integración continua en tres sistemas operativos). Ese
trabajo **está cerrado**. Este no lo reabre. Lo que queda es otra palanca:
quién escribe, con qué modelo, y cuándo se enciende el proceso completo.

Un sistema comparable (Gentle-AI) ya demuestra que un cambio chico puede
resolverse en línea, y que quien aplica un parche puede ir en un modelo
barato mientras el diseño y el juicio se reservan. Nadie —ni nosotros ni
ellos— mide hoy qué porcentaje de las escrituras baratas cierran bien a
la primera, ni pone un cupo aparte a las llamadas caras. Eso es el hueco
que esta propuesta cierra.

## La solución, en un párrafo

Tres reglas simples, aplicables en Cursor (el entorno que estás usando) y
en los demás entornos ya instalados: (1) quien **escribe código** arranca
en el modelo más barato o gratuito que todavía pueda editar y verificar;
si esa pasada no cierra, hay **un** intento caro de reparación por lote
de trabajo, y el segundo fallo te lo trae a vos — no hay cascada
automática; (2) un cambio de una a tres archivos, sin tocar plata,
identidad, migraciones ni contratos públicos, se hace y se registra: no
abre el proceso completo de especificación y revisión en panel; (3) en
Cursor, cada rol usa el modelo que le corresponde (el escritor el barato,
quien revisa otro distinto), en lugar de heredar todos el que esté
elegido en la sesión. Se verá, en el reporte de consumo, qué porcentaje
del escritor barato cierra a la primera y cuántas llamadas caras quedan
en el cupo.

## Alcance

**Incluido**

- Escritor en modelo barato/gratis que aún pueda hacer el trabajo
  (editar, correr la verificación local). Una iniciativa nueva arranca
  siempre en ese nivel barato, no en la variante “rápida” cara.
- Una sola reparación cara por lote si el barato falla (un intento
  excepcional, sin cambiar el modelo habitual de quien repara). El
  segundo fallo se detiene y te consulta.
- Si en **dos lotes seguidos** de la misma iniciativa el barato no cierra
  a la primera, el lote siguiente usa el modelo más pesado **en esa
  pasada**. La reparación cara del mismo lote no cuenta como un segundo
  strike. Una iniciativa nueva vuelve a arrancar barato. No se usa un
  porcentaje inventado.
- Cupo aparte de llamadas a modelos caros: 4 por lote, 16 por iniciativa.
  Llenar el cupo para y te consulta. No se agranda el techo de “cuántas
  personas virtuales pueden intervenir” para disimularlo.
- Quien juzga (revisión, desafío de spec, arquitectura, veredicto) puede
  seguir en modelo caro. El ahorro es el volumen de quien escribe, no
  sacar al juez.
- Quien escribe la spec de producto puede usar modelo caro: es juicio,
  no pala.
- Cambio chico (1–3 archivos) sin señales de riesgo: se implementa, se
  verifica, se deja rastro **sin** abrir un expediente. Si esa
  verificación falla, se reintenta en el acto o se escala con una razón
  concreta; no hay “reparación cara” de lote porque no hay lote. El
  proceso completo queda para cuando hay riesgo concreto o cuando vos
  lo pedís.
- En Cursor, modelo fijado por rol (quien escribe y quien repara, el
  barato; quien revisa, otro). Una pasada cara (reparación o subida de
  nivel) usa el modelo pesado **solo en esa llamada**, sin cambiar el
  modelo habitual del rol.
- Un número visible: porcentaje de escrituras baratas que cierran a la
  primera, más el cupo caro usado.

**Explícitamente fuera de alcance**

- No se agregan dieciséis entornos nuevos de agentes (Windsurf, Kimi,
  Gemini, etc.). Nos quedamos con los cinco que ya existen.
- No se copia el sistema de “recibo de revisión” ni el interruptor de
  pre-commit de Gentle-AI. Ya hay revisión y verificaciones de
  repositorio.
- No hay instalador tipo `curl` / Homebrew / Go para terceros en este
  corte.
- No se arma un banco de 36 recorridos de operador copiado de Gentle-AI.
- No se agregan perfiles tipo “tecla Tab cambia el paquete de modelos”
  en OpenCode. El default barato queda en la configuración nuestra.
- **No se instala Engram.** Usás Obsidian como contexto. El vault del
  proyecto (notas en `docs/notas/` más el vault) es obligatorio y es la
  memoria que ya decidimos. Si un ayudante arranca sin leer esas notas,
  eso es un defecto del vault obligatorio — se corrige ahí — no una
  razón para copiar otro producto de memoria.
- No se reabre el trabajo del menú, de las listas de modelos, ni de la
  integración continua recién cerrada.
- No se bajan, se saltean ni se borran pruebas para hacer pasar el
  cambio de política.

## Supuestos

- El inventario vivo de modelos tiene al menos una opción barata o
  gratuita que todavía puede editar y verificar. Si el inventario no
  tiene ninguna, el trabajo se detiene y te lo muestra; no se inventa
  un nombre de modelo.
- Cursor acepta fijar un modelo distinto por rol (el producto lo
  documenta; hay que medir los identificadores reales al implementar).
- El vault de Obsidian sigue siendo el lugar donde vive el contexto.
  Esta propuesta no lo reemplaza.

## Riesgos y mitigación

| riesgo | mitigación |
|---|---|
| El modelo barato no puede hacer el trabajo (no edita, no verifica) | No se elige a ciegas: tiene que demostrar que puede. Si no hay ninguno, se para y se informa |
| Fijar modelos en Cursor con nombres que Cursor no reconoce | Se miden los nombres reales antes de escribirlos; no se vuelve en silencio al “todos heredan” |
| El cupo caro ahoga una revisión legítima | 4 por lote deja revisión + auditoría + veredicto + una reparación cara; el quinto para y pregunta |
| Un arreglo chico se cuela igual en el proceso pesado | Hay una prueba que **falla** si un cambio de 1–3 archivos entra al proceso pesado sin una razón de riesgo escrita |
| Copiar Engram “por las dudas” | Fuera de alcance, con la razón del vault |

## Fases de entrega (esfuerzo relativo, no fechas)

| fase | qué entrega | esfuerzo |
|---|---|---|
| 1 | Los cambios chicos dejan de abrir el proceso pesado; queda rastro | M |
| 2 | Quien escribe arranca barato; una reparación cara; el test que hoy obliga al modelo caro-por-nombre se reescribe (no se borra) | M |
| 3a | Se ve el porcentaje de acierto a la primera y el cupo de llamadas caras | S |
| 3b | En Cursor, cada rol con su modelo; quien revisa no usa el mismo que quien escribe | M |

3a y 3b pueden avanzar juntas después de la fase 2. Total del corte:
más cerca de **L** por la suma, no porque una sola fase sea enorme.

## Criterios de éxito medibles

1. Un arreglo de una a tres archivos, sin señales de riesgo, se cierra
   con implementación + verificación + rastro, **sin** haber abierto el
   proceso completo.
2. Quien escribe usa, por defecto, un modelo barato o gratuito capaz de
   hacer el trabajo. Si falla, hay **una** reparación cara y no dos. Dos
   lotes seguidos sin cierre a la primera suben el siguiente; esa
   reparación del mismo lote no cuenta como segundo strike.
3. El reporte de consumo muestra el porcentaje de escrituras baratas que
   cerraron a la primera, y cuántas llamadas caras se usaron contra el
   cupo (4 por lote, 16 por iniciativa).
4. En Cursor, el escritor y el revisor no quedan en el mismo modelo
   salvo aviso explícito de que no había otra familia disponible.
5. Las pruebas de independencia entre quien escribe y quien revisa
   siguen en pie. Ninguna prueba se borró para hacer pasar esto.
6. El trabajo anterior (menú, integración continua) sigue cerrado.

## Qué se pide aprobar

Este recorte, estos noes, estos números (1 salvage, 2 fallos seguidos
para subir de nivel, cupo 4/16, 1–3 archivos = camino corto). Con la
aprobación se implementa; un cambio de recorte es otra decisión, no un
ajuste silencioso.
