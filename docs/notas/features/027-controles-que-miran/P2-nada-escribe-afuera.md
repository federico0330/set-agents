# 027-controles-que-miran · P2-nada-escribe-afuera

<!-- notas:auto -->
## Motivo

- objetivo: Que ningun test pueda escribir fuera de un directorio temporal
- complejidad: medium
- paths: `tests`, `ai/scripts`, `docs/adr`
- depende de: P1-alcance-y-aislamiento

## Tareas

- [ ] Guarda que falla si un test escribe fuera de tmp, nombrando el archivo (AC-04) (planned)
- [ ] Probada en las dos direcciones: tmp pasa, HOME falla (AC-05) (planned)

↩ [[features/027-controles-que-miran|027-controles-que-miran]]
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
