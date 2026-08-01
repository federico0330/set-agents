# La validacion de DDL del store de ruteo no ve triggers ni vistas

<!-- notas:auto -->
- fecha: 2026-07-28 · actor: orchestrator
- alcance: [[features/007-quota-visibility|007-quota-visibility]]

## Contexto

Hallazgo F-10 del SPEC_CHALLENGE de la 007, verificado en vivo por el challenger: se instalaron un TRIGGER y una VIEW en una base recien creada y el store abrio igual. _validate_schema (store.py:156) enumera solo type='table' y la comparacion de DDL (store.py:171,185) cubre type IN ('table','index'). Un trigger AFTER INSERT sobre dispatches puede reescribir filas que el arnes acaba de insertar sin que ninguna validacion lo note.

## Decisión

Se registra, no se repara en la 007. Queda fuera de alcance por dos razones: no es el defecto que la feature vino a cerrar, y el control que lo contiene nunca fue vinculante contra el adversario que este hallazgo supone. Quien puede escribir el archivo de la base puede escribir un DDL perfectamente canonico con las filas que quiera, porque las CHECK restringen inserts futuros del arnes y no validan filas existentes. La 007 corrige la prosa que sobredimensionaba el control (AC-07): es un detector de deriva de version y corrupcion, no una defensa anti-manipulacion.

## Consecuencias

Candidato a paquete propio si alguna vez la DB de ruteo pasa a vivir en un directorio compartido o a sincronizarse entre maquinas -- ahi el modelo de amenaza cambia y el hueco pasa a ser vinculante. La reparacion natural es extender ambas enumeraciones a type IN ('table','index','trigger','view') y exigir el conjunto vacio para los dos ultimos. Cuesta poco; lo que no se puede es venderlo como que cierra el vector completo.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
