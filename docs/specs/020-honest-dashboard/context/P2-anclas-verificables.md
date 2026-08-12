# Context pack — P2-anclas-verificables (ADR-0040)

Spec: `docs/specs/020-honest-dashboard/spec.md`, **AC-06..AC-11**. P1 ya está aceptado.

## El defecto, reproducible

`docs/modules/consola.md` dice que `set_agents_app.py:2510` es `main()`. El `main()` real
está en **`:3252`** — corrido **+742 líneas**. También hay deriva en las referencias a
`generate.py` (+9) y en `feature-state.py:788` (+4).

Causa: P3 de la feature 019 sembró esos puntos de entrada y P5 agregó ~880 líneas a los
mismos archivos. **Ningún review de paquete podía verlo**: cada uno miró su propio diff.
Solo apareció en integración, cuando alguien corrió a mano el chequeo que `/explicar`
promete. Registrado en `ai/state/decisions-log.jsonl`, slug
`anclas-file-line-de-docs-modules-derivan-sin-red`.

Es la materialización del riesgo que se aceptó en ADR-0036 al aprobar la desviación del
schema de AC-17: tres secciones derivadas por el motor, cinco sembradas a mano, y como
único mitigante que alguien corra `/explicar`. Este paquete es la red que faltaba.

## Los dos bloqueantes que el spec-challenge ya resolvió — no los re-descubras

### 1. Resolución del nombre de archivo (SC-01)
La mayoría de las anclas usan **solo el basename** (`generate.py:55`, `render_notes.py:51`),
no la ruta desde la raíz. Y `feature_state_lib/*.py` está **duplicado byte a byte en cinco
árboles** (`ai/scripts/`, `PROYECTO/ai/scripts/`, y los tres `Global/*/hooks/`). Una
búsqueda global sería no determinística.

**Regla obligatoria**: un ancla sin ruta completa se resuelve por basename **solo dentro de
los `paths` del módulo que se está chequeando** (`docs/modules/modules.toml`, el mismo
mecanismo que usa `render_modules.matching_modules`). Cero matches, o más de uno, dentro de
esos `paths` **es en sí mismo un ancla rota reportable** — no un caso a ignorar.

### 2. Las dos formas de ancla (SC-02)
En los docs de hoy hay **~20 de la forma completa** (`render_notes.py:51`) y **~19 de la
forma abreviada** (`` `:190` `` suelta, referida al archivo nombrado antes en la misma
oración). Casi 1:1. Cubrir solo la obvia daría `rc=0` verificando la mitad — **una falsa
seguridad, que es una mentira más sutil que la que este paquete vino a eliminar.**

La forma abreviada se resuelve contra **el último archivo nombrado en el mismo ítem de lista
o párrafo**. Una `` `:N` `` que no se pueda resolver así se reporta como **ancla no
resoluble**, nunca se saltea en silencio.

Falsos positivos reales a testear: `localhost:8080`, `12:30`, `http://x:80`, un rango
`10-20`.

## AC-08 — verificación semántica, acotada a propósito

Se verifica el símbolo **solo** cuando viene en backticks **inmediatamente adyacentes al
ancla, en la misma línea** — el caso de `consola.md:26`, que es el defecto insignia. Es una
**comparación de texto**: el identificador aparece o no en la línea destino, con una ventana
chica.

**Explícitamente fuera**: rangos, comodines (`cmd_route_*`), y símbolos separados del ancla
por prosa. Esos reciben chequeo de rango y nada más.

**Nada de parsear Python.** Si el criterio no se puede expresar como comparación de texto
determinista, recortá el AC a chequeo de rango y dejá constancia. El spec-challenger marcó
este AC como el candidato a "proyecto disfrazado": es el punto donde más fácil te pasás del
mandato acotado.

## AC-09 — el contrato never-raises

`sync-notes` corre el verificador y **avisa por stderr sin fallar la mutación**. Mismo
contrato que `render_notes.py:281-285` con `RENDER_FAILURE_LOG`. Escribí el test que lo
prueba: un verificador que lanza excepción y una mutación que igual completa.

`check-anchors` **no es gate bloqueante de ninguna fase** — está en los no-goals y es
deliberado. Avisa; no traba.

## AC-10 — arreglar las anclas de hoy

Corregí las rotas y probá `rc=0` sobre los cinco módulos. **Ojo**: corregir los números a
mano los deja corridos otra vez con el próximo paquete que toque esos archivos — por eso el
verificador es el entregable y la corrección es su consecuencia, no al revés.

## Restricciones

- **`./build.sh` obligatorio** tras tocar `feature_state_lib/`: copias byte-idénticas en 5
  árboles, y un test pinea la igualdad. Después `./build.sh --check`. **Verificá los 5 con
  `md5sum` al final**: en P1 hubo un episodio donde tres espejos perdieron un hunk.
- **No toques el schema de `docs/modules/`** ni la partición máquina/humano de ADR-0036. Las
  cinco secciones sembradas siguen siendo humanas.
- No conviertas nada en gate bloqueante.
- Sin refactors oportunistas.

## Validación local

`python3 -m unittest discover -s tests` (**`pytest` NO está instalado**; base **943 OK**, el
conteo sube y nunca baja; ~9 min, usá `-p "<archivo>" -k <nombre>` mientras trabajás) ·
`./ai/scripts/verify.sh` → `VERIFY_PASS` · `./build.sh` y después `./build.sh --check` sin
drift · `git diff --check` limpio.

Prueba viva que va como evidencia:

```bash
python3 ai/scripts/feature-state.py check-anchors            # antes: rotas; después: rc=0
python3 ai/scripts/feature-state.py check-anchors --module consola
python3 ai/scripts/feature-state.py sync-notes               # no debe romperse nunca
```

## Advertencia de proceso (leela, no es genérica)

La feature 019 acumuló **cuatro afirmaciones de verificación fabricadas**, y el último
review agregó un matiz: hubo transcripciones **anotadas** —con cabeceras que el comando
pegado nunca imprime, o salidas recortadas— que parecían literales sin serlo. **Cada bloque
que pegues es literal, o está marcado como recortado.** Si no lo corriste, "sin verificar".

Y apareció **un test decorativo** en tres de los cinco paquetes de 019 y en P1 de esta
feature. El de P1 decía verificar un tope de menciones y nunca contaba ninguna. Por cada
test nuevo: neutralizá el cambio, confirmá el rojo, revertí, y pegá esa prueba.

**No uses `git checkout`, `git restore` ni `git stash`** sobre archivos del repo: en el
review de P1 un `git checkout --` revirtió el hunk del paquete en tres árboles. Si necesitás
mutar para una mordida, copiá con `cp` y restaurá con `cp`.

## Evidencia esperada

`docs/specs/020-honest-dashboard/evidence/P2-implementer.md`: tabla AC → cambio
(`archivo:línea`) → prueba; la salida de `check-anchors` **antes** (con las rotas de hoy) y
**después** (`rc=0`); los falsos positivos probados en ambas direcciones; el conteo de
anclas detectadas por forma (para probar que cubrís las dos); la prueba de mordida por test;
y los gates pegados con el `md5sum` de los 5 espejos.

## Checkpoint

Murieron tres instancias por stall en la sesión anterior. Escribí la evidencia en el primer
minuto y guardá a disco a medida que avanzás.

## Fuera de alcance

Todo P1 (ya aceptado) · el schema de `docs/modules/` y la partición de ADR-0036 · convertir
`check-anchors` en gate · resolver los blockers de `002` y `011` · todo lo de 019.
