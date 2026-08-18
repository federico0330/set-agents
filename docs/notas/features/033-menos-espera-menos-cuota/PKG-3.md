# 033-menos-espera-menos-cuota · PKG-3

<!-- notas:auto -->
## Motivo

- objetivo: Elegir modelo sin scrollear: agrupado por proveedor, contador, valor actual marcado, sin parpadeo
- ruteo: cursor-host native subagent; no route-decide → implementer (inherit)
- complejidad: high
- riesgo: medium
- paths: `ai/scripts/tui.py`, `ai/scripts/setup_models.py`

## Tareas

- [ ] secciones por proveedor no seleccionables en el picker (planned)
- [ ] contador de posicion, indicadores de scroll y marca del valor actual (planned)
- [ ] anotaciones atenuadas (free, quien lo usa) y busqueda al tipear (planned)
- [ ] sacar el borrado de pantalla completo de tui.py:818 y probarlo a nivel bytes (planned)

context pack: `docs/specs/033-menos-espera-menos-cuota/context/PKG-3.md`

↩ [[features/033-menos-espera-menos-cuota|033-menos-espera-menos-cuota]]
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
