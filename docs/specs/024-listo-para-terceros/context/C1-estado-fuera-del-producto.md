# Context pack — C1-estado-fuera-del-producto

Spec: `docs/specs/024-listo-para-terceros/spec.md`, **AC-01, AC-02**. Primer paquete de 024, y el
más delicado de la feature: **mueve el estado del harness**.

## El defecto, medido hoy

`ai/state/` pesa **2,3 MB** y trae **23 features** en el clon. Un tercero que clone el repo hereda
el historial completo de Federico, incluidas sus features bloqueadas. Y `verify.sh` corre contra
ese estado, así que su gate juzga trabajo ajeno.

**Once módulos de `ai/scripts/` leen `ai/state`.** Ese número es el que manda sobre el diseño.

## La decisión que ya está tomada y baja el riesgo a casi cero

**El path se mantiene.** `ai/state/` sigue siendo `ai/state/` en tiempo de ejecución:

- El historial se mueve a `docs/historia/estado-2026-08/` — **trackeado, legible, leído por nadie**.
- `ai/state/` pasa a estar **gitignoreado** y se **siembra desde `ai/state.seed/`**.

Eso es lo que convierte un cambio de 11 módulos en un cambio de **cero**. Si te encontrás editando
un `Path("ai/state")` en código, parate: significa que te fuiste del diseño.

## TAREA

**AC-01** — `git mv ai/state → docs/historia/estado-2026-08/`, `ai/state/` gitignoreado, y siembra
desde `ai/state.seed/`.

La siembra tiene que dejar un harness **funcional y vacío**, no uno roto: lo mínimo que el arranque
necesita, sin ninguna feature de Federico. Y tiene que ser **idempotente** — sembrar dos veces no
puede duplicar ni pisar estado real.

**Ojo con lo que ya pasó en esta sesión**: el implementer de 022/P4 introdujo un bug de
no-idempotencia (orden de claves JSON entre la siembra en memoria y la relectura) que `verify.sh`
atrapó con `DRIFT_DETECTED`. La siembra es exactamente ese tipo de código. Corré `check-drift.sh`
además de los gates.

**AC-02** — `check-feature-state.py` **no se apaga, se le arregla la pregunta**: de *"¿hay algún
spec entregado sin state file en toda la historia?"* a *"¿desde mi baseline?"*, **conservando el
degradado ruidoso**.

Hoy pregunta sobre toda la historia (`:109-112` resuelve `docs/specs/<feature>/spec.md`), lo que en
un clon limpio significa: 23 specs contra cero state files. Sin este AC, el primer `verify.sh` de un
tercero es rojo.

## La trampa

**El estado de Federico es su historial de trabajo real.** Moverlo mal lo pierde.

- `git mv`, no `cp` + `rm`: preserva la historia de git.
- Después del movimiento, **verificá que las 23 features siguen legibles** en su nueva ubicación.
- Y que su máquina sigue funcionando: su `ai/state/` en runtime tiene que seguir teniendo lo suyo,
  no la semilla vacía. **La siembra sólo puebla un `ai/state/` ausente**, nunca pisa uno existente.

Esa última regla es la que separa "el producto se puede clonar" de "le borré el trabajo al dueño".

## Restricciones

- **ADR-0047** (`ls docs/adr/` para confirmar que está libre, indexalo en `docs/adr/README.md`): el
  estado no es el producto.
- **No cambies ningún path en código.** Si creés que hace falta, pará y reportalo.
- **No toques `models.toml`** ni las suscripciones: eso es C2.
- **No uses `git checkout`, `git restore` ni `git stash`.** Para morder y restaurar: `cp` y `cp`.
- No relajes, saltees ni borres tests.

## Validación

`python3 -m unittest discover -s tests` (**`pytest` NO está instalado**; base **1107 OK / 3 skips**)
· `./ai/scripts/verify.sh` → `VERIFY_PASS` · `./build.sh --check` → `GLOBAL_TREE_SYNC_OK` +
`BUILD_CHECK_PASS` · `./ai/scripts/check-drift.sh` · `git diff --check` limpio.

**Corré los comandos largos así:** `ai/scripts/heartbeat-run.py --interval 20 -- <comando>`
(ADR-0041). La suite tarda ~9 min.

## Evidencia

`docs/specs/024-listo-para-terceros/evidence/C1-implementer.md`, escrito **en el primer minuto**:
tabla AC → cambio (`archivo:línea`) → prueba; **la prueba de que las 23 features siguen legibles**
tras el movimiento; **la prueba de que la siembra no pisa un `ai/state/` existente**, que es lo que
protege el trabajo del dueño; la siembra corrida dos veces mostrando idempotencia; el nuevo
comportamiento de `check-feature-state.py` en un clon limpio; y los gates.

**Por cada test nuevo: neutralizá el cambio, confirmá el rojo, revertí, pegá la prueba.** En este
proyecto ya aparecieron **cinco** guardas que decían cubrir algo que no miraban. No escribas la
sexta.

**Cada bloque literal, o marcado como recortado.** Si no lo corriste, "sin verificar".

## Fuera de alcance

`models.toml` y el overlay del usuario (C2) · el primer arranque y `ROUTING_UNCONFIGURED` (C3) ·
`LICENSE` y la matriz de soporte (C4) · el aislamiento roto de los módulos de test (preexistente,
registrado) · features 025 y 026.
