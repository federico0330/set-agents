#!/usr/bin/env python3
"""set-agents: unified console app for the SET-AGENTS harness (gentle-ai style).

A TTY menu plus a scriptable CLI over the same primitives: install/repair
(install.sh), self-update (git pull --ff-only + managed reinstall), model
routing (setup-models.sh), and — in later sections — the optional tools
catalog, MCP servers, and Claude Code plugins.
"""

import argparse
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import tomllib
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import models_config
import routing
import set_agents_spawn

# SET_AGENTS_ROOT/SET_AGENTS_STATE/SET_AGENTS_ROUTING_TEST_ROOT are test seams; real runs
# never set them. routing_core itself never reads any of them (ADR-0006: the routing store's
# production root is fixed, derived from the account database, never from the environment) —
# this indirection lives entirely here, in the CLI composition layer (F07).
ROOT = Path(os.environ.get("SET_AGENTS_ROOT") or Path(__file__).resolve().parents[2])
STATE_DIR = Path(os.environ.get("SET_AGENTS_STATE") or Path.home() / ".local/state/set-agentes")
ROUTING_TEST_ROOT = os.environ.get("SET_AGENTS_ROUTING_TEST_ROOT")
APP_CONFIG = STATE_DIR / "config.toml"
MANAGED_MCP = models_config.MANAGED_MCP
HARNESS_CLIS = ("opencode", "claude", "codex")


def _routing_store():
    """F07: the one seam a hermetic CLI test uses to drive decide/dispatched/terminal/abandoned
    against a temp root. Never set by real runs (see the module-level seam note above)."""
    return routing.RoutingStore._for_tests(Path(ROUTING_TEST_ROOT)) if ROUTING_TEST_ROOT else routing.RoutingStore()


def routing_catalog(simulation=False):
    """Compose trusted v2 inputs; callers never supply a catalog or route ID."""
    config = models_config.load_config(ROOT / "models.toml")
    roster = models_config.load_roster(ROOT / "roles.tsv")
    # No optimistic defaults: each real invocation gets a fresh exact probe.
    return routing.compose(config, roster, simulate=simulation, store=None if simulation else _routing_store()), config


def _routing_output(payload, human):
    if not human:
        print(json.dumps(payload, sort_keys=True))
        return
    print(f"{payload['command']}: {'OK' if payload['ok'] else 'NO DISPONIBLE'}", file=sys.stderr)
    for key, value in payload["data"].items() if isinstance(payload["data"], dict) else []:
        print(f"{key}: {value}", file=sys.stderr)
    if payload["reason_codes"]: print("reason_codes: " + ", ".join(payload["reason_codes"]), file=sys.stderr)


def cmd_route_explain(task_class, human=False):
    if task_class not in routing.TASK_CLASSES:
        _routing_output(routing.cli_envelope(False, "route-explain", {}, (), ("TASK_CLASS_INVALID",)), human); return 2
    try:
        service, _config = routing_catalog(simulation=True)
        role = "architect" if task_class in routing.CRITICAL else ("debugger" if task_class == "incident" else "product-analyst")
        runtime = "codex" if task_class in routing.CRITICAL else "claude-code"
        request = routing.TaskRequest(role=role, operation="inspection" if task_class == "inspection" else "change", task_class=task_class, selected_runtime=runtime)
        facts = service._observe_for_invocation(role=role, operation=request.operation, task_class=task_class,
            read_write="read" if task_class == "inspection" else "write", write_started=False,
            risk="high" if task_class in routing.CRITICAL else "low", criticality=task_class if task_class in routing.CRITICAL else "",
            affected_surfaces=(), required_tools=("read",), context_required=True, context_present=True,
            critical_coverage=True, selected_runtime=runtime)
        decision = service.route(request, facts)
        # Explain is a successful simulation even when execution would be unavailable.
        _routing_output(routing.cli_envelope(True, "route-explain", decision.to_dict(), (), decision.reason_codes), human)
        return 0
    except models_config.ModelsError:
        _routing_output(routing.cli_envelope(False, "route-explain", {}, (), ("ROUTING_INPUT_INVALID",)), human); return 2
    except (routing.RoutingError, OSError):
        _routing_output(routing.cli_envelope(False, "route-explain", {}, (), ("ROUTING_UNAVAILABLE",)), human); return 1


def cmd_routing_report(human=False):
    try:
        report = _routing_store().report()
    except (OSError, routing.RoutingError):
        report = {"retained_events": 0, "p50_ms": None, "p90_ms": None, "reason_codes": ["ROUTING_UNAVAILABLE"]}
    reasons = tuple(report.get("reason_codes", ()))
    warnings = routing.legacy_warnings(STATE_DIR)
    _routing_output(routing.cli_envelope(not reasons, "routing-report", report, warnings, reasons), human)
    return 1 if reasons else 0


_RUN_ID = re.compile(r"^run1_[0-9a-f]{32}$")


def _role_class_of(row):
    if row["capability"] == "code-rw": return "writer"
    if row["capability"] == "review-ro" and row["duty"] in {"audit", "judge"}: return "review"
    return "other"


# F01: the ONLY two "non-executable but still ok=true" shapes a decision can take — a
# non-executable decision for a non-writer, non-review role class, and the explicit,
# doctrine-named REVIEW_IDENTITY_UNVERIFIED reviewer report. Every other non-executable
# decision (FACTS_INCOMPLETE, NO_ELIGIBLE_ROUTE, REVIEW_IDENTITY_INVALID,
# PROVIDER_UNAUTHENTICATED, REVIEWER_INDEPENDENCE_UNAVAILABLE, AUTHORIZATION_INVALID,
# AUTHORIZATION_REPLAY, CATALOG_INVALID, STATE_CONFLICT, ROUTING_UNAVAILABLE, ...) is a
# real failure: ok=false, exit 1. Centralized so P3's Pi lane inherits the same table.
_DECIDE_OK_NON_EXECUTABLE_REASONS = ((), ("REVIEW_IDENTITY_UNVERIFIED",))


def _decide_status(decision):
    """(ok, exit_code) for a `route-decide` RouteDecision — the reason->exit table (F01)."""
    if decision.execution_enabled or decision.reason_codes in _DECIDE_OK_NON_EXECUTABLE_REASONS:
        return True, 0
    return False, 1


_SAFE_STATE_ID = re.compile(r"^[A-Za-z0-9._-]+$")
# F03: a feature phase or package status this terminal never has an "active" context pack —
# naming it explicitly can never flip CONTEXT_MISSING, and it is never chosen by default
# resolution either.
_TERMINAL_FEATURE_PHASES = {"DONE", "BLOCKED", None}
_TERMINAL_PACKAGE_STATUS = {"accepted", "done", "blocked", "cancelled"}


def _load_feature_doc(path):
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return doc if isinstance(doc, dict) else None


def _validate_context_pack_path(pack):
    """SEC-A02: a foreign/malformed feature-state.json must never crash route-decide nor
    escape the repo. Non-str, empty, absolute, or traversal-outside-ROOT all degrade to 'no
    pack' — never a bare `ROOT / pack` (an absolute right-hand side silently DISCARDS ROOT
    under pathlib's own semantics, which would let a crafted state file probe arbitrary
    filesystem paths)."""
    if not isinstance(pack, str) or not pack or os.path.isabs(pack):
        return None
    root = ROOT.resolve()
    candidate = (root / pack).resolve()
    try:
        if os.path.commonpath([str(candidate), str(root)]) != str(root):
            return None
    except ValueError:
        return None
    return candidate


def _package_context_ok(doc, package_id):
    """Existence AND freshness (F03b): a pack older than the package's own last recorded
    mutation (falling back to the feature doc's) is stale and reports False, conservatively."""
    for package in doc.get("packages", []):
        if package.get("package_id") != package_id:
            continue
        path = _validate_context_pack_path(package.get("context_pack"))
        if path is None:
            return False
        try:
            st = path.lstat()
        except OSError:
            return False
        if stat.S_ISLNK(st.st_mode) or not stat.S_ISREG(st.st_mode):
            return False
        reference = package.get("updated_at") or doc.get("updated_at")
        if isinstance(reference, str):
            try:
                ref_epoch = datetime.fromisoformat(reference).timestamp()
            except ValueError:
                ref_epoch = None
            if ref_epoch is not None and st.st_mtime < ref_epoch:
                return False  # stale: the pack predates the package's last recorded mutation
        return True
    return False


def _resolve_context_pack(feature_id, package_id):
    """AM-1/F03: context flags derive from the active package's context pack — EXISTENCE AND
    FRESHNESS, never presence alone. Returns `(context_ok, feature_id, package_id)`:
    `context_ok` is True/False once a package is identified (pack good, or missing/stale/the
    feature or package is terminal), or None when the package itself could not even be
    resolved (CONTEXT_UNRESOLVED at the caller — distinct from a resolved-but-missing pack,
    contract 004 AC-03's "no resolvable package ⇒ context flags false" applies to the
    EXPLICIT-id case; the ambiguous DEFAULT case is a distinct signal).
    """
    state_dir = ROOT / "ai/state/features"
    if feature_id:
        if not _SAFE_STATE_ID.fullmatch(feature_id):
            return False, feature_id, package_id
        # N10: with an explicit feature_id, open ONLY that one file — never glob the directory.
        doc = _load_feature_doc(state_dir / f"{feature_id}.json")
        if doc is None or doc.get("feature_id") != feature_id:
            return False, feature_id, package_id
        target = package_id if (package_id and _SAFE_STATE_ID.fullmatch(package_id)) else doc.get("current_package_id")
        # F03a: naming a BLOCKED/DONE feature can never flip CONTEXT_MISSING — the same
        # non-terminal filter used by default resolution applies here too. `target` is still
        # resolved above so the audit payload always shows the effective package_id.
        if doc.get("phase") in _TERMINAL_FEATURE_PHASES:
            return False, feature_id, target
        return _package_context_ok(doc, target), feature_id, target
    # No feature_id: resolve the single feature whose CURRENT package is actively executing
    # (package status non-terminal) — "exactly one non-terminal FEATURE" under-resolves
    # whenever more than one feature is mid-flight (e.g. one sitting at PACKAGE_ACCEPTED for
    # its current package while another is still mid-repair).
    candidates = []
    try:
        for candidate_path in sorted(state_dir.glob("*.json")):
            doc = _load_feature_doc(candidate_path)
            if doc is None or doc.get("phase") in _TERMINAL_FEATURE_PHASES:
                continue
            current = doc.get("current_package_id")
            package = next((p for p in doc.get("packages", []) if p.get("package_id") == current), None)
            if package is not None and package.get("status") not in _TERMINAL_PACKAGE_STATUS:
                candidates.append((doc, current))
    except OSError:
        return None, None, None
    if len(candidates) != 1:
        return None, None, None  # CONTEXT_UNRESOLVED at the caller, distinct from NO_ELIGIBLE_ROUTE
    doc, target = candidates[0]
    return _package_context_ok(doc, target), doc.get("feature_id"), target


def cmd_route_decide(source, human=False, fresh=False):
    allowed = {"role", "task_class", "risk", "review_of_run_id", "selected_runtime", "feature_id", "package_id"}
    try:
        raw = sys.stdin.read() if source == "-" else Path(source).read_text(encoding="utf-8")
        doc = json.loads(raw)
        if not isinstance(doc, dict) or set(doc) - allowed: raise ValueError
        role, task_class = doc.get("role"), doc.get("task_class")
        if not isinstance(role, str) or task_class not in routing.TASK_CLASSES: raise ValueError
        req_risk = doc.get("risk", "low"); runtime = doc.get("selected_runtime", "opencode")
        review_of = doc.get("review_of_run_id")
        feature_id = doc.get("feature_id"); package_id = doc.get("package_id")
        for value in (req_risk, runtime) + tuple(v for v in (review_of, feature_id, package_id) if v is not None):
            if not isinstance(value, str) or not value: raise ValueError
        # F01: a descriptor risk/runtime outside the closed enum is a PARSE failure (exit 2
        # ROUTING_INPUT_INVALID) — it never reaches the service to degrade into FACTS_INCOMPLETE.
        if req_risk not in routing.RISK_ORDER or runtime not in routing.SELECTED_RUNTIMES: raise ValueError
    except (OSError, ValueError):
        _routing_output(routing.cli_envelope(False, "route-decide", {}, (), ("ROUTING_INPUT_INVALID",)), human); return 2
    try:
        config = models_config.load_config(ROOT / "models.toml")
        roster = models_config.load_roster(ROOT / "roles.tsv")
        row = next((item for item in roster if item["role"] == role), None)
        if row is None:
            _routing_output(routing.cli_envelope(False, "route-decide", {}, (), ("FACTS_INCOMPLETE",)), human); return 1
        role_class = _role_class_of(row)
        # AM-1 (ADR-0006): capability decides write access and tools; task_class decides criticality
        # and the base risk; the descriptor risk can only RAISE (combined in the service); context
        # flags derive from the active package's context pack.
        writer = role_class == "writer"
        criticality = task_class if task_class in routing.CRITICAL else ""
        base_risk = "high" if (criticality or task_class == "incident") else "low"
        needs_context = bool(criticality) or base_risk == "high" or req_risk == "high"
        context_ok, resolved_feature, resolved_package = _resolve_context_pack(feature_id, package_id)
        if needs_context and context_ok is None:
            # F03d: the harness itself could not narrow the default resolution to exactly one
            # actively-executing package — distinct from NO_ELIGIBLE_ROUTE (a real catalog
            # exclusion), and distinct from a resolved-but-missing pack (plain CONTEXT_MISSING).
            data = {"feature_id": resolved_feature, "package_id": resolved_package, "context_ok": None}
            _routing_output(routing.cli_envelope(False, "route-decide", data, (), ("CONTEXT_UNRESOLVED",)), human)
            return 1
        context_flag = bool(context_ok)
        unverified_review = role_class == "review" and not review_of
        simulate = not writer and not (role_class == "review" and review_of)
        service = routing.compose(config, roster, simulate=simulate, fresh_probes=fresh,
                                  store=None if simulate else _routing_store())
        request = routing.TaskRequest(role=role, operation="inspection" if task_class == "inspection" else "change",
                                      task_class=task_class, risk=req_risk, selected_runtime=runtime)
        facts = service._observe_for_invocation(role=role, operation=request.operation, task_class=task_class,
            read_write="write" if writer else "read", write_started=False,
            risk=base_risk, criticality=criticality, affected_surfaces=(),
            required_tools=("read", "shell", "write") if writer else ("read",),
            context_required=needs_context,
            context_present=context_flag, critical_coverage=context_flag, selected_runtime=runtime)
        decision = service.route(request, facts, review_of, unverified_review=unverified_review)
        tier = next((r.tier for r in service.snapshot.routes if r.route_id == decision.route_id), None)
        data = decision.to_dict(); data["tier"] = tier; data["role_class"] = role_class
        # F03: the effective (feature_id, package_id, context_ok) is always in the envelope,
        # even when context wasn't needed, for audit.
        data["feature_id"] = resolved_feature; data["package_id"] = resolved_package; data["context_ok"] = context_flag
        ok, exit_code = _decide_status(decision)
        _routing_output(routing.cli_envelope(ok, "route-decide", data, (), decision.reason_codes), human)
        return exit_code
    except models_config.ModelsError:
        _routing_output(routing.cli_envelope(False, "route-decide", {}, (), ("ROUTING_INPUT_INVALID",)), human); return 2
    # SEC-A02: any unvalidated internal edge (a malformed feature-state.json field, an
    # out-of-range value reaching the store) degrades to ROUTING_UNAVAILABLE — never an
    # uncaught traceback breaking the schema-2 envelope / one-JSON-line contract.
    except (routing.RoutingError, OSError, TypeError, ValueError, OverflowError):
        _routing_output(routing.cli_envelope(False, "route-decide", {}, (), ("ROUTING_UNAVAILABLE",)), human); return 1


def _lifecycle_command(name, run_id, action, human):
    if not isinstance(run_id, str) or not _RUN_ID.fullmatch(run_id):
        _routing_output(routing.cli_envelope(False, name, {}, (), ("ROUTING_INPUT_INVALID",)), human); return 2
    try:
        result = action(_routing_store())
        _routing_output(routing.cli_envelope(True, name, result, (), ()), human); return 0
    except routing.RoutingError as exc:
        _routing_output(routing.cli_envelope(False, name, {}, (), (str(exc),)), human); return 1
    except (OSError, TypeError, ValueError, OverflowError):
        _routing_output(routing.cli_envelope(False, name, {}, (), ("ROUTING_UNAVAILABLE",)), human); return 1


def cmd_route_dispatched(run_id, human=False):
    def action(store):
        store.mark_dispatched(run_id); return {"run_id": run_id, "state": "dispatched"}
    return _lifecycle_command("route-dispatched", run_id, action, human)


_LATENCY_MAX = 2**31 - 1


def cmd_route_terminal(run_id, outcome, latency_ms, human=False):
    if outcome not in {"success", "failure"}:
        _routing_output(routing.cli_envelope(False, "route-terminal", {}, (), ("ROUTING_INPUT_INVALID",)), human); return 2
    # SEC-A02: bound --latency-ms at the CLI, before it ever reaches the store — an
    # out-of-range value (overflow) or a negative one (would decrement rollup sums) is a
    # PARSE failure, not a runtime one.
    if latency_ms is not None and (isinstance(latency_ms, bool) or not isinstance(latency_ms, int)
                                   or not (0 <= latency_ms <= _LATENCY_MAX)):
        _routing_output(routing.cli_envelope(False, "route-terminal", {}, (), ("ROUTING_INPUT_INVALID",)), human); return 2
    def action(store):
        # F02: ONE transaction reads the state and transitions to exactly the right
        # destination (dispatched->terminal, authorized+failure->abandoned, anything else a
        # single rejected/STATE_CONFLICT) — never a try-terminal-then-except-abandon pair of
        # independent transactions, which left a spurious rejected row behind a successful
        # abandon and wrote two rejected rows for an unclosable run.
        state = store.close_run(run_id, outcome, latency_ms)
        return {"run_id": run_id, "state": state}
    return _lifecycle_command("route-terminal", run_id, action, human)


def cmd_routing_open_runs(human=False):
    try:
        data = {"open_runs": _routing_store().open_runs()}
        _routing_output(routing.cli_envelope(True, "routing-open-runs", data, (), ()), human); return 0
    except (routing.RoutingError, OSError):
        _routing_output(routing.cli_envelope(False, "routing-open-runs", {}, (), ("ROUTING_UNAVAILABLE",)), human); return 1


def cmd_routing_recent_writers(human=False):
    try:
        data = {"recent_writers": _routing_store().recent_writers()}
        _routing_output(routing.cli_envelope(True, "routing-recent-writers", data, (), ()), human); return 0
    except (routing.RoutingError, OSError):
        _routing_output(routing.cli_envelope(False, "routing-recent-writers", {}, (), ("ROUTING_UNAVAILABLE",)), human); return 1


def cmd_doctor(harness, human=False):
    """AC-09: `--doctor --harness pi` — a redacted schema-2 envelope (pinned version,
    auth.json KEY-SET, `pi --list-models` OK/FAIL). Never prints credential contents.
    Only `--harness pi` is specified by this package; any other/absent harness is a
    parse-time input error, not a routing decision."""
    if harness != "pi":
        _routing_output(routing.cli_envelope(False, "doctor", {}, (), ("DOCTOR_HARNESS_UNSUPPORTED",)), human); return 2
    report = set_agents_spawn.doctor()
    ok = bool(report.get("doctor_green"))
    _routing_output(routing.cli_envelope(ok, "doctor", report, (), () if ok else ("PI_DOCTOR_NOT_GREEN",)), human)
    return 0 if ok else 1


def use_color():
    return sys.stdout.isatty() and not os.environ.get("NO_COLOR") and os.environ.get("TERM") != "dumb"


def color(text, code):
    return f"\033[{code}m{text}\033[0m" if use_color() else text


def bold(text):
    return color(text, "1")


def dim(text):
    return color(text, "2")


# --------------------------------------------------------------------- banner

# Two-row half-block wordmark; per-character truecolor gradient cyan -> violet.
WORDMARK = (
    "█▀▀ █▀▀ ▀█▀ ▄▄ ▄▀▄ █▀▀ █▀▀ █▄ █ ▀█▀ █▀▀",
    "▄▄█ █▄▄  █     █▀█ █▄█ █▄▄ █ ▀█  █  ▄▄█",
)
GRADIENT = ((0, 229, 255), (167, 80, 255))
# The app's motif: three agent nodes (one per harness) wired into one system.
NODES = (("opencode", "38;2;77;208;225"), ("claude", "38;2;217;119;87"), ("codex", "38;2;120;220;120"))


def _lerp(t):
    (r1, g1, b1), (r2, g2, b2) = GRADIENT
    return (round(r1 + (r2 - r1) * t), round(g1 + (g2 - g1) * t), round(b1 + (b2 - b1) * t))


def _gradient_row(row, offset):
    width = max(1, len(row) - 1)
    out = []
    for index, char in enumerate(row):
        if char == " ":
            out.append(char)
            continue
        r, g, b = _lerp(min(1.0, (index + offset) / width))
        out.append(f"\033[38;2;{r};{g};{b}m{char}")
    return "".join(out) + "\033[0m"


def banner():
    if not use_color():
        print("SET-AGENTS — opencode · claude · codex")
        return
    node_rows = [
        f"  \033[{code}m●\033[0m \033[2m{name:<8}\033[0m" for name, code in NODES
    ]
    wire = ["─┐", "─┤", "─┘"]
    rows = [
        f"{node_rows[0]}\033[2m{wire[0]}\033[0m   {_gradient_row(WORDMARK[0], 0)}",
        f"{node_rows[1]}\033[2m{wire[1]}\033[0m   {_gradient_row(WORDMARK[1], 6)}",
        f"{node_rows[2]}\033[2m{wire[2]}\033[0m   " + dim("un comando · tres agentes · cero drift"),
    ]
    print("\n".join(rows))


def platform_label():
    if sys.platform == "darwin":
        return "macOS"
    try:
        if "microsoft" in Path("/proc/version").read_text().lower():
            return "WSL"
    except OSError:
        pass
    return "Linux"


def first_run():
    return not APP_CONFIG.exists()


# ---------------------------------------------------------------- app config

def app_config():
    try:
        return tomllib.loads(APP_CONFIG.read_text())
    except (OSError, tomllib.TOMLDecodeError):
        return {}


def auto_update_enabled():
    return app_config().get("auto_update", True)


def set_auto_update(enabled):
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    config = {**app_config(), "auto_update": enabled}
    lines = [
        f"{key} = {'true' if value else 'false'}" if isinstance(value, bool) else f"{key} = {json.dumps(value)}"
        for key, value in sorted(config.items())
    ]
    APP_CONFIG.write_text("\n".join(lines) + "\n")
    print(f"AUTO_UPDATE={'on' if enabled else 'off'}")


# ----------------------------------------------------------------------- git

def git(*args, timeout=None):
    return subprocess.run(
        ["git", "-C", str(ROOT), *args],
        capture_output=True, text=True, timeout=timeout, check=False,
        # Never let git throw an interactive credential prompt at a captured TTY.
        env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
    )


def fetch(timeout=10):
    try:
        return git("fetch", "--quiet", timeout=timeout).returncode == 0
    except subprocess.TimeoutExpired:
        return False


def short_sha():
    result = git("rev-parse", "--short", "HEAD")
    return result.stdout.strip() if result.returncode == 0 else "?"


def rev_count(spec):
    result = git("rev-list", "--count", spec)
    return int(result.stdout.strip()) if result.returncode == 0 else None


def tree_clean():
    return git("status", "--porcelain").stdout.strip() == ""


# -------------------------------------------------------------------- status

def drift_state():
    script = ROOT / "ai/scripts/check-drift.sh"
    if not script.is_file():
        return "unknown"
    result = subprocess.run([str(script), "--quiet"], capture_output=True, text=True, check=False)
    return {0: "ok", 1: "stale"}.get(result.returncode, "unknown")


def auth_state(cli):
    if not shutil.which(cli):
        return "missing"
    if cli == "opencode":
        result = subprocess.run(["opencode", "auth", "list"], capture_output=True, text=True, check=False)
        return "ok" if result.returncode == 0 and result.stdout.strip() else "needed"
    if cli == "codex":
        result = subprocess.run(["codex", "login", "status"], capture_output=True, check=False)
        return "ok" if result.returncode == 0 else "needed"
    # claude: no stable status command; same heuristic install.sh uses.
    credentials = Path.home() / ".claude/.credentials.json"
    return "ok" if credentials.exists() and credentials.stat().st_size > 0 else "needed"


def version_of(cli):
    try:
        out = subprocess.run([cli, "--version"], capture_output=True, text=True, timeout=15, check=False).stdout
        return out.strip().splitlines()[0] if out.strip() else "?"
    except (OSError, subprocess.TimeoutExpired):
        return "?"


def cmd_status(human=False):
    behind = rev_count("HEAD..origin/main")
    drift = drift_state()
    print(
        f"APP_STATUS sha={short_sha()} drift={drift} "
        f"update={behind if behind is not None else '?'} "  # cached; --check-update fetches
        f"auto_update={'on' if auto_update_enabled() else 'off'}"
    )
    if not human:
        return 0
    print()
    print(f"{'CLI':<10} {'VERSIÓN':<28} AUTH")
    for cli in HARNESS_CLIS:
        installed = shutil.which(cli)
        version = version_of(cli) if installed else "FALTA"
        print(f"{cli:<10} {version:<28} {auth_state(cli) if installed else '-'}")
    if drift == "stale":
        print("\ndrift: la instalación quedó atrás del repo → opción [1] o ./build.sh --install")
    return 0


# -------------------------------------------------------------------- update

def cmd_check_update():
    online = fetch()
    behind = rev_count("HEAD..origin/main")
    suffix = "" if online else " (sin red: valor cacheado)"
    print(f"UPDATE_AVAILABLE={behind if behind is not None else '?'}{suffix}")
    return 0 if behind is not None else 2


def cmd_update(yes=False, no_install=False, assume_fetched=False):
    if not tree_clean():
        print("UPDATE_BLOCKED: hay cambios locales sin commitear — resolvelos y reintentá.")
        return 1
    if not assume_fetched:
        fetch()
    behind = rev_count("HEAD..origin/main")
    ahead = rev_count("origin/main..HEAD")
    if behind is None:
        print("UPDATE_BLOCKED: no pude determinar el estado remoto.")
        return 2
    if behind == 0:
        print("UPDATE_AVAILABLE=0")
        return 0
    if ahead:
        print(f"UPDATE_BLOCKED: historia divergida ({ahead} commits locales) — resolvé a mano.")
        return 1
    old = short_sha()
    print(f"Novedades ({behind} commits):")
    print(git("log", "--oneline", "HEAD..origin/main").stdout.rstrip())
    try:
        pull = git("pull", "--ff-only", timeout=180)
    except subprocess.TimeoutExpired:
        print("UPDATE_BLOCKED: git pull colgado (¿red o credenciales? probá `gh auth status`).")
        return 1
    if pull.returncode != 0:
        print(f"UPDATE_BLOCKED: git pull falló:\n{pull.stderr.strip()}")
        return 1
    print(f"UPDATE_APPLIED {old}..{short_sha()}")
    if no_install:
        return 0
    install = [str(ROOT / "build.sh"), "--install"]
    if yes:
        install.append("--yes")
    # No capture: build.sh shows the managed diff and asks on the caller's TTY.
    return subprocess.run(install, check=False).returncode


def launch_update_check():
    """Menu-open behavior: auto-update with notice, or just a badge."""
    online = fetch(timeout=6)
    behind = rev_count("HEAD..origin/main")
    if not online and behind is None:
        return "sin red o sin acceso (probá `gh auth status`)"
    if not behind:
        return "al día"
    if not auto_update_enabled():
        return f"{behind} commits nuevos (auto-update off → opción [2])"
    if not tree_clean() or rev_count("origin/main..HEAD"):
        return f"{behind} commits nuevos (repo local con cambios → opción [2])"
    print(bold(f"Actualización disponible ({behind} commits) — aplicando automáticamente…"))
    cmd_update(yes=True, assume_fetched=True)
    return "al día (recién actualizado)"


# --------------------------------------------------------------------- tools

def load_catalog():
    return tomllib.loads((ROOT / "tools.toml").read_text())


def platform_pm():
    if sys.platform == "darwin":
        return "brew" if shutil.which("brew") else None
    for pm, binary in (("pacman", "pacman"), ("apt", "apt-get")):
        if shutil.which(binary):
            return pm
    return None


def pick_method(install):
    """First applicable method: platform pm -> npm -> curl. None -> manual."""
    order = [platform_pm()]
    if shutil.which("npm") or shutil.which("pnpm"):
        order.append("npm")
    order.append("curl")
    for method in order:
        if method and method in install:
            return method
    return None


def cmd_tools():
    for name, entry in load_catalog().get("cli", {}).items():
        installed = bool(shutil.which(entry["detect"]))
        print(f"TOOL {name} installed={'yes' if installed else 'no'}")
    return 0


def cmd_tools_install(name, dry=False, yes=False):
    entry = load_catalog().get("cli", {}).get(name)
    if entry is None:
        print(f"TOOL_UNKNOWN {name} — agregalo en tools.toml")
        return 2
    if shutil.which(entry["detect"]):
        print(f"TOOL_SKIP {name} ({version_of(entry['detect'])})")
        return 0
    method = pick_method(entry["install"])
    if method is None:
        print(f"TOOL_MANUAL {name}: sin método automático acá — {entry['install'].get('doc', '')}")
        return 1
    command = entry["install"][method]
    if command.startswith("npm ") and not shutil.which("npm"):
        command = "p" + command  # pnpm fallback, same verbs
    if dry:
        print(f"TOOL_PLAN {name} method={method}")
        return 0
    if command.startswith("sudo "):
        # Never silent sudo (same contract as install.sh), even with --yes.
        if not sys.stdin.isatty():
            print(f"TOOL_MANUAL {name}: necesita sudo — corré: {command}")
            return 1
        print(f"Se necesita privilegio de administrador para:\n    {command}")
        if input("¿Ejecutar ese comando? [y/N] ").strip().lower() not in {"y", "yes", "s", "si"}:
            return 1
    elif not yes:
        # No TTY and no --yes -> never run anything silently.
        if not sys.stdin.isatty():
            print(f"TOOL_MANUAL {name}: sin TTY y sin --yes — corré: {command}")
            return 1
        if input(f"¿Ejecutar '{command}'? [y/N] ").strip().lower() not in {"y", "yes", "s", "si"}:
            return 1
    result = subprocess.run(["bash", "-c", command], check=False)
    if result.returncode == 0:
        print(f"TOOL_OK {name}")
        if entry.get("note"):
            print(f"NOTA: {entry['note']}")
        return 0
    print(f"TOOL_FAIL {name} rc={result.returncode} — {entry['install'].get('doc', '')}")
    return 1


def tools_menu():
    catalog = load_catalog().get("cli", {})
    names = list(catalog)
    print()
    for index, name in enumerate(names, 1):
        installed = bool(shutil.which(catalog[name]["detect"]))
        state = color("instalado", "32") if installed else "falta"
        print(f"  [{index}] {name:<10} {state}")
    answer = input("¿Cuál instalo? (número, Enter vuelve): ").strip()
    if answer.isdigit() and 1 <= int(answer) <= len(names):
        cmd_tools_install(names[int(answer) - 1])


# ----------------------------------------------------------------------- mcp

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


def read_json(path):
    try:
        return json.loads(Path(path).read_text())
    except (OSError, json.JSONDecodeError):
        return {}


def read_json_for_write(path):
    """Like read_json, but NEVER treats an existing-but-corrupt file as empty:
    rewriting it would silently destroy the user's config."""
    path = Path(path)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise SystemExit(f"MCP_ABORT {path} existe pero no parsea como JSON ({exc}); arreglalo antes de tocarlo")


def mcp_targets():
    """Detected harnesses that can host MCP servers, adapter config per target."""
    home = Path.home()
    table = {
        "opencode": {"detect": shutil.which("opencode"), "path": home / ".config/opencode/opencode.json"},
        "claude": {"detect": shutil.which("claude"), "path": home / ".claude.json"},
        "codex": {"detect": shutil.which("codex"), "path": home / ".codex/config.toml"},
        "cursor": {"detect": (home / ".cursor").is_dir(), "path": home / ".cursor/mcp.json"},
        "gemini": {"detect": shutil.which("gemini"), "path": home / ".gemini/settings.json"},
    }
    return {name: entry for name, entry in table.items() if entry["detect"]}


def _servers_key(harness):
    return "mcp" if harness == "opencode" else "mcpServers"


def _mcp_json_entry(harness, spec):
    if harness == "opencode":
        entry = {"type": spec["type"]}
        if spec["type"] == "local":
            entry["command"] = spec["command"]
        else:
            entry["url"] = spec["url"]
        entry["enabled"] = False  # repo policy: added disabled, toggled on demand
        return entry
    if spec["type"] == "local":
        return {"command": spec["command"][0], "args": spec["command"][1:]}
    return {"type": "http", "url": spec["url"]}


def _codex_section(name, spec):
    lines = [f"[mcp_servers.{name}]"]
    if spec["type"] == "local":
        lines.append(f"command = {json.dumps(spec['command'][0])}")
        lines.append(f"args = {json.dumps(spec['command'][1:])}")
    else:
        lines.append(f"url = {json.dumps(spec['url'])}")
    lines.append("enabled = false")
    return lines


def _codex_span(lines, name):
    header = f"[mcp_servers.{name}]"
    try:
        start = lines.index(header)
    except ValueError:
        return None
    end = next(
        (i for i in range(start + 1, len(lines)) if lines[i].startswith("[") and lines[i].endswith("]")),
        len(lines),
    )
    return start, end


def mcp_state(harness, target, name):
    path = target["path"]
    if harness == "codex":
        try:
            section = tomllib.loads(path.read_text()).get("mcp_servers", {}).get(name)
        except (OSError, tomllib.TOMLDecodeError):
            section = None
        if section is None:
            return "absent"
        return "on" if section.get("enabled", True) else "off"
    entry = read_json(path).get(_servers_key(harness), {}).get(name)
    if entry is None:
        return "absent"
    if harness == "opencode":
        return "on" if entry.get("enabled") else "off"
    return "on"  # claude/cursor/gemini: present == active


def mcp_write(harness, target, name, spec=None, enabled=None, remove=False):
    """Add (spec), toggle (enabled) or remove a server in the target's native format."""
    path = target["path"]
    if harness == "codex":
        lines = path.read_text().splitlines() if path.exists() else []
        span = _codex_span(lines, name)
        if remove and span:
            del lines[span[0]:span[1]]
        elif enabled is not None and span:
            start, end = span
            pattern = [i for i in range(start + 1, end) if lines[i].split("=")[0].strip() == "enabled"]
            value = f"enabled = {'true' if enabled else 'false'}"
            if pattern:
                lines[pattern[0]] = value
            else:
                lines.insert(start + 1, value)
        elif spec is not None and not span:
            if lines and lines[-1] != "":
                lines.append("")
            lines.extend(_codex_section(name, spec))
        if not lines:
            return  # nothing to write; never create an empty config.toml
        atomic_write(path, "\n".join(lines).rstrip() + "\n")
        return
    data = read_json_for_write(path)
    servers = data.setdefault(_servers_key(harness), {})
    if remove:
        servers.pop(name, None)
    elif enabled is not None and harness == "opencode" and name in servers:
        servers[name]["enabled"] = enabled
    elif spec is not None and name not in servers:
        servers[name] = _mcp_json_entry(harness, spec)
    atomic_write(path, json.dumps(data, indent=2) + "\n")


def _mcp_spec(name):
    spec = load_catalog().get("mcp", {}).get(name)
    if spec is None:
        print(f"MCP_UNKNOWN {name} — agregalo en tools.toml")
    return spec


def _mcp_selected(harness):
    targets = mcp_targets()
    if harness:
        if harness not in targets:
            print(f"MCP_NO_HARNESS {harness} (no detectado en esta máquina)")
            return {}
        return {harness: targets[harness]}
    return targets


def cmd_mcp():
    targets = mcp_targets()
    for name in load_catalog().get("mcp", {}):
        for harness, target in targets.items():
            print(f"MCP {name} harness={harness} state={mcp_state(harness, target, name)}")
    return 0


def cmd_mcp_add(name, harness=None):
    spec = _mcp_spec(name)
    if spec is None:
        return 2
    for h, target in _mcp_selected(harness).items():
        if h == "opencode" and name in MANAGED_MCP:
            print(f"MCP_MANAGED {name} harness=opencode — ya lo gestiona el repo (toggle con --mcp-on/--mcp-off)")
            continue
        if mcp_state(h, target, name) != "absent":
            print(f"MCP_SKIP {name} harness={h} (ya existe)")
            continue
        mcp_write(h, target, name, spec=spec)
        print(f"MCP_ADDED {name} harness={h} state={mcp_state(h, target, name)}")
    if spec.get("note"):
        print(f"NOTA: {spec['note']}")
    return 0


def cmd_mcp_toggle(name, harness, enabled):
    # opencode/codex toggle an existing entry in place, so managed servers
    # (engram/brave-cdp) work here even without a tools.toml spec; the
    # add-on-enable formats (claude/cursor/gemini) do need the catalog.
    spec = load_catalog().get("mcp", {}).get(name)
    for h, target in _mcp_selected(harness).items():
        state = mcp_state(h, target, name)
        if h in ("opencode", "codex"):
            if state == "absent":
                print(f"MCP_ABSENT {name} harness={h} (primero --mcp-add)")
                continue
            mcp_write(h, target, name, enabled=enabled)
        else:
            # No disable flag in these formats: on == present, off == removed.
            if enabled and state == "absent":
                if spec is None:
                    print(f"MCP_UNKNOWN {name} harness={h} — agregalo en tools.toml para poder encenderlo acá")
                    continue
                mcp_write(h, target, name, spec=spec)
            elif not enabled and state != "absent":
                mcp_write(h, target, name, remove=True)
        print(f"MCP_SET {name} harness={h} state={mcp_state(h, target, name)}")
    return 0


def cmd_mcp_remove(name, harness=None):
    targets = _mcp_selected(harness)
    known = name in load_catalog().get("mcp", {}) or any(
        mcp_state(h, target, name) != "absent" for h, target in targets.items()
    )
    if not known:
        # A typo must never delete a user's own unrelated server.
        print(f"MCP_UNKNOWN {name} — no está en el catálogo ni configurado en ningún harness")
        return 2
    for h, target in targets.items():
        if h == "opencode" and name in MANAGED_MCP:
            print(f"MCP_MANAGED {name} harness=opencode — no se remueve un server gestionado")
            continue
        mcp_write(h, target, name, remove=True)
        print(f"MCP_REMOVED {name} harness={h}")
    return 0


# --------------------------------------------------------------------- vault
# Company-level Obsidian vault: one graph per company/client. Default mode:
# project notes live INSIDE each repo (docs/notas/, versioned, auto-rendered
# by feature-state.py) and join the vault through a symlink under Proyectos/.
# Private mode inverts that: notes live INSIDE the vault (so syncing the vault
# folder between machines carries them) and the repo holds a git-excluded
# symlink — nothing note-related ever reaches the project's remote.

VAULT_HUB = "00 - INICIO.md"


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


def cmd_vault_init(target, company=None):
    target = Path(target).expanduser()
    company = company or target.resolve().name.upper()
    vault = target / "obsidian"
    seeds = {
        vault / VAULT_HUB: vault_seed_hub(company),
        vault / company / "contexto.md": (
            f"# {company} — contexto\n\n_TODO: contexto general de la empresa/cliente que "
            "cualquier agente debería conocer antes de trabajar en sus proyectos._\n"
        ),
        vault / "Casos" / "00 - Plantilla Caso.md": vault_seed_case_template(),
    }
    created = False
    for path, content in seeds.items():
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
            print(f"VAULT_CREATED {path.relative_to(target)}")
            created = True
    projects = vault / "Proyectos"
    if not projects.exists():
        projects.mkdir(parents=True)
        created = True
    print(f"{'VAULT_INIT_OK' if created else 'VAULT_INIT_SKIP'} dir={vault}")
    return 0


def find_vault(project, explicit=None):
    if explicit:
        vault = Path(explicit).expanduser()
        return vault if (vault / VAULT_HUB).exists() else None
    for ancestor in Path(project).resolve().parents:
        candidate = ancestor / "obsidian"
        if (candidate / VAULT_HUB).exists():
            return candidate
    configured = app_config().get("vault")
    if configured and (Path(configured).expanduser() / VAULT_HUB).exists():
        return Path(configured).expanduser()
    return None


def project_notes_seed(project_name):
    # feature-state.py regenerates the auto block; this seed adds the manual frame.
    return (
        f"# {project_name} — notas\n\n"
        "<!-- notas:auto -->\n_Se completa solo con la primera mutación de estado "
        "(o corré `python3 ai/scripts/feature-state.py sync-notes`)._\n<!-- /notas:auto -->\n\n"
        "## Notas propias\n\n_Qué es este proyecto, contexto, links útiles — esto no se pisa._\n"
    )


def exclude_notes_from_git(project):
    """Hide docs/notas from the project's git locally (.git/info/exclude, never pushed)."""
    if not (project / ".git").is_dir():
        return False
    info = project / ".git" / "info"
    info.mkdir(parents=True, exist_ok=True)
    exclude = info / "exclude"
    lines = exclude.read_text().splitlines() if exclude.exists() else []
    if "docs/notas" in lines:
        return False
    exclude.write_text("\n".join(lines + ["docs/notas"]) + "\n")
    return True


def vault_link_private(project, target_vault, notes, notes_home):
    """Private mode: notes live in the vault; the repo gets an excluded symlink."""
    if notes.is_symlink():
        if notes.resolve() == notes_home.resolve():
            if exclude_notes_from_git(project):
                print("VAULT_PRIVATE_EXCLUDED docs/notas (.git/info/exclude)")
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
        seed.write_text(project_notes_seed(project.name))
        print(f"VAULT_CREATED {seed}")
    notes.parent.mkdir(parents=True, exist_ok=True)
    try:
        notes.symlink_to(os.path.relpath(notes_home, notes.parent))
    except OSError as exc:
        print(f"VAULT_LINK_CONFLICT no pude crear el symlink: {exc}")
        return 1
    if exclude_notes_from_git(project):
        print("VAULT_PRIVATE_EXCLUDED docs/notas (.git/info/exclude)")
    print(f"VAULT_LINK_OK project={project.name} vault={target_vault} mode=private")
    return 0


def cmd_vault_link(project, vault=None, private=False):
    project = Path(project).expanduser().resolve()
    if not project.is_dir():
        print(f"VAULT_NOT_FOUND proyecto inexistente: {project}")
        return 2
    target_vault = find_vault(project, vault)
    if target_vault is None:
        print("VAULT_NOT_FOUND: no hay obsidian/00 - INICIO.md en los ancestros; corré --vault-init o pasá --vault")
        return 2
    notes = project / "docs" / "notas"
    if private:
        return vault_link_private(project, target_vault, notes, target_vault / "Proyectos" / project.name)
    seed = notes / "00 - Proyecto.md"
    if not seed.exists():
        notes.mkdir(parents=True, exist_ok=True)
        seed.write_text(project_notes_seed(project.name))
        print(f"VAULT_CREATED {seed}")
    link = target_vault / "Proyectos" / project.name
    if link.is_symlink():
        if link.resolve() == notes.resolve():
            print(f"VAULT_LINK_SKIP project={project.name} vault={target_vault}")
            return 0
        print(f"VAULT_LINK_CONFLICT {link} ya apunta a {link.resolve()} — resolvelo a mano")
        return 1
    if link.exists():
        print(f"VAULT_LINK_CONFLICT {link} existe y no es symlink — resolvelo a mano")
        return 1
    link.parent.mkdir(parents=True, exist_ok=True)
    try:
        relative = os.path.relpath(notes, link.parent)
        link.symlink_to(relative)
    except OSError as exc:
        print(f"VAULT_LINK_CONFLICT no pude crear el symlink: {exc}")
        return 1
    print(f"VAULT_LINK_OK project={project.name} vault={target_vault}")
    return 0


def vault_menu():
    print()
    print("El vault de empresa junta las notas de todos tus proyectos en un solo grafo Obsidian.")
    target = input("Directorio de la empresa (ej ~/iey; Enter vuelve): ").strip()
    if not target:
        return
    cmd_vault_init(target)
    project = input("¿Linkear un proyecto ahora? (path, Enter salta): ").strip()
    if project:
        private = input(
            "¿Privado? Las notas viven en el vault y quedan FUERA del git del proyecto [s/N]: "
        ).strip().lower() in {"s", "si", "sí", "y", "yes"}
        cmd_vault_link(project, str(Path(target).expanduser() / "obsidian"), private)


# ------------------------------------------------------------------- plugins

def claude_settings_path():
    return Path.home() / ".claude/settings.json"


def cmd_plugins():
    plugins = read_json(claude_settings_path()).get("enabledPlugins", {})
    if not plugins:
        print("PLUGINS_NONE")
    for name, enabled in sorted(plugins.items()):
        print(f"PLUGIN {name} enabled={'true' if enabled else 'false'}")
    return 0


def cmd_plugin_set(name, enabled):
    if name == "engram@engram":
        print("PLUGIN_MANAGED engram@engram — la política del repo lo fuerza apagado en cada install")
        return 1
    data = read_json_for_write(claude_settings_path())
    data.setdefault("enabledPlugins", {})[name] = enabled
    atomic_write(claude_settings_path(), json.dumps(data, indent=2) + "\n")
    print(f"PLUGIN_SET {name} enabled={'true' if enabled else 'false'}")
    return 0


def mcp_menu():
    catalog = list(load_catalog().get("mcp", {}))
    targets = mcp_targets()
    print()
    print(f"harnesses detectados: {', '.join(targets)}")
    for name in catalog:
        states = ", ".join(f"{h}:{mcp_state(h, t, name)}" for h, t in targets.items())
        print(f"  {name:<12} {states}")
    name = input("Server (Enter vuelve): ").strip()
    if not name:
        return
    action = input("[a]gregar / [e]ncender / a[p]agar / [r]emover: ").strip().lower()
    harness = input(f"Harness ({'/'.join(targets)}, Enter=todos): ").strip() or None
    if action == "a":
        cmd_mcp_add(name, harness)
    elif action == "e":
        cmd_mcp_toggle(name, harness, True)
    elif action == "p":
        cmd_mcp_toggle(name, harness, False)
    elif action == "r":
        cmd_mcp_remove(name, harness)


def plugins_menu():
    cmd_plugins()
    name = input("Plugin a togglear (Enter vuelve): ").strip()
    if not name:
        return
    current = read_json(claude_settings_path()).get("enabledPlugins", {}).get(name, False)
    cmd_plugin_set(name, not current)


# ---------------------------------------------------------------------- menu

def run_tty(command):
    """Foreground child with inherited TTY: sudo/login prompts must reach the user."""
    return subprocess.run(command, check=False).returncode


DRIFT_BADGE = {
    "ok": lambda: color("OK", "32"),
    "stale": lambda: color("DESACTUALIZADO", "33"),
    "unknown": lambda: "?",
}


def menu():
    print()
    banner()
    if first_run():
        print()
        print(bold(f"📖 Primera vez acá → leé README.md (sección {platform_label()}) para saber qué esperar."))
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        APP_CONFIG.write_text("auto_update = true\n")
    print(dim("· chequeando updates…"))
    update_badge = launch_update_check()
    # Drift regenerates a full staging (~2 s): cache it and refresh only after
    # actions that can change it, instead of on every redraw.
    drift = drift_state()
    while True:
        print()
        print(bold(f"=== SET-AGENTS {short_sha()} ==="))
        print(
            f"drift: {DRIFT_BADGE[drift]()} | update: {color(update_badge, '36')} | "
            + dim(f"auto-update: {'on' if auto_update_enabled() else 'off'}")
        )
        print()
        print("[1] 📦 Instalar / Reparar")
        print("[2] 🔄 Actualizar")
        print("[3] 🧠 Modelos")
        print("[4] 🧰 Herramientas (CLIs)")
        print("[5] 🔌 MCPs")
        print("[6] 🧩 Plugins Claude Code")
        print("[7] 📊 Estado")
        print("[8] ⏻  Salir")
        print("[9] 🗒  Vault Obsidian")
        choice = input("> ").strip()
        if choice == "1":
            if run_tty([str(ROOT / "install.sh")]) != 0:
                print(color("El instalador terminó con error — revisá la salida de arriba.", "31"))
            drift = drift_state()
        elif choice == "2":
            if cmd_update() == 0:
                update_badge = "al día"
            drift = drift_state()
        elif choice == "3":
            if run_tty([str(ROOT / "setup-models.sh")]) != 0:
                print(color("El wizard terminó con error — revisá la salida de arriba.", "31"))
            drift = drift_state()
        elif choice == "4":
            tools_menu()
        elif choice == "5":
            mcp_menu()
        elif choice == "6":
            plugins_menu()
        elif choice == "7":
            drift = drift_state()
            cmd_status(human=True)
            answer = input("auto-update: [t]oggle / Enter para volver: ").strip().lower()
            if answer == "t":
                set_auto_update(not auto_update_enabled())
        elif choice == "8":
            return 0
        elif choice == "9":
            vault_menu()


def main():
    parser = argparse.ArgumentParser(
        prog="set-agents",
        description=__doc__,
        epilog="Primera vez: leé README.md — explica qué vas a ver según tu sistema operativo.",
    )
    parser.add_argument("--status", action="store_true", help="estado en una línea (APP_STATUS ...)")
    parser.add_argument("--route-explain", metavar="TASK_CLASS")
    parser.add_argument("--routing-report", action="store_true")
    parser.add_argument("--route-decide", metavar="FILE", help="descriptor JSON ('-' = stdin); decide y, para writers, autoriza")
    parser.add_argument("--route-dispatched", metavar="RUN_ID")
    parser.add_argument("--route-terminal", nargs=2, metavar=("RUN_ID", "OUTCOME"))
    parser.add_argument("--routing-open-runs", action="store_true")
    parser.add_argument("--routing-recent-writers", action="store_true")
    parser.add_argument("--fresh-probes", action="store_true", help="con --route-decide: saltea el cache de probes")
    parser.add_argument("--latency-ms", type=int, default=None, help="con --route-terminal: latencia observada")
    parser.add_argument("--json", action="store_true", help="salida JSON para comandos de observabilidad")
    parser.add_argument("--check-update", action="store_true")
    parser.add_argument("--update", action="store_true")
    parser.add_argument("--yes", action="store_true")
    parser.add_argument("--no-install", action="store_true")
    parser.add_argument("--auto-update", choices=("on", "off"))
    parser.add_argument("--tools", action="store_true", help="TOOL <name> installed=yes/no")
    parser.add_argument("--tools-install", metavar="NAME")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--mcp", action="store_true", help="MCP <name> harness=<h> state=...")
    parser.add_argument("--mcp-add", metavar="NAME")
    parser.add_argument("--mcp-remove", metavar="NAME")
    parser.add_argument("--mcp-on", metavar="NAME")
    parser.add_argument("--mcp-off", metavar="NAME")
    parser.add_argument("--harness", choices=("opencode", "claude", "codex", "cursor", "gemini", "pi"))
    parser.add_argument("--doctor", action="store_true", help="chequeo redactado del harness (usar con --harness pi)")
    parser.add_argument("--plugins", action="store_true")
    parser.add_argument("--plugin-on", metavar="NAME")
    parser.add_argument("--plugin-off", metavar="NAME")
    parser.add_argument("--vault-init", metavar="DIR", help="crea el vault Obsidian de la empresa en DIR/obsidian")
    parser.add_argument("--vault-link", metavar="PROYECTO", help="linkea docs/notas del proyecto al vault")
    parser.add_argument("--vault", metavar="DIR", help="vault explícito para --vault-link")
    parser.add_argument("--private", action="store_true",
                        help="con --vault-link: las notas viven en el vault y el repo queda con un symlink excluido de git")
    parser.add_argument("--company", metavar="NAME")
    args = parser.parse_args()

    routing_human = sys.stdout.isatty() and not args.json
    # Routing modes are total: JSON is a rendering modifier, per-mode modifiers are the only
    # exemptions (--fresh-probes with decide, --latency-ms with terminal), and no other argument —
    # operational command or modifier — may be silently combined with a routing mode. Comparing every
    # parsed argument against its parser default keeps this exhaustive when new flags are added.
    # F08/N11: presence is checked with `is not None` for value-bearing flags, NEVER truthiness —
    # `--route-decide ""` is a present-but-EMPTY string, which is falsy and would otherwise fall
    # straight through every mode check into the interactive menu/help instead of failing closed.
    _mode_flags = (args.route_explain is not None, args.routing_report, args.route_decide is not None,
                   args.route_dispatched is not None, args.route_terminal is not None,
                   args.routing_open_runs, args.routing_recent_writers)
    routing_mode = any(_mode_flags)
    _routing_args = {"json", "route_explain", "routing_report", "route_decide", "route_dispatched",
                     "route_terminal", "routing_open_runs", "routing_recent_writers",
                     "fresh_probes", "latency_ms"}
    other_mode = any(value != parser.get_default(name)
                     for name, value in vars(args).items() if name not in _routing_args)
    modifier_misuse = (args.fresh_probes and args.route_decide is None) or \
                      (args.latency_ms is not None and args.route_terminal is None)
    if (sum(_mode_flags) > 1) or (routing_mode and other_mode) or modifier_misuse:
        _routing_output(routing.cli_envelope(False, "routing", {}, (), ("ROUTING_INPUT_INVALID",)), routing_human)
        return 2
    if args.route_explain is not None:
        return cmd_route_explain(args.route_explain, human=routing_human)
    if args.routing_report:
        return cmd_routing_report(human=routing_human)
    if args.route_decide is not None:
        return cmd_route_decide(args.route_decide, human=routing_human, fresh=args.fresh_probes)
    if args.route_dispatched is not None:
        return cmd_route_dispatched(args.route_dispatched, human=routing_human)
    if args.route_terminal is not None:
        return cmd_route_terminal(args.route_terminal[0], args.route_terminal[1], args.latency_ms, human=routing_human)
    if args.routing_open_runs:
        return cmd_routing_open_runs(human=routing_human)
    if args.routing_recent_writers:
        return cmd_routing_recent_writers(human=routing_human)
    if args.doctor:
        return cmd_doctor(args.harness, human=routing_human)

    if args.status:
        return cmd_status(human=sys.stdout.isatty())
    if args.check_update:
        return cmd_check_update()
    if args.update:
        return cmd_update(yes=args.yes, no_install=args.no_install)
    if args.auto_update:
        set_auto_update(args.auto_update == "on")
        return 0
    if args.tools:
        return cmd_tools()
    if args.tools_install:
        return cmd_tools_install(args.tools_install, dry=args.dry_run, yes=args.yes)
    if args.mcp:
        return cmd_mcp()
    if args.mcp_add:
        return cmd_mcp_add(args.mcp_add, args.harness)
    if args.mcp_remove:
        return cmd_mcp_remove(args.mcp_remove, args.harness)
    if args.mcp_on:
        return cmd_mcp_toggle(args.mcp_on, args.harness, True)
    if args.mcp_off:
        return cmd_mcp_toggle(args.mcp_off, args.harness, False)
    if args.plugins:
        return cmd_plugins()
    if args.plugin_on:
        return cmd_plugin_set(args.plugin_on, True)
    if args.plugin_off:
        return cmd_plugin_set(args.plugin_off, False)
    if args.vault_init:
        return cmd_vault_init(args.vault_init, args.company)
    if args.vault_link:
        return cmd_vault_link(args.vault_link, args.vault, args.private)
    if not sys.stdin.isatty():
        parser.print_help()
        return 2
    return menu()


if __name__ == "__main__":
    raise SystemExit(main())
