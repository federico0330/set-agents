"""020-honest-dashboard PKG-2 (ADR-0040, AC-06..AC-11): verifier for the `file:line`
anchors seeded by hand into `docs/modules/*.md`. D-2 of the spec: those anchors "derive
without a net" -- P3 of 019 sowed them, P5 added ~880 lines to the same files, and no
package review could see the drift because each one only looked at its own diff.

Read-only, never mutates. `check-anchors` is explicitly NOT a gate (spec no-goal): it
warns, it never blocks a phase. `sync-notes` wires it in with the same never-raises
contract as render_notes.py (see `_warn_check_anchors_never_raises` in cli_reporting.py).

Grammar (SC-02, spec-challenge already resolved this -- do not re-litigate):
  1. complete form  -- one backtick token, `basename.ext:N` or `basename.ext:N-M`.
  2. abbreviated form -- a bare `:N`/`:N-M` token, resolved against the LAST file named
     (complete-form OR a bare filename mention) earlier in the SAME list item/paragraph.
     One that cannot resolve this way is reported broken, never silently skipped.

File resolution (SC-01, spec-challenge already resolved this -- do not re-litigate): a
basename is matched ONLY inside the `paths` globs of the module whose doc is being
checked (`docs/modules/modules.toml`, the same glob-expansion idea as
`render_modules.matching_modules`, but expanded against the real files on disk here,
because this module needs to know WHICH files exist, not just whether a given path
string matches a pattern). Zero matches, or more than one, inside that module's own
`paths` is itself a reportable broken anchor -- never a silently-ignored case. This is
what makes two cross-module citations in today's docs (routing.md citing
set_agents_app.py, narracion-notas.md citing cli_reporting.py) impossible to spell as a
checkable anchor: resolving them would require either a global search (explicitly
forbidden -- feature_state_lib/*.py is byte-identical in five trees) or widening one
module's scope into another's (out of scope: this package does not touch modules.toml's
schema or the ADR-0036 partition). AC-10 fixes those two spots by dropping the specific
line number and keeping the prose pointer -- the same "recortá y dejá constancia" posture
AC-08 uses everywhere else in this module.

Semantic check (AC-08, deliberately bounded -- flagged by the spec-challenger as the
likeliest spot for this package to balloon into a disguised project): only when a
backtick symbol is IMMEDIATELY adjacent to a
single-line (non-range) anchor, on the SAME physical line, is the identifier compared as
plain text against a small window of the target file. No Python parsing, ever. Ranges,
wildcarded symbols, and symbols separated from the anchor by prose get resolution + range
checks only, per spec.
"""

from __future__ import annotations

import glob
import re
from pathlib import Path
from typing import Any

from feature_state_lib.model import StateError
from feature_state_lib.render_modules import MODULES_TOML, load_modules_toml


# -- Grammar -----------------------------------------------------------------------
# A plausible source-file token: must end in a short (<=4 char) extension, so bare
# words/URLs/timestamps never qualify (see the false positives below) and so a dotted
# Python reference like `cli_reporting.cmd_digest` (extension "cmd_digest", 10 chars)
# is never mistaken for a filename either.
_FILE_RE_PART = r"[A-Za-z0-9_][A-Za-z0-9_./-]*\.[A-Za-z0-9]{1,4}"
COMPLETE_TOKEN_RE = re.compile(rf"^({_FILE_RE_PART}):(\d+)(-(\d+))?$")
ABBREV_TOKEN_RE = re.compile(r"^:(\d+)(-(\d+))?$")
BARE_FILENAME_RE = re.compile(rf"^{_FILE_RE_PART}$")
BACKTICK_TOKEN_RE = re.compile(r"`([^`\n]*)`")
# AC-08: identifier optionally followed by a call's parens, immediately after an
# anchor's closing backtick, separated by nothing but horizontal whitespace. No `^`
# here on purpose -- `re.Pattern.match(string, pos)` already anchors at `pos`; a literal
# `^` would instead demand position 0 of the whole line (see Python docs on `pos`), not
# "right where the anchor ended".
_SYMBOL_RE = re.compile(r"[ \t]*`([A-Za-z_][A-Za-z0-9_]*)(?:\([^)]*\))?`")
# Real false positives from this repo's own docs, tested in both directions (SC-02):
# `localhost:8080` (no dot in the file part), `12:30` (same), `http://x:80` (no dot
# anywhere before the colon), a bare range `10-20` (no colon at all, and ABBREV requires
# the token to START with one). None of the three regexes above can match any of them --
# see tests/test_check_anchors.py for the adversarial doc that pins this both ways.

SEMANTIC_WINDOW = 2  # "ventana chica" (AC-08): tolerate a couple of lines' slack


class AnchorCheckError(StateError):
    """A malformed docs/modules/modules.toml or an unknown --module -- same fail-closed
    posture as render_modules.ModulesTomlError, surfaced through the CLI's normal
    StateError handling."""


def _expand_module_files(repo_root: Path, patterns: list[str]) -> dict[str, list[str]]:
    """Real files on disk matching this module's own `paths` globs, indexed by
    basename. fnmatch (what render_modules.matching_modules uses) answers "does this
    known path match that pattern"; this answers the opposite question -- "what files
    actually exist under that pattern" -- which is what basename resolution needs.
    `glob.glob(..., recursive=True)` for a globbed pattern, a direct is_file() check for
    a literal path (modules.toml also allows non-glob single-file entries); `__pycache__`
    is always excluded, directories are never indexed (only real files can host anchors).
    """
    index: dict[str, list[str]] = {}
    seen: set[str] = set()
    for pattern in patterns:
        if any(ch in pattern for ch in "*?["):
            matches = glob.glob(pattern, root_dir=str(repo_root), recursive=True)
        else:
            matches = [pattern] if (repo_root / pattern).is_file() else []
        for rel in matches:
            rel = rel.rstrip("/")
            if "__pycache__" in Path(rel).parts:
                continue
            if rel in seen or not (repo_root / rel).is_file():
                continue
            seen.add(rel)
            index.setdefault(Path(rel).name, []).append(rel)
    return index


def _resolve_basename(file_index: dict[str, list[str]], token: str) -> tuple[str | None, str | None]:
    """SC-01: basename-only resolution, scoped to the caller's already-expanded module
    file index. Zero or more-than-one match is itself the broken-anchor reason, never a
    silently ignored case."""
    base = token.rsplit("/", 1)[-1]
    matches = file_index.get(base, [])
    if len(matches) == 1:
        return matches[0], None
    if not matches:
        # F-01 (P2 repair, static hint -- no global search, that would violate SC-01):
        # this reason fires for two very different causes that look identical from here
        # -- (a) the file genuinely does not exist anywhere, and (b) the file exists but
        # is owned by a DIFFERENT module, i.e. a cross-module citation, which SC-01 makes
        # unresolvable by design (see ADR-0040 sect. 5 and the module docstring above).
        # We cannot tell which one it is without a global search, so the message names
        # both possibilities instead of guessing.
        return None, (
            f"no file named {base!r} inside this module's declared paths (modules.toml) "
            "-- if this file exists but belongs to a DIFFERENT module, this is a "
            "cross-module citation, unresolvable by design (SC-01, see ADR-0040 sect. 5): "
            "drop the line number and name the owning module in prose instead, as AC-10 "
            "did for the two real cases in today's docs"
        )
    return None, f"ambiguous basename {base!r}: {len(matches)} files inside this module's declared paths"


def _adjacent_symbol(line: str, pos: int) -> str | None:
    """F-02 (P2 repair): "adjacent" means ONLY horizontal whitespace between the anchor's
    closing backtick and this symbol's opening backtick -- a connector word, a verb, or
    even a comma right there silently turns AC-08's semantic check off (resolution+range
    checks still run, but the identifier is never compared). Concrete, measured case: in
    "`foo.py:8` es `alpha()`", `pos` lands right after `:8` `'s closing backtick, on the
    space before "es"; `_SYMBOL_RE` needs a backtick immediately after that (only) space,
    finds the letter "e" instead, and never matches -- so this returns None and the claim
    passes (`ok=True`) even when line 8 is genuinely `beta`, not `alpha`. Measured on this
    repo's own docs/modules/*.md (P2 repair evidence, ADR-0040 sect. 5): only 12 of 38
    anchors (32%) have an active semantic check today; the other 26 read fine to a human
    but are never compared against the target line's real content.
    """
    m = _SYMBOL_RE.match(line, pos)
    return m.group(1) if m else None


def _semantic_check(repo_root: Path, rel_path: str, line_no: int, symbol: str) -> tuple[bool, str]:
    abs_path = repo_root / rel_path
    try:
        lines = abs_path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError as exc:
        return False, f"cannot read {rel_path} to verify symbol {symbol!r}: {exc}"
    total = len(lines)
    lo = max(1, line_no - SEMANTIC_WINDOW)
    hi = min(total, line_no + SEMANTIC_WINDOW)
    window_text = "\n".join(lines[lo - 1:hi])
    if re.search(rf"\b{re.escape(symbol)}\b", window_text):
        return True, ""
    return False, f"symbol {symbol!r} not found near {rel_path}:{line_no} (checked lines {lo}-{hi})"


def _build_entry(
    repo_root: Path, doc: str, lineno: int, token: str, form: str,
    resolved: str | None, resolve_err: str | None,
    line_s: str, end_s: str | None, raw_line: str, end_pos: int,
) -> dict[str, Any]:
    entry: dict[str, Any] = {"doc": doc, "line": lineno, "raw": f"`{token}`", "form": form}
    if resolved is None:
        entry["ok"] = False
        entry["reason"] = resolve_err or "unresolvable file reference"
        return entry
    target_start = int(line_s)
    target_end = int(end_s) if end_s else target_start
    abs_path = repo_root / resolved
    try:
        total = len(abs_path.read_text(encoding="utf-8", errors="replace").splitlines())
    except OSError as exc:
        entry["ok"] = False
        entry["reason"] = f"cannot read {resolved}: {exc}"
        return entry
    entry["resolved"] = resolved
    if target_start < 1 or target_end > total or target_start > target_end:
        span = f"{target_start}-{target_end}" if end_s else str(target_start)
        entry["ok"] = False
        entry["reason"] = f"line {span} out of range for {resolved} ({total} lines)"
        return entry
    if end_s is None:  # AC-08: ranges never get the semantic check, resolution+range only
        symbol = _adjacent_symbol(raw_line, end_pos)
        if symbol:
            entry["symbol"] = symbol
            ok, reason = _semantic_check(repo_root, resolved, target_start, symbol)
            if not ok:
                entry["ok"] = False
                entry["reason"] = reason
                return entry
    entry["ok"] = True
    return entry


def _scan_doc(repo_root: Path, doc_path: Path, file_index: dict[str, list[str]], doc_label: str) -> list[dict[str, Any]]:
    """One pass, left to right, top to bottom. `last_file` is the real resolved relative
    path of the most recently named file (complete-form anchor OR a bare filename
    mention) -- reset at every blank line, heading, or new list-item bullet, because
    SC-02 scopes abbreviated resolution to "the same list item or paragraph", never
    across one."""
    text = doc_path.read_text(encoding="utf-8")
    results: list[dict[str, Any]] = []
    last_file: str | None = None
    for lineno, raw_line in enumerate(text.splitlines(), start=1):
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            last_file = None
            continue
        if raw_line.lstrip().startswith("- "):
            last_file = None
        for m in BACKTICK_TOKEN_RE.finditer(raw_line):
            token = m.group(1)
            end_pos = m.end()
            cm = COMPLETE_TOKEN_RE.match(token)
            if cm:
                file_token, line_s, _, end_s = cm.groups()
                resolved, err = _resolve_basename(file_index, file_token)
                entry = _build_entry(repo_root, doc_label, lineno, token, "complete",
                                      resolved, err, line_s, end_s, raw_line, end_pos)
                results.append(entry)
                last_file = resolved
                continue
            am = ABBREV_TOKEN_RE.match(token)
            if am:
                line_s, _, end_s = am.groups()
                if last_file is None:
                    results.append({
                        "doc": doc_label, "line": lineno, "raw": f"`{token}`", "form": "abbreviated",
                        "ok": False,
                        "reason": "unresolvable: no file named earlier in this list item/paragraph",
                    })
                else:
                    entry = _build_entry(repo_root, doc_label, lineno, token, "abbreviated",
                                          last_file, None, line_s, end_s, raw_line, end_pos)
                    results.append(entry)
                continue
            if BARE_FILENAME_RE.match(token):
                resolved, _err = _resolve_basename(file_index, token)
                last_file = resolved  # opportunistic: a bare mention that fails to
                # resolve simply leaves no context (fail-closed), surfacing at the next
                # abbreviated anchor that needed it rather than being reported twice.
                continue
            # anything else on the line (a symbol, prose, an unrelated code span) is not
            # one of the two anchor forms -- never reported on its own.
    return results


def check_anchors(repo_root: Path, modules_dir: Path | None = None, only_module: str | None = None) -> dict[str, Any]:
    """Read-only: never writes anything. Same opt-in posture as render_modules -- a repo
    (or a modules_dir override) without modules.toml simply has nothing to check, ok=True."""
    modules_dir = modules_dir or (repo_root / "docs" / "modules")
    toml_path = modules_dir / MODULES_TOML
    modules = load_modules_toml(toml_path)
    if only_module:
        if only_module not in modules:
            raise AnchorCheckError(f"unknown module slug: {only_module!r} (declared in {toml_path})")
        modules = {only_module: modules[only_module]}
    checked_docs: list[str] = []
    all_results: list[dict[str, Any]] = []
    for slug in sorted(modules):
        doc_path = modules_dir / f"{slug}.md"
        if not doc_path.is_file():
            continue
        checked_docs.append(f"{slug}.md")
        file_index = _expand_module_files(repo_root, modules[slug]["paths"])
        all_results += _scan_doc(repo_root, doc_path, file_index, f"docs/modules/{slug}.md")
    broken = [r for r in all_results if not r["ok"]]
    form_counts = {"complete": 0, "abbreviated": 0}
    for r in all_results:
        form_counts[r["form"]] += 1
    return {
        "ok": not broken,
        "checked_docs": checked_docs,
        "anchor_count": len(all_results),
        "form_counts": form_counts,
        "broken": broken,
    }
