#!/usr/bin/env python3
"""Always persist locally; optionally try Engram once with a hard timeout."""

import argparse
import datetime as dt
import re
import shlex
import subprocess
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("entry")
parser.add_argument("--log", default="docs/ai/memory-log.md")
parser.add_argument("--domain", choices=["security", "data", "architecture", "algorithms", "frontend"],
                    help="route the entry to the per-domain knowledge file instead of the general log")
parser.add_argument("--section",
                    help="heading to file the entry under; required with --domain, because the department "
                         "memory is curated by section and is not an append-only log")
parser.add_argument("--feature-id", help="stamped into the entry prefix alongside the year and month")
parser.add_argument("--knowledge-dir", default="docs/ai/knowledge",
                    help="root of the per-domain knowledge tier")
parser.add_argument("--engram-command")
parser.add_argument("--timeout", type=float, default=60.0)
args = parser.parse_args()


def file_under_section(text: str, section: str, line: str) -> str:
    """Append one entry at the end of a named section, never past the end of the file.

    The heading is matched as a whole line.  A substring match would accept any prefix
    of a real heading ("Decision" against "## Decisiones y porqués") and file the entry
    there anyway, which is precisely the mis-typed heading this is supposed to refuse.
    """
    match = re.search(rf"^## {re.escape(section)}[ \t]*$", text, re.MULTILINE)
    if not match:
        present = ", ".join(re.findall(r"^## (.+?)[ \t]*$", text, re.MULTILINE)) or "none"
        raise SystemExit(f"UNKNOWN_SECTION: {section!r} is not a heading of this file (has: {present})")
    head, heading = text[:match.start()], match.group(0)
    body, next_marker, tail = text[match.end():].partition("\n## ")
    return f"{head}{heading}{body.rstrip()}\n{line}\n{next_marker}{tail}"


if args.domain:
    if not args.section:
        raise SystemExit("SECTION_REQUIRED: --domain writes into the department memory, which is filed by "
                         "section; pass --section (the memory-scribe prompt names the sanctioned three)")
    # The scribe's declared contract: `[YYYY-MM][feature-id]` under one of those headings.
    stamp = dt.date.today().strftime("%Y-%m")
    prefix = f"[{stamp}][{args.feature_id}]" if args.feature_id else f"[{stamp}]"
    path = Path(args.knowledge_dir) / f"{args.domain}.md"
    if not path.exists():
        raise SystemExit(f"MISSING_KNOWLEDGE_FILE: {path} (domain files are seeded, never created ad hoc)")
    path.write_text(
        file_under_section(path.read_text(encoding="utf-8"), args.section, f"- {prefix} {args.entry}"),
        encoding="utf-8",
    )
else:
    # The general fallback log stays a flat append: it declares no section contract to honour.
    path = Path(args.log)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(f"\n- {dt.date.today().isoformat()}: {args.entry}\n")

if args.engram_command:
    try:
        subprocess.run(shlex.split(args.engram_command), input=args.entry, text=True, timeout=min(args.timeout, 60.0), check=True)
    except (subprocess.SubprocessError, OSError):
        print("Engram unavailable; local memory retained")
