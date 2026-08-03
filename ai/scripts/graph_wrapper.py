"""set-agents: --graph, a thin subprocess wrapper around feature-state.py's own `graph`
command. Extracted from set_agents_app.py (mechanical, behavior-preserving split).

`root` is an explicit, required keyword-only parameter (never a bare `ROOT` free-name read):
`ROOT` itself must stay defined in set_agents_app.py (see its own module docstring), and
set_agents_app.py's `main()` passes its own `ROOT` in explicitly at the one real call site.
"""

import subprocess
import sys
from pathlib import Path


def cmd_graph(feature_ids=None, project=None, out=None, *, root):
    """AC-25: a thin subprocess wrapper, never a second implementation of the join logic.

    Same sibling-tool posture `verify.sh` already uses for `check-feature-state.py`:
    `feature-state.py graph` does the real work (build_execution_graph/render_mermaid,
    AC-22) and this just re-prints its stdout/stderr and forwards its exit code. It
    degrades exactly like `feature-state.py graph` when there is no state -- there is no
    separate no-state branch here to keep in sync with that one.
    """
    script = root / "ai/scripts/feature-state.py"
    command = ["python3", str(script), "graph"]
    for feature_id in feature_ids or []:
        command += ["--feature-id", feature_id]
    if project:
        command += ["--root", str(Path(project).expanduser().resolve())]
    if out:
        command += ["--out", out]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.stdout:
        sys.stdout.write(result.stdout)
    if result.stderr:
        sys.stderr.write(result.stderr)
    return result.returncode
