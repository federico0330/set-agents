# Un test sin mockear puede escribir en el estado real del usuario, y lo hizo

<!-- notas:auto -->
- fecha: 2026-08-14 · actor: orchestrator
- alcance: [[features/024-listo-para-terceros|024-listo-para-terceros]] · [[features/024-listo-para-terceros/C2-modelstoml-neutro|C2-modelstoml-neutro]]

## Contexto

Durante la implementacion de C2, un test preexistente sin mockear escribio contra el overlay real de Federico en ~/.local/state/set-agentes/ y perdio la entrada 'ollama = false'. El implementer lo detecto, lo corrigio en el acto y lo REPORTO por su cuenta en su informe, sin que nadie preguntara. Verificado por el orquestador: las cuatro suscripciones estan (anthropic true, ollama false, openai true, zen true) y las decisiones de ruteo son identicas -orchestrator opencode-go/grok-4.5, implementer y package-reviewer openai-codex/gpt-5.6-luna-.

## Decisión

Se registra como DEFECTO DEL HARNESS, no del agente. Que un test pueda alcanzar STATE_DIR real significa que cualquier corrida de la suite en la maquina de un usuario puede mutar su configuracion. El agente hizo lo correcto: detectar, corregir y declarar. Lo que falta es que no pueda pasar.

## Consecuencias

Candidato a paquete propio junto con los otros defectos latentes de la misma familia -check-owned-paths.py que no ve archivos nuevos, el aislamiento roto de los modulos de test, y el orden del gate de pi en _probe_pairs-. La forma probable del arreglo: una guarda que haga fallar cualquier test que escriba fuera de un directorio temporal, al estilo del candado de DDL que nacio de la regresion de esquema de 023/B3. No se arregla en 024: esta fuera de su alcance y el paquete que lo descubrio no puede ser el que lo repara.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
