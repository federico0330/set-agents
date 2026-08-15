# Corte de cuota: los cinco agentes concurrentes murieron simultaneamente

<!-- notas:auto -->
- fecha: 2026-08-15 · actor: orchestrator

## Contexto

A las 05:45 aproximadamente del 2026-08-15, los cinco subagentes en vuelo terminaron a la vez con 'Agent terminated early due to an API error: You've hit your session limit'. Eran el repair de 025/D1, el repair de 025/D4, el implementer de 028/N3a, el review de 025/D5 y el implementer del fix de seguridad 030. Es limite de cuenta, no de tarea: ninguno fallo en su trabajo. Trabajo parcial sobreviviente medido en los worktrees: D1-repair 936 inserciones -incluido el arreglo del --json en los prompts de los cuatro harnesses y el ADR-0050-, D4-repair 5622 inserciones -a revisar, el tamano no cuadra con su alcance declarado-, 028/N3a 2027 inserciones con los espejos de PROYECTO/ incluidos y aparentemente coherente. El fix de seguridad 030 NO produjo nada: su worktree quedo vacio.

## Decisión

Doctrina de ADR-0011 y CLAUDE.md: una instancia que muere por cuota no fallo en la tarea, no consume presupuesto de reintentos, y se relanza una vez con otro modelo sin preguntar, persistiendo la causa. Se relanza primero el fix de seguridad, que es lo unico critico y lo unico que no dejo nada. Si el limite es de cuenta y no de modelo, el orquestador lo implementa directamente y lo marca explicitamente como NO revisado de forma independiente, pendiente de review cuando vuelva la cuota: dejar un RCE sin parchear en un repo publico es peor que un parche con su limitacion declarada.

## Consecuencias

Quedan disponibles openai-codex, opencode-go y opencode-zen, verificados autenticados esta misma noche via --route-doctor, asi que el harness NO esta sin proveedores: esto es degradacion, no bloqueo. Lo que se pierde en el camino degradado es la independencia de review sobre lo que el orquestador implemente por su cuenta, y eso queda declarado en vez de disimulado.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
