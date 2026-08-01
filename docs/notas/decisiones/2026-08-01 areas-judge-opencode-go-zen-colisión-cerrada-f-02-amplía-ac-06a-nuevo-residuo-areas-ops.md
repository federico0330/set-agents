# areas.judge.opencode.go-zen colisión CERRADA (F-02, amplía AC-06a); nuevo residuo areas.ops

<!-- notas:auto -->
- fecha: 2026-08-01 · actor: repair-agent
- alcance: [[features/015-anthropic-dispatch-parity|015-anthropic-dispatch-parity]] · [[features/015-anthropic-dispatch-parity/P1-anthropic-dispatch-parity|P1-anthropic-dispatch-parity]]

## Contexto

015 repair, panel RP-01, finding F-02: el test de AC-06(i) original angostaba DOS universos a la vez -- lado área a [areas.audit] solo, y lado rol a models_config.IMPLEMENT_DUTIES (que no cubre los cuatro roles tiered de duty=audit: package-reviewer, delta-reviewer, security-auditor, finding-verifier). Por eso la colisión idéntica en [areas.judge].opencode."go-zen" (mismo valor "openai/gpt-5.6-sol" que el residuo previamente aceptado, slug areas-judge-go-zen-colisiona-residuo-fuera-de-alcance) sobrevivió sin detectarse. El usuario fue consultado y eligió explícitamente ampliar AC-06(a) para cerrar también esa celda.

## Decisión

[areas.judge].opencode."go-zen" pasa de "openai/gpt-5.6-sol" a "openai/gpt-5.5" (mismo valor y mismo patrón que [areas.audit], models.toml:115). El test de AC-06(i) se reescribe genérico como el spec siempre pidió: TODAS las celdas [areas.*].opencode."go-zen" contra TODOS los roles con tabla tiers (sin filtro de duty). Ese escaneo genérico encontró una TERCERA colisión no nombrada por nadie: [areas.ops].opencode."go-zen" == "openai/gpt-5.6-terra", idéntico al valor de tier frontier de la misma escalera de seis roles. Esa celda NO se toca -- está fuera del alcance que el usuario autorizó para este repair (solo judge) -- se documenta como residuo nuevo, explícito, afirmado por el propio test de regresión (no oculto), en ADR-0019 D8 y aquí, para que el orquestador/usuario decida a propósito.

## Consecuencias

El residuo previo sobre [areas.judge] queda CERRADO (superseded por esta entrada, slug distinto -- log-decision no soporta amend, ver slug viejo areas-judge-go-zen-colisiona-residuo-fuera-de-alcance). Un futuro paquete que quiera cerrar [areas.ops].opencode."go-zen" debe leer ADR-0019 D8 y esta entrada antes de tocar esa celda; el test test_ac06a_no_area_go_zen_value_collides_with_any_tiered_roles_go_zen_ladder falla si esa colisión se resuelve sin actualizar la aserción, y falla también si aparece una CUARTA celda colisionando sin que nadie la nombre.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
