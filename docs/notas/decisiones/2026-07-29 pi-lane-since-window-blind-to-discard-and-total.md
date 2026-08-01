# El carril pi de cost-report.py: --since filtra las filas contadas pero no los totales de diagnostico

<!-- notas:auto -->
- fecha: 2026-07-29 · actor: delta-reviewer
- alcance: [[features/007-quota-visibility|007-quota-visibility]] · [[features/007-quota-visibility/P2-spawn-accounting|P2-spawn-accounting]]

## Contexto

N-02 (delta review de 007-P2) encontro que collect_pi conta 'matched' filtrando por since_ms en el loop de Python, pero tanto el conteo de 'otros proyectos' (cuando matched==0) como el conteo de filas descartadas (usage_status!='ok') se calculan con SQL que no aplica ese mismo filtro de tiempo. El primero ya se corrigio (project_key!=? para no acusar al propio proyecto), pero ninguno de los dos aplica --since.

## Decisión

Se acepta como deuda registrada, no se arregla en este repair. Arreglarlo bien requiere que la clausula SQL vea el mismo reloj que el loop de Python ya filtra (updated_at>=?), lo cual es un cambio mayor a dos queries de diagnostico que ya fueron tocadas dos veces en el mismo paquete -- el presupuesto de reparos por hallazgo existe justamente para esto.

## Consecuencias

Con --since, el aviso de filas descartadas puede incluir filas fuera de la ventana de tiempo pedida. No afecta los datos persistidos ni el reporte de tokens en si, solo el texto de los avisos de diagnostico por stderr.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
