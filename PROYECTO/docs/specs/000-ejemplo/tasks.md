# Tasks — Spec 000 (EJEMPLO)

> Work items agrupables en paquetes coherentes. Cada tarea tiene validaciones locales; la revisión profunda se
> ejecuta sobre el paquete integrado.

## T-001 — Tipos de dominio (Money)
- [ ] Money con unidades mínimas enteras o decimal exacto; tests de suma/resta/moneda distinta.
- AC: invariante de plata · Local: unit tests de Money + typecheck.

## T-002 — Modelo de datos + migración
- [ ] Tablas/constraints/índices para asientos, reservas, AuditLog, candidatos de duplicado.
- AC: invariantes · Package surface: architecture + db-integrity.

## T-003 — Confirmar pago atómico
- [ ] Transacción única (asiento→Vendido, reserva→Pagada, AuditLog) con rollback en catch.
- AC: AC-1 · Local: transaction test/focused integration.

## T-004 — Concurrencia optimista
- [ ] UPDATE condicional atómico (`WHERE Id=@id AND Version=@read`), 0 filas ⇒ 409.
- AC: AC-2 · Package surface: db-integrity + security-review.

## T-005 — Auditar intento fallido
- [ ] Persistir el intento perdedor en su propia unidad de trabajo (fuera del rollback).
- AC: AC-3 · Local: audit persistence test.

## T-006 — Validaciones + middleware de errores
- [ ] 404/409 vía excepciones de dominio tipadas + middleware global; sin stack trace al cliente.
- AC: AC-4 · Package surface: security-review + correctness.

## T-007 — Frontend: toast + refresco
- [ ] Mapear 409 a mensaje propio y refrescar el mapa; sin alert(); mapeo de errores centralizado.
- AC: AC-5 · Local: component/error mapping test; UI review if package includes frontend flow.

## T-008 — Listado paginado
- [ ] Paginar en SQL (Skip/Take), devolver {data,total,page,pageSize}; AsNoTracking en lecturas.
- Package surface: performance-scalability.
