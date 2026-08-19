# 033-menos-espera-menos-cuota

<!-- notas:auto -->
## Estado

- fase: `INTEGRATION` · modo: scoped · revisión 244
- spec: `docs/specs/033-menos-espera-menos-cuota/spec.md` (hash `18dcffafa809`)

## Criterios de aceptación

- AC-1.1
- AC-1.2
- AC-1.3
- AC-1.4
- AC-1.5
- AC-1.6
- AC-1.7
- AC-2.1
- AC-2.2
- AC-2.3
- AC-2.4
- AC-2.5
- AC-3.1
- AC-3.2
- AC-3.3
- AC-3.4
- AC-3.5
- AC-3.6
- AC-3.7
- AC-3.8
- AC-4.1
- AC-4.2
- AC-4.3
- AC-4.4
- AC-4.5
- AC-5.1
- AC-5.2
- AC-5.3
- AC-5.4
- AC-5.5
- AC-5.6
- AC-6.1
- AC-6.2
- AC-6.3
- AC-6.4
- AC-6.5
- AC-6.6

## Paquetes

- [[features/033-menos-espera-menos-cuota/PKG-1|PKG-1]] — accepted · Una sola dimension opencode: colapsar go-zen/zen/openai-only en un solo valor por area
- [[features/033-menos-espera-menos-cuota/PKG-2|PKG-2]] — accepted · El menu Modelos no congela: probe asincronico, cache con TTL y degradacion con nombre
- [[features/033-menos-espera-menos-cuota/PKG-3|PKG-3]] — accepted · Elegir modelo sin scrollear: agrupado por proveedor, contador, valor actual marcado, sin …
- [[features/033-menos-espera-menos-cuota/PKG-4|PKG-4]] — accepted · Windows sin mentiras: cerrar las 8 fallas residuales y el flaky de macOS, con techo de sk…
- [[features/033-menos-espera-menos-cuota/PKG-5|PKG-5]] — accepted · El gate se ve: progreso en vivo, falla temprana, resumen final y los 10 tests mas lentos
- [[features/033-menos-espera-menos-cuota/PKG-6|PKG-6]] — accepted · Cuotas que alcanzan: context pack obligatorio, gates sin modelo, panel por riesgo y presu…

## Approach y decisiones

- ruteo PKG-1: cursor-host native subagent; no route-decide
- ruteo PKG-2: cursor-host native subagent; no route-decide
- ruteo PKG-3: cursor-host native subagent; no route-decide
- ruteo PKG-4: cursor-host native subagent; no route-decide
- ruteo PKG-5: cursor-host native subagent; no route-decide
- ruteo PKG-6: cursor-host native subagent; no route-decide
- [2026-08-19] finding-verifier: finding-verifier Cursor inherit. Clean context. In doubt uphold. Same model as writer and reviewer.
- [2026-08-19] finding-verifier: Verification recorded: three upheld. Spawn counter at the scoped ceiling. Next repair plus delta would need two more spawns. Stopped before record-spawn would block the whole feat…
- [2026-08-19] repair-agent: repair-agent Cursor inherit. Three upheld findings. Ceiling 200 lines. No record-spawn: ninth would BLOCK. Bite with cp. Do not edit Global by hand; build.sh regenerates.
- [2026-08-19] orchestrator: PKG-6 accepted. VERIFY_PASS 1336. Repair 3900d4b+de8a476. Ceiling 199/200. Same-model inherit recorded on the panel. Next is integration before/after measurements.
- [2026-08-19] integrator: INTEGRATION. Six packages accepted. Remedir baseline. Do not push. AC-4.5 stays residual without three-job SHA. No --route-decide.
- [2026-08-19] integrator: INTEGRATION evidence d1a5441. VERIFY_PASS 1336/13m08s vs 1286/1237s. Section 2=144. First paint tests 0.031s. AC-4.5 residual: 12 local commits not pushed. Feature stays INTEGRATI…
- decisión: [[decisiones/2026-08-18 orden-paquetes-033-ci-gate-consola-lane|Orden de paquetes: CI y gate primero, consola despues, lane y cuota al final]]
- decisión: [[decisiones/2026-08-18 033-review-mismo-modelo-contexto-limpio|Independencia de review en Cursor: mismo modelo, contexto limpio, degradacion registrada]]
- decisión: [[decisiones/2026-08-18 033-pkg4-commit-antes-del-freeze|PKG-4 se commitea antes del freeze porque el candidato exige refs ya en git]]
- decisión: [[decisiones/2026-08-18 033-pkg5-verify-reporter-modulo-python|El presenter del gate vive en un modulo Python testeable, no en el shell]]
- decisión: [[decisiones/2026-08-18 033-pkg5-digest-no-ensucia-owned-paths|Digest no ensucia el diff de un paquete con bitacoras ajenas]]
- decisión: [[decisiones/2026-08-18 033-pkg2-autoprobe-despues-del-primer-frame|El vivo llega solo despues del primer frame; el test de labels se aisla]]
- decisión: [[decisiones/2026-08-19 033-pkg6-techo-scoped-deja-repair-fuera|033-pkg6-techo-scoped-deja-repair-fuera]]
- decisión: [[decisiones/2026-08-19 033-pkg6-dos-despachos-extra-autorizados|033-pkg6-dos-despachos-extra-autorizados]]
- decisión: [[decisiones/2026-08-19 033-push-main-para-ac-4-5|033-push-main-para-ac-4-5]]

## Convenciones

| Eje | Origen | Stance | Umbral | Siguiente | Revisit |
|---|---|---|---|---|---|
| data-store | n/a | no database: la configuracion vive en models.toml y el estado en archivos JSON del repo |  |  |  |
| api-gateway | n/a | sin superficie de red propia; los unicos procesos externos son los CLIs ya instalados (opencode, codex, claude) |  |  |  |
| deploy-platform | n/a | sin deploy: se instala en la maquina del desarrollador con ./build.sh --install |  |  |  |
| audience | request | Federico como unico desarrollador, con Cursor como runtime de implementacion de este spec |  |  |  |
| embeddings | n/a | sin embeddings ni busqueda vectorial; la busqueda del picker es substring casefold |  |  |  |
| realtime | request | sin tiempo real de red, pero SI hay latencia percibida: el criterio duro es primer frame en menos de 300 ms |  |  |  |
| mobile | n/a | sin superficie mobile: es una consola de terminal |  |  |  |
| auth | n/a | sin autenticacion propia; las credenciales de los proveedores las maneja cada CLI y el harness nunca las lee ni las loguea |  |  |  |
| cost | request | eje central de la feature: bajar despachos por paquete y contexto releido, con linea base medida de 246 despachos y 6.4G de tokens en 8 dias |  |  |  |
| legal | n/a | sin superficie legal: tooling interno de desarrollo, repo publico, sin datos de terceros |  |  |  |

## Qué falta

- → faltan correr los gates globales finales

## Presupuestos

- spawns: 35 (máx 8/paquete) · deep review máx 2 ciclos

[[00 - Proyecto|⌂ Proyecto]] · [[features/033-menos-espera-menos-cuota/grafo|grafo]] · bitácora: `/home/federico/SET-AGENTES/docs/specs/033-menos-espera-menos-cuota/bitacora.md`

_Actualizado: 2026-08-19T02:09:59+00:00_
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
