# 024 — Listo para terceros

- **Estado**: aprobado por Federico como capa C del plan A→B→C (2026-08-12): *"Quiero que la
  aplicación ya quede profesional para todas las personas que lo descarguen"*, con la decisión
  explícita **"producto que se clona y se usa"**.
- **ADRs**: 0047 (el estado no es el producto), 0048 (primer arranque honesto).

## El defecto de fondo

**El repo es el repo de Federico, no un producto.** Medido: `ai/state/` viaja en el clon (1.9 MB,
18 features) y `verify.sh:60` corre contra él, así que un tercero **hereda las features bloqueadas
002 y 011** de otra persona. `models.toml` fija las suscripciones de Federico en `true`, lo que
**apaga** la red tri-estado que detectaría una suscripción caída. Y no hay `LICENSE`.

## Paquetes

### PKG-1 — `estado-fuera-del-producto`

- **AC-01**: `git mv ai/state → docs/historia/estado-2026-08/` — trackeado, legible, **leído por
  nadie** — más `ai/state/` gitignoreado y sembrado desde `ai/state.seed/`. **El path se mantiene**:
  eso baja el diff de 15 módulos a cero.
- **AC-02**: `check-feature-state.py` **no se apaga, se le arregla la pregunta**: de *"¿hay algún
  spec entregado sin state file en toda la historia?"* a *"¿desde mi baseline?"*, conservando el
  degradado ruidoso.

### PKG-2 — `modelstoml-neutro`

- **AC-03**: `[subscriptions]` pasa a **ausente = auto**. Hoy los `true` de Federico apagan la red
  tri-estado que 022 construyó.
- **AC-04**: el small model deja de exigir Zen en la lane `local`, y **la lane `local` se renombra
  a lo que realmente es** — hoy no es local.
- **AC-05**: **overlay de config del usuario en `STATE_DIR`**. Es lo que desbloquea todo lo demás:
  hoy el wizard reescribe el `models.toml` trackeado y eso bloquea `--update` para siempre vía
  `tree_clean()`.

### PKG-3 — `primer-arranque-honesto`

- **AC-06**: el loop infinito de `install.sh:309-311` con `--yes`.
- **AC-07**: código aditivo `ROUTING_UNCONFIGURED` cuando **todas** las exclusiones fueron
  `PROVIDER_UNAUTHENTICATED`. El recién llegado recibe *"logueate con estos comandos"* en vez de un
  `HUMAN_DECISION_REQUIRED` mudo. **Sigue siendo fail-closed; deja de ser ciego.**
- **AC-08**: **dejar de reescribir los globales del usuario sin diff y consentimiento**.
  `install.py:196-206` le cambia el `model` de su `~/.codex/config.toml`. Es la misma familia que
  022/P4 cerró para `opencode.json`.

### PKG-4 — `higiene-de-repo-publico`

- **AC-09**: `LICENSE`, `CONTRIBUTING`, `CHANGELOG`, `SECURITY`. `HANDOFF-PASO9.md` fuera de la raíz.
- **AC-10**: ejemplos sin el nombre del cliente real.
- **AC-11**: **matriz de soporte medida, no asumida**. Lo medido hasta hoy: opencode tiene 47
  agentes y es el único de primera clase; **codex no tiene comandos**; **pi no tiene hooks** y su
  lane de dispatch corre con `--no-skills`; y —medido en esta sesión— **en opencode todos los roles
  del harness son `subagent` y sólo `orchestrator` es `primary`, así que `opencode run --agent <rol>`
  no despacha el rol: cae al agente por defecto con un warning**.
- **AC-12**: update re-apuntable. Hoy `origin/main` está hardcodeado y **un fork se rompe**.

## No-goals

- No se reescribe la historia de features: se mueve, no se borra.
- No se toca el sort key ni el ruteo.
- No se implementa la app de escritorio ni el chatbot: eso es visión, no esta feature.

## Riesgos

1. **Mover `ai/state` rompe 15 módulos.** Mitigado por AC-01: el path se mantiene.
2. **Apagar el estado de Federico le rompe su propio flujo.** El seed y el overlay tienen que dejar
   su máquina funcionando igual; probarlo en su HOME real es **no-goal**, se prueba con fixtures.
3. **La matriz de soporte envejece.** Por eso se declara medida y con fecha, no como promesa.

## Gates

Por paquete: suite en verde, `verify.sh` → `VERIFY_PASS`, `build.sh --check` → `GLOBAL_TREE_SYNC_OK`
+ `BUILD_CHECK_PASS`, ACs con evidencia `file:line`. Review independiente, repair, delta review.

## Criterio de cierre

Clonar el repo en un `HOME` limpio sin credenciales y verificar que **arranca**, que **no hereda**
las features de Federico, y que el primer spawn dice *"logueate"* en vez de
`HUMAN_DECISION_REQUIRED`.
