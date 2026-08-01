# El nivel cross-proyecto del conocimiento se muda al path que los prompts nombran

<!-- notas:auto -->
- fecha: 2026-07-28 · actor: orchestrator
- alcance: [[features/009-self-application|009-self-application]] · [[features/009-self-application/P1-knowledge-home|P1-knowledge-home]]

## Contexto

La capa de conocimiento son dos niveles, no dos copias: docs/ai/knowledge/<dominio>.md es la memoria del proyecto, que escribe solo memory-scribe, y docs/ai/knowledge/_global/<dominio>.md es la capa cross-proyecto que sync-project.sh:84-96 reparte en solo lectura a cada proyecto. El commit 279c10e los creo asi a proposito. El arnes tenia el nivel cross-proyecto en una carpeta knowledge/ en la raiz que ningun prompt nombra, y no tenia el nivel de proyecto en absoluto: se lo daba a todos sus hijos y no a si mismo. Por eso diez prompts leian una ruta inexistente y memory-scribe, obligatorio al cierre de cada feature, nunca consolido nada en cinco features entregadas.

## Decisión

git mv de knowledge/*.md a docs/ai/knowledge/_global/, con sync-project.sh:84 repuntado, y el nivel de proyecto del arnes sembrado copiando verbatim la plantilla de PROYECTO/docs/ai/knowledge/. PROYECTO no se toca: es la semilla de los hijos, no una segunda copia. La alternativa era dejar knowledge/ donde estaba y crear solo el nivel de proyecto, que cuesta menos churn pero deja las cinco rutas _global sin resolver dentro del arnes para siempre, que es el mismo no-op silencioso que la feature existe para matar.

## Consecuencias

En el repo del arnes docs/ai/knowledge/_global/ es a la vez la fuente de distribucion y lo que sus propios agentes leen como capa global; no hay canal automatico entre niveles, la promocion la hace un humano. Un solo consumidor en codigo dependia de la ubicacion vieja y esta repuntado; ni README, ni los instaladores, ni el CI, ni ADR-0008 la mencionaban. El test que exigia knowledge/<dom>.md se reapunto, no se debilito: misma asercion, mas la del nivel nuevo. Se registro aca y no en un ADR porque la regla del arnes dice que una decision que trasciende a su paquete se persiste con log-decision y los ADR se enlazan, no se duplican; ademas docs/architecture/overview.md:3 se declara mapa de trusted routing P1R, no del repo entero.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
