#!/usr/bin/env python3
"""Fail when a feature reached package delivery without a state file.

`feature-state.py init` is a manual orchestrator step with no gate behind it, so
delivering a whole feature outside the state machine costs nothing and produces no
signal at all.  `006-execution-graph` shipped complete -- spec, ADR-0009, code, a
concurrent review panel, refutation, two delta reviews, a final audit, 12 commits,
209 green tests -- and `ai/state/features/` does not contain it.  `STATUS.md` does
not list it and never will.

The signal is the git history, not the file system, and that is a measurement rather
than a preference: 006 left no `evidence/`, no `context/` and no `bitacora.md`, so a
gate keyed on delivery artefacts would report green on the one case it exists to
catch.  `bitacora.md` is worse than useless here -- `feature-state.py` renders it
*from* the state file, so it can only exist once the thing being checked already
does.  Commits are the one trace that delivering produces and drafting does not:
`Feature 006 P2-finding-verification: ...` versus `Feature 005 portable-harness:
contract 1.1.0 approved`.

That is also how the pre-approval lifecycle is protected.  A spec is legitimately
written and revised during SPEC_DRAFT and SPEC_CHALLENGE, before the state file is
supposed to exist, and a guard that reports violations that are not violations gets
disabled.  Requiring a package token means the quiet period is quiet **by
construction**, not by an exception someone has to remember.

Deliberately not distributed to scaffolded projects (`sync-project.sh` does not list
it): a project has its own commit conventions, and this one would misfire there.

ADR-0047 changed the question this asks, without touching what it protects. `ai/state/`
is gitignored now and reseeded empty per clone/machine (`ai/state.seed/`,
`ai/scripts/seed-state.py`); the git history is not gitignored, and the 23 features
already delivered before that move stay in it forever. Read against the WHOLE history,
this guard would see 23 delivery commits with no matching (freshly empty)
`ai/state/features/*.json` and misreport every one of them on the very first `verify.sh`
a fresh clone ever runs -- 23 false positives for work the clone's owner never touched.
`baseline_sha()` anchors the question at "since ai/state.seed/ started existing" (the
commit that performed the move): history at or before it is already accounted for
in `docs/historia/estado-2026-08/`, which this guard does not read either; only commits
strictly after it are ever checked, exactly the ones a fresh clone's own future work
would add. The degraded case stays as loud as the pre-existing shallow-clone one: an
anchor this guard cannot find is announced (`FEATURE_STATE_UNCHECKED
reason=baseline-unknown`), never silently swapped back to full-history scanning.

One case is not degraded: `ai/state.seed/` present on disk but not in any commit yet
is the move itself, mid-flight -- this very repository's own state while the ADR-0047
package was implemented (proven the hard way: `test_guest_copy_scaffolds_and_verifies_portably`,
a full filesystem copy of an uncommitted checkout, failed on exactly this before the
fallback existed). Nothing can be "after" a commit that has not been made yet, so
that window is empty on purpose, not unusable.

Usage: check-feature-state.py <root>
"""

from __future__ import annotations

import hashlib
import re
import subprocess
import sys
from pathlib import Path

# `Feature 006 P2-finding-verification: ...` -- the package token must follow the
# feature number immediately, and the whole shape is declared, not inferred:
# `Global/_canonical/commands/feature-batch.md` states it and names this script as its
# enforcer.  Two earlier drafts of this regex were wrong in ways real history proves:
#   * without IGNORECASE, `feature 006 P2: ...` slips past the gate entirely;
#   * with the token searched anywhere in the subject, `Feature 005: handoff document
#     for continuing P1 in OpenCode` and `Feature 004 T-300 spike: P3-pi-lane
#     feasibility verified` both classify as deliveries, and a draft naming `P95` or
#     `P001` would fire the gate during SPEC_DRAFT -- the exact thing AC-06 forbids.
DELIVERY_SUBJECT = re.compile(r"^Feature\s+0*(\d+)\s+P(\d+)\b", re.IGNORECASE)
# `006-execution-graph` -> 6.  Compared as numbers so a zero-padding change cannot
# quietly stop the guard from recognising its own feature.
FEATURE_ID_NUMBER = re.compile(r"^0*(\d+)\b")

# Every waiver carries its reason and names what settles it.  A waiver without a
# reason is a hole, not a waiver; one whose reason is wrong is worse, because it
# reads as settled.
#
# `006-execution-graph` was waived here from 2026-07-28 until 006-P3-graph-view's
# `init` (2026-07-30): P1/P2 shipped outside the state machine and were never
# backfilled (AC-07 of docs/specs/009-self-application/spec.md:129-132), but P3 is
# tracked from its own first event, so `ai/state/features/006-execution-graph.json`
# now exists and the waiver is retired -- not deleted history, the decision
# `feature-006-delivered-outside-state-machine` in ai/state/decisions-log.jsonl still
# explains why P1/P2 never got one.
WAIVED = {}


def git(root: Path, *args: str) -> str | None:
    """Run a read-only git command, or None when git cannot answer."""
    try:
        proc = subprocess.run(
            ["git", "-C", str(root), *args], capture_output=True, text=True, check=False,
        )
    except OSError:
        return None
    return proc.stdout if proc.returncode == 0 else None


def baseline_sha(root: Path) -> str | None:
    """The commit ADR-0047's move landed in, or None when it cannot be found.

    `ai/state.seed/` is tracked forever from the moment it was introduced, so the
    OLDEST commit that added anything under it is a stable, repository-wide anchor --
    the same commit for every clone, never a per-machine value. Everything at or
    before it is pre-move history, already accounted for in
    `docs/historia/estado-2026-08/` and out of scope for this guard; everything after
    it is checked exactly as before, against whatever `ai/state/features/` this clone
    has actually seeded and grown since.
    """
    log = git(root, "log", "--format=%H", "--diff-filter=A", "--", "ai/state.seed")
    if log is None:
        return None
    lines = [line.strip() for line in log.splitlines() if line.strip()]
    return lines[-1] if lines else None


def delivery_commits(root: Path) -> tuple[list[tuple[int, str, str]] | None, str]:
    """Every delivery commit since the ADR-0047 baseline, or None with a reason.

    None means "this history cannot answer the question", which is a different claim
    from "nothing was delivered".  Three ways to get there now, and the first two
    predate the baseline logic: a shallow clone has the *whole working tree* but a
    truncated log, so treating `git log`'s window as everything that ever happened
    silently inverts the result.  Reproduced before this guard existed in its current
    form: `git clone --depth 1` of this repository made the guard declare 006's waiver
    unnecessary and exit 1, advising a deletion that would have broken every full
    clone.  CI fetches with depth 0, so it would never have been the one to notice.
    The third (`baseline-unknown`) is the same posture applied to the new anchor: a
    full clone that somehow lacks `ai/state.seed/` ANYWHERE -- neither in history nor
    on disk -- cannot answer "since the baseline" either, and guessing (by falling
    back to the full history this function used to scan) would resurrect the exact
    false-positive bug ADR-0047 exists to close.

    One more case is not degraded, on purpose: `ai/state.seed/` present in the
    working tree but not yet in any commit is not "unusable history", it is the
    ADR-0047 move itself, mid-flight -- this repository, right now, before its own
    migration commit lands.  Nothing can be "after" a commit that has not been made
    yet, so the honest window is empty, and the honest answer is the same as any
    other clone with nothing to report: no violations, not "can't tell".
    """
    shallow = git(root, "rev-parse", "--is-shallow-repository")
    if shallow is None:
        return None, "git-history-unavailable"
    if shallow.strip() == "true":
        return None, "shallow-clone"
    baseline = baseline_sha(root)
    if baseline is None:
        if (root / "ai" / "state.seed").is_dir():
            return [], ""
        return None, "baseline-unknown"
    log = git(root, "log", "--format=%h %s", f"{baseline}..HEAD")
    if log is None:
        return None, "git-history-unavailable"
    found = []
    for line in log.splitlines():
        sha, _, subject = line.partition(" ")
        named = DELIVERY_SUBJECT.match(subject)
        if named:
            found.append((int(named.group(1)), sha, subject))
    return found, ""


def remedy(root: Path, feature_id: str) -> str:
    spec = Path("docs/specs") / feature_id / "spec.md"
    absolute = root / spec
    digest = (
        hashlib.sha256(absolute.read_bytes()).hexdigest() if absolute.is_file() else "<sha256 of the spec>"
    )
    return (
        f"python3 ai/scripts/feature-state.py init {feature_id} {spec} {digest} "
        f"--mode feature --approved-by <who approved it> --ac AC-01 --ac AC-02 ..."
    )


def violations(root: Path, commits: list[tuple[int, str, str]]) -> list[str]:
    specs = root / "docs" / "specs"
    if not specs.is_dir():
        return []
    found = []
    for directory in sorted(p for p in specs.iterdir() if p.is_dir()):
        feature_id = directory.name
        if (root / "ai" / "state" / "features" / f"{feature_id}.json").exists():
            continue
        if feature_id in WAIVED:
            continue
        named = FEATURE_ID_NUMBER.match(feature_id)
        if not named:
            continue
        for number, sha, subject in commits:
            if number != int(named.group(1)):
                continue
            found.append(
                f"FEATURE_STATE_MISSING id={feature_id} evidence={sha} {subject!r}\n"
                f"  remedy: {remedy(root, feature_id)}"
            )
            break
    return found


def stale_waivers(root: Path, commits: list[tuple[int, str, str]]) -> list[str]:
    """A waiver that no longer waives anything is the same rot, one level up.

    Skipped entirely when the feature's spec folder is absent, so pointing the guard at
    a tree that simply does not contain the waived feature is silent rather than noisy.
    """
    stale = []
    for feature_id in WAIVED:
        if not (root / "docs" / "specs" / feature_id).is_dir():
            continue
        named = FEATURE_ID_NUMBER.match(feature_id)
        violating = (
            named is not None
            and not (root / "ai" / "state" / "features" / f"{feature_id}.json").exists()
            and any(number == int(named.group(1)) for number, _, _ in commits)
        )
        if not violating:
            stale.append(
                f"WAIVER_UNNECESSARY id={feature_id} — this waiver no longer waives anything; "
                f"delete it from {Path(__file__).name} instead of leaving it to read as settled"
            )
    return stale


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: check-feature-state.py <root>", file=sys.stderr)
        return 2
    for feature_id, reason in WAIVED.items():
        if not reason.strip():
            print(f"WAIVER_WITHOUT_REASON id={feature_id}", file=sys.stderr)
            return 2
    root = Path(sys.argv[1])
    commits, unusable = delivery_commits(root)
    if commits is None:
        # Loud on purpose.  Degrading to a silent no-op is the exact class of defect
        # this feature exists to remove, so an unusable history is announced and
        # pinned by a test rather than swallowed.  Announced, not failed: a truncated
        # history is not evidence of a violation, and a guard that reports violations
        # which are not violations is the one that gets disabled.
        print(f"FEATURE_STATE_UNCHECKED reason={unusable}", file=sys.stderr)
        return 0
    problems = violations(root, commits) + stale_waivers(root, commits)
    for problem in problems:
        print(problem)
    if problems:
        print(f"FEATURE_STATE_MISSING count={len(problems)}", file=sys.stderr)
        return 1
    print("FEATURE_STATE_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
