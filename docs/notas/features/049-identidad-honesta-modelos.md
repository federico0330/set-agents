# 049-identidad-honesta-modelos

<!-- notas:auto -->
## Estado

- fase: `BLOCKED` · modo: feature · revisión 355
- estado final: **BLOCKED**
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
- [2026-09-10] security-auditor: ROUTING_UNAVAILABLE→BASE; evidence sanitization; no product patch
- [2026-09-10] finding-verifier: ROUTING_UNAVAILABLE→BASE; uphold or refute with evidence
- [2026-09-10] repair-agent: ROUTING_UNAVAILABLE→BASE; NEW_D2_REF=9bc4e2d; +170 lines vs 6bd4253
- [2026-09-10] delta-reviewer: ROUTING_UNAVAILABLE→BASE; close F01/SEC-001/SEC-002; no new findings preferred
- [2026-09-10] runtime-verifier: ROUTING_UNAVAILABLE→BASE; evidence PKG-D2-tty.md + 19 tests
- [2026-09-10] adversarial-judge: ROUTING_UNAVAILABLE→BASE; INTEGRATION; all packages accepted
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

- → corresponde tu decisión (ver Blocker)
- ⛔ bloqueo: HUMAN_DECISION_REQUIRED: adversarial-judge FAIL J-049-001 (AC-09 verify.sh rc≠0; cannot green on C2+D2 candidate while …

## Presupuestos

- spawns: 30 (máx 12/paquete) · deep review máx 2 ciclos

[[00 - Proyecto|⌂ Proyecto]] · [[features/049-identidad-honesta-modelos/grafo|grafo]] · bitácora: `/home/federico/SET-AGENTES/docs/specs/049-identidad-honesta-modelos/bitacora.md`

_Actualizado: 2026-09-10T17:04:59+00:00_
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
