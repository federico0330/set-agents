"""Expertise packs: global always_on + project packs.local.toml overlay (ADR-0077)."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

ALWAYS_ON = "always_on"
OPTIONAL = "optional"


@dataclass(frozen=True)
class PackManifest:
    pack_id: str
    tier: str
    summary: str = ""
    skills: tuple[str, ...] = ()
    tools: tuple[str, ...] = ()
    path: Path | None = None


@dataclass
class PackProfile:
    always_on: list[PackManifest] = field(default_factory=list)
    optional_enabled: list[PackManifest] = field(default_factory=list)
    optional_available: list[PackManifest] = field(default_factory=list)
    missing_tools: list[str] = field(default_factory=list)
    project_overlay: Path | None = None
    harness_packs_dir: Path | None = None

    @property
    def active(self) -> list[PackManifest]:
        return [*self.always_on, *self.optional_enabled]


def default_packs_dir(harness_root: Path) -> Path:
    return harness_root / "Global" / "_canonical" / "packs"


def load_pack_manifest(path: Path) -> PackManifest | None:
    try:
        raw = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError):
        return None
    if not isinstance(raw, dict):
        return None
    pack_id = raw.get("id") or path.parent.name
    tier = raw.get("tier") or OPTIONAL
    if tier not in (ALWAYS_ON, OPTIONAL):
        tier = OPTIONAL
    skills = tuple(raw.get("skills") or ())
    tools = tuple(raw.get("tools") or ())
    summary = str(raw.get("summary") or "")
    return PackManifest(
        pack_id=str(pack_id),
        tier=tier,
        summary=summary,
        skills=tuple(str(s) for s in skills),
        tools=tuple(str(t) for t in tools),
        path=path,
    )


def discover_packs(packs_dir: Path) -> dict[str, PackManifest]:
    found: dict[str, PackManifest] = {}
    if not packs_dir.is_dir():
        return found
    for child in sorted(packs_dir.iterdir()):
        manifest = child / "manifest.toml"
        if not manifest.is_file():
            continue
        pack = load_pack_manifest(manifest)
        if pack is None:
            continue
        found[pack.pack_id] = pack
    return found


def load_project_overlay(project_root: Path | None) -> dict[str, Any]:
    if project_root is None:
        return {"enabled": [], "disabled": []}
    path = project_root / "packs.local.toml"
    if not path.is_file():
        return {"enabled": [], "disabled": [], "path": path}
    try:
        raw = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError):
        return {"enabled": [], "disabled": [], "path": path, "error": "unreadable"}
    if not isinstance(raw, dict):
        return {"enabled": [], "disabled": [], "path": path, "error": "bad_shape"}
    enabled = [str(x) for x in (raw.get("enabled") or [])]
    disabled = [str(x) for x in (raw.get("disabled") or [])]
    return {"enabled": enabled, "disabled": disabled, "path": path}


def resolve_profile(
    *,
    harness_root: Path,
    project_root: Path | None = None,
    which=None,
) -> PackProfile:
    """Merge always_on packs with project packs.local.toml enabled optionals."""
    packs_dir = default_packs_dir(harness_root)
    catalog = discover_packs(packs_dir)
    overlay = load_project_overlay(project_root)
    enabled = set(overlay.get("enabled") or [])
    disabled = set(overlay.get("disabled") or [])

    profile = PackProfile(
        project_overlay=overlay.get("path"),
        harness_packs_dir=packs_dir,
    )
    for pack in catalog.values():
        if pack.tier == ALWAYS_ON:
            if pack.pack_id in disabled:
                continue
            profile.always_on.append(pack)
        else:
            if pack.pack_id in enabled:
                profile.optional_enabled.append(pack)
            else:
                profile.optional_available.append(pack)

    needed: list[str] = []
    for pack in profile.active:
        for tool in pack.tools:
            if which is not None:
                present = bool(which(tool))
            else:
                import shutil
                present = shutil.which(tool) is not None
            if not present and tool not in needed:
                needed.append(tool)
    profile.missing_tools = needed
    return profile


def profile_lines(profile: PackProfile) -> list[str]:
    """Human lines for Estado / Perfil — names the three overlay layers."""
    lines = [
        "Capas (ADR-0077):",
        "  Global (harness): packs always_on + tools.toml",
        "  Máquina/clone: tools.local.toml en HARNESS_HOME",
        "  Proyecto: packs.local.toml en PROJECT_ROOT",
        "",
        "Packs activos:",
    ]
    if not profile.active:
        lines.append("  (ninguno — falta Global/_canonical/packs o packs.local.toml)")
    for pack in profile.active:
        tag = "always_on" if pack.tier == ALWAYS_ON else "proyecto"
        lines.append(f"  · {pack.pack_id} [{tag}] — {pack.summary or '—'}")
    avail = [p.pack_id for p in profile.optional_available]
    if avail:
        lines.append("Opcionales disponibles: " + ", ".join(avail))
    if profile.missing_tools:
        lines.append("Tools faltantes (packs): " + ", ".join(profile.missing_tools))
    else:
        lines.append("Tools de packs: ok o sin detectar")
    overlay = profile.project_overlay
    if overlay is not None:
        lines.append(f"Overlay proyecto: {overlay}" + (" (presente)" if overlay.is_file() else " (ausente)"))
    return lines
