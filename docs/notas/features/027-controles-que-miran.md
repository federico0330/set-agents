# 027-controles-que-miran

<!-- notas:auto -->
## Estado

- fase: `DONE` · modo: scoped · revisión 158
- estado final: **DONE**
- spec: `docs/specs/027-controles-que-miran/spec.md` (hash `d049b9533555`)

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

- [[features/027-controles-que-miran/P1-alcance-y-aislamiento|P1-alcance-y-aislamiento]] — accepted · Que el control de alcance vea los archivos nuevos y que los modulos de test pasen aislados
- [[features/027-controles-que-miran/P2-nada-escribe-afuera|P2-nada-escribe-afuera]] — accepted · Que ningun test pueda escribir fuera de un directorio temporal
- [[features/027-controles-que-miran/P3-gates-que-preguntan-antes|P3-gates-que-preguntan-antes]] — accepted · Que el gate de pi corra antes del subproceso y que _decide_status filtre los codigos de m…
- [[features/027-controles-que-miran/P4-owned-paths-matchea-directorios|P4-owned-paths-matchea-directorios]] — accepted · Que owned_paths interprete directorios como directorios, sin falsos positivos ni relajaci…

## Approach y decisiones

- [2026-08-15] implementer: Implementer concurrente. AC-06 mueve el gate de pi antes del _run_cached preservando el parse fail-closed; AC-07 extiende el filtro de marcadores informativos de _decide_status.
- [2026-08-15] package-reviewer: Independencia degradada segun ADR-0011: mismo proveedor, modelo distinto, contexto limpio. Declarado en la evidencia del review.
- [2026-08-15] repair-agent: Pase consolidado sobre P3-F01 a P3-F05. F06 y F07 quedan fuera de alcance y se registran como decision.
- [2026-08-15] implementer: Implementer concurrente. matches() suma una regla de descendencia junto al fnmatch existente, en las dos copias del script.
- [2026-08-15] package-reviewer: Independencia degradada ADR-0011: mismo proveedor, modelo distinto, contexto limpio. El reviewer corrio mutantes y un barrido de las 27 features reales.
- [2026-08-15] repair-agent: Pase consolidado P4-F01 a F04 y F06. F05 y F07 los resuelve el orquestador.
- decisión: [[decisiones/2026-08-15 guarda-de-tests-portable-antes-que-hermetica|La guarda de escritura de tests degrada en vez de exigir bubblewrap]]
- decisión: [[decisiones/2026-08-15 matching-modules-queda-ciego-a-los-directorios-pelados|Defecto latente: matching_modules no entiende la semantica nueva de owned_paths]]
- decisión: [[decisiones/2026-08-15 marcadores-informativos-sin-un-solo-lugar-que-los-nombre|MODEL_PIN_UNAVAILABLE y MODEL_METADATA_INFERRED siguen sin filtrar, y el patron es el defecto]]
- decisión: [[decisiones/2026-08-15 la-suite-no-puede-dar-verde-en-un-clon-fresco|Defecto latente: cuatro tests leen ai/state/project.json, que esta gitignoreado]]
- decisión: [[decisiones/2026-08-15 un-freeze-que-no-midio-nada-se-vuelve-techo-cero|Defecto: freeze-candidate compara HEAD contra HEAD y el techo de reparacion queda en cero para siempre]]
- decisión: [[decisiones/2026-08-15 la-guarda-de-escritura-es-ciega-al-bytecode-de-los-hijos|P2-F11: run_gate filtra el entorno y el hijo escribe bytecode en el repo real, sin bwrap]]
- decisión: [[decisiones/2026-08-15 cuatro-huecos-de-la-guarda-de-escritura-para-una-feature-de-seguimiento|P2-F12 a P2-F15: la guarda cierra los casos nombrados, no las clases]]

## Qué falta

- _nada pendiente_ ✅

## Presupuestos

- spawns: 11 (máx 8/paquete) · deep review máx 2 ciclos

[[00 - Proyecto|⌂ Proyecto]] · [[features/027-controles-que-miran/grafo|grafo]] · bitácora: `/home/federico/SET-AGENTES/docs/specs/027-controles-que-miran/bitacora.md`

_Actualizado: 2026-08-15T03:40:23+00:00_
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
