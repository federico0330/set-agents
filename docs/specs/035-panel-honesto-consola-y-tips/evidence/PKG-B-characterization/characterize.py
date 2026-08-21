#!/usr/bin/env python3
"""PKG-B CLI characterization runner — three channels, closed normalizers, disposable isolation."""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parents[5]
CLI = ROOT / "ai" / "scripts" / "set_agents_app.py"
HERE = Path(__file__).resolve().parent
BASELINE = HERE / "baseline"
AFTER = HERE / "after"
NORMALIZERS_MD = HERE / "NORMALIZERS.md"

ALLOWED_ENV_KEYS = frozenset({
    "PATH",
    "HOME",
    "TMPDIR",
    "LANG",
    "LC_ALL",
    "TERM",
    "GIT_TERMINAL_PROMPT",
    "SET_AGENTS_STATE",
    "SET_AGENTS_ROUTING_TEST_ROOT",
})
_SENSITIVE_ENV_RE = re.compile(
    r"(XAUTHORITY|ICEAUTHORITY|TOKEN|SECRET|CREDENTIAL|API_KEY|PASSWORD|AWS_|GCP_|AZURE_)",
    re.IGNORECASE,
)
_LAUNCHER_ERR_RE = re.compile(r"can't open file")

# --- normalizers (1:1 with NORMALIZERS.md) ---------------------------------

_TIMESTAMP_RE = re.compile(
    r"\b\d{4}-\d{2}-\d{2}(?:[ T]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?)?\b"
)
_TMP_PATH_RE = re.compile(
    r"(?<![\w./-])/(?:tmp|var/tmp|dev/shm)(?:/[^\s\"']+)+"
)
_DURATION_MS_RE = re.compile(r"\b\d+(?:\.\d+)?ms\b")
_PID_RE = re.compile(r"\bpid[=:]?\s*\d{4,7}\b", re.IGNORECASE)
_SHA_RE = re.compile(r"\bsha=[0-9a-f]{7,40}\b")
_SEMVER_RE = re.compile(r"\bv?\d+\.\d+(?:\.\d+)?(?:[-+][0-9A-Za-z.-]+)?\b")


def _home_path_re(home: str) -> re.Pattern[str]:
    return re.compile(r"(?<![\w./-])" + re.escape(home) + r"(?:/[^\s\"']+)*")


def normalize_timestamps(text: str) -> str:
    return _TIMESTAMP_RE.sub("<TIMESTAMP>", text)


def normalize_absolute_tmp_paths(text: str, *, home: str | None = None) -> str:
    out = _TMP_PATH_RE.sub("<TMPPATH>", text)
    if home:
        out = _home_path_re(home).sub("<HOME>", out)
    return out


def normalize_durations_ms(text: str) -> str:
    return _DURATION_MS_RE.sub("<DURATION_MS>", text)


def normalize_pids(text: str) -> str:
    return _PID_RE.sub("pid=<PID>", text)


def normalize_versions(text: str) -> str:
    out = _SHA_RE.sub("sha=<SHA>", text)
    return _SEMVER_RE.sub("<VERSION>", out)


NORMALIZERS: dict[str, Callable[[str], str]] = {
    "normalize_timestamps": normalize_timestamps,
    "normalize_absolute_tmp_paths": normalize_absolute_tmp_paths,
    "normalize_durations_ms": normalize_durations_ms,
    "normalize_pids": normalize_pids,
    "normalize_versions": normalize_versions,
}


def _normalizer_names_in_md() -> set[str]:
    text = NORMALIZERS_MD.read_text(encoding="utf-8")
    return {m.group(1) for m in re.finditer(r"`(normalize_[a-z_]+)`", text)}


def verify_normalizer_bijection() -> None:
    md_names = _normalizer_names_in_md()
    code_names = set(NORMALIZERS)
    if md_names != code_names:
        only_md = sorted(md_names - code_names)
        only_code = sorted(code_names - md_names)
        raise SystemExit(
            "NORMALIZER bijection broken.\n"
            f"  only in NORMALIZERS.md: {only_md}\n"
            f"  only in characterize.py: {only_code}"
        )


def apply_normalizers(text: str, *, home: str | None = None) -> str:
    text = normalize_timestamps(text)
    text = normalize_absolute_tmp_paths(text, home=home)
    text = normalize_durations_ms(text)
    text = normalize_pids(text)
    text = normalize_versions(text)
    return text


# --- cases -----------------------------------------------------------------

@dataclass(frozen=True)
class Case:
    case_id: str
    group: str
    argv: tuple[str, ...]
    isolation: str  # plain | disposable | declared-uncharacterizable
    dry_run: bool = False
    reason: str = ""
    needs_project: bool = False


CASES: tuple[Case, ...] = (
    Case("global-help", "global", ("--help",), "plain"),
    Case("global-no-args", "global", (), "plain"),
    Case("estado-valid", "estado", ("--status",), "plain"),
    Case("estado-missing-arg", "estado", ("--model-pin-set", "role"), "plain"),
    Case("estado-invalid", "estado", ("--harness", "invalid"), "plain"),
    Case("routing-valid", "routing", ("--routing-report", "--json"), "disposable", needs_project=True),
    Case("routing-missing-arg", "routing", ("--route-explain",), "plain"),
    Case("routing-invalid", "routing", ("--route-terminal", "run1_bad", "not-an-outcome"), "disposable", needs_project=True),
    Case(
        "routing-route-decide",
        "routing",
        ("--route-decide", "-"),
        "declared-uncharacterizable",
        reason="host policy: Cursor never --route-decide",
    ),
    Case(
        "routing-route-dispatched",
        "routing",
        ("--route-dispatched", "run1_test"),
        "disposable",
        needs_project=True,
    ),
    Case(
        "routing-route-terminal",
        "routing",
        ("--route-terminal", "run1_test", "success"),
        "disposable",
        needs_project=True,
    ),
    Case(
        "routing-route-quota-exhausted",
        "routing",
        ("--route-quota-exhausted", "run1_test", "--quota-error", "{}", "--latency-ms", "1"),
        "disposable",
        needs_project=True,
    ),
    Case(
        "routing-fresh-probes",
        "routing",
        ("--fresh-probes",),
        "declared-uncharacterizable",
        reason="host policy: Cursor never --route-decide family (modifier for --route-decide)",
    ),
    Case("vault-valid", "vault", ("--vault-doctor", "--dry-run"), "disposable", dry_run=True, needs_project=True),
    Case("vault-missing-arg", "vault", ("--vault-link",), "plain"),
    Case("vault-invalid", "vault", ("--vault-doctor", "--repair"), "disposable", needs_project=True),
    Case("instalacion-valid", "instalacion", ("--check-update",), "disposable"),
    Case("instalacion-missing-arg", "instalacion", ("--auto-update",), "plain"),
    Case("instalacion-invalid", "instalacion", ("--auto-update", "maybe"), "plain"),
    Case("herramientas-valid", "herramientas", ("--tools",), "disposable"),
    Case("herramientas-missing-arg", "herramientas", ("--tools-install",), "plain"),
    Case("herramientas-invalid", "herramientas", ("--mcp-add",), "plain"),
    Case("proveedores-valid", "proveedores", ("--provider-list",), "disposable"),
    Case("proveedores-missing-arg", "proveedores", ("--provider-add",), "plain"),
    Case("proveedores-invalid", "proveedores", ("--provider-add", "badid"), "plain"),
    Case("posturas-valid", "posturas", ("--posturas",), "disposable"),
    Case("posturas-missing-arg", "posturas", ("--model-preference-role-override", "role"), "plain"),
    Case("posturas-invalid", "posturas", ("--postura", "invalid"), "plain"),
    Case("mutant-vault-init", "vault", ("--vault-init", "company"), "disposable", needs_project=True),
    Case("mutant-vault-link", "vault", ("--vault-link", "proj", "--vault", "vault/obsidian"), "disposable", needs_project=True),
    Case("mutant-scaffold", "instalacion", ("--scaffold",), "disposable", needs_project=True),
    Case("mutant-update-dry-run", "instalacion", ("--update", "--dry-run"), "disposable", dry_run=True),
    Case("mutant-tools-install", "herramientas", ("--tools-install", "nonexistent-tool-xyz", "--dry-run"), "disposable", dry_run=True),
    Case("mutant-mcp-add", "herramientas", ("--mcp-add", "brave-search", "--harness", "cursor"), "disposable"),
    Case("mutant-mcp-remove", "herramientas", ("--mcp-remove", "brave-search", "--harness", "cursor"), "disposable"),
    Case("mutant-provider-add", "proveedores", ("--provider-add", "testprov", "--base-url", "https://example.invalid/v1", "--dry-run"), "disposable", dry_run=True),
    Case(
        "mutant-provider-remove",
        "proveedores",
        ("--provider-remove", "nonexistent-id"),
        "disposable",
    ),
    Case("mutant-plugin-on", "herramientas", ("--plugin-on", "frontend-design"), "disposable"),
    Case("mutant-plugin-off", "herramientas", ("--plugin-off", "frontend-design"), "disposable"),
    Case("mutant-model-pin-set", "posturas", ("--model-pin-set", "implementer", "cursor/composer-2.5"), "disposable"),
    Case("mutant-model-pin-clear", "posturas", ("--model-pin-clear", "implementer"), "disposable"),
    Case("mutant-routing-migrate", "routing", ("--routing-migrate",), "disposable", needs_project=True),
    Case("mutant-prune-dead", "proveedores", ("--provider-verify", "--prune-dead"), "disposable"),
    Case("mutant-provider-verify", "proveedores", ("--provider-verify",), "disposable"),
    Case("mutant-quota-failover-e2e", "routing", ("--quota-failover-e2e",), "disposable"),
)


def _require_cli() -> None:
    if not CLI.is_file():
        raise SystemExit(f"CLI entry missing or not a file: {CLI}")


def _assert_env_safe() -> None:
    for key in ALLOWED_ENV_KEYS:
        if _SENSITIVE_ENV_RE.search(key):
            raise SystemExit(f"allowlist contains sensitive env key: {key!r}")


def _build_child_env(
    *,
    home: Path,
    state_dir: Path,
    routing_test_root: Path | None = None,
) -> dict[str, str]:
    env: dict[str, str] = {}
    for key in ALLOWED_ENV_KEYS:
        if key == "HOME":
            env["HOME"] = str(home)
        elif key == "SET_AGENTS_STATE":
            env["SET_AGENTS_STATE"] = str(state_dir)
        elif key == "SET_AGENTS_ROUTING_TEST_ROOT":
            if routing_test_root is not None:
                env["SET_AGENTS_ROUTING_TEST_ROOT"] = str(routing_test_root)
        elif key in os.environ:
            env[key] = os.environ[key]
    env.setdefault("GIT_TERMINAL_PROMPT", "0")
    return env


def _is_launcher_error(stderr: str) -> bool:
    return bool(_LAUNCHER_ERR_RE.search(stderr))


def _read_capture_home(dest_dir: Path, case_id: str) -> str | None:
    sidecar = dest_dir / f"{case_id}.home"
    if not sidecar.exists():
        return None
    value = sidecar.read_text(encoding="utf-8").strip()
    return value or None


def _prepare_disposable(case: Case) -> tuple[dict[str, str], Path, Path, tempfile.TemporaryDirectory[str]]:
    tmp = tempfile.TemporaryDirectory(prefix="set-agents-char-")
    home = Path(tmp.name) / "home"
    home.mkdir()
    project = home / "proj"
    project.mkdir()
    routing_root = Path(tmp.name) / "routing"
    routing_root.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=project, check=False, capture_output=True)
    (project / "ai" / "state").mkdir(parents=True, exist_ok=True)
    (project / "ai" / "state" / "project.json").write_text('{"name":"char-proj"}\n', encoding="utf-8")
    if case.needs_project and case.group == "vault":
        vault = home / "vault" / "obsidian"
        vault.mkdir(parents=True)
        (vault / "00 - INICIO.md").write_text("# vault\n", encoding="utf-8")
    env = _build_child_env(
        home=home,
        state_dir=home / ".local" / "state" / "set-agentes",
        routing_test_root=routing_root if case.group == "routing" else None,
    )
    return env, project, home, tmp


def run_case(case: Case) -> tuple[int, str, str, str | None] | None:
    if case.isolation == "declared-uncharacterizable":
        return None
    cwd = ROOT
    env = _build_child_env(
        home=Path(os.environ.get("HOME", str(Path.home()))),
        state_dir=Path(os.environ.get("SET_AGENTS_STATE", str(Path.home() / ".local" / "state" / "set-agentes"))),
    )
    capture_home: str | None = None
    holder: tempfile.TemporaryDirectory[str] | None = None
    if case.isolation == "disposable":
        env, project, capture_home_path, holder = _prepare_disposable(case)
        capture_home = str(capture_home_path)
        cwd = project
        if case.needs_project and case.group == "routing":
            subprocess.run(
                [sys.executable, str(CLI), "--scaffold"],
                cwd=project,
                env=env,
                capture_output=True,
                text=True,
                timeout=120,
            )
        if case.case_id == "mutant-vault-link":
            vault = Path(env["HOME"]) / "vault" / "obsidian"
            vault.mkdir(parents=True, exist_ok=True)
            (vault / "00 - INICIO.md").write_text("# vault\n", encoding="utf-8")
            (project / "docs" / "notas").mkdir(parents=True, exist_ok=True)
    argv = [sys.executable, str(CLI), *case.argv]
    try:
        proc = subprocess.run(
            argv,
            cwd=cwd,
            env=env,
            capture_output=True,
            text=True,
            timeout=120,
        )
    finally:
        if holder is not None:
            holder.cleanup()
    return proc.returncode, proc.stdout, proc.stderr, capture_home


def write_capture(case: Case, dest_dir: Path) -> str:
    if case.isolation == "declared-uncharacterizable":
        (dest_dir / f"{case.case_id}.stdout").write_text("", encoding="utf-8")
        (dest_dir / f"{case.case_id}.stderr").write_text(f"declared-uncharacterizable: {case.reason}\n", encoding="utf-8")
        (dest_dir / f"{case.case_id}.exit").write_text("declared\n", encoding="utf-8")
        return "declared-uncharacterizable"
    result = run_case(case)
    assert result is not None
    code, stdout, stderr, capture_home = result
    (dest_dir / f"{case.case_id}.stdout").write_text(stdout, encoding="utf-8")
    (dest_dir / f"{case.case_id}.stderr").write_text(stderr, encoding="utf-8")
    (dest_dir / f"{case.case_id}.exit").write_text(f"{code}\n", encoding="utf-8")
    if capture_home is not None:
        (dest_dir / f"{case.case_id}.home").write_text(capture_home + "\n", encoding="utf-8")
    return "captured"


def compare_case(case: Case) -> list[str]:
    if case.isolation == "declared-uncharacterizable":
        return [f"{case.case_id}: declared-uncharacterizable ({case.reason})"]
    lines: list[str] = []
    for channel, ext in (("stdout", ".stdout"), ("stderr", ".stderr"), ("exit", ".exit")):
        base = (BASELINE / f"{case.case_id}{ext}").read_text(encoding="utf-8")
        after = (AFTER / f"{case.case_id}{ext}").read_text(encoding="utf-8")
        norm_base = apply_normalizers(base, home=_read_capture_home(BASELINE, case.case_id))
        norm_after = apply_normalizers(after, home=_read_capture_home(AFTER, case.case_id))
        if norm_base == norm_after:
            lines.append(f"{case.case_id}/{channel}: idéntico")
        else:
            digest_base = hashlib.sha256(norm_base.encode()).hexdigest()[:12]
            digest_after = hashlib.sha256(norm_after.encode()).hexdigest()[:12]
            lines.append(
                f"{case.case_id}/{channel}: DIFF base={digest_base} after={digest_after} "
                f"(len {len(norm_base)} vs {len(norm_after)})"
            )
    return lines


def cmd_capture(target: Path) -> None:
    _require_cli()
    _assert_env_safe()
    target.mkdir(parents=True, exist_ok=True)
    launcher_errors: list[str] = []
    executable = 0
    for case in CASES:
        if case.isolation == "declared-uncharacterizable":
            write_capture(case, target)
            print(f"captured {case.case_id} -> {target.name}/")
            continue
        executable += 1
        result = run_case(case)
        assert result is not None
        code, stdout, stderr, capture_home = result
        if _is_launcher_error(stderr):
            launcher_errors.append(case.case_id)
        (target / f"{case.case_id}.stdout").write_text(stdout, encoding="utf-8")
        (target / f"{case.case_id}.stderr").write_text(stderr, encoding="utf-8")
        (target / f"{case.case_id}.exit").write_text(f"{code}\n", encoding="utf-8")
        if capture_home is not None:
            (target / f"{case.case_id}.home").write_text(capture_home + "\n", encoding="utf-8")
        print(f"captured {case.case_id} -> {target.name}/")
    if executable and len(launcher_errors) == executable:
        raise SystemExit(
            "all executable cases failed with the same launcher error (can't open file); "
            f"cases={launcher_errors}"
        )


def cmd_compare() -> None:
    verify_normalizer_bijection()
    rows: list[str] = ["# PKG-B characterization RESULT", "", f"Compared: {len(CASES)} cases", ""]
    identical = declared = diffs = 0
    for case in CASES:
        case_lines = compare_case(case)
        rows.extend(case_lines)
        rows.append("")
        if case.isolation == "declared-uncharacterizable":
            declared += 1
        elif all("idéntico" in line for line in case_lines):
            identical += 1
        else:
            diffs += 1
    rows.insert(3, f"Summary: identical={identical} declared-uncharacterizable={declared} diff_cases={diffs}")
    (HERE / "RESULT.md").write_text("\n".join(rows), encoding="utf-8")
    print(f"Wrote RESULT.md identical={identical} declared={declared} diff_cases={diffs}")


def cmd_manifest() -> None:
    head = subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip()
    lines = [
        "# PKG-B characterization MANIFEST",
        "",
        f"**Sealed:** 2026-08-20",
        f"**git HEAD:** `{head}`",
        f"**CLI entry:** `python3 ai/scripts/set_agents_app.py`",
        "",
        "| case-id | group | argv | isolation | dry-run |",
        "|---|---|---|---|---|",
    ]
    for case in CASES:
        argv = " ".join(case.argv) if case.argv else "(no args)"
        lines.append(
            f"| `{case.case_id}` | {case.group} | `{argv}` | {case.isolation} | {case.dry_run} |"
        )
    (HERE / "MANIFEST.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote MANIFEST.md HEAD={head[:12]}")


def main() -> int:
    parser = argparse.ArgumentParser(description="PKG-B CLI characterization runner")
    parser.add_argument("command", choices=("manifest", "baseline", "after", "compare"))
    args = parser.parse_args()
    if args.command in ("baseline", "after", "compare"):
        _require_cli()
    if args.command == "manifest":
        cmd_manifest()
    elif args.command == "baseline":
        verify_normalizer_bijection()
        cmd_capture(BASELINE)
    elif args.command == "after":
        verify_normalizer_bijection()
        cmd_capture(AFTER)
    elif args.command == "compare":
        cmd_compare()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
