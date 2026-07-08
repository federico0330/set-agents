# Tasks — Spec 000 (EJEMPLO)

> Tareas chicas y ordenadas. Cada una linkea su AC y su gate de revisión.

## T-001 — Tipos de dominio (Money)
- [ ] Money con unidades mínimas enteras o decimal exacto; tests de suma/resta/moneda distinta.
- AC: invariante de plata · Gate: audit (contra spec) + regression tests + verify.

## T-002 — Modelo de datos + migración
- [ ] Tablas/constraints/índices para asientos, reservas, AuditLog, candidatos de duplicado.
- AC: invariantes · Gate: @architect + @db-auditor.

## T-003 — Confirmar pago atómico
- [ ] Transacción única (asiento→Vendido, reserva→Pagada, AuditLog) con rollback en catch.
- AC: AC-1 · Gate: @db-auditor.

## T-004 — Concurrencia optimista
- [ ] UPDATE condicional atómico (`WHERE Id=@id AND Version=@read`), 0 filas ⇒ 409.
- AC: AC-2 · Gate: @db-auditor + @red-team.

## T-005 — Auditar intento fallido
- [ ] Persistir el intento perdedor en su propia unidad de trabajo (fuera del rollback).
- AC: AC-3 · Gate: @db-auditor.

## T-006 — Validaciones + middleware de errores
- [ ] 404/409 vía excepciones de dominio tipadas + middleware global; sin stack trace al cliente.
- AC: AC-4 · Gate: @security-auditor + @auditor.

## T-007 — Frontend: toast + refresco
- [ ] Mapear 409 a mensaje propio y refrescar el mapa; sin alert(); mapeo de errores centralizado.
- AC: AC-5 · Gate: @ux-ui-designer.

## T-008 — Listado paginado
- [ ] Paginar en SQL (Skip/Take), devolver {data,total,page,pageSize}; AsNoTracking en lecturas.
- Gate: @performance-auditor.
