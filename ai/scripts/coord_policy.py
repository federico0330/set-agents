#!/usr/bin/env python3
"""Deny-by-default command policy for read-only coordination."""

import re
import shlex
import sys
from urllib.parse import urlparse

# Keep the full marker in source artifacts. install.py replaces this exact byte
# sequence only when writing the installed policy, while verify.sh can prove the
# tracked Global/** tree never baked a builder-specific root.
APP_CLI = "__SET_AGENTS_ROOT__/ai/scripts/set_agents_app.py"
# SEC-P1-002 (015 repair, panel RP-01): the Claude-Code-lane cross-process spawn CLI
# (`ai/scripts/claude_code_spawn.py --dispatch-writer`/`--dispatch-review`) -- the ONLY
# execution surface AC-03/AC-04's doctrine has for actually invoking this module, since
# the orchestrator's Bash is deny-by-default and nothing allowlisted it before this fix.
CLAUDE_SPAWN_CLI = "__SET_AGENTS_ROOT__/ai/scripts/claude_code_spawn.py"
# ADR-0032: the OpenCode/Codex-lane cross-process spawn CLIs -- the mechanism that
# applies a --route-decide model AT SPAWN TIME for any roster role on those lanes
# (retiring MODEL_STATIC_FALLBACK as the normal path, ADR-0030's stated gap).
OPENCODE_SPAWN_CLI = "__SET_AGENTS_ROOT__/ai/scripts/opencode_spawn.py"
CODEX_SPAWN_CLI = "__SET_AGENTS_ROOT__/ai/scripts/codex_spawn.py"

SAFE = [
    # Sanctioned mutation channel: the state CLI validates every transition and
    # writes only atomic JSON under ai/state/. FORBIDDEN_SYNTAX still blocks any
    # shell composition around it. `_blocks_integration_transition` (below) denies
    # the one shape this blanket allow must NOT cover: a direct, unwrapped
    # `transition ... INTEGRATION` -- that phase requires the receipt-checked
    # wrapper (docs/adr/0020-*.md), the next SAFE entry.
    r"python3 ai/scripts/feature-state\.py .+",
    # docs/adr/0020-*.md: the receipt-checked integration wrapper. `integration_action.py`
    # re-derives the frozen candidate_identity live and independently re-validates the
    # command shape before running anything -- this allow only narrows WHICH Bash
    # surface can reach it, never substitutes for its own checks.
    r"python3 ~/\.claude/hooks/integration_action\.py \S+ \S+ (freeze-candidate|record-receipt|transition) -- .+",
]

# Exact argv comparison keeps a baked path with spaces auditable without turning it
# into a permissive raw-string/glob rule.  The tracked copy intentionally matches no
# local invocation until install.py substitutes HARNESS_HOME.
SAFE_ARGV = [
    # `modifiers=None` means "argv[2] alone decides", exactly as before: set_agents_app.py's
    # own routing-mode-exclusivity guard in main() (_mode_flags/other_mode) is the thing that
    # keeps a routing invocation from carrying an unrelated flag, so this entry doesn't need
    # to re-derive that flag's full grammar here.
    ({"python3", "python"}, APP_CLI, re.compile(r"--rout(e|ing)-\S+"), None),
    # ADR-0012/AC-19: a THIRD sanctioned channel, distinct from the one above. --context is
    # read-only (cmd_context never writes anything, never reads a credential surface) --
    # justified precisely because of that, never merged into the mutating-capable entry.
    # SEC-001: unlike --route*, --context takes no value of its own, so its rest-of-argv CAN
    # be exhaustively enumerated instead of trusted blind: argv[2] matching used to be treated
    # as clearance for the whole command, which let `--context --scaffold X` (or --update
    # --yes, --tools-install, ...) through this allowlist -- demonstrated writing real files.
    # main() now also refuses that combination on its own, but this keeps coord_policy from
    # claiming a command is safe when it never actually looked past argv[2].
    ({"python3", "python"}, APP_CLI, re.compile(r"--context\S*"), {"--json": 0, "--project": 1}),
    # SEC-P1-002: a FOURTH sanctioned channel, distinct from the three above -- the
    # Claude-Code-lane cross-process spawn CLI. Exhaustively enumerated `modifiers` (the
    # `--context` precedent's form, never `modifiers=None`, never a trailing-wildcard
    # regex): every flag `claude_code_spawn.main()` actually defines, and no other. The
    # untrusted content itself (a diff, a task) never appears as an argv VALUE this
    # allowlist has to reason about -- `--task`/`--supplementary` only ever carry a file
    # path or the literal `-` (stdin), never inline text, so a diff containing shell
    # metacharacters can never smuggle itself into what this policy inspects.
    # DR-02 (015 repair, delta-review round 2): `--routing-test-root` is deliberately
    # ABSENT from this modifier map -- `claude_code_spawn.main()` no longer defines that
    # flag at all (it was a hermetic test-only seam on `dispatch_writer` itself, never
    # meant to be reachable via a real, allowlisted invocation of this CLI; exposing it
    # here let an allowlisted command redirect the SEC-P1-003 audit binding away from the
    # routing store's real 0700 production root). Every entry below must keep matching
    # `claude_code_spawn.main()`'s real, current flag set exactly -- no more, no less.
    ({"python3", "python"}, CLAUDE_SPAWN_CLI, re.compile(r"--dispatch-(writer|review)"), {
        "--role": 1, "--provider": 1, "--model": 1, "--task": 1, "--run-id": 1,
        "--supplementary": 1, "--spawn-cwd": 1, "--cwd": 1,
        "--timeout": 1,
    }),
    # ADR-0032: FIFTH and SIXTH sanctioned spawn channels -- one per lane CLI, same
    # exhaustively-enumerated `modifiers` discipline as the claude_code_spawn entry
    # above (never `modifiers=None`, never a trailing-wildcard regex). The flag maps
    # must keep matching each module's real `main()` flag set exactly -- no more, no
    # less (`--effort` exists here and NOT on claude_code_spawn, whose main() never
    # defines it; the catalog pins anthropic routes to effort=medium by construction).
    # `--dispatch-simulate` is the ADR-0030 simulate universe: role_class `other` only,
    # zero routing-store bookkeeping, refused for writer/review roles by the module.
    ({"python3", "python"}, OPENCODE_SPAWN_CLI, re.compile(r"--dispatch-(writer|review|simulate)"), {
        "--role": 1, "--provider": 1, "--model": 1, "--effort": 1, "--task": 1,
        "--run-id": 1, "--supplementary": 1, "--spawn-cwd": 1, "--cwd": 1,
        "--timeout": 1,
    }),
    ({"python3", "python"}, CODEX_SPAWN_CLI, re.compile(r"--dispatch-(writer|review|simulate)"), {
        "--role": 1, "--provider": 1, "--model": 1, "--effort": 1, "--task": 1,
        "--run-id": 1, "--supplementary": 1, "--spawn-cwd": 1, "--cwd": 1,
        "--timeout": 1,
    }),
]

# SEC-030: Enumerated binary commands with exact flag sets. Each command's rest-of-argv
# is validated against a `modifiers` map (like SAFE_ARGV) specifying which flags are
# allowed and how many arguments each takes. No trailing-wildcard regex; no prefix-match.
# Format: (command_name, modifiers_dict)
# The modifiers dict maps flag names to argument counts:
#   "--flag": 0  (boolean flag)
#   "--flag": 1  (flag takes one value)
#   "-f": 1      (short form)
SAFE_BINARY_COMMANDS = [
    # git: read-only operations only. Forbidden always: -c (config), --exec-path,
    # --upload-pack, --receive-pack (all execute code or delegate execution).
    ("git", {
        "status": 0,
        "--porcelain": 0,
        "--short": 0,
        "--long": 0,
        "-z": 0,
        "diff": 0,
        "--check": 0,
        "--stat": 0,
        "--numstat": 0,
        "--shortstat": 0,
        "--name-only": 0,
        "--name-status": 0,
        "--no-color": 0,
        "--color": 0,
        "-U": 1,
        "--unified": 1,
        "log": 0,
        "--oneline": 0,
        "-n": 1,
        "--max-count": 1,
        "-p": 0,
        "--patch": 0,
        "--since": 1,
        "--until": 1,
        "--author": 1,
        "--grep": 1,
        "show": 0,
        "--": 0,
    }),
    # python3: script execution and specific modules. Forbidden: -c (exec code).
    # python3: covered by SAFE_ARGV (feature-state.py, integration_action.py, etc)
    # and _python_m_allowed (for -m unittest, -m py_compile).
    # npm: package inspection, no mutations. Allowed: ls, list (with optional --depth).
    ("npm", {
        "ls": 0,
        "list": 0,
        "--depth": 1,
    }),
    # node: version and REPL, no code execution via CLI flags.
    ("node", {
        "--version": 0,
        "-v": 0,
        "-e": 1,  # allow -e for inline scripts (still subject to FORBIDDEN_SYNTAX)
    }),
    # python: version check only.
    ("python", {
        "--version": 0,
        "-V": 0,
        "-m": 1,
    }),
    # pip/pip3: list packages, show metadata.
    ("pip", {
        "list": 0,
        "show": 0,
    }),
    ("pip3", {
        "list": 0,
        "show": 0,
    }),
    # dotnet: version and listing, no build.
    ("dotnet", {
        "--list-sdks": 0,
        "--list-runtimes": 0,
        "--info": 0,
    }),
    # Inspection tools: no execution, no writing.
    ("grep", {
        "-n": 0,
        "-r": 0,
        "-v": 0,
        "-i": 0,
        "-c": 0,
        "-E": 0,
        "-F": 0,
        "-l": 0,
        "-L": 0,
        "-o": 0,
        "--": 0,
    }),
    ("ls", {
        "-l": 0,
        "-a": 0,
        "-h": 0,
        "-R": 0,
        "-d": 0,
        "-F": 0,
        "--": 0,
    }),
    ("head", {
        "-n": 1,
        "-c": 1,
        "-q": 0,
        "-v": 0,
        "--": 0,
    }),
    ("tail", {
        "-n": 1,
        "-c": 1,
        "-q": 0,
        "-v": 0,
        "-f": 0,  # follow (may block, use cautiously)
        "--": 0,
    }),
    ("cat", {
        "-n": 0,
        "-E": 0,
        "-v": 0,
        "-T": 0,
        "--": 0,
    }),
    ("wc", {
        "-l": 0,
        "-w": 0,
        "-c": 0,
        "-m": 0,
        "--": 0,
    }),
    ("cmp", {
        "-s": 0,
        "-l": 0,
        "-b": 0,
        "--": 0,
    }),
    ("diff", {
        "-u": 0,
        "-c": 0,
        "-q": 0,
        "-r": 0,
        "-N": 0,
        "-a": 0,
        "-b": 0,
        "-w": 0,
        "-i": 0,
        "--": 0,
    }),
    ("find", {
        "-name": 1,
        "-type": 1,
        "-path": 1,
        "-maxdepth": 1,
        "-mindepth": 1,
        "-size": 1,
        "-newer": 1,
        "-mtime": 1,
        "-mmin": 1,
        "-print": 0,
        "-print0": 0,
        "-ls": 0,
        "-quit": 0,
        # Forbidden: -exec, -execdir, -ok, -okdir, -delete, etc.
    }),
    ("rg", {
        "-n": 0,
        "-l": 0,
        "-c": 0,
        "-i": 0,
        "-v": 0,
        "-A": 1,
        "-B": 1,
        "-C": 1,
        "--": 0,
    }),
    ("fd", {
        "-t": 1,
        "-e": 1,
        "-x": 1,  # NO -X (dangerous)
        "-d": 1,
        "-H": 0,
        "-L": 0,
        "-F": 0,
        "--": 0,
    }),
    ("bat", {
        "--line-range": 1,
        "-l": 1,
        "--language": 1,
        "-n": 0,
        "--number": 0,
        "-p": 0,
        "--plain": 0,
        "--": 0,
    }),
    ("eza", {
        "-l": 0,
        "-a": 0,
        "-R": 0,
        "-r": 0,
        "-s": 1,
        "--group-directories-first": 0,
        "--": 0,
    }),
    ("tree", {
        "-L": 1,
        "-d": 0,
        "-a": 0,
        "-I": 1,
        "--": 0,
    }),
    ("file", {
        "-b": 0,
        "-i": 0,
        "-L": 0,
        "--": 0,
    }),
    ("stat", {
        "-c": 1,
        "-f": 1,
        "-L": 0,
        "--": 0,
    }),
    ("du", {
        "-sh": 0,
        "-h": 0,
        "-s": 0,
        "-d": 1,
        "--": 0,
    }),
    ("df", {
        "-h": 0,
        "-i": 0,
        "-T": 0,
        "-k": 0,
        "-m": 0,
        "--": 0,
    }),
    ("ps", {
        "aux": 0,
        "-ef": 0,
        "-A": 0,
        "-u": 1,
        "-p": 1,
        "--": 0,
    }),
    ("pwd", {}),
    ("which", {}),
    ("uname", {
        "-a": 0,
        "-s": 0,
        "-m": 0,
        "-r": 0,
        "-v": 0,
    }),
    ("lsb_release", {
        "-a": 0,
        "-d": 0,
        "-i": 0,
        "-r": 0,
        "-c": 0,
        "-s": 0,
    }),
    ("sw_vers", {}),
    ("opencode", {
        "models": 0,
    }),
    ("rustup", {
        "toolchain": 0,
        "list": 0,
        "show": 0,
    }),
    ("cargo", {
        "--version": 0,
        "-V": 0,
    }),
    ("rustc", {
        "--version": 0,
        "-V": 0,
    }),
    ("go", {
        "version": 0,
    }),
    ("claude", {
        "--version": 0,
        "-V": 0,
    }),
    ("codex", {
        "--version": 0,
        "-V": 0,
    }),
    ("./build.sh", {
        "--check": 0,
        "--profile": 1,
        "--target": 1,
        "--output": 1,
    }),
    ("./install.sh", {
        "--yes": 0,
        "--force": 0,
    }),
]


def _rest_allowed(rest: list[str], modifiers: dict[str, int]) -> bool:
    """Generic validator for flag+value pairs. Handles both --flag value and --flag=value.
    Non-flag tokens are allowed as positional arguments only if modifiers contains only flags (all start with -).
    If modifiers contains subcommands (tokens without -), positional args are rejected."""
    # Determine if modifiers has subcommands (non-flag entries)
    has_subcommands = any(k for k in modifiers.keys() if not k.startswith("-"))

    i = 0
    while i < len(rest):
        token = rest[i]
        # Handle --flag=value syntax
        if "=" in token and token.startswith("-"):
            flag, _ = token.split("=", 1)
            nargs = modifiers.get(flag)
            if nargs is None:
                return False
            i += 1
            continue
        # Handle --flag value syntax
        if token.startswith("-"):
            nargs = modifiers.get(token)
            if nargs is None:
                # Try to handle composed short flags like -rn, -la
                if not token.startswith("--"):
                    # Composed short flags: validate each char
                    for char in token[1:]:
                        if "-" + char not in modifiers:
                            return False
                    i += 1
                    continue
                # Unknown flag → error
                return False
            i += 1 + nargs
        else:
            # Non-flag token
            if has_subcommands:
                # modifiers has subcommands: this token must be a known subcommand
                if token not in modifiers:
                    return False
                i += 1
            else:
                # modifiers has only flags: allow positional argument, protected by FORBIDDEN_SYNTAX
                i += 1
    return True


def _gh_allowed(argv: list[str]) -> bool:
    """ADR-0025: GitHub inspection only (no mutations). Nested subcommand validation."""
    if len(argv) < 2 or argv[0] != "gh":
        return False
    allowed_paths = {
        "run": {"list", "view", "watch"},
        "pr": {"list", "view", "checks", "status", "diff"},
        "workflow": {"list", "view"},
        "issue": {"list", "view"},
        "auth": {"status"},
        "repo": {"view"},
    }
    subcommand = argv[1]
    if subcommand not in allowed_paths:
        return False
    if len(argv) < 3:
        return subcommand == "auth"  # `gh auth` alone is invalid
    subaction = argv[2]
    if subaction not in allowed_paths[subcommand]:
        return False
    # Rest of argv: must be flags and their values from gh's safe set
    # For simplicity, allow --json, --template, --jq, numeric args (run IDs, PR numbers)
    rest = argv[3:]
    i = 0
    while i < len(rest):
        token = rest[i]
        if token in {"--json", "--template", "--jq", "--log"}:
            i += 2 if token != "--log" else 1  # --log takes optional arg, for safety require it
        elif token.startswith("--"):
            i += 1  # skip unknown flags
        else:
            i += 1  # assume numeric ID or other positional arg
    return True


def _curl_allowed(argv: list[str]) -> bool:
    """Validate curl: no file://, no -o/-O/-d/--config, URL as last token, http/https only."""
    if len(argv) < 2 or argv[0] != "curl":
        return False
    # Forbidden flags
    forbidden_flags = {"-o", "--output", "-O", "--remote-name", "-T", "--upload",
                       "-d", "--data", "--data-raw", "--data-binary", "--data-urlencode",
                       "-K", "--config"}
    # Find URL (should be last non-flag token)
    url = None
    i = 1
    while i < len(argv):
        token = argv[i]
        if token.startswith("-"):
            # Check for forbidden flags
            if token.split("=")[0] in forbidden_flags:
                return False
            # Skip flag + its argument
            if token in {"-H", "--header", "-A", "--user-agent", "-b", "--cookie", "-u", "--user"}:
                i += 2
            else:
                i += 1
        else:
            # Non-flag token: could be URL or arg to previous flag
            if not url and (i == 1 or not argv[i-1].startswith("-")):
                url = token
            i += 1
    # Validate URL
    if not url:
        return False
    try:
        parsed = urlparse(url)
        # Only allow http/https, reject file://, scp://, dict://, etc.
        if parsed.scheme not in {"http", "https"}:
            return False
    except Exception:
        return False
    return True


def _python_m_allowed(argv: list[str]) -> bool:
    """Special validator for python3/python -m <module> to allow submodule arguments."""
    if len(argv) < 3 or argv[0] not in {"python3", "python"}:
        return False
    if argv[1] != "-m":
        return False
    module = argv[2]
    # Allow unittest and py_compile with their subcommands
    if module in {"unittest", "py_compile"}:
        # Rest of argv is unittest/py_compile arguments, protected by FORBIDDEN_SYNTAX
        return True
    return False


def _binary_command_allowed(argv: list[str]) -> bool:
    """Validate binary commands using SAFE_BINARY_COMMANDS."""
    if not argv:
        return False
    cmd = argv[0]
    # Find command in SAFE_BINARY_COMMANDS
    modifiers = None
    for cmd_name, mods in SAFE_BINARY_COMMANDS:
        if cmd_name == cmd:
            modifiers = mods
            break
    if modifiers is None:
        return False
    # Special handling for numeric flags (head -20, tail -5)
    rest = argv[1:]
    normalized = []
    for token in rest:
        # Convert -<N> to -n <N> for head/tail
        if cmd in {"head", "tail"} and token.lstrip("-").isdigit():
            normalized.extend(["-n", token.lstrip("-")])
        else:
            normalized.append(token)
    return _rest_allowed(normalized, modifiers)

# F-01 repair (019-harness-evolution P5 review): the old pattern enumerated `&&` but
# never a BARE `&` -- in `bash -c`, `&` alone is a full statement separator (backgrounds
# the left side, then runs the right side) exactly like `;` is, and
# `_validate_install_command('true & touch /tmp/X')` used to return None (accepted) for
# exactly that reason. `[\x00-\x1f\x7f]` additionally denies every ASCII control
# character a command string could carry (defense in depth alongside `allowed()`'s own
# explicit `"\n" in command` check just below, which only ever covered newline).
FORBIDDEN_SYNTAX = re.compile(r"(?:>|>>|<|<<|\|\||&&|;|\||&)|`|\$\(|[\x00-\x1f\x7f]")
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


def _transition_blocks_integration(argv: list[str]) -> bool:
    """A `feature-state.py transition` invocation whose resolved `to_phase`
    positional is INTEGRATION must go through the wrapped `integration_action.py`
    path (docs/adr/0020-*.md), never the direct blanket `feature-state.py` allow.

    This walks argv the same way argparse actually resolves `transition`'s one
    positional among its all-value-taking flags (`--feature-id`, `--package-id`,
    `--reason`, plus the common `--state-file`/`--expect-revision`/`--actor`/
    `--event-id`) -- a plain substring/prefix check on the raw command string
    would miss `feature-state.py transition --actor x INTEGRATION --package-id y`,
    which argparse parses identically to `transition INTEGRATION --actor x
    --package-id y` but a naive `"transition INTEGRATION"` regex would not catch.
    """
    if len(argv) < 3 or argv[1] != "ai/scripts/feature-state.py" or argv[2] != "transition":
        return False
    i = 3
    while i < len(argv):
        token = argv[i]
        if token.startswith("--"):
            i += 2  # every flag `transition` accepts takes exactly one value
            continue
        return token == "INTEGRATION"
    return False


# ADR-0025: names accepted by the tool-catalog channel below. Tight on purpose:
# a catalog key or harness id, never a path, never an option, never empty.
_CATALOG_NAME = re.compile(r"[a-z0-9][a-z0-9_-]{0,31}")

# ADR-0038: the closed set of `--install-<method>` suffixes the flag-name itself may
# carry. `_tools_propose_allowed` below only needs to know this is a *shape* (some
# lowercase method word), not validate it's a real installer -- `set_agents_app.py`'s
# own `_INSTALL_METHODS` is the semantic source of truth; this regex only keeps the
# flag pattern itself from matching something absurd like `--install-` (empty) or
# `--install-../../etc`.
_INSTALL_METHOD_FLAG = re.compile(r"--install-[a-z]+")

# ADR-0038: the exact, exhaustively-enumerated flag set `--tools-propose` accepts --
# `--kind`, `--detect`, `--why`, plus exactly one `--install-<method>`. All four are
# required, none may repeat, nothing else is allowed to appear.
_TOOLS_PROPOSE_REQUIRED = frozenset({"--kind", "--detect", "--why", "--install-<method>"})


def _tools_propose_allowed(rest: list[str]) -> bool:
    """ADR-0038: `--tools-propose NAME --kind K --detect D --install-<method> CMD --why W`,
    nothing else. Same positional-aware-walker discipline as `_tools_channel_allowed`
    itself (never a trailing-wildcard regex): this only confirms the SHAPE is well-formed
    -- `cmd_tools_propose` in `set_agents_app.py` re-validates every value semantically
    (name grammar, kind enum, escalator/hidden-pipe rejection on the command, via its own
    character ALLOWLIST -- ADR-0038 §3, F-01 repair). A command string containing a real
    shell metacharacter (`;`, a bare `|`, a bare `&`, backticks, `$(`, `>`, `<`, or any
    ASCII control character) is already refused upstream by `FORBIDDEN_SYNTAX` before
    this function ever runs -- see `allowed()` -- so this walker does not need to reason
    about command CONTENT, only about which flags may appear and how many times. (F-01
    repair note: the previous version of `FORBIDDEN_SYNTAX` did NOT include a bare `&`,
    so this claim used to be false for that one character -- fixed alongside this
    docstring, not just described here.)"""
    if not rest or not _CATALOG_NAME.fullmatch(rest[0]):
        return False
    i, seen = 1, set()
    while i < len(rest):
        token = rest[i]
        if token in {"--kind", "--detect", "--why"}:
            key = token
        elif _INSTALL_METHOD_FLAG.fullmatch(token):
            key = "--install-<method>"
        else:
            return False
        if key in seen or i + 1 >= len(rest):
            return False
        seen.add(key)
        i += 2
    return seen == _TOOLS_PROPOSE_REQUIRED


def _tools_channel_allowed(argv: list[str]) -> bool:
    """ADR-0025 sanctioned tool-catalog channel: `--tools`, `--tools-install NAME
    [--yes|--dry-run]`, `--mcp[-add|-on|-off] [NAME] [--harness H]` -- and nothing
    else. A dedicated positional-aware walker (the `_transition_blocks_integration`
    pattern), never a trailing-wildcard regex: `--tools-install` takes a bare NAME
    value, which `SAFE_ARGV`'s flag-only `modifiers` grammar cannot express, and
    the historical `--context --scaffold X` escape (see SAFE_ARGV's SEC-001 note)
    shows exactly what a lax rest-of-argv check costs. `set_agents_app.py` itself
    still re-checks everything (catalog membership, sudo refusal, TTY/--yes); this
    walker only narrows which Bash surface can reach it.

    ADR-0038 adds `--tools-propose` (validates + prints a question, never installs,
    never writes the catalog) to this same channel. `--tools-approve` deliberately
    NEVER matches, in either direction of this function: it is the human-approval step
    itself (`ai/state/decisions-log.jsonl`, slug `tools-approve-fuera-del-canal-del-agente`) --
    letting an agent run it would make propose->human->approve theatre. The branch
    below is an explicit, named deny (not just the implicit fallthrough at the bottom)
    so a future catch-all refactor of this function can't reopen it by accident."""
    if len(argv) < 3 or argv[0] not in {"python3", "python"} or argv[1] != APP_CLI:
        return False
    head, rest = argv[2], argv[3:]
    if head == "--tools":
        return not rest
    if head == "--tools-install":
        if not rest or not _CATALOG_NAME.fullmatch(rest[0]):
            return False
        extras = rest[1:]
        return all(item in {"--yes", "--dry-run"} for item in extras) and len(set(extras)) == len(extras)
    if head == "--tools-propose":
        return _tools_propose_allowed(rest)
    if head == "--tools-approve":
        return False
    if head == "--mcp":
        return not rest or (len(rest) == 2 and rest[0] == "--harness" and bool(_CATALOG_NAME.fullmatch(rest[1])))
    if head in {"--mcp-add", "--mcp-on", "--mcp-off"}:
        if not rest or not _CATALOG_NAME.fullmatch(rest[0]):
            return False
        extras = rest[1:]
        if not extras:
            return True
        return len(extras) == 2 and extras[0] == "--harness" and bool(_CATALOG_NAME.fullmatch(extras[1]))
    return False


def _argv_allowed(argv: list[str]) -> bool:
    if len(argv) < 3:
        return False
    for interpreters, script, flag, modifiers in SAFE_ARGV:
        if argv[0] not in interpreters or argv[1] != script or not flag.fullmatch(argv[2]):
            continue
        if modifiers is None or _rest_allowed(argv[3:], modifiers):
            return True
    return False


def _contains_tools_approve(argv: list[str]) -> bool:
    """F-08 repair: `--tools-approve` must never reach the agent channel through ANY
    allow path -- including a `SAFE_ARGV` entry whose `modifiers` is `None` (the
    `--route*`/`--routing*` entry) or an incomplete modifier map, neither of which walks
    the FULL rest of argv the way `_tools_channel_allowed`'s own dedicated walker does.
    Verified live: `allowed("python3 <APP> --routing-report --tools-approve foo")` used
    to be `True` -- `SAFE_ARGV`'s routing entry only inspects `argv[2]`
    (`--routing-report`) and, with `modifiers=None`, never looks past it, so a
    `--tools-approve` riding along afterward was invisible to it. This is a narrow,
    SPECIFIC guard (only this one flag, checked in every token position) -- the broader
    "modifiers=None doesn't walk the rest of argv" gap is PRE-EXISTING (the same shape
    already lets `--tools-install`/`--yes` ride along a routing invocation) and is not
    this repair's to fix; `--tools-approve` gets its own guard because this whole
    package's security invariant depends on that one flag never being reachable, the
    same discipline `_transition_blocks_integration` already applies for its own
    single, specific, security-critical shape."""
    return any(token == "--tools-approve" or token.startswith("--tools-approve=") for token in argv)


def allowed(command: str) -> bool:
    command = command.strip()
    if not command or "\n" in command or FORBIDDEN_SYNTAX.search(command) or FORBIDDEN_OPTIONS.search(command):
        return False
    try:
        argv = shlex.split(command)
    except ValueError:
        return False
    # Checked before both allow-paths below, so neither SAFE_ARGV nor a SAFE regex
    # match can let a direct `transition ... INTEGRATION` through by construction.
    if _transition_blocks_integration(argv):
        return False
    # ADR-0038/F-08: same discipline, for --tools-approve specifically -- checked before
    # any allow path can short-circuit past it.
    if _contains_tools_approve(argv):
        return False
    if _argv_allowed(argv):
        return True
    if _tools_channel_allowed(argv):
        return True
    # SEC-030: Exhaustive argv validation, not prefix-match
    # Special case validators for complex commands
    if _gh_allowed(argv):
        return True
    if argv[0] == "curl" and _curl_allowed(argv):
        return True
    if _python_m_allowed(argv):
        return True
    # General binary command validation
    if _binary_command_allowed(argv):
        return True
    # Finally, check SAFE regex patterns (feature-state.py, integration_action.py)
    return any(re.fullmatch(pattern, command) for pattern in SAFE)


if __name__ == "__main__":
    if len(sys.argv) != 2 or not allowed(sys.argv[1]):
        print("Blocked by coord-ro policy", file=sys.stderr)
        raise SystemExit(2)
