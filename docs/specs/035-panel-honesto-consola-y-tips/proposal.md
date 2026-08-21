# Propuesta ejecutiva — Control de calidad verificable, consola mantenible y guía al día

**Para:** el área de IT / quien decide sobre esta herramienta
**Fecha:** 2026-08-20
**Estado:** propuesta para aprobación — **revisión 2** (incorpora la auditoría interna de la
revisión 1: mediciones rehechas, alcance de la corrección de norma ampliado, y la promesa
de "misma salida" convertida en algo verificable)

---

## El problema y su caso de negocio

Esta herramienta coordina asistentes de IA para que trabajen sobre un repositorio con
control de calidad: quien escribe el código no es quien lo aprueba, y cada cambio deja
registro auditable. Ese es el producto. Hoy tiene tres grietas, y una de ellas es
material.

**1. El control de calidad se puede saltear sin que nada avise.**
El sistema clasifica cada tanda de trabajo por complejidad y riesgo. Cuando la
clasificación es media o alta, la regla es que hagan falta **dos** revisiones
independientes: una de código y una de seguridad. Existen dos formas de registrar una
revisión: una las exige a las dos, y la otra —más antigua, y la que se sigue usando en
la práctica— **acepta una sola y no pregunta nada**. El resultado es que una tanda de
trabajo clasificada como riesgosa puede quedar cerrada, aprobada y archivada sin que la
revisión de seguridad haya existido nunca. El registro no miente explícitamente: dice
"una revisión pasó". Simplemente no dice quién. Para una herramienta cuya propuesta de
valor es *el proceso deja rastro*, eso es el defecto más caro del inventario.

Hay una segunda grieta en la misma puerta: esa forma antigua también acepta un "aprobado"
mientras hay observaciones graves sin resolver. La forma nueva lo rechaza. La vieja no.

Y hay un agravante que cambia el tamaño del trabajo: **la norma interna escrita todavía
recomienda la vía insegura.** El documento que define cómo se coordina el trabajo presenta
la forma antigua como el camino normal y las dos revisiones como algo que se hace "cuando
resulta útil" — opcional, a criterio de quien coordina. Cerrar la vía en el software sin
corregir la norma dejaría a la herramienta rechazando exactamente lo que su propio manual
aconseja. Por eso esta entrega incluye la corrección de la norma y el registro formal del
cambio de comportamiento, no sólo el código.

**2. La consola de administración se volvió difícil de mantener.**
El módulo que atiende la línea de comandos (estado, proveedores, herramientas,
integraciones, notas) tiene ~4400 líneas y concentra responsabilidades que no se
relacionan entre sí. Ya hubo un primer intento de dividirlo, que sacó dos piezas
afuera y **dejó documentado, en el propio código, por qué el resto no pudo salir**. El
costo no es estético: cada cambio ahí obliga a leer más de lo necesario y el riesgo de
romper algo lateral es más alto que en cualquier otro archivo del proyecto.

**3. La guía de uso describe una arquitectura que ya no es la real.**
El documento que un nuevo integrante lee primero afirma que sólo uno de los entornos
puede coordinar trabajo y que los otros son "carriles de una sola tarea". Eso dejó de
ser cierto: hoy hay tres entornos capaces de coordinar y cinco entornos soportados,
mientras la guía menciona tres. Además omite, en la sección de medición de consumo, un
entorno que el sistema **sí** mide. Una guía desactualizada no rompe nada de inmediato;
cuesta en tiempo de puesta en marcha y en decisiones tomadas sobre información vieja.

**El caso de negocio en una línea:** la pieza 1 es una brecha de aseguramiento de
calidad que puede dejar pasar trabajo sensible sin revisión de seguridad; las piezas 2 y
3 son deuda que encarece cada cambio futuro. Las tres estaban identificadas y postergadas
por falta de alcance definido. Esta propuesta les da alcance.

---

## La solución propuesta

Cerrar la brecha de control de calidad haciendo que la vía antigua de registro **rechace
explícitamente** los casos que no le corresponden —cuando la clasificación exige dos
revisiones, o cuando hay observaciones graves abiertas— y que indique cuál es la vía
correcta, en lugar de aceptar en silencio —acompañado de la corrección de la norma interna
y del registro formal de ese cambio, para que el software y el manual digan lo mismo—;
completar la división del módulo de consola con una red de seguridad tomada **antes** de
mover una sola línea, comparando salida, mensajes de error y código de resultado de cada
comando antes y después; y corregir la guía de uso junto con el documento que hoy la señala
como desactualizada, para que las dos superficies queden consistentes en la misma entrega.

---

## Alcance

**Incluido**
- La vía antigua de registro de revisiones rechaza los casos que exigen dos revisiones
  independientes, nombrando qué falta y qué comando usar en su lugar.
- La misma vía rechaza un "aprobado" mientras haya observaciones graves abiertas,
  igualando el comportamiento de la vía nueva.
- La clasificación se recalcula cuando el registro histórico no la tiene guardada, con
  criterio conservador: ante la duda, se exige la revisión completa, no la mínima.
- Los registros ya cerrados y archivados no se re-juzgan ni se alteran.
- **Corrección de la norma interna de trabajo** —el documento que hoy recomienda la vía
  insegura— y **registro formal de la decisión** como cambio de comportamiento
  documentado, en la misma entrega que el código.
- División del módulo de consola con red de seguridad previa, comparando **salida,
  mensajes de error y código de resultado** de cada comando antes y después.
- Corrección de la guía de uso y del documento que la referencia.

**Explícitamente NO incluido**
- **Cerrar una segunda vía de elusión ya identificada.** Existe otro punto del sistema
  —una excepción prevista en el registro de reparaciones— por el que un trabajo puede
  avanzar de etapa mientras queda una observación abierta que esa excepción no revisó. Está
  medido, documentado y **queda fuera de esta propuesta a propósito**: cerrarlo tiene su
  propio alcance y su propio riesgo, y meterlo acá ampliaría la entrega sin necesidad. Lo
  que sí se hace es dejarlo **nombrado en el código**, en lugar de dejar un comentario que
  afirme que el problema ya no existe.
- Reorganizar el conjunto de pruebas automatizadas del proyecto (es el contrato de
  regresión; dividirlo pierde cobertura y necesita su propio alcance).
- Ampliar los límites de consumo del sistema. La revisión de seguridad adicional se paga
  con el presupuesto existente; si un caso lo excede, se detiene y se consulta.
- Rediseñar el sistema de notas/conocimiento, ni reemplazarlo por un servicio externo de
  memoria.
- Reabrir decisiones ya cerradas de las tres entregas anteriores.
- Cambiar quién puede aprobar y quién puede desestimar una observación. Esta propuesta
  agrega una obligación de participación; no redistribuye autoridad.
- Reescribir la guía de uso completa. Se corrige lo que es **medidamente falso**, no lo
  que es cuestión de estilo.
- Aprovechar la división del módulo para arreglar otros defectos "de paso". Si aparece
  uno, se registra y se trata aparte.

---

## Supuestos

1. El comportamiento esperado es **rechazar** la vía antigua en los casos exigentes, no
   ampliarla para que acepte varias revisiones. La razón es de presupuesto interno:
   registrar dos revisiones por esa vía consumiría el cupo completo de ciclos de revisión
   de una tanda de trabajo.
2. Un registro histórico sin clasificación guardada **no** significa "sin requisito". Se
   recalcula. Esto no es hipotético, y la medición se rehizo para esta versión de la
   propuesta: de **76 tandas de trabajo** registradas (en 31 procesos), **71 no tienen el
   dato guardado en absoluto** y sólo 5 lo tienen. La versión anterior de este documento
   decía "30 de 31" contando procesos en lugar de tandas; el número correcto es más
   contundente, no menos. Además, 4 tandas tampoco tienen clasificación de complejidad: para
   ésas rige el criterio conservador (revisión completa).
3. Se identificaron **cuatro** puntos del sistema por donde un trabajo puede avanzar de
   etapa; dos ya controlan correctamente, **uno se cierra en esta propuesta** y el cuarto
   queda documentado y fuera de alcance (ver "NO incluido"). **Queda por confirmar** si
   existe un quinto camino no previsto; esa verificación es la primera tarea del trabajo,
   antes de escribir el control.
4. La división del módulo puede tener un techo técnico real, ya documentado en el propio
   código. Si lo alcanza, el cierre válido es dejar el resto **enumerado con su razón**,
   y esa razón tiene que ser producto de este trabajo —un intento de mover que falló, o
   una lectura del acoplamiento— no una cita de la documentación que ya existía.
5. La corrección de la guía no promete más cobertura de medición que la que el sistema
   realmente tiene.
6. "La línea de comandos se comporta igual" se verifica comparando, para un conjunto
   representativo de invocaciones —correctas, con datos faltantes, con datos inválidos, y
   la ayuda—, la **salida**, los **mensajes de error** y el **código de resultado**. No se
   promete igualdad literal absoluta: los valores que cambian entre dos ejecuciones del
   mismo programa (fechas, rutas temporales, duraciones) se normalizan, y la lista de esas
   normalizaciones se fija **antes** de comparar, no después de ver una diferencia.

---

## Riesgos y mitigación

| riesgo | impacto | mitigación |
|---|---|---|
| El control nuevo obliga a ajustar más pruebas automatizadas de las estimadas | esfuerzo mayor al previsto | Riesgo bajado: el conteo se rehizo y ahora está cerrado. De **20** usos reales del comando en el conjunto de pruebas, **7** requieren ajuste y 13 no, identificados uno por uno. La primera corrida completa confirma esa lista; si apareciera un caso no previsto, se registra antes de tocarlo |
| Existe otra vía de elusión no detectada | el control queda parcial y **parece** completo, que es peor que no tenerlo | La verificación de todas las vías es la primera tarea, con parada obligatoria si aparece una nueva. Y la vía que queda fuera de alcance **se nombra en el código**: el riesgo real no es que quede abierta, es que un comentario afirme que se cerró |
| El control funciona con datos de prueba y falla con los datos reales | falsa sensación de cierre | Se exige probar contra las **tres** formas que tienen los registros reales, no una: dato ausente (71 de 76 tandas), dato presente pero vacío, y complejidad sin clasificar (4 tandas). Un control probado sólo contra la segunda forma pasaría en verde sin tocar un solo registro real |
| Se ajusta una prueba bajándole la exigencia en lugar de adaptarla | pérdida silenciosa de cobertura | Prohibido explícitamente: reclasificar una tanda de prueba de complejidad media a baja para que el control no se active convierte una prueba del camino exigente en una del camino simple. Requiere decisión humana, no criterio del implementador |
| La división del módulo se convierte en una reescritura sin fin | costo abierto, riesgo de regresión | Dos cierres válidos definidos de antemano, y una decisión temprana sobre cuál aplica. La red de seguridad previa es un requisito bloqueante |
| El resto no movido se "justifica" reciclando documentación que ya existía | el trabajo parece cerrado sin haberse hecho | El cierre exige una matriz con una columna de **evidencia producida por este trabajo**: qué se intentó mover y qué falló, o qué lectura prueba el acoplamiento. Citar el comentario que ya estaba en el código no cierra |
| La división introduce un cambio de comportamiento silencioso | la línea de comandos se comporta distinto | Ninguna prueba automatizada debe cambiar de resultado, y la comparación cubre los **tres** canales (salida, errores, código de resultado) sobre invocaciones correctas **y** fallidas. El camino de error es justamente donde este tipo de reorganización rompe cosas |
| Se cierra la vía en el software y la norma interna sigue recomendándola | quien coordina elige el camino que ahora falla, y la herramienta parece rota | La norma y el registro formal de la decisión viajan en la **misma** entrega que el código, y se propagan a los cuatro entornos con el mecanismo que ya existe |
| Se corrige la guía y queda el otro documento afirmando lo contrario | el repositorio se contradice al revés | Las dos superficies se corrigen en la misma entrega, por requisito |
| Tres tandas de trabajo abiertas quedan trabadas por el control nuevo | interrupción operativa | Las tres están en etapas previas a la revisión; el camino correcto ya existe y está disponible. Ninguna se "migra" a mano |
| El control adicional se paga alterando el presupuesto de consumo | pérdida del límite que protege la cuota | El límite no se toca. Si un caso lo excede, se detiene y se consulta |

---

## Fases de entrega y esfuerzo relativo

| fase | qué entrega | esfuerzo |
|---|---|---|
| **1 — Control de calidad verificable** | La vía antigua de registro rechaza los casos que exigen dos revisiones y los que tienen observaciones graves abiertas. Norma interna corregida y decisión registrada formalmente, en la misma entrega. Registros históricos intactos. Las 7 pruebas automatizadas afectadas ajustadas y verificadas | **M** |
| **2 — Consola mantenible** | Red de seguridad tomada antes de mover código, cubriendo salida, errores y código de resultado; división aplicada donde es posible; el resto enumerado con evidencia propia; línea de comandos con comportamiento verificado idéntico | **M–L** (la incertidumbre está en el techo técnico, que se resuelve temprano) |
| **3 — Guía al día** | Guía de uso corregida y el documento que la referencia, consistentes entre sí | **S** |

La fase 1 es la que entrega valor por sí sola: es la única que cambia lo que el sistema
**permite**. Las fases 2 y 3 se pueden ejecutar en paralelo entre sí. No se comprometen
fechas: el esfuerzo es relativo y la secuencia es la garantía.

---

## Criterios de éxito medibles

1. **Cero** casos donde una tanda de trabajo clasificada como riesgo medio o alto pueda
   quedar aprobada y archivada sin la revisión de seguridad registrada.
2. **Cero** casos donde un "aprobado" convive con observaciones graves sin resolver.
3. Las tandas clasificadas como pequeñas y de bajo riesgo siguen cerrando con **una**
   sola revisión. Si esto se rompe, se rompió el equilibrio, no se mejoró el control.
4. El control se demuestra sobre las **tres** formas reales que tienen los registros: dato
   ausente, dato presente pero vacío, y complejidad sin clasificar. No sólo sobre registros
   recién creados.
5. Los **7** casos de prueba identificados se ven **fallar antes** del cambio y **pasar
   después**, con las corridas documentadas. Una prueba que nunca falló no demuestra nada.
   Ninguno se hace pasar bajándole la clasificación de complejidad.
6. Los 27 procesos ya cerrados siguen validando sin modificación.
7. **Ninguna** afirmación de la norma interna sigue recomendando la vía que el software
   ahora rechaza, verificado en los cuatro entornos, y la decisión queda registrada
   formalmente como cambio de comportamiento.
8. La línea de comandos de la consola conserva **todas** sus opciones y, para el conjunto
   representativo de invocaciones acordado, produce **la misma salida, los mismos mensajes
   de error y el mismo código de resultado** que la red de seguridad tomada previamente.
   Las opciones que escriben o que usan credenciales se verifican en un entorno temporal
   descartable, y ningún valor secreto queda registrado en la evidencia.
9. Ninguna prueba automatizada existente cambia de resultado por la división del módulo.
10. Ninguna afirmación de la guía de uso contradice a otro documento del repositorio.
11. Los límites de consumo del sistema quedan sin modificación.
