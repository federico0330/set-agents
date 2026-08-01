# areas.judge.opencode.go-zen colisiona con la misma escalera implementer, fuera de alcance

<!-- notas:auto -->
- fecha: 2026-08-01 · actor: implementer
- alcance: [[features/015-anthropic-dispatch-parity|015-anthropic-dispatch-parity]] · [[features/015-anthropic-dispatch-parity/P1-anthropic-dispatch-parity|P1-anthropic-dispatch-parity]]

## Contexto

AC-06(a) (015-anthropic-dispatch-parity) corrige [areas.audit].opencode."go-zen" (colisionaba con [roles.implementer.tiers.balanced].opencode."go-zen", ambos "openai/gpt-5.6-sol"). Durante la implementación se detectó que [areas.judge].opencode."go-zen" tiene EXACTAMENTE el mismo valor "openai/gpt-5.6-sol" y por lo tanto la MISMA colisión latente contra la escalera dinámica implementer/debugger/etc.

## Decisión

No se toca. El contrato aprobado (Non-goals) restringe AC-06 a exactamente dos celdas nombradas de models.toml ([areas.audit].opencode."go-zen" y [areas.audit]/[areas.judge].claude); [areas.judge].opencode."go-zen" es una tercera celda no nombrada, y tocarla sería una ampliación de alcance no aprobada. Se documenta como residuo explícito en docs/adr/0019-anthropic-dispatch-parity.md (D8) y aquí, para que un futuro paquete lo cierre a propósito, no por descubrimiento accidental.

## Consecuencias

Deuda registrada, no bloquea P1-anthropic-dispatch-parity. Un futuro paquete que edite [areas.judge] debe leer ADR-0019 D8 antes de tocar esa celda.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
