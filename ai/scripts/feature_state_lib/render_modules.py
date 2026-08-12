"""AC-17/AC-18/AC-19 (019-harness-evolution PKG-3, ADR-0036): `docs/modules/<slug>.md`
render engine plus `docs/modules/modules.toml` parsing/detection. Same contract as
render_notes.py -- never-raises, atomic, shared `render-failures.log` -- and reuses its
`merge_note`/`write_note`/`_short` directly rather than re-implementing the machine/human
merge a second time. See ADR-0036 decision 3 for exactly how the schema's eight sections
map onto this: two are re-derived whole (Responsabilidad, Últimos cambios estructurales),
a third (Posee / Depende de) is split -- its "Posee" half gets its own machine heading
here, its "Depende de" half stays seeded prose -- and six headings total (Puntos de
entrada, Componentes, Flujo, Posee / Depende de, Invariantes, Decisiones; five of them
with no machine-derived half at all, the sixth being the human half of the split above)
are seeded once and then preserved as human-owned content -- forcing narrative-only sections inside the
machine block would either freeze them as placeholders forever or, worse, delete real
prose on the next render.
"""

from __future__ import annotations

import fnmatch
import re
import tomllib
from pathlib import Path
from typing import Any

from feature_state_lib import model
from feature_state_lib.model import StateError
from feature_state_lib.render_notes import merge_note, write_note, _short, _log_render_failure
from feature_state_lib.render_status import status_root


MODULES_TOML = "modules.toml"
MODULE_SLUG_RE = re.compile(r"^[a-z][a-z0-9-]*$")
MODULES_TOML_ALLOWED_KEYS = {"nombre", "responsabilidad", "paths"}
MAX_RECENT_CHANGES = 10

# ADR-0036 decision 3: seeded once at doc creation, then human-owned forever (merge_note
# never touches anything outside its own markers).
HUMAN_SCAFFOLD_SECTIONS = [
    "Puntos de entrada",
    "Componentes",
    "Flujo",
    "Posee / Depende de",
    "Invariantes",
    "Decisiones",
]


class ModulesTomlError(StateError):
    """A malformed docs/modules/modules.toml -- fail-closed, surfaced through the CLI's
    normal StateError handling (exit 2, clean JSON error) rather than a bare traceback."""


def modules_toml_path(state_file: Path, modules_dir: str | None = None) -> Path | None:
    """Same "managed project" marker as `render_notes.notes_root`: `ai/state/` existing,
    never "does docs/modules/ already exist" -- a repo without docs/modules/ (or without
    modules.toml) simply never renders, it never fails."""
    if modules_dir:
        return Path(modules_dir) / MODULES_TOML
    _, out_dir = status_root(state_file)
    if not (out_dir.is_dir() and out_dir.name == "state" and out_dir.parent.name == "ai"):
        return None
    return out_dir.parent.parent / "docs" / "modules" / MODULES_TOML


def load_modules_toml(path: Path) -> dict[str, dict[str, Any]]:
    """Fail-closed parse. Absent file -> {} (opt-in, same posture as notes_root). A
    MALFORMED file (bad TOML, wrong shape, unknown key, bad slug) raises
    ModulesTomlError -- a typo'd registry that silently matched nothing would be a worse
    failure than a loud refusal, same fail-closed posture as the rest of this repo's
    config parsing.
    """
    if not path.is_file():
        return {}
    try:
        raw = tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as exc:
        raise ModulesTomlError(f"{path}: invalid TOML: {exc}") from exc
    modules = raw.get("module")
    if modules is None:
        return {}
    if not isinstance(modules, dict):
        raise ModulesTomlError(f"{path}: [module] must be a table of tables")
    result: dict[str, dict[str, Any]] = {}
    for slug, entry in modules.items():
        if not isinstance(slug, str) or not MODULE_SLUG_RE.match(slug):
            raise ModulesTomlError(f"{path}: malformed module slug: {slug!r} (expected ^[a-z][a-z0-9-]*$)")
        if not isinstance(entry, dict):
            raise ModulesTomlError(f"{path}: [module.{slug}] must be a table")
        unknown = set(entry) - MODULES_TOML_ALLOWED_KEYS
        if unknown:
            raise ModulesTomlError(f"{path}: [module.{slug}] has unknown key(s): {', '.join(sorted(unknown))}")
        nombre = entry.get("nombre")
        responsabilidad = entry.get("responsabilidad")
        paths = entry.get("paths")
        if not isinstance(nombre, str) or not nombre.strip():
            raise ModulesTomlError(f"{path}: [module.{slug}].nombre is required and must be a non-empty string")
        if not isinstance(responsabilidad, str) or not responsabilidad.strip():
            raise ModulesTomlError(f"{path}: [module.{slug}].responsabilidad is required and must be a non-empty string")
        if not isinstance(paths, list) or not paths or not all(isinstance(p, str) and p for p in paths):
            raise ModulesTomlError(f"{path}: [module.{slug}].paths must be a non-empty list of strings")
        result[slug] = {"nombre": nombre, "responsabilidad": responsabilidad, "paths": list(paths)}
    return result


def matching_modules(paths: list[str], modules: dict[str, dict[str, Any]]) -> list[str]:
    """AC-18: candidate slugs whose declared globs match any of `paths`. fnmatch, never
    glob.glob -- these are repo-relative strings out of state, some possibly already gone
    from disk (a repair's changed_files can list a since-deleted file). fnmatch's `*`
    already spans `/`, so `pkg/**` and `pkg/*` behave identically here.

    Known limitation (F-06, P3 review, not fixed -- documented, not repaired): this only
    matches a candidate PATH against a module PATTERN with `fnmatch`; it never compares two
    globs against each other for semantic overlap. A package whose `owned_paths` declares
    something wider than any registered module pattern -- e.g. `ai/scripts/**` when every
    `modules.toml` entry only owns narrower globs like `ai/scripts/routing_core/**` -- gets
    zero hits here even though every module pattern is a strict subset of that owned path.
    Fixing this properly needs glob-vs-glob subset/overlap reasoning (or expanding both
    sides against the real file tree), which is a redesign, not a bounded repair; see
    ADR-0036 decision on `module-impact-detect` for the accepted scope."""
    hits = []
    for slug, entry in modules.items():
        for pattern in entry["paths"]:
            if any(fnmatch.fnmatch(p, pattern) for p in paths):
                hits.append(slug)
                break
    return sorted(hits)


def unmatched_candidate_paths(paths: list[str], modules: dict[str, dict[str, Any]]) -> list[str]:
    """F-06 (P3 review, advisory only -- never gates anything): candidate paths that
    matched NO module pattern at all. This is exactly the signal that a package touched
    something `modules.toml` doesn't know about yet and may be worth a new `[module.<slug>]`
    entry -- `module-impact-detect` was silently dropping this information."""
    orphans = []
    for path in paths:
        if not any(
            fnmatch.fnmatch(path, pattern)
            for entry in modules.values()
            for pattern in entry["paths"]
        ):
            orphans.append(path)
    return sorted(set(orphans))


def package_candidate_paths(package: dict[str, Any]) -> list[str]:
    """AC-18's detection source: the package's declared `owned_paths` plus every
    `changed_files` from its recorded repairs. Deliberately never the receipt -- its
    `paths_digest` is a hash, not a path list, so it has nothing to match against."""
    paths = list(package.get("owned_paths") or [])
    for repair in package.get("repairs", []) or []:
        if isinstance(repair, dict):
            paths += repair.get("changed_files", []) or []
    return paths


def detect_module_candidates(package: dict[str, Any], modules: dict[str, dict[str, Any]]) -> list[str]:
    return matching_modules(package_candidate_paths(package), modules)


def _module_auto_body(slug: str, entry: dict[str, Any], changes: list[dict[str, Any]]) -> str:
    lines = ["## Responsabilidad", "", _short(entry.get("responsabilidad", ""), 400)]
    lines += ["", "## Posee", ""]
    for pattern in entry.get("paths", []):
        lines.append(f"- `{_short(pattern, 200)}`")
    lines += ["", "## Últimos cambios estructurales", ""]
    if changes:
        for change in changes[:MAX_RECENT_CHANGES]:
            # F-03 repair evidence (P3 review): feature_id/package_id come straight from
            # state (module_impacts is appended from CLI args, not schema-validated
            # content) -- every field written into the machine block must pass through
            # `_short`, same invariant this module's own docstring and
            # docs/modules/narracion-notas.md:40 declare. Without this, a crafted
            # package_id/feature_id containing "<!--"/"-->" or newlines can inject a fake
            # heading or arbitrary content INSIDE the machine block, persistently
            # (re-rendered on every mutation).
            lines.append(
                f"- {change.get('at', '')[:10]} {_short(change.get('feature_id', '?'), 80)}/"
                f"{_short(change.get('package_id', '?'), 80)} "
                f"— {_short(change.get('cambio', ''), 200)}"
            )
    else:
        lines.append("- _sin cambios registrados todavía_")
    lines += ["", STALENESS_NOTICE]
    return "\n".join(lines)


# F-04 repair evidence (P3 review): a visible (non-HTML-comment) line at the end of the
# machine block, so the human/machine boundary survives Obsidian preview, where HTML
# comments render invisibly and the reader cannot otherwise tell where regenerated content
# ends and hand-maintained prose begins.
STALENESS_NOTICE = (
    "_Debajo de esta línea la prosa es mantenida a mano — contrastala con la fecha del "
    "último cambio estructural._"
)


def render_module_doc(path: Path, slug: str, entry: dict[str, Any], changes: list[dict[str, Any]]) -> bool:
    """Write/refresh one module doc. Returns whether the file changed (write_note's own
    idempotence: unchanged content is not rewritten)."""
    existed_before = path.exists()
    body = _module_auto_body(slug, entry, changes)
    changed = write_note(path, entry.get("nombre", slug), body)
    if not existed_before and changed:
        # First creation: seed the human-owned scaffold (ADR-0036 decision 3) below the
        # marker so a human opening a brand-new module doc sees exactly which sections to
        # fill in, not merge_note's bare generic "Notas propias" note alone. Appended AFTER
        # write_note's own atomic write -- a plain append, not a second merge_note pass, so
        # nothing here can ever touch the machine block.
        with path.open("a", encoding="utf-8") as handle:
            for section in HUMAN_SCAFFOLD_SECTIONS:
                handle.write(f"\n## {section}\n\n_(completar)_\n")
    return changed


def render_modules(
    state_file: Path,
    modules_dir: str | None = None,
    only_feature: str | None = None,
    force: bool = False,
) -> list[str]:
    """Rebuild every module doc that has at least one recorded impact. Never raises: a
    broken module render must not block a state mutation. `only_feature`, when given,
    limits WHICH modules get rewritten (only those touched by that feature) but the
    "Últimos cambios estructurales" content is always aggregated across every feature's
    state -- a module's history is not scoped to one feature, same as the notes hub already
    aggregates across every feature for its own summary. `force` mirrors render_notes:
    sync-notes is the consolidation point and must always render regardless of
    --no-render's `model.RENDER_SKIP`.
    """
    written: list[str] = []
    if model.RENDER_SKIP and not force:
        return written
    try:
        fallback_out_dir = status_root(state_file)[1]
    except Exception:
        fallback_out_dir = None
    try:
        toml_path = modules_toml_path(state_file, modules_dir)
        if toml_path is None:
            return written
        modules = load_modules_toml(toml_path)
        if not modules:
            return written
        features_dir, out_dir = status_root(state_file)
        changes_by_slug: dict[str, list[dict[str, Any]]] = {slug: [] for slug in modules}
        touched_by_feature: dict[str, set[str]] = {}
        import json
        for path in sorted(features_dir.glob("*.json")):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            fid = data.get("feature_id", path.stem)
            for package in data.get("packages", []) or []:
                if not isinstance(package, dict):
                    continue
                for impact in package.get("module_impacts", []) or []:
                    if not isinstance(impact, dict):
                        continue
                    slug = impact.get("module")
                    if slug not in changes_by_slug:
                        continue
                    changes_by_slug[slug].append({
                        "at": impact.get("at", ""),
                        "feature_id": impact.get("feature_id", fid),
                        "package_id": impact.get("package_id", package.get("package_id")),
                        "cambio": impact.get("cambio", ""),
                    })
                    touched_by_feature.setdefault(fid, set()).add(slug)
        modules_root = toml_path.parent
        for slug, entry in modules.items():
            changes = sorted(changes_by_slug.get(slug, []), key=lambda item: item.get("at", ""), reverse=True)
            if not changes and not force:
                # AC-19: the incremental (mutation-time) pass only renders modules with at
                # least one impact -- never 30 empty scaffolds on every state write. `force`
                # (sync-notes's full-regen pass, D-01 P3 repair) is the explicit exception:
                # a module seeded before it ever got an impact must still be reachable by
                # regeneration, or the engine can never re-apply a machine-block format
                # change (e.g. the F-04 staleness line) to a doc it itself created -- the
                # bug this repair fixes. `_module_auto_body` already renders the correct
                # "sin cambios registrados todavía" body for an empty `changes` list.
                continue
            if only_feature and slug not in touched_by_feature.get(only_feature, set()):
                continue
            try:
                if render_module_doc(modules_root / f"{slug}.md", slug, entry, changes):
                    written.append(f"{slug}.md")
            except Exception as exc:  # one broken module doc must not block the rest
                _log_render_failure(out_dir, f"module={slug}", exc)
                continue
    except Exception as exc:  # the module docs are best-effort by contract, like render_notes
        if fallback_out_dir is not None:
            _log_render_failure(fallback_out_dir, "render_modules", exc)
    return written
