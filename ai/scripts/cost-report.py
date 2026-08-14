#!/usr/bin/env python3
"""Token-consumption report per project -- TWO sections, named by source, NEVER summed
together (023-senales-de-consumo PKG-B2, AC-04/AC-05): this harness's own dispatch ledger
and each CLI's own native accounting are two independent MEASUREMENTS OF OVERLAPPING SPEND,
never two halves of one total.

Section 1 -- CLI-NATIVE STORES (each CLI's own accounting, entirely independent of whether
the harness dispatched the run at all -- a session started by hand shows up here too):
- OpenCode:    ~/.local/share/opencode/opencode.db  (session table aggregates, per-agent)
- Claude Code: ~/.claude/projects/<enc-cwd>/**/*.jsonl (per-message usage, per-agent)
- Codex:       ~/.codex/state_5.sqlite threads (per-thread aggregate; --deep parses the
               rollout jsonl for the cached/reasoning breakdown)

Section 2 -- HARNESS DISPATCH REGISTRY (this harness's own `dispatches` table,
~/.local/state/set-agentes/routing-v2/routing.db, 023-senales-de-consumo PKG-B1/B2): every
run the ROUTER ITSELF dispatched and closed with usable usage, across EVERY runtime it can
route to -- pi natively, plus any claude-code-lane/opencode-lane redirect PKG-B2 wired onto
the store's flat vocabulary (`routing_core/usage.py`). Every row is still labeled "pi" for
historical reasons this package does not fix (cosmetic, per the package's own context pack)
-- but this section's COVERAGE is every runtime the harness dispatches, not only the pi CLI.
Bounded to spawns the harness itself dispatched through set_agents_spawn.py/
claude_code_spawn.py/opencode_spawn.py -- a session started by hand is invisible here. The
stored project_key is a one-way hash, not invertible to a directory: this section is
attributed to a project only when --project is given (the key is recomputed locally and
matched); otherwise it is reported unattributed rather than guessed.

WHY THESE NEVER SUM (AC-04): a run the harness dispatches through the claude-code or
opencode lane is the SAME spend Section 1 already counts from that CLI's own transcript/
session store -- Section 2 counts it a SECOND time, from the router's own vantage point.
Adding the two sections' totals into one grand total would double-count that spend. Each
section prints only its OWN total; this report never prints one total across sections
(AC-05 -- no total anywhere on this surface without saying which section it came from).

Tokens only — subscription plans have no meaningful dollar-per-token, what matters is quota.

Section 3 -- ESTIMATED REMAINING QUOTA (023-senales-de-consumo PKG-B4, AC-08/AC-09/AC-10,
ADR-0046): reads `usage_rollups` (schema 9, PKG-B3) for the current UTC-calendar-day window
and, per token FIELD, prints what was actually MEASURED (raw sum) plus its COVERAGE
(`usage_<field>_reported_count` of `run_count` runs actually reported that field -- never
averaged over the runs that did not, which would silently treat "did not report" as "reported
zero"). No provider exposes remaining quota (ADR-0046) -- a "restante" line only ever appears
for a FIELD the caller declared with `--budget FIELD=N`, and it is always labeled `ESTIMADO`
with `provider_reported: false` and its `basis`. A field with no declared budget shows only
what was measured, never a guessed remainder (AC-10).

Usage:
  cost-report.py [--project DIR] [--since YYYY-MM-DD] [--md] [--deep] [--home DIR]
                  [--budget FIELD=N ...]
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
import time
import unicodedata
from collections import defaultdict
from pathlib import Path

FIELDS = ("input", "output", "cache_read", "cache_write", "reasoning")
# 023-senales-de-consumo PKG-B3: the same UTC-calendar-day boundary
# `routing_core/store.py`'s `_rollup_usage_in` buckets `usage_rollups.window_start` into.
# Duplicated, not imported (AC-16, see `_pi_project_key`'s docstring for why this module
# never imports repo-local code) -- pinned against the real constant by a test instead.
_DAY_MS = 86400000


def parse_args():
    parser = argparse.ArgumentParser(
        description=__doc__.splitlines()[0],
        epilog="Two sections, never summed (AC-04/AC-05): Section 1 is each CLI's own native "
               "store; Section 2 is this harness's own dispatch registry (every runtime it "
               "dispatched, labeled 'pi' per row for historical reasons -- see the module "
               "docstring). Section 2 coverage: only spawns dispatched through "
               "set_agents_spawn.py/claude_code_spawn.py/opencode_spawn.py; a session started "
               "by hand is invisible there. Without --project it is reported unattributed "
               "(project_key is a one-way hash, never guessed back to a path).",
    )
    parser.add_argument("--project", help="only sessions whose cwd is inside this directory "
                        "(also required to attribute Section 2 to a project)")
    parser.add_argument("--since", help="only sessions updated on/after this date (YYYY-MM-DD)")
    parser.add_argument("--md", action="store_true", help="markdown output")
    parser.add_argument("--deep", action="store_true", help="Codex: parse rollouts for cached/reasoning split")
    parser.add_argument("--home", default=str(Path.home()), help=argparse.SUPPRESS)
    parser.add_argument("--budget", action="append", default=[], metavar="FIELD=N",
                        help="AC-10: declare a quota for one token FIELD (input/output/"
                             "cache_read/cache_write/reasoning) so Section 3 may show a "
                             "\"restante\" for it, always labeled ESTIMADO -- a FIELD with "
                             "no --budget only ever shows what was measured")
    parser.add_argument("--window-start", type=int, default=None, help=argparse.SUPPRESS)
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


# ---------------------------------------------------------------------------------------
# 023-senales-de-consumo PKG-B4 (AC-08/AC-09/AC-10, ADR-0046) -- ESTIMATED remaining quota,
# read from `usage_rollups` (schema 9, PKG-B3). Tokens only, same "what matters is quota"
# doctrine the module docstring already states for Sections 1/2 -- no cost_micros budget.
# ---------------------------------------------------------------------------------------

def parse_budgets(items):
    """`FIELD=N`, FIELD in FIELDS. AC-10 exists so that a "restante" only ever appears for a
    budget the caller EXPLICITLY declared for a real field -- a typo silently ignored would
    make that declaration silently vanish, which is the same silent-invention AC-10
    forbids, just moved into argument parsing. Dies loudly instead.
    """
    budgets = {}
    for item in items:
        field, sep, value = item.partition("=")
        if not sep or field not in FIELDS:
            raise SystemExit(
                f"cost-report.py: --budget {item!r} -- FIELD must be one of "
                f"{', '.join(FIELDS)}, given as FIELD=N")
        try:
            n = int(value)
        except ValueError:
            raise SystemExit(f"cost-report.py: --budget {item!r} -- N must be an integer")
        if n < 0:
            raise SystemExit(f"cost-report.py: --budget {item!r} -- N must be >= 0")
        budgets[field] = n
    return budgets


def window_bounds(now_ms=None):
    """The exact UTC-calendar-day window `usage_rollups.window_start` buckets a close into
    (`routing_core/store.py:_rollup_usage_in`) -- `_DAY_MS` above is pinned against that
    module's own constant by a test, so this cannot silently drift from what a row here
    was actually summed under.
    """
    if now_ms is None:
        now_ms = int(time.time() * 1000)
    start = (now_ms // _DAY_MS) * _DAY_MS
    return start, start + _DAY_MS


def window_label(start_ms, end_ms):
    """AC-08: the window NAMED BY ITS DEFINITION -- the exact range, never a relative
    phrase like "last week"."""
    start = dt.datetime.fromtimestamp(start_ms / 1000, tz=dt.timezone.utc).isoformat()
    end = dt.datetime.fromtimestamp(end_ms / 1000, tz=dt.timezone.utc).isoformat()
    return f"{start} to {end} (UTC calendar day, usage_rollups.window_start)"


def collect_estimate(home, project, window_start_ms):
    """Reads `usage_rollups` for exactly ONE UTC-day window and returns, per token FIELD,
    the raw measured sum and how many of the window's runs actually REPORTED that field --
    the coverage pair the schema itself already carries (023-senales-de-consumo PKG-B3),
    never averaged over the runs that did not report (the trap this package's context pack
    names explicitly: 12-of-40 coverage presented as if the other 28 reported zero).

    Returns `None` (with a stderr message, same discipline as `collect_pi`) when the store
    is absent, `usage_rollups` does not exist yet (a database still on an older schema), or
    `--project` names an identity this module cannot trust -- never a silent zero.
    """
    db = home / ".local/state/set-agentes/routing-v2/routing.db"
    if not db.exists():
        return None
    conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    try:
        tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if "usage_rollups" not in tables:
            print("estimate: routing.db has no usage_rollups table yet (older schema) -- skipping",
                  file=sys.stderr)
            return None
        args = [window_start_ms]
        query = ("SELECT COALESCE(SUM(run_count),0), " + ", ".join(
            f"COALESCE(SUM(usage_{field}_sum),0), COALESCE(SUM(usage_{field}_reported_count),0)"
            for field in FIELDS
        ) + " FROM usage_rollups WHERE window_start=?")
        if project:
            try:
                args.append(_pi_project_key(Path(project).resolve()))
            except _ProjectIdentityError:
                print(f"estimate: invalid project identity at {project} -- skipping", file=sys.stderr)
                return None
            query += " AND project_key=?"
        row = conn.execute(query, args).fetchone()
    finally:
        conn.close()
    run_count = row[0]
    fields = {}
    for i, field in enumerate(FIELDS):
        fields[field] = {"sum": row[1 + i * 2], "reported": row[2 + i * 2]}
    return {"run_count": run_count, "fields": fields}


def format_metric_estimate(field, measured, run_count, window_label_text, budget=None):
    """AC-08/AC-09: the ONLY place in this module that ever writes a "restante" line --
    pinned by `test_cost_report_restante_has_exactly_one_render_site` (counts this exact
    marker's occurrences in this file's source), so a future call site that prints its own
    ad hoc "restante" without the four required elements below fails the gate the moment it
    is added, not the next time someone happens to notice.

    AC-10: `budget` is `None` for every field the caller did not declare with `--budget` --
    and then this function NEVER writes a "restante" line at all, only "consumido en la
    ventana" (the measured sum), because `budget - consumed` needs a budget or it is
    invented, and this harness does not invent.
    """
    consumed = measured["sum"]
    reported = measured["reported"]
    coverage = f"{reported}/{run_count} runs reportaron {field} en esta ventana"
    lines = [
        f"{field}: consumido en la ventana = {consumed} (medido, no proyectado)",
        f"  ventana: {window_label_text}",
        f"  cobertura: {coverage}",
    ]
    if budget is not None:
        remaining = budget - consumed
        lines.append(
            f"  restante estimado: {remaining} -- ESTIMADO, provider_reported: false, "
            f"basis: presupuesto declarado ({budget}) menos {field} consumido y medido en "
            f"la ventana ({consumed}); cobertura {coverage}; nunca proyectado sobre los "
            f"runs que no reportaron"
        )
    return "\n".join(lines)


_ESTIMATE_DISCLAIMER = (
    "No provider exposes remaining quota (measured -- the permitted commands answer "
    "authenticated yes/no and which models list, nothing about quota). Every \"restante\" "
    "line above is an ESTIMATE computed from this harness's OWN measured consumption "
    "against a budget YOU declared with --budget FIELD=N -- never data the provider "
    "reported (ADR-0046). A field with no --budget shows only what was measured, never a "
    "guessed remainder (AC-10)."
)


def render_estimate(estimate, md, budgets, window_label_text):
    heading = f"Section 3 -- ESTIMADO (source: routing.db usage_rollups, window {window_label_text})"
    if md:
        print(f"## {heading}")
    else:
        print(heading)
        print("=" * len(heading))
    if estimate is None:
        print("No usage_rollups data matched.")
        print()
        return
    for field in FIELDS:
        print(format_metric_estimate(field, estimate["fields"][field], estimate["run_count"],
                                      window_label_text, budgets.get(field)))
    print()
    print(_ESTIMATE_DISCLAIMER)
    print()


def fmt(n):
    if n >= 10**9:
        return f"{n / 10**9:.1f}G"
    if n >= 10**6:
        return f"{n / 10**6:.1f}M"
    if n >= 10**3:
        return f"{n / 10**3:.1f}k"
    return str(n)


def render(report, md, *, title, source):
    """AC-04/AC-05: `title`/`source` are printed WITH the table, never only in this
    module's docstring -- a reader looking at one call's output alone still sees which of
    the two sections it is and that the `TOTAL` row is scoped to THIS section only. Two
    separate calls (`main`, below) are the only way this module ever renders a total --
    there is no code path that sums `report` dicts from different sections together."""
    heading = f"{title} (source: {source})"
    if md:
        print(f"## {heading}")
    else:
        print(heading)
        print("=" * len(heading))
    if not report:
        print("No sessions matched.")
        print()
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
    # AC-05: the footer literally says "this section only" -- a total copy-pasted out of
    # context (e.g. into a chat message) still carries its own scope with it.
    footer = (f"TOTAL ({title}, this section only)", "", "", "", str(totals["sessions"]),
             *(fmt(totals[field]) for field in FIELDS), fmt(grand))
    if md:
        print("| " + " | ".join(header) + " |")
        print("|" + "---|" * len(header))
        for row in rows + [footer]:
            print("| " + " | ".join(row) + " |")
    else:
        widths = [max(len(str(row[i])) for row in [header, footer, *rows]) for i in range(len(header))]
        for row in [header, *rows, footer]:
            print("  ".join(str(cell).ljust(width) for cell, width in zip(row, widths)))
    print()


# AC-04: two sections, named by their own source, that this module never sums together --
# see the module docstring's "WHY THESE NEVER SUM" paragraph for the double-count risk this
# split exists to prevent.
_SECTION_1_TITLE = "Section 1 -- CLI-native stores"
_SECTION_1_SOURCE = "opencode.db / .claude/projects transcripts / codex rollouts (each CLI's own accounting)"
_SECTION_2_TITLE = "Section 2 -- harness dispatch registry"
_SECTION_2_SOURCE = "routing.db `dispatches` table (this harness's own record of what IT dispatched, every runtime)"
_NEVER_SUM_DISCLAIMER = (
    "These two sections measure OVERLAPPING spend from different vantage points -- a run this "
    "harness dispatches through the claude-code or opencode lane is counted in BOTH sections "
    "above (AC-04, 023-senales-de-consumo PKG-B2). Do not add the two sections' TOTAL rows "
    "together; each section's own total is the only total this report ever prints (AC-05)."
)


def main():
    args = parse_args()
    home = Path(args.home)
    since_ms = since_epoch_ms(args.since)
    # Validated FIRST, before any output: a malformed --budget should never let this run
    # print two whole sections and then die -- fail loudly, up front, same discipline
    # `parse_budgets` itself already documents.
    budgets = parse_budgets(args.budget)

    cli_native = defaultdict(new_bucket)
    collect_opencode(cli_native, home, args.project, since_ms)
    collect_claude(cli_native, home, args.project, since_ms)
    collect_codex(cli_native, home, args.project, since_ms, args.deep)

    harness_registry = defaultdict(new_bucket)
    collect_pi(harness_registry, home, args.project, since_ms)

    render(cli_native, args.md, title=_SECTION_1_TITLE, source=_SECTION_1_SOURCE)
    render(harness_registry, args.md, title=_SECTION_2_TITLE, source=_SECTION_2_SOURCE)
    print(_NEVER_SUM_DISCLAIMER)
    print()

    # 023-senales-de-consumo PKG-B4 (AC-08/AC-09/AC-10): a THIRD, separate surface -- never
    # folded into the "two sections, never summed" disclaimer above, because Section 3 is
    # not a third measurement of the same overlapping spend, it is an ESTIMATE derived from
    # Section 2's own store (`usage_rollups`), always labeled as such.
    window_start_ms, window_end_ms = window_bounds(args.window_start)
    label = window_label(window_start_ms, window_end_ms)
    estimate = collect_estimate(home, args.project, window_start_ms)
    render_estimate(estimate, args.md, budgets, label)


if __name__ == "__main__":
    main()
