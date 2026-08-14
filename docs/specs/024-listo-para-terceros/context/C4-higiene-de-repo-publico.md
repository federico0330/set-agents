# Context pack — C4-higiene-de-repo-publico

Spec: `docs/specs/024-listo-para-terceros/spec.md`, **AC-09..AC-12**. Último paquete de 024.
Depende de **C3**, ya aceptada.

## Estado medido

| Archivo | Estado |
|---|---|
| `LICENSE` | **ausente** |
| `CONTRIBUTING.md` | **ausente** |
| `CHANGELOG.md` | **ausente** |
| `SECURITY.md` | **ausente** |
| `HANDOFF-PASO9.md` | **en la raíz** |

Y `origin/main` está **hardcodeado** en `set_agents_app.py:1145`, `:1194` y `:1206`
(`rev_count("HEAD..origin/main")`). El remoto real es
`https://github.com/federico0330/set-agents.git`: **un fork se rompe**, porque su `origin/main` no
es el upstream.

## AC-09 — la licencia ya está decidida por evidencia, no la elijas vos

**MIT.** No es una opinión: las skills canónicas del propio repo ya declaran `license: MIT` en su
frontmatter (`Global/_canonical/skills/aesthetic-frontend/SKILL.md:4`, `error-handling-http`,
`performance-scalability`, y más). El `LICENSE` de la raíz **formaliza lo que el repo ya afirma**.

Titular del copyright: el dueño del repo. `HANDOFF-PASO9.md` sale de la raíz a `docs/`.

## AC-11 — la matriz de soporte se **mide**, no se asume

Es el AC con más valor y el más fácil de arruinar escribiendo promesas. Lo ya medido en esta
sesión y en las anteriores, que va con su fecha:

- **opencode**: 47 agentes instalados; es el único de primera clase.
- **codex**: **cero comandos**.
- **pi**: **cero hooks**, y su lane de dispatch corre con `--no-skills`.
- **En opencode, todos los roles del harness son `subagent` y sólo `orchestrator` es `primary`**, así
  que `opencode run --agent <rol>` **no despacha el rol**: cae al agente por defecto con un warning.
  Medido el 2026-08-13 al intentar despachar un `package-reviewer`.

**Lo que no puedas medir, no lo escribas.** Una matriz con una fila optimista es peor que una fila
faltante, porque alguien la va a creer.

## AC-12 — el update re-apuntable

`rev_count("HEAD..origin/main")` en los tres sitios. Un fork tiene su propio `origin`, así que el
"estás N commits atrás" mide contra el lugar equivocado. Hace falta poder apuntar el upstream a otro
lado, con el default actual como fallback.

## AC-10 — ejemplos sin el nombre del cliente real

Un `grep` obvio no encontró nada. **Eso no prueba que no esté**: buscá nombres propios, dominios y
rutas específicas en `docs/`, `README`, ejemplos y notas. Si no encontrás nada, **decilo así** —
"buscado, no encontrado" es un resultado; "no hay" sin buscar es una promesa.

## Restricciones

- **No inventes contenido de licencia**: MIT tiene texto canónico, usalo tal cual con el año y el
  titular.
- **No prometas soporte que no medís.**
- **No uses `git checkout`, `git restore` ni `git stash`.** Para morder y restaurar: `cp` y `cp`.
- **No toques nada bajo `~`.**
- Mover `HANDOFF-PASO9.md` con `git mv`, no `cp` + `rm`.
- `tests/test_harness.py` assertea rutas y frases por grep: `grep -n` antes de mover el archivo.

## Validación

`python3 -m unittest discover -s tests` (**`pytest` NO está instalado**; base **1116 OK / 3 skips**)
· `./ai/scripts/verify.sh` → `VERIFY_PASS` · `./build.sh --check` → `GLOBAL_TREE_SYNC_OK` +
`BUILD_CHECK_PASS` · `git diff --check` limpio.

**Corré los comandos largos así:** `ai/scripts/heartbeat-run.py --interval 20 -- <comando>`
(ADR-0041).

## Evidencia

`docs/specs/024-listo-para-terceros/evidence/C4-implementer.md`, escrito **en el primer minuto**:
tabla AC → cambio (`archivo:línea`) → prueba; **la matriz de soporte con la medición que respalda
cada fila y su fecha**, y lo que quedó sin medir declarado como tal; la prueba de que el update
apunta a otro upstream y sigue funcionando con el default; qué buscaste para AC-10 y qué
encontraste; y los gates.

**Por cada test nuevo: neutralizá el cambio, confirmá el rojo, revertí, pegá la prueba.** Ya van
cinco guardas huecas en este proyecto. No escribas la sexta.

**Cada bloque literal, o marcado como recortado.** Si no lo corriste, "sin verificar".

## Fuera de alcance

El sort key · `ai/state` (C1) · `models.toml` (C2) · el primer arranque (C3) · los defectos latentes
registrados (`check-owned-paths.py`, aislamiento de tests, gate de pi, tests que escriben en
`STATE_DIR`) · features 025 y 026.
