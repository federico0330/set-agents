# 035-panel-honesto-consola-y-tips

<!-- notas:auto -->
## Estado

- fase: `DONE` · modo: scoped · revisión 133
- estado final: **DONE**
- spec: `docs/specs/035-panel-honesto-consola-y-tips/spec.md` (hash `296e051fccfd`)

## Criterios de aceptación

- AC-A.1
- AC-A.2
- AC-A.3
- AC-A.4
- AC-A.5
- AC-A.6
- AC-A.7
- AC-A.8
- AC-A.9
- AC-B.1
- AC-B.2
- AC-B.3
- AC-B.4
- AC-B.5
- AC-B.6
- AC-B.7
- AC-B.8
- AC-C.1
- AC-C.2
- AC-C.3
- AC-C.4
- AC-C.5
- AC-C.6

## Paquetes

- [[features/035-panel-honesto-consola-y-tips/PKG-A|PKG-A]] — accepted · Panel honesto: record-review deja de cerrar un paquete de panel FULL y de pasar por encim…
- [[features/035-panel-honesto-consola-y-tips/PKG-B|PKG-B]] — accepted · Segunda pasada de extraccion de set_agents_app.py con caracterizacion previa de tres cana…
- [[features/035-panel-honesto-consola-y-tips/PKG-C|PKG-C]] — accepted · TIPS-USO.md deja de afirmar un control plane unico y de omitir arboles que el repo genera…

## Approach y decisiones

- ruteo PKG-A: Cursor host pin 034/ADR-0063: implementer=composer-2.5; sin --route-decide en el anfitrion
- ruteo PKG-B: Cursor host pin 034/ADR-0063: implementer=composer-2.5; sin --route-decide en el anfitrion
- ruteo PKG-C: Cursor host pin 034/ADR-0063: implementer=composer-2.5; sin --route-decide en el anfitrion
- [2026-08-21] integrator: INTEGRATION bundle completion. JUDGE-035-004. Dump reviews/panels/verifications/deltas from state JSON. Do not invent verdicts. No verify.sh. No routing decide.
- [2026-08-21] adversarial-judge: Third adversarial-judge gpt-5.6-sol clean context. 003 answered by design.md:518-521 path-b same binary. 004 answered by evidence/REVIEWS.md from state JSON. No verify.sh. No rout…
- [2026-08-21] integrator: Spawn 10/10 PKG-C JSON ceiling. JUDGE-035-005 INTEGRATION.md:130. JUDGE-035-006 ADR-0066:131-136 wc 4340 after F005 shadow delete. No fourth judge this spawn. No routing decide.
- [2026-08-21] orchestrator: INTEGRATION VERIFY_PASS 1372. Three judges then composition fixes. PKG-C 10/10 JSON. Fourth judge needs max_spawns_per_package 10 to 11. MODE_BUDGETS untouched. No CLI reopen.
- [2026-08-21] adversarial-judge: Spawn 11/11 PKG-C after federico-authorized JSON 10->11. adversarial-judge gpt-5.6-sol. MODE_BUDGETS untouched. No CLI reopen. No verify.sh. No routing decide.
- [2026-08-21] orchestrator: DONE. JUDGE_PASS 38b6bbf8. VERIFY_PASS 1372. JSON ceiling 11 federico-authorized. MODE_BUDGETS.scoped still 8. memory-scribe next on PKG-A slot 11. No Engram.
- decisión: [[decisiones/2026-08-20 035-pkg-a-owned-path-exceptions|Excepciones PKG-A: suciedad de spec/consult/notas]]
- decisión: [[decisiones/2026-08-20 035-pkg-a-module-docs-eighth-site|T-006 octavo sitio: test_module_docs _init_ready_package]]
- decisión: [[decisiones/2026-08-20 035-pkg-a-freeze-uncommitted|Freeze PKG-A committed-only; panel lee working tree]]
- decisión: [[decisiones/2026-08-20 035-pkg-a-authorized-two-extra-spawns|Federico autoriza 2 spawns extra en JSON, no MODE_BUDGETS ni CLI reopen]]
- decisión: [[decisiones/2026-08-20 035-pkg-a-repair-ceiling-uncommitted-freeze|Repair ceiling: freeze 0 lines no congela techo 0]]
- decisión: [[decisiones/2026-08-20 035-pkg-a-revert-spawn-ceiling|Techo JSON vuelve a 8 al cerrar PKG-A]]
- decisión: [[decisiones/2026-08-20 035-pkg-b-owned-exceptions-uncommitted-a|Excepciones PKG-B por PKG-A sin commitear]]
- decisión: [[decisiones/2026-08-20 035-pkg-a-ceiling-cannot-revert|No se puede bajar el JSON a 8: PKG-A ya gasto 10]]
- decisión: [[decisiones/2026-08-20 035-pkg-b-owned-bitacoras-digest|Excepciones: bitacoras ajenas y estado.md regenerados]]
- decisión: [[decisiones/2026-08-21 035-pkg-b-authorized-two-extra-spawns|Federico autoriza repair+delta de PKG-B]]
- decisión: [[decisiones/2026-08-21 035-pkg-b-repair-ceiling-uncommitted-freeze|Sin techo de repair: freeze committed vs HEAD es 0 lineas]]
- decisión: [[decisiones/2026-08-21 035-pkg-c-owned-exceptions-uncommitted-ab|Excepciones PKG-C por A y B sin commitear]]
- decisión: [[decisiones/2026-08-21 035-judge-fail-composition|Juez bloquea: §11 miente y falta --provider-remove]]
- decisión: [[decisiones/2026-08-21 035-judge-003-path-b-same-binary|JUDGE-035-003 contradice el camino (b) aprobado]]
- decisión: [[decisiones/2026-08-21 035-pkg-c-authorized-fourth-judge-spawn|Federico autoriza spawn 11 para el cuarto juez]]

## Convenciones

| Eje | Origen | Stance | Umbral | Siguiente | Revisit |
|---|---|---|---|---|---|
| data-store | n/a | no new persistence; mutates local feature-state JSON and Python modules only |  |  |  |
| api-gateway | n/a | no external HTTP API or gateway; local CLI verbs only |  |  |  |
| deploy-platform | n/a | no deploy change; ships in this git repo via existing build.sh install |  |  |  |
| audience | n/a | harness operators (Federico) and the orchestrator reading TIPS-USO |  |  |  |
| embeddings | n/a | no embeddings or vector search in this slice |  |  |  |
| realtime | n/a | no realtime channel; file-first state machine unchanged |  |  |  |
| mobile | n/a | no mobile surface |  |  |  |
| auth | n/a | no auth/PII/tenant change; PKG-A forces security-auditor membership on the review verb |  |  |  |
| cost | n/a | MODE_BUDGETS scoped stays 8; extra security-auditor spawn paid from existing ceiling |  |  |  |
| legal | n/a | no ToS/PII processing change |  |  |  |

## Qué falta

- _nada pendiente_ ✅

## Presupuestos

- spawns: 31 (máx 11/paquete) · deep review máx 2 ciclos

[[00 - Proyecto|⌂ Proyecto]] · [[features/035-panel-honesto-consola-y-tips/grafo|grafo]] · bitácora: `/home/federico/SET-AGENTES/docs/specs/035-panel-honesto-consola-y-tips/bitacora.md`

_Actualizado: 2026-08-21T13:48:41+00:00_
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
