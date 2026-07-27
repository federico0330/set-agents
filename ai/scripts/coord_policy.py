#!/usr/bin/env python3
"""Deny-by-default command policy for read-only coordination."""

import re
import shlex
import sys

# Keep the full marker in source artifacts. install.py replaces this exact byte
# sequence only when writing the installed policy, while verify.sh can prove the
# tracked Global/** tree never baked a builder-specific root.
APP_CLI = "__SET_AGENTS_ROOT__/ai/scripts/set_agents_app.py"

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
    r"(cat|ls|find|grep|head|tail|wc|tree|file|stat|diff|du|df|ps|pwd|which)(\s|$)",
    r"curl (?:-[A-Za-z]+\s+)*(?:http://)?(?:localhost|127\.0\.0\.1)(?::\d+)?(?:/|\s|$)",
    # Sanctioned mutation channel: the state CLI validates every transition and
    # writes only atomic JSON under ai/state/. FORBIDDEN_SYNTAX still blocks any
    # shell composition around it.
    r"python3 ai/scripts/feature-state\.py \S+",
]

# Exact argv comparison keeps a baked path with spaces auditable without turning it
# into a permissive raw-string/glob rule.  The tracked copy intentionally matches no
# local invocation until install.py substitutes HARNESS_HOME.
SAFE_ARGV = [
    ({"python3", "python"}, APP_CLI, re.compile(r"--rout(e|ing)-\S+")),
]

FORBIDDEN_SYNTAX = re.compile(r"(?:>|>>|<|<<|\|\||&&|;|\|)|`|\$\(")
FORBIDDEN_OPTIONS = re.compile(r"(?:--output(?:=|\s)|--ext-diff|--pre(?:=|\s)|--exec(?:=|\s)|--exec-batch(?:=|\s)|(?:^|\s)-x(?:\s|$)|(?:^|\s)-e(?:\s|$))")

# Short, irreducible safety net: hard-blocked for every role, including subagents that
# otherwise fail open to "ask". Everything else is a matter of asking the human, never a
# silent deny.
ALWAYS_DENY = re.compile(
    r"(?:^|\s)sudo(?:\s|$)|"
    r"rm\s+-[a-zA-Z]*r[a-zA-Z]*f|rm\s+-[a-zA-Z]*f[a-zA-Z]*r|"
    r"git\s+push\s+(?:--force(?:-with-lease)?|-f)(?:\s|$)|"
    r"gh\s+repo\s+delete"
)


def always_denied(command: str) -> bool:
    return bool(ALWAYS_DENY.search(command.strip()))


def _argv_allowed(argv: list[str]) -> bool:
    if len(argv) < 3:
        return False
    return any(argv[0] in interpreters and argv[1] == script and flag.fullmatch(argv[2])
               for interpreters, script, flag in SAFE_ARGV)


def allowed(command: str) -> bool:
    command = command.strip()
    if not command or "\n" in command or FORBIDDEN_SYNTAX.search(command) or FORBIDDEN_OPTIONS.search(command):
        return False
    try:
        argv = shlex.split(command)
    except ValueError:
        return False
    if _argv_allowed(argv):
        return True
    return any(re.fullmatch(pattern + r".*", command) for pattern in SAFE)


if __name__ == "__main__":
    if len(sys.argv) != 2 or not allowed(sys.argv[1]):
        print("Blocked by coord-ro policy", file=sys.stderr)
        raise SystemExit(2)
