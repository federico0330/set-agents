# pi y opencode pasan a instalacion real; PI_PINNED_VERSION 0.81.1 -> 0.84.0

<!-- notas:auto -->
- fecha: 2026-08-07 · actor: claude-code

## Contexto

pi update/opencode upgrade no funcionaban: ~/.local/bin/{pi,opencode} eran wrappers pnpm-dlx (cache temporal + MINIMUM_RELEASE_AGE=7200) sin instalacion que actualizar. El pin del harness (0.81.1) quedo atras del interactivo (0.83.0).

## Decisión

Wrappers respaldados como *.bak. opencode instalado via installer oficial (~/.opencode/bin, 1.18.14, 'opencode upgrade' nativo funciona). pi instalado global con pnpm (global-bin-dir=~/.local/bin, 0.84.0; se actualiza con 'pi update' nativo o pnpm add -g @earendil-works/pi-coding-agent@latest). Bump deliberado de PI_PINNED_VERSION a 0.84.0 tras verificar en vivo que pi 0.84.0 conserva todos los flags del spawner (--print --mode json --no-session --no-extensions --no-context-files --no-skills --no-prompt-templates --tools --append-system-prompt --thinking).

## Consecuencias

set_agents_spawn.py --doctor verde con pinned_version 0.84.0; warm-up pnpm dlx @0.84.0 ok; tests test_routing+test_pi_effort 242 OK.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
