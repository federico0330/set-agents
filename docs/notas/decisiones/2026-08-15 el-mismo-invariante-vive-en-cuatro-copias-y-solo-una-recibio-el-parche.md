# CRITICO: los guardas de shell son cuatro copias del mismo invariante, con agujeros distintos cada una

<!-- notas:auto -->
- fecha: 2026-08-15 · actor: orchestrator

## Contexto

Segundo eje de la auditoria, y es la causa raiz de las guardas falsas-verdes confirmada por tercera vez. El mismo invariante -que comando no puede componer shell- vive duplicado en cuatro lugares con contenido distinto: coord_policy.FORBIDDEN_SYNTAX (con el & del arreglo F-01 y la clase de caracteres de control), claude_release_guard.FORBIDDEN (SIN el & y SIN los caracteres de control: el arreglo F-01 nunca se propago), claude_local_gate_guard (SIN NINGUN chequeo de composicion), y una cuarta copia en globs en generate.py:186-197 para la lane de OpenCode, con un conjunto de agujeros distinto de los otros tres. PoC ejecutado contra los hooks reales: 'record-gate --state-file <valido> ' devuelve ALLOW en claude_local_gate_guard, porque valida la forma de argv con shlex.split y bash despues expande la sustitucion; y 'release_action.py ST act -- true & touch /tmp/pwn_rel' devuelve ALLOW en claude_release_guard. El primero es RCE desde local-gate-runner, que es el rol con el perimetro mas chico declarado del harness.

## Decisión

Los tres guardas de Python deben IMPORTAR coord_policy.FORBIDDEN_SYNTAX en vez de redeclarar su propia copia, y un test parametrico unico tiene que correr el MISMO corpus de metacaracteres contra los cuatro. Entra en la feature 030 junto con SEC-001.

## Consecuencias

Una reparacion aplicada a una sola copia deja las otras tres en verde, y eso ya paso: el comentario de coord_policy.py:127-133 explica el bug del & con detalle y lo arregla en un solo archivo. Mientras existan cuatro copias, cada hallazgo de seguridad futuro va a tener que repararse cuatro veces y nadie va a acordarse.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
