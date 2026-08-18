# El locale de la maquina no decide como se escriben los artefactos del harness

<!-- notas:auto -->
- fecha: 2026-08-18 · actor: orchestrator

## Contexto

render-status escribia STATUS.md con tempfile.NamedTemporaryFile('w') sin encoding, o sea con el encoding del locale. Medido en Linux el 2026-08-18 con PYTHONCOERCECLOCALE=0 LC_ALL=C: la escritura levanto UnicodeEncodeError sobre 'Bitacora', un 'except Exception: pass' se lo trago, render-status salio 0, STATUS.md NUNCA se escribio y el temporal a medias quedo en ai/state/, uno por cada render fallido. La CI de Windows pego el reflejo del mismo hueco: cp1252 escrito ahi y despues leido como UTF-8, 16 UnicodeDecodeError.

## Decisión

encoding='utf-8' explicito en toda lectura y escritura de texto de ai/scripts (barrido completo, 15 archivos), el temporal parcial se borra en el fallo, y el fallo de render_status se rutea a _log_render_failure como ya hacian render_notes y render_modules en vez de desaparecer. Un test AST fija la propiedad sobre todo ai/scripts.

## Consecuencias

Un dashboard que se queda viejo en silencio mientras el comando reporta exito es el falso verde exacto que este harness existe para matar, y estaba en el archivo que reporta el estado. Afectaba a cualquier maquina con locale no UTF-8, no solo a Windows.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
