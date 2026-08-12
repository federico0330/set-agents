# 020-honest-dashboard

<!-- notas:auto -->
## Estado

- fase: `DONE` · modo: feature · revisión 82
- estado final: **DONE**
- spec: `docs/specs/020-honest-dashboard/spec.md` (hash `432dd66a7d50`)

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

## Paquetes

- [[features/020-honest-dashboard/P1-digest-no-esconde|P1-digest-no-esconde]] — accepted · Que el digest, el hub de notas y --status no escondan lo que necesita una decision humana…
- [[features/020-honest-dashboard/P2-anclas-verificables|P2-anclas-verificables]] — accepted · Que una referencia file:line en docs/modules/ que ya no apunta a lo que dice sea un fallo…

## Approach y decisiones

- [2026-08-12] implementer: P1 de 020 (AC-01..05, AC-12): un predicado compartido de feature viva reemplaza las dos copias mal escritas (cli_reporting.py:194 y _hub_body), seccion Necesita tu decision con di…
- [2026-08-12] package-reviewer: package-reviewer sobre 020/P1: anthropic/sonnet, independence_verified=true frente al writer openai-codex/gpt-5.6-sol. Eje especial: el implementer MODIFICO un fixture de test pre…
- [2026-08-12] implementer: P2 de 020 (AC-06..11): gramatica de dos formas de ancla con resolucion por basename acotada a los paths del modulo, comando check-anchors read-only con rc distinto de cero, verifi…
- [2026-08-12] implementer: Relanzamiento unico de P2. Mitigacion: escribir evidencia en el primer minuto y guardar a disco por tramo. Si vuelve a morir, se parte en dos encargos mas chicos en vez de un terc…
- [2026-08-12] -: 020 DONE. 2 paquetes, ADR-0040, suite 943 -> 970. P1: predicado compartido de feature viva; el digest, el hub y cmd_status dejaron de esconder lo bloqueado. P2: check_anchors.py y…
- decisión: [[decisiones/2026-08-12 owned-paths-desactualizado-por-cambio-de-diseno|owned_paths escrito contra un diseno que el ADR despues cambio: error del orquestador, no del implementer]]
- decisión: [[decisiones/2026-08-12 cuarto-stall-de-la-sesion-patron-de-infraestructura|Cuarto stall de infraestructura de la sesion: el patron es de agentes mutadores de corrida larga, no de un encargo puntual]]

## Qué falta

- 1 hallazgos abiertos

## Presupuestos

- spawns: 4 (máx 12/paquete) · deep review máx 2 ciclos

[[00 - Proyecto|⌂ Proyecto]] · [[features/020-honest-dashboard/grafo|grafo]] · bitácora: `/home/federico/SET-AGENTES/docs/specs/020-honest-dashboard/bitacora.md`

_Actualizado: 2026-08-12T11:19:21+00:00_
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
