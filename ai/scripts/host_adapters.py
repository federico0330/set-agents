"""Host lane adapters (046/047, ADR-0072).

Each registered adapter exposes the four-operation contract:
  detect() -> bool
  probe_models() -> set[str]   # fail-closed, verified CLI id, never invent
  materialize(model, effort) -> list[str]  # argv
  install_harness() -> None | raises  # harness into $HOME of that host

Registration is refused if any operation is missing (047 AC-01).
fx closes as SPAWN_DEFERRED with a written reason when absent/unstable (047 AC-05).
Copilot CLI is independent of OpenCode github-copilot M-1 (047 AC-06).
"""
from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from typing import Callable


EFFORTS = ("low", "medium", "high", "xhigh")


class AdapterContractError(ValueError):
    """Raised when a lane adapter is missing a required operation."""


@dataclass(frozen=True)
class HostAdapter:
    host_id: str
    detect: Callable[[], bool]
    probe_models: Callable[[], set[str]]
    materialize: Callable[[str, str | None], list[str]]
    install_harness: Callable[[], None]
    spawn_deferred_reason: str | None = None


_REGISTRY: dict[str, HostAdapter] = {}


def register(adapter: HostAdapter) -> HostAdapter:
    missing = [
        name for name in ("detect", "probe_models", "materialize", "install_harness")
        if not callable(getattr(adapter, name, None))
    ]
    if missing:
        raise AdapterContractError(
            f"lane adapter {adapter.host_id!r} refused: missing {', '.join(missing)}"
        )
    _REGISTRY[adapter.host_id] = adapter
    return adapter


def get_adapter(host_id: str) -> HostAdapter | None:
    return _REGISTRY.get(host_id)


def registered_hosts() -> tuple[str, ...]:
    return tuple(_REGISTRY)


# --------------------------------------------------------------------------- agy


def _agy_detect() -> bool:
    return bool(shutil.which("agy"))


def _agy_probe_models() -> set[str]:
    """Fail-closed: only accept models listed by `agy models` after a clean run.
    Not logged in / empty / error → empty set (unlistable), never invent."""
    if not _agy_detect():
        return set()
    try:
        result = subprocess.run(
            ["agy", "models"],
            capture_output=True, text=True, timeout=30, check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return set()
    combined = (result.stdout or "") + "\n" + (result.stderr or "")
    if "sign in" in combined.lower() or "not logged" in combined.lower():
        return set()
    if result.returncode != 0:
        return set()
    models = set()
    for line in (result.stdout or "").splitlines():
        token = line.strip()
        if not token or token.startswith("ERROR") or " " in token and "/" not in token:
            # Prefer bare model ids or provider/model; skip prose.
            if not token or " " in token:
                continue
        if token and not token.startswith("ERROR") and "Fetching" not in token:
            # Accept provider/model or bare slug without spaces.
            if "/" in token or (token.replace("-", "").replace("_", "").isalnum()):
                if " " not in token and ":" not in token.split("/")[-1][:1]:
                    models.add(token)
    return models


def _agy_materialize(model: str, effort: str | None = None) -> list[str]:
    """`agy --print --model <m> [--effort <e>]` — measured from `agy --help` 2026-08-26."""
    argv = ["agy", "--print", "--model", model]
    if effort in EFFORTS:
        argv.extend(["--effort", effort])
    return argv


def _agy_install_harness() -> None:
    """Harness install into Antigravity's config dir is deferred to install.py target;
    this stub documents the contract seam (047 AC-01)."""
    raise NotImplementedError("agy install_harness: use install.py --target agy when wired")


register(HostAdapter(
    host_id="agy",
    detect=_agy_detect,
    probe_models=_agy_probe_models,
    materialize=_agy_materialize,
    install_harness=_agy_install_harness,
))


# --------------------------------------------------------------------------- fx (deferred)


def _fx_detect() -> bool:
    return bool(shutil.which("fx"))


def _fx_probe_models() -> set[str]:
    return set()  # never invent; SPAWN_DEFERRED


def _fx_materialize(model: str, effort: str | None = None) -> list[str]:
    raise RuntimeError("SPAWN_DEFERRED: fx probe/materialize not stable on this machine")


def _fx_install_harness() -> None:
    raise RuntimeError("SPAWN_DEFERRED: fx harness install not available")


FX_DEFERRED_REASON = (
    "SPAWN_DEFERRED: fx binary absent or probe contract unverified "
    "(measured 2026-08-26: which(fx)=None on this machine; "
    "Vercel Labs fx is experimental — no verified CLI id for probe_models yet)"
)

register(HostAdapter(
    host_id="fx",
    detect=_fx_detect,
    probe_models=_fx_probe_models,
    materialize=_fx_materialize,
    install_harness=_fx_install_harness,
    spawn_deferred_reason=FX_DEFERRED_REASON,
))


# --------------------------------------------------------------------------- Copilot CLI


def _copilot_detect() -> bool:
    return bool(shutil.which("copilot"))


def _copilot_probe_models() -> set[str]:
    """Fail-closed. Copilot CLI wrapper often fails (pnpm dlx); empty = unlistable.
    Independent of OpenCode github-copilot M-1 (never reads that provider)."""
    if not _copilot_detect():
        return set()
    try:
        result = subprocess.run(
            ["copilot", "--help"],
            capture_output=True, text=True, timeout=20, check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return set()
    combined = (result.stdout or "") + (result.stderr or "")
    if "EACCES" in combined or "Could not resolve" in combined:
        return set()
    # No verified model-list subcommand measured yet → empty (unlistable), not invented.
    return set()


def _copilot_materialize(model: str, effort: str | None = None) -> list[str]:
    argv = ["copilot", "-p", "--model", model]
    if effort in EFFORTS:
        argv.extend(["--effort", effort])
    return argv


def _copilot_install_harness() -> None:
    raise NotImplementedError("copilot install_harness: use install.py --target copilot when wired")


register(HostAdapter(
    host_id="copilot",
    detect=_copilot_detect,
    probe_models=_copilot_probe_models,
    materialize=_copilot_materialize,
    install_harness=_copilot_install_harness,
))


def probe_host_model_counts(*, which=None) -> dict[str, int]:
    """Verified model counts for resolve_host_state. Absent adapter → no entry
    (unlistable if has_lane). fx with spawn_deferred still reports 0 when present.

    The probes run CONCURRENTLY. Each one is a subprocess this thread does nothing but wait
    on (`agy models` and friends, up to a 30 s timeout apiece), so probing them in sequence
    made the console's first paint cost the SUM of every unauthenticated CLI's timeout --
    the single largest wait a new user faces. In parallel it costs the slowest one. Nothing
    else changes: same adapters, same timeouts, same fail-closed empty set on any error, and
    the result dict is rebuilt in registry order so the output is byte-identical."""
    present = [
        (host_id, adapter) for host_id, adapter in _REGISTRY.items()
        if adapter.detect()
    ]
    if not present:
        return {}

    def _count(adapter):
        try:
            return len(adapter.probe_models())
        except Exception:
            return 0

    if len(present) == 1:
        return {present[0][0]: _count(present[0][1])}
    import concurrent.futures
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(present)) as pool:
        measured = list(pool.map(lambda pair: _count(pair[1]), present))
    return {host_id: count for (host_id, _), count in zip(present, measured)}
