# 031 — Verbos de corrección de registro

- **Estado**: aprobado por Federico (2026-08-17): el prompt de tanda describe los dos defectos,
  los dos casos reales donde bloquearon el registro, y las decisiones ya tomadas en
  `ai/state/decisions-log.jsonl` (`d5-revision-correctiva-sin-camino-de-estado`,
  `replanteo-028-paquetes-sin-work-items`, `replanteo-028-imposible-el-motor-no-tiene-salida`).
- **ADRs**: pendiente de asignar número (post-implementación).

## Motivación

El harness bloqueó el registro de evidencia real en dos ocasiones:

1. **025/D5-vault-en-todo-spawn** (`phase: DONE`): La delta review correctiva que encontró una
   regresión de seguridad viva (vault en argv, visible en `ps aux`) no pudo registrarse porque
   `record-delta-review` exige fase `DELTA_REVIEW` y `reopen` sólo aplica desde `BLOCKED`.
   La evidencia quedó sólo en archivo, fuera del registro oficial del paquete.

2. **028-narracion-que-ensena** (`phase: BLOCKED`): El error original fue que `create-package`
   no acepta tasks si ya existe el package_id, `update-package` no tiene `--task`, y
   `LEGAL_TRANSITIONS` no lleva de `PACKAGE_PLANNING` a `PACKAGE_ACCEPTED` sin tasks completas.
   Aunque el caso de 028 fue resuelto de otro modo, el vector de defecto (paquete sin work items
   que no se puede reparar) sigue abierto para cualquier feature futura.

## Criterios de aceptación

### `reopen --from-done` (AC-01 a AC-06)

- **AC-01**: `reopen` con `--from-done` sobre una feature en fase `DONE` la mueve a
  `PACKAGE_PLANNING` y registra un evento `reopen-from-done` con `from_phase`, `reason` y
  `authorized_by`.
- **AC-02**: `reopen --from-done` sobre una feature **no** en `DONE` devuelve error explicativo.
- **AC-03**: `reopen` sin `--from-done` sobre una feature en `DONE` devuelve error (comportamiento
  anterior preservado: "reopen only applies to BLOCKED; use --from-done to reopen from DONE").
- **AC-04**: `--reason` y `--authorized-by` siguen siendo obligatorios (igual que hoy).
- **AC-05**: El cierre anterior (`final_state: DONE`) se popea, igual que hoy hace `reopen`
  desde BLOCKED con `final_state: BLOCKED`.
- **AC-06**: `reopen --from-done` NO resetea counters de bloqueadores (no hay bloqueadores activos
  en DONE; hacerlo sería un blanket clear sin justificación).

### `amend-package` (AC-07 a AC-13)

- **AC-07**: `amend-package --package-id <pid> --task <id> --reason <text>` agrega tasks al array
  `package["tasks"]` de un paquete existente.
- **AC-08**: `amend-package` sobre un paquete con `status == "accepted"` devuelve error:
  "cannot amend an accepted package; create a new package for additional work".
- **AC-09**: `amend-package` sobre un package_id inexistente devuelve error.
- **AC-10**: `--reason` es obligatorio y debe tener al menos 80 caracteres (el motivo es la única
  evidencia de que la corrección es legítima y no inventada post-facto).
- **AC-11**: `amend-package` registra un evento `amend-package` con `{package_id, added_tasks, reason}`.
- **AC-12**: La fase de la feature NO cambia. El verbo opera en cualquier fase no-terminal excepto
  sobre paquetes accepted.
- **AC-13**: Los tasks agregados llegan con `status: "planned"`, no `completed`. Quien los usa
  tiene que completarlos antes de que `package_review_ready` los acepte.

## Riesgos y mitigaciones

| Riesgo | Mitigación |
|--------|-----------|
| `reopen --from-done` se vuelve la puerta para reabrir y maquillar cualquier feature cerrada | `--from-done` obliga conciencia explícita; `--authorized-by` registra quién autorizó (igual que D4 en 025); el evento `reopen-from-done` queda visible en el historial |
| `amend-package` agrega tasks inventados después de correr el gate | La guarda `status != accepted` impide hacerlo post-aceptación; el `--reason` largo deja rastro auditable |
| `record-late-review` se debilita indirectamente | NO se toca `record-late-review`. Su negativa sobre paquetes accepted sigue siendo correcta y está razonada en su docstring. 031 le da una puerta previa, no la fuerza |

## Paquete único: P1-verbos-correctivos

- **Implementación**: `ai/scripts/feature_state_lib/cli_lifecycle.py`
- **Mirror**: `PROYECTO/ai/scripts/feature_state_lib/cli_lifecycle.py` (via `./build.sh`)
- **Registro de subparser**: `ai/scripts/feature-state.py`
- **Tests**: `tests/test_feature_state.py` o archivo equivalente
- **Complexity**: small (dos verbos, un archivo, cambio quirúrgico)

### Tasks

- `extend-reopen`: Extender `cmd_reopen` para aceptar `--from-done`
- `add-amend-package`: Implementar `cmd_amend_package` nuevo verbo
- `register-subparsers`: Registrar ambos verbos en `feature-state.py`
- `build-mirror`: Ejecutar `./build.sh` y verificar GLOBAL_TREE_SYNC_OK
- `tests-bite`: Tests en ambas direcciones para los dos verbos
