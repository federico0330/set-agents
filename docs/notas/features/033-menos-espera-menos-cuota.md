# 033-menos-espera-menos-cuota

<!-- notas:auto -->
## Estado

- fase: `PACKAGE_PLANNING` · modo: scoped · revisión 6
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
- [[features/033-menos-espera-menos-cuota/PKG-4|PKG-4]] — planned · Windows sin mentiras: cerrar las 8 fallas residuales y el flaky de macOS, con techo de sk…
- [[features/033-menos-espera-menos-cuota/PKG-5|PKG-5]] — planned · El gate se ve: progreso en vivo, falla temprana, resumen final y los 10 tests mas lentos
- [[features/033-menos-espera-menos-cuota/PKG-6|PKG-6]] — planned · Cuotas que alcanzan: context pack obligatorio, gates sin modelo, panel por riesgo y presu…

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

- → toca planificar el próximo paquete
- 5 tareas pendientes en PKG-6

## Presupuestos

- spawns: 0 (máx 8/paquete) · deep review máx 2 ciclos

[[00 - Proyecto|⌂ Proyecto]] · [[features/033-menos-espera-menos-cuota/grafo|grafo]] · bitácora: `/home/federico/SET-AGENTES/docs/specs/033-menos-espera-menos-cuota/bitacora.md`

_Actualizado: 2026-08-18T15:33:49+00:00_
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
