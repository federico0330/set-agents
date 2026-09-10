"""onboarding.py — the guided first run of `./set-agents` (stdlib only, DEC-4).

Five steps: what is on this machine, what to configure, how you want to work, a review you
have to confirm, and the applying. Nothing mutates before step 4 is confirmed.

Two rules this module is built around:

- **Screens are pure.** Every `*_lines` / `*_options` function turns data into strings and
  nothing else, so the copy and the layout are testable without a terminal.
- **Mutations are injected, never imported.** `run(ops)` receives the callables it is allowed
  to invoke from `set_agents_app`. That keeps every mutating command inside the monolith where
  the golden suite patches it (ADR-0066's extraction ceiling) and makes this module trivially
  mockable.
"""
from __future__ import annotations

import dataclasses

import tui
import ui

STEPS_TOTAL = 5


@dataclasses.dataclass(frozen=True)
class Target:
    """One AI CLI the harness can be applied to."""

    host_id: str
    label: str
    harness: str  # what install.sh --harness expects, verbatim


# The four `install.sh --harness` values a first run should ever need. Order is the one the
# README teaches; `pi` last because it rides along with Claude Code.
TARGETS = (
    Target("claude", "Claude Code", "claude"),
    Target("codex", "Codex", "codex"),
    Target("opencode", "OpenCode", "opencode"),
    Target("pi", "pi", "pi"),
)


@dataclasses.dataclass(frozen=True)
class Preset:
    key: str
    label: str
    hint: str
    postura: str
    metodologia: str


PRESETS = (
    Preset("equilibrado", "Equilibrado",
           "trabaja solo y te consulta lo que no se puede deshacer",
           "autonoma", "sdd"),
    Preset("cuidadoso", "Cuidadoso",
           "te pide confirmación antes de tocar archivos o correr comandos",
           "consultiva", "sdd"),
    Preset("suelto", "Suelto",
           "la menor cantidad de preguntas posible",
           "autonoma", "off"),
)


# --------------------------------------------------------------------------- pure screens

def step_header(index: int, label: str, body: list[str]) -> str:
    parts = [ui.steps(index, STEPS_TOTAL, label), ""]
    parts += body
    parts.append("")
    return "\n".join(parts)


def detection_lines(host_rows, counts=None) -> list[str]:
    """Step 1. One row per candidate, always — an absent CLI is information, not an omission.
    The model count is printed only where a probe actually returned one."""
    counts = counts or {}
    known = {target.host_id: target.label for target in TARGETS}
    words = {"vivo": "listo", "ausente": "no está",
             "unlistable": "sin sesión iniciada", "sin lane": "todavía sin lane"}
    lines = []
    for host_id, state in host_rows:
        label = known.get(host_id, ui.HOST_TITLES.get(host_id, host_id))
        detail = words.get(state, state)
        if state == "vivo" and counts.get(host_id):
            detail = f"listo · {counts[host_id]} modelos"
        lines.append(f"  {ui.dot(state == 'vivo')} {ui.pad(label, 16)}{ui.muted(detail)}")
    return lines


def install_options(host_rows) -> tuple[tuple[Target, str], ...]:
    """Step 2. Every target is offered; the ones that are not installed say so, because
    `install.sh` installs them and the user should know that before marking the box."""
    present = {host_id for host_id, state in host_rows if state != "ausente"}
    return tuple(
        (target, "" if target.host_id in present else "no está — te la instalo")
        for target in TARGETS
    )


def review_lines(chosen: tuple[Target, ...], preset: Preset) -> list[str]:
    """Step 4. What is about to happen, in full, before anything happens."""
    lines = [f"  {ui.body('Voy a hacer esto:')}", ""]
    if chosen:
        for target in chosen:
            lines.append(f"  {ui.ok(ui.DOT_ON)} aplicar el harness en {target.label}")
    else:
        lines.append(f"  {ui.muted(ui.DOT_OFF)} no tocar ninguna CLI")
    lines.append(f"  {ui.ok(ui.DOT_ON)} autonomía: {preset.label.lower()} ({preset.hint})")
    lines.append(f"  {ui.ok(ui.DOT_ON)} dejar los modelos en automático")
    lines += ["", f"  {ui.muted('Nada se toca hasta que elijas Aplicar.')}"]
    return lines


def summary_lines(results: list[tuple[str, bool]], preset: Preset) -> list[str]:
    """The closing screen. Reports what actually happened, failures included."""
    lines = []
    for label, succeeded in results:
        glyph = ui.ok(ui.CHECK) if succeeded else ui.err(ui.CROSS)
        tail = "" if succeeded else ui.err("  falló — mirá la salida de arriba")
        lines.append(f"  {glyph} {label}{tail}")
    if not results:
        lines.append(f"  {ui.muted(ui.DOT_OFF)} no se aplicó el harness en ninguna CLI")
    lines.append(f"  {ui.ok(ui.CHECK)} forma de trabajo: {preset.label.lower()}")
    lines += ["", f"  {ui.body('Abrí tu CLI de IA en un proyecto y empezá a trabajar.')}"]
    return lines


# --------------------------------------------------------------------------- the runner

def run(ops, style=None):
    """Drive the five steps. `ops` supplies every mutating callable (see
    `set_agents_app._onboarding_ops`). Returns True when the user applied, False when they
    walked away — cancelling at any step before 4 changes nothing on disk."""
    style = style or {}
    try:
        host_rows, counts = ops["host_rows"]()
    except Exception:
        host_rows, counts = [], {}

    # ---- 1. what is here
    header = step_header(1, "Qué encontré en tu máquina", detection_lines(host_rows, counts))
    if not isinstance(tui.run_picker(("Seguir", "Salir"), style=style, header=header), tui.Selected):
        return False

    # ---- 2. what to configure
    options = install_options(host_rows)
    present = {host_id for host_id, state in host_rows if state != "ausente"}
    labels = [
        target.label + (f"   ({note})" if note else "")
        for target, note in options
    ]
    preselected = [i for i, (target, _) in enumerate(options) if target.host_id in present]
    header = step_header(2, "Qué querés que configure", [
        f"  {ui.muted('Marcá las CLIs donde querés el harness. Podés cambiarlo después.')}"])
    marked = tui.run_picker(labels, style=style, header=header, multi=True, marked=preselected)
    if not isinstance(marked, tui.Marked):
        return False
    chosen = tuple(options[i][0] for i in marked.indices)

    # ---- 3. how you want to work
    header = step_header(3, "Cómo querés trabajar", [
        f"  {ui.muted('Cuánto te consulta el harness antes de actuar.')}"])
    picked = tui.run_picker(
        [f"{preset.label} — {preset.hint}" for preset in PRESETS], style=style, header=header)
    if not isinstance(picked, tui.Selected):
        return False
    preset = PRESETS[picked.index]

    # ---- 4. review (nothing has been written yet)
    header = step_header(4, "Revisá antes de aplicar", review_lines(chosen, preset))
    confirm = tui.run_picker(("Aplicar", "Cancelar"), style=style, header=header)
    if not isinstance(confirm, tui.Selected) or confirm.index == 1:
        return False

    # ---- 5. apply
    ops["set_postura"](preset.postura)
    ops["set_metodologia"](preset.metodologia)
    results = []
    for target in chosen:
        # The installer owns the terminal while it runs (it can prompt for sudo), so nothing
        # here redraws over it: one plain line before, the child, then the mark.
        print(f"{ui.CURSOR} aplicando el harness en {target.label}…")
        results.append((target.label, ops["install"](target.harness) == 0))
    header = step_header(5, "Listo", summary_lines(results, preset))
    tui.run_picker(("Ir al menú",), style=style, header=header)
    return True
