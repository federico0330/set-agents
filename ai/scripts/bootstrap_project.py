#!/usr/bin/env python3
"""Conservative project bootstrap: create missing files, never overwrite.

Docs are inlined. The harness scripts (run/verify/loop/e2e/mcp/audit) are copied from the single-source
templates in ../PROYECTO/ai/scripts so they never drift, and run.sh's start commands are inferred from the
project's stack when possible — so downstream agents (app-runner, runtime-verifier) find a real, runnable
script instead of a stub that hangs or exits with an unhelpful error.
"""

import argparse
import json
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("target")
args = parser.parse_args()
root = Path(args.target)

TEMPLATE_DIR = Path(__file__).resolve().parents[2] / "PROYECTO" / "ai" / "scripts"
SCRIPT_TEMPLATES = ["run.sh", "verify.sh", "loop.sh", "e2e.sh", "mcp.sh", "audit-readonly.sh"]

FILES = {
    "AGENTS.md": "# Project agent rules\n\nRun `ai/scripts/verify.sh` before review. Preserve existing project contracts.\n",
    "docs/project/overview.md": "# Product overview\n\nTODO: users, outcomes, and scope.\n",
    "docs/project/domain.md": "# Domain\n\nTODO: entities, invariants, and terminology.\n",
    "docs/project/architecture.md": "# Architecture\n\nTODO: boundaries, dependencies, and deployment.\n",
    "docs/project/development.md": "# Development\n\nTODO: setup, commands, and conventions.\n",
    ".opencode/AGENTS.md": "# Local OpenCode rules\n\nFollow ../../AGENTS.md and delegate deterministic gates.\n",
    ".claude/CLAUDE.md": "# Local Claude rules\n\nFollow ../AGENTS.md and preserve separation of duties.\n",
    ".codex/config.toml": "[agents]\nmax_depth = 1\nmax_threads = 4\n",
}


def infer_run_cmds(project_root: Path):
    """Best-effort start commands from the stack. Empty string = leave the template's TODO placeholder."""
    backend = frontend = ""
    pkg = project_root / "package.json"
    if pkg.exists():
        try:
            scripts = json.loads(pkg.read_text()).get("scripts", {})
        except Exception:
            scripts = {}
        if "dev" in scripts:
            frontend = "npm run dev"
        elif "start" in scripts:
            frontend = "npm start"
    try:
        csproj = next(iter(sorted(project_root.rglob("*.csproj"))), None)
    except Exception:
        csproj = None
    if csproj is not None:
        backend = f"dotnet run --project {csproj.relative_to(project_root)}"
    elif (project_root / "manage.py").exists():
        backend = "python manage.py runserver"
    elif (project_root / "pyproject.toml").exists() or (project_root / "requirements.txt").exists():
        backend = "python -m uvicorn app.main:app --reload --port 8000  # TODO: ajustá el módulo"
    return backend, frontend


created = []
conflicts = []
notes = []

# 1. Inlined docs / local harness config (create-if-missing, never overwrite).
for relative, content in FILES.items():
    path = root / relative
    if path.exists():
        if path.read_text() != content:
            conflicts.append(relative)
        continue
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    created.append(relative)

# 2. Harness scripts copied from single-source templates; run.sh gets stack inference.
backend_cmd, frontend_cmd = infer_run_cmds(root)
for name in SCRIPT_TEMPLATES:
    dest = root / "ai" / "scripts" / name
    tpl = TEMPLATE_DIR / name
    if dest.exists():
        continue
    if not tpl.exists():
        notes.append(f"missing template: {name}")
        continue
    content = tpl.read_text()
    if name == "run.sh":
        if backend_cmd:
            content = content.replace('BACKEND_CMD=""', f'BACKEND_CMD="{backend_cmd}"', 1)
        if frontend_cmd:
            content = content.replace('FRONTEND_CMD=""', f'FRONTEND_CMD="{frontend_cmd}"', 1)
        if backend_cmd or frontend_cmd:
            notes.append(f"run.sh inferred: backend={backend_cmd or '-'} frontend={frontend_cmd or '-'}")
        else:
            notes.append("run.sh left as stub (stack not inferred — fill BACKEND_CMD/FRONTEND_CMD)")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(content)
    dest.chmod(0o755)
    created.append(f"ai/scripts/{name}")

print("BOOTSTRAP_CREATED=" + ",".join(created))
print("BOOTSTRAP_CONFLICTS=" + ",".join(conflicts))
print("BOOTSTRAP_NOTES=" + " | ".join(notes))
