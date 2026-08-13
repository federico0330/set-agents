# La captura A/B del refresh se observa pasivamente en vez de forzarse

<!-- notas:auto -->
- fecha: 2026-08-13 · actor: orchestrator
- alcance: [[features/022-disponibilidad-real|022-disponibilidad-real]] · [[features/022-disponibilidad-real/P3-liveness-real|P3-liveness-real]]

## Contexto

AC-08 exige validar con captura A/B real que refreshToken, scopes y subscriptionType no rotan en un refresh normal. El implementer NO la hizo y lo marco 'sin verificar', con la razon de que forzar un refresh puede rotar el refresh_token del lado del servidor y el usuario duerme y depende de esas credenciales manana. La cautela es correcta y coincide con la instruccion explicita que se le dio de no correr logout de verdad.

## Decisión

Se observa un refresh NATURAL en vez de forzarlo. El orquestador tomo un snapshot A de hashes POR CAMPO (nunca valores) de ~/.claude/.credentials.json y ~/.codex/auth.json y lo compara mas tarde en la misma noche, ya que Claude Code corre durante horas y un refresh de OAuth va a ocurrir solo. Riesgo cero. La tarea del A/B queda ABIERTA hasta tener el snapshot B; no se marca completa.

## Consecuencias

El diseno de la firma es robusto a esa incertidumbre por construccion -nunca lee campos rotantes- pero eso es un argumento, no una medicion. Si el snapshot B muestra que scopes/subscriptionType/rateLimitTier rotan, la firma de claude-code hay que rediseniarla y P3 se reabre. Se registra asi para que nadie lea la evidencia como si el supuesto estuviera verificado.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
