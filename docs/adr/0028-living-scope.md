# ADR-0028 — Alcance vivo: re-verificación de spec hash, amend-spec, supersede-package

- Estado: Accepted (2026-08-04). Feature 017. Cuarta de cinco (0025-0029).

## Contexto

`verify_spec_hash` se invocaba en exactamente un lugar: `cmd_init`. Después del init el contrato quedaba
simultáneamente inmutable e inauditado: `acceptance_criteria` solo se escribe en init, `update-package`
es una whitelist que no permite tocar objetivo/tareas/paths, no existía `amend-spec` ni estado
`superseded`, y `done_ready` exigía todo paquete `accepted` — un paquete obsoleto por cambio de alcance
bloqueaba la feature para siempre. La única salida era `init --force`, destructiva, ya pagada dos veces
(decisiones 2026-07-28). El requisito del dueño es explícito y bidireccional: ningún cambio de alcance
sin reflejo y consulta previos — si el usuario cambia el alcance y el harness no se entera, o viceversa,
las iteraciones siguientes son desperdicio.

## Decisión

1. **Re-verificación**: `resume`/`next` re-hashean el spec y anotan `SPEC_DRIFT` (aviso no fatal con
   instrucción de pasar por `amend-spec`); `accept-package` bloquea con la misma instrucción. El init
   sigue siendo el único punto que lo exige para arrancar.
2. **`amend-spec`**: registra nueva versión del contrato (path + hash + motivo + actor) en
   `spec_amendments[]`, actualiza `approved_spec`, regenera notas. Requiere confirmación del usuario —
   es una de las preguntas que la Question policy YA autoriza (cambio mayor de alcance). Nunca más
   `init --force` para cambios de alcance.
3. **`supersede-package`**: estado terminal `superseded` con motivo y amendment vinculado; `done_ready`
   acepta `accepted|superseded` (extensión aditiva — los tests inmutables, que solo usan `accepted`,
   siguen verdes).
4. **Doctrina de drift**: si el pedido del usuario contradice el spec aprobado, el orquestador para y
   ofrece amend (pregunta autorizada); si el harness detecta `SPEC_DRIFT` por hash, mismo camino.

## Rejected alternatives

- **Hacer `verify_spec_hash` fatal en resume/next**: rompería sesiones legítimas donde el humano editó
  prosa no normativa del spec; el punto duro correcto es `accept-package` (donde se certifica trabajo
  contra el contrato).
- **Permitir editar paquetes in-place**: destruye la trazabilidad paquete↔contrato; superseder + crear
  paquete nuevo conserva la historia.

## Consecuencias

- El contrato pasa de "candado de un solo uso" a documento vivo con historial auditable.
- `init --force` queda para su caso real (estado corrupto), no como válvula de escape de alcance.
