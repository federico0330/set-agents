"""ui.py — the console app's single visual system (stdlib only, DEC-4).

Replaces `tui_views.py`. Three defects that module had, fixed here by construction:

1. **The palette was frozen at import time** (`if use_color():` at module level). A process
   that imported it without a TTY got empty color codes forever. Here every colour decision
   goes through `caps()`, which re-reads the environment and the stream on each call.
2. **Padding used `len()`** on strings that could contain wide glyphs, so every box drawn
   with a double-width character came out with a crooked right border. `cell_width()` is the
   only width authority in this module, and it knows East Asian Width.
3. **Decorative glyphs leaked into label strings.** They belong to the renderer, never to the
   text: `is_safe_label()` states that rule positively (letters, digits, spaces, and a closed
   punctuation set) instead of the `isascii()` approximation, which rejected honest Spanish
   ("Cómo") while still admitting symbols like U+23FB.

Palette: Rose Pine, addressed by ROLE (`title`, `ok`, `warn`, ...) and never by colour name,
so a future theme swaps one table and nothing else.
"""
from __future__ import annotations

import os
import re
import shutil
import sys
import time
import unicodedata
from typing import Any, Callable

# --------------------------------------------------------------------------- text measuring

_ANSI_RE = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]")


def strip_ansi(text: str) -> str:
    return _ANSI_RE.sub("", str(text))


def cell_width(text: str) -> int:
    """Terminal cells `text` occupies, ANSI excluded. Wide/Fullwidth count 2, combining
    marks count 0, everything else 1 (Ambiguous resolves to 1, matching every terminal
    this app targets). The one width authority here — never call `len()` for layout."""
    width = 0
    for char in strip_ansi(text):
        if unicodedata.combining(char):
            continue
        width += 2 if unicodedata.east_asian_width(char) in ("W", "F") else 1
    return width


# Letters, digits, spaces and this closed punctuation set. Nothing else: a decorative glyph
# is the renderer's job (`CURSOR`, `DOT_ON`, ...), never part of the label it decorates.
# This is ADR-0050's actual decision -- the defect it fixed was variable glyph width, not
# accented Latin -- stated as a rule that admits "Cómo está" and still rejects U+23FB.
LABEL_PUNCT = " -/()[]·?¿!¡,.:;+&'\""


def is_safe_label(text: str) -> bool:
    """True when `text` may be used as a menu label."""
    return all(char.isalnum() or char in LABEL_PUNCT for char in str(text))


def term_width(minimum: int = 40, maximum: int = 100) -> int:
    try:
        return max(minimum, min(maximum, shutil.get_terminal_size().columns))
    except (ValueError, OSError):
        return 78


def pad(text: str, width: int, align: str = "left") -> str:
    """Cell-width aware padding — `str.ljust` counts codepoints and would lie here."""
    missing = max(0, width - cell_width(text))
    if align == "right":
        return " " * missing + text
    if align == "center":
        left = missing // 2
        return " " * left + text + " " * (missing - left)
    return text + " " * missing


def clip(text: str, width: int) -> str:
    """Truncate to `width` cells, marking the cut with an ellipsis. ANSI-naive by design:
    callers clip raw text and colour afterwards."""
    if width <= 0:
        return ""
    if cell_width(text) <= width:
        return text
    out = ""
    used = 0
    for char in text:
        char_width = cell_width(char)
        if used + char_width > width - 1:
            break
        out += char
        used += char_width
    return out + "…"


# --------------------------------------------------------------------------- capability

def caps(stream=None) -> str:
    """"truecolor" | "256" | "16" | "none" — recomputed on every call, never cached at
    import (that was `tui_views.py`'s bug)."""
    stream = sys.stdout if stream is None else stream
    if os.environ.get("NO_COLOR"):
        return "none"
    term = os.environ.get("TERM", "")
    if term == "dumb":
        return "none"
    try:
        if not stream.isatty():
            return "none"
    except (AttributeError, ValueError):
        return "none"
    if os.environ.get("COLORTERM", "").lower() in ("truecolor", "24bit"):
        return "truecolor"
    if "256" in term:
        return "256"
    return "16"


def use_color(stream=None) -> bool:
    return caps(stream) != "none"


# --------------------------------------------------------------------------- palette

# Rose Pine, one row per role: (hex, xterm-256 index, ANSI-16 SGR code).
_ROLES: dict[str, tuple[str, int, int]] = {
    "text":    ("e0def4", 189, 37),
    "muted":   ("908caa", 103, 90),
    "line":    ("6e6a86",  60, 90),
    "title":   ("c4a7e7", 183, 95),   # iris
    "heading": ("ebbcba", 217, 95),   # rose
    "accent":  ("c4a7e7", 183, 95),   # iris
    "ok":      ("9ccfd8", 152, 96),   # foam
    "warn":    ("f6c177", 222, 93),   # gold
    "err":     ("eb6f92", 211, 91),   # love
    "cool":    ("31748f",  24, 36),   # pine
}

RESET = "\033[0m"


def _sgr(role: str, level: str) -> str:
    hex_value, xterm, ansi = _ROLES[role]
    if level == "truecolor":
        r, g, b = (int(hex_value[i:i + 2], 16) for i in (0, 2, 4))
        return f"\033[38;2;{r};{g};{b}m"
    if level == "256":
        return f"\033[38;5;{xterm}m"
    return f"\033[{ansi}m"


def paint(text: str, role: str = "text", *, bold: bool = False, stream=None) -> str:
    """Colour `text` for `role`. Degrades to the plain string when colour is off."""
    level = caps(stream)
    if level == "none":
        return str(text)
    prefix = _sgr(role, level)
    if bold:
        prefix = "\033[1m" + prefix
    return f"{prefix}{text}{RESET}"


def title(text, **kw) -> str: return paint(text, "title", bold=True, **kw)
def heading(text, **kw) -> str: return paint(text, "heading", bold=True, **kw)
def body(text, **kw) -> str: return paint(text, "text", **kw)
def muted(text, **kw) -> str: return paint(text, "muted", **kw)
def accent(text, **kw) -> str: return paint(text, "accent", **kw)
def ok(text, **kw) -> str: return paint(text, "ok", **kw)
def warn(text, **kw) -> str: return paint(text, "warn", **kw)
def err(text, **kw) -> str: return paint(text, "err", **kw)


def bold(text, stream=None) -> str:
    return f"\033[1m{text}{RESET}" if caps(stream) != "none" else str(text)


# --------------------------------------------------------------------------- glyphs

# Every glyph here is one cell wide and carries no variation selector.
CURSOR = "▸"
DOT_ON = "●"
DOT_OFF = "○"
DOT_WARN = "▲"
CHECK = "✓"
CROSS = "✗"
BAR_FULL = "█"
BAR_EMPTY = "░"
SPINNER = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"


# How each host id is spelled for a person. One map, read by the Estado panel, the hosts
# menu and the onboarding wizard -- a display name is presentation, so it lives here and not
# in `provider_registry`, whose HOSTS table is a machine contract.
HOST_TITLES = {
    "agy": "Antigravity",
    "fx": "fx",
    "copilot": "GitHub Copilot",
    "claude": "Claude Code",
    "codex": "Codex",
    "opencode": "OpenCode",
    "pi": "pi",
}


# --------------------------------------------------------------------------- components

def rule(label: str = "", width: int | None = None) -> str:
    """`── Label ──────────` — a section divider that costs one row, unlike a box."""
    total = width or term_width()
    if not label:
        return paint("─" * total, "line")
    head = paint("──", "line")
    text = heading(label)
    filler = max(0, total - 3 - cell_width(label) - 3)
    return f"{head} {text} {paint('─' * filler, 'line')}"


def kv(label: str, value: str, *, role: str = "text", label_width: int = 18) -> str:
    return f"  {muted(pad(label, label_width))}{paint(value, role)}"


def chip(text: str, role: str = "muted") -> str:
    return paint(f"[ {text} ]", role)


def dot(state) -> str:
    """● listo / ▲ aviso / ○ nada. `state` is a bool or one of the app's state words."""
    if state is True or state in ("listo", "ok", "vivo", "al dia", "al día", "instalado"):
        return ok(DOT_ON)
    if state in ("aviso", "stale", "warn", "unlistable", "sin lane"):
        return warn(DOT_WARN)
    return muted(DOT_OFF)


def steps(index: int, total: int, label: str) -> str:
    """`Paso 2 de 5 · Qué querés configurar      ●●○○○`"""
    left = f"Paso {index} de {total}"
    beads = ok(DOT_ON * index) + muted(DOT_OFF * max(0, total - index))
    line = f"  {title(left)} {muted('·')} {heading(label)}"
    gap = max(1, term_width() - cell_width(line) - total - 2)
    return line + " " * gap + beads


def bar(pct: int, width: int = 24) -> str:
    pct = max(0, min(100, int(pct)))
    filled = round(width * pct / 100)
    return f"{ok(BAR_FULL * filled)}{muted(BAR_EMPTY * (width - filled))}  {paint(f'{pct}%', 'warn', bold=True)}"


def checkbox(label: str, checked: bool, focused: bool = False) -> str:
    marker = ok(f"[{CHECK}]") if checked else muted("[ ]")
    if focused:
        return f"  {accent(CURSOR)} {marker} {paint(label, 'title', bold=True)}"
    return f"    {marker} {body(label)}"


def radio(label: str, selected: bool, focused: bool = False) -> str:
    marker = ok(f"({DOT_ON})") if selected else muted("( )")
    if focused:
        return f"  {accent(CURSOR)} {marker} {paint(label, 'title', bold=True)}"
    return f"    {marker} {body(label)}"


def _mark(current_mark: str) -> str:
    """Colour the marker the renderer already chose -- `● ` for "this is the value in effect",
    `[x] `/`[ ] ` for a multi picker. The styler must never substitute a glyph of its own:
    doing that is what made a multi picker paint dots instead of checkboxes."""
    if not current_mark:
        return ""
    filled = DOT_ON in current_mark or "x" in current_mark
    return (ok(current_mark) if filled else muted(current_mark))


def row_selected(item: str, current_mark: str, suffix: str) -> str:
    """Picker row styler (`tui.run_picker(style={"selected_row": ...})`)."""
    return f"  {accent(CURSOR)} {_mark(current_mark)}{paint(item, 'title', bold=True)}{suffix}"


def row_unselected(item: str, current_mark: str, suffix: str) -> str:
    return f"    {_mark(current_mark)}{body(item)}{suffix}"


# --------------------------------------------------------------------------- wordmark

# Two-row half-block wordmark, per-character gradient rose -> iris.
_WORDMARK = (
    "█▀▀ █▀▀ ▀█▀ ▄▄ ▄▀▄ █▀▀ █▀▀ █▄ █ ▀█▀ █▀▀",
    "▄▄█ █▄▄  █     █▀█ █▄█ █▄▄ █ ▀█  █  ▄▄█",
)
_GRADIENT = ((235, 188, 186), (196, 167, 231))  # rose -> iris


def _gradient_row(row: str, offset: int, level: str) -> str:
    if level != "truecolor":
        return paint(row, "title", bold=True)
    (r1, g1, b1), (r2, g2, b2) = _GRADIENT
    span = max(1, len(row) - 1)
    out = []
    for index, char in enumerate(row):
        if char == " ":
            out.append(char)
            continue
        t = min(1.0, (index + offset) / span)
        r, g, b = (round(r1 + (r2 - r1) * t), round(g1 + (g2 - g1) * t), round(b1 + (b2 - b1) * t))
        out.append(f"\033[38;2;{r};{g};{b}m{char}")
    return "".join(out) + RESET


def wordmark(tagline: str = "") -> list[str]:
    """The product signature. Degrades to one plain line without colour."""
    level = caps()
    if level == "none":
        return ["SET-AGENTS" + (f" — {tagline}" if tagline else "")]
    rows = [f"  {_gradient_row(_WORDMARK[0], 0, level)}",
            f"  {_gradient_row(_WORDMARK[1], 6, level)}"]
    if tagline:
        rows.append(f"  {muted(tagline)}")
    return rows


# --------------------------------------------------------------------------- session cache

class SessionCache:
    """In-memory TTL cache so back-navigation never re-pays for a subprocess probe."""

    def __init__(self, ttl_seconds: float = 60.0):
        self._ttl = ttl_seconds
        self._cache: dict[str, tuple[float, Any]] = {}

    def get(self, key: str) -> Any | None:
        if key in self._cache:
            stamped, value = self._cache[key]
            if time.monotonic() - stamped < self._ttl:
                return value
            del self._cache[key]
        return None

    def set(self, key: str, value: Any) -> None:
        self._cache[key] = (time.monotonic(), value)

    def get_or_compute(self, key: str, compute: Callable[[], Any]) -> Any:
        cached = self.get(key)
        if cached is not None:
            return cached
        value = compute()
        self.set(key, value)
        return value

    def invalidate(self, key: str | None = None) -> None:
        if key is None:
            self._cache.clear()
        else:
            self._cache.pop(key, None)


GLOBAL_CACHE = SessionCache(ttl_seconds=60.0)
