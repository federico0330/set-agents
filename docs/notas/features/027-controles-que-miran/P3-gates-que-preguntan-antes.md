# 027-controles-que-miran · P3-gates-que-preguntan-antes

<!-- notas:auto -->
## Motivo

- objetivo: Que el gate de pi corra antes del subproceso y que _decide_status filtre los codigos de modelo
- complejidad: medium
- paths: `ai/scripts/routing_core`, `ai/scripts/routing_cli.py`, `tests`, `docs/adr`
- depende de: P2-nada-escribe-afuera

## Tareas

- [ ] El gate de credenciales de pi corre antes del subproceso, sin cambiar el resultado (AC-06) (planned)
- [ ] _decide_status filtra MODEL_PINNED y MODEL_REQUEST_* (AC-07) (planned)

↩ [[features/027-controles-que-miran|027-controles-que-miran]]
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
