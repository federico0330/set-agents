# ADR 0001 — <Decisión> (EJEMPLO)

## Estado
Propuesto | Aceptado | Reemplazado por ADR-XXXX

## Contexto
<Qué fuerza la decisión: requisito, restricción, riesgo de datos/seguridad/plata.>
Ejemplo: necesitamos garantizar atomicidad y concurrencia correcta al confirmar pagos de asientos.

## Opciones consideradas
1. <Opción A> — pros / contras.
2. <Opción B> — pros / contras.
Ejemplo: (A) UPDATE condicional atómico con token de versión; (B) lock pesimista por fila.

## Decisión
<La opción elegida y por qué.>
Ejemplo: UPDATE condicional atómico (`WHERE Id=@id AND Version=@read`); 0 filas afectadas ⇒ 409. Menos
contención que el lock pesimista y la base garantiza la exclusión.

## Consecuencias
<Qué se gana, qué se acepta como costo, qué queda abierto.>
