#!/usr/bin/env python3
"""Always persist locally; optionally try Engram once with a hard timeout."""

import argparse
import datetime as dt
import shlex
import subprocess
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("entry")
parser.add_argument("--log", default="docs/ai/memory-log.md")
parser.add_argument("--engram-command")
parser.add_argument("--timeout", type=float, default=60.0)
args = parser.parse_args()

path = Path(args.log)
path.parent.mkdir(parents=True, exist_ok=True)
with path.open("a", encoding="utf-8") as handle:
    handle.write(f"\n- {dt.date.today().isoformat()}: {args.entry}\n")

if args.engram_command:
    try:
        subprocess.run(shlex.split(args.engram_command), input=args.entry, text=True, timeout=min(args.timeout, 60.0), check=True)
    except (subprocess.SubprocessError, OSError):
        print("Engram unavailable; local memory retained")
