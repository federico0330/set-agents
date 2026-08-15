# Context pack — D2-trabajo-visible

Spec: `docs/specs/025-consola-minima-y-flexible/spec.md`, **AC-04, AC-05**. Depende de D1.

## Estado medido hoy

**No hay spinner.** Medido: `grep -rniE "spinner|animat" ai/scripts/*.py` → **0 resultados**. `tui.py`
(830 líneas) tiene picker, raw mode, alternate screen, bracketed paste, viewport clamp — y nada de
progreso. La palabra "progress" en `tui.py` aparece sólo en `decode_keys` (`tui.py:273`, secuencia
incompleta) y en `run_picker` (`tui.py:799`, "making progress" en un loop). **Arrancás de cero.**

Lo único que hoy le dice al usuario que algo pasa es una línea estática:
`print(dim("· chequeando updates…"))` (`set_agents_app.py:3545`), impresa antes de
`launch_update_check()`, que corre `fetch(timeout=6)` (`set_agents_app.py:1262`).

### Lo que tarda más de ~300 ms (medido o con timeout declarado)

| Operación | Evidencia | Orden |
|---|---|---|
| Arranque en frío del CLI | medido: `--version` **145 ms**, `--help` **147 ms** | bajo el umbral |
| Probes de routing | `probe_inventory(timeout=20.0)` `routing_core/catalog.py:860`; 4 sitios de `subprocess.run` con ese timeout: `catalog.py:561,729,1124,1165` | segundos |
| `--route-doctor` | `route_doctor(timeout=20.0)` `catalog.py:1136`, llamado en `set_agents_app.py:562` | segundos |
| `--doctor-all` | `probe_listed_and_usable` `catalog.py:1238`, invocado en `set_agents_app.py:932` | segundos |
| Estado de auth por CLI | `AUTH_STATE_TIMEOUT_SECONDS = 15` `set_agents_app.py:1116`, usado en 1124/1133 | segundos |
| `--version` de cada CLI | `timeout=15` `set_agents_app.py:1147` | segundos |
| `git fetch` al abrir menú | `fetch(timeout=6)` `set_agents_app.py:1080,1262` | segundos |
| `git pull` del update | `timeout=180` `set_agents_app.py:1242` | minutos |
| `install.py --preview` | dump de diffs; el propio código lo describe como **~565 KB / 96 archivos** en una instalación desde cero (`install.py:248`) | segundos |
| Liveness de providers | `_provider_liveness` `set_agents_app.py:2492`, `urlopen(timeout=…)` 2509 | segundos |

Los tiempos de `--version`/`--help` los corrí; el resto son **timeouts declarados en el código, no
latencias medidas** — marcalo así si lo citás. Medí los reales antes de elegir el umbral.

## La trampa

**Hay consumidores máquina de stdout, y el spinner no puede vivir ahí.**

1. `_routing_output` (`set_agents_app.py:498-509`) imprime el **JSON en `stdout`**
   (`print(json.dumps(payload, sort_keys=True))`, línea 505) y el **texto humano en `stderr`**
   (509-511). Un spinner en stdout corrompe el contrato de `--json` byte a byte, que es
   exactamente lo que D1 tiene prohibido romper.
2. `check-drift.sh:45` parsea stdout de `install.py --preview` con
   `sed -n 's/^MANAGED_DIFF_FILES=//p'`. Un spinner con `\r` que caiga sobre esa línea la rompe.
3. **Los spawns fuerzan el entorno degradado**: `dict(os.environ, CI="1", NO_COLOR="1", TERM="dumb")`
   en `opencode_spawn.py:202`, `codex_spawn.py:222`, `set_agents_spawn.py:115` y
   `routing_core/catalog.py:557,757,1120,1161`. Todo lo que el harness invoca a sí mismo corre así.

Y la trampa fina: `use_color()` (`set_agents_app.py:943`) pregunta por **`sys.stdout.isatty()`**.
Reusarla para gatear el spinner es preguntarle al stream equivocado — el spinner va a stderr, y
`set-agents > out.json` tiene stdout piped con stderr todavía TTY. Necesitás un predicado propio
sobre el stream donde vas a escribir. `routing_human` (`set_agents_app.py:3743`) tiene el mismo
sesgo y por la misma razón no es reusable tal cual.

`tui._is_tty()` (`tui.py:397-403`) ya resuelve el "degradá en vez de explotar" para streams que no
saben responder: **reusalo, no lo reescribas**.

## La mordida exigida

Nueve guardas falsas-verdes en este repo. Tres tests, cada uno con su rojo demostrado:

1. **stdout intacto**: con el spinner activo, `--route-doctor --json` produce **exactamente** los
   mismos bytes en stdout que hoy. Rojo: escribí el spinner a stdout a propósito, confirmá que el
   test falla, revertí, pegá ambas salidas.
2. **Degradación real**: sin TTY, con `NO_COLOR=1` y con `TERM=dumb`, **cero secuencias ANSI y cero
   `\r`** en la salida capturada. Rojo: neutralizá la rama de degradación, confirmá el fallo. Cubrí
   los tres gates por separado — un test que sólo prueba "no TTY" no prueba `NO_COLOR`.
3. **Nunca único indicador (AC-05)**: la operación deja una línea de estado **persistente** al
   terminar, presente también en modo degradado. Rojo: borrá esa línea final y confirmá el fallo.
   Sin este test, AC-05 es decorativo.

AC-05 también exige **no bloquear input**: si el spinner corre en un hilo, tiene que apagarse antes
de cualquier prompt. `tui.suspend_terminal()` (`tui.py:536`) ya existe para exactamente ese handoff
y `set_agents_app.py:1255` lo usa antes de `subprocess.run(install)`. Es el punto de integración.

## Restricciones

- **ADR reservado: 0053** (`ls docs/adr/` para confirmar; 0050 está reservado sin escribir por D1,
  0052 lo tomó 027/P4). Indexalo en `docs/adr/README.md`.
- `owned_paths`: `ai/scripts/tui.py`, `ai/scripts/set_agents_app.py`, `tests`. **No toques
  `routing_core/`, `install.py` ni los `*_spawn.py`** — instrumentá desde el llamador.
- **No cambiés el formato de `--json`** (contrato de D1, AC-03).
- No uses `git checkout`/`restore`/`stash`. Para morder y restaurar: `cp` y `cp`.
- No toques nada bajo `~`. Nunca corras `./build.sh --install`.
- Sin dependencias nuevas: **stdlib solamente** (`rich`/`tqdm` no están y no entran).
- Windows: `tui.py` importa `termios` bajo `try/except ImportError` (`tui.py:38-41`) porque el job
  `windows-bootstrap` corre la suite entera. Todo lo que agregues respeta esa guarda.

## Validación

`python3 -m unittest discover -s tests` (**`pytest` NO está instalado**) · `./ai/scripts/verify.sh` →
`VERIFY_PASS` · `./build.sh --check` → `GLOBAL_TREE_SYNC_OK` + `BUILD_CHECK_PASS` · `git diff --check`.

Manual, pegado en la evidencia: `set-agents --route-doctor` en TTY, `| cat`, y con `NO_COLOR=1`.

**Comandos largos: `ai/scripts/heartbeat-run.py --interval 20 -- <comando>`** (ADR-0041).

## Evidencia

`docs/specs/025-consola-minima-y-flexible/evidence/D2-implementer.md`, escrito en el primer minuto:
tabla AC → cambio (`archivo:línea`) → prueba; **la tabla de latencias reales medidas** que justifica
qué operaciones se instrumentan y cuáles no; las tres salidas (TTY / pipe / `NO_COLOR`) pegadas
literales; y las tres pruebas de mordida con su rojo. Cada bloque literal o marcado como recortado.

## Fuera de alcance

Menú, flags ocultas y `--json` humano (D1) · posturas y toggles (D3) · instalación por CLI (D4) ·
vault (D5) · el ruteo y el sort key · rediseñar el picker.
