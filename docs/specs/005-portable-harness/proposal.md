# Propuesta ejecutiva — Harness portable, bóveda de contexto obligatoria y menú interactivo

## El problema y su impacto en el negocio

Hoy el sistema que elige automáticamente qué modelo de IA usar para cada tarea (una mejora ya entregada y en
producción) sólo funciona si uno para de trabajar exactamente dentro de la carpeta original donde se instaló
por primera vez. En cualquier otro proyecto propio — otra carpeta, otra máquina, otro cliente — esa selección
inteligente de modelo simplemente no está disponible: el sistema no la reconoce y listo, sin aviso claro de
por qué. Esto significa que el beneficio ya pagado (mejor modelo para cada tipo de tarea, con el costo y la
calidad correspondientes) sólo se aprovecha en un lugar, cuando el valor real está en poder llevarlo a
cualquier proyecto.

Además, hay una segunda pieza — un sistema de notas y contexto pensado para que cualquier persona (o
cualquier asistente de IA) entienda rápido "qué es este proyecto, qué se decidió y por qué" — que hoy es
opcional, se activa manualmente, y una vez activado NADIE lo vuelve a leer: se escribe pero no se usa. Peor
todavía: se detectó que las notas reales de cuatro proyectos activos (incluyendo el propio negocio) quedaron
"huérfanas" desde hace unos días — viven en un solo lugar, sin respaldo, y el mecanismo que las mantenía
sincronizadas dejó de funcionar sin que nadie lo notara.

Por último, el menú de configuración del sistema es hoy "escribí un número y apretá enter" — funcional, pero
lejos de la experiencia de un producto terminado.

## La solución propuesta, en una idea

Convertir tres piezas que hoy dependen de "estar parado en la carpeta correcta" o de "acordarse de activar
algo a mano" en comportamiento automático y a prueba de errores: (1) que la selección inteligente de modelo
funcione en cualquier proyecto propio, en cualquier computadora, sin pasos manuales adicionales; (2) que el
sistema de notas se active solo desde el primer minuto de cada proyecto nuevo, se lea automáticamente antes
de trabajar (no sólo se escriba), y que las cuatro carpetas de notas ya existentes se recuperen de forma
segura, sin perder ni un archivo; (3) que el menú de configuración se sienta como una aplicación moderna, con
flechas del teclado en lugar de números, sin agregar ninguna dependencia externa que pueda romperse en otra
computadora.

## Alcance

**Incluido:**

- Que cualquier proyecto propio, en cualquier computadora, con el sistema instalado en cualquier ubicación,
  obtenga automáticamente la selección inteligente de modelo — validado con una prueba explícita: alguien
  que nunca usó el sistema lo instala desde cero en una carpeta nueva y funciona a la primera.
  Con una garantía adicional: los datos de un proyecto (por ejemplo, quién revisó el trabajo de quién) nunca
  se mezclan con los de otro proyecto, aunque compartan la misma computadora.
- Instalación asistida de la aplicación de notas (Obsidian) en Windows, Mac y Linux, siempre pidiendo
  confirmación antes de cualquier paso que requiera permisos de administrador — nunca en silencio.
- Activación automática del sistema de notas para todo proyecto nuevo, y lectura automática de ese contexto
  antes de que cualquier asistente de IA empiece a trabajar — hoy eso no pasa, sólo se escribe.
- Recuperación segura de los cuatro proyectos con notas huérfanas: primero una simulación que muestra qué se
  movería sin tocar nada, después una confirmación explícita, y sólo entonces el movimiento real — con copia
  de seguridad verificada antes de borrar cualquier original. El contenido recuperado NO se sube
  automáticamente al control de versiones de cada proyecto: eso queda como decisión del usuario, proyecto por
  proyecto, más adelante.
- Un chequeo de salud que detecta y (con permiso explícito) repara el problema real que causó la pérdida de
  sincronización, para que no vuelva a pasar desapercibido.
- Un menú de configuración con navegación por flechas, sin agregar ninguna librería externa (para no
  arriesgar la instalación en otras computadoras).
- Si la computadora no tiene la aplicación de notas instalada (por ejemplo, un servidor sin interfaz
  gráfica), el sistema de archivos de notas simple sigue funcionando igual — sólo se avisa que falta el
  visor gráfico, nunca se bloquea nada por eso.

**Explícitamente fuera de alcance:**

- No se toca qué modelo de IA se elige para cada tarea ni la lógica de esa decisión — eso ya está entregado
  y funcionando; esta propuesta sólo la lleva a cualquier proyecto.
- No se migran ni reparan bases de datos de selección de modelo de otras personas o de otras computadoras —
  sólo la propia, en la propia máquina.
- No se agregan complementos de la comunidad a la aplicación de notas (por confiabilidad offline); sólo las
  funciones núcleo (buscar, ver relaciones entre notas, etc.).
- El modo "notas privadas, guardadas fuera del proyecto" (elegido activamente por el usuario en el pasado)
  se sigue permitiendo tal cual — esta propuesta sólo agrega la manera de distinguirlo automáticamente del
  caso "se rompió el enlace por accidente", para no confundir uno con el otro.
- No se toca la sincronización en la nube de las notas — siguen siendo archivos locales.
- No hay mouse ni scroll en el nuevo menú — se navega con flechas del teclado, que alcanza para un menú de
  esta simpleza.
- La instalación real, con interfaz gráfica, en Mac y Windows queda como un paso de verificación manual —
  no se puede automatizar una instalación gráfica real desde este tipo de entorno; se prueba de forma
  automática todo lo que SÍ se puede probar así (la lógica de qué comando ejecutar en cada sistema
  operativo) en las tres plataformas.
- No se agrega ninguna dependencia de software de terceros al menú interactivo.

## Supuestos

- El usuario sigue teniendo la última palabra sobre cualquier paso que pida permisos de administrador: nunca
  se ejecuta nada de ese tipo sin mostrar el comando exacto y pedir confirmación.
- Los cuatro proyectos con notas huérfanas siguen existiendo, en el mismo estado, hasta el momento de
  ejecutar la recuperación (se revalida justo antes de tocar cualquier archivo).
- La computadora donde se instala tiene Python 3.11 o superior — el único requisito que el sistema ya exige
  hoy; no se suma ningún requisito nuevo.

## Riesgos y mitigación

| Riesgo | Mitigación |
|---|---|
| Los datos de notas de los cuatro proyectos reales son la única copia que existe — un error al moverlos sería irrecuperable. | Simulación previa obligatoria, copia de seguridad verificada ANTES de borrar cualquier original, y confirmación explícita del usuario antes de tocar datos reales. |
| Que la selección de modelo de un proyecto se filtre o se confunda con la de otro al compartir computadora. | Cada proyecto queda identificado de forma única e independiente del path o del nombre de carpeta; ante cualquier duda, el sistema NIEGA el cruce entre proyectos en lugar de permitirlo. |
| Que el mecanismo de "instalación con permisos de administrador" quede escondido en un menú con navegación de flechas y el usuario no vea bien qué está aprobando. | El menú siempre vuelve a un modo de pantalla normal y legible antes de mostrar cualquier pedido de confirmación de este tipo — nunca se pide una confirmación sobre una pantalla en modo especial. |
| Que una actualización futura del sistema quede incompatible con datos de selección de modelo generados antes de esta mejora. | Documentado explícitamente: una versión anterior del sistema simplemente no lee la base de datos nueva y lo informa con claridad, en vez de corromper datos — comportamiento ya usado hoy para casos similares. |

## Fases de entrega (esfuerzo relativo, no fechas)

1. **Portabilidad del núcleo** (esfuerzo: L) — que cualquier proyecto, en cualquier computadora, obtenga la
   selección inteligente de modelo, con la garantía de que los proyectos nunca se mezclan entre sí.
2. **Bóveda de notas obligatoria** (esfuerzo: L) — activación automática, lectura automática por parte de
   los asistentes de IA, recuperación segura de los cuatro proyectos afectados, e instalación asistida en
   los tres sistemas operativos.
3. **Menú interactivo** (esfuerzo: M) — reemplazo del menú numérico por navegación con flechas, sin agregar
   dependencias externas.

Cada fase se entrega, se valida y se aprueba antes de pasar a la siguiente.

## Criterios de éxito medibles

- Una persona que nunca usó el sistema puede instalarlo desde cero en una carpeta cualquiera, en una
  computadora cualquiera, y la selección inteligente de modelo funciona a la primera — sin pasos manuales
  extra ni ayuda del equipo que lo construyó.
- Cero mezcla de datos entre proyectos distintos que comparten la misma computadora, verificado con una
  prueba automática específica para ese caso.
- Los cuatro proyectos con notas huérfanas quedan recuperados con el 100% de sus archivos intactos (ninguno
  perdido, ninguno duplicado, ninguno corrompido) y visibles de nuevo en la aplicación de notas.
- Cualquier asistente de IA que empiece a trabajar en un proyecto lee automáticamente su contexto (qué es el
  proyecto, decisiones previas, pendientes) sin que nadie se lo tenga que pedir.
- El menú funciona con flechas de teclado en Windows, Mac y Linux, y sigue funcionando en modo texto simple
  (sin colores ni animaciones) cuando se usa desde un script o una automatización, exactamente como antes.
- Ninguna instalación con permisos de administrador ocurre sin que el usuario vea el comando exacto y lo
  confirme explícitamente — en el menú nuevo exactamente igual que en el actual.
