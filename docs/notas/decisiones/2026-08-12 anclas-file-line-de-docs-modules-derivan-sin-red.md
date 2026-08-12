# Las anclas file:line sembradas en docs/modules/ derivaron dentro de la misma feature: la desviacion de AC-17 dejo de ser teorica

<!-- notas:auto -->
- fecha: 2026-08-12 · actor: orchestrator
- alcance: [[features/019-harness-evolution|019-harness-evolution]]

## Contexto

El integrator, verificando el criterio (d) de cierre, corrio a mano el procedimiento de staleness que /explicar promete y encontro deriva real en las secciones sembradas de docs/modules/: las referencias a generate.py estan corridas +9 lineas, feature-state.py:788 esta corrida +4, y docs/modules/consola.md dice que set_agents_app.py:2510 es main() cuando esta corrida +742. Causa: P3 sembro esos puntos de entrada y despues P5 agrego ~880 lineas a esos mismos archivos. Es un defecto de interaccion entre paquetes, invisible para los cinco reviews de paquete porque cada uno miro su propio diff. Y es exactamente el riesgo que se acepto al aprobar la desviacion del schema de AC-17 (tres secciones derivadas por el motor, cinco sembradas a mano y preservadas), cuyo unico mitigante registrado es que /explicar las contraste contra el codigo cada vez que corre -- o sea, algo manual y solo si alguien lo corre.

## Decisión

Se registra como deuda conocida de 019, NO se parchea a mano en la integracion: corregir los numeros hoy los deja corridos otra vez con el proximo paquete que toque esos archivos, que es precisamente el modo de falla. La solucion correcta es un verificador de anclas -- que una referencia file:line en docs/modules/ que ya no apunta a lo que dice sea un fallo detectable por comando, no por lectura humana. Va como feature nueva con su flujo completo.

## Consecuencias

Mientras tanto, docs/modules/ contiene referencias file:line falsas. Quien las lea antes del arreglo tiene que verificarlas contra el codigo, que es justamente lo que /explicar manda hacer. La feature 019 se cierra con esta deuda explicita en su evidencia de integracion.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
