"""Git tree-hash freeze/re-derive for the RDD-inspired `candidate_identity`
(docs/adr/0020-*.md and siblings). Concept ported from gentle-ai's
`internal/reviewtransaction/snapshot.go`, simplified: SET-AGENTES's package
workflow already commits one verified step at a time (see the harness's own
commit discipline), so the freeze always resolves two committed refs via
`git rev-parse <ref>^{tree}` -- never a temporary index over an uncommitted
worktree, which is the harder problem gentle-ai's version also solves. If a
caller wants to freeze uncommitted work, it must commit first.
"""

from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path
from typing import Any

from feature_state_lib.model import StateError

# Same budget and fail-open-with-reason posture as cli_repair.py's `_git_answer`
# (SEC-003): a hung git process must not hang the whole CLI, and a caller needs
# to know WHY a lookup failed, not just that it did.
GIT_TIMEOUT_SECONDS = 10


def _git(args: list[str]) -> tuple[str | None, str | None]:
    try:
        proc = subprocess.run(["git", *args], cwd=Path.cwd(), capture_output=True, text=True,
                              check=False, timeout=GIT_TIMEOUT_SECONDS)
    except OSError:
        return None, "git-unavailable"
    except subprocess.TimeoutExpired:
        return None, "git-unavailable"
    if proc.returncode != 0:
        return None, (proc.stderr or "git-error").strip()
    return proc.stdout, None


def _resolve_tree(ref: str) -> str:
    """The tree object ID a ref points at -- unlike a commit sha, this changes
    only when the ref's CONTENT changes, never on an amend that reproduces the
    same tree or a merge that doesn't touch these paths."""
    out, reason = _git(["rev-parse", f"{ref}^{{tree}}"])
    if out is None:
        raise StateError(f"cannot resolve tree for ref {ref!r}: {reason}")
    return out.strip()


def _changed_paths(base_tree: str, candidate_tree: str) -> list[str]:
    out, reason = _git(["diff", "--name-only", base_tree, candidate_tree])
    if out is None:
        raise StateError(f"cannot diff {base_tree}..{candidate_tree}: {reason}")
    return sorted(line for line in out.splitlines() if line)


def _changed_lines(base_tree: str, candidate_tree: str) -> int:
    """Sum of insertions+deletions from `--numstat`. Binary entries report `-`
    for both counts (not a number) -- they contribute 0 rather than raising,
    since a line-count ceiling has nothing meaningful to say about a binary."""
    out, reason = _git(["diff", "--numstat", base_tree, candidate_tree])
    if out is None:
        raise StateError(f"cannot diff {base_tree}..{candidate_tree}: {reason}")
    total = 0
    for line in out.splitlines():
        if not line:
            continue
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        added, removed = parts[0], parts[1]
        if added.isdigit():
            total += int(added)
        if removed.isdigit():
            total += int(removed)
    return total


def _paths_digest(paths: list[str]) -> str:
    return "sha256:" + hashlib.sha256("\n".join(paths).encode()).hexdigest()


def freeze(baseline_ref: str, candidate_ref: str = "HEAD") -> dict[str, Any]:
    """Resolve and hash the two refs. Does not mutate the repository (no
    write-tree, no index touch, no ref creation) -- both trees already exist
    as committed objects; this only reads them.
    """
    base_tree = _resolve_tree(baseline_ref)
    candidate_tree = _resolve_tree(candidate_ref)
    paths = _changed_paths(base_tree, candidate_tree)
    return {
        "baseline_ref": baseline_ref,
        "candidate_ref": candidate_ref,
        "base_tree": base_tree,
        "candidate_tree": candidate_tree,
        "paths_digest": _paths_digest(paths),
        "changed_lines": _changed_lines(base_tree, candidate_tree),
    }


def rederive_and_compare(frozen: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
    """Recompute the freeze from `frozen`'s own recorded refs and bit-for-bit
    compare `base_tree`/`candidate_tree`/`paths_digest` against the stored
    values. This is what makes a later gate (record-receipt, the future
    integration hook) never trust a stored boolean -- it re-derives live,
    every time, the same posture gentle-ai's `validateDerivedGate` uses.

    Returns `(matches, fresh)` -- `fresh` is always the live recomputation, so
    a caller reporting a mismatch can show exactly which field diverged and
    from what to what, rather than a bare "invalid" verdict.
    """
    fresh = freeze(frozen["baseline_ref"], frozen.get("candidate_ref", "HEAD"))
    matches = all(
        fresh[field] == frozen.get(field) for field in ("base_tree", "candidate_tree", "paths_digest")
    )
    return matches, fresh
