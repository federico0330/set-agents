# SET-AGENTES — notas

<!-- notas:auto -->
## Features

- [[features/002-adaptive-pi-orchestration|002-adaptive-pi-orchestration]] — fase `BLOCKED` · paquetes 0/1 · **BLOCKED**
- [[features/003-trusted-routing-pi-runtime|003-trusted-routing-pi-runtime]] — fase `DONE` · paquetes 1/1 · **DONE**
- [[features/004-adaptive-dispatch|004-adaptive-dispatch]] — fase `DONE` · paquetes 3/3 · **DONE**
- [[features/005-portable-harness|005-portable-harness]] — fase `DONE` · paquetes 3/3 · **DONE**
- [[features/006-execution-graph|006-execution-graph]] — fase `PACKAGE_ACCEPTED` · paquetes 1/1
- [[features/007-quota-visibility|007-quota-visibility]] — fase `DONE` · paquetes 3/3 · **DONE**
- [[features/008-dynamic-selection|008-dynamic-selection]] — fase `PACKAGE_ACCEPTED` · paquetes 1/1
- [[features/009-self-application|009-self-application]] — fase `DONE` · paquetes 3/3 · **DONE**
- [[features/010-spawn-provenance|010-spawn-provenance]] — fase `PACKAGE_ACCEPTED` · paquetes 1/1
- [[features/011-quota-failover|011-quota-failover]] — fase `BLOCKED` · paquetes 0/1 · **BLOCKED**
- [[features/012-discovered-inventory|012-discovered-inventory]] — fase `PACKAGE_ACCEPTED` · paquetes 1/1
- [[features/013-pi-interactive-target|013-pi-interactive-target]] — fase `PACKAGE_PLANNING` · paquetes 0/0
- [[features/015-anthropic-dispatch-parity|015-anthropic-dispatch-parity]] — fase `DONE` · paquetes 1/1 · **DONE**

## Qué falta

- **002-adaptive-pi-orchestration** ⛔ bloqueo: HUMAN_DECISION_REQUIRED: user-authorized third repair cycle failed final review; five high findings remain and P1 exhau…
- **002-adaptive-pi-orchestration** 5 hallazgos abiertos
- **006-execution-graph** → `INTEGRATION` — all packages accepted
- **008-dynamic-selection** → `INTEGRATION` — all packages accepted
- **010-spawn-provenance** → `INTEGRATION` — all packages accepted
- **011-quota-failover** ⛔ bloqueo: HUMAN_DECISION_REQUIRED: AC-06 exige una suscripción Anthropic controlada y genuinamente agotada junto a un proveedor a…
- **011-quota-failover** tareas pendientes en P1-quota-failover: additive schema/migration and invariants, narrow classifier + Pi terminal plumbing, BEGIN IMMEDIATE close/exhaust/authorize idempotent transition + selection exclusion, deterministic routing/migration/concurrency tests, credential-gated real exhausted-provider E2E runner/evidence
- **012-discovered-inventory** → `INTEGRATION` — all packages accepted
- **013-pi-interactive-target** → `PACKAGE_IMPLEMENTATION` — plan next coherent package

## Quick-fixes recientes

- 2026-07-30T01:22 — P2-vault-mandatory (accepted): exclude_notes_from_git/_notes_currently_excluded chequeaban (project/'.git').is_dir(), f… (done)
- 2026-07-30T01:22 — P2-vault-mandatory (accepted): write_vault_registry_entry resolvía el vault_path a través del symlink recién creado, gu… (done)

## Decisiones

- [[decisiones/2026-08-01 areas-ops-opencode-go-zen-colision-cerrada-f-03-ac-06a-queda-genericamente-cerrado|areas.ops.opencode.go-zen colision CERRADA (F-03); AC-06(a) queda genericamente cerrado, sin residuo]]
- [[decisiones/2026-08-01 areas-judge-opencode-go-zen-colisión-cerrada-f-02-amplía-ac-06a-nuevo-residuo-areas-ops|areas.judge.opencode.go-zen colisión CERRADA (F-02, amplía AC-06a); nuevo residuo areas.ops]]
- [[decisiones/2026-08-01 areas-judge-go-zen-colisiona-residuo-fuera-de-alcance|areas.judge.opencode.go-zen colisiona con la misma escalera implementer, fuera de alcance]]
- [[decisiones/2026-08-01 setting-sources-user-confía-en-scope-generado-desde-el-propio-repo|setting-sources user confía en scope generado desde el propio repo]]
- [[decisiones/2026-08-01 redirect-de-effective-runtime-es-silencioso-sin-reason-code|Redirect de _effective_runtime es silencioso, sin reason_code]]
- [[decisiones/2026-07-31 013-pi-interactive-target-must-sequence-its-own-orchestrator-md-work-after-015-lands|013-pi-interactive-target must sequence its own orchestrator.md work after 015 lands]]
- [[decisiones/2026-07-30 p2-discovered-inventory-pasa-a-ser-su-propia-feature-012|P2-discovered-inventory se separa de 008 y pasa a ser la feature 012, mismo patrón que 010/006]]
- [[decisiones/2026-07-30 family-se-normaliza-no-se-captura-del-vendor-para-ids-compartidos|Para modelos compartidos entre lanes de OpenCode, family se normaliza (colisiona), no se copia del vendor]]

## Referencias

- `ai/state/STATUS.md` — dashboard técnico
- `docs/adr/` — decisiones formales de arquitectura

_Actualizado: 2026-08-01T22:46:55+00:00_
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._

### Lo que queda (2026-08-01, sin formalizar en specs)

- **013-pi-interactive-target** — contrato aprobado, todavía sin paquete. Falta `package-planner` +
  implementación. Importante: su propio trabajo sobre `Global/_canonical/agents/orchestrator.md` debe
  releer el texto POST-015 (ya registrado como decisión), no el que tenía antes.
- **014-model-preference-policy** — contrato en 3.1.0, todavía sin pasar por aprobación final del
  usuario. Ahora que 015 está `DONE`, su clase `build` (implementadores) y `grunt` (revisores) van a
  tener efecto real apenas se apruebe e implemente — antes de 015 hubiera quedado inerte para ambas.
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
