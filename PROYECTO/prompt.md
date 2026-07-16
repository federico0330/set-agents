# prompt.md — Package workflow starters

Pegá una de estas plantillas como primer mensaje, parado en la raíz del repo. Convierten a la IA en
orquestador, pero el estado ejecutable vive en `ai/state/features/<feature_id>.json`.

**Dónde orquestar: SIEMPRE en OpenCode** (`/feature-batch`), que es el plano de control del harness.
Claude Code queda para review/debug puntual y Codex para una segunda opinión de UNA tarea acotada —
nunca orquestes una feature larga en Codex: sus subagentes heredan el modelo de la sesión e ignoran el
ruteo por rol, y pueden clonar el historial completo (eso quemó una semana de cuota en dos días).

Regla rápida para elegir:
- **Cambio chico y claro** → usá la variante corta o pedilo directo.
- **Feature no trivial** → usá `/feature-batch <descripción>` o la plantilla "Feature nueva".
- **Continuar algo ya empezado** → usá `/resume-feature <feature_id>`.

El flujo activo es:

```text
REQUISITOS
→ SPEC
→ SPEC_CHALLENGE
→ APROBACIÓN DEL USUARIO
→ PACKAGE_PLANNING
→ PACKAGE_IMPLEMENTATION
→ PACKAGE_GATES
→ PACKAGE_REVIEW
→ PACKAGE_REPAIR
→ DELTA_REVIEW
→ PACKAGE_TESTING
→ PACKAGE_RUNTIME_QA
→ PACKAGE_ACCEPTED
→ INTEGRATION
→ DONE | BLOCKED
```

Durante `PACKAGE_IMPLEMENTATION`, cada tarea ejecuta validaciones locales: compile/typecheck, lint dirigido,
unit tests o pruebas locales relevantes, smoke checks e inspección rápida del diff. Eso NO convoca una auditoría
profunda. La auditoría profunda ocurre una vez sobre el paquete integrado.

El orquestador decide qué subagentes convocar. No le pidas al usuario que instancie auditores. Si una feature
toca seguridad, datos, performance, UX o infraestructura, el orquestador arma un panel de revisión con esos
especialistas y lo registra como una sola iteración de auditoría.

---

## A) CONTINUAR un trabajo en curso

> Actuá como el **orchestrator** de este repo. Sos un agente-en-el-loop, pero el workflow se gobierna por
> `ai/scripts/feature-state.py`.
>
> 1. Leé `AGENTS.md`, `docs/specs/**`, `docs/adr/**` y `ai/state/features/**`.
> 2. Ejecutá `python3 ai/scripts/feature-state.py resume <feature_id>` o, si no te di id, localizá el estado
>    activo y consultá `status`.
> 3. Continuá solamente desde la transición permitida por el estado. No reinicies requisitos ni spec si ya están
>    aprobados.
> 4. Implementadores hacen validación local por tarea, pero no llaman reviewers. `package-reviewer` revisa el
>    paquete completo cuando `feature-state.py` permite `PACKAGE_REVIEW`.
> 5. Registrá cada resultado con `feature-state.py`: tareas, gates, review, reparación, delta review, aceptación,
>    integración o bloqueo.
> 6. Preguntame sólo ante `HUMAN_DECISION_REQUIRED`: decisión funcional incompatible, cambio fuerte de alcance,
>    operación irreversible, credenciales faltantes o budget agotado.
>
> Empezá mostrando `feature_id`, fase, próximo evento permitido y paquete activo. Después seguí hasta terminal
> `DONE` o `BLOCKED`.

---

## B) FEATURE NUEVA desde cero

> Actuá como el **orchestrator** de este repo. Quiero arrancar una feature nueva.
>
> **Feature:** <describí qué querés, para qué, y para quién>
>
> 1. Primero cerrá requisitos y Feature Contract con `@product-analyst`; si el pedido está fuzzy, usá
>    `@brainstormer` antes de escribir la spec.
> 2. Si toca arquitectura/datos/seguridad/plata/contratos públicos, `@architect` produce diseño y ADR.
> 3. `@spec-challenger` hace revisión read-only de la spec. Incorporá sólo correcciones concretas y volvé a
>    mostrar el resumen.
> 4. Esperá mi aprobación explícita de la spec.
> 5. Después de aprobar, inicializá estado:
>
>    ```bash
>    python3 ai/scripts/feature-state.py init <feature_id> <spec_path> <spec_hash> --ac AC-1 --ac AC-2
>    ```
>
> 6. `@package-planner` crea paquetes coherentes y registralos con `create-package`. Cada paquete normal debe
>    tener varias tareas relacionadas; sólo usá `complexity=small` para scopes mínimos.
> 7. Delegá implementación del paquete. Cada tarea debe registrar validaciones locales con `complete-task`.
> 8. Corré gates deterministas del paquete y ownership check; registralos con `record-gate`.
> 9. Recién si `feature-state.py next` indica `PACKAGE_REVIEW`, armá el panel necesario:
>    `@package-reviewer` más `@security-auditor`, `@db-auditor`, `@performance-auditor`, `@red-team`,
>    `@blue-team` o `@ux-ui-designer` cuando la superficie lo justifique. Registrá `start-review-panel`,
>    `record-subreview` y `finalize-review-panel`.
> 10. Si hay findings, `@repair-agent` repara el conjunto completo y se registra `record-repair`.
> 11. `@delta-reviewer` revisa el delta. Si pasa, se avanza a testing; si cambia arquitectura/contratos/riesgo, el
>     estado decide si queda budget para re-review completo.
> 12. `@test-writer` agrega regresiones de fin de ciclo, `@gate-runner` corre tests/gates y se registra
>     `record-testing`.
> 13. Si hay comportamiento visible o runtime relevante, `@app-runner` levanta la app y `@runtime-verifier`
>     prueba en navegador/runtime. Registrá `record-runtime-qa` con URL, screenshots/logs y checks.
> 14. Recién después `accept-package`. `@integrator` integra paquetes aceptados, se registran gates globales y se
>     transiciona a `DONE`.
>
> No ejecutes una auditoría profunda después de cada tarea. No me preguntes por fallos rutinarios de tests o gates;
> reparalos dentro del scope y registrá evidencia.

---

## C) Variante corta

> Orchestrator: leé `AGENTS.md`, `docs/specs/**` y `ai/state/features/**`. Si no hay spec aprobada, arrancá el
> flujo de `/feature-batch`. Si ya hay estado, ejecutá `python3 ai/scripts/feature-state.py resume <feature_id>` y
> seguí únicamente desde el próximo paso permitido.

## D) Terminal / diagnóstico

```bash
python3 ai/scripts/feature-state.py status <feature_id>
python3 ai/scripts/feature-state.py next <feature_id>
python3 ai/scripts/feature-state.py dry-run smoke-package-flow
```

`ai/scripts/loop.sh` ya no ejecuta el ciclo viejo; sólo explica cómo migrar a `/feature-batch`.

---

## ¿Cuándo edito un archivo yo?

Casi nunca. Sólo cuando cambia contexto permanente:
- `AGENTS.md` del repo: stack, invariantes de negocio, comandos de test/lint/build.
- Skills de dominio: reglas del cliente que se repiten en muchas features.

Features y fixes viven en specs, paquetes y estado ejecutable.
