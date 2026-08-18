# 028-narracion-que-ensena

<!-- notas:auto -->
## Estado

- fase: `DONE` · modo: scoped · revisión 70
- estado final: **DONE**
- spec: `docs/specs/028-narracion-que-ensena/spec.md` (hash `d2826ba869ec`)

## Paquetes

- [[features/028-narracion-que-ensena/N1-campos-que-obligan|N1-campos-que-obligan]] — accepted · Agregar campos y guardas de narración exigible en log-narrative
- [[features/028-narracion-que-ensena/N2-doctrina-que-explica|N2-doctrina-que-explica]] — accepted · Actualizar doctrina para cierres que expliquen por qué y alternativa
- [[features/028-narracion-que-ensena/N3b-los-campos-donde-se-leen|N3b-los-campos-donde-se-leen]] — accepted · Mostrar campos learned/next/why/alternative en bitácora y digest

## Approach y decisiones

- [2026-08-17] package-reviewer: package-reviewer read-only sobre f688531, contexto limpio, modelo distinto al escritor (Cursor/Copilot). Cubre N1/N2/N3b contra AC-01..AC-20. Independencia por ADR-0011: proveedor…
- [2026-08-18] package-reviewer: mismo revisor que N1, misma sesión; todos los hallazgos de 028 bajo docs/specs/028-narracion-que-ensena/evidence/N-package-review.md
- [2026-08-18] package-reviewer: misma sesión de revisión independiente; N3b hallazgo N3b-F01 sobre el límite de render vs escritura
- decisión: [[decisiones/2026-08-17 replanteo-028-paquetes-sin-work-items|Los tres paquetes de 028 se replantean porque fueron creados sin work items]]
- decisión: [[decisiones/2026-08-17 replanteo-028-imposible-el-motor-no-tiene-salida|Correccion: los paquetes de 028 tampoco se pueden replantear -- el motor no tiene salida]]
- decisión: [[decisiones/2026-08-18 028-deuda-test-narracion-digest|tests/test_narracion_digest.py nunca se creó]]
- decisión: [[decisiones/2026-08-18 028-deuda-ac16-codex-drift|AC-16 AGENTS.codex.md: confirmación de deriva no registrada]]

## Convenciones

| Eje | Origen | Stance | Umbral | Siguiente | Revisit |
|---|---|---|---|---|---|
| data-store | - | - | - | - | - |
| api-gateway | - | - | - | - | - |
| deploy-platform | - | - | - | - | - |
| audience | - | - | - | - | - |
| embeddings | - | - | - | - | - |
| realtime | - | - | - | - | - |
| mobile | - | - | - | - | - |
| auth | - | - | - | - | - |
| cost | - | - | - | - | - |
| legal | - | - | - | - | - |

## Qué falta

- _nada pendiente_ ✅

## Presupuestos

- spawns: 3 (máx 8/paquete) · deep review máx 2 ciclos

[[00 - Proyecto|⌂ Proyecto]] · [[features/028-narracion-que-ensena/grafo|grafo]] · bitácora: `/home/federico/SET-AGENTES/docs/specs/028-narracion-que-ensena/bitacora.md`

_Actualizado: 2026-08-18T01:09:20+00:00_
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
