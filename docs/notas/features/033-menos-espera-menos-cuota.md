# 033-menos-espera-menos-cuota

<!-- notas:auto -->
## Estado

- fase: `PACKAGE_GATES` · modo: scoped · revisión 73
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

- [[features/033-menos-espera-menos-cuota/PKG-1|PKG-1]] — planned · Una sola dimension opencode: colapsar go-zen/zen/openai-only en un solo valor por area
- [[features/033-menos-espera-menos-cuota/PKG-2|PKG-2]] — planned · El menu Modelos no congela: probe asincronico, cache con TTL y degradacion con nombre
- [[features/033-menos-espera-menos-cuota/PKG-3|PKG-3]] — planned · Elegir modelo sin scrollear: agrupado por proveedor, contador, valor actual marcado, sin …
- [[features/033-menos-espera-menos-cuota/PKG-4|PKG-4]] — accepted · Windows sin mentiras: cerrar las 8 fallas residuales y el flaky de macOS, con techo de sk…
- [[features/033-menos-espera-menos-cuota/PKG-5|PKG-5]] — package_gates · El gate se ve: progreso en vivo, falla temprana, resumen final y los 10 tests mas lentos
- [[features/033-menos-espera-menos-cuota/PKG-6|PKG-6]] — planned · Cuotas que alcanzan: context pack obligatorio, gates sin modelo, panel por riesgo y presu…

## Approach y decisiones

- ruteo PKG-1: cursor-host native subagent; no route-decide
- ruteo PKG-2: cursor-host native subagent; no route-decide
- ruteo PKG-3: cursor-host native subagent; no route-decide
- ruteo PKG-4: cursor-host native subagent; no route-decide
- ruteo PKG-5: cursor-host native subagent; no route-decide
- ruteo PKG-6: cursor-host native subagent; no route-decide
- [2026-08-18] package-reviewer: Panel RP-01 pass. package-reviewer: AC-4.1 a 4.4 cubiertos en 1f5a24f, techo 660=654+6, probe intacto. security-auditor: SECURITY_PASS, relative_to no emite puntos-puntos, run() s…
- [2026-08-18] orchestrator: PKG-4 accepted. Candidato 1f5a24f. Gates VERIFY_PASS 1290/1393s. Panel RP-01 pass. AC-4.5 residual: SHA de verify-linux, verify-macos y windows-bootstrap en la misma corrida, pend…
- [2026-08-18] implementer: implementer nativo Cursor, inherit, sin route-decide. Context pack PKG-5.md. Archivos: verify.sh, ai/scripts/verify_reporter.py, tests/test_verify_reporter.py. No paralelizar.
- [2026-08-18] gate-runner: gate-runner nativo Cursor, readonly, inherit, sin route-decide. heartbeat-run verify.sh ~20 min. No repara.
- [2026-08-18] implementer: implementer Cursor inherit. Causa: sys.path[0]=ai/scripts al invocar el archivo; chdir ROOT no alcanza. Bite: rojo contra el crash, luego verde.
- [2026-08-18] gate-runner: gate-runner Cursor inherit readonly. heartbeat-run verify.sh. No repara. Gate failures 1/3 ya gastado.
- decisión: [[decisiones/2026-08-18 orden-paquetes-033-ci-gate-consola-lane|Orden de paquetes: CI y gate primero, consola despues, lane y cuota al final]]
- decisión: [[decisiones/2026-08-18 033-review-mismo-modelo-contexto-limpio|Independencia de review en Cursor: mismo modelo, contexto limpio, degradacion registrada]]
- decisión: [[decisiones/2026-08-18 033-pkg4-commit-antes-del-freeze|PKG-4 se commitea antes del freeze porque el candidato exige refs ya en git]]
- decisión: [[decisiones/2026-08-18 033-pkg5-verify-reporter-modulo-python|El presenter del gate vive en un modulo Python testeable, no en el shell]]
- decisión: [[decisiones/2026-08-18 033-pkg5-digest-no-ensucia-owned-paths|Digest no ensucia el diff de un paquete con bitacoras ajenas]]

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

- → falta registrar la referencia del diff integrado; el paquete todavía no está integrado localmente

## Presupuestos

- spawns: 9 (máx 8/paquete) · deep review máx 2 ciclos

[[00 - Proyecto|⌂ Proyecto]] · [[features/033-menos-espera-menos-cuota/grafo|grafo]] · bitácora: `/home/federico/SET-AGENTES/docs/specs/033-menos-espera-menos-cuota/bitacora.md`

_Actualizado: 2026-08-18T18:45:51+00:00_
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
