# Conocimiento global — Datos e integridad

> Capa CROSS-PROYECTO del "departamento" de data. Vive en el repo SET-AGENTES y se distribuye a cada
> proyecto como `docs/ai/knowledge/_global/data.md` (solo lectura ahí; se refresca en cada
> `sync-project.sh`). Se alimenta promoviendo entradas de la sección `## Candidatos a global` de los
> proyectos cuando aplican a cualquier stack. Nunca secretos, tokens, PII ni datos de un cliente.

## Invariantes
- Dinero nunca en float binario: entero de la unidad mínima (centavos) o decimal exacto. Un `float` para plata
  acumula error y es un bug de auditoría, no de redondeo.
- Toda operación multi-paso que debe ser todo-o-nada va en una transacción; un fallo a mitad no puede dejar
  estado parcial. La transacción cubre exactamente el conjunto que debe ser atómico, ni más ni menos.
- Concurrencia real se defiende con control explícito (optimistic concurrency con version/rowversion, o locks):
  verificar que el mecanismo REALMENTE dispara ante escrituras concurrentes, no que "está puesto".
- Borrado y estado sensible: preferir soft-delete/estado sobre `DELETE` físico cuando hay auditoría o
  referencias; el intento fallido también se audita (quién intentó qué y por qué se rechazó).
- Los datos derivados no son fuente de verdad: se recalculan o invalidan; no se persisten como si fueran el dato
  primario sin un mecanismo de consistencia.

## Errores conocidos y causas raíz
- **N+1 queries**: iterar entidades y pegar una query por cada una. Causa raíz: falta de join/`include`/proyección.
  Se detecta en review de datos; se arregla trayendo el set en una query.
- **Paginar en memoria**: traer todo y cortar en el código en vez de `LIMIT/OFFSET` (o keyset) en SQL → explota
  con volumen. La paginación va en la query.
- **Optimistic concurrency que no dispara**: la columna de versión existe pero el `UPDATE ... WHERE version = :v`
  no está, así que dos escrituras se pisan sin conflicto detectado.
- **Índice ausente en el filtro caliente**: query sobre una columna sin índice → scan completo. El review de
  escalabilidad chequea el plan, no sólo que "funciona" en dev con pocos datos.

## Decisiones y porqués
- `package-reviewer` cubre integridad de datos y escalabilidad en su propia checklist (atomicidad, N+1,
  paginación en SQL, `AsNoTracking`/read-only), en la misma pasada. Porqué: no hace falta un agente de DB/perf
  aparte para paquetes normales; se delega sólo si el riesgo lo amerita.
- La elección relacional vs no-relacional vs vector store es uno de los tres ejes de arquitectura que NO se
  deciden por defecto silencioso: requieren ADR o pregunta al usuario (ver architecture).
