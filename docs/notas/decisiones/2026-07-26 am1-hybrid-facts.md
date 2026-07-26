# AM-1: derivacion hibrida de facts con risk raise-only (enmienda a 003)

<!-- notas:auto -->
- fecha: 2026-07-26 · actor: orchestrator
- alcance: [[features/004-adaptive-dispatch|004-adaptive-dispatch]]

## Contexto

004 necesita que el orquestador aporte task_class al ruteo, pero la 003 exige que los facts no vengan del caller. Challenge B1: sin regla, un orquestador con incentivo de costo puede bajar el tier declarando mechanical/low.

## Decisión

Usuario (2026-07-26): derivacion mecanica de todo lo derivable (role/read_write/required_tools desde roster+capability, criticality desde task_class, context flags desde el context-pack en feature state, selected_runtime desde composicion); el descriptor aporta task_class; risk solo puede SUBIR la base derivada (CRITICAL/incident=>high, resto low). Registrado como enmienda acotada a la 003; mecanica en ADR-0006.

## Consecuencias

El tier queda gobernado por la base derivada; declarar low en tarea critica no baja nada. La adaptabilidad depende de task_class del orquestador, unico campo de intencion.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
