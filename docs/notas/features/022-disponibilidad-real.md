# 022-disponibilidad-real

<!-- notas:auto -->
## Estado

- fase: `DONE` · modo: feature · revisión 190
- estado final: **DONE**
- spec: `docs/specs/022-disponibilidad-real/spec.md` (hash `a72d851a3317`)

## Criterios de aceptación

- AC-01
- AC-02
- AC-03
- AC-04
- AC-05
- AC-06
- AC-07
- AC-08
- AC-09
- AC-10
- AC-11
- AC-12
- AC-13
- AC-14
- AC-15
- AC-16
- AC-17
- AC-18
- AC-19

## Paquetes

- [[features/022-disponibilidad-real/P1-registro-de-proveedores|P1-registro-de-proveedores]] — accepted · Un unico registro del que se derivan las seis tablas de proveedores que hoy estan en lock…
- [[features/022-disponibilidad-real/P2-techo-catalogo-tri-estado|P2-techo-catalogo-tri-estado]] — accepted · Que [catalog] deje de ser requisito de configuracion, sin abrir la puerta a que entre cua…
- [[features/022-disponibilidad-real/P3-liveness-real|P3-liveness-real]] — accepted · Que dar de baja una credencial se note en la decision siguiente, en los cuatro runtimes, …
- [[features/022-disponibilidad-real/P4-proveedores-del-usuario|P4-proveedores-del-usuario]] — accepted · Administrar proveedores propios desde set-agents, sin editar JSON, y que quitar funcione …
- [[features/022-disponibilidad-real/P5-altas-y-bajas-automaticas|P5-altas-y-bajas-automaticas]] — accepted · Que activar una suscripcion alcance para usarla, y que darla de baja se note, sin tocar n…

## Approach y decisiones

- [2026-08-13] repair-agent: P3-F03 critical: pi_auth_provider_keys acepta {'openai-codex': []} y hasta {'proveedor-inventado': {...}}, devolviendo keyset y firma no vacios. Ultimo ciclo de review disponible …
- [2026-08-13] delta-reviewer: Reparador claude-code/anthropic/opus (run1_ccfef5c2). Delta reviewer codex/openai-codex/gpt-5.6-terra, dec1_686d1590, independence_verified=true. Es el segundo y ultimo ciclo de r…
- [2026-08-13] implementer: P4 de 022 (AC-11..15). Medicion clave del pack: el bloque ollama del opencode.json del usuario es BYTE-IDENTICO al que envia Global/_shared/opencode.json:5-23, o sea no lo agrego …
- [2026-08-13] package-reviewer: Writer claude-code/anthropic/opus (run1_f193bfbd). Reviewer codex/openai-codex/gpt-5.6-terra, independence_verified=true. Se le pide dictaminar tambien el desvio de alcance a prov…
- [2026-08-13] implementer: P5 de 022 (AC-16..19), ultimo paquete. Evidencia en vivo: github copilot figura authenticated=true detected_unlistable=true models_listable=0; openai-codex lista 6 modelos y su in…
- [2026-08-13] package-reviewer: Writer claude-code/anthropic/opus (run1_12758dae; murio por error de API tras escribir codigo y tests, los gates los corrio el orquestador: 1065 OK, VERIFY_PASS). Reviewer codex/o…
- decisión: [[decisiones/2026-08-13 ruteo-nombra-el-runtime-que-realmente-ejecuta|El descriptor de ruteo nombra el runtime que realmente ejecuta]]
- decisión: [[decisiones/2026-08-13 el-probe-dice-vivo-y-la-inferencia-dice-token-vencido|Medicion en vivo: listar modelos funciona y la inferencia falla con token vencido]]
- decisión: [[decisiones/2026-08-13 check-owned-paths-no-ve-archivos-nuevos|El control de alcance no ve los archivos nuevos: usa git diff, que solo lista trackeados]]
- decisión: [[decisiones/2026-08-13 captura-ab-del-refresh-se-observa-no-se-fuerza|La captura A/B del refresh se observa pasivamente en vez de forzarse]]
- decisión: [[decisiones/2026-08-13 el-gate-de-pi-corre-despues-del-subproceso-preexistente|El gate de credenciales de pi corre despues del subproceso, y es preexistente]]
- decisión: [[decisiones/2026-08-13 captura-ab-cerrada-el-refresh-natural-confirmo-el-diseno|Captura A/B cerrada: el refresh natural confirmo el diseno de la firma]]
- decisión: [[decisiones/2026-08-13 desvio-de-alcance-de-p4-aprobado-con-medicion|El desvio de alcance de P4 a provider_registry.py queda aprobado, medido]]
- decisión: [[decisiones/2026-08-13 copilot-aparecio-solo-durante-la-noche|Copilot paso de no listable a 26 modelos durante la noche, y el harness lo adopto solo]]
- decisión: [[decisiones/2026-08-13 el-coordinador-deja-de-ser-gpt-en-la-lane-opencode|El coordinador deja de ser GPT en la lane de opencode]]
- decisión: [[decisiones/2026-08-13 los-modulos-de-test-no-pasan-aislados-preexistente|Los modulos de test no pasan aislados, y es preexistente]]

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

- spawns: 16 (máx 12/paquete) · deep review máx 2 ciclos

[[00 - Proyecto|⌂ Proyecto]] · [[features/022-disponibilidad-real/grafo|grafo]] · bitácora: `/home/federico/SET-AGENTES/docs/specs/022-disponibilidad-real/bitacora.md`

_Actualizado: 2026-08-13T13:40:43+00:00_
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
