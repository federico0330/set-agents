#!/usr/bin/env python3
"""Fail when a canonical prompt sends an agent to a path that does not exist.

The instruction "read X FIRST if it exists" degrades to a silent no-op when X is
missing, so the whole department-knowledge layer sat dead for five features without
a single failing check.  This catches the class, not that one instance.

It deliberately does NOT check templated literals: a form carrying `<placeholder>`
or a glob is filled in at run time, and a `{a,b,c}` enumeration is checked by
`test_knowledge_write_and_read_targets_agree`, which parses and expands it and
asserts every member exists.  The two guards are complementary on purpose — this
one covers concrete literals across every prompt, that one covers the brace form
of the knowledge layer.  Neither alone covers both.

Usage: check-canonical-paths.py <root>
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# Roots a prompt can name that must resolve inside the harness itself.
PREFIXES = ("docs/", "ai/", "knowledge/", "tests/", "Global/", "PROYECTO/", "profiles/")
# A real placeholder is an angle-bracket span or a glob, never a lone punctuation mark.
TEMPLATED = re.compile(r"<[^>]+>|\*")
CANDIDATE = re.compile(r"`([A-Za-z0-9_][A-Za-z0-9_./@{}<>*,-]*)`")

# Every waiver carries its reason and names the file that settles it.  A waiver
# without a reason is a hole, not a waiver — and one whose reason is wrong is worse,
# because it reads as settled.
WAIVED = {
    "ai/state/verify.log": (
        "written by PROYECTO/ai/scripts/verify.sh:9 inside a scaffolded project, never by this "
        "repository's own verify.sh; named as an input by Global/_canonical/agents/debugger.md:16"
    ),
    "docs/adr/NNNN-slug.md": (
        "filename pattern for a new ADR at Global/_canonical/skills/system-design-decisions/SKILL.md:136, "
        "not a path to an existing file"
    ),
    "docs/project/architecture.md": (
        "created by Global/_canonical/agents/project-bootstrapper.md:6 in a scaffolded project; "
        "the harness is not one of its targets"
    ),
}


def dangling(root: Path) -> list[str]:
    canonical = root / "Global" / "_canonical"
    found = set()
    for prompt in sorted(canonical.rglob("*")):
        if not prompt.is_file() or prompt.suffix not in (".md", ".toml"):
            continue
        relative = prompt.relative_to(root)
        for number, line in enumerate(prompt.read_text(encoding="utf-8").splitlines(), 1):
            for named in CANDIDATE.findall(line):
                if not named.startswith(PREFIXES) or TEMPLATED.search(named) or "{" in named:
                    continue
                if named in WAIVED or (root / named).exists():
                    continue
                found.add(f"CANONICAL_DANGLING_PATH file={relative}:{number} path={named}")
    return sorted(found)


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: check-canonical-paths.py <root>", file=sys.stderr)
        return 2
    for path, reason in WAIVED.items():
        if not reason.strip():
            print(f"WAIVER_WITHOUT_REASON path={path}", file=sys.stderr)
            return 2
    problems = dangling(Path(sys.argv[1]))
    for problem in problems:
        print(problem)
    if problems:
        print(f"CANONICAL_DANGLING_PATH count={len(problems)}", file=sys.stderr)
        return 1
    print("CANONICAL_PATHS_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
