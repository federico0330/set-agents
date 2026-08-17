# La revision correctiva de D5 no puede aterrizar en el registro del paquete

<!-- notas:auto -->
- fecha: 2026-08-17 · actor: orchestrator
- alcance: [[features/025-consola-minima-y-flexible|025-consola-minima-y-flexible]] · [[features/025-consola-minima-y-flexible/D5-vault-en-todo-spawn|D5-vault-en-todo-spawn]]

## Contexto

D5 quedo accepted con diff_ref=WORKTREE-D5-2026-08-17 (un worktree, no un SHA) y con una review cuya evidencia era D5-implementation.md, escrito por el propio implementer. Federico pidio una delta review real. Al intentar registrarla, record-spawn falla con 'cannot record spawn from phase DONE' (ai/scripts/feature-state.py:407-408, guarda TERMINAL) y record-delta-review exige phase DELTA_REVIEW (ai/scripts/feature_state_lib/cli_repair.py:279-280). reopen solo aplica desde BLOCKED (cli_lifecycle.py:527-528). No existe salida de DONE.

## Decisión

La delta review se ejecuta igual con un delta-reviewer independiente sobre el diff real 8091b0b..1014b02 acotado a los cuatro spawners, y su resultado se persiste como archivo de evidencia mas esta decision, NO como delta_review del paquete. No se falsea el registro del paquete ni se edita el JSON a mano para simular un camino que la maquina de estados no tiene.

## Consecuencias

El registro de D5 sigue mostrando cero delta reviews; la revision correctiva vive en docs/specs/025-consola-minima-y-flexible/evidence/D5-delta-review-correctiva.md. Queda expuesto un hueco del harness: una feature cerrada cuya aceptacion resulta defectuosa no tiene camino de correccion en la maquina de estados. Candidato a feature propia.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
