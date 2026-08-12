# Context pack — P3-cognitive-module-docs (ADR-0036)

Spec: `docs/specs/019-harness-evolution/spec.md`, AC-17..AC-24. Este es el paquete más grande de la
feature y el único que no toca routing: es infraestructura de estado y documentación.

## El problema que resolvés

El harness registra con obsesión el estado del **pipeline** (qué paquete, qué fase, qué hallazgo) y no
registra nada del **software construido**. La única documentación global de lo que se construyó es
`docs/architecture/overview.md`, mantenida a mano por el rol `architect` en fase de diseño
(`Global/_canonical/agents/architect.md:41-47`), sin ningún gate — y está stale **en este mismo repo**:
quedó congelada en "trusted routing P1R" mientras el harness llegó a ADR-0035.

Objetivo concreto y medible: que Federico pueda abrir `docs/modules/<slug>.md` y en **90 segundos**
recuperar qué hace el módulo, por dónde fluye, qué invariantes tiene y qué cambió último.

## Infraestructura que YA existe y tenés que reutilizar (no escribas otra)

`ai/scripts/feature_state_lib/render_notes.py` ya resolvió todos los problemas difíciles:

- `merge_note(existing, title, body)` (`:52`) — regenera **solo** el bloque máquina entre
  `<!-- notas:auto -->` y su cierre, preservando todo lo que el humano escribió fuera. Si el archivo
  no existe, crea el esqueleto con una sección `## Notas propias`.
- `write_note(path, title, body)` (`:68`) — escritura **atómica** vía `NamedTemporaryFile` + `os.replace`,
  y devuelve `False` sin tocar el disco cuando el contenido no cambió (idempotencia real).
- `_short(text, limit)` (`:79`) — colapsa whitespace, **neutraliza `<!--` y `-->`** y trunca. Todo
  campo escrito por un agente pasa por acá: sin eso, un texto malicioso o accidental mueve la frontera
  máquina/humano de forma permanente. **Ningún campo que venga del estado se escribe sin pasar por
  `_short`.**
- `notes_root(state_file)` (`:36`) — el marcador de "proyecto gestionado por el harness" es que exista
  `ai/state/`, nunca "¿ya existe el directorio de docs?". Copiá ese criterio: un repo sin
  `docs/modules/` **no falla**, simplemente no renderiza.
- `_log_render_failure(out_dir, context, exc)` (`:285`) + `RENDER_FAILURE_LOG` (`:281`) — el contrato
  never-raises: un render roto **nunca** puede romper la mutación de estado que lo disparó; el error se
  anota en `ai/state/render-failures.log` (por proyecto, con rotación a 200 KB).

## Archivos y qué hacer

### AC-17/AC-19 — `ai/scripts/feature_state_lib/render_modules.py` (NUEVO)

Motor de render, mismo contrato que `render_notes`: **never-raises, atómico, con
`render-failures.log`**. Importá `merge_note`/`write_note`/`_short` de `render_notes`, no los
dupliques.

Schema del doc, **en español**, dentro del bloque máquina:

```
# <Nombre>
## Responsabilidad        (1-2 líneas)
## Puntos de entrada
## Componentes
## Flujo                  (cadena corta: HTTP → Controller → Service → Repo)
## Posee / Depende de
## Invariantes
## Decisiones             (wikilinks [[...]] a ADRs y decisiones)
## Últimos cambios estructurales   (lista capada ~10: <fecha> <feature/pkg> — <cambio>)
```

Debajo del bloque, la zona humana que `merge_note` preserva.

### AC-18 — `docs/modules/modules.toml` (NUEVO)

`[module.<slug>]` con `nombre`, `responsabilidad`, `paths = [globs]`. Es la fuente de la detección:
se matchean los `owned_paths` del paquete y los `changed_files` de los repairs/receipt contra esos
globs. Validación fail-closed como el resto del repo: slug con forma cerrada, `paths` lista no vacía
de strings, clave desconocida = error explícito.

### AC-20 — comandos en `ai/scripts/feature-state.py`

- `record-module-impact <fid> --package-id P --module <slug> --cambio "<qué cambió estructuralmente>"
  --modelo-mental "<qué tenés que saber ahora>"` → hace append a `package["module_impacts"]`,
  regenera `docs/modules/<slug>.md` e **imprime el bloque Impacto humano** listo para que el
  orquestador lo pegue en la narración (P4 define su formato exacto: `Impacto humano:` / `Módulo:` /
  `Cambio de modelo mental:` / `Tenés que saber:`).
- `module-impact-detect <fid> --package-id P` → lista módulos candidatos, **sin mutar**.
- `--module-impact-waived --reason "<motivo>"` → la válvula. Un quick-fix trivial no paga un doc
  entero; el waiver es barato, explícito y queda registrado.

Seguí la forma argparse/`mutate` de los comandos de `cli_lifecycle.py`. Ojo con dónde ponés el
código: `feature-state.py` ya está partido en `feature_state_lib/`; elegí el módulo que corresponda y
respetá el grafo de imports (mirá el docstring de `cli_integration.py:1-13`, que documenta un ciclo
que evitaron a propósito).

### AC-19 — enganche del render

`ai/scripts/feature-state.py:160-170`, dentro de `mutate()`: hoy corre `render_status`,
`render_bitacora` y `render_notes` en cada mutación que cambia algo. Sumá `render_modules` ahí y a
`sync-notes`. **Solo módulos con impacts** — no generes 30 archivos vacíos. Un repo sin
`docs/modules/` no falla.

### AC-21 — el gate

- `ai/scripts/feature_state_lib/transitions.py:108-114`: entrar a `INTEGRATION` exige que **cada
  paquete accepted** tenga `module_impacts` no vacío **o** un waiver registrado.
- `model.py:449-472` `done_ready`: el mismo check como error nuevo.
- **Importante para el ADR**: ADR-0024 decidió deliberadamente **no** poner precondiciones en la
  entrada a INTEGRATION. Este paquete agrega una. No lo escondas: explicá en ADR-0036 por qué esta
  precondición es distinta (es sobre documentación derivable del propio estado, con waiver barato, no
  sobre una verificación externa que pueda quedar trabada) y registrá la relación con ADR-0024
  explícitamente.

### AC-22 — digest

`cli_reporting.cmd_digest` (`:152-244`) suma la sección `## Qué cambió en el software`, derivada de
los `module_impacts` de la ventana. Mirá cómo las secciones existentes ("Qué quedó listo", "Qué se
está haciendo", "Qué falta", "Decisiones nuevas") arman sus líneas y seguí ese estilo.

### AC-24 — seed real de ESTE repo

No es un ejemplo de juguete: creá `modules.toml` y los docs iniciales para los módulos reales, al
menos routing, feature-state/estado, generación de árboles, app de consola, y narración/notas. Y
**regenerá `docs/architecture/overview.md`**, que está stale — esa regeneración es parte de la
evidencia de que el mecanismo sirve.

Escribí los docs con contenido **verdadero y verificado** (`file:line`), no plausible. Si no podés
verificar algo de un módulo, escribí menos, no inventes.

## Read-only (NO editar)

Todo `ai/scripts/routing_core/`, `models.toml`, `ai/catalogs/`, `ai/scripts/set_agents_app.py`,
`ai/scripts/setup_models.py` (P1/P2, ya aceptados). `Global/_canonical/agents/*.md` y
`Global/_canonical/commands|skills/` son **de P4**: no los toques, ni siquiera `integrator.md` o
`architect.md`, aunque el ADR-0036 los mencione.

## Restricciones

- **ADR-0036 primero, después test, después código.** Re-verificá con `ls docs/adr/` que `0036` esté
  libre e indexalo en `docs/adr/README.md`.
- **`./build.sh` obligatorio** tras tocar `feature_state_lib/`: hay copias byte-idénticas en los 4
  árboles de `Global/` y en `PROYECTO/`. Después `./build.sh --check` para confirmar cero drift. Un
  test de la suite pinea esa byte-igualdad: si lo ves fallar, te faltó el `build.sh`.
- El render **nunca** puede romper una mutación de estado. Escribí el test que lo prueba: un
  `render_modules` que lanza excepción y una mutación que igual completa y deja la línea en
  `render-failures.log`.
- El merge tiene que ser **idempotente** y preservar la zona humana: test round-trip que escribe,
  edita la zona humana a mano, re-renderiza y verifica que la edición sobrevive y que el bloque
  máquina quedó igual.
- El gate no puede volverse fricción: el waiver es la válvula y tiene que ser barato. Test de ambos
  caminos.
- Nada de refactors oportunistas en `feature_state_lib/`.

## Validación local

`python3 -m unittest discover -s tests` (**`pytest` no está instalado**; hoy 831 tests OK con 3 skips
preexistentes — el conteo sube, nunca baja) · `./ai/scripts/verify.sh` → `VERIFY_PASS` ·
`./build.sh` y después `./build.sh --check` sin drift · `git diff --check` limpio.

Nota: correr `python3 -m unittest tests.test_harness` **aislado** produce ~72 errores
`KeyError: 'set_agents_app'` que son un problema **preexistente** de aislamiento de import, no una
regresión tuya. La forma válida de correr todo es `discover` o `verify.sh`.

Pruebas vivas que van como evidencia:

```bash
python3 ai/scripts/feature-state.py module-impact-detect 019-harness-evolution --package-id P3-cognitive-module-docs
python3 ai/scripts/feature-state.py record-module-impact 019-harness-evolution --package-id P3-cognitive-module-docs --module <slug> --cambio "..." --modelo-mental "..."
python3 ai/scripts/feature-state.py sync-notes
python3 ai/scripts/feature-state.py digest
```

## Evidencia esperada

`docs/specs/019-harness-evolution/evidence/P3-implementer.md`: tabla AC → cambio (`archivo:línea`) →
prueba; el schema del doc renderizado de verdad (pegá uno completo); la prueba de idempotencia del
merge; la prueba de que el render nunca rompe una mutación; el gate bloqueando y el waiver
liberando; la sección nueva del digest; y la lista de módulos seedeados con la justificación de cada
uno. Lo que no puedas verificar, marcalo "sin verificar".

## Checkpoint

Este paquete es grande. Si te acercás al límite de ejecución, **escribí primero** el progreso parcial
y los próximos pasos exactos en el archivo de evidencia, y recién ahí pará: una instancia fresca
tiene que poder retomar barato.

## Fuera de alcance

Narración, `integrator.md`, `architect.md`, question policy y `/explicar` → **P4**. Tools discovery →
P5. Routing, billing y consola → P1/P2, ya aceptados. No agregues un gate de auditoría externa
(codex-audit): DEC-3 lo descarta explícitamente.
