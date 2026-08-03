# AC-08/AC-14 supersedes ac09-ac10-pi-minimal-target-accepted: pi gains a real install.py target and generated agent tree

<!-- notas:auto -->
- fecha: 2026-08-02 · actor: implementer
- alcance: [[features/013-pi-interactive-target|013-pi-interactive-target]] · [[features/013-pi-interactive-target/P1-pi-interactive-target|P1-pi-interactive-target]]

## Contexto

004-adaptive-dispatch/P3-pi-lane's 2026-07-27 decision (slug ac09-ac10-pi-minimal-target-accepted, ai/state/decisions-log.jsonl) asserted 'install.py stays untouched; P3 adds no generated pi agent tree' for the dispatch-lane-only surface it shipped. 013-pi-interactive-target adds a SEPARATE, interactive pi surface (opening pi directly, not through the dispatch lane) that this old decision's own text does not anticipate.

## Decisión

This decision explicitly supersedes ac09-ac10-pi-minimal-target-accepted for the interactive surface: install.py gains a fourth target, pi -> ~/.pi/agent, and generate.py emits a real Global/pi/agents/<role>.md per active-roster role, Global/pi/skills/**, Global/pi/prompts/**, and Global/pi/AGENTS.md. The dispatch lane's own mechanism (canonical prompt passed verbatim via --append-system-prompt, no install-time substitution) is unchanged and the old decision's reasoning stays correct for that lane specifically.

## Consecuencias

docs/adr/0007-pi-lane.md gains an in-file amendment near its Decision 4; docs/adr/0017-pi-interactive-target.md records this supersession as a first-class decision; docs/adr/README.md rows for 0007/0017 updated.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
