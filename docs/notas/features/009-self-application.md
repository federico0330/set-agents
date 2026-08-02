# 009-self-application

<!-- notas:auto -->
## Estado

- fase: `DONE` · modo: feature · revisión 110
- estado final: **DONE**
- spec: `docs/specs/009-self-application/spec.md` (hash `ec14f43bbd17`)

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

## Paquetes

- [[features/009-self-application/P1-knowledge-home|P1-knowledge-home]] — accepted · Que la capa de conocimiento exista en el arnes en los dos niveles que los prompts nombran…
- [[features/009-self-application/P2-state-machine-required|P2-state-machine-required]] — accepted · Que entregar una feature por fuera de la maquina de estados sea un error y no silencio, e…
- [[features/009-self-application/P3-panel-integrity|P3-panel-integrity]] — accepted · Cerrar los tres agujeros del ciclo de review que aparecieron al usarlo (panel sin miembro…

## Approach y decisiones

- [2026-07-28] package-reviewer: Panel RP-01, miembro 1 de 2, declarado en la llamada de apertura con --role (que ahora es obligatorio, gracias a este mismo paquete). Sonnet 5, contexto limpio, read-only. Foco: e…
- [2026-07-28] architect: Panel RP-01, miembro 2 de 2, concurrente con el package-reviewer. Sonnet 5, contexto limpio, read-only. Es el mismo rol cuyos cinco hallazgos, en 007-P0, no tuvieron canal -- que …
- [2026-07-28] finding-verifier: Fable 5, cuarto modelo distinto de la cadena tras un escritor en Opus 5 y dos revisores en Sonnet 5. Read-only. Los cuatro hallazgos en un solo lote. Ojo con F-01 y F-02: el patro…
- [2026-07-28] delta-reviewer: Sonnet 5, contexto limpio, read-only, alcance limitado a los cuatro archivos del lote. Foco: si replayed() unifico bien las dos definiciones que antes podian discrepar, si blackli…
- [2026-07-28] -: P3 aceptado. 238 tests (base 217, +21), ninguno skipeado, VERIFY_PASS, SELF_SCAFFOLD_SYNC_OK files=2, OWNERSHIP_PASS sobre 130 archivos. Cinco hallazgos: cuatro sostenidos y repar…
- [2026-07-29] integrator: Integracion de 009-self-application: verify.sh y build.sh --check ya corrieron en verde (284 tests, SELF_SCAFFOLD_SYNC_OK) a nivel orquestador; el integrador confirma que P1+P2+P3…
- decisión: [[decisiones/2026-07-28 estado-no-sabe-amendar-un-contrato-revisado|La maquina de estados no sabe amendar un contrato revisado ni retirar un paquete superado]]
- decisión: [[decisiones/2026-07-28 skip-delta-deja-la-aceptacion-inalcanzable|record-repair --skip-delta despues de un delta review repair_required deja el paquete imposible de aceptar]]
- decisión: [[decisiones/2026-07-28 re-init-de-009-tras-el-desafio-del-contrato-con-la-historia-descartada-preservada|Re-init de 009 tras el desafio del contrato, con la historia descartada preservada]]
- decisión: [[decisiones/2026-07-28 el-chequeo-de-ownership-es-ciego-a-los-archivos-sin-trackear|El chequeo de ownership es ciego a los archivos sin trackear]]
- decisión: [[decisiones/2026-07-28 el-nivel-cross-proyecto-del-conocimiento-se-muda-al-path-que-los-prompts-nombran|El nivel cross-proyecto del conocimiento se muda al path que los prompts nombran]]
- decisión: [[decisiones/2026-07-28 el-gate-de-estado-obligatorio-vive-en-verify-sh|El gate que exige archivo de estado vive en verify.sh, no en un hook de git]]
- decisión: [[decisiones/2026-07-28 cuatro-archivos-de-estado-afirman-un-spec-que-ya-no-existe|La deriva de hash ya existente se registra como deuda, no se convierte en un gate]]
- decisión: [[decisiones/2026-07-28 las-cuatro-fases-previas-a-la-aprobacion-siguen-sin-transiciones|PHASES conserva cuatro fases que LEGAL_TRANSITIONS no conoce, y AC-13 no las convierte en transiciones reales]]
- decisión: [[decisiones/2026-07-28 el-canal-tardio-se-niega-contra-un-paquete-aceptado|Un hallazgo que llega despues de aceptado el paquete se rechaza en vez de registrarse]]
- decisión: [[decisiones/2026-07-28 una-feature-bloqueada-y-reabierta-no-puede-llegar-nunca-a-done|done_ready mira si la lista de blockers esta vacia, no si algun blocker sigue abierto]]
- decisión: [[decisiones/2026-07-28 las-cinco-deudas-del-ciclo-de-review-que-p3-nombro-y-no-reparo|Lo que quedo abierto en el ciclo de review despues de panel-integrity]]

## Qué falta

- _nada pendiente_ ✅

## Presupuestos

- spawns: 13 (máx 12/paquete) · deep review máx 2 ciclos

[[00 - Proyecto|⌂ Proyecto]] · [[features/009-self-application/grafo|grafo]] · bitácora: `/home/federico/SET-AGENTS/docs/specs/009-self-application/bitacora.md`

_Actualizado: 2026-07-29T17:10:45+00:00_
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
