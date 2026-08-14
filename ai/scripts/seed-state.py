#!/usr/bin/env python3
"""Populate `ai/state/` from the tracked `ai/state.seed/` skeleton -- ONLY when absent.

ADR-0047: `ai/state/` is gitignored, so a fresh clone starts with no `ai/state/` at
all, not the tracked directory eleven `ai/scripts/` modules read and write. Left
alone, that is a hole shaped like a crash the first time any of them expects
`ai/state/features/` to exist. This script fills the hole with a functional, empty
harness -- no feature, no decision, no narrative entry belongs to whoever cloned
the repo before this ran.

The one invariant that matters more than the feature itself: this never overwrites
a real `ai/state/`. Whether `ai/state/` already exists because this machine has
real history (Federico's, or anyone's), or because a previous run of this exact
script already seeded it, the answer is the same -- do nothing. The guard is
"present or absent", nothing finer: this script does not diff, does not merge,
does not selectively fill in missing files inside an existing tree. That
coarseness is deliberate; anything finer is a second place this could get the
"whose data wins" question wrong.

Usage: seed-state.py <root>
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path


def _present(path: Path) -> bool:
    """True for anything at all at `path` -- file, directory, or broken symlink.

    `Path.exists()` follows symlinks and reports False for a broken one, which
    would read as "absent" for a spot that is very much occupied. `lstat` never
    follows, so a broken symlink still counts as present and the seed still
    refuses to touch it.
    """
    try:
        path.lstat()
    except OSError:
        return False
    return True


def seed_state(root: Path) -> str:
    """Copy `ai/state.seed/` to `ai/state/`, but only into an absent `ai/state/`.

    Returns a status word rather than raising, so a caller (or a test) can branch
    on the outcome without parsing stderr.
    """
    target = root / "ai" / "state"
    source = root / "ai" / "state.seed"
    if _present(target):
        return "STATE_SEED_SKIP_EXISTING"
    if not source.is_dir():
        return "STATE_SEED_SOURCE_MISSING"
    shutil.copytree(source, target)
    return "STATE_SEEDED"


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: seed-state.py <root>", file=sys.stderr)
        return 2
    root = Path(sys.argv[1])
    status = seed_state(root)
    print(status)
    return 0 if status in ("STATE_SEEDED", "STATE_SEED_SKIP_EXISTING") else 1


if __name__ == "__main__":
    raise SystemExit(main())
