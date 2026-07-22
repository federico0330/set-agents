#!/usr/bin/env python3
"""One-shot migration: legacy roles.tsv (model columns) -> models.toml + trimmed roles.tsv.

Areas get the majority value per duty; roles that differ become [roles.<role>]
overrides, so the migrated config resolves to exactly the legacy assignment.
Deleted after the migration lands (see plan phase 6).
"""

import argparse
import csv
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import models_config

ROOT = Path(__file__).resolve().parents[2]
LEGACY_LANE_COLUMNS = {"go-zen": "opencode_go", "zen": "opencode_zen", "local": "opencode_local"}
LEGACY_HEADER = [
    "role", "mode", "temperature", "capability", "duty", "opencode_go",
    "opencode_zen", "opencode_local", "claude_model", "codex_model", "codex_effort",
]
CATALOG_BASE = {
    "claude": {"opus", "sonnet", "haiku", "fable"},
    "codex": {"gpt-5.4", "gpt-5.4-mini", "gpt-5.5", "gpt-5.6-sol", "gpt-5.6-terra", "gpt-5.6-luna"},
    "codex_effort": {"low", "medium", "high", "xhigh"},
}


def majority(values):
    counts = Counter(values)
    best = max(counts.values())
    return sorted(value for value, count in counts.items() if count == best)[0]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--roles", default=str(ROOT / "roles.tsv"))
    parser.add_argument("--models-out", default=str(ROOT / "models.toml"))
    parser.add_argument("--roles-out", default=str(ROOT / "roles.tsv"))
    args = parser.parse_args()

    with Path(args.roles).open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if list(reader.fieldnames or ()) != LEGACY_HEADER:
            raise SystemExit("MIGRATE_FAILED: input roles.tsv is not in the legacy format")
        rows = list(reader)

    areas = {}
    for duty in {row["duty"] for row in rows}:
        group = [row for row in rows if row["duty"] == duty]
        areas[duty] = {
            "claude": majority(r["claude_model"] for r in group),
            "codex": majority(r["codex_model"] for r in group),
            "codex_effort": majority(r["codex_effort"] for r in group),
            "opencode": {
                lane: majority(r[column] for r in group)
                for lane, column in LEGACY_LANE_COLUMNS.items()
            },
        }

    overrides = {}
    for row in rows:
        area = areas[row["duty"]]
        override = {}
        for field, column in (("claude", "claude_model"), ("codex", "codex_model"), ("codex_effort", "codex_effort")):
            if row[column] != area[field]:
                override[field] = row[column]
        lanes = {
            lane: row[column]
            for lane, column in LEGACY_LANE_COLUMNS.items()
            if row[column] != area["opencode"][lane]
        }
        if lanes:
            override["opencode"] = lanes
        if override:
            overrides[row["role"]] = override

    config = {
        "schema": 1,
        "subscriptions": {"anthropic": True, "ollama": False, "openai": True, "zen": True},
        "catalog": {
            "claude": sorted(CATALOG_BASE["claude"] | {r["claude_model"] for r in rows}),
            "codex": sorted(CATALOG_BASE["codex"] | {r["codex_model"] for r in rows}),
            "codex_effort": sorted(CATALOG_BASE["codex_effort"] | {r["codex_effort"] for r in rows}),
        },
        "families": {},
        "providers": {},
        "session": {
            # Value hardcoded until now in Global/_shared/opencode.json.
            "opencode_small_model": {lane: "opencode/north-mini-code-free" for lane in models_config.LANES},
        },
        "areas": areas,
        "roles": overrides,
    }

    Path(args.models_out).write_text(models_config.emit(config))
    header = "\t".join(["role", "mode", "temperature", "capability", "duty"])
    trimmed = [header] + [
        "\t".join([row["role"], row["mode"], row["temperature"], row["capability"], row["duty"]])
        for row in rows
    ]
    Path(args.roles_out).write_text("\n".join(trimmed) + "\n")
    print(f"MIGRATE_OK roles={len(rows)} areas={len(areas)} overrides={len(overrides)}")


if __name__ == "__main__":
    main()
