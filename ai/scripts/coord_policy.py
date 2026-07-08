#!/usr/bin/env python3
"""Deny-by-default command policy for read-only coordination."""

import re
import shlex
import sys

SAFE = [
    r"git (status|diff|log|show)(\s|$)",
    r"(rg|bat|eza|fd)(\s|$)",
    r"(uname|lsb_release|sw_vers)(\s|$)",
    r"opencode models(\s|$)",
    r"dotnet --(list-sdks|list-runtimes|info)(\s|$)",
    r"node (--version|-v)(\s|$)",
    r"npm (ls|list)(\s|$)",
    r"python(3)? (--version|-V)(\s|$)",
    r"pip(3)? (list|show)(\s|$)",
    r"go version(\s|$)",
    r"rustup (toolchain list|show)(\s|$)",
    r"(cargo|rustc) (--version|-V)(\s|$)",
    r"(claude|codex|opencode) (--version|-V)(\s|$)",
]

FORBIDDEN_SYNTAX = re.compile(r"(?:>|>>|<|<<|\|\||&&|;|\|)|`|\$\(")
FORBIDDEN_OPTIONS = re.compile(r"(?:--output(?:=|\s)|--ext-diff|--pre(?:=|\s)|--exec(?:=|\s)|--exec-batch(?:=|\s)|(?:^|\s)-x(?:\s|$)|(?:^|\s)-e(?:\s|$))")


def allowed(command: str) -> bool:
    command = command.strip()
    if not command or "\n" in command or FORBIDDEN_SYNTAX.search(command) or FORBIDDEN_OPTIONS.search(command):
        return False
    try:
        shlex.split(command)
    except ValueError:
        return False
    return any(re.fullmatch(pattern + r".*", command) for pattern in SAFE)


if __name__ == "__main__":
    if len(sys.argv) != 2 or not allowed(sys.argv[1]):
        print("Blocked by coord-ro policy", file=sys.stderr)
        raise SystemExit(2)
