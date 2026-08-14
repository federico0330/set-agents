# ADR-0047 — El estado no es el producto: `ai/state/` gitignorado, sembrado, historia archivada

- Estado: Accepted (2026-08-14). Feature 024-listo-para-terceros, paquete
  C1-estado-fuera-del-producto (AC-01, AC-02). No supersede nada.

## Contexto

`ai/state/` pesaba 2,3 MB y traía 23 features en cada clon del repositorio: un tercero que
clonara el harness heredaba el historial completo de trabajo de Federico, incluidas features
bloqueadas y en curso que no le pertenecen. Y `verify.sh` corría — y sigue corriendo — contra
ese mismo estado, así que su propio gate terminaba juzgando trabajo ajeno.

Medido antes de decidir nada: **once módulos** de `ai/scripts/` leen o escriben rutas bajo
`ai/state/` (`generate.py`, `check-canonical-paths.py`, `routing_cli.py`,
`claude_local_gate_guard.py`, `coord_policy.py`, `cost-report.py`,
`check-feature-state.py`, `project_identity.py`, `bootstrap_project.py`,
`feature-state.py` — y todo `feature_state_lib/` que importa —, `set_agents_app.py`). Ese
número es el que manda sobre el diseño: cualquier decisión que obligue a tocar los once es una
decisión cara y frágil.

## Decisión

### 1. El path se mantiene — `ai/state/` sigue siendo `ai/state/` en tiempo de ejecución

Ninguno de los once módulos cambia. La ruta que leen y escriben (`root / "ai" / "state"`, en
sus distintas formas) sigue existiendo, en el mismo lugar, con el mismo contrato. Lo que cambia
es de dónde sale su contenido y si Git lo seguía.

### 2. El historial se archiva, trackeado y sin lectores — `docs/historia/estado-2026-08/`

`git mv ai/state docs/historia/estado-2026-08` (nunca `cp` + `rm`: preserva el historial de
cada archivo — confirmado con `git status` mostrando los 29 pares como `renombrados`, no como
`nuevo archivo` + `borrado`). Es un archivo de lectura — nadie en el código lo lee ni lo
escribe — trackeado y legible como cualquier otro documento del repositorio.

### 3. `ai/state/` pasa a gitignorado y se siembra desde `ai/state.seed/`

`.gitignore` gana `/ai/state/` (ADR-0047). `ai/state.seed/` es el esqueleto trackeado de un
harness funcional y vacío — ninguna feature, decisión o entrada de narrativa de nadie —
copiado a `ai/state/` por `ai/scripts/seed-state.py` **únicamente cuando `ai/state/` está
ausente**. La guarda es "existe o no existe", nada más fino: nunca diffea, nunca mergea, nunca
completa selectivamente archivos faltantes dentro de un árbol que ya existe. Esa aspereza es
deliberada — cualquier cosa más fina es un segundo lugar donde la pregunta "de quién es este
dato" se puede responder mal. Sembrar dos veces es la misma llamada dos veces: la segunda
encuentra `ai/state/` presente y no toca un solo byte (pinneado por comparación de manifiesto
byte a byte, no sólo por el código de estado impreso).

### 4. `check-feature-state.py` cambia la pregunta, no se apaga

Antes: "¿hay algún spec entregado sin state file en **toda la historia**?" — en un clon nuevo,
eso son 23 specs contra un `ai/state/features/` recién sembrado y vacío, es decir, 23 falsos
positivos en el primer `verify.sh` que corre cualquier tercero.

Ahora: "¿hay algún spec entregado sin state file **desde mi baseline**?" `baseline_sha()`
ancla la pregunta en el commit más antiguo que agregó algo bajo `ai/state.seed/` — el mismo
commit para cualquier clon, nunca un valor por máquina. Todo lo anterior a ese commit ya está
contabilizado en `docs/historia/estado-2026-08/`, que este guardián no lee; todo lo posterior
se revisa exactamente igual que antes. El degradado ruidoso se conserva: un ancla que no se
puede encontrar (`baseline-unknown`) se anuncia igual que el caso preexistente de clon
superficial (`shallow-clone`) — nunca cae en silencio de vuelta al escaneo de toda la historia,
que resucitaría el mismo bug de falsos positivos.

## La trampa que este ADR existe para cerrar

El estado de Federico es su historial de trabajo real, corriendo en producción en su máquina
mientras este paquete se implementaba. `git mv` mueve — no copia — el contenido físico de
`ai/state/` a `docs/historia/estado-2026-08/`; sin un paso adicional, el `ai/state/` en tiempo
de ejecución de esa máquina habría quedado ausente hasta la próxima siembra, que lo habría
poblado con el esqueleto **vacío** — perdiendo, en la práctica, el trabajo real del dueño
detrás de un `git mv` técnicamente correcto.

La regla que lo evita: la siembra sólo puebla un `ai/state/` ausente, nunca pisa uno existente
(sección 3). Verificado en la implementación: inmediatamente después del `git mv`, `ai/state/`
se restauró con una copia exacta de `docs/historia/estado-2026-08/` (comparación
`diff -rq` limpia contra el backup tomado antes de mover nada), de modo que cuando
`ai/scripts/seed-state.py` corre después, encuentra `ai/state/` ya poblado y no hace nada —
la misma guarda que protege a un tercero protege, primero, al dueño.

## Alternativas rechazadas

- **Mover el path en código** (`ai/state` → otra ruta en los once módulos): rechazado — convierte
  un cambio de cero módulos en un cambio de once, cada uno una superficie nueva de romper algo
  que hoy funciona, sin ganar nada que gitignorar-y-sembrar no dé ya.
- **`cp` + `rm` en vez de `git mv`**: rechazado — pierde la vinculación de renombrado que Git
  arma automáticamente; `git log --follow` sobre cualquier archivo de
  `docs/historia/estado-2026-08/` deja de encontrar su historia previa bajo `ai/state/`.
- **Retirar `check-feature-state.py`** en vez de arreglarle la pregunta: rechazado — es
  exactamente la clase de "degradar a no-operación silenciosa" que el propio docstring del
  guardián nombra como el defecto que existe para evitar; un guardián que reporta violaciones
  que no lo son se termina deshabilitando, un guardián retirado no vuelve.
- **Sembrar con los datos reales del dueño en vez de un esqueleto vacío**: rechazado — un
  tercero que clona el repositorio no puede heredar features ajenas bajo ningún escenario; el
  esqueleto vacío es la única semilla que no reintroduce el defecto original.

## Consecuencias

- Un clon nuevo pesa 2,3 MB menos y no trae ninguna feature ajena.
- `ai/state.seed/ai/scripts/seed-state.py` son la única superficie nueva; los once módulos que
  leen `ai/state/` siguen exactamente como estaban.
- `docs/historia/estado-2026-08/` es de sólo lectura por convención (nada en el código la lee);
  un futuro mes de archivado repetiría el mismo patrón con su propio sufijo de fecha, no
  reabriría este directorio.
- El primer arranque interactivo (cuándo y cómo se invoca `seed-state.py` para un usuario nuevo,
  `ROUTING_UNCONFIGURED`) queda fuera de este paquete — es C3 de la misma feature.

## Evidencia

`docs/specs/024-listo-para-terceros/evidence/C1-implementer.md`.
