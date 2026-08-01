# 013-pi-interactive-target must sequence its own orchestrator.md work after 015 lands

<!-- notas:auto -->
- fecha: 2026-07-31 · actor: package-planner
- alcance: [[features/015-anthropic-dispatch-parity|015-anthropic-dispatch-parity]] · [[features/015-anthropic-dispatch-parity/P1-anthropic-dispatch-parity|P1-anthropic-dispatch-parity]]

## Contexto

015-anthropic-dispatch-parity (priority, ~12-day deadline) rewrites Global/_canonical/agents/orchestrator.md's Tiered dispatch section (AC-03/AC-04: same-lane/cross-lane-redirect/true-off-lane branching) and regenerates it into all 3 currently-generated harness copies. 013-pi-interactive-target (also in PACKAGE_PLANNING, no packages/owned_paths claimed yet) separately plans to convert this same canonical file into Global/pi/AGENTS.md (its own AC-14/ADR-0017 scope). Today there is no live ownership collision (013 has not created a package or claimed owned_paths), but the two features' plans genuinely touch the same source file.

## Decisión

015 lands first (priority + deadline). 013's own package-planning pass, whenever it runs create-package for its orchestrator.md/AGENTS.md work, must read Global/_canonical/agents/orchestrator.md in its POST-015 state (i.e. after this package's AC-03/AC-04 rewrite is accepted and integrated), not the pre-015 text this note was written against. This is not resolved unilaterally here -- 013's package-planner is responsible for re-reading the file live at its own planning time.

## Consecuencias

If 013's package-planning runs before 015-P1-anthropic-dispatch-parity is accepted/integrated, it must either wait or explicitly re-verify the file's content has not changed underneath it before claiming owned_paths on Global/_canonical/agents/orchestrator.md. No code or state change enforces this automatically -- it is a process note for the next package-planner invocation on 013.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
