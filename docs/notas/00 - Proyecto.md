# SET-AGENTES — notas

<!-- notas:auto -->
## Features

- [[features/002-adaptive-pi-orchestration|002-adaptive-pi-orchestration]] — fase `BLOCKED` · paquetes 0/1 · **BLOCKED**
- [[features/003-trusted-routing-pi-runtime|003-trusted-routing-pi-runtime]] — fase `DONE` · paquetes 1/1 · **DONE**
- [[features/004-adaptive-dispatch|004-adaptive-dispatch]] — fase `DONE` · paquetes 3/3 · **DONE**
- [[features/005-portable-harness|005-portable-harness]] — fase `DONE` · paquetes 3/3 · **DONE**
- [[features/006-execution-graph|006-execution-graph]] — fase `PACKAGE_ACCEPTED` · paquetes 1/1
- [[features/007-quota-visibility|007-quota-visibility]] — fase `DONE` · paquetes 3/3 · **DONE**
- [[features/008-dynamic-selection|008-dynamic-selection]] — fase `DONE` · paquetes 1/1 · **DONE**
- [[features/009-self-application|009-self-application]] — fase `DONE` · paquetes 3/3 · **DONE**
- [[features/010-spawn-provenance|010-spawn-provenance]] — fase `PACKAGE_ACCEPTED` · paquetes 1/1
- [[features/011-quota-failover|011-quota-failover]] — fase `BLOCKED` · paquetes 0/1 · **BLOCKED**
- [[features/012-discovered-inventory|012-discovered-inventory]] — fase `DONE` · paquetes 1/1 · **DONE**
- [[features/013-pi-interactive-target|013-pi-interactive-target]] — fase `DONE` · paquetes 1/1 · **DONE**
- [[features/014-model-preference-policy|014-model-preference-policy]] — fase `DONE` · paquetes 1/1 · **DONE**
- [[features/015-anthropic-dispatch-parity|015-anthropic-dispatch-parity]] — fase `DONE` · paquetes 1/1 · **DONE**
- [[features/016-audit-debt-repayment|016-audit-debt-repayment]] — fase `DONE` · paquetes 2/2 · **DONE**

## Qué falta

- **002-adaptive-pi-orchestration** ⛔ bloqueo: HUMAN_DECISION_REQUIRED: user-authorized third repair cycle failed final review; five high findings remain and P1 exhau…
- **002-adaptive-pi-orchestration** 5 hallazgos abiertos
- **006-execution-graph** → `INTEGRATION` — all packages accepted
- **010-spawn-provenance** → `INTEGRATION` — all packages accepted
- **011-quota-failover** ⛔ bloqueo: HUMAN_DECISION_REQUIRED: AC-06 exige una suscripción Anthropic controlada y genuinamente agotada junto a un proveedor a…
- **011-quota-failover** tareas pendientes en P1-quota-failover: additive schema/migration and invariants, narrow classifier + Pi terminal plumbing, BEGIN IMMEDIATE close/exhaust/authorize idempotent transition + selection exclusion, deterministic routing/migration/concurrency tests, credential-gated real exhausted-provider E2E runner/evidence
- **016-audit-debt-repayment** 1 hallazgos abiertos

## Quick-fixes recientes

- 2026-08-03T02:36 — P1F-01: cmd_transition's repair_entry pop for PACKAGE_REPAIR was nested under 'if args.package_id:'; since --package-id… (done)
- 2026-07-30T01:22 — P2-vault-mandatory (accepted): exclude_notes_from_git/_notes_currently_excluded chequeaban (project/'.git').is_dir(), f… (done)
- 2026-07-30T01:22 — P2-vault-mandatory (accepted): write_vault_registry_entry resolvía el vault_path a través del symlink recién creado, gu… (done)

## Decisiones

- [[decisiones/2026-08-03 ac-01i-grunt-no-flip-en-verified-review-2-proveedores|AC-01(i): grunt no puede flippear provider en verified review con catalogo de 2 proveedores]]
- [[decisiones/2026-08-03 audit-debt-006-p2-cierre-parcial-016|Cierre parcial de audit-debt-006-p2: PR-07/08/09 saldadas por 016; PR-06/10/11 siguen diferidas]]
- [[decisiones/2026-08-02 p1f-01-repair-entry-pop-package-id-opcional|P1F-01 aceptado como deuda low: el pop de repair_entry depende del --package-id opcional]]
- [[decisiones/2026-08-02 build-staging-no-concurrent-full-gates|Los gates de suite completa no se corren en paralelo: build.sh colisiona en staging compartido]]
- [[decisiones/2026-08-02 ac-13-roster-half-environment-gated|AC-13: la mitad de discoverability viva del roster queda environment-gated, no BLOCKED de feature]]
- [[decisiones/2026-08-02 ac09-ac10-pi-minimal-target-superseded-by-013|AC-08/AC-14 supersedes ac09-ac10-pi-minimal-target-accepted: pi gains a real install.py target and generated agent tree]]
- [[decisiones/2026-08-02 pasada-integracion-2026-08-02|Pasada de integración 2026-08-02: 008 y 012 a DONE; 006 y 010 quedan PACKAGE_ACCEPTED por diseño]]
- [[decisiones/2026-08-01 areas-ops-opencode-go-zen-colision-cerrada-f-03-ac-06a-queda-genericamente-cerrado|areas.ops.opencode.go-zen colision CERRADA (F-03); AC-06(a) queda genericamente cerrado, sin residuo]]

## Referencias

- `ai/state/STATUS.md` — dashboard técnico
- `docs/adr/` — decisiones formales de arquitectura

_Actualizado: 2026-08-03T00:38:12+00:00_
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._

### Lo que queda (actualizado 2026-08-02)

**Pasada completa 2026-08-02 (A–D):** 008 y 012 a `DONE` con gate global verde; 006 y 010 validadas
con `pass` pero quedan en `PACKAGE_ACCEPTED` **por diseño registrado** (spec 006 §proceso: P1/P2
salieron por waiver; HANDOFF-PASO9 §5.5 para 010) — su "próximo paso: INTEGRATION" del tablero es
fraseo automático, no pendiente real. Además, con ciclo completo cada una:

- ~~**013-pi-interactive-target**~~ — **`DONE`**: `pi` interactivo es el cuarto destino generado
  (`Global/pi/**` → `~/.pi/agent/`) con guardia anti-colisión fail-closed, E2E real contra pi 0.83.0,
  cierre del dispatch-lane y ADR-0017. La mitad "roster vivo vía pi-subagents" de AC-13 quedó
  environment-gated (test opt-in `SET_AGENTS_PI_E2E=1`, decisión registrada).
- ~~**014-model-preference-policy**~~ — **`DONE`** con contrato 3.2.0 (re-baselineado post-015,
  aprobado 2026-08-02): taxonomía decision/grunt/build/unscoped, `model-preference.toml` opt-in con
  CLI, sesgo en posición 3 del sort-key (independencia y tier inviolables), ADR-0018. Efecto real
  probado en vivo sobre 6 roles con tiers.
- **016-audit-debt-repayment** — **`DONE`**: PR-07/08/09 saldadas + limpieza (AC-08) + reason-code
  del redirect. Quedan diferidas PR-06/PR-10/PR-11 y la nueva deuda low P1F-01 (fix anotado).
- **008-dynamic-selection P3 (budget-aware-selection)** — sigue bloqueada esperando a que
  **011-quota-failover** llegue a `accepted`. 011 a su vez está `BLOCKED` esperando un agotamiento real
  de cuota (decisión explícita del usuario: no forzarlo).
- **002-adaptive-pi-orchestration** — sigue `BLOCKED`, retirada formalmente como superseded por 003
  (decisión ya registrada). No requiere más trabajo, solo queda así por diseño.
- **Idea "Gateway" (V2, del usuario)** — un modelo liviano y fijo que actúa de pasamanos y decide
  dinámicamente qué modelo usa cada rol, para que solo un agente tenga algo hardcodeado. Mencionada
  durante el diseño de 014, deliberadamente diferida — no diseñada todavía.
- **Feature nueva propuesta durante 015, no abierta**: extender el mecanismo de redirect cross-lane
  para que revisores sigan funcionando después del día ~13 (cuando GPT se pierda de verdad y quede un
  solo proveedor). 015 resuelve la ventana de ~12 días con dos proveedores; después de eso las
  revisiones automáticas vuelven a frenar hasta que exista un segundo proveedor real (Kimi u otro).
  Aceptado explícitamente como límite, no como bug — pero es el próximo cuello de botella real.
