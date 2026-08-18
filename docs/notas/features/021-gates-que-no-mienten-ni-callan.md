# 021-gates-que-no-mienten-ni-callan

<!-- notas:auto -->
## Estado

- fase: `DONE` · modo: feature · revisión 80
- estado final: **DONE**
- spec: `docs/specs/021-gates-que-no-mienten-ni-callan/spec.md` (hash `e324d748afc0`)

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

## Paquetes

- [[features/021-gates-que-no-mienten-ni-callan/P1-check-que-verifica|P1-check-que-verifica]] — accepted · Que build.sh --check compare de verdad contra Global/ y que la suite deje de enmascarar e…
- [[features/021-gates-que-no-mienten-ni-callan/P2-gates-que-no-callan|P2-gates-que-no-callan]] — accepted · Que correr los gates no deje al que los corre mudo mas de 60s, y que la doctrina deje de …

## Approach y decisiones

- [2026-08-12] package-reviewer: package-reviewer sobre 021/P1: anthropic/sonnet, independence_verified=true frente al writer openai-codex/gpt-5.6-sol. Eje critico: el implementer TOCO setup_models.py, que el con…
- [2026-08-12] implementer: P2 de 021 (AC-06..09). Causa raiz CORREGIDA: no es buffering del escritor sino que tail -N sin -f no puede emitir hasta EOF; stdbuf NO lo arregla, verificado. AC-09 es prevencion …
- [2026-08-12] package-reviewer: package-reviewer sobre 021/P2: anthropic/sonnet, independence_verified=true frente al writer openai-codex/gpt-5.6-luna. Re-decidido con risk=medium tras un primer decide con risk=…
- [2026-08-12] package-reviewer: Review PARTIDO tras dos muertes por stall del encargo completo (decision registrada en slug sexto-stall-segunda-muerte-del-mismo-encargo, Federico eligio la opcion a). Parte A: AC…
- [2026-08-12] package-reviewer: Parte B: AC-07 (donde vive la doctrina y si propaga de verdad), AC-09 (el test y su mordida), residuos del antipatron, y la pregunta de si AC-07 promete mas de lo que entrega dado…
- [2026-08-12] -: 021 DONE. 2 paquetes, ADR-0041. build.sh --check pasa de no comparar nada a comparar los 4 arboles con perfil go-zen fijo; heartbeat-run.py mas la doctrina imperativa en spawn-pro…
- decisión: [[decisiones/2026-08-12 check-compara-con-perfil-canonico-fijo|build.sh --check compara siempre con --profile go-zen fijo, no con el perfil local]]
- decisión: [[decisiones/2026-08-12 la-evidencia-de-build-check-de-019-y-020-no-probaba-drift|Los gates de 019 y 020 que citaban 'build.sh --check -> CHECK_PASS' como prueba de sin-drift no probaban eso]]
- decisión: [[decisiones/2026-08-12 correccion-setup-models-si-habia-que-tocarlo|CORRECCION: la nota que decia que setup_models.py seguia funcionando sin tocarlo era falsa]]
- decisión: [[decisiones/2026-08-12 commitear-un-paquete-en-review-es-guardar-no-aceptar|Commitear un paquete que esta en PACKAGE_REVIEW: guardar no es aceptar]]
- decisión: [[decisiones/2026-08-12 segunda-vez-owned-paths-con-adr-adivinado|Segunda vez que escribo owned_paths con un nombre de ADR que todavia no existe]]
- decisión: [[decisiones/2026-08-12 p2-murio-por-limite-de-sesion-con-trabajo-parcial|El implementer de P2 murio por limite de sesion con AC-06, 08 y 09 hechos y AC-07 pendiente]]
- decisión: [[decisiones/2026-08-12 olvide-route-dispatched-en-el-relanzamiento|Cuarto desliz de bookkeeping del orquestador: omiti --route-dispatched en un relanzamiento]]
- decisión: [[decisiones/2026-08-12 quinto-stall-corrige-el-patron-y-la-mitigacion|Quinto stall: el patron no era 'agentes mutadores' y nombrar la herramienta no alcanza]]
- decisión: [[decisiones/2026-08-12 sexto-stall-segunda-muerte-del-mismo-encargo|HUMAN_DECISION_REQUIRED: sexto stall de la sesion y segunda muerte del review de P2]]

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

- spawns: 6 (máx 12/paquete) · deep review máx 2 ciclos

[[00 - Proyecto|⌂ Proyecto]] · [[features/021-gates-que-no-mienten-ni-callan/grafo|grafo]] · bitácora: `/home/federico/SET-AGENTES/docs/specs/021-gates-que-no-mienten-ni-callan/bitacora.md`

_Actualizado: 2026-08-12T21:09:05+00:00_
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
