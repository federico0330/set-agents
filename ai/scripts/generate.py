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


def load_roles(profile, roles_path=None, models_path=None):
    """Resolution and doctrine validation live in models_config; this adds the prompt check."""
    roles = models_config.load_roles(profile, roles_path, models_path)
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


def oc_permissions(capability, roles, role=None):
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
        lines += ["  edit: deny", "  question: ask", "  doom_loop: deny", "  webfetch: allow", "  websearch: ask", "  task:", '    "*": deny']
        lines += [f'    "{r["role"]}": allow' for r in roles if r["role"] in ORCHESTRATOR_TASK_ALLOW]
        lines += [
            f'    "{path.stem}": allow'
            for path in sorted((CANON / "opencode-agents").glob("*.md"))
            if path.stem in ORCHESTRATOR_TASK_ALLOW
        ]
        # The state CLI is the orchestrator's sanctioned mutation channel: it only
        # writes validated, atomic JSON under ai/state/ and enforces the physical
        # budgets. Allowing the full subcommand surface (init, record-spawn,
        # transition, ...) is what lets the orchestrator follow its own doctrine
        # without a permission prompt per delegation. Shell composition is still
        # caught by hard_denies below.
        lines += ["  bash:", '    "*": deny', *safe,
                  '    "python3 ai/scripts/feature-state.py *": allow', *hard_denies]
    elif capability == "review-ro":
        lines += ["  edit: deny", "  question: deny", "  doom_loop: deny", "  task: deny", "  bash:", '    "*": ask', *safe, *always_deny]
    elif capability == "gate-ro":
        lines += ["  edit: deny", "  question: deny", "  doom_loop: deny", "  task: deny", "  bash:", '    "*": ask',
                  '    "./ai/scripts/verify.sh*": allow', '    "npm test*": allow',
                  '    "npm run test*": allow', '    "npm run lint*": allow',
                  '    "npm run typecheck*": allow', '    "npm run build*": allow',
                  '    "dotnet test*": allow', '    "go test*": allow', '    "cargo test*": allow',
                  '    "python -m pytest*": allow', *safe, *always_deny]
    elif capability == "release":
        lines += ["  edit: deny", "  question: deny", "  doom_loop: deny", "  task: deny", "  bash:", '    "*": ask', *safe,
                  '    "python3 ~/.config/opencode/hooks/release_action.py*": allow', *always_deny]
    elif capability == "run-ro":
        lines += ["  edit: deny", "  question: deny", "  doom_loop: deny", "  task: deny", "  bash:", '    "*": ask', *safe,
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
        lines += ["  edit: allow", "  question: deny", "  doom_loop: deny", "  task: deny", "  bash:", '    "*": ask', *safe, *always_deny]
    return "\n".join(lines)


def claude_tools(capability, roles, role=None):
    if role == "local-gate-runner":
        return "Read, Bash"
    if capability == "coord-ro":
        names = ", ".join(r["role"] for r in roles if r["role"] in ORCHESTRATOR_TASK_ALLOW)
        return f"Read, Grep, Glob, Bash, Agent({names})"
    if capability in READ_ONLY or capability in {"gate-ro", "release", "run-ro"}:
        return "Read, Grep, Glob, Bash"
    return "Read, Grep, Glob, Edit, Write, Bash"


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


def write_indexes(out):
    for harness in ("opencode", "claude-code", "codex"):
        base = out / harness
        files = sorted(str(p.relative_to(base)) for p in base.rglob("*") if p.is_file() and p.name != "managed-files.txt")
        (base / "managed-files.txt").write_text("\n".join(files) + "\n")


def generate(out, profile, roles_path=None, models_path=None):
    roles = load_roles(profile, roles_path, models_path)
    if out.exists():
        shutil.rmtree(out)
    for harness in ("opencode", "claude-code", "codex"):
        (out / harness).mkdir(parents=True)

    for row in roles:
        body = (CANON / "agents" / f"{row['role']}.md").read_text()
        desc = description(body)
        oc = "\n".join([
            "---", f"description: {json.dumps(desc)}", f"mode: {row['mode']}",
            f"model: {row['opencode_model']}", f"temperature: {row['temperature']}",
            f"steps: {oc_steps(row['role'], row['capability'], row['duty'])}",
            ("hidden: true" if oc_hidden(row["role"]) else ""),
            oc_permissions(row["capability"], roles, row["role"]), "---", "", body,
        ])
        if row["role"] == "orchestrator":
            oc += (
                "\n\nFor `replenishment-v2` package `RPL-P0A` only, route deterministic package gates to "
                "`package-gate-runner`. That agent is unavailable for every other feature, package, worktree, "
                "and baseline."
            )
        oc = oc.replace("\n\npermission:", "\npermission:")
        path = out / "opencode/agents" / f"{row['role']}.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(oc)

        claude = "\n".join([
            "---", f"name: {row['role']}", f"description: {json.dumps(desc)}",
            f"tools: {claude_tools(row['capability'], roles, row['role'])}", f"model: {row['claude_model']}",
            frontmatter_hook(row["capability"], row["role"]).rstrip(), "---", "", body,
        ])
        path = out / "claude-code/agents" / f"{row['role']}.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(claude)

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
        path.write_text(codex)

    copy_tree(CANON / "opencode-agents", out / "opencode/agents")

    for harness in ("opencode", "claude-code"):
        copy_tree(CANON / "commands", out / harness / "commands")
    for harness in ("opencode", "claude-code", "codex"):
        copy_tree(CANON / "skills", out / harness / "skills")

    shutil.copy2(SHARED / "AGENTS.opencode.md", out / "opencode/AGENTS.md")
    shutil.copy2(SHARED / "CLAUDE.md", out / "claude-code/CLAUDE.md")
    shutil.copy2(SHARED / "AGENTS.codex.md", out / "codex/AGENTS.md")
    shutil.copy2(SHARED / "config.codex.snippet.toml", out / "codex/config.snippet.toml")

    oc_config = json.loads((SHARED / "opencode.json").read_text())
    oc_config["model"] = next(r["opencode_model"] for r in roles if r["role"] == "orchestrator")
    oc_config["small_model"] = models_config.small_model(profile, models_path)
    for item in oc_config.get("mcp", {}).values():
        item["enabled"] = False
    (out / "opencode/opencode.json").write_text(json.dumps(oc_config, indent=2) + "\n")

    overlay = {"enabledPlugins": {"engram@engram": False}, "disabledMcpjsonServers": ["engram", "context7", "playwright", "brave-cdp"]}
    (out / "claude-code/settings.overlay.json").write_text(json.dumps(overlay, indent=2) + "\n")
    hooks = out / "claude-code/hooks"
    hooks.mkdir()
    shutil.copy2(ROOT / "ai/scripts/coord_policy.py", hooks / "coord_policy.py")
    shutil.copy2(ROOT / "ai/scripts/claude_bash_guard.py", hooks / "claude_bash_guard.py")
    shutil.copy2(ROOT / "ai/scripts/claude_ask_guard.py", hooks / "claude_ask_guard.py")
    shutil.copy2(ROOT / "ai/scripts/claude_local_gate_guard.py", hooks / "claude_local_gate_guard.py")
    shutil.copy2(ROOT / "ai/scripts/claude_release_guard.py", hooks / "claude_release_guard.py")
    shutil.copy2(ROOT / "ai/scripts/release_action.py", hooks / "release_action.py")
    for harness in ("opencode", "codex"):
        hooks = out / harness / "hooks"
        hooks.mkdir()
        shutil.copy2(ROOT / "ai/scripts/release_action.py", hooks / "release_action.py")
        shutil.copy2(ROOT / "ai/scripts/release_gate.py", hooks / "release_gate.py")
    shutil.copy2(ROOT / "ai/scripts/release_gate.py", out / "claude-code/hooks/release_gate.py")
    write_indexes(out)
    validate(out, roles)


def validate(out, roles=None):
    roles = roles or load_roles((ROOT / "active-profile").read_text().strip())
    json.loads((out / "opencode/opencode.json").read_text())
    json.loads((out / "claude-code/settings.overlay.json").read_text())
    for path in (out / "codex/agents").glob("*.toml"):
        data = tomllib.loads(path.read_text())
        for key in ("name", "description", "developer_instructions", "model", "sandbox_mode"):
            if not data.get(key):
                die(f"{path}: missing {key}")
    for harness in ("opencode", "claude-code"):
        for path in (out / harness / "agents").glob("*.md"):
            text = path.read_text()
            if not text.startswith("---\n") or "\n---\n" not in text[4:]:
                die(f"{path}: invalid frontmatter")
    expected = {r["role"] for r in roles}
    opencode_only = {p.stem for p in (CANON / "opencode-agents").glob("*.md")}
    for harness, suffix in (("opencode", ".md"), ("claude-code", ".md"), ("codex", ".toml")):
        actual = {p.stem for p in (out / harness / "agents").glob(f"*{suffix}")}
        harness_expected = expected | opencode_only if harness == "opencode" else expected
        if actual != harness_expected:
            die(f"{harness}: generated role set mismatch")
    orchestrator = (out / "opencode/agents/orchestrator.md").read_text()
    for role in ORCHESTRATOR_TASK_ALLOW:
        if f'    "{role}": allow' not in orchestrator:
            die(f"orchestrator cannot delegate required role: {role}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--profile")
    parser.add_argument("--roles")
    parser.add_argument("--models")
    args = parser.parse_args()
    profile = args.profile or (ROOT / "active-profile").read_text().strip()
    try:
        generate(Path(args.output), profile, args.roles, args.models)
    except (OSError, ValueError, json.JSONDecodeError, tomllib.TOMLDecodeError) as exc:
        print(f"CHECK_FAILED: {exc}", file=sys.stderr)
        return 2
    print(f"CHECK_PASS: generated and validated profile {profile}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
