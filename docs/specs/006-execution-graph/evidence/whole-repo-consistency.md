# 006-execution-graph — evidencia de consistencia whole-repo (2026-07-30)

**Esta NO es evidencia de fase `INTEGRATION`, y no gatilla ninguna transición.** 006 se queda en
`PACKAGE_ACCEPTED` para siempre, por diseño ya escrito en `docs/specs/006-execution-graph/spec.md`
(contrato 1.2.0): `init` solo declaró los AC de P3 (AC-20..AC-29), sin backfillear P1/P2 (entregados
fuera de la máquina de estados el 2026-07-28, ver `docs/notas/decisiones/2026-07-28
feature-006-delivered-outside-state-machine.md`). Llamar `transition INTEGRATION` o `transition DONE`
sobre esta feature afirmaría que toda la feature —no solo lo trackeado— quedó verificada, lo cual sería
falso. Este archivo existe únicamente para dejar registro de que la pasada de consistencia whole-repo de
esta noche (motivada por la integración de 005-portable-harness) también corrió contra el trabajo
aceptado de 006, sin que eso implique ningún avance de fase.

## Gates corridos contra el árbol de trabajo actual

Nada está commiteado esta sesión (regla de sesión: solo se commitea a pedido explícito del usuario).
`HEAD` sigue en `898c539669b840e5b5d78a97f484b9abef0df9a6`, el mismo sha que el `diff_ref` histórico de
`P3-graph-view` — pero el trabajo real vive en el árbol de trabajo sin commitear. Estos gates verifican
el árbol vivo, no un commit.

- `./ai/scripts/verify.sh` → **`VERIFY_PASS`** (457 tests, 0 skips, `GLOBAL_PORTABILITY_OK`,
  `CANONICAL_PATHS_OK`, `FEATURE_STATE_OK`).
- `./build.sh --check` → **`SELF_SCAFFOLD_SYNC_OK files=2`** (`ai/scripts/feature-state.py` y
  `PROYECTO/ai/scripts/feature-state.py` siguen byte-idénticos).

## AC-20..AC-29 contra el árbol de hoy

| AC | Qué exige | Estado |
|---|---|---|
| AC-20 | Edges solo por join estructural (nunca heurístico) | Sostenido — sin cambios desde P3-graph-view aceptado |
| AC-21 | `--commit` en `record-repair`, formato 7-40 hex, fail-open ante git ausente/timeout | Sostenido |
| AC-22 | Subcomando `graph`: inventario de node types, namespaces `sg_` vs nodos disjuntos | Sostenido |
| AC-23 | Esqueleto de estado vacío | Sostenido |
| AC-24 | `render_notes()` best-effort + backlink `[[grafo]]` + guarda de nombre reservado | Sostenido |
| AC-25 | `set-agents --graph` como wrapper de subprocess | Sostenido |
| AC-26 | Edge `bloqueó` desde `data["blockers"]`, 3 ramas (match/none/unmatched) | Sostenido |
| AC-27 | Mínimos de label por node type, fallback rol-o-actor en reviews | Sostenido |
| AC-28 | Atomicidad del retiro del waiver + los 4 grupos de aserciones reales | Sostenido |
| AC-29 | Tolerancia a historia legada / política de fixtures sintéticos | Sostenido |

Ningún hallazgo nuevo. Sin cambios de código en este paso — es una relectura de consistencia, no una
re-revisión de paquete (el integrador no reabre paquetes ya aceptados por observaciones cosméticas).

## Veredicto

Consistente con el resto del repo tal como está esta noche. `006-execution-graph` permanece
`PACKAGE_ACCEPTED`, sin transición de fase, sin `record-gate`, sin panel de revisión nuevo.
