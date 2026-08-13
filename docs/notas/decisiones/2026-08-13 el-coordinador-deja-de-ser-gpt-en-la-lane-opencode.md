# El coordinador deja de ser GPT en la lane de opencode

<!-- notas:auto -->
- fecha: 2026-08-13 · actor: orchestrator
- alcance: [[features/022-disponibilidad-real|022-disponibilidad-real]]

## Contexto

Pedido de Federico (2026-08-13): 'no me gusta gpt como alguien que resuelve o determina acciones, me sienta mejor claude/grok/qwen para ese tipo de decisiones', y ademas 'no creo que este tan bueno poner un modelo de anthropic de copilot porque me va a consumir la suscripcion a todo poder'. Medido antes de tocar: el rol orchestrator ruteaba a openai-codex/gpt-5.6-luna, y el modelo de nivel superior de su opencode.json era openai/gpt-5.6-fast, ambos GPT.

## Decisión

Dos palancas, las dos aplicadas. (1) models.toml [areas.coord].opencode pasa de openai/gpt-5.6-fast a opencode-go/grok-4.5 en la lane go-zen y opencode/grok-4.5 en zen y local; el orquestador hereda de coord y generate.py:569 usa ese valor como modelo de nivel superior del opencode.json. (2) --model-pin-set orchestrator opencode-go/grok-4.5, verificado en vivo: la decision devuelve MODEL_PINNED opencode-go/grok-4.5 con BILLING_RANK rank=0. Se eligio opencode-go porque es SUSCRIPCION: no consume la de Copilot ni el medido por token de zen.

## Consecuencias

Limite honesto: en la lane de CODEX el orquestador sigue siendo GPT (gpt-5.6-terra) y no puede ser otra cosa -el CLI de codex solo sirve modelos de OpenAI-. En la lane de claude-code es sonnet, que es la suscripcion propia de Federico, no la de Copilot. Correccion detectada al aplicar: grok-4.6 NO esta en el techo [catalog].opencode_zen, asi que zen y local usan grok-4.5. Ademas quedan CUATRO roles de juicio que siguen cayendo en GPT por defecto y que el pedido no nombro: adversarial-judge, package-reviewer, spec-challenger y architect, los cuatro a openai-codex/gpt-5.6-luna. Se reportan para que Federico decida, no se cambian por iniciativa propia.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
