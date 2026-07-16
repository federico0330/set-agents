#!/usr/bin/env python3
"""Token-consumption report per project across the three harnesses.

Reads the session stores each harness already writes (no instrumentation):
- OpenCode:    ~/.local/share/opencode/opencode.db  (session table aggregates, per-agent)
- Claude Code: ~/.claude/projects/<enc-cwd>/**/*.jsonl (per-message usage, per-agent)
- Codex:       ~/.codex/state_5.sqlite threads (per-thread aggregate; --deep parses the
               rollout jsonl for the cached/reasoning breakdown)

Tokens only — subscription plans have no meaningful dollar-per-token, what matters is quota.

Usage:
  cost-report.py [--project DIR] [--since YYYY-MM-DD] [--md] [--deep] [--home DIR]
"""

import argparse
import datetime as dt
import json
import sqlite3
from collections import defaultdict
from pathlib import Path

FIELDS = ("input", "output", "cache_read", "cache_write", "reasoning")


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--project", help="only sessions whose cwd is inside this directory")
    parser.add_argument("--since", help="only sessions updated on/after this date (YYYY-MM-DD)")
    parser.add_argument("--md", action="store_true", help="markdown output")
    parser.add_argument("--deep", action="store_true", help="Codex: parse rollouts for cached/reasoning split")
    parser.add_argument("--home", default=str(Path.home()), help=argparse.SUPPRESS)
    return parser.parse_args()


def new_bucket():
    return {field: 0 for field in FIELDS} | {"sessions": 0}


def since_epoch_ms(since):
    if not since:
        return None
    return int(dt.datetime.strptime(since, "%Y-%m-%d").timestamp() * 1000)


def in_project(directory, project):
    if not project:
        return True
    if not directory:
        return False
    try:
        Path(directory).resolve().relative_to(Path(project).resolve())
        return True
    except ValueError:
        return False


def add(report, project_dir, harness, model, agent, bucket_update):
    bucket = report[(project_dir or "?", harness, model or "?", agent or "-")]
    for key, value in bucket_update.items():
        bucket[key] += value


def collect_opencode(report, home, project, since_ms):
    db = home / ".local/share/opencode/opencode.db"
    if not db.exists():
        return
    conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    try:
        rows = conn.execute(
            "SELECT directory, model, agent, tokens_input, tokens_output, tokens_cache_read,"
            " tokens_cache_write, tokens_reasoning, time_updated FROM session"
        )
        for directory, model, agent, t_in, t_out, t_cr, t_cw, t_re, updated in rows:
            if since_ms and (updated or 0) < since_ms:
                continue
            if not in_project(directory, project):
                continue
            if model:
                try:
                    parsed = json.loads(model)
                    model = f"{parsed.get('providerID', '?')}/{parsed.get('id', '?')}"
                except (ValueError, TypeError):
                    pass
            add(report, directory, "opencode", model, agent, {
                "input": t_in or 0, "output": t_out or 0, "cache_read": t_cr or 0,
                "cache_write": t_cw or 0, "reasoning": t_re or 0, "sessions": 1,
            })
    finally:
        conn.close()


def collect_claude(report, home, project, since_ms):
    root = home / ".claude/projects"
    if not root.is_dir():
        return
    for transcript in root.glob("**/*.jsonl"):
        if since_ms and transcript.stat().st_mtime * 1000 < since_ms:
            continue
        seen_session = set()
        try:
            with transcript.open() as handle:
                for line in handle:
                    if '"usage"' not in line:
                        continue
                    try:
                        entry = json.loads(line)
                    except ValueError:
                        continue
                    message = entry.get("message") or {}
                    usage = message.get("usage")
                    if not usage or entry.get("type") != "assistant":
                        continue
                    cwd = entry.get("cwd")
                    if not in_project(cwd, project):
                        continue
                    agent = entry.get("attributionAgent") or ("subagent" if entry.get("isSidechain") else "main")
                    key = (cwd, message.get("model"), agent)
                    add(report, cwd, "claude-code", message.get("model"), agent, {
                        "input": usage.get("input_tokens", 0),
                        "output": usage.get("output_tokens", 0),
                        "cache_read": usage.get("cache_read_input_tokens", 0),
                        "cache_write": usage.get("cache_creation_input_tokens", 0),
                        "reasoning": 0,
                        "sessions": 0 if key in seen_session else 1,
                    })
                    seen_session.add(key)
        except OSError:
            continue


def codex_rollout_breakdown(rollout_path):
    """Last cumulative token_count of a rollout → cached/reasoning split."""
    last = None
    try:
        with open(rollout_path) as handle:
            for line in handle:
                if '"token_count"' not in line:
                    continue
                try:
                    payload = json.loads(line).get("payload") or {}
                except ValueError:
                    continue
                info = payload.get("info") or {}
                usage = info.get("total_token_usage")
                if usage:
                    last = usage
    except OSError:
        return None
    return last


def collect_codex(report, home, project, since_ms, deep):
    db = home / ".codex/state_5.sqlite"
    if not db.exists():
        return
    conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    try:
        rows = conn.execute(
            "SELECT cwd, model, agent_role, tokens_used, updated_at, rollout_path FROM threads"
        )
        for cwd, model, agent_role, tokens, updated, rollout in rows:
            # updated_at is epoch seconds in state_5; tolerate ms too
            updated_ms = (updated or 0) * (1 if (updated or 0) > 10**12 else 1000)
            if since_ms and updated_ms < since_ms:
                continue
            if not in_project(cwd, project):
                continue
            usage = codex_rollout_breakdown(rollout) if deep and rollout else None
            if usage:
                add(report, cwd, "codex", model, agent_role, {
                    "input": usage.get("input_tokens", 0) - usage.get("cached_input_tokens", 0),
                    "output": usage.get("output_tokens", 0),
                    "cache_read": usage.get("cached_input_tokens", 0),
                    "cache_write": 0,
                    "reasoning": usage.get("reasoning_output_tokens", 0),
                    "sessions": 1,
                })
            else:
                add(report, cwd, "codex", model, agent_role, {
                    "input": tokens or 0, "output": 0, "cache_read": 0, "cache_write": 0,
                    "reasoning": 0, "sessions": 1,
                })
    finally:
        conn.close()


def fmt(n):
    if n >= 10**9:
        return f"{n / 10**9:.1f}G"
    if n >= 10**6:
        return f"{n / 10**6:.1f}M"
    if n >= 10**3:
        return f"{n / 10**3:.1f}k"
    return str(n)


def render(report, md):
    if not report:
        print("No sessions matched.")
        return
    header = ("project", "harness", "model", "agent", "sessions", "input", "output", "cache_read", "cache_write", "reasoning", "total")
    rows = []
    totals = defaultdict(int)
    for (project_dir, harness, model, agent), bucket in sorted(report.items()):
        total = sum(bucket[field] for field in FIELDS)
        rows.append((project_dir, harness, model, agent, str(bucket["sessions"]),
                     *(fmt(bucket[field]) for field in FIELDS), fmt(total)))
        for field in FIELDS:
            totals[field] += bucket[field]
        totals["sessions"] += bucket["sessions"]
    grand = sum(totals[field] for field in FIELDS)
    footer = ("TOTAL", "", "", "", str(totals["sessions"]), *(fmt(totals[field]) for field in FIELDS), fmt(grand))
    if md:
        print("| " + " | ".join(header) + " |")
        print("|" + "---|" * len(header))
        for row in rows + [footer]:
            print("| " + " | ".join(row) + " |")
    else:
        widths = [max(len(str(row[i])) for row in [header, footer, *rows]) for i in range(len(header))]
        for row in [header, *rows, footer]:
            print("  ".join(str(cell).ljust(width) for cell, width in zip(row, widths)))


def main():
    args = parse_args()
    home = Path(args.home)
    since_ms = since_epoch_ms(args.since)
    report = defaultdict(new_bucket)
    collect_opencode(report, home, args.project, since_ms)
    collect_claude(report, home, args.project, since_ms)
    collect_codex(report, home, args.project, since_ms, args.deep)
    render(report, args.md)


if __name__ == "__main__":
    main()
