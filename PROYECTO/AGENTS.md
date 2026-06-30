# Reglas del Proyecto — <NOMBRE DEL PROYECTO>

> Esqueleto. Reemplazá los placeholders <...> y borrá lo que no aplique. Este archivo manda sobre las
> reglas globales del harness cuando hay conflicto, SOLO para este repo.

## Dominio del producto
<Una o dos frases: qué resuelve el sistema y para quién.>
Ejemplo: control de cobros futuros, pagos pendientes, comprobantes, detección de duplicados y conciliación manual.

## Fuente de verdad
- Specs: `docs/specs/**`  · ADRs: `docs/adr/**`  · Estado/logs IA: `ai/state/**`  · Memoria IA: `docs/ai/memory-log.md`

## Invariantes de dominio (ejemplos — ajustar)
- La plata NUNCA se calcula con punto flotante binario (usar enteros en unidades mínimas o decimal exacto).
- Toda acción de cobro/pago/comprobante/conciliación es auditable (actor, timestamp, antes/después).
- Operaciones que deben pasar juntas van en UNA transacción (atómicas).
- La detección de duplicados NO fusiona automáticamente: propone candidatos para revisión humana.
- Estados (pendiente/futuro/vencido) se derivan de status explícito + fechas, no de lógica oculta de UI.

## Verificación
Correr `./ai/scripts/verify.sh` antes de auditar o dar por terminada una tarea.

## Alcance de implementación
Implementar SOLO la tarea activa de `docs/specs/<id>/tasks.md`. No agregar integraciones, sync bancario,
exportes contables, OCR ni pasarelas de pago si no están pedidos.

## Gates de revisión (cuándo son obligatorios)
- **DB** (`@db-auditor`): schema, migraciones, plata, duplicados, conciliación, concurrencia, audit trail.
- **Seguridad** (`@security-auditor` + `@red-team`): auth, roles, upload/comprobantes, aislamiento por tenant, secrets, servicios externos.
- **Performance** (`@performance-auditor`): endpoints de listado, queries, loops sobre datos, paginación.
- **Diseño** (`@architect`): nuevos módulos, cambios de modelo de datos, máquinas de estado.
- **UI/UX** (`@ux-ui-designer`): cualquier cambio de interfaz o manejo de errores en el cliente.

## Stack y comandos
- Stack: <node | .NET | go | python | ...>
- Test: `<comando de test>`  · Lint: `<...>`  · Build: `<...>` (reflejarlos en verify.sh).

## Modelos (override local opcional)
Por defecto se usan los modelos globales. Para forzar otros en los loops, exportá `IMPL_MODEL`,
`AUDIT_MODEL`, etc. antes de correr `ai/scripts/loop.sh`.

## MCP
- Context7 para docs actuales del framework/ORM/librerías de test cuando haya incertidumbre de versión.
- Engram solo para decisiones de alto valor y lecciones verificadas del proyecto.
