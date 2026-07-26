from __future__ import annotations
import dataclasses
import os
from pathlib import Path
import subprocess

@dataclasses.dataclass(frozen=True)
class GateSpec:
    gate_id: str
    argv: tuple[str,...]
    cwd: str
    env: tuple[str,...] = ()

def gate_specs(root: Path):
    root=str(root.resolve())
    return {"v2:python-compile": GateSpec("v2:python-compile",("/usr/bin/python3","-m","py_compile","ai/scripts/routing.py"),root,("PYTHONUTF8",)),
            "v2:routing-unit": GateSpec("v2:routing-unit",("/usr/bin/python3","-m","unittest","discover","-s","tests","-p","test_routing.py"),root,("PYTHONUTF8",)),
            "v2:harness-verify": GateSpec("v2:harness-verify",(str((Path(root)/"ai/scripts/verify.sh").resolve()),),root,())}


def run_gate(spec: GateSpec, root: Path, environment: dict[str, str] | None = None) -> int:
    """Run only a declared absolute argv from the exact repository cwd.

    This prevents a gate ID, shell fragment, ambient PATH, or caller cwd from
    becoming an execution capability.
    """
    declared = gate_specs(root).get(spec.gate_id)
    if declared != spec or Path(spec.cwd).resolve() != Path(root).resolve() or not Path(spec.argv[0]).is_absolute():
        raise ValueError("GATE_INVALID")
    supplied = environment or {}
    if set(supplied) - set(spec.env):
        raise ValueError("GATE_ENV_INVALID")
    env = {name: os.environ[name] for name in ("PATH", "SYSTEMROOT", "WINDIR") if name in os.environ}
    env.update({name: value for name, value in supplied.items() if name in spec.env})
    return subprocess.run(spec.argv, cwd=spec.cwd, env=env, check=False).returncode
