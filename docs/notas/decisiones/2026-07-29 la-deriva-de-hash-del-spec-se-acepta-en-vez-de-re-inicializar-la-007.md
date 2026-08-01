# El contrato se enmienda a 1.3.0 y la deriva de hash se acepta, porque re-inicializar tiraria el registro de P1 recien aceptado

<!-- notas:auto -->
- fecha: 2026-07-29 · actor: orchestrator
- alcance: [[features/007-quota-visibility|007-quota-visibility]] · [[features/007-quota-visibility/P2-spawn-accounting|P2-spawn-accounting]]

## Contexto

verify_spec_hash solo corre en cmd_init, asi que la unica forma de volver a alinear el hash guardado con el disco es init --force, y eso descarta la historia entera de la feature. La 007 acaba de ser re-inicializada con acta hace unas horas y P1-schema-normalize ya esta accepted con su panel de tres miembros, su hallazgo refutado y sus siete gates. Estado tras la enmienda: guardado 31d6e65a, disco 068f0d24.

## Decisión

Se acepta la deriva y se registra. Re-inicializar por un cambio de prosa que no toca ningun AC seria cambiar un registro correcto por uno vacio. Es exactamente el defecto que 009-P2 dejo abierto hacia atras: el gate de hash cierra el agujero hacia adelante y no tiene forma de re-aprobar un spec enmendado sin perder la historia.

## Consecuencias

Suma la 007 a las cuatro features que ya afirman un spec que no existe en disco (decision cuatro-archivos-de-estado-afirman-un-spec-que-ya-no-existe), con la diferencia de que aca la deriva es deliberada, del mismo dia, y su contenido esta escrito en el tercer log de enmiendas del propio spec. El arreglo de fondo sigue siendo el mismo y sigue sin paquete: un verbo que re-apruebe un spec enmendado sin re-inicializar.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
