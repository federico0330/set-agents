# 033-menos-espera-menos-cuota · PKG-5

<!-- notas:auto -->
## Motivo

- objetivo: El gate se ve: progreso en vivo, falla temprana, resumen final y los 10 tests mas lentos
- ruteo: cursor-host native subagent; no route-decide → implementer (inherit)
- complejidad: medium
- riesgo: low
- paths: `ai/scripts/verify.sh`

## Tareas

- [ ] linea de progreso en vivo con ETA derivada del ritmo real (planned)
- [ ] bloque de falla impreso apenas ocurre, no al final (planned)
- [ ] resumen final con fallas, skips agrupados y los 10 tests mas lentos (planned)
- [ ] prueba de que el conjunto de tests ejecutados no cambia (planned)

context pack: `docs/specs/033-menos-espera-menos-cuota/context/PKG-5.md`

↩ [[features/033-menos-espera-menos-cuota|033-menos-espera-menos-cuota]]
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
