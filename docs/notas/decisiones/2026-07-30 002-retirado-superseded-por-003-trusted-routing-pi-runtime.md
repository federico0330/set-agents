# 002 retirado, superseded por 003-trusted-routing-pi-runtime

<!-- notas:auto -->
- fecha: 2026-07-30 · actor: orchestrator
- alcance: [[features/002-adaptive-pi-orchestration|002-adaptive-pi-orchestration]]

## Contexto

002 quedó phase=BLOCKED, final_state=BLOCKED desde 2026-07-24 (P1-routing-core, status=repair_required, HUMAN_DECISION_REQUIRED sin resolver: tercer ciclo de reparación autorizado por el usuario agotó 12/12 spawns y 2/2 ciclos de revisión profunda, con 5 hallazgos altos aún reproducibles: P1-DR2-001 route_id mutable, P1-DR2-002 observations omitibles, P1-DR2-003 identidad de implementador no atada conjuntamente, P1-DR2-007 symlink de ancestro de telemetría aceptado, P1-DR2-008 recuperación de crash/corrupción insegura). docs/specs/002-adaptive-pi-orchestration/spec.md ya lleva desde entonces una nota de supersesión propia apuntando a 003-trusted-routing-pi-runtime.

## Decisión

Verificado feature por feature: 003-trusted-routing-pi-runtime llegó a phase=DONE (paquete P1R-trusted-routing accepted) el 2026-07-29, y su diseño resuelve cada uno de los 5 hallazgos abiertos de 002: route_id estático atado a contenido (rt1_<16hex> = SHA-256 de la tupla canónica) resuelve P1-DR2-001; ObservedTaskFacts fail-closed ante ausencia/conflicto (execution_enabled=false + FACTS_INCOMPLETE) resuelve P1-DR2-002; ImplementationIdentity derivada solo de un dispatch persistido, todo-o-nada, resuelve P1-DR2-003; apertura del store con lstat no-follow por ancestro/componente resuelve P1-DR2-007; el store SQLite transaccional (BEGIN IMMEDIATE, WAL, synchronous=FULL) en reemplazo del JSON/JSONL de archivos resuelve P1-DR2-008. 002 se retira: no hay más trabajo de código bajo este feature-id. phase/final_state se dejan BLOCKED tal cual -- PHASES no tiene un valor SUPERSEDED y no se inventa uno esta noche (sería refactor oportunista del propio state machine sin contrato de usuario detrás). El registro histórico y la nota de supersesión en el spec son el artefacto de cierre.

## Consecuencias

Deuda de herramienta nombrada, no arreglada: (1) LEGAL_TRANSITIONS['BLOCKED'] = set() no tiene salida hacia un estado terminal 'cerrado pero no aceptado' -- reopen() solo lleva de vuelta a PACKAGE_PLANNING, nunca a un cierre; (2) STATUS.md no tiene ningún lenguaje para 'retirado/superseded'; (3) el mismo gap de blockers-nunca-se-vacían que 009 ya logueó (una feature reabierta no puede llegar a DONE sin edición a mano) aplica en espejo acá: ni siquiera reabriendo se podría cerrar 002 limpiamente hoy. Candidato a un paquete futuro chico (un campo tipo 'superseded_by' por un mecanismo genérico, nunca un PHASES nuevo) -- no emprendido esta noche, sin pedido del usuario para eso.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
