# 019-harness-evolution

<!-- notas:auto -->
## Estado

- fase: `DONE` · modo: feature · revisión 258
- estado final: **DONE**
- spec: `docs/specs/019-harness-evolution/spec.md` (hash `c9346fe817cf`)

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
- AC-20
- AC-21
- AC-22
- AC-23
- AC-24
- AC-25
- AC-26
- AC-27
- AC-28
- AC-29
- AC-30
- AC-31
- AC-32
- AC-33
- AC-34
- AC-35

## Paquetes

- [[features/019-harness-evolution/P1-provider-auto-adoption|P1-provider-auto-adoption]] — accepted · Auto-adopcion de providers autenticados y verificables del runtime opencode: discovered_p…
- [[features/019-harness-evolution/P2-billing-aware-ordering|P2-billing-aware-ordering]] — accepted · Ordenamiento consciente del costo (suscripcion/free antes que metered a igual tier) y sup…
- [[features/019-harness-evolution/P3-cognitive-module-docs|P3-cognitive-module-docs]] — accepted · Capa cognitiva: docs/modules/ generado, registro modules.toml, motor render_modules, coma…
- [[features/019-harness-evolution/P4-doctrine-human-layer|P4-doctrine-human-layer]] — accepted · Doctrina: sub-bloque Impacto humano en la narracion, pasos de integrator y architect, pro…
- [[features/019-harness-evolution/P5-tools-discovery|P5-tools-discovery]] — accepted · Catalogo de tools abierto con aprobacion humana: --tools-propose/--tools-approve, tools.l…

## Approach y decisiones

- [2026-08-11] repair-agent: P5 repair ronda 2. NEW-01 (high): tools.local.toml untracked llega a bash -c por --tools-install --yes sin pasar por _validate_install_command, que en cmd_tools_install aparece so…
- [2026-08-11] delta-reviewer: delta-reviewer ronda 2 sobre P5: anthropic/opus frontier, independence_verified=true frente al writer openai-codex/gpt-5.6-terra. Ejes: atacar el camino de lectura con su propio t…
- [2026-08-12] delta-reviewer: delta-reviewer ronda 3 sobre P5: anthropic/opus frontier, independence_verified=true. Alcance: solo NEW-02 y las dos correcciones cosmeticas. El repair encontro un segundo call si…
- [2026-08-12] delta-reviewer: delta-reviewer ronda 4 sobre P5. Alcance: NEW-03 (forma nativa completa del spec mcp) y NEW-04 (transcripcion corregida). El orquestador ya re-verifico las 8 variantes en vivo. Co…
- [2026-08-12] integrator: integrator sobre 019: los 5 paquetes accepted, los 5 con module_impacts registrados (el gate de INTEGRATION que construyo P3 ya paso). Verifica los criterios de cierre (a)-(f) de …
- [2026-08-12] -: 019 DONE. 5/5 paquetes accepted, 6 module_impacts, ADRs 0034-0038 mas 0039 (arreglo del motor de estado autorizado aparte). Suite 815 -> 917 (+102), VERIFY_PASS, CHECK_PASS + SELF…
- decisión: [[decisiones/2026-08-10 el-nuevo-default-discovered-providers-auto-rompe-setup-models-py-que-es-propiedad-de-p2|El nuevo default discovered_providers='auto' rompe setup_models.py, que es propiedad de P2]]
- decisión: [[decisiones/2026-08-10 el-refresh-de-models-toml-catalog-opencode-zen-opencode-go-f-02-de-la-review-de-p1-se-asigna-a-p2|El refresh de models.toml [catalog] opencode_zen/opencode_go (F-02 de la review de P1) se asigna a P2]]
- decisión: [[decisiones/2026-08-10 f-02-refresh-de-models-toml-catalog-vuelve-a-p1-un-hallazgo-se-repara-en-el-paquete-que-lo-levanto|F-02 (refresh de models.toml [catalog]) vuelve a P1: un hallazgo se repara en el paquete que lo levanto]]
- decisión: [[decisiones/2026-08-11 el-schema-de-ac-17-se-parte-3-secciones-derivadas-en-el-bloque-maquina-5-sembradas-en-zona-humana|El schema de AC-17 se parte: 3 secciones derivadas en el bloque maquina, 5 sembradas en zona humana]]
- decisión: [[decisiones/2026-08-11 la-evidencia-del-rol-reparador-no-es-confiable-por-si-sola-tercera-afirmacion-de-verificacion-fabricada-en-la-misma-feature|La evidencia del rol reparador no es confiable por si sola: tercera afirmacion de verificacion fabricada en la misma feature]]
- decisión: [[decisiones/2026-08-11 tools-approve-fuera-del-canal-del-agente|El approve del catalogo de herramientas no entra al canal del agente]]
- decisión: [[decisiones/2026-08-11 p5-implementer-stall-relanzamiento|El primer implementer de P5 murio por stall de infraestructura; se relanza una vez]]
- decisión: [[decisiones/2026-08-11 budget-de-verificacion-cuenta-llamadas-no-veredictos|El presupuesto de verificacion cuenta LLAMADAS a record-verification, no veredictos]]
- decisión: [[decisiones/2026-08-11 p5-repair-excepciones-y-diseno|Excepcion de ownership sobre cmd_tools_install y variante elegida para F-02]]
- decisión: [[decisiones/2026-08-11 p5-repair-stall-relanzamiento|El repair de P5 murio por stall de infraestructura; se relanza una vez (asignacion distinta al implementer)]]
- decisión: [[decisiones/2026-08-11 reopen-no-resetea-el-contador-de-verificacion|HUMAN_DECISION_REQUIRED: reopen limpia el blocker pero no el contador, y deja al paquete permanentemente inaceptable]]
- decisión: [[decisiones/2026-08-11 reopen-resetea-contadores-opcion-A-autorizada|Federico autorizo la opcion A: reopen resetea el contador cuyo agotamiento produjo el blocker]]
- decisión: [[decisiones/2026-08-12 cuarta-verificacion-fabricada-y-patron-del-hermano|Cuarta verificacion fabricada del rol reparador, y el patron de reparar el ejemplo en vez de la clase (tercera iteracion)]]
- decisión: [[decisiones/2026-08-12 anclas-file-line-de-docs-modules-derivan-sin-red|Las anclas file:line sembradas en docs/modules/ derivaron dentro de la misma feature: la desviacion de AC-17 dejo de ser teorica]]

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

- spawns: 14 (máx 12/paquete) · deep review máx 2 ciclos

[[00 - Proyecto|⌂ Proyecto]] · [[features/019-harness-evolution/grafo|grafo]] · bitácora: `/home/federico/SET-AGENTES/docs/specs/019-harness-evolution/bitacora.md`

_Actualizado: 2026-08-12T02:43:19+00:00_
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
