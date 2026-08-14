# 024-listo-para-terceros

<!-- notas:auto -->
## Estado

- fase: `PACKAGE_REVIEW` · modo: scoped · revisión 93
- spec: `docs/specs/024-listo-para-terceros/spec.md` (hash `f848f29b2069`)

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

- [[features/024-listo-para-terceros/C1-estado-fuera-del-producto|C1-estado-fuera-del-producto]] — accepted · Que el estado de Federico deje de viajar en el clon, sin mover el path
- [[features/024-listo-para-terceros/C2-modelstoml-neutro|C2-modelstoml-neutro]] — accepted · models.toml deja de fijar las suscripciones de una persona y el usuario tiene overlay pro…
- [[features/024-listo-para-terceros/C3-primer-arranque-honesto|C3-primer-arranque-honesto]] — package_review · Que el primer arranque de un tercero diga que hacer en vez de morir mudo
- [[features/024-listo-para-terceros/C4-higiene-de-repo-publico|C4-higiene-de-repo-publico]] — planned · Lo que un repo publico necesita, y una matriz de soporte medida en vez de asumida

## Approach y decisiones

- [2026-08-14] implementer: AC-01/02, clase migration. Medido: ai/state pesa 2,3 MB con 23 features, y ONCE modulos de ai/scripts lo leen. El path se MANTIENE -historial a docs/historia/estado-2026-08, ai/st…
- [2026-08-14] implementer: AC-03/04/05, clase migration. AC-05 desbloquea a los otros dos: hoy el wizard reescribe el models.toml trackeado y tree_clean() es literalmente 'git status --porcelain == vacio', …
- [2026-08-14] implementer: AC-06/07/08. Medido: confirm() en install.sh:56-62 devuelve 0 siempre con --yes, y :309-311 es un 'while confirm ...' que nunca termina. NO_ELIGIBLE_ROUTE (service.py:437) es corr…
- decisión: [[decisiones/2026-08-14 un-test-puede-escribir-en-el-estado-real-del-usuario|Un test sin mockear puede escribir en el estado real del usuario, y lo hizo]]

## Qué falta

- _nada pendiente_ ✅

## Presupuestos

- spawns: 3 (máx 8/paquete) · deep review máx 2 ciclos

[[00 - Proyecto|⌂ Proyecto]] · [[features/024-listo-para-terceros/grafo|grafo]] · bitácora: `/home/federico/SET-AGENTES/docs/specs/024-listo-para-terceros/bitacora.md`

_Actualizado: 2026-08-14T09:40:48+00:00_
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
