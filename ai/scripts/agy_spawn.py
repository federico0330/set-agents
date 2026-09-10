#!/usr/bin/env python3
"""agy (Antigravity CLI) spawn lane — 047.

Materializes a routing decision onto `agy --print --model … [--effort …]`.
Harness install into ~/.gemini is deferred to install.py --target agy.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import host_adapters


def main(argv=None):
    parser = argparse.ArgumentParser(description="Spawn a one-shot agy print turn")
    parser.add_argument("--model", required=True)
    parser.add_argument("--effort", choices=list(host_adapters.EFFORTS))
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    adapter = host_adapters.get_adapter("agy")
    if adapter is None:
        print("AGY_ADAPTER_MISSING", file=sys.stderr)
        return 2
    if not adapter.detect():
        print("AGY_ABSENT", file=sys.stderr)
        return 2
    argv_cmd = adapter.materialize(args.model, args.effort) + [args.prompt]
    if args.dry_run:
        print(json.dumps({"argv": argv_cmd, "host": "agy"}, sort_keys=True))
        return 0
    result = subprocess.run(argv_cmd, check=False)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
