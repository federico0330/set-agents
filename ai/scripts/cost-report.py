#!/usr/bin/env python3
"""Token-consumption report per project across the three harnesses, plus the pi lane.

Reads the session stores each harness already writes (no instrumentation):
- OpenCode:    ~/.local/share/opencode/opencode.db  (session table aggregates, per-agent)
- Claude Code: ~/.claude/projects/<enc-cwd>/**/*.jsonl (per-message usage, per-agent)
- Codex:       ~/.codex/state_5.sqlite threads (per-thread aggregate; --deep parses the
               rollout jsonl for the cached/reasoning breakdown)
- pi:          the routing database this harness's own dispatches write
               (~/.local/state/set-agentes/routing-v2/routing.db). Coverage is bounded to
               spawns the harness itself dispatched through set_agents_spawn.py — a `pi`
               session started by hand is invisible here. The stored project_key is a
               one-way hash, not invertible to a directory: the pi lane is attributed to a
               project only when --project is given (the key is recomputed locally and
               matched); otherwise it is reported unattributed rather than guessed.

Tokens only — subscription plans have no meaningful dollar-per-token, what matters is quota.

Usage:
  cost-report.py [--project DIR] [--since YYYY-MM-DD] [--md] [--deep] [--home DIR]
"""

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import sqlite3
import stat
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

FIELDS = ("input", "output", "cache_read", "cache_write", "reasoning")


def parse_args():
    parser = argparse.ArgumentParser(
        description=__doc__.splitlines()[0],
        epilog="pi lane coverage: only spawns dispatched through set_agents_spawn.py; a pi "
               "session started by hand is invisible here. Without --project it is reported "
               "unattributed (project_key is a one-way hash, never guessed back to a path).",
    )
    parser.add_argument("--project", help="only sessions whose cwd is inside this directory "
                        "(also required to attribute the pi lane to a project)")
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


_PROJECT_KEY_RE = re.compile(r"^proj1_[0-9a-f]{32}$")
# Mirrors set_agents_app.py:_MAX_FEATURE_BYTES exactly -- a smaller cap here would make
# a project.json that project_key_for accepts as valid (merely large, still under ITS
# limit) look "invalid" only on this side, the same kind of divergence this whole
# hardening pass exists to close.
_MAX_IDENTITY_BYTES = 1024 * 1024


class _ProjectIdentityError(ValueError):
    """A present `ai/state/project.json` is unusable; never silently fall back to a path
    hash for it -- that would silently split the project's history, same reasoning as
    `set_agents_app.py:project_key_for`'s `ProjectIdentityError`."""


def _pi_project_key(root):
    """Duplicates `set_agents_app.py:project_key_for`'s public behaviour: a persisted
    `ai/state/project.json` wins, else a casefold-normalized-path hash. Duplicated rather
    than imported because a read-only reporter must never be able to redirect where
    durable authorizations are read from (ADR-0005) — `store.py.__init__` derives the
    routing home from the account database, not `$HOME`, on purpose. A test pins that the
    two independently-written derivations agree.

    007-P2 review findings (F-SEC-04/F-PR-05, both reviewers independently, upheld by
    finding-verifier): the original version used `identity.read_text()` and treated ANY
    read/parse failure the same as "absent", silently falling back to the path hash. That
    diverges from `project_key_for` on exactly the case it treats as a deliberate refusal
    (`ProjectIdentityError`: "falling back would silently split history") -- a present but
    corrupt/wrong-schema/oversized/symlinked `project.json` was hashed as if it were
    genuinely absent, reporting the pi lane as zero-cost instead of failing loudly. It also
    followed symlinks and could hang indefinitely on a FIFO. This version mirrors
    `_safe_read`'s guards (reject non-regular files and symlinks via `O_NOFOLLOW`, bound
    the read) and raises `_ProjectIdentityError` on every unusable-but-present case,
    exactly where `project_key_for` raises `ProjectIdentityError` -- never a silent hash.
    """
    identity = root / "ai/state/project.json"
    try:
        before = identity.lstat()
    except FileNotFoundError:
        before = None
    except OSError as exc:
        raise _ProjectIdentityError("invalid project identity") from exc
    if before is not None:
        if stat.S_ISLNK(before.st_mode) or not stat.S_ISREG(before.st_mode):
            raise _ProjectIdentityError("invalid project identity")
        try:
            fd = os.open(identity, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0))
            with os.fdopen(fd, "rb") as handle:
                opened = os.fstat(handle.fileno())
                if not stat.S_ISREG(opened.st_mode):
                    raise _ProjectIdentityError("invalid project identity")
                raw = handle.read(_MAX_IDENTITY_BYTES + 1)
        except OSError as exc:
            raise _ProjectIdentityError("invalid project identity") from exc
        if len(raw) > _MAX_IDENTITY_BYTES:
            raise _ProjectIdentityError("invalid project identity")
        try:
            doc = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, ValueError):
            raise _ProjectIdentityError("invalid project identity")
        if (isinstance(doc, dict) and doc.get("schema") == 1
                and _PROJECT_KEY_RE.fullmatch(doc.get("project_key", ""))
                and isinstance(doc.get("created_at"), str)):
            return doc["project_key"]
        raise _ProjectIdentityError("invalid project identity")
    value = unicodedata.normalize("NFC", os.path.realpath(root))
    parent, name = os.path.split(value)
    try:
        swapped = "".join(char.swapcase() for char in name)
        if swapped != name and os.lstat(value).st_ino == os.lstat(os.path.join(parent, swapped)).st_ino:
            value = value.lower()
    except OSError:
        pass
    if sys.platform in {"darwin", "win32"}:
        value = value.lower()
    digest = hashlib.sha256(b"set-agents-project-v1\0" + value.encode("utf-8", "surrogateescape")).hexdigest()[:32]
    return "proj1_" + digest


def collect_pi(report, home, project, since_ms):
    db = home / ".local/state/set-agentes/routing-v2/routing.db"
    if not db.exists():
        return
    conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    try:
        # AC-11 x AC-16: only 'ok' rows have anything usable — 'absent'/'invalid' are all
        # NULL and would otherwise show up as phantom zero-token sessions.
        query = "SELECT actual_model, role, usage_input, usage_output, usage_cache_read, usage_cache_write, usage_reasoning, updated_at FROM dispatches WHERE usage_status='ok'"
        args = ()
        directory = None
        if project:
            directory = str(project)
            try:
                args = (_pi_project_key(Path(project).resolve()),)
            except _ProjectIdentityError:
                # 007-P2 review finding (F-SEC-04/F-PR-05): fail loudly rather than
                # silently reporting the pi lane as zero-cost for an identity file that
                # `project_key_for` itself would refuse to trust.
                print(f"pi lane: invalid project identity at {project} -- skipping", file=sys.stderr)
                return
            query += " AND project_key=?"
        matched = 0
        for model, role, t_in, t_out, t_cr, t_cw, t_re, updated in conn.execute(query, args):
            if since_ms and (updated or 0) < since_ms:
                continue
            matched += 1
            add(report, directory, "pi", model, role, {
                "input": t_in or 0, "output": t_out or 0, "cache_read": t_cr or 0,
                "cache_write": t_cw or 0, "reasoning": t_re or 0, "sessions": 1,
            })
        # 007-P2 review finding (F-PR-04): unlike the other three collectors, `--project`
        # here matches an exact recomputed key, not a path PREFIX (`in_project()`'s
        # `relative_to`) -- a `--project` that is an ancestor or descendant of the real
        # scaffolded root matches nothing and previously vanished with no message. Silence
        # is not acceptable: if this project matched zero rows but the pi lane has activity
        # for OTHER projects, say so instead of looking identical to "pi costs nothing".
        #
        # 007-P2 delta-review finding (N-02): the count below used to have no
        # `project_key` exclusion, so a project whose own rows were simply older than
        # `--since` (nothing to do with the recomputed key) got blamed for "other
        # projects" activity that was actually its own. Excluding this project's key is
        # what makes "other projects" mean what it says; the --since blindness itself is
        # registered as residual debt (`pi-lane-since-window-blind-to-discard-and-total`),
        # not fixed here -- fixing it needs the SQL to see the same clock the Python loop
        # already filters by, which is a bigger change than a delta review repair covers.
        if project and matched == 0 and args:
            total = conn.execute(
                "SELECT COUNT(*) FROM dispatches WHERE usage_status='ok' AND project_key!=?", args
            ).fetchone()[0]
            if total:
                print(f"pi lane: 0 rows matched --project {project}, but {total} 'ok' row(s) exist "
                      "for other projects -- --project must be the exact scaffolded root, not an "
                      "ancestor or descendant of it", file=sys.stderr)
        # 007-P2 review finding (F-PR-03, upheld by finding-verifier): 'absent'/'invalid'
        # rows are correctly excluded from the table above, but excluding them silently
        # is the same blindness AC-11 exists to end, moved one level up into reporting --
        # a mass discard would look identical to zero pi activity. Counted and named here.
        #
        # 007-P2 delta-review finding (N-02 follow-on): without `GROUP BY usage_status`,
        # SQLite's aggregate-without-GROUP-BY rule returns exactly one row -- `(None, 0)`
        # -- even when nothing was discarded, and that single row is truthy, so every
        # plain run printed a nonsensical "excluded 0 None row(s)" warning.
        discard_query = ("SELECT usage_status,COUNT(*) FROM dispatches WHERE usage_status IS NOT NULL "
                          "AND usage_status!='ok'")
        discard_args = ()
        if project and args:
            discard_query += " AND project_key=?"
            discard_args = args
        discard_query += " GROUP BY usage_status"
        discarded = dict(conn.execute(discard_query, discard_args))
        if discarded:
            parts = ", ".join(f"{count} {status}" for status, count in sorted(discarded.items()))
            print(f"pi lane: excluded {parts} row(s) with no usable usage", file=sys.stderr)
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
    collect_pi(report, home, args.project, since_ms)
    render(report, args.md)


if __name__ == "__main__":
    main()
