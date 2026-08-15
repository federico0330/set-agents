# Los numeros de ADR de la spec 025 estaban viejos y se corrigieron a favor de los context packs

<!-- notas:auto -->
- fecha: 2026-08-15 · actor: orchestrator
- alcance: [[features/025-consola-minima-y-flexible|025-consola-minima-y-flexible]]

## Contexto

Hallazgo D1-F10 del review independiente. La spec de 025 (escrita el 2026-08-12) declaraba ADRs 0049 para superficie humana y 0050 para posturas de autonomia. Los dos numeros quedaron mal: 0049 lo tomo 024/C3 primer-arranque-honesto antes de que 025 arrancara, y 0051 y 0052 los tomo la feature 027 mientras 025 estaba detenida. Los context packs de D1 a D5, escritos el 2026-08-15, asignaron un bloque contiguo distinto -0050, 0053, 0054, 0055, 0056- y son los que siguieron los implementers: D1 ya escribio docs/adr/0050-superficie-humana.md.

## Decisión

Gana la asignacion de los context packs, que es la que refleja el estado real de docs/adr/ y la que ya esta implementada. La linea de la spec se corrigio dejando la correccion visible en el propio documento en vez de reescribirla en silencio, porque una spec aprobada que cambia sin dejar rastro es peor que una spec con un numero viejo. El mapa vigente: 0050 D1, 0053 D2, 0054 D3, 0055 D4, 0056 D5; 0057 para la feature 028 y 0058 para la 029, desempatados aparte el mismo dia.

## Consecuencias

De paso se remidio la seccion 'Estado medido' de la spec, que declaraba 67 flags y 31 internas sin criterio escrito. Hoy son 68, y el review independiente midio que las que un humano usa de verdad son 15, o 22 contando diagnostico defendible. La spec deja de dar una cuota y pasa a exigir evidencia por flag.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
