# 024-listo-para-terceros · C2-modelstoml-neutro

<!-- notas:auto -->
## Motivo

- objetivo: models.toml deja de fijar las suscripciones de una persona y el usuario tiene overlay propio
- complejidad: medium
- paths: `models.toml`, `ai/scripts/models_config.py`, `tests`, `docs/adr`
- depende de: C1-estado-fuera-del-producto

## Tareas

- [ ] [subscriptions] pasa a ausente = auto (AC-03) (planned)
- [ ] El small model deja de exigir Zen en local, y la lane local se renombra a lo que es (AC-04) (planned)
- [ ] Overlay de config del usuario en STATE_DIR, que desbloquea --update (AC-05) (planned)

↩ [[features/024-listo-para-terceros|024-listo-para-terceros]]
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
