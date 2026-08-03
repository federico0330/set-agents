# ADR-0022 — Strict TDD as an opt-in per-package mode, additive to the default flow

- Estado: Accepted (2026-08-03). Tercera de cinco ADRs (0020-0024) del estudio de RDD de `gentle-ai`; ver
  ADR-0020 para el contexto compartido.

## Contexto

gentle-ai's disciplina de TDD estricto (RED→GREEN→TRIANGULATE→REFACTOR, safety-net obligatorio, patrones de
assertion prohibidos, auditoría independiente de la evidencia RED/GREEN) demostró mejores resultados en su
propio uso. El flujo por defecto de SET-AGENTES es explícitamente NO test-first (`test-writer.md`: "you write
regression tests AFTER the package behavior has converged"), una decisión ya tomada y confirmada por el
usuario en el pasado. El usuario, al ver lo que descubrió gentleman, pidió explícitamente adoptar el flujo
real de TDD estricto — no un stub, el contenido real (las Tres Leyes, el ciclo completo, la lista de
assertions prohibidas, el mock hygiene, la regla de implementation-detail-coupling) — como una vía disponible,
no como reemplazo del flujo por defecto.

## Decisión

1. Dos skills nuevos, portados con contenido real de `gentle-ai` (`internal/assets/skills/sdd-apply/
   strict-tdd.md` y `sdd-verify/strict-tdd-verify.md`), adaptados al contrato de salida de SET-AGENTES:
   `Global/_canonical/skills/strict-tdd/SKILL.md` (`enabled_for: implementer`) y
   `Global/_canonical/skills/strict-tdd-verify/SKILL.md` (`enabled_for: package-reviewer`).
2. Toggle por paquete: `package["strict_tdd"]` (booleano, default `false`), declarado por `package-planner`
   vía `create-package --strict-tdd true` (o modificado después con `update-package --strict-tdd`). Nunca un
   flag de feature completa — la ceremonia extra se paga por paquete, donde realmente se necesita.
3. Cuando `strict_tdd: true`: `implementer` carga `strict-tdd` y su ciclo RED→GREEN→TRIANGULATE→REFACTOR
   REEMPLAZA el paso 2 de su procedimiento por defecto (escribir tests como parte llana del entregable) SOLO
   para ese paquete — todo paquete sin el flag mantiene el flujo actual sin cambios. El resultado se reporta
   como un array `tdd_evidence` nuevo en el Output JSON ya existente de `implementer`, no como un artefacto
   separado (gentle-ai usa un archivo `apply-progress` propio; SET-AGENTES no tiene ese artefacto y no se
   crea uno solo para esto).
4. `package-reviewer` carga `strict-tdd-verify` cuando el paquete tiene el flag y audita la evidencia
   `tdd_evidence` independientemente: re-corre los tests GREEN citados, escanea los archivos de test tocados
   por los patrones de assertion prohibidos. Los hallazgos son findings estructurados comunes
   (`category: testing`, ya existente en el enum), consolidados en el mismo reporte — no un segundo rol de
   revisión ni un segundo pase.
5. `finding-verifier`/ADR-0009 quedan intocados: un finding sobre evidencia TDD débil fluye por la refutación
   adversarial existente como cualquier otro finding, sin caso especial.

## Rejected alternatives

- **TDD estricto obligatorio para todo paquete.** Rechazado: reabriría una decisión de producto ya tomada
  (`test-writer` post-convergencia) para TODO el proyecto en vez de sumarlo como vía disponible; el usuario
  pidió explícitamente que sea aditivo.
- **Un artefacto `apply-progress` separado, calcado de gentle-ai.** Rechazado: SET-AGENTES ya tiene un
  contrato de salida JSON para `implementer` y otro para `package-reviewer` — crear un tercer artefacto solo
  para TDD duplicaría infraestructura que ya existe y que estos roles ya leen/escriben.
- **Un segundo rol de revisión dedicado a auditar TDD.** Rechazado por el mismo principio que ADR-0021: la
  auditoría se pliega en `package-reviewer` (misma postura read-only que ya usa para todo lo demás), no se
  fragmenta en otro agente.

## Consecuencias

- El flujo por defecto (test-writer después de la convergencia) no cambia para ningún paquete que no declare
  el flag explícitamente — cero riesgo de regresión de comportamiento para trabajo existente.
- `strict_tdd` viaja por el mismo esquema de estado (`ai/state/features/<id>.json`) y el mismo patrón de
  default `.get()`-seguro que el resto de los campos RDD-inspirados (ADR-0020/0021).
- Un paquete que declara `strict_tdd: true` paga ceremonia real (ciclo completo, auditoría independiente) —
  la expectativa es que se use en superficies lógicamente densas o históricamente frágiles, no por defecto.
