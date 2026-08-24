# 036 — Specs vigentes, actas históricas

- **Estado:** Shipped (2026-08-24).
- **Modo:** scoped · señal `public-contract`.
- **ADRs:** 0067 (nuevo); referencia 0028 (intra-feature), 0063 (supersede parcial 032).

## Problema

El índice [`docs/specs/README.md`](../README.md) lista nueve filas mientras existen treinta y cinco
`docs/specs/*/spec.md` en el repo. Features cerradas (034, 035) siguen `Approved` en la tabla aunque
[`docs/notas/00 - Proyecto.md`](../../notas/00%20-%20Proyecto.md) las marca `DONE`. Los agentes arrancan
leyendo specs viejos como si fueran contrato vigente; ADR-0028 cubre drift **dentro** de una feature
(`amend-spec` / `supersede-package`) pero no hay precedencia cross-feature escrita donde el orquestador
sí lee al inicio.

## Usuarios

- Mantenedores del harness que necesitan saber qué spec manda sin recorrer carpetas.
- Orquestador y roles de lectura que citan contratos al arrancar una sesión.
- `product-analyst` que mantiene el índice (hoy sin gate).

## Alcance

1. **Law stack** — precedencia explícita en tres sitios que el agente lee al arrancar:
   `.cursor/rules/00-harness.mdc`, `Global/_canonical/agents/orchestrator.md` (+ `./build.sh --check`),
   y una línea en `TIPS-USO.md` que apunte a esa precedencia.
2. **Índice completo** — backfill de `docs/specs/README.md`: una fila por carpeta `docs/specs/<id>/spec.md`
   (excluir `PROYECTO/docs/specs/000-ejemplo`), estados alineados a `00 - Proyecto.md`.
3. **Cartel histórico** — plantilla `## Supersession notice` (como
   [002](../002-adaptive-pi-orchestration/spec.md):3-8) en specs viejos **sin reescribir el cuerpo**;
   mínimo [032](../032-cursor-como-runtime/spec.md) (supersede parcial AC-06/`inherit` → 034 + ADR-0063).
4. **`## Supersedes` en diseño** — `architect.md` y skill `feature-contract`: toda feature nueva declara
   qué cláusulas/AC de specs shippeados pisa, o `none`.
5. **ADR-0067** — formaliza cartel + “no reescribir acta” + índice como única tabla de vigencia; fila en
   `docs/adr/README.md`.
6. **Test** — en `tests/test_harness.py`: fila por spec, status cerrado, `DONE` en notas → `Shipped` o
   `Superseded by …`. **No leer `ai/state/`** (gitignored).

## Fuera de alcance (no-goals)

- Reescribir el cuerpo de specs `DONE`.
- Grafo `supersedes.toml` ni CLI `supersede-spec` cross-feature.
- Arreglar las seis secciones sembradas de `docs/modules/`.
- Reabrir 002/011/032/033.
- Digest compilado de precedencia.

## Law stack (orden mandatorio → histórico)

1. Código + tests + `generate.py` (si el test está rojo, gana el test).
2. ADR **Accepted** más nuevo sobre el tema ([`docs/adr/README.md`](../../adr/README.md)).
3. Spec de la **feature activa** (context pack + spec con hash).
4. Specs con status `Shipped` / `Superseded by …` en el índice = acta histórica; no se ejecutan como
   contrato vigente.

ADR-0028 sigue cubriendo solo drift **dentro** de una feature.

## Criterios de aceptación

- **AC-01** Los tres sitios de doctrina (00-harness, orchestrator canónico, TIPS una línea) declaran el
  law stack en el orden de arriba, sin contradecirse.
- **AC-02** `docs/specs/README.md` tiene una fila por cada `docs/specs/<NNN-*/spec.md` del repo raíz;
  vocabulario de status: `Draft` | `Approved` | `Shipped` | `Superseded by <id>` (inglés en la tabla).
- **AC-03** Filas alineadas a `docs/notas/00 - Proyecto.md`: feature `DONE` → `Shipped` salvo fila ya
  `Superseded by …`; features no cerradas (032, 033, 011) no dicen `Shipped`.
- **AC-04** `docs/specs/032-cursor-como-runtime/spec.md` lleva `## Supersession notice` arriba del cuerpo,
  citando supersede **parcial** de AC-06/`inherit` por 034 + ADR-0063; cuerpo intacto.
- **AC-05** `docs/adr/0067-spec-index-and-precedence.md` Accepted + fila en `docs/adr/README.md`.
- **AC-06** `Global/_canonical/agents/architect.md` y `Global/_canonical/skills/feature-contract/SKILL.md`
  exigen `## Supersedes` en `design.md` (`none` si no pisa nada).
- **AC-07** Test en `tests/test_harness.py` falla si falta fila, status inválido, o `DONE` sin
  `Shipped`/`Superseded by`.
- **AC-08** `./build.sh --check` verde (twins orchestrator/product-analyst/architect/feature-contract).

## Riesgos

| Riesgo | Mitigación |
|--------|------------|
| Backfill inventa cadenas `Superseded by` | Solo 002→003 y parcial 032; resto `Shipped`/`Approved`/`Draft` según notas |
| Product-analyst y README divergen de nuevo | Test AC-07 como contrato |
| Doctrina duplicada en cuatro runtimes | Solo `_canonical` + build check |

## Spec audit

- **Universo del test:** carpetas `docs/specs/[0-9][0-9][0-9]-*/spec.md` bajo repo root; excluye PROYECTO.
- **Fuente DONE:** regex sobre `docs/notas/00 - Proyecto.md`, no `ai/state/`.
- **Precedencia vs ADR-0028:** explicitada en spec y ADR-0067; sin conflicto (ámbitos distintos).
- **UNVERIFIED:** fechas exactas de shipment para features 006–010 inferidas de notas/commits — el test no
  las valida, solo status.

## Paquete único: P1-spec-index-precedence

- **Paths:** `docs/specs/README.md`, banners, `docs/adr/0067-*`, `Global/_canonical/**`, `.cursor/rules/00-harness.mdc`, `TIPS-USO.md`, `tests/test_harness.py`
- **Complexity:** small+low · `runtime_surface=false`
