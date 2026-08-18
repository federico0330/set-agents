#!/usr/bin/env python3
"""Evidence-based risk classification for a package's frozen candidate (docs/adr/0021-*.md).

Never reads file count or line count -- a five-line auth change outranks a
five-thousand-line mechanical rename, so only named evidence escalates.
Self-contained (no feature_state_lib import), matching check-owned-paths.py's
standalone-scaffold-script pattern -- both are copied as their own generic
files by sync-project.sh, independent of the feature_state_lib family.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any

# Path-token signals: a changed path whose name plausibly touches one of these
# surfaces is HIGH risk regardless of how small the diff is.
HIGH_PATH_SIGNALS = {
    "auth": re.compile(r"(^|/)(auth|authn|authz|login|session)([/_.\-]|$)", re.IGNORECASE),
    "payments": re.compile(r"(^|/)(payment|billing|invoice|checkout)([/_.\-]|$)", re.IGNORECASE),
    "pii": re.compile(r"(^|/)(pii|personal[_-]?data|profile)([/_.\-]|$)", re.IGNORECASE),
    "secrets": re.compile(r"(secret|token|credential|api[_-]?key)", re.IGNORECASE),
    "tenant": re.compile(r"(^|/)(tenant|organi[sz]ation)([/_.\-]|$)", re.IGNORECASE),
    "migration": re.compile(r"(^|/)(migrations?|schema)([/_.\-]|$)", re.IGNORECASE),
}

# A workflow/shell file is MEDIUM on its own -- worth a closer look, not
# automatically an identity/money/PII-grade surface.
MEDIUM_PATH_SIGNALS = {
    "workflow": re.compile(r"^\.github/workflows/"),
    "shell-script": re.compile(r"\.sh$"),
}

# Content signals, checked on the candidate's own bytes for the changed path.
SHEBANG_RE = re.compile(rb"^#!")
SUBPROCESS_RE = re.compile(rb"\b(subprocess|os\.system|child_process|Process\.Start)\b")
CONTENT_SCAN_LIMIT = 8192  # bytes; enough to catch a shebang or an early import, cheap to read


def load_state(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def package_by_id(data: dict[str, Any], package_id: str) -> dict[str, Any]:
    for package in data.get("packages", []):
        if package.get("package_id") == package_id:
            return package
    raise SystemExit(f"UNKNOWN_PACKAGE: {package_id}")


def _git_text(args: list[str]) -> str:
    result = subprocess.run(["git", *args], text=True, capture_output=True, check=False)
    if result.returncode != 0:
        raise SystemExit(f"GIT_FAILED: {' '.join(args)}: {result.stderr.strip()}")
    return result.stdout


def _git_bytes(args: list[str]) -> bytes:
    result = subprocess.run(["git", *args], capture_output=True, check=False)
    if result.returncode != 0:
        return b""  # binary/missing/renamed-away path: no content signal, not a hard failure
    return result.stdout


def changed_paths(base_tree: str, candidate_tree: str) -> list[str]:
    out = _git_text(["diff", "--name-only", base_tree, candidate_tree])
    return [line.strip() for line in out.splitlines() if line.strip()]


def executable_mode_added(base_tree: str, candidate_tree: str, path: str) -> bool:
    summary = _git_text(["diff", "--summary", base_tree, candidate_tree, "--", path])
    return "mode change 100644 => 100755" in summary or "new mode 100755" in summary


def content_signals(candidate_tree: str, path: str) -> set[str]:
    raw = _git_bytes(["show", f"{candidate_tree}:{path}"])[:CONTENT_SCAN_LIMIT]
    signals = set()
    if SHEBANG_RE.match(raw):
        signals.add("shebang")
    if SUBPROCESS_RE.search(raw):
        signals.add("subprocess-spawn")
    return signals


def classify(base_tree: str, candidate_tree: str) -> tuple[str, list[str]]:
    high_reasons: list[str] = []
    medium_reasons: list[str] = []
    for path in changed_paths(base_tree, candidate_tree):
        for name, pattern in HIGH_PATH_SIGNALS.items():
            if pattern.search(path):
                high_reasons.append(f"path:{name}:{path}")
        for name, pattern in MEDIUM_PATH_SIGNALS.items():
            if pattern.search(path):
                medium_reasons.append(f"path:{name}:{path}")
        if executable_mode_added(base_tree, candidate_tree, path):
            high_reasons.append(f"content:executable-mode-added:{path}")
        for signal in content_signals(candidate_tree, path):
            high_reasons.append(f"content:{signal}:{path}")
    if high_reasons:
        return "high", sorted(set(high_reasons))
    if medium_reasons:
        return "medium", sorted(set(medium_reasons))
    return "low", []


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--state-file", required=True)
    parser.add_argument("--package-id", required=True)
    args = parser.parse_args()

    data = load_state(Path(args.state_file))
    package = package_by_id(data, args.package_id)
    frozen = package.get("candidate_identity")
    if not frozen:
        raise SystemExit("NO_CANDIDATE_IDENTITY: run freeze-candidate before classify-risk.py")

    level, reasons = classify(frozen["base_tree"], frozen["candidate_tree"])
    payload = {"package_id": args.package_id, "level": level, "reasons": reasons}
    print(json.dumps(payload, indent=2, sort_keys=True))
    print(f"RISK_LEVEL {level}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
