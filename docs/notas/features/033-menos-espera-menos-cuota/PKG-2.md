# 033-menos-espera-menos-cuota · PKG-2

<!-- notas:auto -->
## Motivo

- objetivo: El menu Modelos no congela: probe asincronico, cache con TTL y degradacion con nombre
- ruteo: cursor-host native subagent; no route-decide → implementer (inherit)
- complejidad: high
- riesgo: medium
- paths: `ai/scripts/setup_models.py`, `ai/scripts/models_config.py`

## Tareas

- [ ] primer render antes de 300 ms con lo que ya esta en disco (planned)
- [ ] probe y catalogo de modelos fuera del camino critico, con with_progress (planned)
- [ ] cache en disco con TTL y antiguedad visible, mas tecla de refresco (planned)
- [ ] reemplazar el except Exception mudo de setup_models.py:356-359 por degradacion nombrada (planned)

context pack: `docs/specs/033-menos-espera-menos-cuota/context/PKG-2.md`

↩ [[features/033-menos-espera-menos-cuota|033-menos-espera-menos-cuota]]
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
