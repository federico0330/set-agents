# 036 — Criterios de aceptación (BDD)

> Escenarios observables. Fuente DONE: `docs/notas/00 - Proyecto.md` (git-tracked). No `ai/state/`.

---

## Diagrama

```
  orquestador / test          artefacto                    resultado
  ─────────────────          ─────────                    ─────────

  arranque sesión      ──▶  00-harness + orchestrator  ──▶  law stack en orden AC-01
  feature nueva        ──▶  design.md ## Supersedes     ──▶  lista o `none` (AC-06)

  pytest               ──▶  test_harness spec index     ──▶  verde si índice honesto (AC-07)
  00 - Proyecto DONE   ──▶  README status column        ──▶  Shipped o Superseded (AC-03)

  lector abre 032      ──▶  Supersession notice         ──▶  parcial 034/0063, cuerpo intacto (AC-04)
  ./build.sh --check   ──▶  Global/cursor twins         ──▶  GLOBAL_TREE_SYNC_OK (AC-08)
```

---

## AC-01 — Law stack en doctrina de arranque

**Given** los tres artefactos de arranque (`.cursor/rules/00-harness.mdc`,
`Global/_canonical/agents/orchestrator.md`, `TIPS-USO.md`)

**When** un lector busca precedencia cross-feature

**Then** encuentra el mismo orden: (1) código/tests/generate, (2) ADR Accepted más nuevo,
(3) spec feature activa, (4) Shipped/Superseded = histórico; y TIPS apunta a harness/orchestrator
sin repetir el párrafo entero.

---

## AC-02 — Índice completo

**Given** el conjunto de carpetas `docs/specs/[0-9][0-9][0-9]-*/spec.md` en el repo raíz

**When** se lee `docs/specs/README.md`

**Then** cada id numérico tiene exactamente una fila con link al spec; PROYECTO/000-ejemplo excluido.

---

## AC-03 — Status alineado a notas

**Given** una línea `fase \`DONE\`` en `00 - Proyecto.md` para feature `<id>`

**When** se lee la fila `<id>` del índice

**Then** el status es `Shipped` o `Superseded by …` (nunca `Approved`/`Draft`).

**Given** 032 en `PACKAGE_GATES`, 033 en `INTEGRATION`, 011 en `BLOCKED`

**When** se lee su fila

**Then** ninguna dice `Shipped`.

---

## AC-04 — Cartel 032

**Given** `docs/specs/032-cursor-como-runtime/spec.md`

**When** se abre el archivo

**Then** `## Supersession notice` precede al cuerpo original; menciona supersede parcial AC-06 por 034 y
ADR-0063; el texto bajo el cartel no fue reescrito.

---

## AC-05 — ADR-0067

**Given** `docs/adr/0067-spec-index-and-precedence.md`

**When** se consulta el índice ADR

**Then** fila Accepted con título coherente; el ADR declara índice como tabla de vigencia y prohíbe
reescribir actas.

---

## AC-06 — Supersedes en diseño

**Given** `architect.md` y `feature-contract/SKILL.md` canónicos

**When** una feature nueva entra a diseño

**Then** la plantilla exige `## Supersedes` en `design.md` con formato `- <id> · <cláusula> · <ADR>` o `none`.

---

## AC-07 — Test de índice

**Given** el test `test_spec_index_matches_disk_and_project_notes` (nombre tentativo)

**When** `python3 -m unittest tests.test_harness.<TestClass>.<test>` corre

**Then** falla si falta fila, status fuera del vocabulario cerrado, o DONE sin Shipped/Superseded.

---

## AC-08 — Build check

**Given** cambios en `Global/_canonical/**`

**When** `./build.sh --check` corre en CI/local

**Then** exit 0 (`GLOBAL_TREE_SYNC_OK`).
