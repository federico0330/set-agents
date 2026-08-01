# El gate que exige archivo de estado vive en verify.sh, no en un hook de git

<!-- notas:auto -->
- fecha: 2026-07-28 · actor: orchestrator
- alcance: [[features/009-self-application|009-self-application]] · [[features/009-self-application/P2-state-machine-required|P2-state-machine-required]]

## Contexto

AC-05 nombra tres candidatos y dice que ninguno es gratis. Medidos: verify.sh no tiene ninguna nocion de commit, pero es lo unico que corre el CI en Linux y macOS (.github/workflows/ci.yml:19,30) y ya hospeda el guard de rutas canonicas de P1. El hook post-commit existe, lo escribe build.sh:37-49 y termina en '|| true', asi que no puede hacer fallar nada por construccion, y ademas el objeto commit ya existe cuando corre. Un pre-commit bloqueante seria una clase de aplicacion que este repositorio nunca tuvo, y el dato que lo decide es que .git/hooks/ no se versiona: no existe en un clon nuevo, no existe en el runner del CI, y build.sh tendria que instalarlo en cada maquina.

## Decisión

El gate vive solo en verify.sh, como ai/scripts/check-feature-state.py invocado despues de check-canonical-paths.py. Script propio y no heredoc: el hallazgo F-02 de P1 probo que un guard cuyo camino de falla ningun test puede manejar se pudre sin que nadie lo note.

## Consecuencias

Asumido por escrito: NO bloquea un commit local. Una entrega por fuera de la maquina de estados se puede commitear y se descubre en la proxima verificacion o en el PR, no en el momento. A cambio, es el unico punto que ve todo el mundo - CI, clon nuevo, invitado - en vez de una sola maquina. La senal que usa son los commits que nombran feature y paquete, porque 006 no dejo evidence/, ni context/, ni bitacora.md: un gate del sistema de archivos estaria verde justo sobre el caso que existe para detectar, y bitacora.md ademas es circular porque lo renderiza feature-state.py desde el archivo de estado. Efecto lateral buscado: el periodo previo a la aprobacion queda tranquilo por construccion, porque redactar un spec no produce commits con token de paquete.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
