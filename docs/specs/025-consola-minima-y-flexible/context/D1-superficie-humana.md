# Context pack — D1-superficie-humana

Spec: `docs/specs/025-consola-minima-y-flexible/spec.md`, **AC-01, AC-02, AC-03**. Primer paquete de
025.

## Estado medido hoy

`MENU_ITEMS` (`set_agents_app.py:3523-3534`) son **10 ítems, los 10 con emoji**:

```
🩺 Estado general · 📦 Instalar / Reparar · 🔄 Actualizar · 🧠 Modelos ·
🧰 Herramientas (CLIs) · ➕ Proponer herramienta nueva · 🔌 MCPs ·
🧩 Plugins Claude Code · 🗒 Vault Obsidian · ⏻ Salir
```

El CLI expone **68 flags**. `tui.py` tiene un picker sólido con detección de TTY.

## El pedido, en las palabras de Federico

*"Quiero que la app de terminal sea más minimalista y sólo muestre lo transparente al usuario, sin
muchos comandos ni caracteres raros… Y quita/oculta las opciones que al usuario no le agregan
nada."*

Y la decisión que ya tomó, no re-litigable: **las flags internas se ocultan del `--help` y siguen
funcionando**.

## TAREA

**AC-01** — Menú sin emoji, jerarquía por **espaciado y peso**.

La regla que transfiere de la skill `ui-ux-pro-max` —scopeada a web y mobile, pero esta regla
aplica— es **no usar emoji como iconos estructurales**: dependen de la fuente, rompen alineación, y
no se pueden tematizar. Mirá `🗒  Vault Obsidian` y `⏻  Salir` en el código: ya llevan **dos
espacios** en vez de uno, porque esos dos glifos miden distinto. Ese parche es la prueba del
problema.

**AC-02** — Las flags internas se **ocultan del `--help`** y **siguen respondiendo igual**.

**Borrarlas rompe el harness**: `coord_policy` las tiene en su allowlist y los spawns las invocan.
Ocultar es `help=argparse.SUPPRESS`, no eliminar. `--help --avanzado` las muestra.

**Cuáles son internas es una decisión que tomás vos, con criterio y a la vista**: la spec dice 31 de
68, pero ese número salió de una exploración anterior. **Contá las de hoy y justificá el corte** —
lo que un humano usa en su terminal queda; lo que sólo invoca un spawn se oculta. Escribí la lista
en la evidencia.

**Test obligatorio**: cada flag oculta **sigue respondiendo**. Sin eso, el próximo cambio la borra.

**AC-03** — La salida JSON cruda de los comandos de routing pasa a **texto humano por default**, con
`--json` para la máquina.

Hoy `--route-doctor` escupe un JSON de una línea. Pero **hay consumidores máquina**: el propio
orquestador parsea esas salidas en sus scripts. `--json` tiene que preservar **exactamente** el
formato actual, byte por byte, o rompés a quien ya lo consume.

## La trampa

**Ocultar una flag que un spawn invoca la mata en la práctica**, aunque el parser la acepte: nadie
va a saber que existe. Por eso `--help --avanzado` no es un extra, es la contraparte.

Y al revés: si dejás visible todo lo que un humano *podría* llegar a usar, no cambiaste nada. El
pedido es que la superficie sea **mínima**, no que esté ordenada.

## Restricciones

- **ADR-0050** (`ls docs/adr/` para confirmar, indexalo en `docs/adr/README.md`): superficie humana.
- **No borres ninguna flag.** Ocultar sí, borrar no.
- **No cambies el formato de `--json`.**
- **No uses `git checkout`, `git restore` ni `git stash`.** Para morder y restaurar: `cp` y `cp`.
- **No toques nada bajo `~`.**
- `tests/test_harness.py` assertea frases y ayudas por grep: **`grep -n` antes de mover texto**.

## Validación

`python3 -m unittest discover -s tests` (**`pytest` NO está instalado**; base **1117 OK / 3 skips**)
· `./ai/scripts/verify.sh` → `VERIFY_PASS` · `./build.sh --check` → `GLOBAL_TREE_SYNC_OK` +
`BUILD_CHECK_PASS` · `git diff --check` limpio.

**Corré los comandos largos así:** `ai/scripts/heartbeat-run.py --interval 20 -- <comando>`
(ADR-0041). Cuatro agentes ya lo violaron esta noche y tuvieron que repetir.

## Evidencia

`docs/specs/025-consola-minima-y-flexible/evidence/D1-implementer.md`, escrito **en el primer
minuto**: tabla AC → cambio (`archivo:línea`) → prueba; **el menú antes y después, pegado**; **la
lista de flags ocultas con el criterio del corte**, y la prueba de que cada una sigue respondiendo;
la salida de `--route-doctor` humana y la de `--json` idéntica a la de hoy; y los gates.

**Por cada test nuevo: neutralizá el cambio, confirmá el rojo, revertí, pegá la prueba.** Ya van
cinco guardas huecas en este proyecto. No escribas la sexta.

**Cada bloque literal, o marcado como recortado.** Si no lo corriste, "sin verificar".

## Fuera de alcance

Spinner y progreso (D2) · posturas de autonomía y toggles (D3) · harness por CLI (D4) · vault (D5) ·
el sort key · los defectos latentes registrados · el codename de cliente de 024, que está bloqueado
esperando decisión humana.
