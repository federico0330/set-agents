# La deriva de hash ya existente se registra como deuda, no se convierte en un gate

<!-- notas:auto -->
- fecha: 2026-07-28 · actor: orchestrator
- alcance: [[features/009-self-application|009-self-application]] · [[features/009-self-application/P2-state-machine-required|P2-state-machine-required]]

## Contexto

AC-13 hace que init verifique el sha256 del spec, pero nada re-verifica el hash despues. Medido hoy sobre los 7 archivos de estado vivos: 002, 005, 007 y 008 declaran un hash que no coincide con su spec en disco, y el de 005 ni siquiera tiene forma de sha256 (16 caracteres hexadecimales). validate_state:251-253 solo exige que path y hash sean no vacios, asi que 'h' pasa. Cuatro de siete expedientes afirman la aprobacion de bytes que ya no existen.

## Decisión

No se endurece validate_state ni se agrega un ratchet que falle sobre la deriva existente. Exigir forma de sha256 invalidaria el archivo vivo de 005, y sync-project.sh:24-25 aborta la sincronizacion si alguna feature no terminal falla validate: el arnes se quedaria sin poder sincronizar proyectos por una deuda historica. Queda registrado y visible.

## Consecuencias

El agujero queda cerrado hacia adelante y abierto hacia atras. Cerrarlo del todo necesita decidir que hacer con cada uno de los cuatro: re-aprobar el spec y re-inicializar con acta (como se hizo con 008 y 009), o baselinear la deriva con su motivo escrito, al estilo del set 'legacy' de GLOBAL_ABSOLUTE_PATH_RATCHET en verify.sh:33-36. Es un paquete propio, no un arreglo de contrabando dentro de este.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
