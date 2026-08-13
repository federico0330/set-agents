# Captura A/B cerrada: el refresh natural confirmo el diseno de la firma

<!-- notas:auto -->
- fecha: 2026-08-13 · actor: orchestrator
- alcance: [[features/022-disponibilidad-real|022-disponibilidad-real]] · [[features/022-disponibilidad-real/P3-liveness-real|P3-liveness-real]]

## Contexto

AC-08 exigia validar con captura A/B real que los campos usados por la firma de claude-code no rotan en un refresh. El implementer no la hizo por riesgo de rotar el refresh_token del usuario; el orquestador OBSERVO un refresh natural en vez de forzarlo. Snapshot A a las 00:5x, snapshot G a las 06:04, hashes POR CAMPO (nunca valores).

## Decisión

CONFIRMADO. El refresh natural ocurrio (mtime del archivo cambio). ROTARON: accessToken, expiresAt, refreshToken, refreshTokenExpiresAt. NO ROTARON: scopes, subscriptionType, rateLimitTier -- que son exactamente los tres campos que _claude_code_auth_signature lee (catalog.py:484-502). La firma es estable a traves de un refresh, como el diseno afirmaba. La tarea A/B de AC-08 queda CERRADA con medicion, y P3 NO se reabre.

## Consecuencias

Dos validaciones de diseno que antes eran solo argumento y ahora son medicion. PRIMERA: refreshToken SI rota. La spec habia rechazado hashearlo por el limite de identidad de cuenta; resulta que ademas habria roto la firma en cada refresh, probeando en cada decision (hasta 60 s en pi). La decision correcta lo era por una razon mas de la que se sabia. SEGUNDA: el mtime del archivo cambio, asi que hashear el archivo o su mtime -la trampa que el context pack nombro por el mcpOAuth- habria rotado igual. Ambas trampas confirmadas empiricamente en la maquina del usuario, sin tocar una sola credencial.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
