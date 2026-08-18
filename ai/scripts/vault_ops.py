"""set-agents: company-level Obsidian vault -- registry, seeds, migration planning/repair.

Extracted from set_agents_app.py (mechanical, behavior-preserving split).

Deliberately NOT moved here (stay in set_agents_app.py, documented deviation): `find_vault`,
`_resolve_vault`, `cmd_vault_init`, `cmd_vault_link` (all need `app_config`/`write_app_config`,
which must stay in set_agents_app.py -- see its own module docstring for why), and
`apply_vault_migration`'s own call chain would need a live back-reference to `cmd_vault_link`;
`cmd_vault_doctor`/`_vault_doctor_marker_path`/`vault_menu`/`VAULT_DOCTOR_MARKER_TTL_SECONDS`
(entangled with `set_agents_app.STATE_DIR`/`cmd_vault_init`/`cmd_vault_link` monkeypatches in
tests/test_harness.py). A module-level (or even a lazily call-time) `from set_agents_app import
...` here would be a genuine circular import: set_agents_app.py imports this module, so the
reverse edge breaks under tests/test_harness.py's `_import()` helper, which loads
set_agents_app.py via `importlib.util.spec_from_file_location` WITHOUT registering it in
`sys.modules` -- a nested `import set_agents_app` from inside this module, while that fresh
instance's own top-level exec is still in progress, cannot find it there and instead starts a
second, independent top-level exec of set_agents_app.py from disk. `atomic_write`/`_BACKED_UP`
are duplicated here (identical logic) rather than imported back for the same reason; unlike
`app_config`/`write_app_config`, `atomic_write` never reads `STATE_DIR`/`APP_CONFIG`, so the
only cost of the duplication is a `_BACKED_UP` dedup set that is scoped per-module instead of
shared -- harmless, since vault registry files never collide with the config paths
set_agents_app.py's own `atomic_write` calls touch.
"""

import json
import os
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path

VAULT_HUB = "00 - INICIO.md"
# ADR-0012/DEC-6: a per-project intent marker, keyed by the project's FULL repo path (never the
# basename, so two repos sharing a basename at different paths never collide). Lives in the vault
# root (travels with the vault, e.g. via Syncthing) rather than in any one repo. --vault-doctor
# (T-207) refuses to act on any project without an entry here.
VAULT_REGISTRY = ".set-agentes-vault.json"

_BACKED_UP = set()


def atomic_write(path, content):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path not in _BACKED_UP:
        shutil.copy2(path, str(path) + ".bak")
        _BACKED_UP.add(path)
    fd, temp = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w") as handle:
            handle.write(content)
        os.replace(temp, path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


def vault_registry_path(vault):
    return Path(vault) / VAULT_REGISTRY


def read_vault_registry(vault):
    path = vault_registry_path(vault)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def write_vault_registry_entry(vault, repo_path, *, topology, vault_path, notes_excluded=False):
    """Read-merge-write (never a raw overwrite — same discipline as app_config's writers).

    `vault_path` is normalized by resolving its PARENT only, never the path itself: for
    hybrid topology the caller (cmd_vault_link) already turned it into a symlink before this
    runs, and a bare `Path(vault_path).resolve()` would dereference that symlink and store
    the repo-side real directory instead of the vault-side symlink location --
    vault_doctor_report's health check reads this field expecting the symlink's own path
    (`linked, real = vault_path, notes`), so that made every freshly-linked hybrid project
    report `health=drift` forever, never `healthy`. For private topology `vault_path` is a
    real directory, not a symlink, so resolving its parent-then-name is unchanged behavior.
    """
    vault_path = Path(vault_path)
    normalized_vault_path = vault_path.parent.resolve() / vault_path.name
    registry = read_vault_registry(vault)
    key = str(Path(repo_path).resolve())
    registry[key] = {
        "topology": topology,
        "vault_path": str(normalized_vault_path),
        "repo_path": key,
        "linked_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "notes_excluded": bool(notes_excluded),
    }
    atomic_write(vault_registry_path(vault), json.dumps(registry, indent=2, sort_keys=True) + "\n")
    return registry[key]


def vault_seed_hub(company):
    return (
        f"# {company} — INICIO\n\n"
        "_La nota del café: abrila a la mañana y navegá desde acá._\n\n"
        "## Rol\n\n_TODO: quién sos en esta empresa/cliente y qué se espera de vos._\n\n"
        "## Forma de trabajo\n\n_TODO: cómo querés que los agentes trabajen acá "
        "(prioridades, estilo, límites, qué preguntar y qué no)._\n\n"
        "## Entrega de resultados\n\n_TODO: formato y tono en que querés los resultados "
        "(resumen ejecutivo primero, evidencia después, etc.)._\n\n"
        "## Qué falta por proyecto\n\n"
        "Cada proyecto linkeado mantiene su propio hub con la sección «Qué falta»:\n\n"
        "_(los proyectos aparecen acá abajo a medida que los linkees)_\n\n"
        "## Casos (portfolio)\n\n"
        "Un caso de una página por proyecto terminado — plantilla: [[Casos/00 - Plantilla Caso]]\n"
    )


def vault_seed_case_template():
    return (
        "# Caso — (nombre del proyecto)\n\n"
        "_Plantilla de portfolio: copiá esta nota por cada proyecto terminado y pedí "
        "autorización antes de publicar versiones anonimizadas. La experiencia se mide "
        "por decisiones, sistemas y resultados — no por meses trabajados._\n\n"
        "## Situación inicial\n\n_TODO_\n\n"
        "## Problema de negocio\n\n_TODO_\n\n"
        "## Riesgos y restricciones\n\n_TODO_\n\n"
        "## Alternativas evaluadas\n\n_TODO_\n\n"
        "## Arquitectura elegida\n\n_TODO_\n\n"
        "## Implementación\n\n_TODO_\n\n"
        "## Resultado medible\n\n_TODO: de X a Y, horas eliminadas, errores evitados._\n\n"
        "## Aprendizajes\n\n_TODO_\n"
    )


def project_notes_seed(project_name):
    # feature-state.py regenerates the auto block; this seed adds the manual frame.
    return (
        f"# {project_name} — notas\n\n"
        "<!-- notas:auto -->\n_Se completa solo con la primera mutación de estado "
        "(o corré `python3 ai/scripts/feature-state.py sync-notes`)._\n<!-- /notas:auto -->\n\n"
        "## Notas propias\n\n_Qué es este proyecto, contexto, links útiles — esto no se pisa._\n"
    )


def _git_rev_parse(project, *args):
    """`git -C project rev-parse <args>`, hardened the same way as `git()` above:
    a purged env (a `GIT_DIR`/`GIT_WORK_TREE`/`GIT_COMMON_DIR`/`GIT_INDEX_FILE` inherited
    from the caller's shell would redirect git at a repo `project` never named -- verified
    live: with a stray `GIT_DIR` set, `rev-parse --git-common-dir` happily answers about an
    unrelated repo even for a `project` that isn't inside any repo at all), a timeout (never
    hang the CLI on git), and a caught missing binary. Returns None on any failure.
    """
    import subprocess

    env = {
        key: value for key, value in os.environ.items()
        if key not in ("GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR", "GIT_INDEX_FILE")
    }
    env["GIT_TERMINAL_PROMPT"] = "0"
    try:
        result = subprocess.run(
            ["git", "-C", str(project), "rev-parse", *args],
            capture_output=True, text=True, timeout=10, check=False, env=env,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def _git_exclude_path(project):
    """The real `info/exclude` for `project`, resolved via `git rev-parse
    --git-common-dir` rather than assuming `.git` is a directory -- a linked git
    worktree's `.git` is a FILE (a `gitdir:` pointer), and `info/exclude` is not
    per-worktree: it lives in the common dir all worktrees of a repo share. Returns
    None when `project` isn't inside a git repo at all, OR when it's a subdirectory of
    someone else's repo rather than a repo root itself (`--show-toplevel` walks UP past
    `project`, so a project with no `.git` of its own but sitting inside e.g. `~/iey`'s own
    repo would otherwise silently write into -- and report notes_excluded=true against --
    a repo the caller never named, and whose root-anchored `docs/notas` pattern would not
    even match the nested path).
    """
    toplevel = _git_rev_parse(project, "--show-toplevel")
    if toplevel is None or Path(toplevel) != Path(project).resolve():
        return None
    common = _git_rev_parse(project, "--git-common-dir")
    if common is None:
        return None
    common_dir = Path(common) if Path(common).is_absolute() else project / common
    return common_dir / "info" / "exclude"


def _notes_currently_excluded(project):
    exclude = _git_exclude_path(project)
    return exclude is not None and exclude.exists() and "docs/notas" in exclude.read_text(encoding="utf-8").splitlines()


def exclude_notes_from_git(project):
    """Hide docs/notas from the project's git locally (.git/info/exclude, never pushed)."""
    exclude = _git_exclude_path(project)
    if exclude is None:
        return False
    exclude.parent.mkdir(parents=True, exist_ok=True)
    lines = exclude.read_text(encoding="utf-8").splitlines() if exclude.exists() else []
    if "docs/notas" in lines:
        return False
    exclude.write_text("\n".join(lines + ["docs/notas"]) + "\n", encoding="utf-8")
    return True


def vault_link_private(project, target_vault, notes, notes_home):
    """Private mode: notes live in the vault; the repo gets an excluded symlink."""
    if notes.is_symlink():
        if notes.resolve() == notes_home.resolve():
            if exclude_notes_from_git(project):
                print("VAULT_PRIVATE_EXCLUDED docs/notas (.git/info/exclude)")
            write_vault_registry_entry(
                target_vault, project, topology="private", vault_path=notes_home,
                notes_excluded=_notes_currently_excluded(project),
            )
            print(f"VAULT_LINK_SKIP project={project.name} vault={target_vault} mode=private")
            return 0
        print(f"VAULT_LINK_CONFLICT {notes} ya apunta a {notes.resolve()} — resolvelo a mano")
        return 1
    if notes_home.is_symlink():
        # Old outward link (vault -> repo) from default mode: replace with the real home.
        notes_home.unlink()
    if notes_home.exists() and not notes_home.is_dir():
        print(f"VAULT_LINK_CONFLICT {notes_home} existe y no es un directorio — resolvelo a mano")
        return 1
    notes_home.mkdir(parents=True, exist_ok=True)
    if notes.is_dir():
        # Migrate repo-resident notes into the vault: never clobber a differing file.
        files = [path for path in sorted(notes.rglob("*")) if path.is_file()]
        conflicts = [
            path.relative_to(notes) for path in files
            if (notes_home / path.relative_to(notes)).exists()
            and (notes_home / path.relative_to(notes)).read_bytes() != path.read_bytes()
        ]
        if conflicts:
            listed = ", ".join(str(item) for item in conflicts[:5])
            print(f"VAULT_LINK_CONFLICT notas difieren entre repo y vault ({listed}) — resolvelo a mano")
            return 1
        for path in files:
            destination = notes_home / path.relative_to(notes)
            if not destination.exists():
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(path), str(destination))
        shutil.rmtree(notes)
    seed = notes_home / "00 - Proyecto.md"
    if not seed.exists():
        seed.write_text(project_notes_seed(project.name), encoding="utf-8")
        print(f"VAULT_CREATED {seed}")
    notes.parent.mkdir(parents=True, exist_ok=True)
    try:
        notes.symlink_to(os.path.relpath(notes_home, notes.parent))
    except OSError as exc:
        print(f"VAULT_LINK_CONFLICT no pude crear el symlink: {exc}")
        return 1
    if exclude_notes_from_git(project):
        print("VAULT_PRIVATE_EXCLUDED docs/notas (.git/info/exclude)")
    write_vault_registry_entry(
        target_vault, project, topology="private", vault_path=notes_home,
        notes_excluded=_notes_currently_excluded(project),
    )
    print(f"VAULT_LINK_OK project={project.name} vault={target_vault} mode=private")
    return 0


class VaultMigrationError(Exception):
    """The migration cannot proceed safely; the caller must stop, never guess."""


def _plan_relpath(path, root):
    """Relative path for vault plans, always POSIX.

    The plan is a portable contract (AC-4.2.7): ``str(Path)`` on Windows emits
    backslashes, so merge plans compared as ``features\\replenishment-v2.md`` vs
    ``features/replenishment-v2.md``. ``Path / posix_rel`` still joins on Windows.
    """
    return path.relative_to(root).as_posix()


def vault_migration_plan(project, vault_project_dir):
    """ADR-0012's merge-case algorithm (AC-16), read-only: never touches disk. `project` is the
    repo path (may not exist yet); `vault_project_dir` is the real vault-side directory (the
    legacy vault-resident/`--private` source). Returns a plan dict with an `action` key:
    repo-missing / already-linked / symlink-conflict / repo-side-conflict / conflict /
    pure-move / merge. Only pure-move and merge are ever applied.
    """
    project = Path(project)
    vault_project_dir = Path(vault_project_dir)
    notes = project / "docs" / "notas"
    if not project.is_dir():
        return {"action": "repo-missing", "project": str(project)}
    if vault_project_dir.is_symlink():
        # Idempotent re-run against the vault side AFTER a completed migration: the vault path
        # is now the hybrid-mode symlink cmd_vault_link created, not a real directory anymore.
        if vault_project_dir.resolve() == notes.resolve():
            return {"action": "already-linked", "project": str(project)}
        return {"action": "symlink-conflict", "project": str(project), "target": str(vault_project_dir.resolve())}
    if notes.is_symlink():
        target = notes.resolve()
        if target == vault_project_dir.resolve():
            return {"action": "already-linked", "project": str(project)}
        # Dangling link or an outward `--private` link: different from "absent", never
        # silently overwritten.
        return {"action": "symlink-conflict", "project": str(project), "target": str(target)}
    # SEC-003: rglob("*") follows symlinks (files AND traversed directories), so a symlink
    # planted under the vault-side project dir would otherwise be treated as an ordinary
    # file to migrate -- demonstrated copying an attacker-chosen file's real contents into
    # the repo under an innocuous-looking name. Refuse the whole migration instead of
    # silently skipping: same "never silently overwritten" doctrine as symlink-conflict.
    all_entries = list(vault_project_dir.rglob("*"))
    unsafe_symlink = next((p for p in all_entries if p.is_symlink()), None)
    if unsafe_symlink is not None:
        return {
            "action": "unsafe-symlink", "project": str(project),
            "path": _plan_relpath(unsafe_symlink, vault_project_dir),
        }
    vault_files = [p for p in sorted(all_entries) if p.is_file()]
    if not notes.exists():
        return {
            "action": "pure-move", "project": str(project),
            "files": [_plan_relpath(p, vault_project_dir) for p in vault_files],
        }
    if not notes.is_dir():
        return {"action": "repo-side-conflict", "project": str(project)}
    to_copy, already_present, conflicts = [], [], []
    for path in vault_files:
        rel = path.relative_to(vault_project_dir)
        dest = notes / rel
        if not dest.exists():
            to_copy.append(_plan_relpath(path, vault_project_dir))
        elif dest.read_bytes() != path.read_bytes():
            conflicts.append(_plan_relpath(path, vault_project_dir))
        else:
            # Byte-identical: already migrated by a prior interrupted/partial run. Nothing to
            # copy, but the vault-side original still needs cleaning up to finish the migration.
            already_present.append(_plan_relpath(path, vault_project_dir))
    if conflicts:
        return {"action": "conflict", "project": str(project), "conflicts": conflicts}
    return {"action": "merge", "project": str(project), "files": to_copy, "already_present": already_present}


def _vault_project_dir_for(vault, project):
    return Path(vault) / "Proyectos" / Path(project).resolve().name


def _vault_side_for_doctor(vault, project_path):
    """Registry-driven resolution for --vault-doctor's per-project pass (SEC-004): a
    directory that merely SHARES a project's basename under Proyectos/ is not the same
    project. The registry (keyed by the exact resolved repo path) is authoritative when an
    entry exists; the basename convention is only a fallback for a genuinely never-linked
    project, and even then refused if that same vault-side path is already claimed by a
    DIFFERENT registered repo -- demonstrated moving one client's confidential notes into
    another client's repo purely because both repos share a basename.

    Returns (vault_side, refusal_reason). `vault_side` is None when refused.
    """
    # `vault_side` is always the basename convention -- both topologies place their
    # vault-side artifact at `vault/Proyectos/<name>` (vault_link_private is called with
    # exactly that path; hybrid's `link` IS that path). This function never trusts a
    # registered entry's stored `vault_path` for the path itself (even though, since the
    # write_vault_registry_entry fix, hybrid entries DO correctly store the vault-side
    # symlink location now) -- membership is all it needs the registry for: does some OTHER
    # repo already occupy this same conventional path?
    registry = read_vault_registry(vault)
    key = str(Path(project_path).resolve())
    vault_side = _vault_project_dir_for(vault, project_path)
    if key not in registry:
        claimed_by = next(
            (other_repo for other_repo in registry
             if other_repo != key and _vault_project_dir_for(vault, other_repo).resolve() == vault_side.resolve()),
            None,
        )
        if claimed_by:
            return None, f"path-claimed-by-other-project other_project={claimed_by}"
    return vault_side, None


def vault_doctor_report(vault):
    """Report-only (ORQ-4): registered projects' topology/health, plus any REAL directory
    under Proyectos/ that has no registry entry at all (a lost-link candidate for T-206)."""
    vault = Path(vault)
    registry = read_vault_registry(vault)
    seen = set()
    rows = []
    for repo_path, entry in sorted(registry.items()):
        project = Path(repo_path)
        vault_path = Path(entry["vault_path"])
        if vault_path.exists() or vault_path.is_symlink():
            seen.add(vault_path.resolve())
        notes = project / "docs" / "notas"
        if entry["topology"] == "hybrid":
            linked, real = vault_path, notes
        else:
            linked, real = notes, vault_path
        if not linked.exists() and not linked.is_symlink():
            health = "dangling"
        elif not linked.is_symlink():
            health = "drift"  # a real directory sits where a link should be
        elif not linked.resolve().exists():
            # A symlink whose target got deleted/renamed still IS a symlink and
            # Path.resolve() on it still returns that (now-gone) target rather than
            # raising -- without this check it would fall through to the equality
            # branch below, and a dangling link whose target happens to equal `real`
            # (the common case: `real` is the very target that got deleted) would
            # misreport as "healthy" instead of "dangling".
            health = "dangling"
        elif linked.resolve() != real.resolve():
            health = "drift"
        else:
            health = "healthy"
        rows.append({"project": repo_path, "topology": entry["topology"], "health": health})
    projects_dir = vault / "Proyectos"
    if projects_dir.is_dir():
        for candidate in sorted(projects_dir.iterdir()):
            if candidate.resolve() in seen:
                continue
            if candidate.is_dir() and not candidate.is_symlink():
                rows.append({"project": None, "vault_path": str(candidate), "topology": None, "health": "unregistered"})
    return rows


def _plan_fingerprint(plan):
    import hashlib
    return hashlib.sha256(json.dumps(plan, sort_keys=True).encode()).hexdigest()


def _read_vault_doctor_marker(marker):
    """Consume the marker (single-use, atomically-enough for a single-operator CLI) and
    return its parsed content, or None if it's absent/corrupt/expired. SEC-008: a corrupt
    marker used to raise `json.JSONDecodeError` straight through the CLI; this also closes
    the read-then-unlink gap by unlinking BEFORE trusting the content, so a second racing
    `--repair` sees the marker gone rather than a partially-consumed one.
    """
    try:
        raw_bytes = marker.read_bytes()
        marker.unlink()
    except OSError:
        return None
    # DR-006: reading as text (implicit UTF-8, strict) raised UnicodeDecodeError for a
    # non-UTF-8 marker BEFORE the unlink() above ran, both crashing the CLI and leaving the
    # marker in place -- breaking the single-use invariant on exactly the corrupt-input path
    # it exists to handle. Bytes are read (can't fail on decoding) and unlinked first; decode
    # errors past that point are just another "not a valid marker" outcome.
    try:
        recorded = json.loads(raw_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    if not isinstance(recorded, dict):
        return None
    # SEC-008: a --dry-run marker with no expiry stayed valid forever -- see
    # set_agents_app.VAULT_DOCTOR_MARKER_TTL_SECONDS (the caller applies the TTL; this
    # function only parses/consumes the marker and returns its recorded fields).
    return recorded
