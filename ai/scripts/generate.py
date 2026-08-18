#!/usr/bin/env python3
"""Generate and validate native harness artifacts from roles.tsv + models.toml."""

import argparse
import json
import re
import shutil
import sys
import tomllib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import models_config

ROOT = Path(__file__).resolve().parents[2]
CANON = ROOT / "Global/_canonical"
SHARED = ROOT / "Global/_shared"
READ_ONLY = models_config.READ_ONLY
ORCHESTRATOR_TASK_ALLOW = {
    "brainstormer",
    "product-analyst",
    "project-bootstrapper",
    "architect",
    "agent-factory",
    "ux-ui-designer",
    "spec-challenger",
    "package-planner",
    "implementer",
    "frontend-engineer",
    "refactor-specialist",
    "debugger",
    "gate-runner",
    "local-gate-runner",
    "package-gate-runner",
    "package-reviewer",
    "finding-verifier",
    "repair-agent",
    "delta-reviewer",
    "security-auditor",
    "integrator",
    "test-writer",
    "runtime-verifier",
    "adversarial-judge",
    "github-release-manager",
    "memory-scribe",
    "image-describer",
    "app-runner",
}


def die(message):
    raise ValueError(message)


def load_roles(roles_path=None, models_path=None):
    """Resolution and doctrine validation live in models_config; this adds the prompt check."""
    roles = models_config.load_roles(roles_path, models_path)
    for row in roles:
        if not (CANON / "agents" / f"{row['role']}.md").is_file():
            die(f"{row['role']}: missing canonical prompt")
    return roles


def description(body):
    match = re.search(r"^#\s+(.+)$", body, re.MULTILINE)
    return match.group(1) if match else "Specialized harness agent"


# OpenCode step budgets per role. Steps are a circuit breaker for a runaway agent,
# NOT the anti-loop mechanism (feature-state.py budgets own that). Size them at
# 2-3x the expected tool-call count for the role's bounded task: a spare step is
# nearly free, while running out mid-task forces a full re-instantiation that
# re-reads everything from scratch. Adjust here; steps are harness mechanics and
# stay identical across model profiles, so they do not belong in roles.tsv.
OC_STEPS = {
    "orchestrator": 50,
    "spec-challenger": 12,
    "package-planner": 16,
    "package-reviewer": 18,
    "delta-reviewer": 12,
    "repair-agent": 24,
    "integrator": 20,
    "implementer": 30,
    "frontend-engineer": 30,
    "refactor-specialist": 18,
    "debugger": 20,
    "test-writer": 20,
    "gate-runner": 12,
    "runtime-verifier": 16,
    "app-runner": 24,
}


def oc_steps(role, capability, duty):
    if role in OC_STEPS:
        return OC_STEPS[role]
    if duty in {"audit", "judge"}:
        return 14
    if capability in {"docs-rw", "factory-rw"}:
        return 14
    if capability == "review-ro":
        return 12
    return 10


def oc_hidden(role):
    return role in {
        "spec-challenger",
        "package-planner",
        "package-reviewer",
        "repair-agent",
        "delta-reviewer",
        "integrator",
    }


# ADR-0029 (017 PKG-A2): the only model aliases guaranteed to resolve on ANY
# Claude account tier. Anything else is omitted from claude-code frontmatter.
CLAUDE_UNIVERSAL_ALIASES = {"sonnet", "opus", "haiku"}

CURSOR_DELEGATION_OVERRIDE = """

## Delegation in Cursor (this runtime only — overrides the routing section above)

Cursor is a HOST runtime of this harness, not a routing lane: it is deliberately absent from
`models_config.RUNTIMES` and `routing_core.domain.SELECTED_RUNTIMES` (032/C1). Two consequences,
and they override every `--route-decide` instruction above while you are hosted here:

1. **Never call `--route-decide`, and never call any `*_spawn.py --dispatch-*`.** A routing
   decision taken here can only ever name SOMEONE ELSE'S lane, so obeying it would spend the
   OpenCode, Codex or Claude subscription instead of the Cursor session you are actually running
   in. That is the exact failure this target exists to prevent.
2. **Delegate through Cursor's own subagents**: `/implementer <task>`, `/package-reviewer <task>`,
   or "use the <role> subagent to ...". Every roster role is installed as one
   (`~/.cursor/agents/<role>.md`); the read-only ones carry `readonly: true`, and each starts with
   a clean context — which is what reviewer independence rests on here, because every role inherits
   the single model you picked in Cursor. Record that degradation in the review evidence
   (`record-subreview --evidence` / `finalize-review-panel --evidence`): a shared model keeps
   correlated blind spots that a clean context does not remove.

Everything else in this doctrine — the phase machine, the gates, the file-first state, the
narration, the question policy — is unchanged and still binds.
"""



# ADR-0026: analysis roles whose claims need CURRENT sources (docs, prices, CVEs,
# library APIs) get the web tools; mechanical/gate roles never do (least privilege).
WEB_ANALYSIS_ROLES = {
    "architect", "brainstormer", "package-reviewer", "security-auditor",
    "debugger", "product-analyst",
}


def oc_permissions(capability, roles, role=None, yolo=False, variant_names=()):
    safe = [
        '    "git status*": allow', '    "git diff*": allow', '    "git log*": allow',
        '    "git show*": allow', '    "rg*": allow', '    "bat*": allow', '    "eza*": allow',
        '    "fd*": allow', '    "uname*": allow', '    "lsb_release*": allow', '    "sw_vers*": allow',
        '    "opencode models*": allow', '    "dotnet --list-sdks*": allow',
        '    "dotnet --list-runtimes*": allow', '    "dotnet --info*": allow',
        '    "node --version*": allow', '    "node -v*": allow', '    "npm ls*": allow',
        '    "npm list*": allow', '    "python --version*": allow', '    "python3 --version*": allow',
        '    "pip list*": allow', '    "pip3 list*": allow', '    "go version*": allow',
        '    "rustup toolchain list*": allow', '    "rustup show*": allow', '    "cargo --version*": allow',
        '    "rustc --version*": allow', '    "claude --version*": allow', '    "codex --version*": allow',
        '    "opencode --version*": allow',
        '    "cat *": allow', '    "ls*": allow', '    "find *": allow', '    "grep *": allow',
        '    "head *": allow', '    "tail *": allow', '    "wc *": allow', '    "tree*": allow',
        '    "file *": allow', '    "stat *": allow', '    "diff *": allow', '    "du *": allow',
        '    "df*": allow', '    "ps*": allow', '    "pwd*": allow', '    "which *": allow',
        '    "curl http://localhost*": allow', '    "curl http://127.0.0.1*": allow',
        '    "curl localhost*": allow', '    "curl 127.0.0.1*": allow',
    ]
    # Irreducible safety net kept as a hard deny for every role, including subagents that
    # otherwise fail open to "ask": destructive/irreversible actions never get a silent
    # auto-run, and are never worth even asking for since a "yes" can't be undone.
    always_deny = [
        '    "sudo *": deny', '    "rm -rf*": deny', '    "rm -fr*": deny',
        '    "git push --force*": deny', '    "git push -f*": deny',
        '    "git push --force-with-lease*": deny', '    "gh repo delete*": deny',
    ]
    # Shell tricks that could smuggle a denied command past a prefix match still fall
    # through to "ask" (rather than a hard block) for every role except the orchestrator,
    # since a human reviewing the literal command text is the real backstop now.
    # The yolo permission profile ([permissions] in models.toml) turns that fallthrough
    # into "allow": only always_deny and the orchestrator/local-gate-runner postures
    # remain, trading the human backstop for uninterrupted runs.
    bash_default = '    "*": allow' if yolo else '    "*": ask'
    lines = ["permission:"]
    if role == "local-gate-runner":
        lines += [
            "  read: allow", "  edit:", '    "*": deny',
            '    "ai/state/002-local-uat-identities-and-feature-state.json": allow',
            "  glob: deny", "  grep: deny", "  list: deny",
            "  task: deny", "  question: deny", "  webfetch: deny", "  websearch: deny", "  lsp: deny",
            "  skill: deny", "  todowrite: deny", "  doom_loop: deny", "  external_directory: deny",
            "  bash:", '    "*": ask',
            '    "python3 -m py_compile ai/scripts/feature-state.py": allow',
            '    "python3 -m py_compile ai/scripts/check-owned-paths.py": allow',
            '    "python3 ai/scripts/feature-state.py --help": allow',
            '    "python3 ai/scripts/check-owned-paths.py --help": allow',
            '    "python3 ai/scripts/check-owned-paths.py --state-file * --package-id * --baseline *": allow',
            '    "git diff --check": allow',
            '    "python3 ai/scripts/feature-state.py record-gate * --state-file ai/state/002-local-uat-identities-and-feature-state.json*": allow',
            '    "*.env*": deny', *always_deny,
        ]
    elif capability == "coord-ro":
        # The orchestrator is the one deliberate exception: it must delegate rather than
        # act, so its Bash stays deny-by-default with a tight read-only allowlist and no
        # "ask" escape hatch.
        hard_denies = [
            '    "* > *": deny', '    "*>*": deny', '    "* >> *": deny', '    "*>>*": deny',
            '    "* < *": deny', '    "*<*": deny', '    "* << *": deny', '    "*<<*": deny',
            '    "* | *": deny', '    "*|*": deny', '    "* && *": deny', '    "*&&*": deny',
            '    "* ; *": deny', '    "*;*": deny', '    "*`*": deny', '    "*$(*": deny', '    "*mcp.sh*": deny',
            '    "*loop.sh*": deny', '    "git add*": deny', '    "git commit*": deny',
            '    "git push*": deny', '    "gh *": deny', '    "* install*": deny', '    "sed -i*": deny',
            '    "tee *": deny', '    "rm *": deny', '    "sudo *": deny',
            '    "*--output*": deny', '    "*--ext-diff*": deny', '    "*--pre*": deny',
            '    "*--exec*": deny', '    "fd * -x *": deny', '    "node * -e *": deny',
            '    "* -exec *": deny', '    "*-toolexec*": deny',
        ]
        lines += ["  edit: deny", "  question: ask", "  doom_loop: deny", "  webfetch: allow",
                  "  websearch: allow" if yolo else "  websearch: ask", "  task:", '    "*": deny']
        lines += [f'    "{r["role"]}": allow' for r in roles if r["role"] in ORCHESTRATOR_TASK_ALLOW]
        lines += [
            f'    "{path.stem}": allow'
            for path in sorted((CANON / "opencode-agents").glob("*.md"))
            if path.stem in ORCHESTRATOR_TASK_ALLOW
        ]
        # Tier variants (contract 004 T-202): additive OpenCode-only `<role>@<tier>`
        # agents for the roles models.toml declares tiered. Not a roster entry and not
        # under Global/_canonical/opencode-agents, so neither loop above sees them —
        # without this, "*": deny blocks every tiered spawn.
        lines += [f'    "{name}": allow' for name in sorted(variant_names)]
        # The state CLI is the orchestrator's sanctioned mutation channel: it only
        # writes validated, atomic JSON under ai/state/ and enforces the physical
        # budgets. Allowing the full subcommand surface (init, record-spawn,
        # transition, ...) is what lets the orchestrator follow its own doctrine
        # without a permission prompt per delegation. Shell composition is still
        # caught by hard_denies below.
        # The routing CLI (contract 004 T-203) is a second, narrower sanctioned mutation
        # channel: `--route-decide` authorizes a writer run, and the orchestrator ALSO
        # closes runs it owns (`--route-dispatched`/`--route-terminal`, e.g. the
        # model-mismatch and worker-death doctrines below) — documented here as an
        # explicitly MUTATING-capable coord exception, narrated on use like every spawn.
        # ADR-0012/AC-19: --context is a THIRD, DISTINCT sanctioned channel — read-only
        # (cmd_context never writes, never reads a credential surface), never merged into the
        # two mutating-capable entries above.
        # SEC-P1-002/DR-01 (015 repair, delta-review round 2): a FOURTH sanctioned channel —
        # the Claude-Code-lane cross-process spawn CLI. This is the OpenCode-lane half of the
        # SAME paired fix `coord_policy.SAFE_ARGV` already carries (ai/scripts/coord_policy.py's
        # own `CLAUDE_SPAWN_CLI` entry): on any lane whose OWN host harness is OpenCode, the
        # orchestrator's Bash surface is THIS generated permission map, not coord_policy.py —
        # coord_policy.py alone (the round-1 repair) never reached the one lane where the
        # cross-lane-redirect doctrine branch actually fires. Two entries, enumerated to match
        # `claude_code_spawn.main()`'s own two mutually-exclusive modes exactly (never a bare
        # `claude_code_spawn.py*` catch-all) — the same one-entry-per-sanctioned-shape
        # granularity `--route*`/`--context*` already use above.
        lines += ["  bash:", '    "*": deny', *safe,
                  '    "python3 ai/scripts/feature-state.py *": allow',
                  # docs/adr/0020-*.md: narrower than coord_policy.py's positional-aware
                  # check can express in this glob-only permission format, but denies the
                  # canonical invocation shape orchestrator.md's own doctrine always emits
                  # (`transition INTEGRATION` immediately, never reordered) -- placed AFTER
                  # the blanket allow above so it overrides, matching this list's existing
                  # last-match-wins convention (see hard_denies below).
                  '    "python3 ai/scripts/feature-state.py transition INTEGRATION*": deny',
                  '    "python3 ~/.config/opencode/hooks/integration_action.py*": allow',
                  '    "python3 __SET_AGENTS_ROOT__/ai/scripts/set_agents_app.py --route*": allow',
                  '    "python3 __SET_AGENTS_ROOT__/ai/scripts/set_agents_app.py --routing*": allow',
                  '    "python3 __SET_AGENTS_ROOT__/ai/scripts/set_agents_app.py --context*": allow',
                  # ADR-0025: FIFTH sanctioned channel — the tool-catalog verbs (--tools,
                  # --tools-install NAME --yes, --mcp[-add|-on|-off]). Coarser than
                  # coord_policy.py's dedicated walker (glob-only format), but the CLI
                  # itself re-validates catalog membership and refuses sudo/TTY-less runs.
                  '    "python3 __SET_AGENTS_ROOT__/ai/scripts/set_agents_app.py --tools*": allow',
                  # ADR-0038: --tools-propose is meant to be part of the --tools* allow just
                  # above (validates + prints a question, never installs, never writes the
                  # catalog). --tools-approve is NOT -- it is the human approval step itself
                  # (ai/state/decisions-log.jsonl, slug tools-approve-fuera-del-canal-del-agente),
                  # and this glob format is coarser than coord_policy.py's dedicated walker: a
                  # bare "--tools*": allow would swallow it by prefix. Placed AFTER the allow
                  # above so it wins (this list's existing last-match-wins convention, same
                  # shape as --mcp-remove*: deny right after --mcp*: allow below).
                  '    "python3 __SET_AGENTS_ROOT__/ai/scripts/set_agents_app.py --tools-approve*": deny',
                  '    "python3 __SET_AGENTS_ROOT__/ai/scripts/set_agents_app.py --mcp*": allow',
                  '    "python3 __SET_AGENTS_ROOT__/ai/scripts/set_agents_app.py --mcp-remove*": deny',
                  '    "python3 __SET_AGENTS_ROOT__/ai/scripts/claude_code_spawn.py --dispatch-writer*": allow',
                  '    "python3 __SET_AGENTS_ROOT__/ai/scripts/claude_code_spawn.py --dispatch-review*": allow',
                  # ADR-0032: the OpenCode/Codex-lane spawn CLIs -- the paired OpenCode-lane
                  # half of coord_policy.SAFE_ARGV's two new enumerated entries (DR-01
                  # discipline: both sides must keep matching each module's main() modes
                  # exactly, one entry per sanctioned shape, never a bare catch-all).
                  '    "python3 __SET_AGENTS_ROOT__/ai/scripts/opencode_spawn.py --dispatch-writer*": allow',
                  '    "python3 __SET_AGENTS_ROOT__/ai/scripts/opencode_spawn.py --dispatch-review*": allow',
                  '    "python3 __SET_AGENTS_ROOT__/ai/scripts/opencode_spawn.py --dispatch-simulate*": allow',
                  '    "python3 __SET_AGENTS_ROOT__/ai/scripts/codex_spawn.py --dispatch-writer*": allow',
                  '    "python3 __SET_AGENTS_ROOT__/ai/scripts/codex_spawn.py --dispatch-review*": allow',
                  '    "python3 __SET_AGENTS_ROOT__/ai/scripts/codex_spawn.py --dispatch-simulate*": allow',
                  *hard_denies,
                  # ADR-0025: read-only gh inspection, placed AFTER hard_denies' blanket
                  # `"gh *": deny` so it overrides per this list's last-match-wins
                  # convention. Enumerated verbs only — mirrors coord_policy.SAFE.
                  '    "gh run list*": allow', '    "gh run view*": allow', '    "gh run watch*": allow',
                  '    "gh pr list*": allow', '    "gh pr view*": allow', '    "gh pr checks*": allow',
                  '    "gh pr status*": allow', '    "gh pr diff*": allow',
                  '    "gh workflow list*": allow', '    "gh workflow view*": allow',
                  '    "gh issue list*": allow', '    "gh issue view*": allow',
                  '    "gh auth status*": allow', '    "gh repo view*": allow']
    elif capability == "review-ro":
        lines += ["  edit: deny", "  question: deny", "  doom_loop: deny", "  task: deny", "  bash:", bash_default, *safe, *always_deny]
    elif capability == "gate-ro":
        lines += ["  edit: deny", "  question: deny", "  doom_loop: deny", "  task: deny", "  bash:", bash_default,
                  '    "./ai/scripts/verify.sh*": allow', '    "npm test*": allow',
                  '    "npm run test*": allow', '    "npm run lint*": allow',
                  '    "npm run typecheck*": allow', '    "npm run build*": allow',
                  '    "dotnet test*": allow', '    "go test*": allow', '    "cargo test*": allow',
                  '    "python -m pytest*": allow', *safe, *always_deny]
    elif capability == "release":
        lines += ["  edit: deny", "  question: deny", "  doom_loop: deny", "  task: deny", "  bash:", bash_default, *safe,
                  '    "python3 ~/.config/opencode/hooks/release_action.py*": allow', *always_deny]
    elif capability == "run-ro":
        lines += ["  edit: deny", "  question: deny", "  doom_loop: deny", "  task: deny", "  bash:", bash_default, *safe,
                  '    "./ai/scripts/run.sh*": allow', '    "./ai/scripts/verify.sh*": allow',
                  '    "./ai/scripts/e2e.sh*": allow',
                  '    "./ai/scripts/mcp.sh browser-gate*": allow',
                  '    "./ai/scripts/mcp.sh ensure-brave-cdp*": allow',
                  '    "./ai/scripts/mcp.sh on playwright*": allow',
                  '    "./ai/scripts/mcp.sh on brave-cdp*": allow',
                  '    "./ai/scripts/mcp.sh off playwright*": allow',
                  '    "./ai/scripts/mcp.sh off brave-cdp*": allow',
                  '    "./ai/scripts/mcp.sh status*": allow', *always_deny]
    else:
        lines += ["  edit: allow", "  question: deny", "  doom_loop: deny", "  task: deny", "  bash:", bash_default, *safe, *always_deny]
    # ADR-0026: web tools for the analysis roles, in every capability branch that
    # didn't already set them (coord-ro sets its own pair above and is not in the set).
    if role in WEB_ANALYSIS_ROLES and not any(l.startswith("  webfetch:") for l in lines):
        lines[1:1] = ["  webfetch: allow", "  websearch: allow"]
    return "\n".join(lines)


def claude_tools(capability, roles, role=None):
    # ADR-0026: the analysis set researches with sources; nothing else gets the web.
    web = ", WebSearch, WebFetch" if role in WEB_ANALYSIS_ROLES else ""
    if role == "local-gate-runner":
        return "Read, Bash"
    if capability == "coord-ro":
        names = ", ".join(r["role"] for r in roles if r["role"] in ORCHESTRATOR_TASK_ALLOW)
        return f"Read, Grep, Glob, Bash{web}, Agent({names})"
    if capability in READ_ONLY or capability in {"gate-ro", "release", "run-ro"}:
        return f"Read, Grep, Glob, Bash{web}"
    return f"Read, Grep, Glob, Edit, Write, Bash{web}"


def pi_tools(capability, role=None):
    """AC-03: pi-subagents' own tools vocabulary (comma-separated, lowercase — observed
    values: read, grep, find, ls, bash, edit, write, plus the open `subagent` delegation
    token). The ceiling invariant: no capability CLASS granted here that the same role's
    Claude Code grant (claude_tools()) lacks — Glob has no single pi equivalent, so
    `find`/`ls` together stand in for it; `subagent` is the one deliberate, documented
    divergence, granted only to the coord-ro class (see AC-03 user decision 3)."""
    if role == "local-gate-runner":
        return "read, bash"
    if capability == "coord-ro":
        return "read, grep, find, ls, bash, subagent"
    if capability in READ_ONLY or capability in {"gate-ro", "release", "run-ro"}:
        return "read, grep, find, ls, bash"
    return "read, grep, find, ls, bash, edit, write"


def frontmatter_hook(capability, role=None):
    if role == "local-gate-runner":
        return """hooks:
  PreToolUse:
    - matcher: \"Bash\"
      hooks:
        - type: command
          command: \"python3 ~/.claude/hooks/claude_local_gate_guard.py\"
"""
    if capability not in {"coord-ro", "review-ro", "gate-ro", "release", "run-ro"}:
        return ""
    # coord-ro (orchestrator) keeps the strict deny-by-default guard. release keeps its
    # gated-wrapper-only guard. Every other read-only role (review-ro/gate-ro/run-ro) shares
    # the fail-open guard: only the short always-dangerous list blocks, everything else asks.
    script = {"release": "claude_release_guard.py"}.get(capability, "claude_bash_guard.py" if capability == "coord-ro" else "claude_ask_guard.py")
    return """hooks:
  PreToolUse:
    - matcher: \"Bash\"
      hooks:
        - type: command
          command: \"python3 ~/.claude/hooks/%s\"
""" % script


def copy_tree(source, target):
    if source.exists():
        shutil.copytree(source, target, dirs_exist_ok=True)


def generate_pi_prompts(out):
    """AC-06: Global/_canonical/commands/*.md -> Global/pi/prompts/*.md. `$ARGUMENTS`
    needs no translation (pi's own template engine treats it as a native alias for
    `$@`) and copies through verbatim. The `agent:` frontmatter key has no pi
    prompt-template equivalent (docs/prompt-templates.md's Format section only
    recognizes `description`/`argument-hint`) — per user decision 2 it is never
    silently dropped: it is stripped from the emitted frontmatter and folded into the
    body as an explicit `subagent({ agent: ..., task: ... })` instruction instead, so
    the role binding still exists somewhere `pi-subagents` can act on it."""
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    for path in sorted((CANON / "commands").glob("*.md")):
        text = path.read_text(encoding="utf-8")
        if not (text.startswith("---\n") and "\n---\n" in text[4:]):
            die(f"{path}: invalid frontmatter")
        end = text.index("\n---\n", 4)
        header_lines = text[4:end].splitlines()
        body = text[end + 5:]
        agent = None
        kept_lines = []
        for line in header_lines:
            if line.startswith("agent:"):
                agent = line.split(":", 1)[1].strip()
                continue
            kept_lines.append(line)
        out_lines = ["---", *kept_lines, "---", ""]
        if agent:
            out_lines.append(
                f'Before doing anything else, invoke `subagent({{ agent: "{agent}", '
                f'task: "<the request/arguments below>" }})` to delegate this to the `{agent}` role — '
                "never handle it directly."
            )
            out_lines.append("")
        out_lines.append(body)
        (out / path.name).write_text("\n".join(out_lines), encoding="utf-8")


def write_cursor_rule(path, doctrine):
    """032/C1 (AC-05): the harness doctrine as a Cursor PROJECT rule.

    Cursor has no user-level rules file: `~/.cursor/agents` and `~/.cursor/skills` are
    global, rules are not (verified 2026-08-18, https://cursor.com/docs/context/rules).
    `alwaysApply: true` is therefore the only shape that puts this doctrine in EVERY
    session without the user remembering to @-mention it. The body is the very same
    AGENTS.cursor.md the target ships, so the two can never say different things.
    """
    body = doctrine.lstrip("\n")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("---\nalwaysApply: true\n---\n\n" + body, encoding="utf-8")


def write_indexes(out):
    for harness in ("opencode", "claude-code", "codex", "pi", "cursor"):
        base = out / harness
        files = sorted(str(p.relative_to(base)) for p in base.rglob("*") if p.is_file() and p.name != "managed-files.txt")
        (base / "managed-files.txt").write_text("\n".join(files) + "\n", encoding="utf-8")


def yolofy(node):
    """Flip every 'ask' in a permission tree to 'allow'; denies and allows survive."""
    if node == "ask":
        return "allow"
    if isinstance(node, dict):
        return {key: yolofy(value) for key, value in node.items()}
    return node


def _roster_filtered_role_tiers(roles, role_tiers):
    """PKG-N02: variant EMISSION is always driven by `roles` (the active roster); the
    EXPECTATION (`variant_names`/`variant_expected`) must be built from that same
    roster-filtered set, never straight off `models_config.load_role_tiers`'s raw
    result — otherwise a tiered role absent from the active roster silently produces
    an expected-but-never-emitted variant, surfacing later as an opaque "generated
    role set mismatch" instead of a targeted diagnostic. Fails closed: a tiers table
    for a role outside the roster is a stale/mistaken models.toml entry, named
    explicitly, never silently dropped or silently honored."""
    roster_names = {row["role"] for row in roles}
    orphaned = sorted(set(role_tiers) - roster_names)
    if orphaned:
        die(
            f"models.toml declares [roles.<role>.tiers] for role(s) {orphaned} not present "
            f"in the active roster (roles.tsv) — remove the stale tier table or add the "
            f"role to roles.tsv"
        )
    return role_tiers


def generate(out, roles_path=None, models_path=None, routes_path=None):
    roles = load_roles(roles_path, models_path)
    config = models_config.load_config(models_path)
    role_tiers = _roster_filtered_role_tiers(roles, models_config.load_role_tiers(config))
    variant_names = sorted(f"{role}@{tier}" for role, tiers in role_tiers.items() for tier in tiers)
    yolo = models_config.permission_profile(models_path) == "yolo"
    if out.exists():
        shutil.rmtree(out)
    for harness in ("opencode", "claude-code", "codex", "pi", "cursor"):
        (out / harness).mkdir(parents=True)

    bodies = {}
    for row in roles:
        body = (CANON / "agents" / f"{row['role']}.md").read_text(encoding="utf-8")
        bodies[row["role"]] = body
        desc = description(body)
        oc = "\n".join([
            "---", f"description: {json.dumps(desc)}", f"mode: {row['mode']}",
            f"model: {row['opencode_model']}", f"temperature: {row['temperature']}",
            f"steps: {oc_steps(row['role'], row['capability'], row['duty'])}",
            ("hidden: true" if oc_hidden(row["role"]) else ""),
            oc_permissions(row["capability"], roles, row["role"], yolo, variant_names), "---", "", body,
        ])
        oc = oc.replace("\n\npermission:", "\npermission:")
        path = out / "opencode/agents" / f"{row['role']}.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(oc, encoding="utf-8")

        # ADR-0029 (017 PKG-A2): the frontmatter only ever pins a UNIVERSAL alias —
        # one that resolves on any Claude account. A curated non-universal id (e.g.
        # `fable`) is omitted instead: the agent inherits the session model, and the
        # routed spawn path already overrides with --model regardless (spec 015).
        model_line = ([f"model: {row['claude_model']}"]
                      if row["claude_model"] in CLAUDE_UNIVERSAL_ALIASES else [])
        claude = "\n".join([
            "---", f"name: {row['role']}", f"description: {json.dumps(desc)}",
            f"tools: {claude_tools(row['capability'], roles, row['role'])}", *model_line,
            frontmatter_hook(row["capability"], row["role"]).rstrip(), "---", "", body,
        ])
        path = out / "claude-code/agents" / f"{row['role']}.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(claude, encoding="utf-8")

        sandbox = "read-only" if (
            row["capability"] in READ_ONLY
            or row["capability"] == "release"
            or row["role"] == "gate-runner"
        ) else "workspace-write"
        escaped = body.replace('"""', '\\\"\\\"\\\"')
        if row["capability"] == "release":
            escaped += "\n\nCodex release-manager is read-only in this harness. Prepare the exact gated commands and report readiness; do not execute mutations here."
        if row["role"] == "local-gate-runner":
            escaped += "\n\nCodex requires workspace-write only because record-gate writes ai/state/002-local-uat-identities-and-feature-state.json. Do not write anything else."
        codex = "\n".join([
            f"name = {json.dumps(row['role'])}", f"description = {json.dumps(desc)}",
            f"model = {json.dumps(row['codex_model'])}",
            f"model_reasoning_effort = {json.dumps(row['codex_effort'])}",
            f"sandbox_mode = {json.dumps(sandbox)}", 'developer_instructions = """', escaped.rstrip(), '"""', "",
        ])
        path = out / "codex/agents" / f"{row['role']}.toml"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(codex, encoding="utf-8")

        pi_lines = [
            "---", f"name: {row['role']}", f"description: {json.dumps(desc)}",
            f"tools: {pi_tools(row['capability'], row['role'])}", "systemPromptMode: replace",
        ]
        if row["capability"] == "coord-ro":
            pi_lines.append("maxSubagentDepth: 2")
        pi_lines += ["---", "", body]
        pi = "\n".join(pi_lines)
        path = out / "pi/agents" / f"{row['role']}.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(pi, encoding="utf-8")

        # 032/C1 (AC-01, AC-06): Cursor subagents. Frontmatter fields verified 2026-08-18
        # against https://cursor.com/docs/subagents -- name/description/model/readonly/
        # is_background, and NOTHING else. `model: inherit` is the whole point: Cursor is a
        # host runtime, not a routing lane, so no models.toml value reaches it and no role
        # can spend a quota the user did not pick in the UI. `readonly` reuses the SAME
        # predicate Codex's `sandbox_mode` already uses above -- one audited definition of
        # "this role must not write", not a second one that could drift from it.
        cursor = "\n".join([
            "---", f"name: {row['role']}", f"description: {json.dumps(desc)}",
            "model: inherit", f"readonly: {'true' if sandbox == 'read-only' else 'false'}",
            "---", "", body + (CURSOR_DELEGATION_OVERRIDE if row["capability"] == "coord-ro" else ""),
        ])
        path = out / "cursor/agents" / f"{row['role']}.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(cursor, encoding="utf-8")

    # Tier variants (contract 004 T-202): additive, OpenCode-ONLY `<role>@<tier>` agents
    # for the roles models.toml declares tiered (models_config.load_role_tiers). Same
    # prompt body, same permissions, same step budget as the base agent — the ONLY line
    # that differs is `model:`. The base agent above is unchanged and keeps being
    # emitted for every harness; Claude Code and Codex never receive a variant.
    for row in roles:
        tiers = role_tiers.get(row["role"])
        if not tiers:
            continue
        body = bodies[row["role"]]
        desc = description(body)
        for tier in models_config.MODEL_TIERS:
            oc = "\n".join([
                "---", f"description: {json.dumps(desc)}", f"mode: {row['mode']}",
                f"model: {tiers[tier]}", f"temperature: {row['temperature']}",
                f"steps: {oc_steps(row['role'], row['capability'], row['duty'])}",
                ("hidden: true" if oc_hidden(row["role"]) else ""),
                oc_permissions(row["capability"], roles, row["role"], yolo, variant_names), "---", "", body,
            ])
            oc = oc.replace("\n\npermission:", "\npermission:")
            path = out / "opencode/agents" / f"{row['role']}@{tier}.md"
            path.write_text(oc, encoding="utf-8")

    copy_tree(CANON / "opencode-agents", out / "opencode/agents")

    # 032/C1 (AC-05): Cursor reads slash commands ONLY from a project's `.cursor/commands/`
    # -- there is no user-level equivalent (verified 2026-08-18). They are emitted into the
    # target anyway so `bootstrap_project.py` has one installed source to project into a
    # project, exactly as it already does for `ai/scripts` templates.
    for harness in ("opencode", "claude-code", "cursor"):
        copy_tree(CANON / "commands", out / harness / "commands")
    for harness in ("opencode", "claude-code", "codex", "pi", "cursor"):
        copy_tree(CANON / "skills", out / harness / "skills")
    generate_pi_prompts(out / "pi/prompts")

    shutil.copy2(SHARED / "AGENTS.opencode.md", out / "opencode/AGENTS.md")
    shutil.copy2(SHARED / "CLAUDE.md", out / "claude-code/CLAUDE.md")
    shutil.copy2(SHARED / "AGENTS.codex.md", out / "codex/AGENTS.md")
    shutil.copy2(SHARED / "config.codex.snippet.toml", out / "codex/config.snippet.toml")
    shutil.copy2(SHARED / "AGENTS.pi.md", out / "pi/AGENTS.md")
    shutil.copy2(SHARED / "AGENTS.cursor.md", out / "cursor/AGENTS.md")
    write_cursor_rule(out / "cursor/rules/00-harness.mdc",
                      (SHARED / "AGENTS.cursor.md").read_text(encoding="utf-8"))

    oc_config = json.loads((SHARED / "opencode.json").read_text(encoding="utf-8"))
    oc_config["model"] = next(r["opencode_model"] for r in roles if r["role"] == "orchestrator")
    oc_config["small_model"] = models_config.small_model(models_path)
    if yolo:
        oc_config["permission"] = yolofy(oc_config.get("permission", {}))
    for item in oc_config.get("mcp", {}).values():
        item["enabled"] = False
    (out / "opencode/opencode.json").write_text(json.dumps(oc_config, indent=2) + "\n", encoding="utf-8")

    overlay = {"enabledPlugins": {"engram@engram": False}, "disabledMcpjsonServers": ["engram", "context7", "playwright", "brave-cdp"]}
    (out / "claude-code/settings.overlay.json").write_text(json.dumps(overlay, indent=2) + "\n", encoding="utf-8")
    hooks = out / "claude-code/hooks"
    hooks.mkdir()
    shutil.copy2(ROOT / "ai/scripts/coord_policy.py", hooks / "coord_policy.py")
    shutil.copy2(ROOT / "ai/scripts/claude_bash_guard.py", hooks / "claude_bash_guard.py")
    shutil.copy2(ROOT / "ai/scripts/claude_ask_guard.py", hooks / "claude_ask_guard.py")
    shutil.copy2(ROOT / "ai/scripts/claude_local_gate_guard.py", hooks / "claude_local_gate_guard.py")
    shutil.copy2(ROOT / "ai/scripts/claude_release_guard.py", hooks / "claude_release_guard.py")
    shutil.copy2(ROOT / "ai/scripts/release_action.py", hooks / "release_action.py")
    for harness in ("opencode", "codex", "cursor"):
        hooks = out / harness / "hooks"
        hooks.mkdir()
        shutil.copy2(ROOT / "ai/scripts/release_action.py", hooks / "release_action.py")
        shutil.copy2(ROOT / "ai/scripts/release_gate.py", hooks / "release_gate.py")
    shutil.copy2(ROOT / "ai/scripts/release_gate.py", out / "claude-code/hooks/release_gate.py")
    # docs/adr/0020-*.md: the integration triad. Unlike release_gate.py (fully
    # self-contained JSON I/O), integration_gate.py genuinely imports
    # feature_state_lib.candidate_identity -- reusing the one freeze/re-derive
    # implementation rather than forking a second copy of git tree-hash logic into
    # the hooks directory. A live hooks install has no other feature_state_lib on
    # its sys.path (hooks live outside any project's ai/scripts/, per ADR-0008's
    # HARNESS_HOME/PROJECT_ROOT split), so the package is copied alongside it.
    for harness in ("claude-code", "opencode", "codex", "cursor"):
        hooks = out / harness / "hooks"
        shutil.copy2(ROOT / "ai/scripts/integration_gate.py", hooks / "integration_gate.py")
        shutil.copy2(ROOT / "ai/scripts/integration_action.py", hooks / "integration_action.py")
        shutil.copytree(ROOT / "ai/scripts/feature_state_lib", hooks / "feature_state_lib",
                        dirs_exist_ok=True, ignore=shutil.ignore_patterns("__pycache__"))
    write_indexes(out)
    validate(out, roles, role_tiers, routes_path)


def _opencode_projected_route(model):
    """Pure, offline projection (contract 004 T-202): `openai/<M>` projects to the
    catalog identity (provider=openai-codex, model=<M>) — the only routes.v1.toml
    provider reachable from the OpenCode lane (anthropic runs through claude-code,
    not OpenCode). Any other prefix (the `opencode/*` zen aggregator included) never
    projects. No live probes: this is a static lookup over the full catalog, never a
    runtime/subscription/availability check."""
    prefix, sep, rest = model.partition("/")
    if not sep or prefix != "openai" or not rest:
        return None
    return ("openai-codex", rest)


def _load_routes(routes_path):
    path = Path(routes_path)
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    routes = data.get("routes")
    if not isinstance(routes, list):
        die(f"{path}: missing [[routes]]")
    return routes


def check_variant_catalog_coherence(role_tiers, routes_path):
    """Build-time gate (AC-06): each declared (role, tier) variant model must equal the
    model of EXACTLY ONE routes.v1.toml row that shares its tier, is opencode-reachable
    (see _opencode_projected_route), and lists the role — under a full-inventory
    assumption (no probing). Zero or ambiguous matches fail the build."""
    routes = _load_routes(routes_path)
    for role, tiers in role_tiers.items():
        for tier, model in tiers.items():
            projected = _opencode_projected_route(model)
            matches = [
                row for row in routes
                if projected is not None
                and row.get("provider") == projected[0]
                and row.get("model") == projected[1]
                and row.get("tier") == tier
                and role in (row.get("roles") or ())
            ]
            if len(matches) != 1:
                die(
                    f"variant coherence: {role}@{tier} model {model!r} projects to "
                    f"{len(matches)} catalog rows (expected exactly 1, full-inventory, "
                    f"offline projection over {Path(routes_path).name})"
                )


def validate_pi_target(roles):
    """013-pi-interactive-target AC-02 (round 2, C-01): kept, not removed. pi DOES get
    a generated agent tree now — the per-role loop above emits a real
    `Global/pi/agents/<role>.md` for every active-roster role. This function is the
    explicit, pi-target-scoped
    assertion that every active-roster role's canonical prompt (`Global/_canonical/
    agents/<role>.md`) exists on the SOURCE side — the one invariant every generated
    `Global/pi/agents/<role>.md` file transitively depends on, since each is a direct
    copy of that same canonical body. `load_roles` already enforces this upstream in
    every path that reaches `validate()`; this re-asserts it as a second, explicit,
    pi-named check. It is distinct from, and not duplicated by, the two `validate()`
    loops above that gained a `pi` tuple member: those check the GENERATED pi output
    (frontmatter validity, role-set completeness); this one checks the source. The
    dispatch lane (`ai/scripts/set_agents_spawn.py`) also still reads the same
    canonical prompt verbatim via `--append-system-prompt` — see docs/adr/0007-pi-lane.md,
    amended by docs/adr/0017-pi-interactive-target.md for this feature's own additions."""
    for row in roles:
        if not (CANON / "agents" / f"{row['role']}.md").is_file():
            die(f"pi target: {row['role']}: missing canonical prompt")


def validate_cursor_target(out):
    """032/C1 (AC-01, AC-06): Cursor is a host runtime, never a routing lane.

    The one thing that must never regress here is the model line: the moment a concrete
    model id lands in a Cursor agent, the harness starts spending a subscription the user
    never chose in the UI -- which is the exact failure that motivated this target.
    """
    rule = out / "cursor/rules/00-harness.mdc"
    if not rule.exists() or not rule.read_text(encoding="utf-8").startswith("---\nalwaysApply: true\n---\n"):
        die("cursor: rules/00-harness.mdc must declare alwaysApply: true")
    for path in (out / "cursor/agents").glob("*.md"):
        text = path.read_text(encoding="utf-8")
        if "\nmodel: inherit\n" not in text:
            die(f"{path}: cursor agents must inherit the session model")
        if "\nreadonly: true\n" not in text and "\nreadonly: false\n" not in text:
            die(f"{path}: cursor agents must declare readonly explicitly")


def validate(out, roles=None, role_tiers=None, routes_path=None, models_path=None):
    roles = roles or load_roles(models_path=models_path)
    if role_tiers is None:
        role_tiers = models_config.load_role_tiers(models_config.load_config(models_path))
    role_tiers = _roster_filtered_role_tiers(roles, role_tiers)
    routes_path = routes_path or (ROOT / "ai/catalogs/routes.v1.toml")
    json.loads((out / "opencode/opencode.json").read_text(encoding="utf-8"))
    json.loads((out / "claude-code/settings.overlay.json").read_text(encoding="utf-8"))
    for path in (out / "codex/agents").glob("*.toml"):
        data = tomllib.loads(path.read_text(encoding="utf-8"))
        for key in ("name", "description", "developer_instructions", "model", "sandbox_mode"):
            if not data.get(key):
                die(f"{path}: missing {key}")
    for harness in ("opencode", "claude-code", "pi", "cursor"):
        for path in (out / harness / "agents").glob("*.md"):
            text = path.read_text(encoding="utf-8")
            if not text.startswith("---\n") or "\n---\n" not in text[4:]:
                die(f"{path}: invalid frontmatter")
    expected = {r["role"] for r in roles}
    variant_expected = {f"{role}@{tier}" for role, tiers in role_tiers.items() for tier in tiers}
    opencode_only = {p.stem for p in (CANON / "opencode-agents").glob("*.md")}
    for harness, suffix in (("opencode", ".md"), ("claude-code", ".md"), ("codex", ".toml"),
                            ("pi", ".md"), ("cursor", ".md")):
        actual = {p.stem for p in (out / harness / "agents").glob(f"*{suffix}")}
        harness_expected = expected | opencode_only | variant_expected if harness == "opencode" else expected
        if actual != harness_expected:
            die(f"{harness}: generated role set mismatch")
    orchestrator = (out / "opencode/agents/orchestrator.md").read_text(encoding="utf-8")
    for role in ORCHESTRATOR_TASK_ALLOW:
        if f'    "{role}": allow' not in orchestrator:
            die(f"orchestrator cannot delegate required role: {role}")
    for name in variant_expected:
        if f'    "{name}": allow' not in orchestrator:
            die(f"orchestrator cannot delegate required tier variant: {name}")
    check_variant_catalog_coherence(role_tiers, routes_path)
    validate_pi_target(roles)
    validate_cursor_target(out)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--roles")
    parser.add_argument("--models")
    parser.add_argument("--routes")
    args = parser.parse_args()
    try:
        generate(Path(args.output), args.roles, args.models, args.routes)
    except (OSError, ValueError, json.JSONDecodeError, tomllib.TOMLDecodeError) as exc:
        print(f"CHECK_FAILED: {exc}", file=sys.stderr)
        return 2
    print("CHECK_PASS: generated and validated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
