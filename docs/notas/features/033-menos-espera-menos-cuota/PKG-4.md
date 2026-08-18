# 033-menos-espera-menos-cuota · PKG-4

<!-- notas:auto -->
## Motivo

- objetivo: Windows sin mentiras: cerrar las 8 fallas residuales y el flaky de macOS, con techo de skips
- complejidad: high
- riesgo: medium
- paths: `tests`, `.github/workflows/ci.yml`, `ai/scripts/vault_ops.py`

## Tareas

- [ ] los 4 tests que llaman bash directo pasan por la guarda de toolchain (planned)
- [ ] diagnosticar y resolver los casos 5 a 8 uno por uno, con evidencia por caso (planned)
- [ ] techo de skips fijado en el job windows-bootstrap (planned)
- [ ] volver determinista el test de liveness de macOS sin subir el sleep (planned)

↩ [[features/033-menos-espera-menos-cuota|033-menos-espera-menos-cuota]]
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
