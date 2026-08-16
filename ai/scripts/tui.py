"""tui.py — stdlib-only arrow-key picker (005-portable-harness, package P3-tui).

DEC-4 (spec non-goal, hard constraint): zero third-party TUI libraries. Everything here is
stdlib: `termios`/`tty` on POSIX (guarded by `try/except ImportError` so importing this module
on native Windows Python never raises — the CI `windows-bootstrap` job runs the full test suite
there), `msvcrt` best-effort on `win32`.

Layers (see docs/specs/005-portable-harness/plan.md T-300..T-308):
  1. Pure core   — `PickerState` + `KeyEvent` + `reduce()`. Zero I/O, unit-tested without a pty
                    (AC-22). `reduce()` never imports `termios`/`signal`/anything platform-specific.
  2. Decoder     — `decode_keys()`: raw terminal bytes -> logical `KeyEvent`s (AC-23). Stateless;
                    a `read()` on a raw fd can cut an ESC sequence or a multibyte UTF-8 character
                    in half between two calls, so it returns `(events, remainder)` and the CALLER
                    re-feeds `remainder + next_chunk` on the next read.
  3. TerminalSession — raw mode / alternate screen / bracketed paste, restored via `finally` AND
                    `SIGTERM`/`SIGHUP` handlers (AC-27), never only `EOFError`/`KeyboardInterrupt`.
  4. run_picker  — the only layer that touches a real fd: consumes `decode_keys()` output, drives
                    `reduce()`, renders with the caller's `style` callables (AC-24/AC-25/AC-26).
  5. suspend_terminal() — module-level, no-op when no `TerminalSession` is active. Lets a single
                    `input()` call work unmodified whether it's reached from a bare CLI flag (no
                    active session) or from the picker (active session, needs cooked mode for the
                    prompt to echo) — AC-26.

`tui.py` NEVER imports `set_agents_app`/`setup_models` (one-way dependency: those modules import
this one, never the reverse).
"""
from __future__ import annotations

import contextlib
import os
import select
import signal
import sys
import threading
import time
from dataclasses import dataclass, replace

try:
    import termios
    import tty
except ImportError:  # pragma: no cover - exercised on native Windows Python only
    termios = None
    tty = None

try:
    import msvcrt
except ImportError:  # pragma: no cover - exercised on POSIX only
    msvcrt = None


# --------------------------------------------------------------------- pure core (AC-22)

class _Pending:
    """Sentinel: the picker has not decided a result yet. A dedicated class (not `None`,
    which IS a valid terminal result meaning 'cancelled') so `state.result is PENDING` is
    unambiguous."""

    def __repr__(self):
        return "PENDING"


PENDING = _Pending()


@dataclass(frozen=True)
class KeyEvent:
    """A logical key event, already decoded from raw bytes (or synthesized directly, e.g. by
    tests exercising `reduce()` without going through `decode_keys()` at all — that separation
    is the point of AC-22 vs AC-23)."""

    kind: str  # UP DOWN ENTER ESCAPE INTERRUPT EOF SEARCH BACKSPACE CHAR PASTE UNKNOWN
    char: str | None = None


@dataclass(frozen=True)
class Selected:
    """`reduce()` resolved the picker to an existing item, by index into `state.items`."""

    index: int


@dataclass(frozen=True)
class FreeText:
    """`reduce()` resolved the picker to a value the user typed, not one of `state.items`
    (or a bare free-text prompt — a picker constructed with `items=()`)."""

    value: str


@dataclass(frozen=True)
class PickerState:
    """items/cursor/mode/query/freetext_allowed/result — see module docstring layer 1.

    Design decisions (documented here for the reviewer, not just in the implementer's evidence):

    - Cursor WRAPS at the boundaries (`UP` at index 0 goes to the last item, `DOWN` at the last
      item goes to 0) rather than clamping. Chosen because every replaced menu is a short, fully
      visible list — wrap-around is one keystroke cheaper for reaching the last item and never
      strands the user against an invisible wall.
    - Three modes, not two: `navigate` (arrow list), `search` (typeahead entered via `/` from
      navigate — F-08: `query` live-filters `items` by substring/casefold, arrow-navigable
      exactly like `navigate` over just the matches; Enter resolves to `Selected` on whichever
      match is highlighted, or to `FreeText` when `freetext_allowed` and the query matches
      nothing at all — this is the AC-24 replacement for `setup_models.choose()`'s "number or
      free text" line), and
      `freetext` (a bare single-line prompt with no backing list at all — the mode `run_picker`
      starts in when called with `items=()`, replacing a raw `input()` call with one that is
      raw-mode/suspend-aware). `search` and `freetext` share editing keys (CHAR/BACKSPACE) but
      differ on ESCAPE (search falls back to navigate; freetext has nothing to fall back to, so
      it cancels the whole picker) and on ENTER (search requires a match-or-freetext-allowed;
      freetext always resolves, even to an empty string — same as the old `input().strip()`
      idiom, where the caller decides what an empty string means).
    - `reduce()` never rejects a `SEARCH`-kind event just because `mode != "navigate"`: it
      reinterprets it as a literal `/` character appended to the query instead (so typing a `/`
      while already composing a path or a model id in `search`/`freetext` mode works as expected,
      it does not re-trigger a mode switch). This mirrors, in `reduce()`, the note attached to
      AC-23's decoder vocabulary ("SEARCH only if mode==navigate, otherwise it's a CHAR") without
      making `decode_keys()` itself state-aware — `decode_keys()` stays a pure `bytes -> events`
      function with no knowledge of `PickerState` at all, which is what keeps AC-22 and AC-23
      independently testable.
    - A `PASTE` event is IGNORED in `navigate` mode on purpose (AC-23's immunity: a payload
      containing e.g. a literal up-arrow sequence must never move the cursor or select
      anything — decoded already as one opaque `PASTE` event, never retokenized). In `search`/
      `freetext` mode, where free-text entry is the whole point (the vault path/project prompts,
      `setup_models.choose()`'s free-text model id), a `PASTE` event is the PRIMARY input path on
      any terminal that honors bracketed paste, so it is sanitized (see `_sanitize_paste`: control
      bytes stripped, only the first line kept — never re-tokenized as keys) and appended to
      `query`, same as a run of `CHAR` events would be.
    """

    items: tuple[str, ...]
    cursor: int = 0
    mode: str = "navigate"
    query: str = ""
    freetext_allowed: bool = False
    result: object = PENDING


def reduce(state: PickerState, key: KeyEvent) -> PickerState:
    """`(state, key) -> state`. Zero I/O. Once `state.result` is no longer PENDING the state is
    terminal — further keys are no-ops (idempotent), so a caller never needs to guard against
    calling `reduce()` one extra time after the loop already decided."""
    if state.result is not PENDING:
        return state
    if key.kind in ("INTERRUPT", "EOF"):
        return replace(state, result=None)
    if state.mode == "navigate":
        return _reduce_navigate(state, key)
    if state.mode == "search":
        return _reduce_text_entry(state, key, cancels_to_navigate=True)
    if state.mode == "freetext":
        return _reduce_text_entry(state, key, cancels_to_navigate=False)
    return state


def _reduce_navigate(state: PickerState, key: KeyEvent) -> PickerState:
    n = len(state.items)
    if key.kind == "UP":
        return state if n == 0 else replace(state, cursor=(state.cursor - 1) % n)
    if key.kind == "DOWN":
        return state if n == 0 else replace(state, cursor=(state.cursor + 1) % n)
    if key.kind == "ENTER":
        return state if n == 0 else replace(state, result=Selected(state.cursor))
    if key.kind == "ESCAPE":
        return replace(state, result=None)
    if key.kind == "SEARCH":
        return replace(state, mode="search", query="")
    return state


def _sanitize_paste(payload: str) -> str:
    """Bracketed-paste payload -> the text `search`/`freetext` actually append to `query`
    (F-02): only the FIRST line survives (these are single-line prompts, never a multi-line
    editor -- a newline embedded in the payload must not become "press Enter" mid-paste), and
    any remaining control byte is dropped (tabs kept, everything below 0x20 otherwise cut).
    Never re-tokenizes the payload as keys -- it stays a single opaque string operation."""
    if not payload:
        return ""
    first_line = payload.splitlines()[0]
    return "".join(ch for ch in first_line if ch == "\t" or ch >= " ")


def _search_matches(items: tuple[str, ...], query: str) -> tuple[int, ...]:
    """F-08: which `items` indices survive `search` mode's live filter -- substring, case-
    insensitive, against `query`. An empty query matches everything (an arrow-navigable full
    list with a live query bar on top, the same list `navigate` already shows, plus the
    ability to start narrowing it by typing) -- this is what makes `/` "type to filter and
    pick with arrows" instead of the old "type the exact item name from memory, Enter"."""
    if not query:
        return tuple(range(len(items)))
    needle = query.casefold()
    return tuple(i for i, item in enumerate(items) if needle in item.casefold())


def _retarget_cursor(state: PickerState, *, is_search: bool) -> PickerState:
    """After a query-changing keystroke in `search` mode, keep `cursor` pointing at a
    surviving match (F-08) -- otherwise it could stay stranded on a now-filtered-out item:
    nothing highlighted in the rendered list, and Enter would silently no-op even though
    other matches are visible. A no-op outside `search` mode (`freetext` has no item list to
    retarget against) and when the current cursor is already among the matches."""
    if not is_search:
        return state
    matches = _search_matches(state.items, state.query)
    if not matches or state.cursor in matches:
        return state
    return replace(state, cursor=matches[0])


def _reduce_text_entry(state: PickerState, key: KeyEvent, *, cancels_to_navigate: bool) -> PickerState:
    # `cancels_to_navigate` is True exactly for `search` mode (see `reduce()`) -- `freetext`
    # mode has no backing item list at all, so none of the F-08 filtering/navigation below
    # applies there; it stays the bare single-line prompt it always was.
    is_search = cancels_to_navigate
    if key.kind == "ESCAPE":
        if cancels_to_navigate:
            return replace(state, mode="navigate", query="")
        return replace(state, result=None)
    if is_search and key.kind in ("UP", "DOWN"):
        # F-08: arrows move the cursor among the FILTERED matches only, wrapping within that
        # subset -- never landing on an item the current query has hidden.
        matches = _search_matches(state.items, state.query)
        if not matches:
            return state
        position = matches.index(state.cursor) if state.cursor in matches else 0
        position = (position + (1 if key.kind == "DOWN" else -1)) % len(matches)
        return replace(state, cursor=matches[position])
    if key.kind == "BACKSPACE":
        return _retarget_cursor(replace(state, query=state.query[:-1]), is_search=is_search)
    if key.kind in ("CHAR", "SEARCH"):
        char = key.char if key.kind == "CHAR" else "/"
        if not char:
            return state
        return _retarget_cursor(replace(state, query=state.query + char), is_search=is_search)
    if key.kind == "PASTE":
        addition = _sanitize_paste(key.char or "")
        if not addition:
            return state
        return _retarget_cursor(replace(state, query=state.query + addition), is_search=is_search)
    if key.kind == "ENTER":
        if not cancels_to_navigate:
            return replace(state, result=FreeText(state.query))
        # F-08: Enter selects whichever match is currently HIGHLIGHTED (cursor, kept valid by
        # `_retarget_cursor`/the arrow handling above) rather than demanding an exact
        # casefold match against the typed text -- "type to filter, arrows to pick" instead of
        # "type the item's full name from memory". The free-text fallback (a query that
        # matches nothing, `freetext_allowed=True`) is unchanged.
        matches = _search_matches(state.items, state.query)
        if matches and state.cursor in matches:
            return replace(state, result=Selected(state.cursor))
        if state.freetext_allowed and state.query:
            return replace(state, result=FreeText(state.query))
        return state
    return state


# ---------------------------------------------------------------- raw-byte decoder (AC-23)

_PASTE_START = b"\x1b[200~"
_PASTE_END = b"\x1b[201~"


def _utf8_length(lead: int) -> int | None:
    if lead & 0xE0 == 0xC0:
        return 2
    if lead & 0xF0 == 0xE0:
        return 3
    if lead & 0xF8 == 0xF0:
        return 4
    return None


def decode_keys(buf: bytes) -> tuple[list[KeyEvent], bytes]:
    """Raw terminal bytes -> `(events, remainder)`. `remainder` is the tail of an incomplete
    sequence (an ESC sequence or a multibyte UTF-8 char cut short, or an in-progress bracketed
    paste) — the caller prepends it to the next chunk read from the fd and calls again. An empty
    `buf` (`read()` returned nothing — real EOF at the fd) decodes to a single EOF event.

    Never raises: any byte sequence this vocabulary does not recognize becomes `UNKNOWN` (and is
    consumed, never a crash, never an infinite loop).
    """
    if buf == b"":
        return [KeyEvent("EOF")], b""
    events: list[KeyEvent] = []
    i = 0
    n = len(buf)
    while i < n:
        b = buf[i]
        if b == 0x1B:
            remaining = buf[i:]
            if remaining.startswith(_PASTE_START):
                end = buf.find(_PASTE_END, i + len(_PASTE_START))
                if end == -1:
                    return events, remaining  # marker matched, payload/terminator incomplete
                payload = buf[i + len(_PASTE_START):end].decode("utf-8", "replace")
                events.append(KeyEvent("PASTE", payload))
                i = end + len(_PASTE_END)
                continue
            if len(remaining) < len(_PASTE_START) and _PASTE_START.startswith(remaining):
                return events, remaining  # incomplete marker prefix, wait for more bytes
            if i + 1 >= n:
                return events, buf[i:]  # lone ESC byte so far -- could be a sequence prefix
            second = buf[i + 1]
            if second in (0x5B, 0x4F):  # '[' (CSI) or 'O' (SS3)
                if i + 2 >= n:
                    return events, buf[i:]
                third = buf[i + 2]
                if third in (0x41, 0x42):  # 'A' / 'B'
                    events.append(KeyEvent("UP" if third == 0x41 else "DOWN"))
                    i += 3
                    continue
                if second == 0x5B:
                    # An unrecognized CSI sequence: consume through its final byte
                    # (0x40-0x7e) rather than emitting UNKNOWN per-byte and risking a stray
                    # 'A'/'B' inside its parameters being misread as an arrow key later.
                    j = i + 2
                    while j < n and not (0x40 <= buf[j] <= 0x7E):
                        j += 1
                    if j >= n:
                        return events, buf[i:]
                    events.append(KeyEvent("UNKNOWN"))
                    i = j + 1
                    continue
                events.append(KeyEvent("UNKNOWN"))  # unrecognized SS3 (\x1bO<x>, x not A/B)
                i += 3
                continue
            events.append(KeyEvent("ESCAPE"))  # a real, standalone Escape keypress
            i += 1
            continue
        if b in (0x0D, 0x0A):
            events.append(KeyEvent("ENTER"))
            i += 1
            continue
        if b == 0x03:
            events.append(KeyEvent("INTERRUPT"))
            i += 1
            continue
        if b == 0x04:
            events.append(KeyEvent("EOF"))
            i += 1
            continue
        if b in (0x7F, 0x08):
            events.append(KeyEvent("BACKSPACE"))
            i += 1
            continue
        if b == 0x2F:  # '/'
            events.append(KeyEvent("SEARCH"))
            i += 1
            continue
        if b < 0x20:
            events.append(KeyEvent("UNKNOWN"))
            i += 1
            continue
        if b < 0x80:
            events.append(KeyEvent("CHAR", chr(b)))
            i += 1
            continue
        length = _utf8_length(b)
        if length is None:
            events.append(KeyEvent("UNKNOWN"))
            i += 1
            continue
        if i + length > n:
            return events, buf[i:]  # multibyte char cut short by this read
        try:
            char = buf[i:i + length].decode("utf-8")
        except UnicodeDecodeError:
            events.append(KeyEvent("UNKNOWN"))
            i += 1
            continue
        events.append(KeyEvent("CHAR", char))
        i += length
    return events, b""


def flush_incomplete(remainder: bytes) -> list[KeyEvent]:
    """Force-resolve a `decode_keys()` remainder the caller has decided is never completing (a
    short read timeout, used by `run_picker` to break the classic bare-Escape-vs-escape-sequence
    ambiguity — a real Escape keypress and the start of `\\x1b[A` are indistinguishable until
    either more bytes arrive or a timeout says they never will). NEVER called by `decode_keys()`
    itself — this is I/O-loop policy, not decoding."""
    if not remainder:
        return []
    if remainder[0] == 0x1B:
        return [KeyEvent("ESCAPE")]
    return [KeyEvent("UNKNOWN")]  # an unrecoverable partial multibyte char at real EOF/timeout


# --------------------------------------------------------- terminal session (AC-26, AC-27)

_ACTIVE_SESSION: "TerminalSession | None" = None
_ALT_SCREEN_ON = "\x1b[?1049h"
_ALT_SCREEN_OFF = "\x1b[?1049l"
_PASTE_MODE_ON = "\x1b[?2004h"
_PASTE_MODE_OFF = "\x1b[?2004l"


def _is_tty(stream) -> bool:
    """`stream.isatty()`, degrading to `False` for anything that cannot answer (no `isatty`
    at all, or a closed/invalid stream) rather than raising. Shared by `TerminalSession`
    (gates its ANSI writes on stdOUT, not just the stdIN raw-mode decision — F-05) and
    `_render` (F-05/F-08: no ANSI at all, not even the viewport math, to a non-TTY stdout)."""
    try:
        return bool(stream.isatty())
    except (AttributeError, ValueError, OSError):
        return False


class TerminalSession:
    """Context manager: raw mode + alternate screen + bracketed paste on POSIX TTYs. `__exit__`
    restores via `finally` unconditionally (AC-27) — including when the `with` block raised.
    `SIGTERM`/`SIGHUP` handlers (only installed when the signal exists — `SIGHUP` does not on
    Windows) restore the terminal before letting the process exit, for the abnormal-exit case
    `finally` alone cannot reach (a signal interrupts a syscall, it doesn't raise a Python
    exception the `with` block would see).

    On `win32` (no `termios`) this degrades to registering `_ACTIVE_SESSION` only — `msvcrt`'s
    key-reading primitives don't require a raw/cooked mode toggle the way POSIX ttys do, so
    there is nothing to save/restore there; `suspended()` is correspondingly a no-op on win32.
    """

    def __init__(self, *, stdin=None, stdout=None):
        self._stdin = stdin if stdin is not None else sys.stdin
        self._stdout = stdout if stdout is not None else sys.stdout
        self._original_attrs = None
        self._raw = False
        self._prev_handlers: dict[int, object] = {}

    def _is_tty(self) -> bool:
        return _is_tty(self._stdin)

    def _write(self, text: str) -> None:
        # F-05: the raw-mode DECISION stays on stdin (that's where it belongs — it governs
        # whether reading keys needs raw mode at all) but every byte this session writes is
        # ANSI meant for a terminal, so it must never reach a non-TTY stdout (`set-agents |
        # tee log.txt` from a real terminal has a tty stdin — the picker starts — and a piped
        # stdout; without this gate the alternate-screen/paste-mode/redraw bytes land in the
        # pipe on every redraw).
        if not _is_tty(self._stdout):
            return
        try:
            self._stdout.write(text)
            self._stdout.flush()
        except (OSError, ValueError):
            pass

    def _enter_raw(self) -> None:
        if termios is None or tty is None or not self._is_tty():
            return
        fd = self._stdin.fileno()
        self._original_attrs = termios.tcgetattr(fd)
        tty.setraw(fd)
        self._raw = True
        self._write(_ALT_SCREEN_ON)
        self._write(_PASTE_MODE_ON)

    def _restore(self) -> None:
        if not self._raw:
            return
        try:
            fd = self._stdin.fileno()
            termios.tcsetattr(fd, termios.TCSADRAIN, self._original_attrs)
        except (OSError, ValueError, AttributeError):
            pass
        self._write(_PASTE_MODE_OFF)
        self._write(_ALT_SCREEN_OFF)
        self._raw = False

    def _handle_signal(self, signum, frame):  # pragma: no cover - real delivery not exercised
        """Invoked either by a real signal delivery, or DIRECTLY by a test (never via
        `os.kill` against the test process — see tests/test_harness.py). Restores the
        terminal, then exits with the conventional 128+signum status instead of re-raising
        the signal at the OS level, which would need a real `os.kill` round-trip to reproduce
        the platform's default terminating behavior and is not something a hermetic test can
        safely trigger against its own process."""
        self._restore()
        raise SystemExit(128 + signum)

    def __enter__(self) -> "TerminalSession":
        global _ACTIVE_SESSION
        # F-06: if anything between entering raw mode and finishing signal-handler
        # installation raises (e.g. `signal.signal()` off the main thread), `__enter__`
        # never completes -- Python then never calls `__exit__` for a `with` whose `__enter__`
        # raised, so without this the terminal would stay in raw mode with no handler
        # installed at all. Restore and re-raise instead of leaving that half-entered state.
        try:
            self._enter_raw()
            for name in ("SIGTERM", "SIGHUP"):
                sig = getattr(signal, name, None)
                if sig is not None:
                    self._prev_handlers[sig] = signal.getsignal(sig)
                    signal.signal(sig, self._handle_signal)
        except BaseException:
            self._restore()
            for sig, handler in self._prev_handlers.items():
                # D-06: if the SAME reason the original `signal.signal()` call above failed
                # (e.g. running off the main thread) also makes THIS restore call fail, an
                # uncaught exception here would replace the original one being handled --
                # Python then chains "During handling of the above exception, another
                # exception occurred", masking the real cause behind a confusing traceback.
                # The terminal is already restored by `self._restore()` above regardless.
                with contextlib.suppress(ValueError):
                    signal.signal(sig, handler)
            self._prev_handlers = {}
            raise
        _ACTIVE_SESSION = self
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        global _ACTIVE_SESSION
        try:
            self._restore()
        finally:
            for sig, handler in self._prev_handlers.items():
                signal.signal(sig, handler)
            self._prev_handlers = {}
            if _ACTIVE_SESSION is self:
                _ACTIVE_SESSION = None
        return False  # never swallow an exception raised inside the `with` block

    @contextlib.contextmanager
    def suspended(self):
        """Exit raw mode/alternate screen for the duration of the block (an in-process prompt:
        `input()` doesn't echo under raw mode, and unreadable consent is not consent — AC-26),
        then re-enter. A no-op nested nicely if the session was never actually raw (e.g. stdin
        isn't a tty, or we're on win32) — never double-restores, never leaves raw mode entered an
        extra time."""
        was_raw = self._raw
        if was_raw:
            self._restore()
        try:
            yield
        finally:
            if was_raw:
                self._enter_raw()


def suspend_terminal():
    """No-op context manager when no `TerminalSession` is active (a bare CLI invocation, e.g.
    `set-agents --tools-install NAME` outside the picker); otherwise delegates to the active
    session's `.suspended()`. This is what lets `cmd_tools_install`'s sudo confirmation and
    `mcp_menu`'s free-text prompts use the exact same `input()` call regardless of whether they
    were reached from the CLI directly or from inside the picker (AC-26) — no need to fork them
    into two versions."""
    if _ACTIVE_SESSION is None:
        return contextlib.nullcontext()
    return _ACTIVE_SESSION.suspended()


# ------------------------------------------------------------ progress / spinner (AC-04, AC-05)
#
# 025/D2: any operation over ~300ms says so. This NEVER writes to stdout -- stdout is the
# machine channel (`--json` envelopes, `install.py --preview`'s MANAGED_DIFF_FILES= that
# `check-drift.sh` parses with `sed`); every byte here targets `stream`, which callers pass
# as `sys.stderr`. `use_color()` (set_agents_app.py) asks `sys.stdout.isatty()` -- the wrong
# stream for something that writes to stderr -- so this module owns its own predicate instead
# of reusing it.

def supports_progress(stream) -> bool:
    """True when `stream` can safely carry an animated, `\\r`-redrawing indicator: a real TTY
    on THAT stream (reuses `_is_tty`, not a rewrite -- see its docstring: degrades to `False`
    for anything that can't answer `isatty()` instead of raising), and no explicit request to
    degrade. `NO_COLOR` and `TERM=dumb` are the same two escape hatches `use_color()` honors
    for stdout color, checked here independently because they must gate a DIFFERENT stream."""
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("TERM") == "dumb":
        return False
    return _is_tty(stream)


_SPINNER_FRAMES = "|/-\\"
_SPINNER_INTERVAL_SECONDS = 0.1


def with_progress(message, fn, *, stream=None, final=None):
    """Run `fn()` (no arguments) while telling `stream` (default `sys.stderr` -- NEVER
    stdout) that work is happening, for operations that can take seconds (AC-04: routing
    probes, `--doctor-all`, `--route-doctor`, all measured over the ~300ms threshold in
    the D2 context pack).

    Live mode (`supports_progress(stream)`): a background thread redraws a `\\r`-prefixed
    spinner frame every `_SPINNER_INTERVAL_SECONDS`. Degraded mode (no TTY, `NO_COLOR`,
    `TERM=dumb`, or any stream that can't answer `isatty()`): one static line, no `\\r`, no
    ANSI -- printed once, not touched again until the final line.

    AC-05, "never the only indicator": when `fn()` returns, a PERSISTENT line is always
    written to `stream` -- `final(result)` if given, else a plain "<message>: listo"
    fallback -- in BOTH modes. If `fn()` raises, the spinner is still stopped and the
    spinner line cleared (the `finally` below) before the exception propagates, but no
    final line is written for a result that doesn't exist; the caller's own error path is
    what informs the user in that case.

    AC-05, "never blocks input": the spinner thread is always joined (bounded 1s timeout,
    matching this module's other terminal-restore joins) BEFORE `with_progress` returns,
    so nothing here can still be writing when a caller immediately follows with an
    `input()`/`tui.suspend_terminal()` prompt."""
    stream = stream if stream is not None else sys.stderr
    live = supports_progress(stream)
    stop_event = threading.Event()
    thread = None

    def _write(text):
        try:
            stream.write(text)
            stream.flush()
        except (OSError, ValueError):
            pass

    if live:
        def _spin():
            i = 0
            while not stop_event.wait(_SPINNER_INTERVAL_SECONDS):
                frame = _SPINNER_FRAMES[i % len(_SPINNER_FRAMES)]
                _write(f"\r{frame} {message}…")
                i += 1
        thread = threading.Thread(target=_spin, daemon=True)
        thread.start()
    else:
        _write(f"· {message}…\n")

    try:
        result = fn()
    finally:
        if thread is not None:
            stop_event.set()
            thread.join(timeout=1.0)
            _write("\r" + " " * (len(message) + 4) + "\r")

    _write((final(result) if final is not None else f"{message}: listo") + "\n")
    return result


# --------------------------------------------------------------------------- render loop

_IDENTITY_STYLE = {
    "color": lambda text, code: text,
    "bold": lambda text: text,
    "dim": lambda text: text,
}

_ESC_TIMEOUT_SECONDS = 0.05


def _read_chunk_posix(stdin, timeout):
    """`None` result means "timed out, no bytes yet" (still open); `b""` means real EOF."""
    try:
        fd = stdin.fileno()
    except (AttributeError, OSError, ValueError):
        return b""
    try:
        ready, _, _ = select.select([fd], [], [], timeout)
    except (OSError, ValueError):
        return b""
    if not ready:
        return None
    try:
        return os.read(fd, 4096)
    except OSError:
        return b""


_WIN32_SCANCODE_MAP = {
    b"H": "UP", b"P": "DOWN",  # arrow keys arrive as a two-call sequence: \x00/\xe0 then this
}


def _read_key_win32() -> KeyEvent | None:  # pragma: no cover - exercised only on native Windows
    """Best-effort (DEC-7c): translates `msvcrt` key reads directly into the same `KeyEvent`
    vocabulary `decode_keys()` produces, without attempting to reuse `decode_keys()` itself —
    Windows console scancodes are a different wire format from POSIX terminal escape sequences,
    not a variant of the same one. Returns `None` when no key is waiting."""
    if msvcrt is None or not msvcrt.kbhit():
        return None
    ch = msvcrt.getwch()
    if ch in ("\x00", "\xe0"):  # arrow/function-key prefix; the real code follows
        code = msvcrt.getwch()
        kind = _WIN32_SCANCODE_MAP.get(code.encode("latin-1", "ignore"))
        return KeyEvent(kind) if kind else KeyEvent("UNKNOWN")
    if ch in ("\r", "\n"):
        return KeyEvent("ENTER")
    if ch == "\x1b":
        return KeyEvent("ESCAPE")
    if ch == "\x03":
        return KeyEvent("INTERRUPT")
    if ch in ("\x08", "\x7f"):
        return KeyEvent("BACKSPACE")
    if ch == "/":
        return KeyEvent("SEARCH")
    if ch == "":
        return KeyEvent("EOF")
    if ch >= " ":
        return KeyEvent("CHAR", ch)
    return KeyEvent("UNKNOWN")


_FALLBACK_VIEWPORT_ROWS = 24  # used only when the real terminal height cannot be read at all


def _terminal_rows(stdout) -> int:
    """Best-effort terminal height for the viewport clamp (F-08). Falls back to a named
    constant — never crashes — when `stdout` has no real fd behind it (a pipe, a StringIO in
    tests, `get_terminal_size` failing with ENOTTY, ...)."""
    try:
        return os.get_terminal_size(stdout.fileno()).lines
    except (AttributeError, OSError, ValueError):
        return _FALLBACK_VIEWPORT_ROWS


def _viewport_slice(cursor: int, total: int, rows: int) -> tuple[int, int]:
    """Which `[start, end)` half-open range of item indices to actually render so the visible
    window never exceeds `rows` lines and ALWAYS contains `cursor` (F-08) — without this, a
    catalog longer than the terminal (plugins, the MCP catalog, `opencode models`) pushes the
    cursor and most of the list off-screen with no way to see where you are."""
    if rows <= 0 or total <= rows:
        return 0, total
    start = max(0, min(cursor - rows // 2, total - rows))
    return start, start + rows


def _render_items(lines: list[str], style, cursor: int, indices: tuple[int, ...], items: tuple[str, ...], rows_available: int) -> None:
    """Append the visible, viewport-clamped rows for `indices` (either every item, in
    `navigate`, or only the F-08 search matches) to `lines`. `cursor` is always an index into
    `items` (never into `indices` itself) -- shared by both modes so the same marker/bold-
    current-row logic and the same `_viewport_slice` clamp apply to both."""
    bold = style["bold"]
    total = len(indices)
    local_cursor = indices.index(cursor) if cursor in indices else 0
    start, end = _viewport_slice(local_cursor, total, rows_available)
    for position in range(start, end):
        index = indices[position]
        item = items[index]
        marker = "›" if index == cursor else " "
        text = bold(item) if index == cursor else item
        lines.append(f"{marker} {text}")


def _clamp_prefix(prefix: list[str], rows: int, *, min_trailer: int) -> list[str]:
    """D-03: truncate the caller's `header`/`prompt` prefix so the frame's LAST lines (the
    cursor/query row and the hint line, `min_trailer` of them) always fit inside `rows` -- an
    unclamped header taller than the terminal (e.g. `mcp_menu`'s one-line-per-server catalog
    table on a split pane) used to make `max(rows - reserved, 1)` silently give up, scrolling
    the cursor and the hint off-screen -- exactly the original F-08 failure mode, reopened
    through the header instead of the item list. `min_trailer` is mode-specific: `navigate`
    only ever appends 1 hint line below its (always >= 1 row) item viewport, but `search`/
    `freetext` ALSO have their own fixed `> query` row above that, so they need one more line
    of headroom than `navigate` does to guarantee the same "cursor/hint never scrolls off"
    property."""
    max_prefix = max(rows - min_trailer, 0)
    return prefix[:max_prefix] if len(prefix) > max_prefix else prefix


def _render(stdout, state: PickerState, style, prompt=None, header=None) -> None:
    # F-05: never write ANSI (not even the viewport arithmetic below has any point) to a
    # stdout that isn't a real terminal -- see `TerminalSession._write`'s docstring for why.
    if not _is_tty(stdout):
        return
    bold, dim = style["bold"], style["dim"]
    rows = _terminal_rows(stdout)

    prefix: list[str] = []
    if header:
        # F-03: the caller's decision context (MCP/status tables, the vault intro line, the
        # drift/update banner) rendered INSIDE this picker's own frame, so it survives every
        # redraw instead of being printed to the normal screen and erased the instant the
        # alternate screen takes over -- exactly when the user needs it to decide.
        prefix.extend(str(header).splitlines())
        prefix.append("")
    if prompt:
        prefix.append(bold(prompt))
    # D-03: `navigate` always appends exactly 1 trailer line (the hint) below its own
    # (always >= 1 row) item viewport; `search`/`freetext` ALSO have a fixed `> query` row
    # before that, one more line of guaranteed trailer than `navigate` has.
    min_trailer = 2 if state.mode == "navigate" else 3 if state.mode == "search" else 2
    lines = _clamp_prefix(prefix, rows, min_trailer=min_trailer)  # never push cursor/hint off-screen

    if state.mode == "navigate":
        reserved = len(lines) + 1  # + the hint line appended after the items below
        viewport = max(rows - reserved, 1)
        _render_items(lines, style, state.cursor, tuple(range(len(state.items))), state.items, viewport)
        if not state.items:
            lines.append(dim("(sin opciones)"))
        hint = "↑↓ mover · Enter elegir · Esc cancelar"
        if state.freetext_allowed or state.items:
            hint += " · / buscar"
        lines.append(dim(hint))
    elif state.mode == "search":
        # F-08: `/` now filters the visible list by substring/casefold of `query` instead of
        # requiring the item's exact name typed from memory -- navigable with arrows exactly
        # like `navigate`; Enter selects whichever match is highlighted (see `reduce()`).
        lines.append(f"{dim('>')} {state.query}")
        reserved = len(lines) + 1
        viewport = max(rows - reserved, 1)
        matches = _search_matches(state.items, state.query)
        if matches:
            _render_items(lines, style, state.cursor, matches, state.items, viewport)
        elif state.items:
            lines.append(dim("(sin coincidencias)"))
        if state.freetext_allowed:
            hint = "↑↓ mover · Enter elegir · Esc vuelve · sin coincidencia = texto libre"
        else:
            hint = "↑↓ mover · Enter elegir · Esc vuelve"
        lines.append(dim(hint))
    else:  # freetext -- bare single-line prompt, no backing item list at all
        lines.append(f"{dim('>')} {state.query}")
        lines.append(dim("Enter acepta · Esc cancela"))

    stdout.write("\x1b[H\x1b[2J")
    stdout.write("\r\n".join(lines) + "\r\n")
    stdout.flush()


def run_picker(items, *, freetext_allowed=False, style=None, stdin=None, stdout=None, stderr=None, prompt=None, header=None):
    """The render loop (layer 4). Returns `Selected(index)` | `FreeText(value)` | `None`
    (cancelled — Esc, Ctrl-C, or EOF). `style` is a dict of `color`/`bold`/`dim` callables
    (defaults to identity/passthrough, per the module docstring, so `tui.py` stays importable
    and runnable standalone without `set_agents_app`). `header` (F-03) is the caller's decision
    context — a table, a banner, an intro line — rendered inside THIS picker's own frame on
    every redraw, so it survives the alternate-screen switch instead of being printed to the
    normal screen right before it and erased.

    Each call is a short-lived, self-contained raw-mode session by default: it enters raw mode/
    alternate screen, runs its own loop, and restores cooked mode again BEFORE returning — a
    caller that immediately follows with `print()`s or a subprocess call (`run_tty()`, `cmd_
    tools_install()`'s confirmations) is already back in normal mode, no explicit hand-off
    needed for those. If a `TerminalSession` is ALREADY active when `run_picker` is called
    (e.g. one picker composing a nested prompt of its own), it reuses that ambient session
    instead of nesting a second raw-mode/alternate-screen/signal-handler setup on top of it —
    a caller chaining several pickers in one interaction (`mcp_menu`, `vault_menu`) can open ONE
    `TerminalSession` up front so none of the chained pickers re-swaps the alternate screen
    (F-03).

    D-02: the raw-mode DECISION stays on `stdin` only (`TerminalSession._enter_raw`'s
    contract), but a real terminal stdin with a PIPED stdout (`set-agents | tee log.txt`) used
    to leave the picker invisible while still fully live -- it kept consuming real keystrokes
    and could resolve a real `Selected(...)` with nobody able to see the cursor, so a blind
    Enter at the default cursor position (`MENU_ITEMS[0]`, "Instalar / Reparar") could launch
    the installer unattended. This falls back to `stderr` (not swallowed by `tee`'s stdout
    redirection) whenever `stdout` is not a TTY but `stderr` is; if literally nothing the
    process can write to is a TTY while stdin still is, it refuses to drive the loop at all
    and resolves to cancelled (`None`) -- exactly like an immediate Esc -- instead of ever
    consuming a keystroke nobody could have seen land.
    """
    stdin = stdin if stdin is not None else sys.stdin
    stdout = stdout if stdout is not None else sys.stdout
    stderr = stderr if stderr is not None else sys.stderr
    render_stdout = stdout if _is_tty(stdout) else (stderr if _is_tty(stderr) else stdout)
    if _is_tty(stdin) and not _is_tty(render_stdout):
        return None
    resolved_style = {**_IDENTITY_STYLE, **(style or {})}
    items = tuple(items)
    initial_mode = "freetext" if not items and freetext_allowed else "navigate"
    state = PickerState(items=items, mode=initial_mode, freetext_allowed=freetext_allowed)

    if _ACTIVE_SESSION is not None:
        state = _drive_loop(state, stdin, render_stdout, resolved_style, prompt, header)
    else:
        with TerminalSession(stdin=stdin, stdout=render_stdout):
            state = _drive_loop(state, stdin, render_stdout, resolved_style, prompt, header)

    if isinstance(state.result, (Selected, FreeText)):
        return state.result
    return None


def _drive_loop(state, stdin, stdout, style, prompt=None, header=None):
    if sys.platform == "win32" and msvcrt is not None:
        return _run_loop_win32(state, stdout, style, prompt, header)
    return _run_loop_posix(state, stdin, stdout, style, prompt, header)


def _run_loop_posix(state, stdin, stdout, style, prompt=None, header=None):
    pending = b""
    while state.result is PENDING:
        _render(stdout, state, style, prompt, header)
        timeout = _ESC_TIMEOUT_SECONDS if pending else None
        chunk = _read_chunk_posix(stdin, timeout)
        if chunk is None:  # timed out waiting -- resolve whatever we were holding back
            events = flush_incomplete(pending)
            pending = b""
        elif chunk == b"":
            # Real fd EOF: no more bytes are EVER coming, so a further read would just
            # return b"" again forever -- flush any incomplete sequence we were still
            # holding (same policy as the timeout branch above) AND surface EOF itself,
            # rather than looping without making progress when `pending` is non-empty.
            events = flush_incomplete(pending) + [KeyEvent("EOF")]
            pending = b""
        else:
            events, pending = decode_keys(pending + chunk)
        for event in events:
            state = reduce(state, event)
            if state.result is not PENDING:
                break
    return state


_WIN32_POLL_SECONDS = 0.05  # F-01: how long the win32 loop backs off between kbhit() polls


def _run_loop_win32(state, stdout, style, prompt=None, header=None):  # pragma: no cover - native Windows only
    """`msvcrt.kbhit()` is non-blocking (unlike POSIX `select()`, there is no fd to block on),
    so this loop must supply its own wait: F-01 was a tight `while: kbhit(); continue` with no
    sleep at all, which pins a CPU core at 100% and, worse, never yields the interpreter long
    enough for the real `windows-bootstrap` CI job (which never sends a key) to do anything but
    spin until its job timeout. Backs off with `time.sleep()` on every empty poll instead, and
    only redraws when a key actually changed the state -- not on every empty poll."""
    _render(stdout, state, style, prompt, header)
    while state.result is PENDING:
        event = _read_key_win32()
        if event is None:
            time.sleep(_WIN32_POLL_SECONDS)
            continue
        state = reduce(state, event)
        if state.result is PENDING:
            _render(stdout, state, style, prompt, header)
    return state
