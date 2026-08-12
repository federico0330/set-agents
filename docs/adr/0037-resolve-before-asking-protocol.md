# ADR-0037 — Resolvé antes de preguntar: protocolo de cuatro fuentes antes de cualquier pregunta

- Estado: Accepted (2026-08-11). Feature 019-harness-evolution, PKG-4 (`P4-doctrine-human-layer`).
  Extends ADR-0025 (resolve-first autonomy) — no lo re-litiga: ADR-0025 decidió QUÉ categorías son
  askable (credenciales, plataforma nombrada, CLI faltante) y con qué válvulas; esta ADR decide el
  PROCEDIMIENTO que corre antes de decidir que algo cae en esas categorías, para cualquier pregunta,
  no solo las de ADR-0025.

## Contexto

`orchestrator.md`'s Question policy (`Global/_canonical/agents/orchestrator.md:517-553`) ya lista lo
askable y ADR-0025 ya resolvió el carve-out de plataforma nombrada, `--tools-install` automático y el
flujo interactivo antes de pedir credenciales. Pero esas resoluciones viven como **excepciones puntuales
dentro de cada categoría** (missing credentials, missing CLI, plataforma nombrada) — no hay un paso
previo y genérico, aplicado a TODA pregunta candidata, que obligue a mirar lo que el propio repositorio
ya sabe antes de decidir que hace falta preguntar. En la práctica esto produjo preguntas evitables: el
pedido original ya nombraba la decisión, `docs/notas/` ya la tenía en "Qué falta" o "Approach y
decisiones", `ai/state/decisions-log.jsonl` ya la registraba de un turno anterior, o la spec/ADR
aprobados ya la resolvían — y el orquestador preguntaba de nuevo porque revisaba la categoría (¿es esto
una plataforma nombrada? ¿es un scope change?) sin revisar primero si la pregunta ya tenía respuesta en
alguna de esas cuatro fuentes.

## Decisión

1. **Protocolo "Resolvé antes de preguntar (ADR-0037)"**, insertado en
   `Global/_canonical/agents/orchestrator.md`'s `## Question policy`, **ANTES** de la lista de lo
   askable, con encabezado exacto y testeable: `**Resolvé antes de preguntar (ADR-0037)**`. Ninguna
   pregunta candidata sale sin pasar, en orden, por cuatro fuentes:
   1. el pedido original del turno o de la feature (¿ya lo dijo el usuario, aunque en otras palabras?),
   2. `docs/notas/` — específicamente las secciones "Qué falta" y "Approach y decisiones" de la nota de
      feature/paquete relevante,
   3. `ai/state/decisions-log.jsonl` (¿un turno anterior ya registró esta decisión con `log-decision`?),
   4. la spec aprobada y los ADRs (¿el documento vinculante ya lo fija?).

   Lo que alguna fuente ya resuelve **se ejecuta con `log-decision`, nunca se pregunta de nuevo** — el
   registro cita la fuente (qué nota, qué línea del log, qué ADR) para que la decisión sea auditable, no
   una afirmación de memoria (ADR-0026). Solo si las cuatro fuentes están genuinamente mudas sobre el
   punto, la pregunta candidata pasa a evaluarse contra la lista askable existente (producto
   incompatible, scope change, irreversible, credenciales, arquitectura sin ADR, etc.).
2. **El carve-out de plataforma nombrada (ADR-0025.2) queda como caso particular de esta regla
   general**, no como excepción suelta: es exactamente la fuente (1) — el pedido original ya resolvió el
   eje — aplicada al caso más frecuente. Se referencia desde el protocolo en vez de duplicar su texto.
3. **Espejos cortos (2-3 líneas) en las cuatro doctrinas por runtime** (`Global/_shared/CLAUDE.md`,
   `Global/_shared/AGENTS.pi.md`, `Global/_shared/AGENTS.opencode.md`, `Global/_shared/AGENTS.codex.md`)
   y en la skill `request-triage` (`Global/_canonical/skills/request-triage/SKILL.md`), que ya es donde
   el orquestador decide el modo y hace las primeras preguntas de scoping — el protocolo aplica ahí
   también, no solo en el flujo de paquete. Los espejos no repiten el texto completo del protocolo: cada
   uno nombra las cuatro fuentes en una o dos líneas y remite a `orchestrator.md` para el detalle.
4. **No se tocan los cuatro árboles generados** (`Global/opencode/AGENTS.md`, `Global/claude-code/CLAUDE.md`
   [via `Global/_shared/CLAUDE.md`], `Global/codex/AGENTS.md`, `Global/pi/AGENTS.md`): se regeneran con
   `./build.sh` desde `Global/_shared/*` y `Global/_canonical/agents/orchestrator.md`.

## Rejected alternatives

- **Un quinto ítem en la lista askable ("¿ya está resuelto en otro lado?") en vez de un protocolo
  previo.** Rechazado: mezclarlo con la lista de categorías askable perdería el orden explícito (pedido
  → notas → decisions-log → spec/ADR) y el hecho de que corre ANTES de evaluar la categoría, no como una
  categoría más.
- **Reescribir el carve-out de plataforma nombrada como excepción independiente, duplicando lógica.**
  Rechazado: el carve-out YA es un caso de "el pedido original resuelve el eje" — tratarlo aparte
  hubiera dejado dos reglas describiendo el mismo mecanismo con lenguaje distinto, exactamente el tipo
  de deriva doctrinal que este ADR busca cerrar.
- **Espejos completos del protocolo en cada doctrina de runtime.** Rechazado por el mismo motivo que
  ADR-0026 usó para sus propios espejos: `orchestrator.md` es la única fuente completa; los espejos
  existen para que un runtime sin acceso directo al agente completo (pi, codex) sepa que la regla
  existe, no para duplicar su texto entero.

## Fuera de alcance de esta ADR

`integrator.md`/`architect.md` (impacto humano en `docs/modules/`, ADR-0036) y `/explicar` son P4
también, pero mecanismos independientes de este protocolo — no dependen uno del otro.

## Consecuencias

- Una pregunta que el repositorio ya respondió en cualquiera de las cuatro fuentes deja de llegar al
  usuario; se ejecuta con `log-decision` citando la fuente.
- El carve-out de plataforma nombrada deja de leerse como una excepción aislada — es legible como una
  instancia de la regla general, lo que reduce la chance de que un futuro ADR agregue una quinta
  excepción suelta en vez de reconocerla como otra instancia de "el pedido original ya resolvió esto".
- Los runtimes sin el agente completo (pi, codex) tienen al menos el recordatorio corto de que el
  protocolo existe y dónde está el detalle.
