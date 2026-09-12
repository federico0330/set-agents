# 049-identidad-honesta-modelos

<!-- notas:auto -->
## Estado

- fase: `DONE` · modo: feature · revisión 370
- estado final: **DONE**
- spec: `docs/specs/049-identidad-honesta-modelos/spec.md` (hash `0ed880d4bbb7`)

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

- [[features/049-identidad-honesta-modelos/PKG-A|PKG-A]] — accepted · Proyección efectiva para instalación y drift locales
- [[features/049-identidad-honesta-modelos/PKG-B|PKG-B]] — accepted · ModelState singular y CLI de observación privada
- [[features/049-identidad-honesta-modelos/PKG-C|PKG-C]] — superseded · Consola cache-first y wizard de convergencia por readback
- [[features/049-identidad-honesta-modelos/PKG-D|PKG-D]] — superseded · Integración de identidad de modelos, ayuda y TTY aislada
- [[features/049-identidad-honesta-modelos/PKG-C2|PKG-C2]] — accepted · Rehacer consola cache-first y convergencia en candidato Git aislado
- [[features/049-identidad-honesta-modelos/PKG-D2|PKG-D2]] — accepted · Integración de identidad de modelos, ayuda y TTY aislada sobre candidato reconstruido

## Approach y decisiones

- ruteo PKG-A: Route decision dec1_874f5386d86738581762fbe607c1dc46 was supplied; its resolved provider/model is not present in readab…
- ruteo PKG-B: Route decision dec1_874f5386d86738581762fbe607c1dc46 was supplied; its resolved provider/model is not present in readab…
- ruteo PKG-C: Route decision dec1_874f5386d86738581762fbe607c1dc46 was supplied; its resolved provider/model is not present in readab…
- ruteo PKG-D: Route decision dec1_874f5386d86738581762fbe607c1dc46 was supplied; its resolved provider/model is not present in readab…
- ruteo PKG-C2: Replacement explicitly chosen by user after unrecoverable dirty-worktree candidate identity; isolated Git reconstructio…
- ruteo PKG-D2: Replacement integration package depends on the isolated PKG-C2 candidate chosen by the user.
- [2026-09-10] runtime-verifier: ROUTING_UNAVAILABLE→BASE; evidence PKG-D2-tty.md + 19 tests
- [2026-09-10] adversarial-judge: ROUTING_UNAVAILABLE→BASE; INTEGRATION; all packages accepted
- [2026-09-10] adversarial-judge: ROUTING_UNAVAILABLE→BASE; tip 5076dd2; J-049-001/002 remediated
- [2026-09-10] adversarial-judge: tip 95edc5654c218c0f7e8fa52d66cc015abcd6350f; J-049-003 fixed
- [2026-09-10] adversarial-judge: JUDGE_PASS eaa1dfd8; tip 95edc5654c218c0f7e8fa52d66cc015abcd6350f
- [2026-09-10] adversarial-judge: El re-juicio pasó porque el árbol integrado ya traía el cuarteto y el verify dejó de fallar por espacios al final de línea en evidence/PKG-C2-runtime-qa.md:3.
- decisión: [[decisiones/2026-09-09 rehacer-pkg-c-desde-candidato-git-aislado|Rehacer PKG-C desde candidato Git aislado]]
- decisión: [[decisiones/2026-09-09 fundación-preexistente-de-c2|Fundación preexistente de C2]]
- decisión: [[decisiones/2026-09-09 navegación-tty-como-fundación-preexistente-de-c2|Navegación TTY como fundación preexistente de C2]]
- decisión: [[decisiones/2026-09-09 corrección-de-alcance-para-fundación-tty-c2|Corrección de alcance para fundación TTY C2]]
- decisión: [[decisiones/2026-09-10 última-continuación-aislada-de-pkg-c2|Última continuación aislada de PKG-C2]]
- decisión: [[decisiones/2026-09-10 extender-fundación-c2-a-dependencias-integradas|Extender fundación C2 a dependencias integradas]]
- decisión: [[decisiones/2026-09-10 pkg-c2-repair-ceiling-exceeded-after-unique-retry|PKG-C2 repair ceiling exceeded after unique retry]]
- decisión: [[decisiones/2026-09-10 waiver-del-techo-de-reparación-pkg-c2-a-315|Waiver del techo de reparación PKG-C2 a 315]]
- decisión: [[decisiones/2026-09-10 segundo-repair-delta-elevó-el-total-a-416|Segundo repair delta elevó el total a 416]]
- decisión: [[decisiones/2026-09-10 waiver-del-techo-pkg-c2-ampliado-a-416|Waiver del techo PKG-C2 ampliado a 416]]
- decisión: [[decisiones/2026-09-10 waiver-del-techo-pkg-c2-ampliado-a-454|Waiver del techo PKG-C2 ampliado a 454]]
- decisión: [[decisiones/2026-09-10 ampliar-frontier-pkg-d2-tras-frontier-cap-exhausted|Ampliar frontier PKG-D2 tras FRONTIER_CAP_EXHAUSTED]]
- decisión: [[decisiones/2026-09-10 waiver-techo-reparación-pkg-d2-a-170|Waiver techo reparación PKG-D2 a 170]]
- decisión: [[decisiones/2026-09-10 049-bloqueado-por-juicio-adversario-en-verify-sh|049 bloqueado por juicio adversario en verify.sh]]
- decisión: [[decisiones/2026-09-10 cerrar-049-vía-integrar-045-048-primero|Cerrar 049 vía integrar 045-048 primero]]
- decisión: [[decisiones/2026-09-10 049-close-after-option-2-whitespace-fix|049 close after option-2 + whitespace fix]]

## Convenciones

| Eje | Origen | Stance | Umbral | Siguiente | Revisit |
|---|---|---|---|---|---|
| data-store | adr | Reutiliza archivos locales y memoria efímera; sin SQL, NoSQL ni vector |  |  |  |
| api-gateway | n/a | No aplica: CLI local sin nueva entrada de red |  |  |  |
| deploy-platform | adr | Instalación local mediante build.sh; sin PaaS, VPS ni managed nuevo |  |  |  |
| audience | request | Personas que operan SET y OpenCode localmente |  |  |  |
| embeddings | n/a | No aplica: no hay búsqueda semántica |  |  |  |
| realtime | adr | No aplica: refresh explícito, sin streaming |  |  |  |
| mobile | n/a | No aplica: consola TTY/CLI |  |  |  |
| auth | adr | Reutiliza autenticación local de OpenCode; no maneja credenciales |  |  |  |
| cost | request | Sin servicios pagos nuevos; subprocesses sólo bajo refresh explícito |  |  |  |
| legal | adr | No persiste ni muestra prompts, respuestas o IDs de sesión |  |  |  |

## Qué falta

- WARN spawns 11/12 WARN 80%

## Presupuestos

- spawns: 33 (máx 12/paquete) · deep review máx 2 ciclos

[[00 - Proyecto|⌂ Proyecto]] · [[features/049-identidad-honesta-modelos/grafo|grafo]] · bitácora: `/home/federico/SET-AGENTES/docs/specs/049-identidad-honesta-modelos/bitacora.md`

_Actualizado: 2026-09-10T17:52:36+00:00_
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
