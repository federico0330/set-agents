# ADR-0077 — Auto-setup de proyecto: orquestador detecta; bootstrapper programa el overlay; no hay agente “autoprogramable” nuevo

- Estado: **Accepted** (2026-09-23).
- Extiende ADR-0008 (dos raíces), ADR-0025 (resolver primero), ADR-0038 (propose→approve humano), ADR-0054 (posturas).
- Rechaza un subagente de checklist / “self-programming” dedicado al seteo.

## Contexto

El harness debe dejar de depender de que el humano tipeé `migrate-legacy-state`, `log-deferred` o
`bus-post`. A la vez hace falta un **overlay de proyecto** (`packs.local.toml`, y con el tiempo
tools/MCP de proyecto) distinto del catálogo global (`tools.toml`) y del overlay de máquina
(`tools.local.toml` en `HARNESS_HOME`, ADR-0038 F-11).

La pregunta de producto: ¿quién hace ese auto-seteo — el orquestador o un subagente que “se
autoprograma”?

## Decisión

### Tres capas, tres dueños — no un cuarto agente

| Qué | Quién | Por qué |
|---|---|---|
| Detectar necesidad (estado legacy, overlay ausente, cierre de sesión, handoff entre roles) y **disparar** el verbo de harness | **Orquestador** | Es el PO de la sesión; Hard boundary ya permite el canal `feature-state.py` y el catálogo ADR-0025/0038. No inventa contenido de packs. |
| Verbos **determinísticos** (`migrate-legacy-state`, `log-deferred`, `bus-post`/`bus-list`, leer Estado) | **CLI del harness**, invocados por el orquestador (o por un mutador cuando el Hard boundary lo exige) | Cero juicio; backup + schema; ya allowlisteados vía `python3 ai/scripts/feature-state.py …`. |
| **Programar el overlay de proyecto** (qué packs opcionales, qué tools/MCP/skills de stack inferido → `--tools-propose`, texto de `packs.local.toml`) | **`project-bootstrapper`** (rol existente) | Ya posee discovery conservador del repo. Eso **es** la “autoprogramación” del proyecto: escribe propuestas de overlay, no doctrina global. |
| Aprobar binarios / sudo / entradas nuevas al catálogo | **Humano** (`--tools-approve`) | ADR-0038 intacto; ningún agente se auto-aprueba. |

### Qué queda fuera a propósito

- **No** se crea un agente `auto-setup` / `self-programmer` / relay de checklist. Contradice el
  precedente gentle-ai (no checklist agents) y duplicaría `project-bootstrapper`.
- **No** el orquestador edita `packs.local.toml` ni `tools.local.toml` a mano: detecta, delega o
  corre CLI; el juicio de perfil es del bootstrapper; la mutación del catálogo abierto es
  propose→humano→approve.
- Mid-feature, un worker que necesita un CLI ausente sigue el canal existente: **implementer**
  propone / instala curado; el orquestador retransmite la pregunta de approve — sin spawn de
  “setup agent”.

### Auto-migrate y cierre de sesión (sin comando manual del usuario)

1. Si `ai/state/features/<id>.json` carece de `schema_version == 1` o trae `packages` en forma
   dict (legacy), `resume`/`next`/`status` corren **migrate-legacy-state** con backup
   `.bak.<ts>` antes de validar. El usuario no tiene que conocer el verbo; el orquestador no
   pregunta “¿migro?”.
2. Al cerrar sesión / encargo: mejoras fuera de alcance van a `log-deferred`. 
   `describe_next_step` **nunca** lee el deferred log — no reabre trabajo por sugerencias.
3. Handoffs entre roles usan `bus-post` / `bus-list` bajo `ai/state/bus/` (append-only), sin
   agente intermediario.

### Overlay explícito en consola

Estado / Perfil de trabajo nombran tres capas:

1. **Global (harness)** — `tools.toml` + packs `always_on` en `Global/_canonical/packs/`.
2. **Máquina / clone** — `tools.local.toml` en `HARNESS_HOME` (ADR-0038).
3. **Proyecto** — `packs.local.toml` en `PROJECT_ROOT` (dueño: bootstrapper + humano).

## Consecuencias

- Doctrina del orquestador y de `project-bootstrapper` citan esta ADR; generate propaga a los
  cinco árboles.
- Un colega en Ubuntu no necesita memorizar subcomandos de higiene: el orquestador los corre.
- El perfil de un repo concreto sigue siendo auditable en `packs.local.toml`, no escondido en
  chat.
- Extensiones futuras de tools/MCP **por proyecto** reusan el mismo dueño (bootstrapper +
  propose→approve), sin inventar un sexto rol.

## Alternatives rejected

1. **Orquestador escribe solo el overlay** — viola Hard boundary (“never edit files”) y mezcla
   juicio de stack con conducción de sesión.
2. **Subagente nuevo “auto-setup”** — checklist relay; coste de spawn sin expertise nueva frente
   a `project-bootstrapper`.
3. **Sólo documentación (“corré migrate a mano”)** — el dolor original (ScrappingML 012 bloqueado
   en `HUMAN_DECISION_REQUIRED` por schema legacy) vuelve.
