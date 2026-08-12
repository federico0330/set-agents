# 021-gates-que-no-mienten-ni-callan

<!-- notas:auto -->
## Estado

- fase: `PACKAGE_REVIEW` · modo: feature · revisión 23
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

- [[features/021-gates-que-no-mienten-ni-callan/P1-check-que-verifica|P1-check-que-verifica]] — package_review · Que build.sh --check compare de verdad contra Global/ y que la suite deje de enmascarar e…
- [[features/021-gates-que-no-mienten-ni-callan/P2-gates-que-no-callan|P2-gates-que-no-callan]] — planned · Que correr los gates no deje al que los corre mudo mas de 60s, y que la doctrina deje de …

## Approach y decisiones

- [2026-08-12] implementer: P1 de 021 (AC-01..05): --check compara el STAGING contra los 4 arboles con --profile go-zen FIJO (decision de Federico: con perfil local rompe install.sh:370 y setup_models.py). R…
- [2026-08-12] package-reviewer: package-reviewer sobre 021/P1: anthropic/sonnet, independence_verified=true frente al writer openai-codex/gpt-5.6-sol. Eje critico: el implementer TOCO setup_models.py, que el con…
- decisión: [[decisiones/2026-08-12 check-compara-con-perfil-canonico-fijo|build.sh --check compara siempre con --profile go-zen fijo, no con el perfil local]]
- decisión: [[decisiones/2026-08-12 la-evidencia-de-build-check-de-019-y-020-no-probaba-drift|Los gates de 019 y 020 que citaban 'build.sh --check -> CHECK_PASS' como prueba de sin-drift no probaban eso]]
- decisión: [[decisiones/2026-08-12 correccion-setup-models-si-habia-que-tocarlo|CORRECCION: la nota que decia que setup_models.py seguia funcionando sin tocarlo era falsa]]

## Qué falta

- _nada pendiente_ ✅

## Presupuestos

- spawns: 2 (máx 12/paquete) · deep review máx 2 ciclos

[[00 - Proyecto|⌂ Proyecto]] · [[features/021-gates-que-no-mienten-ni-callan/grafo|grafo]] · bitácora: `/home/federico/SET-AGENTES/docs/specs/021-gates-que-no-mienten-ni-callan/bitacora.md`

_Actualizado: 2026-08-12T14:28:51+00:00_
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
