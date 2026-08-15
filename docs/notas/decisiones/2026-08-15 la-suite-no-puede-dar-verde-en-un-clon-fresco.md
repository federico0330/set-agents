# Defecto latente: cuatro tests leen ai/state/project.json, que esta gitignoreado

<!-- notas:auto -->
- fecha: 2026-08-15 · actor: orchestrator
- alcance: [[features/027-controles-que-miran|027-controles-que-miran]] · [[features/027-controles-que-miran/P3-gates-que-preguntan-antes|P3-gates-que-preguntan-antes]]

## Contexto

Hallazgo P3-F07 del reviewer independiente, preexistente y no causado por P3. tests/test_routing.py:2810 y tres tests hermanos leen ROOT/ai/state/project.json directo. Desde 024/C1 (ADR-0047) ai/state/ esta gitignoreado (.gitignore:53), asi que esos cuatro tests fallan con FileNotFoundError en cualquier worktree o clon fresco. El reviewer lo midio en las dos direcciones: con P3 'Ran 323 tests, FAILED (failures=2, errors=2)' y en HEAD limpio 'Ran 321 tests, FAILED (failures=2, errors=2)', con conjuntos de fallas IDENTICOS. Los tres implementers de esta noche lo vieron en sus worktrees.

## Decisión

No se repara dentro de 027. tests/test_routing.py es archivo de P3 pero estos cuatro tests no tienen relacion con AC-06 ni AC-07, y arreglarlos seria refactor oportunista. Se registra medido, con su file:line y su mitigacion existente: ai/scripts/seed-state.py reconstruye el estado desde ai/state.seed/.

## Consecuencias

El repo es publico desde 024. Un tercero que lo clone y corra la suite ve cuatro rojos que no son suyos, en la primera experiencia con el harness -exactamente el problema que 024 vino a resolver-. Y los gates de paquete corren en worktrees, que es donde esto se manifiesta, asi que va a seguir apareciendo en cada feature hasta que alguien lo cierre: o los tests siembran su propio project.json en un temp, o llaman a seed-state.py, o el gate lo hace antes. Es de la misma familia que los seis defectos de 027: algo que informa OK sobre algo que no mira, esta vez al reves.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
