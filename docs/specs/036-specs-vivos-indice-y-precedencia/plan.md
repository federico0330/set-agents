# 036 — Plan

## Secuencia

1. Spec + challenge (este slice).
2. `feature-state.py init` scoped + `public-contract`.
3. Un paquete `P1-spec-index-precedence`: doctrina → ADR-0067 → README backfill → banner 032 → test → build check.
4. Gates: `verify.sh` owned paths, `./build.sh --check`.
5. Review + integración → DONE.

## Dependencias

- ADR-0063 ya documenta supersede parcial 032 (no re-litigar).
- `./build.sh --check` depende de edits en `_canonical`.

## Decisiones humanas

- Plan aprobado implícito al pedir implementación (2026-08-24).

## Riesgos de ejecución

- README largo: mantener tabla legible, títulos acortados donde haga falta.
