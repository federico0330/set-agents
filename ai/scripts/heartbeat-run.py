#!/usr/bin/env python3
"""Run a long command that never goes more than `--interval` seconds without output.

AC-06 (021/P2, ADR-0041). The defect this replaces is `| tail -N`: without `-f`, `tail`
structurally cannot emit a single byte until it sees EOF, no matter how the upstream command
buffers its own writes (measured: `stdbuf -oL <cmd with explicit flush=True> | tail -3` hangs
exactly like the unbuffered case). Piping a multi-minute gate through it makes the agent running
it look stalled for the whole run, which is how four agents died mid-session with `Agent stalled:
no progress for 600s` (D-3 of the spec) -- the 600s watchdog belongs to the agent runtime, not to
this repository (AC-08); what this repo controls is not creating the silence that trips it.

This wrapper streams the child's stdout+stderr (merged) line by line as they arrive -- it never
buffers waiting for the child to exit -- and injects a synthetic heartbeat line of its own if
`--interval` seconds pass with no real line, so something is always emitted well under any
watchdog. It does not make the child faster and does not change its exit code; AC-06 is about
silence, not speed (a slower child is a different, explicitly out-of-scope problem).

Usage: heartbeat-run.py [--interval SECONDS] -- <command> [args...]
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import threading
import time

DEFAULT_INTERVAL = 60.0


def run(command: list[str], interval: float, out=sys.stdout) -> int:
    try:
        proc = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
    except (FileNotFoundError, PermissionError) as exc:
        out.write(f"heartbeat-run: cannot execute '{command[0]}': {exc.strerror}\n")
        out.flush()
        return 1
    lock = threading.Lock()
    state = {"last": time.monotonic()}
    done = threading.Event()

    def reader() -> None:
        assert proc.stdout is not None
        for line in proc.stdout:
            with lock:
                state["last"] = time.monotonic()
            out.write(line)
            out.flush()
        done.set()

    reader_thread = threading.Thread(target=reader, daemon=True)
    reader_thread.start()

    # Poll well below the interval so the worst-case delay before a heartbeat is small
    # relative to it, not another `interval` on top of it.
    poll = max(0.05, min(1.0, interval / 4))
    while not done.is_set():
        done.wait(timeout=poll)
        if done.is_set():
            break
        with lock:
            silent_for = time.monotonic() - state["last"]
        if silent_for >= interval:
            out.write(f"... heartbeat-run: still running, {int(silent_for)}s without output\n")
            out.flush()
            with lock:
                state["last"] = time.monotonic()

    reader_thread.join()
    return proc.wait()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--interval", type=float, default=DEFAULT_INTERVAL,
        help=f"max seconds of silence before a heartbeat line (default {DEFAULT_INTERVAL:g})",
    )
    parser.add_argument(
        "command", nargs=argparse.REMAINDER,
        help="command to run, after a literal --, e.g. heartbeat-run.py -- python3 -m unittest discover -s tests -v",
    )
    args = parser.parse_args(argv)
    command = args.command
    if command and command[0] == "--":
        command = command[1:]
    if not command:
        parser.error("no command given -- usage: heartbeat-run.py [--interval N] -- <command> [args...]")
    if args.interval <= 0:
        parser.error("--interval must be > 0")
    return run(command, args.interval)


if __name__ == "__main__":
    raise SystemExit(main())
