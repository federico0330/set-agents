# Context pack — P1-spec-index-precedence

Feature: `036-specs-vivos-indice-y-precedencia`  
Package: `P1-spec-index-precedence`  
Risk signal: `public-contract`

## Objective

Make the spec index honest and write cross-feature precedence (ADR-0067): law stack in harness/orchestrator/TIPS,
full README backfill, partial supersession banner on 032, `## Supersedes` in architect/feature-contract, regression test.

## Owned paths

- `docs/specs/README.md`, `docs/specs/032-cursor-como-runtime/spec.md`
- `docs/adr/0067-spec-index-and-precedence.md`, `docs/adr/README.md`
- `Global/_canonical/agents/{orchestrator,architect,product-analyst}.md`
- `Global/_canonical/skills/feature-contract/SKILL.md`
- `.cursor/rules/00-harness.mdc`, `TIPS-USO.md`, `tests/test_harness.py`

## Traps

- Do not rewrite shipped spec bodies; banner only on 032.
- Do not invent `Superseded by` chains beyond 002→003 and partial 032.
- Test reads `docs/notas/00 - Proyecto.md`, not `ai/state/`.
- Run `./build.sh` after `_canonical` edits so `--check` passes.

## AC mapping

AC-01 doctrina · AC-02/03 README · AC-04 banner · AC-05 ADR · AC-06 Supersedes · AC-07 test · AC-08 build check
