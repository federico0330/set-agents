#!/usr/bin/env python3
"""Deny-by-default command policy for read-only coordination."""

import re
import shlex
import sys

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
    # ADR-0025 resolve-first: READ-ONLY GitHub inspection for the coordinator — CI runs,
    # PR state, workflow listings, auth status. Enumerated subcommands only: `gh api`,
    # `gh pr merge`, `gh release`, etc. stay denied (mutating or arbitrary-request
    # surfaces), and ALWAYS_DENY keeps `gh repo delete` hard-blocked for every role.
    r"gh (run (list|view|watch)|pr (list|view|checks|status|diff)|workflow (list|view)|issue (list|view)|auth status|repo view)(\s|$)",
    r"(cat|ls|find|grep|head|tail|wc|tree|file|stat|diff|du|df|ps|pwd|which)(\s|$)",
    r"curl (?:-[A-Za-z]+\s+)*(?:http://)?(?:localhost|127\.0\.0\.1)(?::\d+)?(?:/|\s|$)",
    # Sanctioned mutation channel: the state CLI validates every transition and
    # writes only atomic JSON under ai/state/. FORBIDDEN_SYNTAX still blocks any
    # shell composition around it. `_blocks_integration_transition` (below) denies
    # the one shape this blanket allow must NOT cover: a direct, unwrapped
    # `transition ... INTEGRATION` -- that phase requires the receipt-checked
    # wrapper (docs/adr/0020-*.md), the next SAFE entry.
    r"python3 ai/scripts/feature-state\.py \S+",
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


def _rest_allowed(rest: list[str], modifiers: dict[str, int]) -> bool:
    i = 0
    while i < len(rest):
        nargs = modifiers.get(rest[i])
        if nargs is None:
            return False
        i += 1 + nargs
    return True

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


def _tools_channel_allowed(argv: list[str]) -> bool:
    """ADR-0025 sanctioned tool-catalog channel: `--tools`, `--tools-install NAME
    [--yes|--dry-run]`, `--mcp[-add|-on|-off] [NAME] [--harness H]` -- and nothing
    else. A dedicated positional-aware walker (the `_transition_blocks_integration`
    pattern), never a trailing-wildcard regex: `--tools-install` takes a bare NAME
    value, which `SAFE_ARGV`'s flag-only `modifiers` grammar cannot express, and
    the historical `--context --scaffold X` escape (see SAFE_ARGV's SEC-001 note)
    shows exactly what a lax rest-of-argv check costs. `set_agents_app.py` itself
    still re-checks everything (catalog membership, sudo refusal, TTY/--yes); this
    walker only narrows which Bash surface can reach it."""
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
    if _argv_allowed(argv):
        return True
    if _tools_channel_allowed(argv):
        return True
    return any(re.fullmatch(pattern + r".*", command) for pattern in SAFE)


if __name__ == "__main__":
    if len(sys.argv) != 2 or not allowed(sys.argv[1]):
        print("Blocked by coord-ro policy", file=sys.stderr)
        raise SystemExit(2)
