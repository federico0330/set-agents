# 007-quota-visibility

<!-- notas:auto -->
## Estado

- fase: `DONE` · modo: feature · revisión 114
- estado final: **DONE**
- spec: `docs/specs/007-quota-visibility/spec.md` (hash `31d6e65add49`)

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

- [[features/007-quota-visibility/P1-schema-normalize|P1-schema-normalize]] — accepted · Que la comparacion de DDL compare estructura y no prosa, y que una base que genuinamente …
- [[features/007-quota-visibility/P2-spawn-accounting|P2-spawn-accounting]] — accepted · Persistir en el expediente el usage que el spawn ya recibe y hacer visible el gasto por c…
- [[features/007-quota-visibility/P3-correct-record|P3-correct-record]] — accepted · Retractar la afirmacion registrada de que el carril anthropic de Pi cobra por token como …

## Approach y decisiones

- [2026-07-29] package-reviewer: Panel RP-01, un solo miembro (complexity: small, sin superficie de codigo ni de seguridad). package-reviewer, read-only, chequea las dos correcciones contra las citas de spec.md (…
- [2026-07-29] finding-verifier: Read-only, sin panel nuevo -- es el paso finding-verifier entre PACKAGE_REVIEW y PACKAGE_REPAIR que exige record-verification para severidad > low. Los 8 hallazgos ya fueron repar…
- [2026-07-29] delta-reviewer: Sonnet, contexto limpio, read-only, alcance acotado a docs/notas/BUENOS-DIAS.md y ai/state/decisions-log.jsonl (las dos entradas de decision). F-01/F-02 high descartan --skip-delt…
- [2026-07-29] finding-verifier: finding-verifier, read-only. 3 hallazgos: N-01 medium (local_validations del task rendido en la nota del paquete), N-02/N-03 low (notas de decision sin marca de supersesion / con …
- [2026-07-29] delta-reviewer: Sonnet, contexto limpio, read-only. Alcance: docs/notas/features/007-quota-visibility/P3-correct-record.md y las dos notas de decision, seccion Notas propias unicamente. No re-rev…
- [2026-07-29] integrator: Integracion de 007-quota-visibility: confirma que P1 (normalizacion de schema) + P2 (contabilidad de spawns) + P3 (correccion de la nota) juntos satisfacen el contrato 1.3.0, incl…
- decisión: [[decisiones/2026-07-28 routing-ddl-validation-blind-to-triggers|La validacion de DDL del store de ruteo no ve triggers ni vistas]]
- decisión: [[decisiones/2026-07-28 start-review-panel-silent-noop|start-review-panel devuelve ok sin agregar roles cuando se le pasa un panel-id existente]]
- decisión: [[decisiones/2026-07-28 p0-architect-findings-outside-package-record|Los cinco hallazgos del architect sobre P0 no pudieron entrar al expediente del paquete]]
- decisión: [[decisiones/2026-07-28 p0-role-affinity-reverted|P0-role-affinity revertido: codificaba a mano la decision que el usuario quiere dinamica]]
- decisión: [[decisiones/2026-07-29 007-reconciliada-con-acta-antes-de-p1|El registro de la 007 se reconcilia con acta antes de abrir P1]]
- decisión: [[decisiones/2026-07-29 la-normalizacion-de-ddl-baja-a-minusculas-los-literales-de-los-check|El comparador de DDL acepta una base cuyos CHECK enumeran valores distintos, porque normaliza a minusculas tambien adentro de los literales]]
- decisión: [[decisiones/2026-07-29 un-hallazgo-refutado-puede-dejar-trabajo-y-el-ciclo-no-tiene-puerta-para-registrarlo|Cuando el unico hallazgo se refuta, el paquete salta a PACKAGE_TESTING y el trabajo que la refutacion revelo se queda sin canal]]
- decisión: [[decisiones/2026-07-29 la-deriva-de-hash-del-spec-se-acepta-en-vez-de-re-inicializar-la-007|El contrato se enmienda a 1.3.0 y la deriva de hash se acepta, porque re-inicializar tiraria el registro de P1 recien aceptado]]
- decisión: [[decisiones/2026-07-29 pi-usage-cache-keys-are-camelcase-not-snake-case|El usage real de Pi manda cacheRead/cacheWrite en camelCase, no cache_read/cache_write]]
- decisión: [[decisiones/2026-07-29 pi-lane-since-window-blind-to-discard-and-total|El carril pi de cost-report.py: --since filtra las filas contadas pero no los totales de diagnostico]]
- decisión: [[decisiones/2026-07-29 cost-report-pi-collector-crashes-on-pre-schema-6-routing-db|cost-report.py se cae entero si routing.db todavia no migro a schema 6]]
- decisión: [[decisiones/2026-07-29 buenos-dias-anthropic-surcharge-claim-was-wrong|BUENOS-DIAS.md retractaba mal el costo del carril Pi]]
- decisión: [[decisiones/2026-07-29 buenos-dias-anthropic-surcharge-claim-was-wrong-supersedes-first-pass|La primera correccion de BUENOS-DIAS.md tambien afirmaba sin verificar]]
- decisión: [[decisiones/2026-07-29 ac-19-rationale-drifted-mid-package-routing-db-recreated|AC-19 del contrato 007 quedo con una frase falsa por la propia QA en vivo de P2]]
- decisión: [[decisiones/2026-07-29 record-delta-review-new-finding-missing-source-role|record-delta-review no estampa source_role en --new-finding, a diferencia de record-subreview y record-late-review]]
- decisión: [[decisiones/2026-07-29 ac-19-spec-prose-amendment-deferred-past-integration|AC-19's stale spec.md rationale clause stays unedited past integration too]]

## Qué falta

- _nada pendiente_ ✅

## Presupuestos

- spawns: 13 (máx 12/paquete) · deep review máx 2 ciclos

[[00 - Proyecto|⌂ Proyecto]] · [[features/007-quota-visibility/grafo|grafo]] · bitácora: `/home/federico/SET-AGENTS/docs/specs/007-quota-visibility/bitacora.md`

_Actualizado: 2026-07-29T17:10:45+00:00_
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
