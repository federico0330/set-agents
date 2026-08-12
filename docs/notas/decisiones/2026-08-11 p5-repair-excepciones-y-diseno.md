# Excepcion de ownership sobre cmd_tools_install y variante elegida para F-02

<!-- notas:auto -->
- fecha: 2026-08-11 · actor: orchestrator
- alcance: [[features/019-harness-evolution|019-harness-evolution]] · [[features/019-harness-evolution/P5-tools-discovery|P5-tools-discovery]]

## Contexto

La reparacion de P5 necesita tocar dos cosas que el context pack habia declarado intocables o no habia previsto. Lección de P3 registrada: un finding se repara en el paquete que lo levanto, y lo correcto es ensanchar la ownership de ese paquete con una excepcion aprobada, nunca mover el finding a otro paquete.

## Decisión

1) EXCEPCION DE OWNERSHIP APROBADA: F-03 obliga a tocar cmd_tools_install:1544 (el startswith('sudo ')), que el context pack habia puesto fuera de alcance. La prohibicion apuntaba a que no se relajara la postura; este cambio la ENDURECE (rechaza escaladores con path en la rama que muestra y pregunta), asi que respeta la intencion y se aprueba. El resto del cuerpo de cmd_tools_install sigue intocable. 2) VARIANTE ELEGIDA PARA F-02: cmd_tools_approve re-imprime el bloque completo de la propuesta y exige confirmacion interactiva, reusando el patron que cmd_tools_install:1549-1555 ya usa para sudo (incluida la negativa sin TTY). Se descarta la variante del digest (--tools-approve <name> --confirm <digest>) como requisito: puede sumarse encima, pero no reemplaza la re-impresion, porque el problema es que el humano no ve lo que aprueba. Es coherente con la decision de producto ya tomada (siempre preguntar antes de instalar) y conserva la gramatica de solo-el-nombre que fija AC-31. 3) F-11: se documenta el alcance REAL (el catalogo es global al clon del harness, no per-project) y se corrige el comentario del .gitignore; no se rediseña a per-project, que seria otro paquete.

## Consecuencias

Las tres quedan argumentadas en ADR-0038 antes de tocar el codigo. La excepcion de ownership se registra en el estado del paquete.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
