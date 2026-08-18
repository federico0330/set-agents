# 031-registro-correctivo

<!-- notas:auto -->
## Estado

- fase: `DONE` · modo: scoped · revisión 26
- estado final: **DONE**
- spec: `docs/specs/031-registro-correctivo/spec.md` (hash `08dae37bf0c1`)

## Paquetes

- [[features/031-registro-correctivo/P1-verbos-correctivos|P1-verbos-correctivos]] — accepted · Implementar reopen --from-done y amend-package en feature-state.py

## Approach y decisiones

- ruteo P1-verbos-correctivos: cambio quirúrgico en un solo módulo Python
- [2026-08-18] package-reviewer: review interno: 6 tests cubren AC-01..AC-03 y AC-07..AC-10 en ambas direcciones; suite 1266 tests OK; VERIFY_PASS

## Convenciones

| Eje | Origen | Stance | Umbral | Siguiente | Revisit |
|---|---|---|---|---|---|
| data-store | n/a | no external data store; mutates only local JSON state files under ai/state/ | - | - | - |
| api-gateway | n/a | no external API calls; operates only on the local filesystem | - | - | - |
| deploy-platform | n/a | no deployment artifact; pure Python script shipped with the repo | - | - | - |
| audience | notas | harness operators (Federico and future maintainers running feature-state.py CLI) | - | - | - |
| embeddings | n/a | no embeddings; pure text and JSON manipulation | - | - | - |
| realtime | n/a | no realtime requirements; CLI invoked on demand | - | - | - |
| mobile | n/a | no mobile surface; terminal tool | - | - | - |
| auth | n/a | no auth system; authorized-by field is an assertion, not a credential check | - | - | - |
| cost | n/a | no API cost; runs locally | - | - | - |
| legal | n/a | harness internal tooling; no external data, no compliance surface | - | - | - |

## Qué falta

- _nada pendiente_ ✅

## Presupuestos

- spawns: 1 (máx 8/paquete) · deep review máx 2 ciclos

[[00 - Proyecto|⌂ Proyecto]] · [[features/031-registro-correctivo/grafo|grafo]] · bitácora: `/home/federico/SET-AGENTES/docs/specs/031-registro-correctivo/bitacora.md`

_Actualizado: 2026-08-18T01:03:08+00:00_
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
