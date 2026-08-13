# Context pack — P4-proveedores-del-usuario

Spec: `docs/specs/022-disponibilidad-real/spec.md`, **AC-11..AC-15**. Depende de **P3**, ya
aceptada. Es el paquete que responde el pedido literal de Federico: *"los agregados quiero poder
administrarlos desde `set-agents`, sin tener que modificar ningún JSON"*.

## Medición que corrige el diagnóstico del pedido. Leela primero.

Federico dijo: *"antes yo había agregado en el .json de opencode algunos modelos de ollama que
había probado en local y ya no existen"*.

**Medido hoy en su máquina: no los agregó él.** Su `~/.config/opencode/opencode.json` tiene
**exactamente un** provider, `ollama`, y su bloque es **byte-idéntico** al que el harness envía en
`Global/_shared/opencode.json:5-23`:

```
vivo : {"ollama": {"models": {"llama3.1:8b": ..., "qwen2.5-coder:7b": ..., "qwen2.5-coder:7b-instruct-q5_K_M": ...}}}
envia: {"ollama": {"models": {"llama3.1:8b": ..., "qwen2.5-coder:7b": ..., "qwen2.5-coder:7b-instruct-q5_K_M": ...}}}
IDENTICOS
```

Y el endpoint está **muerto**: `curl http://localhost:11434/v1/models` → `000`, sin respuesta.

Tres consecuencias para tu diseño:

1. **El caso real no es "quitar lo que el usuario agregó", es "quitar lo que el harness impuso".**
   `deep_merge` (`install.py:49-56`) sólo agrega y el overlay gana: si el usuario borra el bloque,
   el próximo install se lo repone. Hoy la única salida es editar el repo. Eso es AC-13 y es el
   corazón del paquete.
2. **La siembra migratoria de AC-15 tiene que distinguir**, no aplanar. Etiquetar este bloque como
   `origin=user` sería mentir sobre su procedencia — y encima le impediría al harness dejar de
   enviarlo. Es `harness-legacy`. La comparación contra el bloque enviado es **decidible hoy**,
   porque son idénticos; escribí la comparación, no una heurística por nombre.
3. **Hoy no hay ningún provider propio del usuario en esa máquina.** Así que el test de AC-14 —"un
   provider agregado a mano sobrevive intacto a un install que poda otro"— **no** lo podés validar
   contra el estado real: construilo con un fixture. Decilo así en la evidencia en vez de sugerir
   que lo verificaste en vivo.

## Los mecanismos, medidos

| Qué | Dónde | Nota |
|---|---|---|
| Bloque hardcodeado | `Global/_shared/opencode.json:5-23` | lo que hay que dejar de enviar así |
| Merge que sólo agrega | `install.py:49-56` (`deep_merge`) | el overlay gana; por eso quitar no funciona |
| Merge de opencode.json | `install.py:117` (`merged_json`) | |
| Manifiesto | `install.py:46`, `MANIFEST = STATE_DIR/"managed-files.json"` | **a nivel de archivo** |
| `opencode.json` en el manifiesto | `Global/opencode/managed-files.txt:93` | figura, pero se gestiona por `merged_json` |
| Precedente de archivo de estado | `set_agents_app.py:106` `MODEL_PREFERENCE_PATH`, escritura atómica en `:382,402,443,461` | copiá esta forma |

**AC-14 es el riesgo del paquete.** La poda pasa de archivos a **subárboles JSON**
(`opencode.json#/provider/ollama`). Una poda que se equivoque **le borra al usuario una clave que
él puso**. Regla dura: sólo se poda un id que esté **en el manifiesto**, jamás una clave que el
harness no escribió. El test obligatorio es el de un provider hecho a mano que sobrevive intacto a
un install que poda otro.

## Alcance del paquete

`ai/scripts/set_agents_app.py` (comandos `--provider-*`) · `ai/scripts/install.py` (render + poda de
subárboles) · `Global/_shared/opencode.json` (dejar de hardcodear) · `tests/` · `docs/adr/`

**Después de tocar `Global/_shared/` corré `./build.sh` y después `./build.sh --check`**, que ahora
sí compara de verdad contra los cuatro árboles (ADR-0041). Si te da `GLOBAL_TREE_DRIFT`, te faltó
el `build.sh`.

**Si aparece un archivo fuera de esa lista, pará y reportalo.** `check-owned-paths.py:40-42` usa
`git diff --name-only` y **no ve archivos nuevos** — la disciplina la ponés vos.

## AC-12 — qué NO es este paquete

`--provider-list|add|remove|verify`, sin tocar JSON a mano. **El wizard de `setup_models.py` no se
toca**: remapea modelos de `models.toml`, es otra cosa. Y `--provider-verify` de AC-18 (el `GET
{baseURL}/models`, timeout 2 s, `alive|dead|unreachable`) es **P5**, no acá — acá `verify` es sólo
la superficie declarada, no la medición de liveness.

## Restricciones

- **Extendé `docs/adr/0042`** para los tres orígenes (`harness`, `discovered`, `user`); la spec le
  asigna a 0042 "registro + techo tri-estado + tres orígenes". No crees un ADR nuevo.
- **A nadie le desaparece nada.** El registro declara qué hay y de dónde vino; **nunca borra** por
  su cuenta. Quitar es una acción explícita del usuario.
- **Sin refactors oportunistas.** No toques el sort key, ni `route()`, ni el techo tri-estado.
- **No uses `git checkout`, `git restore` ni `git stash`.** Para morder y restaurar: `cp` y `cp`.
- **No toques el `~/.config/opencode/opencode.json` real del usuario.** Está durmiendo y lo
  necesita mañana. Todo con fixtures y `HOME` de prueba.

## Validación

`python3 -m unittest discover -s tests` (**`pytest` NO está instalado**; base **1006 OK / 3 skips**)
· `./ai/scripts/verify.sh` → `VERIFY_PASS` · `./build.sh` y `./build.sh --check` →
`GLOBAL_TREE_SYNC_OK` + `BUILD_CHECK_PASS` · `git diff --check` limpio.

**Corré los comandos largos exactamente así:**

```
ai/scripts/heartbeat-run.py --interval 20 -- python3 -m unittest discover -s tests
```

No los pipees a `tail`: sin `-f` no emite un byte hasta EOF, la suite tarda ~10 minutos y el
watchdog te mata a los 600 s (ADR-0041). Es el comando, no una opción.

## Evidencia

`docs/specs/022-disponibilidad-real/evidence/P4-implementer.md`, escrito **en el primer minuto**:
tabla AC → cambio (`archivo:línea`) → prueba; **la prueba de que quitar funciona de verdad** —un
install posterior no repone lo quitado, medido, no argumentado—; el test del provider hecho a mano
que sobrevive a una poda; la siembra migratoria distinguiendo `harness-legacy` de `user`; y los
gates.

**Por cada test nuevo: neutralizá el cambio, confirmá el rojo, revertí, pegá la prueba.** En P1 de
esta feature, dos de tres guardas pasaban en **verde** con la fuente rota. Mordé todo, en las dos
direcciones.

**Cada bloque literal, o marcado como recortado.** Si no lo corriste, "sin verificar".

## Checkpoint

Si te acercás al límite de ejecución, escribí progreso parcial **y los próximos pasos exactos** en
la evidencia antes de parar.

## Fuera de alcance

`--provider-verify` como medición de liveness y `--prune-dead` (P5) · altas y bajas automáticas
(P5) · el sort key · agregar Copilot · el wizard de `setup_models.py` · arreglar
`check-owned-paths.py` · features 023-025.
