"""set-agents: project-root discovery and stable project identity.

Extracted from set_agents_app.py (mechanical, behavior-preserving split). `_routing_store`
stays behind in set_agents_app.py: it reads the mutable module globals `PROJECT_KEY` and
`ROUTING_TEST_ROOT` that only `set_agents_app.main()` ever reassigns (via `global PROJECT_KEY`),
and a static import here would freeze the value at import time instead of tracking it live.

`_PROJECT_KEY_RE`/`_MAX_FEATURE_BYTES` are duplicated here (identical values) rather than
imported back from set_agents_app.py: neither is ever monkeypatched by any test, and a
module-level `import set_agents_app` here would be a genuine circular import that breaks
under `tests/test_harness.py`'s `_import()` helper (a fresh `spec_from_file_location` load
that is never registered in `sys.modules`, so the reverse import can't resolve to the
in-progress module and instead starts a second, doomed top-level exec of set_agents_app.py).
"""

import hashlib
import json
import os
import re
import stat
import sys
import unicodedata
from pathlib import Path

_PROJECT_KEY_RE = re.compile(r"^proj1_[0-9a-f]{32}$")
_MAX_FEATURE_BYTES = 1024 * 1024


def _real_directory(path: Path) -> bool:
    try:
        mode = path.lstat().st_mode
    except OSError:
        return False
    return stat.S_ISDIR(mode) and not stat.S_ISLNK(mode)


def _has_project_marker(path: Path) -> bool:
    return _real_directory(path / "ai") and _real_directory(path / "ai/state") and _real_directory(path / "ai/state/features") or (path / ".git").exists()


def find_project_root(start: Path) -> Path | None:
    """Nearest marker wins; filesystem root is never a project confinement boundary."""
    try:
        begin = start.resolve()
    except OSError:
        return None
    for candidate in (begin, *begin.parents):
        if candidate == candidate.parent:
            break
        if _has_project_marker(candidate):
            return candidate
    return None


def resolve_project_root(start: Path, explicit: str | None = None) -> Path | None:
    requested = explicit if explicit is not None else os.environ.get("SET_AGENTS_PROJECT")
    if requested is not None:
        try:
            candidate = Path(requested).resolve()
        except OSError as exc:
            raise ValueError("invalid project") from exc
        if candidate == candidate.parent or not candidate.is_dir() or not _has_project_marker(candidate):
            raise ValueError("invalid project")
        return candidate
    return find_project_root(start)


def _casefold_project_path(path: Path) -> str:
    value = unicodedata.normalize("NFC", os.path.realpath(path))
    parent, name = os.path.split(value)
    try:
        swapped = "".join(char.swapcase() for char in name)
        if swapped != name and os.lstat(value).st_ino == os.lstat(os.path.join(parent, swapped)).st_ino:
            return value.lower()
    except OSError:
        pass
    if sys.platform in {"darwin", "win32"}:
        return value.lower()
    return value


def _safe_read(path: Path, *, limit: int) -> bytes | None:
    try:
        # A project directory is untrusted.  Reject every non-regular object before
        # opening it (in particular FIFOs, which would otherwise block this CLI), then
        # repeat the regular-file check on the descriptor we actually opened.
        before = path.lstat()
        if stat.S_ISLNK(before.st_mode) or not stat.S_ISREG(before.st_mode):
            return None
        fd = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0))
        with os.fdopen(fd, "rb") as handle:
            opened = os.fstat(handle.fileno())
            if not stat.S_ISREG(opened.st_mode):
                return None
            data = handle.read(limit + 1)
    except OSError:
        return None
    return data if len(data) <= limit else None


class ProjectIdentityError(ValueError):
    """A present identity is malformed or unsafe; never replace it with a path hash."""


def project_key_for(root: Path, *, require_persisted: bool = False) -> str:
    """Read a persistent project identity, or use the documented Git-only fallback.

    A missing state tree is normal for a Git-only project.  A present, unusable
    identity is not: falling back in that case would silently split its history.
    """
    state = root / "ai/state"
    identity = state / "project.json"
    try:
        identity.lstat()
    except FileNotFoundError:
        pass
    except OSError as exc:
        raise ProjectIdentityError("invalid project identity") from exc
    else:
        raw = _safe_read(identity, limit=_MAX_FEATURE_BYTES)
        try:
            doc = json.loads(raw.decode("utf-8")) if raw is not None else None
        except (UnicodeDecodeError, ValueError):
            doc = None
        if (not isinstance(doc, dict) or doc.get("schema") != 1 or not _PROJECT_KEY_RE.fullmatch(doc.get("project_key", ""))
                or not isinstance(doc.get("created_at"), str)):
            raise ProjectIdentityError("invalid project identity")
        return doc["project_key"]
    if require_persisted:
        raise ValueError("missing project identity")
    digest = hashlib.sha256(b"set-agents-project-v1\0" + _casefold_project_path(root).encode("utf-8", "surrogateescape")).hexdigest()[:32]
    return "proj1_" + digest
