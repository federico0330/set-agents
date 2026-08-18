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
KNOWLEDGE_TEMPLATE_DIR = Path(__file__).resolve().parents[2] / "PROYECTO" / "docs" / "ai" / "knowledge"
# 032/C2 (AC-05): Cursor reads rules and slash commands ONLY from the project tree -- there is
# no user-level equivalent for either (verified 2026-08-18, https://cursor.com/docs/context/rules).
# Agents and skills DO install globally into ~/.cursor, so those are not projected here; without
# this step a project opened in Cursor would have the roles but not the doctrine that governs them.
CURSOR_TARGET_DIR = Path(__file__).resolve().parents[2] / "Global" / "cursor"

FILES = {
    "AGENTS.md": "# Project agent rules\n\nRun `ai/scripts/verify.sh` before review. Preserve existing project contracts.\n",
    "docs/project/overview.md": "# Product overview\n\nTODO: users, outcomes, and scope.\n",
    "docs/project/domain.md": "# Domain\n\nTODO: entities, invariants, and terminology.\n",
    "docs/project/architecture.md": "# Architecture\n\nTODO: boundaries, dependencies, and deployment.\n",
    "docs/project/development.md": "# Development\n\nTODO: setup, commands, and conventions.\n",
    "docs/architecture/overview.md": (
        "# Arquitectura — mapa vivo del sistema\n\n"
        "> Documento único y vivo: cada sección se REEMPLAZA cuando cambia, nunca se apila. "
        "El \"por qué\" de cada decisión vive en `docs/adr/README.md`.\n\n"
        "## Flujo de datos\nTODO: diagrama Mermaid del flujo de datos de punta a punta.\n\n"
        "## Workflows clave\nTODO: un `sequenceDiagram` corto por workflow importante.\n\n"
        "## Casos de uso\nTODO: lista corta de los casos de uso principales.\n\n"
        "## Mapa de componentes\nTODO: diagrama Mermaid de módulos/servicios y cómo se hablan.\n\n"
        "## Decisiones\nTODO: tabla que linkea a `docs/adr/README.md`.\n"
    ),
    "docs/adr/README.md": (
        "# Índice de ADRs\n\n"
        "> Una fila por ADR, sin excepciones. `architect` la actualiza al escribir cada ADR nuevo.\n\n"
        "| ADR | Título | Estado | Fecha |\n|---|---|---|---|\n"
    ),
    "docs/specs/README.md": (
        "# Índice de specs\n\n"
        "> Una fila por feature, sin excepciones. `product-analyst` la actualiza al escribir "
        "(`Draft`), aprobar (`Aprobado`), integrar (`Shippeado`), o superar (`Superado por <id>`) un spec.\n\n"
        "| ID | Título | Estado | Fecha |\n|---|---|---|---|\n"
    ),
    "docs/notas/00 - Proyecto.md": (
        "# Notas del proyecto\n\n"
        "<!-- notas:auto -->\n"
        "_Se completa solo con la primera mutación de estado (o corré "
        "`python3 ai/scripts/feature-state.py sync-notes`)._\n"
        "<!-- /notas:auto -->\n\n"
        "## Notas propias\n\n_Qué es este proyecto, contexto, links útiles — esto no se pisa._\n"
    ),
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
            scripts = json.loads(pkg.read_text(encoding="utf-8")).get("scripts", {})
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
        if path.read_text(encoding="utf-8") != content:
            conflicts.append(relative)
        continue
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
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
    content = tpl.read_text(encoding="utf-8")
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
    dest.write_text(content, encoding="utf-8")
    dest.chmod(0o755)
    created.append(f"ai/scripts/{name}")

# 2b. DR-005 (005-P2 delta review): .gitignore, single-source from PROYECTO/.gitignore so it
#     never drifts from the harness's own -- create-if-missing, never overwrite. Without this
#     a bootstrapped project inherited none of the hygiene rules the harness repo relies on
#     (e.g. ai/state/render-failures.log had nothing keeping it out of git).
GITIGNORE_TEMPLATE = Path(__file__).resolve().parents[2] / "PROYECTO" / ".gitignore"
gitignore_dest = root / ".gitignore"
if not gitignore_dest.exists() and GITIGNORE_TEMPLATE.exists():
    gitignore_dest.write_text(GITIGNORE_TEMPLATE.read_text(encoding="utf-8"), encoding="utf-8")
    created.append(".gitignore")

# 2c. 032/C2 (AC-05): the Cursor project surface -- the always-applied doctrine rule and the
#     slash commands. Create-if-missing like everything else here, and a divergent existing file
#     is reported as a conflict rather than silently replaced: the user may have edited it.
for relative, source in (
    [(".cursor/rules/00-harness.mdc", CURSOR_TARGET_DIR / "rules" / "00-harness.mdc")]
    + [(f".cursor/commands/{tpl.name}", tpl)
       for tpl in (sorted((CURSOR_TARGET_DIR / "commands").glob("*.md"))
                   if (CURSOR_TARGET_DIR / "commands").is_dir() else [])]
):
    if not source.exists():
        notes.append(f"missing cursor template: {relative}")
        continue
    dest = root / relative
    content = source.read_text(encoding="utf-8")
    if dest.exists():
        if dest.read_text(encoding="utf-8") != content:
            conflicts.append(relative)
        continue
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(content, encoding="utf-8")
    created.append(relative)

# 3. Per-domain knowledge seeds (create-if-missing, never overwrite: memory-scribe grows them,
#    so an existing file with more content is the expected state, not a conflict).
for tpl in sorted(KNOWLEDGE_TEMPLATE_DIR.glob("*.md")) if KNOWLEDGE_TEMPLATE_DIR.is_dir() else []:
    dest = root / "docs" / "ai" / "knowledge" / tpl.name
    if dest.exists():
        continue
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(tpl.read_text(encoding="utf-8"), encoding="utf-8")
    created.append(f"docs/ai/knowledge/{tpl.name}")

print("BOOTSTRAP_CREATED=" + ",".join(created))
print("BOOTSTRAP_CONFLICTS=" + ",".join(conflicts))
print("BOOTSTRAP_NOTES=" + " | ".join(notes))
