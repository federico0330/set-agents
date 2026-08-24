# ADR-0067 — Spec index as vigor table and cross-feature precedence

- Estado: **Accepted** (2026-08-24). Feature `036-specs-vivos-indice-y-precedencia`, PKG P1.
- Relacionado: ADR-0028 (intra-feature drift only), ADR-0063 (partial supersede of 032 AC-06).

## Contexto

`docs/specs/README.md` listaba nueve filas mientras el repo tenía treinta y cinco `docs/specs/*/spec.md`.
Features `DONE` seguían `Approved` en la tabla. Los agentes leen specs al arrancar; sin precedencia
cross-feature escrita, actas históricas se ejecutaban como contrato vigente. ADR-0028 cubre
`amend-spec` / `supersede-package` **dentro** de una feature, no qué spec manda entre features cerradas
y la activa.

## Decisión

1. **Law stack** (mandatory → historical), declarado en `.cursor/rules/00-harness.mdc`,
   `Global/_canonical/agents/orchestrator.md`, y una línea en `TIPS-USO.md`:
   (1) código + tests + `generate.py`, (2) ADR Accepted más nuevo, (3) spec de la feature activa,
   (4) filas `Shipped` / `Superseded by …` = acta histórica.
2. **`docs/specs/README.md`** es la única tabla de vigencia: una fila por carpeta
   `docs/specs/<id>/spec.md` (excluir `PROYECTO/`), status en inglés:
   `Draft` | `Approved` | `Shipped` | `Superseded by <id>`.
3. **No reescribir actas:** specs cerrados llevan `## Supersession notice` arriba del cuerpo intacto
   (plantilla en 002); supersede parcial documentado en cartel + ADR, no fila `Superseded by` entera
   mientras la feature no esté DONE.
4. **`## Supersedes` en `design.md`:** toda feature nueva declara qué cláusulas shippeadas pisa
   (`architect.md`, skill `feature-contract`).
5. **Test en `tests/test_harness.py`:** fila por spec, vocabulario cerrado, `DONE` en
   `docs/notas/00 - Proyecto.md` → `Shipped` o `Superseded by`. No leer `ai/state/` (gitignored).

## Consecuencias

- `product-analyst` mantiene el índice; el test convierte la promesa en contrato.
- No se agrega CLI `supersede-spec` ni grafo `supersede.toml` en este ADR.
- ADR-0028 sigue siendo el mecanismo de drift intra-feature.
