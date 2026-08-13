# Medicion en vivo: listar modelos funciona y la inferencia falla con token vencido

<!-- notas:auto -->
- fecha: 2026-08-13 · actor: orchestrator
- alcance: [[features/022-disponibilidad-real|022-disponibilidad-real]] · [[features/022-disponibilidad-real/P1-registro-de-proveedores|P1-registro-de-proveedores]]

## Contexto

El router eligio opencode/openai-codex/gpt-5.6-terra para el reviewer de P1 (dec1_4ac1490e, independence_verified=true). La ejecucion real fallo: 'Error: Provided authentication token is expired.' Medido en la misma sesion: 'opencode auth list --pure' muestra la credencial OpenAI (oauth) presente, y 'opencode models openai --pure' lista 13 modelos sin error. O sea el probe -que es una llamada de LISTADO- dice que el par esta vivo, y la INFERENCIA no funciona.

## Decisión

El reviewer se ejecuta en opencode/gpt-5.6-terra servido por opencode-zen (credencial API key, verificada con un smoke que devolvio PONG). Mismo modelo que eligio el router, proveedor distinto al del writer (anthropic), independencia preservada. Se registra el desvio en la evidencia del review.

## Consecuencias

Es evidencia empirica para 022: listable != usable. AC-16 y P3 asumen que un probe de listado prueba liveness; esta medicion muestra que no. Deberia entrar como insumo de P3 (liveness-real) y de AC-19 (separar listed_by_provider de usable). Tambien queda medido que en opencode TODOS los roles del harness son subagent y solo 'orchestrator' es primary, asi que 'opencode run --agent <rol>' no puede despachar un rol: cae al agente por defecto con un warning.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
