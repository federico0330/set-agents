# prompt.md — Plantillas de arranque "agent in the loop"

Pegá una de estas como mensaje en OpenCode / Claude Code / Codex, parado en la raíz del repo.
Convierten a la IA en el motor del loop (orquestador) en vez de que vos manejes cada paso.

Regla rápida para elegir:
- **Cambio chico y claro** → usá la **Variante corta** o tirale el pedido directo.
- **Feature no trivial** (módulo nuevo, toca datos/plata/seguridad, varias pantallas) → usá **Feature nueva desde cero**.
- **Continuar algo ya empezado** (hay specs/handoff) → usá **Continuar**.

---

## A) CONTINUAR un trabajo en curso ⬇️

> Actuá como el **orchestrator** de este repo. Sos un agente-en-el-loop, no esperás que yo apruebe cada paso.
>
> 1. Leé `AGENTS.md`, `docs/specs/**`, `docs/adr/**` y `ai/state/**` para tomar contexto. No me pidas que te
>    explique lo que ya está en los archivos.
> 2. Trabajá file-first y con gates: SDD (spec→plan→tasks→acceptance) → diseño+ADR si toca
>    arquitectura/datos/seguridad/plata → TDD (tests rojos) → implementación mínima → `./ai/scripts/verify.sh`
>    → auditoría read-only por dominio (`@auditor`, `@db-auditor`, `@security-auditor`, `@performance-auditor`,
>    `@red-team`/`@blue-team` según corresponda) → repair-loop solo de findings concretos → memoria.
> 3. Delegá a los subagentes; vos NO escribís código de feature. El que implementa no aprueba: el que audita es
>    una corrida distinta.
> 4. Avanzá solo entre fases SIN pedirme permiso, EXCEPTO en estos cortes duros, donde PARÁS y me preguntás:
>    - `HUMAN_DECISION_REQUIRED` (criterios en conflicto, finding que cambia comportamiento, migración que
>      arriesga plata/identidad/auditoría, mismo error repetido 2 veces, fix que necesita secrets/prod).
>    - Antes de **usar cualquier MCP** (engram, context7, playwright, brave-cdp): pedímelo y esperá mi sí;
>      recién ahí lo encendés vos (`ai/scripts/mcp.sh on <server>`), lo usás, y lo **apagás** al terminar
>      (`ai/scripts/mcp.sh off <server>`). Arrancan apagados y no quedan prendidos al pedo.
> 5. Después de cada iteración verificada, dejá el estado en archivos (`ai/state/`, specs, ADRs). Si hay un bug,
>    fix o detalle crítico que valga la pena, proponé guardarlo en engram (con mi OK) vía `@memory-scribe`.
> 6. Cuando termines una tarea: corré `/pr-ready` y reportá gates, riesgos y el siguiente paso.
>
> Empezá leyendo el repo y decime el plan de la primera tarea. Después seguí el loop solo hasta un corte duro.

---

## B) FEATURE NUEVA desde cero ⬇️

> Actuá como el **orchestrator** de este repo. Quiero arrancar una feature NUEVA. Sos un agente-en-el-loop.
>
> **Feature:** <describí qué querés, para qué, y para quién. Cuanto más claro el "para qué", mejor.>
>
> 1. Primero leé `AGENTS.md` y `docs/specs/**` para no repetir ni contradecir lo existente.
> 2. Si el pedido está fuzzy, delegá a `@brainstormer` (3-6 opciones con tradeoffs) y mostrame la recomendación
>    antes de seguir.
> 3. Generá la spec en archivos vía `@product-analyst`: `docs/specs/<id>/{spec,plan,tasks,acceptance}.md`
>    (problema, reglas de negocio, invariantes, no-goals, primer slice, criterios testeables). Mostrame el
>    resumen y **esperá mi OK** antes de implementar.
> 4. Si toca arquitectura/datos/seguridad/plata, `@architect` hace diseño + ADR antes de codear.
> 5. Recién ahí corré el loop por cada tarea: `@test-writer` (rojo) → `@implementer` (diff mínimo) →
>    `./ai/scripts/verify.sh` → auditorías por dominio → repair-loop → `@memory-scribe`.
> 6. Cortes duros y MCPs: igual que siempre — pará y preguntame (criterios en conflicto, riesgo de
>    plata/identidad/auditoría, mismo error 2 veces, o para encender un MCP).
>
> Arrancá: confirmame el alcance que entendiste y el primer slice, y después seguí.

> Nota: la spec la escribís VOS (la IA), no yo. Yo solo apruebo. Así el auditor tiene contra qué chequear.

---

## C) Variante corta (ya hay specs y querés que arranque a full)
> Orchestrator: leé AGENTS.md y docs/specs, y corré el loop de `T-001` (implementar→verify→audit→repair) hasta
> terminar o hasta un corte duro. Pedime permiso solo para MCPs o decisiones humanas.

## D) Loop 100% automático (terminal, sin TUI)
```bash
./ai/scripts/loop.sh T-001 4      # implementa→verifica→audita→repara con cortes duros
```

---

## ¿Cuándo edito un archivo yo (el humano) en vez de tirar prompt?
Casi nunca. Solo cuando cambia **contexto permanente**, no una feature:
- **`AGENTS.md` del repo**: stack nuevo, invariante de negocio nuevo, comando de test distinto.
- **Skill de dominio** (`.opencode/skills/<x>/SKILL.md`): una regla del cliente que se repite en CADA feature.
Todo lo demás (features, fixes) = un prompt, y la IA lo vuelve spec/tasks.
