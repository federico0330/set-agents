# SET-AGENTES — notas

<!-- notas:auto -->
## Features

- [[features/002-adaptive-pi-orchestration|002-adaptive-pi-orchestration]] — fase `BLOCKED` · paquetes 0/1 · **BLOCKED**
- [[features/003-trusted-routing-pi-runtime|003-trusted-routing-pi-runtime]] — fase `DONE` · paquetes 1/1 · **DONE**
- [[features/004-adaptive-dispatch|004-adaptive-dispatch]] — fase `DONE` · paquetes 3/3 · **DONE**
- [[features/005-portable-harness|005-portable-harness]] — fase `DONE` · paquetes 3/3 · **DONE**
- [[features/006-execution-graph|006-execution-graph]] — fase `DONE` · paquetes 1/1 · **DONE**
- [[features/007-quota-visibility|007-quota-visibility]] — fase `DONE` · paquetes 3/3 · **DONE**
- [[features/008-dynamic-selection|008-dynamic-selection]] — fase `DONE` · paquetes 1/1 · **DONE**
- [[features/009-self-application|009-self-application]] — fase `DONE` · paquetes 3/3 · **DONE**
- [[features/010-spawn-provenance|010-spawn-provenance]] — fase `DONE` · paquetes 1/1 · **DONE**
- [[features/011-quota-failover|011-quota-failover]] — fase `BLOCKED` · paquetes 0/1 · **BLOCKED**
- [[features/012-discovered-inventory|012-discovered-inventory]] — fase `DONE` · paquetes 1/1 · **DONE**
- [[features/013-pi-interactive-target|013-pi-interactive-target]] — fase `DONE` · paquetes 1/1 · **DONE**
- [[features/014-model-preference-policy|014-model-preference-policy]] — fase `DONE` · paquetes 1/1 · **DONE**
- [[features/015-anthropic-dispatch-parity|015-anthropic-dispatch-parity]] — fase `DONE` · paquetes 1/1 · **DONE**
- [[features/016-audit-debt-repayment|016-audit-debt-repayment]] — fase `DONE` · paquetes 2/2 · **DONE**
- [[features/019-harness-evolution|019-harness-evolution]] — fase `DONE` · paquetes 5/5 · **DONE**
- [[features/020-honest-dashboard|020-honest-dashboard]] — fase `DONE` · paquetes 2/2 · **DONE**
- [[features/021-gates-que-no-mienten-ni-callan|021-gates-que-no-mienten-ni-callan]] — fase `DONE` · paquetes 2/2 · **DONE**
- [[features/022-disponibilidad-real|022-disponibilidad-real]] — fase `DONE` · paquetes 5/5 · **DONE**
- [[features/023-senales-de-consumo|023-senales-de-consumo]] — fase `DONE` · paquetes 4/4 · **DONE**
- [[features/024-listo-para-terceros|024-listo-para-terceros]] — fase `DONE` · paquetes 4/4 · **DONE**
- [[features/025-consola-minima-y-flexible|025-consola-minima-y-flexible]] — fase `DONE` · paquetes 6/6 · **DONE**
- [[features/026-orquestador-elige-modelo|026-orquestador-elige-modelo]] — fase `DONE` · paquetes 2/2 · **DONE**
- [[features/027-controles-que-miran|027-controles-que-miran]] — fase `DONE` · paquetes 4/4 · **DONE**
- [[features/028-narracion-que-ensena|028-narracion-que-ensena]] — fase `DONE` · paquetes 3/3 · **DONE**
- [[features/029-convenciones-antes-del-codigo|029-convenciones-antes-del-codigo]] — fase `DONE` · paquetes 1/1 · **DONE**
- [[features/030-guardas-que-no-se-pueden-prefijar|030-guardas-que-no-se-pueden-prefijar]] — fase `DONE` · paquetes 1/1 · **DONE**
- [[features/031-registro-correctivo|031-registro-correctivo]] — fase `DONE` · paquetes 1/1 · **DONE**

## Qué falta

- **002-adaptive-pi-orchestration** → corresponde tu decisión (ver Blocker)
- **002-adaptive-pi-orchestration** ⛔ bloqueo: HUMAN_DECISION_REQUIRED: user-authorized third repair cycle failed final review; five high findings remain and P1 exhau…
- **002-adaptive-pi-orchestration** 5 hallazgos abiertos
- **011-quota-failover** → corresponde tu decisión (ver Blocker)
- **011-quota-failover** ⛔ bloqueo: HUMAN_DECISION_REQUIRED: AC-06 exige una suscripción Anthropic controlada y genuinamente agotada junto a un proveedor a…
- **011-quota-failover** 5 tareas pendientes en P1-quota-failover

## Quick-fixes recientes

- 2026-08-18T02:48 — F-04 (020-honest-dashboard/P2-anclas-verificables) cerrado: verify.sh ahora pasa --profile go-zen a ./build.sh --output… (done)
- 2026-08-18T02:48 — P1F-01 cerrado: fix validado — cmd_transition ya tiene try/except alrededor del pop de repair_entry, cubriendo el caso … (done)
- 2026-08-12T15:24 — render_notes emitia trailing whitespace en la linea de un finding sin category ni summary, rompiendo git diff --check y… (done)
- 2026-08-06T13:33 — Preserve explicit --project context in set_agents_app.py script mode by aliasing __main__ for lazy routing_cli imports (done)
- 2026-08-03T02:36 — P1F-01: cmd_transition's repair_entry pop for PACKAGE_REPAIR was nested under 'if args.package_id:'; since --package-id… (done)

## Decisiones

- [[decisiones/2026-08-18 d5-dr03-asimetria-cobertura-anticacheo|D5-DR03: asimetría de cobertura anti-cacheo de fallos transitorios]]
- [[decisiones/2026-08-18 028-deuda-ac16-codex-drift|AC-16 AGENTS.codex.md: confirmación de deriva no registrada]]
- [[decisiones/2026-08-18 028-deuda-test-narracion-digest|tests/test_narracion_digest.py nunca se creó]]
- [[decisiones/2026-08-17 replanteo-028-imposible-el-motor-no-tiene-salida|Correccion: los paquetes de 028 tampoco se pueden replantear -- el motor no tiene salida]]
- [[decisiones/2026-08-17 replanteo-028-paquetes-sin-work-items|Los tres paquetes de 028 se replantean porque fueron creados sin work items]]
- [[decisiones/2026-08-17 d5-revision-correctiva-sin-camino-de-estado|La revision correctiva de D5 no puede aterrizar en el registro del paquete]]
- [[decisiones/2026-08-17 d5-relanzamiento-único-tras-watchdog|D5 relanzamiento único tras watchdog]]
- [[decisiones/2026-08-17 d4-presupuesto-spawn-agotado-antes-delta-final|D4 agotó su presupuesto de spawns antes del delta final]]

## Convenciones

| Feature | Cobertura | Orígenes |
|---|---|---|
| 031-registro-correctivo | 10/10 | n/a, notas |

## Referencias

- `ai/state/STATUS.md` — dashboard técnico
- `docs/adr/` — decisiones formales de arquitectura

_Actualizado: 2026-08-18T02:47:40+00:00_
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
