#!/usr/bin/env python3
"""set-agents: unified console app for the SET-AGENTS harness (gentle-ai style).

A TTY menu plus a scriptable CLI over the same primitives: install/repair
(install.sh), self-update (git pull --ff-only + managed reinstall), model
routing (setup-models.sh), and — in later sections — the optional tools
catalog, MCP servers, and Claude Code plugins.
"""

import argparse
import hashlib
import json
import os
import re
import secrets
import shutil
import stat
import subprocess
import sys
import tempfile
import tomllib
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import models_config
import routing
import set_agents_spawn
import tui
from routing_core.domain import classify_pi_terminal_error

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
PROJECT_ROOT: Path | None = None
PROJECT_KEY: str | None = None
ROUTING_WARNINGS: tuple[str, ...] = ()
_PROJECT_KEY_RE = re.compile(r"^proj1_[0-9a-f]{32}$")
_MAX_FEATURE_BYTES = 1024 * 1024
_MAX_FEATURE_FILES = 256

# project_identity.py: project-root discovery and stable identity. It carries its own
# (identical-value) copies of `_PROJECT_KEY_RE`/`_MAX_FEATURE_BYTES` rather than importing
# them back from here, to avoid a genuine circular import (see its own module docstring).
from project_identity import (  # noqa: E402
    _real_directory, _has_project_marker, find_project_root, resolve_project_root,
    _casefold_project_path, _safe_read, ProjectIdentityError, project_key_for,
)


def _routing_store():
    """F07: the one seam a hermetic CLI test uses to drive decide/dispatched/terminal/abandoned
    against a temp root. Never set by real runs (see the module-level seam note above)."""
    key = PROJECT_KEY
    return (routing.RoutingStore._for_tests(Path(ROUTING_TEST_ROOT), project_key=key)
            if ROUTING_TEST_ROOT else routing.RoutingStore(project_key=key))


def _project_root_or_harness() -> Path:
    # Direct helper calls in legacy unit tests have no CLI resolution; production
    # routes always set PROJECT_ROOT in main before accessing project data.
    return PROJECT_ROOT or ROOT


# --------------------------------------------------- 014-model-preference-policy (AC-02)
#
# One real, per-harness-install sibling config file next to `APP_CONFIG` (the same
# private `STATE_DIR`, `write_app_config`'s own directory) -- NEVER routed through
# `write_app_config` (its flat `key = value` serializer, `:XXX` below, corrupts a nested
# preference table) or `app_config()` (its silent parse-failure-as-`{}` swallow). This
# file gets its OWN dedicated, atomic, fail-closed round-trip: `atomic_write` (already
# established for the Claude settings JSON writer above) for the temp-file+`os.replace`
# discipline, and a small, purpose-built two-table TOML serializer for a schema this
# contract fully owns and closes (`[preference]`, `[role_override]`) -- not a
# general-purpose nested-TOML writer (round-2 finding R2-F-04).
MODEL_PREFERENCE_PATH = STATE_DIR / "model-preference.toml"

# The closed, four-provider universe `_PAIR_COMMANDS` already probes
# (`routing_core/catalog.py:133-140`) -- defined independently here, never importing or
# referencing the catalog module's own billing-kind classification table (AC-06 non-goal).
_MODEL_PREFERENCE_PROVIDERS = ("openai-codex", "anthropic", "opencode-zen", "opencode-go")
_MODEL_PREFERENCE_CLASSES = ("decision", "grunt", "build")
# AC-02's inertness note: the six roles with real, live effect today (`### Honest scope`,
# spec) -- every other in-scope role, and the whole `decision` class, is genuinely inert.
_MODEL_PREFERENCE_LIVE_ROLES = frozenset({
    "delta-reviewer", "finding-verifier", "package-reviewer", "security-auditor",
    "implementer", "debugger",
})


class ModelPreferenceError(ValueError):
    """AC-02: fail-closed error for the sibling `model-preference.toml` file/CLI -- a
    malformed value never degrades to a silent default (round-1 F-07, round-3 R3-F-04)."""


def _model_preference_die(message):
    raise ModelPreferenceError(message)


def _validate_preference_providers(class_name, providers):
    """AC-02 resolution states 1/2/4d: shared by the config-load path and the CLI write
    path (`load_model_preference`/`cmd_model_preference_set` below) -- a malformed value
    can never even be WRITTEN by the CLI to begin with; a hand-edited file is the only way
    to reach this same check at load time."""
    if not isinstance(providers, (list, tuple)) or not providers:
        _model_preference_die(f"model-preference.toml: [preference].{class_name} must be a non-empty list of providers")
    validated = []
    for token in providers:
        if not isinstance(token, str) or token not in _MODEL_PREFERENCE_PROVIDERS:
            _model_preference_die(f"model-preference.toml: [preference].{class_name} contains unknown provider {token!r}")
        validated.append(token)
    if len(validated) != len(set(validated)):
        _model_preference_die(f"model-preference.toml: [preference].{class_name} contains a duplicate provider")
    return tuple(validated)


def _validate_role_override_entry(role, class_name, roster_roles):
    """AC-02 resolution states 3/4: reuses the exact `models_config.load_roles` unknown-
    role precedent shape (per-role-named `die()`, `models_config.py:274-276`), and rejects
    `"unscoped"` (a resolution OUTCOME, never a legal override target)."""
    if role not in roster_roles:
        _model_preference_die(f"model-preference.toml: [role_override].{role} does not match any role in roles.tsv")
    if not isinstance(class_name, str) or class_name not in _MODEL_PREFERENCE_CLASSES:
        _model_preference_die(f"model-preference.toml: [role_override].{role} names unknown class {class_name!r}")
    return class_name


def _read_model_preference_raw():
    """Fail-closed parse only -- never `app_config()`'s silent `except: return {}}` swallow
    (round-3 R3-F-04(a)); a malformed file loudly fails every caller, load or write alike."""
    try:
        raw = MODEL_PREFERENCE_PATH.read_text()
    except FileNotFoundError:
        return {}
    except OSError as exc:
        _model_preference_die(f"model-preference.toml: {exc}")
    try:
        doc = tomllib.loads(raw)
    except tomllib.TOMLDecodeError as exc:
        _model_preference_die(f"model-preference.toml: {exc}")
    if not isinstance(doc, dict) or set(doc) - {"preference", "role_override"}:
        _model_preference_die("model-preference.toml: unknown top-level key")
    return doc


def load_model_preference(roster_roles=None):
    """AC-02/AC-03: the config-load path. Returns
    `{"preference": {class: (providers...)}, "role_override": {role: class}}` --
    absent file is the unbiased default (both tables empty), never a crash. `roster_roles`
    is an optional pre-loaded `{role, ...}` set (the CLI's own composition already has
    one); when omitted, the roster is loaded fresh from `roles.tsv`."""
    doc = _read_model_preference_raw()
    preference_table = doc.get("preference", {})
    if not isinstance(preference_table, dict):
        _model_preference_die("model-preference.toml: [preference] must be a table")
    preference = {}
    for class_name, providers in preference_table.items():
        if class_name not in _MODEL_PREFERENCE_CLASSES:
            _model_preference_die(f"model-preference.toml: [preference] has unknown class {class_name!r}")
        preference[class_name] = _validate_preference_providers(class_name, providers)
    override_table = doc.get("role_override", {})
    if not isinstance(override_table, dict):
        _model_preference_die("model-preference.toml: [role_override] must be a table")
    roles = roster_roles if roster_roles is not None else {row["role"] for row in models_config.load_roster(ROOT / "roles.tsv")}
    role_override = {}
    for role, class_name in override_table.items():
        role_override[role] = _validate_role_override_entry(role, class_name, roles)
    return {"preference": preference, "role_override": role_override}


def _config_with_model_preference(config, roster):
    """AC-04: the one channel available to feed AC-02's resolved preference tables into
    `RoutingService` without touching `routing.py`'s read-only `compose()` signature --
    injected under an internal-marker key `RoutingService.__init__` reads and strips,
    the same underscore-prefixed convention `models_config.py` already uses for
    `config["_source_schema"]` (never itself re-serialized to models.toml). A malformed
    sibling file fails closed exactly like a malformed `models.toml` already does --
    `ModelPreferenceError` bubbles to the caller's own existing except clause."""
    roster_roles = {row["role"] for row in roster}
    config["_model_preference"] = load_model_preference(roster_roles)
    return config


def _serialize_model_preference(doc):
    """The small, purpose-built, fixed-shape emitter this schema's own closure makes safe
    -- exactly two tables, each a flat mapping to a closed-vocabulary list/string. NOT a
    general nested-TOML writer (R2-F-04); every value is `json.dumps`-quoted, which is
    valid TOML string syntax for these ASCII, punctuation-free tokens."""
    lines = []
    preference = doc.get("preference") or {}
    if preference:
        lines.append("[preference]")
        for class_name in sorted(preference):
            rendered = ", ".join(json.dumps(token) for token in preference[class_name])
            lines.append(f"{class_name} = [{rendered}]")
        lines.append("")
    role_override = doc.get("role_override") or {}
    if role_override:
        lines.append("[role_override]")
        for role in sorted(role_override):
            lines.append(f"{role} = {json.dumps(role_override[role])}")
        lines.append("")
    return ("\n".join(lines).rstrip("\n") + "\n") if (preference or role_override) else ""


def _model_preference_class_inert(class_name):
    """AC-02: re-baselined round 4 (F-01) -- only `decision` is inert as a WHOLE class
    today; `grunt`/`build` each have at least one live tiered role, so a class-scoped
    write to either never fires the note even though some of that class's own non-tiered
    members individually would (checked per-role by `_model_preference_role_inert`)."""
    return class_name == "decision"


def _model_preference_role_inert(role):
    """AC-02: true for every role except the six with real, live effect today."""
    return role not in _MODEL_PREFERENCE_LIVE_ROLES


_MODEL_PREFERENCE_NOTE_SUFFIX = "(see docs/specs/014-model-preference-policy/spec.md ### Honest scope)"


def cmd_model_preference_set(class_name, providers):
    """AC-02: `--model-preference-set CLASS --provider NAME [--provider NAME ...]` --
    writes/replaces `[preference].<CLASS>`, leaving every other key untouched (the
    round-trip regression test proves this isolation)."""
    validated = _validate_preference_providers(class_name, providers)
    # RF14-06: the ENTIRE existing document -- not just the class/role this write
    # touches -- must validate via `load_model_preference`'s own validators before any
    # merge/re-serialize; a pre-existing invalid entry (e.g. a hand-edited non-list
    # value) must `die()` here rather than reach `_serialize_model_preference`, whose
    # `", ".join(... for token in preference[class_name])` would silently iterate a
    # string value character by character and corrupt the file.
    load_model_preference()
    doc = _read_model_preference_raw()
    preference = dict(doc.get("preference") or {})
    preference[class_name] = list(validated)
    doc = {**doc, "preference": preference}
    atomic_write(MODEL_PREFERENCE_PATH, _serialize_model_preference(doc))
    if _model_preference_class_inert(class_name):
        print(f"MODEL_PREFERENCE_NOTE class={class_name} has no observable effect on the primary lane today {_MODEL_PREFERENCE_NOTE_SUFFIX}", file=sys.stderr)
    print(f"MODEL_PREFERENCE_SET class={class_name} providers=" + ",".join(validated))
    return 0


def cmd_model_preference_role_override(role, class_name):
    """AC-02: `--model-preference-role-override ROLE CLASS` -- writes/replaces
    `[role_override].<ROLE>`, moving that one role into a different class than AC-01's
    default resolution."""
    roster_roles = {row["role"] for row in models_config.load_roster(ROOT / "roles.tsv")}
    validated_class = _validate_role_override_entry(role, class_name, roster_roles)
    # RF14-06: same fail-closed whole-document validation as cmd_model_preference_set above.
    load_model_preference(roster_roles)
    doc = _read_model_preference_raw()
    role_override = dict(doc.get("role_override") or {})
    role_override[role] = validated_class
    doc = {**doc, "role_override": role_override}
    atomic_write(MODEL_PREFERENCE_PATH, _serialize_model_preference(doc))
    if _model_preference_role_inert(role):
        print(f"MODEL_PREFERENCE_NOTE role={role} has no observable effect on the primary lane today {_MODEL_PREFERENCE_NOTE_SUFFIX}", file=sys.stderr)
    print(f"MODEL_PREFERENCE_ROLE_OVERRIDE role={role} class={validated_class}")
    return 0


def cmd_model_preference_show():
    """AC-02 resolution state (e): read-only, prints the sibling file's current, fully-
    resolved `[preference]`/`[role_override]` contents, or a clear no-preferences line."""
    data = load_model_preference()
    if not data["preference"] and not data["role_override"]:
        print("MODEL_PREFERENCE_NONE")
        return 0
    for class_name in sorted(data["preference"]):
        print(f"MODEL_PREFERENCE preference.{class_name}=" + ",".join(data["preference"][class_name]))
    for role in sorted(data["role_override"]):
        print(f"MODEL_PREFERENCE role_override.{role}=" + data["role_override"][role])
    return 0


def routing_catalog(simulation=False):
    """Compose trusted v2 inputs; callers never supply a catalog or route ID."""
    config = models_config.load_config(ROOT / "models.toml")
    roster = models_config.load_roster(ROOT / "roles.tsv")
    config = _config_with_model_preference(config, roster)
    # No optimistic defaults: each real invocation gets a fresh exact probe.
    return routing.compose(config, roster, simulate=simulation, store=None if simulation else _routing_store()), config


def _routing_output(payload, human):
    if ROUTING_WARNINGS:
        payload = dict(payload)
        payload["warnings"] = list(dict.fromkeys((*payload.get("warnings", ()), *ROUTING_WARNINGS)))
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
    except ModelPreferenceError as exc:
        _routing_output(routing.cli_envelope(False, "route-explain", {"message": str(exc)}, (), ("ROUTING_INPUT_INVALID",)), human); return 2
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

# routing_cli.py: routing helpers with no dependency on `_routing_store`/`_routing_output`
# (both stay in this file -- see routing_cli.py's own module docstring for why).
from routing_cli import (  # noqa: E402
    _role_class_of, _DECIDE_OK_NON_EXECUTABLE_REASONS, _decide_status, _SAFE_STATE_ID,
    _TERMINAL_FEATURE_PHASES, _TERMINAL_PACKAGE_STATUS, _load_feature_doc, _safe_state_id,
    _validate_context_pack_path, _package_context_ok, _resolve_context_pack,
    _MAX_USAGE_TEXT_LEN, parse_usage,
)


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
        config = _config_with_model_preference(config, roster)
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
    except ModelPreferenceError as exc:
        _routing_output(routing.cli_envelope(False, "route-decide", {"message": str(exc)}, (), ("ROUTING_INPUT_INVALID",)), human); return 2
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


def cmd_route_quota_exhausted(run_id, quota_error_text, latency_ms, usage_text=None, human=False):
    try:
        error = parse_usage(quota_error_text)
        usage = parse_usage(usage_text) if usage_text is not None else None
    except ValueError:
        _routing_output(routing.cli_envelope(False, "route-quota-exhausted", {}, (), ("ROUTING_INPUT_INVALID",)), human); return 2
    if classify_pi_terminal_error(error) != "quota_exhausted":
        _routing_output(routing.cli_envelope(False, "route-quota-exhausted", {}, (), ("AUTHORIZATION_INVALID",)), human); return 1
    def action(store):
        replacement = store.close_exhausted_and_authorize_replacement(run_id, "quota_exhausted", usage, latency_ms)
        return {"run_id": run_id, "state": "terminal_failure", "outcome": "quota_exhausted",
                "replacement_run_id": replacement["run_id"], "replacement_existing": replacement["existing"],
                "replacement_provider": replacement.get("provider"), "replacement_model": replacement.get("model")}
    return _lifecycle_command("route-quota-exhausted", run_id, action, human)


def cmd_quota_failover_e2e():
    """AC-06's deliberately separate live-provider gate.

    This harness never manufactures an exhausted subscription, credentials, or provider
    inventory.  Until an operator supplies and independently verifies that controlled
    environment, the only honest outcome is blocked; in particular this command must not
    become a green mock/simulation shortcut for the real failure path.
    """
    print(json.dumps({"status": "BLOCKED", "reason": "HUMAN_DECISION_REQUIRED",
                      "gate": "AC-06", "detail": "controlled exhausted subscription not verified"},
                     sort_keys=True))
    return 3


_LATENCY_MAX = 2**31 - 1


def cmd_route_terminal(run_id, outcome, latency_ms, usage_text=None, human=False):
    if outcome not in {"success", "failure"}:
        _routing_output(routing.cli_envelope(False, "route-terminal", {}, (), ("ROUTING_INPUT_INVALID",)), human); return 2
    # SEC-A02: bound --latency-ms at the CLI, before it ever reaches the store — an
    # out-of-range value (overflow) or a negative one (would decrement rollup sums) is a
    # PARSE failure, not a runtime one.
    if latency_ms is not None and (isinstance(latency_ms, bool) or not isinstance(latency_ms, int)
                                   or not (0 <= latency_ms <= _LATENCY_MAX)):
        _routing_output(routing.cli_envelope(False, "route-terminal", {}, (), ("ROUTING_INPUT_INVALID",)), human); return 2
    # AC-11: malformed (unparseable) --usage is a PARSE failure at the CLI, same edge as
    # --latency-ms above. Anything parseable but untrustworthy is the STORE's edge
    # (close_run/_usage_row), never rejected here. "There is nothing to protect" was this
    # comment's claim before N-01 (delta review): a dict always serializes to valid JSON,
    # so malformed input is unreachable from route_and_spawn's production wiring either
    # way -- but a legitimate, merely-large usage object is reachable from it, and that
    # case is not "nothing to protect" (see parse_usage's docstring and ADR-0010 D3).
    usage = None
    if usage_text is not None:
        try:
            usage = parse_usage(usage_text)
        except ValueError:
            _routing_output(routing.cli_envelope(False, "route-terminal", {}, (), ("ROUTING_INPUT_INVALID",)), human); return 2
    def action(store):
        # F02: ONE transaction reads the state and transitions to exactly the right
        # destination (dispatched->terminal, authorized+failure->abandoned, anything else a
        # single rejected/STATE_CONFLICT) — never a try-terminal-then-except-abandon pair of
        # independent transactions, which left a spurious rejected row behind a successful
        # abandon and wrote two rejected rows for an unclosable run.
        state = store.close_run(run_id, outcome, latency_ms, usage=usage)
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


def write_app_config(**updates):
    """Read-merge-write over app_config() — the ONE writer every config mutation goes through
    (AC-15). A raw `APP_CONFIG.write_text(...)` anywhere else would silently clobber whatever
    this call didn't know about (e.g. a `vault` key persisted by a prior, unrelated run)."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    config = {**app_config(), **updates}
    lines = [
        f"{key} = {'true' if value else 'false'}" if isinstance(value, bool) else f"{key} = {json.dumps(value)}"
        for key, value in sorted(config.items())
    ]
    APP_CONFIG.write_text("\n".join(lines) + "\n")
    return config


def set_auto_update(enabled):
    write_app_config(auto_update=enabled)
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


# F-04: both remote CLI probes get an explicit timeout -- without one, a scripted
# `set-agents --status` (or the menu's status branch) can hang indefinitely on a wedged
# `opencode auth list`/`codex login status` instead of degrading to "needed" like `version_of`
# already does for a wedged `--version`.
AUTH_STATE_TIMEOUT_SECONDS = 15


def auth_state(cli):
    if not shutil.which(cli):
        return "missing"
    if cli == "opencode":
        try:
            result = subprocess.run(
                ["opencode", "auth", "list"], capture_output=True, text=True,
                timeout=AUTH_STATE_TIMEOUT_SECONDS, check=False,
            )
        except subprocess.TimeoutExpired:
            return "needed"
        return "ok" if result.returncode == 0 and result.stdout.strip() else "needed"
    if cli == "codex":
        try:
            result = subprocess.run(
                ["codex", "login", "status"], capture_output=True,
                timeout=AUTH_STATE_TIMEOUT_SECONDS, check=False,
            )
        except subprocess.TimeoutExpired:
            return "needed"
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


def _status_data(*, rows=True):
    """AC-28: the data cmd_status() prints from -- both the one-line machine summary and the
    human table rows, so a caller (the menu, a future non-print consumer) never has to re-derive
    what cmd_status() already computed.

    F-04: `rows` is lazy on purpose -- the per-CLI table (`version_of`/`auth_state`, up to 6
    subprocess probes) is ONLY needed for the human-readable render. `cmd_status(human=False)`
    (the scripted/piped `set-agents --status` path) must stay as cheap as it was before the
    data/print split -- it never calls this with `rows=True`.
    """
    data = {
        "sha": short_sha(), "drift": drift_state(), "behind": rev_count("HEAD..origin/main"),
        "auto_update": auto_update_enabled(), "rows": [],
    }
    if rows:
        for cli in HARNESS_CLIS:
            installed = shutil.which(cli)
            version = version_of(cli) if installed else "FALTA"
            data["rows"].append((cli, version, auth_state(cli) if installed else "-"))
    return data


def _status_machine_line(data):
    return (
        f"APP_STATUS sha={data['sha']} drift={data['drift']} "
        f"update={data['behind'] if data['behind'] is not None else '?'} "  # cached; --check-update fetches
        f"auto_update={'on' if data['auto_update'] else 'off'}"
    )


def _status_table_lines(data):
    """AC-28/F-03: the human table's lines, shared between `cmd_status(human=True)`'s own print
    and `menu()`'s status branch, which ALSO needs this exact text as the toggle picker's
    `header=` (F-03) so it survives the alternate-screen switch instead of being erased."""
    lines = [f"{'CLI':<10} {'VERSIÓN':<28} AUTH"]
    for cli, version, auth in data["rows"]:
        lines.append(f"{cli:<10} {version:<28} {auth}")
    if data["drift"] == "stale":
        # F-09: "Instalar / Reparar" is the actual menu item label now (arrow-key selector,
        # no numbered grid) -- "opción [1]" stopped meaning anything the day the grid did.
        lines.append("")
        lines.append("drift: la instalación quedó atrás del repo → Instalar / Reparar o ./build.sh --install")
    return lines


def cmd_status(human=False):
    data = _status_data(rows=human)
    print(_status_machine_line(data))
    if not human:
        return 0
    print()
    for line in _status_table_lines(data):
        print(line)
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
    # No capture: build.sh shows the managed diff and asks on the caller's TTY (AC-26).
    with tui.suspend_terminal():
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
        # F-09: "Actualizar" is the actual menu item label -- "opción [2]" is a numbered-grid
        # reference that stopped being true the day the grid was replaced by the arrow selector.
        return f"{behind} commits nuevos (auto-update off → Actualizar)"
    if not tree_clean() or rev_count("origin/main..HEAD"):
        return f"{behind} commits nuevos (repo local con cambios → Actualizar)"
    print(bold(f"Actualización disponible ({behind} commits) — aplicando automáticamente…"))
    cmd_update(yes=True, assume_fetched=True)
    return "al día (recién actualizado)"


# --------------------------------------------------------------------- tools

def load_catalog():
    return tomllib.loads((ROOT / "tools.toml").read_text())


def platform_pm():
    if sys.platform == "darwin":
        return "brew" if shutil.which("brew") else None
    if sys.platform == "win32":
        for pm, binary in (("winget", "winget"), ("choco", "choco")):
            if shutil.which(binary):
                return pm
        return None
    for pm, binary in (("pacman", "pacman"), ("apt", "apt-get"), ("dnf", "dnf"), ("zypper", "zypper")):
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


def _safe_input(prompt):
    """`input()` that exits cleanly instead of a traceback on EOFError/KeyboardInterrupt
    (AC-29) — every remaining raw `input()` call in this module goes through this, since a
    prompt reached from the picker runs in COOKED mode (via `tui.suspend_terminal()`, where
    Ctrl-C generates a real SIGINT again, unlike inside the raw-mode picker loop itself, which
    reads Ctrl-C as a plain byte and never raises at all)."""
    try:
        return input(prompt)
    except (EOFError, KeyboardInterrupt):
        print()
        return ""


def _tools_data():
    """AC-28: the data cmd_tools()/tools_menu() both render, in catalog order."""
    return [
        (name, bool(shutil.which(entry["detect"])))
        for name, entry in load_catalog().get("cli", {}).items()
    ]


def cmd_tools():
    for name, installed in _tools_data():
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
        # AC-26: reached from the picker (tools_menu -> here), the terminal must be in cooked
        # mode for this to echo at all -- a no-op when there is no active session (the bare
        # --tools-install CLI path), so the behavior above is unchanged either way.
        with tui.suspend_terminal():
            answer = _safe_input("¿Ejecutar ese comando? [y/N] ")
        if answer.strip().lower() not in {"y", "yes", "s", "si"}:
            return 1
    elif not yes:
        # No TTY and no --yes -> never run anything silently.
        if not sys.stdin.isatty():
            print(f"TOOL_MANUAL {name}: sin TTY y sin --yes — corré: {command}")
            return 1
        with tui.suspend_terminal():
            answer = _safe_input(f"¿Ejecutar '{command}'? [y/N] ")
        if answer.strip().lower() not in {"y", "yes", "s", "si"}:
            return 1
    with tui.suspend_terminal():  # the command itself may prompt too (e.g. a sudo password)
        result = subprocess.run(["bash", "-c", command], check=False)
    if result.returncode == 0:
        print(f"TOOL_OK {name}")
        if entry.get("note"):
            print(f"NOTA: {entry['note']}")
        return 0
    print(f"TOOL_FAIL {name} rc={result.returncode} — {entry['install'].get('doc', '')}")
    return 1


def tools_menu():
    data = _tools_data()
    if not data:
        print("(sin herramientas en el catálogo)")
        return
    items = [
        f"{name:<10} {color('instalado', '32') if installed else 'falta'}"
        for name, installed in data
    ]
    choice = tui.run_picker(items, style={"color": color, "bold": bold, "dim": dim})
    if isinstance(choice, tui.Selected):
        cmd_tools_install(data[choice.index][0])


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


def _mcp_data():
    """AC-28: the data cmd_mcp()/mcp_menu() both render -- [(server, [(harness, state), ...]), ...]."""
    targets = mcp_targets()
    return [
        (name, [(harness, mcp_state(harness, target, name)) for harness, target in targets.items()])
        for name in load_catalog().get("mcp", {})
    ]


def cmd_mcp():
    for name, states in _mcp_data():
        for harness, state in states:
            print(f"MCP {name} harness={harness} state={state}")
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

# vault_ops.py: registry read/write, seed text, migration planning/repair, doctor reporting.
# `find_vault`/`_resolve_vault`/`cmd_vault_init`/`cmd_vault_link`/`apply_vault_migration`/
# `cmd_vault_doctor`/`vault_menu` stay here (see vault_ops.py's own module docstring for why:
# they need `app_config`/`write_app_config`/`STATE_DIR`, which must stay in this file).
from vault_ops import (  # noqa: E402
    VAULT_HUB, VAULT_REGISTRY, vault_registry_path, read_vault_registry, write_vault_registry_entry,
    vault_seed_hub, vault_seed_case_template, project_notes_seed, _git_rev_parse, _git_exclude_path,
    _notes_currently_excluded, exclude_notes_from_git, vault_link_private, VaultMigrationError,
    vault_migration_plan, _vault_project_dir_for, _vault_side_for_doctor, vault_doctor_report,
    _plan_fingerprint, _read_vault_doctor_marker as _vault_ops_read_vault_doctor_marker,
)


# AC-14: fixed core-plugin set, no community plugin manager. Ids verified against a real,
# already-configured Obsidian vault on this machine (~/iey/obsidian/.obsidian/core-plugins.json),
# not guessed — "backlink"/"tag-pane"/"global-search" are the real ids, not the spec's colloquial
# "backlinks"/"tags"/"search". app.json/appearance.json start empty, same as every vault Obsidian
# itself creates; Obsidian fills them in as the user configures the app, never overwritten here
# after first creation.
OBSIDIAN_CORE_PLUGINS = {"graph": True, "backlink": True, "outline": True, "global-search": True, "tag-pane": True}


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
        vault / ".obsidian" / "app.json": "{}\n",
        vault / ".obsidian" / "appearance.json": "{}\n",
        vault / ".obsidian" / "core-plugins.json": json.dumps(OBSIDIAN_CORE_PLUGINS, indent=2) + "\n",
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
    write_app_config(vault=str(vault.resolve()))  # AC-15: known-vault fallback for find_vault()
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


def _git_rev_parse(project, *args):
    """`git -C project rev-parse <args>`, hardened the same way as `git()` above:
    a purged env (a `GIT_DIR`/`GIT_WORK_TREE`/`GIT_COMMON_DIR`/`GIT_INDEX_FILE` inherited
    from the caller's shell would redirect git at a repo `project` never named -- verified
    live: with a stray `GIT_DIR` set, `rev-parse --git-common-dir` happily answers about an
    unrelated repo even for a `project` that isn't inside any repo at all), a timeout (never
    hang the CLI on git), and a caught missing binary. Returns None on any failure.
    """
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
    return exclude is not None and exclude.exists() and "docs/notas" in exclude.read_text().splitlines()


def exclude_notes_from_git(project):
    """Hide docs/notas from the project's git locally (.git/info/exclude, never pushed)."""
    exclude = _git_exclude_path(project)
    if exclude is None:
        return False
    exclude.parent.mkdir(parents=True, exist_ok=True)
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
    write_vault_registry_entry(
        target_vault, project, topology="private", vault_path=notes_home,
        notes_excluded=_notes_currently_excluded(project),
    )
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
    write_app_config(vault=str(target_vault.resolve()))  # AC-15: known-vault fallback for find_vault()
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
            write_vault_registry_entry(target_vault, project, topology="hybrid", vault_path=link, notes_excluded=_notes_currently_excluded(project))
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
    write_vault_registry_entry(target_vault, project, topology="hybrid", vault_path=link, notes_excluded=_notes_currently_excluded(project))
    print(f"VAULT_LINK_OK project={project.name} vault={target_vault}")
    return 0


def apply_vault_migration(project, target_vault, vault_project_dir, plan, *, exclude_notes=True):
    """Executes a `pure-move`/`merge` plan. Copy-verify-then-delete PER FILE (never a bare
    `shutil.move`, never a batch delete after a batch copy): an interrupted run leaves both
    copies present for whatever it hadn't reached yet, and a re-run is idempotent because
    `vault_migration_plan` skips files already copied and byte-identical. Reuses
    `cmd_vault_link`'s own hybrid-linking code for the final symlink instead of duplicating it.
    """
    if plan["action"] not in ("pure-move", "merge"):
        raise VaultMigrationError(f"cannot apply a plan with action={plan['action']!r}")
    project = Path(project)
    vault_project_dir = Path(vault_project_dir)
    notes = project / "docs" / "notas"
    notes.mkdir(parents=True, exist_ok=True)
    for rel in plan["files"]:
        src = vault_project_dir / rel
        dest = notes / rel
        # SEC-003: containment on both ends, re-checked here rather than trusted from the
        # plan -- plan and apply can run far apart, and a symlink planted at `dest` (e.g. a
        # dangling link into a repo outside the tree) is invisible to `dest.exists()` but
        # `shutil.copy2` still writes straight through it. Demonstrated arbitrary write.
        if _resolve_within(src, vault_project_dir) is None:
            raise VaultMigrationError(f"VAULT_MIGRATION_UNSAFE_SOURCE {rel}: source escapes the vault project dir")
        if dest.is_symlink() or _resolve_within(dest, notes) is None:
            raise VaultMigrationError(f"VAULT_MIGRATION_UNSAFE_DEST {rel}: destination is a symlink or escapes docs/notas")
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        if dest.stat().st_size != src.stat().st_size or dest.read_bytes() != src.read_bytes():
            raise VaultMigrationError(f"VAULT_MIGRATION_VERIFY_FAILED {rel}: copy did not match source")
        src.unlink()
    for rel in plan.get("already_present", []):
        # Byte-identical (re-verified, never trusted from a stale plan): safe to drop the
        # vault-side original without copying anything new.
        src, dest = vault_project_dir / rel, notes / rel
        if _resolve_within(src, vault_project_dir) is None or _resolve_within(dest, notes) is None:
            raise VaultMigrationError(f"VAULT_MIGRATION_UNSAFE_PATH {rel}: source or destination escapes its tree")
        if src.read_bytes() != dest.read_bytes():
            raise VaultMigrationError(f"VAULT_MIGRATION_VERIFY_FAILED {rel}: no longer byte-identical since planning")
        src.unlink()
    # Drop now-empty subdirectories left behind on the vault side, deepest first; never rmtree
    # (a directory that still holds something -- e.g. a sibling file this plan didn't touch --
    # simply fails to rmdir and is left alone).
    all_rel = plan["files"] + plan.get("already_present", [])
    emptied = sorted({(vault_project_dir / rel).parent for rel in all_rel}, key=lambda p: -len(p.parts))
    for directory in emptied:
        try:
            directory.rmdir()
        except OSError:
            pass
    if exclude_notes:
        exclude_notes_from_git(project)
    try:
        vault_project_dir.rmdir()
    except OSError:
        pass  # not empty or already gone -- cmd_vault_link below still succeeds either way
    return cmd_vault_link(project, vault=str(target_vault), private=False)


# ---------------------------------------------------------------- vault doctor (AC-17)

def _resolve_vault(explicit=None):
    """Same tail as find_vault(), for the no-project report pass: explicit path, else the
    configured fallback. Never walks ancestors — there is no project to walk from."""
    if explicit:
        vault = Path(explicit).expanduser()
        return vault if (vault / VAULT_HUB).exists() else None
    configured = app_config().get("vault")
    if configured and (Path(configured).expanduser() / VAULT_HUB).exists():
        return Path(configured).expanduser()
    return None


def _vault_doctor_marker_path(project):
    key = hashlib.sha256(str(Path(project).resolve()).encode()).hexdigest()[:16]
    return STATE_DIR / "vault-doctor-pending" / f"{key}.json"


# SEC-008: a --dry-run marker with no expiry stayed valid forever -- a marker backdated (or
# simply forgotten) by hours was still accepted for --repair. 15 minutes covers the real
# workflow (dry-run, read the plan, confirm, repair) without turning into a standing grant.
VAULT_DOCTOR_MARKER_TTL_SECONDS = 900


def _read_vault_doctor_marker(marker):
    """Consume the marker (single-use, atomically-enough for a single-operator CLI) and
    return its parsed content, or None if it's absent/corrupt/expired/stale. SEC-008: a
    corrupt marker used to raise `json.JSONDecodeError` straight through the CLI, and an
    expired one had no TTL at all -- see `vault_ops._read_vault_doctor_marker` (the
    read/unlink/parse step, moved out) for the single-use-consumption details; the TTL check
    itself stays here because it needs `VAULT_DOCTOR_MARKER_TTL_SECONDS`, kept alongside
    `cmd_vault_doctor` for the same STATE_DIR-monkeypatch reasons documented on vault_ops.py.
    """
    recorded = _vault_ops_read_vault_doctor_marker(marker)
    if recorded is None:
        return None
    try:
        age = (datetime.now(timezone.utc) - datetime.fromisoformat(recorded["at"].replace("Z", "+00:00"))).total_seconds()
    except (KeyError, ValueError):
        return None
    if age > VAULT_DOCTOR_MARKER_TTL_SECONDS:
        return None
    return recorded


def cmd_vault_doctor(project=None, vault=None, dry_run=False, repair=False, exclude_notes=True):
    # AC-21: missing Obsidian is a steady WARNING, never a blocking exit -- the file vault
    # (docs/notas/, plain git-tracked markdown) works with or without a GUI to browse it in.
    if not shutil.which("obsidian"):
        print("VAULT_DOCTOR_WARNING obsidian no está instalado — el vault de archivos sigue funcionando igual; instalalo con --tools-install obsidian si querés navegarlo con la app")
    if project is None:
        if repair:
            print("VAULT_DOCTOR_REPAIR_REFUSED reason=no-project — --repair exige --project, nunca headless/generico")
            return 1
        resolved_vault = _resolve_vault(vault)
        if resolved_vault is None:
            print("VAULT_NOT_FOUND: no hay vault configurado — corré --vault-init o pasá --vault")
            return 2
        for row in vault_doctor_report(resolved_vault):
            if row["project"] is not None:
                print(f"VAULT_DOCTOR project={row['project']} topology={row['topology']} health={row['health']}")
            else:
                print(f"VAULT_DOCTOR_UNREGISTERED vault_path={row['vault_path']} health=unregistered")
        return 0

    project_path = Path(project).expanduser().resolve()
    resolved_vault = find_vault(project_path, vault)
    if resolved_vault is None:
        print("VAULT_NOT_FOUND: no hay obsidian/00 - INICIO.md en los ancestros; corré --vault-init o pasá --vault")
        return 2
    vault_side, refusal = _vault_side_for_doctor(resolved_vault, project_path)
    if vault_side is None:
        print(f"VAULT_DOCTOR_REPAIR_REFUSED reason={refusal}")
        return 1
    plan = vault_migration_plan(project_path, vault_side)
    marker = _vault_doctor_marker_path(project_path)

    if repair:
        if plan["action"] not in ("pure-move", "merge"):
            print(f"VAULT_DOCTOR_REPAIR_REFUSED action={plan['action']} — nada para reparar de forma segura; corré --dry-run para ver el detalle")
            return 1
        if not marker.exists():
            print("VAULT_DOCTOR_REPAIR_REFUSED reason=no-dry-run — corré --vault-doctor --project ... --dry-run primero")
            return 1
        # SEC-008: consumes (unlinks) the marker before trusting its content -- single-use
        # either way, and a corrupt/expired/absent marker degrades to a clean refusal instead
        # of an uncaught JSONDecodeError.
        recorded = _read_vault_doctor_marker(marker)
        if recorded is None:
            print("VAULT_DOCTOR_REPAIR_REFUSED reason=marker-invalid-or-expired — corré --vault-doctor --project ... --dry-run de nuevo")
            return 1
        if recorded.get("fingerprint") != _plan_fingerprint(plan):
            print("VAULT_DOCTOR_REPAIR_REFUSED reason=plan-changed-since-dry-run — el estado del disco cambió, corré --dry-run de nuevo")
            return 1
        rc = apply_vault_migration(
            project_path, resolved_vault, vault_side, plan, exclude_notes=recorded.get("exclude_notes", True),
        )
        if rc == 0:
            print(f"VAULT_DOCTOR_REPAIRED project={project_path} action={plan['action']}")
        return rc

    if dry_run:
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.write_text(json.dumps({
            "fingerprint": _plan_fingerprint(plan),
            "exclude_notes": bool(exclude_notes),
            "at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        }))
        print(f"VAULT_DOCTOR_PLAN project={project_path} action={plan['action']}")
        for key in ("files", "already_present", "conflicts"):
            if plan.get(key):
                print(f"  {key}: {', '.join(plan[key])}")
        return 0

    print(f"VAULT_DOCTOR project={project_path} action={plan['action']}")
    return 0


# context_pack.py: --context (AC-18, read-only) leaf helpers. `_resolve_within` is also used
# above by `apply_vault_migration`. `cmd_context` itself stays defined here (not in
# context_pack.py): it calls `find_vault`/`read_vault_registry`, and `find_vault` must stay in
# this file too (see context_pack.py's own module docstring for why moving it would be a
# circular import).
from context_pack import (  # noqa: E402
    CONTEXT_BYTE_CAP, CONTEXT_SECTION_BYTE_CAP, _RESERVED_VAULT_CHILDREN, _cap_text_bytes,
    _read_capped, _extract_section, _resolve_company_dir, _UNTRUSTED_OPEN, _UNTRUSTED_CLOSE,
    _mark_untrusted, _resolve_within,
)


def cmd_context(project=None, as_json=False):
    """Read-only (ORQ-1/AC-18/AC-19). Degrades honestly at every step, never crashes, never
    fabricates: no vault -> VAULT_NOT_FOUND-shaped result; no company dir -> hub-only; no project
    note -> reported absent (null), not invented. NEVER reads credential surfaces -- it touches
    exactly four paths (hub, company contexto.md, the project's own note, nothing else) and none
    of them is under a CLI's auth store.
    """
    project_path = Path(project or ".").expanduser().resolve()
    vault = find_vault(project_path)
    if vault is None:
        result = {"hub": None, "company": None, "project": None, "pending": None}
        if as_json:
            print(json.dumps(result))
        else:
            print("CONTEXT_VAULT_NOT_FOUND")
        return 0
    hub = _read_capped(vault / VAULT_HUB)
    company_dir = _resolve_company_dir(vault)
    company = _read_capped(company_dir / "contexto.md") if company_dir else None
    registry = read_vault_registry(vault)
    entry = registry.get(str(project_path))
    if entry and entry.get("topology") == "private":
        # SEC-002: the registry is an externally-writable, Syncthing-synced file. A
        # `vault_path` pointing outside the vault, or a note file that is itself a symlink
        # escaping it, must never reach _read_capped -- that's how a fake `vault_path` or a
        # planted symlink turned this read-only, credential-surface-excluded command into a
        # generic file-exfiltration primitive (demonstrated against a fake auth.json).
        candidate = Path(entry["vault_path"]) / "00 - Proyecto.md"
        project_note_path = _resolve_within(candidate, vault)
    else:
        project_note_path = project_path / "docs" / "notas" / "00 - Proyecto.md"
    project_note = _read_capped(project_note_path) if project_note_path else None
    # SEC-006: `pending` is extracted from the RAW note, before marking -- otherwise the
    # marker text itself would leak into the extracted section, or get extracted twice.
    pending = _extract_section(project_note, "## Qué falta")
    result = {
        "hub": _mark_untrusted(hub), "company": _mark_untrusted(company),
        "project": _mark_untrusted(project_note), "pending": _mark_untrusted(pending),
    }
    if as_json:
        print(json.dumps(result))
        return 0
    print("CONTEXT_OK" if hub is not None else "CONTEXT_HUB_ABSENT")
    for label, value in result.items():
        if value:
            print(f"--- {label} ---")
            print(value)
    return 0


# graph_wrapper.py: --graph, a thin subprocess wrapper (its own `cmd_graph`, distinct from
# feature_state_lib/graph.py's internal `cmd_graph` used by feature-state.py itself).
from graph_wrapper import cmd_graph as _graph_wrapper_cmd_graph  # noqa: E402


def cmd_graph(feature_ids=None, project=None, out=None):
    return _graph_wrapper_cmd_graph(feature_ids, project, out, root=ROOT)


_VAULT_INTRO = "El vault de empresa junta las notas de todos tus proyectos en un solo grafo Obsidian."


def vault_menu():
    # F-03: the intro line travels as `header=` into every picker's own frame instead of being
    # print()ed to the normal screen right before the FIRST picker's alternate screen erases it
    # (AC-25/AC-26 nested composition: a single `TerminalSession` wraps all 3 chained pickers so
    # none of them re-swaps the alternate screen for what is one interaction, not three).
    style = {"color": color, "bold": bold, "dim": dim}
    with tui.TerminalSession():
        target_result = tui.run_picker(
            (), freetext_allowed=True, style=style, header=_VAULT_INTRO,
            prompt="Directorio de la empresa (ej ~/iey; Esc vuelve):",
        )
        target = target_result.value.strip() if isinstance(target_result, tui.FreeText) else ""
        if not target:
            return
        # cmd_vault_init prints/creates seed files -- suspend so it runs in cooked mode
        # (AC-26) rather than under the still-active alternate screen the pickers share.
        with tui.suspend_terminal():
            cmd_vault_init(target)
        project_result = tui.run_picker(
            (), freetext_allowed=True, style=style, header=_VAULT_INTRO,
            prompt="¿Linkear un proyecto ahora? (path; Esc salta):",
        )
        project = project_result.value.strip() if isinstance(project_result, tui.FreeText) else ""
        if not project:
            return
        private_choice = tui.run_picker(
            ("No — notas en el repo (hybrid)", "Sí — notas solo en el vault (privado)"),
            style=style, header=_VAULT_INTRO,
            prompt="¿Privado? Las notas privadas quedan FUERA del git del proyecto:",
        )
        # F-07: cancelling this step (Esc/Ctrl-C/EOF) must never fall through to a default --
        # same "cancel never reaches a mutating command" contract every other chained picker in
        # this module keeps (mcp_menu's action/harness steps).
        if not isinstance(private_choice, tui.Selected):
            return
        private = private_choice.index == 1
    cmd_vault_link(project, str(Path(target).expanduser() / "obsidian"), private)


# ------------------------------------------------------------------- plugins

def claude_settings_path():
    return Path.home() / ".claude/settings.json"


def _plugins_data():
    """AC-28: the data cmd_plugins()/plugins_menu() both render -- [(name, enabled), ...]."""
    return sorted(read_json(claude_settings_path()).get("enabledPlugins", {}).items())


def cmd_plugins():
    plugins = _plugins_data()
    if not plugins:
        print("PLUGINS_NONE")
    for name, enabled in plugins:
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


_MCP_ACTIONS = ("Agregar", "Encender", "Apagar", "Remover")


def mcp_menu():
    """AC-24/AC-26/AC-29: three chained pickers instead of three raw `input()` lines --
    server (free-text ALLOWED: a name outside the catalog is still valid for --mcp-remove-style
    cleanup, same as the old input() line accepted anything), then action and harness, both
    CLOSED enums with no free text at all. Closing the enums is what "mcp_menu's free-text
    inputs validated" (AC-29) means in practice: action/harness can no longer be a garbage
    string `cmd_mcp_toggle` silently ignores -- they are picked, not typed. There is no raw
    `input()` left in this function at all, so the AC-26 terminal-handoff concern that applied
    to the old input() lines doesn't even arise here anymore; every step is its own picker.
    """
    data = _mcp_data()
    targets = mcp_targets()
    header_lines = [f"harnesses detectados: {', '.join(targets)}"]
    for name, states in data:
        rendered = ", ".join(f"{h}:{s}" for h, s in states)
        header_lines.append(f"  {name:<12} {rendered}")
    header = "\n".join(header_lines)
    style = {"color": color, "bold": bold, "dim": dim}
    catalog = [name for name, _ in data]
    # F-03: `header` carries this context into EVERY chained picker's own frame (it stays
    # visible across all 3 steps, not just the first), and the whole chain shares ONE
    # `TerminalSession` so picking "Server" -> "Acción" -> "Harness" swaps the alternate screen
    # once for the interaction, not three times.
    with tui.TerminalSession():
        server_choice = tui.run_picker(catalog, freetext_allowed=True, style=style, header=header, prompt="Server:")
        if isinstance(server_choice, tui.Selected):
            name = catalog[server_choice.index]
        elif isinstance(server_choice, tui.FreeText):
            name = server_choice.value.strip()
        else:
            return
        if not name:
            return
        action_choice = tui.run_picker(_MCP_ACTIONS, style=style, header=header, prompt="Acción:")
        if not isinstance(action_choice, tui.Selected):
            return
        harness_options = ("Todos",) + tuple(targets)
        harness_choice = tui.run_picker(harness_options, style=style, header=header, prompt="Harness:")
        if not isinstance(harness_choice, tui.Selected):
            return
    harness = None if harness_choice.index == 0 else harness_options[harness_choice.index]
    action = _MCP_ACTIONS[action_choice.index]
    if action == "Agregar":
        cmd_mcp_add(name, harness)
    elif action == "Encender":
        cmd_mcp_toggle(name, harness, True)
    elif action == "Apagar":
        cmd_mcp_toggle(name, harness, False)
    elif action == "Remover":
        cmd_mcp_remove(name, harness)


def plugins_menu():
    # AC-29: human-readable text, never the raw machine format cmd_plugins() prints for
    # scripted callers -- rendered straight from _plugins_data(), not by shelling out to
    # cmd_plugins()'s own stdout.
    plugins = _plugins_data()
    if not plugins:
        print("(sin plugins instalados)")
        return
    items = [f"{name} — {'activado' if enabled else 'apagado'}" for name, enabled in plugins]
    choice = tui.run_picker(items, style={"color": color, "bold": bold, "dim": dim})
    if isinstance(choice, tui.Selected):
        name, enabled = plugins[choice.index]
        cmd_plugin_set(name, not enabled)


# ---------------------------------------------------------------------- menu

def cmd_scaffold(target: str | None) -> int:
    """Create only the P1 project marker, generic state helpers, and stable identity."""
    root = Path(target or os.getcwd()).resolve()
    created: list[str] = []
    conflicts: list[str] = []
    skips: list[str] = []
    features = root / "ai/state/features"
    if not features.exists():
        features.mkdir(parents=True)
        created.append("ai/state/features")
    elif not _real_directory(features):
        print("SCAFFOLD_CONFLICT path=ai/state/features reason=not_directory")
        print("SCAFFOLD_CONFLICTS n=1")
        return 1
    else:
        skips.append("ai/state/features")
    template_dir = ROOT / "PROYECTO/ai/scripts"
    feature_state_lib_dir = template_dir / "feature_state_lib"
    feature_state_lib_names = tuple(
        f"feature_state_lib/{path.name}"
        for path in sorted(feature_state_lib_dir.glob("*.py"))
    ) if feature_state_lib_dir.is_dir() else ()
    for name in ("feature-state.py", *feature_state_lib_names, "check-owned-paths.py"):
        source, destination = template_dir / name, root / "ai/scripts" / name
        if not source.is_file():
            conflicts.append(f"ai/scripts/{name}")
            print(f"SCAFFOLD_CONFLICT path=ai/scripts/{name} reason=template_missing")
            continue
        try:
            destination.lstat()
        except FileNotFoundError:
            pass
        except OSError:
            conflicts.append(f"ai/scripts/{name}")
            print(f"SCAFFOLD_CONFLICT path=ai/scripts/{name} reason=unreadable")
            continue
        else:
            existing = _safe_read(destination, limit=_MAX_FEATURE_BYTES)
            source_bytes = source.read_bytes()
            if existing != source_bytes:
                conflicts.append(f"ai/scripts/{name}")
                print(f"SCAFFOLD_CONFLICT path=ai/scripts/{name} reason=differs")
            else:
                skips.append(f"ai/scripts/{name}")
            continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(source.read_bytes())
        destination.chmod(0o755)
        created.append(f"ai/scripts/{name}")
    identity = root / "ai/state/project.json"
    try:
        identity.lstat()
    except FileNotFoundError:
        identity_exists = False
    except OSError:
        identity_exists = True
    else:
        identity_exists = True
    if identity_exists:
        try:
            key = project_key_for(root, require_persisted=True)
        except ValueError:
            conflicts.append("ai/state/project.json")
            print("SCAFFOLD_CONFLICT path=ai/state/project.json reason=invalid_identity")
            key = None
        else:
            skips.append("ai/state/project.json")
    else:
        key = "proj1_" + secrets.token_hex(16)
        payload = {"schema": 1, "project_key": key, "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")}
        identity.write_text(json.dumps(payload, separators=(",", ":")) + "\n", encoding="utf-8")
        identity.chmod(0o644)
        created.append("ai/state/project.json")
    if conflicts:
        print(f"SCAFFOLD_CONFLICTS n={len(conflicts)}")
        return 1
    for path in created:
        print(f"SCAFFOLD_CREATED path={path}")
    for path in skips:
        print(f"SCAFFOLD_SKIP path={path}")
    _scaffold_attempt_obsidian_once(root)
    print(f"SCAFFOLD_OK project={root} project_key={key}")
    return 0


OBSIDIAN_INSTALL_MARKER = "obsidian-install.json"


def _scaffold_attempt_obsidian_once(root):
    """AC-21: attempt the Obsidian install exactly once per project, ever — never inside a
    retry loop, and never letting the outcome (ok/declined/manual/no-method) propagate as a
    `--scaffold` failure. The file vault (docs/notas/, git-tracked markdown) works with or
    without Obsidian installed; this only affects whether there's a GUI to browse it in.
    """
    marker = root / "ai/state" / OBSIDIAN_INSTALL_MARKER
    if marker.exists():
        return  # already attempted (any outcome) -- never re-prompt on a later --scaffold
    if shutil.which("obsidian"):
        outcome = "already-installed"
    else:
        try:
            rc = cmd_tools_install("obsidian", dry=False, yes=False)
        except Exception:
            rc = 1
        outcome = "ok" if rc == 0 else "declined"
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text(json.dumps({
        "outcome": outcome,
        "at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }))


def cmd_routing_migrate() -> int:
    try:
        key = project_key_for(ROOT, require_persisted=True)
        # Production keeps ADR-0005's fixed store root. The existing seam is
        # used only by hermetic tests, so migration can be exercised safely.
        rows, backup, moved_from, moved_to = _routing_store().migrate(key)
    except (ValueError, routing.RoutingError, OSError) as exc:
        print("ROUTING_MIGRATE_FAILED", file=sys.stderr)
        # 007 AC-05: a database that genuinely cannot be migrated says which object
        # diverged.  Read with getattr so this file never imports the store's class, and
        # printed after the reason code so the first line and the exit code are unchanged.
        detail = getattr(exc, "schema_diagnostic", None)
        if detail:
            print(detail, file=sys.stderr)
        return 2
    # 007 AC-14: the observed versions, not a hardcoded pair. ADR-0008 D8 pinned the literal
    # `from=4 to=5`; ADR-0010 D4 supersedes that clause and only that clause. The format is
    # unchanged — same keys, same order — because once schema 6 exists `from=4 to=5` is a
    # false statement rather than a formatting choice.
    print(f"ROUTING_MIGRATE_OK from={moved_from} to={moved_to} rows={rows} backup={backup}")
    return 0


def run_tty(command):
    """Foreground child with inherited TTY: sudo/login prompts must reach the user. AC-26:
    wrapped with `tui.suspend_terminal()` so a subprocess launched while a picker session is
    still active (nested composition) gets cooked mode for its prompts too -- a no-op under
    the normal per-call picker sessions this module uses today, where control is already back
    in cooked mode by the time any menu branch reaches here."""
    with tui.suspend_terminal():
        return subprocess.run(command, check=False).returncode


DRIFT_BADGE = {
    "ok": lambda: color("OK", "32"),
    "stale": lambda: color("DESACTUALIZADO", "33"),
    "unknown": lambda: "?",
}


# AC-24/AC-29: the single source of truth for the main menu's order -- Vault sits right
# before Salir (closing the menu-debt finding: the old numbered grid had it AFTER Salir, at
# index 9 while Salir was 8). Arrow-key navigation makes the bracketed numbers themselves
# cosmetic history, not a contract -- README.md/INSTALACION.md (AC-30) describe the selector,
# not literal [N] numbers.
MENU_ITEMS = (
    "📦 Instalar / Reparar",
    "🔄 Actualizar",
    "🧠 Modelos",
    "🧰 Herramientas (CLIs)",
    "🔌 MCPs",
    "🧩 Plugins Claude Code",
    "📊 Estado",
    "🗒  Vault Obsidian",
    "⏻  Salir",
)


def menu():
    print()
    banner()
    if first_run():
        print()
        print(bold(f"📖 Primera vez acá → leé README.md (sección {platform_label()}) para saber qué esperar."))
        write_app_config(auto_update=True)
    print(dim("· chequeando updates…"))
    update_badge = launch_update_check()
    # Drift regenerates a full staging (~2 s): cache it and refresh only after
    # actions that can change it, instead of on every redraw.
    drift = drift_state()
    style = {"color": color, "bold": bold, "dim": dim}
    while True:
        # F-03: this "=== SET-AGENTS sha === / drift: ... | update: ..." banner used to be
        # print()ed to the normal screen right before `run_picker` switched to the alternate
        # screen and cleared it -- invisible exactly while the user is choosing. It now also
        # travels as the menu picker's `header=`, so it stays on screen inside the picker's own
        # frame too.
        menu_header = (
            f"=== SET-AGENTS {short_sha()} ===\n"
            f"drift: {DRIFT_BADGE[drift]()} | update: {color(update_badge, '36')} | "
            + dim(f"auto-update: {'on' if auto_update_enabled() else 'off'}")
        )
        print()
        print(menu_header)
        # AC-29: Esc/Ctrl-C/EOF resolve to `None` INSIDE run_picker (never a raised
        # EOFError/KeyboardInterrupt reaching here) -- treated the same as picking Salir.
        choice = tui.run_picker(MENU_ITEMS, style=style, header=menu_header)
        if not isinstance(choice, tui.Selected):
            return 0
        index = choice.index
        if index == 0:
            if run_tty([str(ROOT / "install.sh")]) != 0:
                print(color("El instalador terminó con error — revisá la salida de arriba.", "31"))
            drift = drift_state()
        elif index == 1:
            if cmd_update() == 0:
                update_badge = "al día"
            drift = drift_state()
        elif index == 2:
            if run_tty([str(ROOT / "setup-models.sh")]) != 0:
                print(color("El wizard terminó con error — revisá la salida de arriba.", "31"))
            drift = drift_state()
        elif index == 3:
            tools_menu()
        elif index == 4:
            mcp_menu()
        elif index == 5:
            plugins_menu()
        elif index == 6:
            drift = drift_state()
            status_data = _status_data(rows=True)
            print(_status_machine_line(status_data))
            print()
            status_lines = _status_table_lines(status_data)
            for line in status_lines:
                print(line)
            # F-03: same table, as the toggle picker's header -- visible while deciding, not
            # only before the alternate screen clears it.
            status_header = "\n".join([_status_machine_line(status_data), ""] + status_lines)
            toggle = tui.run_picker(("Togglear auto-update", "Volver"), style=style, header=status_header)
            if isinstance(toggle, tui.Selected) and toggle.index == 0:
                set_auto_update(not auto_update_enabled())
        elif index == 7:
            vault_menu()
        elif index == 8:
            return 0


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
    parser.add_argument("--route-quota-exhausted", metavar="RUN_ID")
    parser.add_argument("--quota-failover-e2e", action="store_true",
                        help="AC-06 live gate; bloquea hasta verificar una suscripción agotada controlada")
    parser.add_argument("--quota-error", metavar="JSON")
    parser.add_argument("--routing-open-runs", action="store_true")
    parser.add_argument("--routing-recent-writers", action="store_true")
    parser.add_argument("--routing-migrate", action="store_true", help="migra explícitamente la DB de routing al schema actual")
    parser.add_argument("--project", metavar="DIR", help="ancla explícita del proyecto para ruteo")
    parser.add_argument("--scaffold", nargs="?", metavar="DIR", const="", help="crea el estado portable mínimo del proyecto")
    parser.add_argument("--fresh-probes", action="store_true", help="con --route-decide: saltea el cache de probes")
    parser.add_argument("--latency-ms", type=int, default=None, help="con --route-terminal: latencia observada")
    parser.add_argument("--usage", metavar="JSON", help="con --route-terminal: uso/costo del spawn")
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
    parser.add_argument("--context", action="store_true", help="hub + contexto de empresa + nota del proyecto + qué falta (solo lectura)")
    parser.add_argument("--graph", action="store_true", help="grafo de ejecución (mermaid): findings, reviews, verificaciones, repairs, blockers (solo lectura)")
    parser.add_argument("--feature-id", action="append", metavar="ID", help="con --graph: limita a esta feature (repetible; sin ninguna, todas)")
    parser.add_argument("--out", metavar="FILE", help="con --graph: escribe el mermaid en FILE en vez de stdout")
    parser.add_argument("--vault-doctor", action="store_true", help="estado del vault: symlinks sanos, drift, no-registrados (report-only)")
    parser.add_argument("--repair", action="store_true", help="con --vault-doctor --project: aplica lo que el --dry-run inmediatamente anterior confirmó")
    # SEC-005: DEC-5/AC-16 say notes exclusion is "written/kept" as part of migration, full
    # stop -- no opt-in mentioned. An --exclude-notes flag defaulting to False inverted that:
    # a real migration left client notes untracked-but-visible in git until the caller
    # remembered the flag. Privacy is now the default; --include-notes is the explicit opt-out.
    parser.add_argument("--include-notes", action="store_true", help="con --vault-doctor --project --dry-run: docs/notas queda DENTRO del git del proyecto tras migrar (opt-out explícito; por defecto DEC-5 lo excluye)")
    parser.add_argument("--private", action="store_true",
                        help="con --vault-link: las notas viven en el vault y el repo queda con un symlink excluido de git")
    parser.add_argument("--company", metavar="NAME")
    # 014-model-preference-policy AC-02: --provider is repeatable-ordered, the same idiom
    # --feature-id already establishes above (order of appearance IS the ranked list).
    parser.add_argument("--model-preference-set", metavar="CLASS", choices=_MODEL_PREFERENCE_CLASSES,
                        help="escribe [preference].CLASS en model-preference.toml; combinar con --provider (repetible, ordenado)")
    parser.add_argument("--provider", action="append", metavar="NAME",
                        help="con --model-preference-set: proveedor, repetible, el orden en la línea de comando es la preferencia")
    parser.add_argument("--model-preference-role-override", nargs=2, metavar=("ROLE", "CLASS"),
                        help="escribe [role_override].ROLE = CLASS en model-preference.toml")
    parser.add_argument("--model-preference-show", action="store_true", help="lee model-preference.toml (solo lectura)")
    args = parser.parse_args()

    # This gate is intentionally outside the ordinary routing modes.  It has no
    # credentials or mock fallback and performs no durable mutation while blocked.
    if args.quota_failover_e2e:
        return cmd_quota_failover_e2e()

    routing_human = sys.stdout.isatty() and not args.json
    # Routing modes are total: JSON is a rendering modifier, per-mode modifiers are the only
    # exemptions (--fresh-probes with decide, --latency-ms with terminal), and no other argument —
    # operational command or modifier — may be silently combined with a routing mode. Comparing every
    # parsed argument against its parser default keeps this exhaustive when new flags are added.
    # F08/N11: presence is checked with `is not None` for value-bearing flags, NEVER truthiness —
    # `--route-decide ""` is a present-but-EMPTY string, which is falsy and would otherwise fall
    # straight through every mode check into the interactive menu/help instead of failing closed.
    _mode_flags = (args.route_explain is not None, args.routing_report, args.route_decide is not None,
                   args.route_dispatched is not None, args.route_terminal is not None, args.route_quota_exhausted is not None,
                   args.routing_open_runs, args.routing_recent_writers, args.routing_migrate)
    routing_mode = any(_mode_flags)
    _routing_args = {"json", "route_explain", "routing_report", "route_decide", "route_dispatched",
                     "route_terminal", "route_quota_exhausted", "quota_error", "routing_open_runs", "routing_recent_writers",
                     "routing_migrate", "fresh_probes", "latency_ms", "usage", "project"}
    other_mode = any(value != parser.get_default(name)
                     for name, value in vars(args).items() if name not in _routing_args)
    modifier_misuse = (args.fresh_probes and args.route_decide is None) or \
                      (args.latency_ms is not None and args.route_terminal is None and args.route_quota_exhausted is None) or \
                      (args.usage is not None and args.route_terminal is None and args.route_quota_exhausted is None) or \
                      (args.quota_error is not None and args.route_quota_exhausted is None) or \
                      (args.route_quota_exhausted is not None and args.quota_error is None)
    if (sum(_mode_flags) > 1) or (routing_mode and other_mode) or modifier_misuse:
        _routing_output(routing.cli_envelope(False, "routing", {}, (), ("ROUTING_INPUT_INVALID",)), routing_human)
        return 2
    # SEC-001: --context is the third sanctioned read-only channel (coord_policy.SAFE_ARGV,
    # generate.py's OpenCode glob) and, like the routing modes above, must be total. Without
    # this, dispatch below is plain flag-precedence, so `--context --scaffold X` (or --update
    # --yes, --tools-install, --vault-doctor --repair, ...) reached its handler untouched --
    # demonstrated writing real files through the allowlisted argv shape.
    _context_args = {"context", "project", "json"}
    if args.context and any(value != parser.get_default(name)
                            for name, value in vars(args).items() if name not in _context_args):
        _routing_output(routing.cli_envelope(False, "context", {}, (), ("CONTEXT_INPUT_INVALID",)), routing_human)
        return 2
    if args.scaffold is not None:
        return cmd_scaffold(args.scaffold or None)
    global PROJECT_ROOT, PROJECT_KEY, ROUTING_WARNINGS
    if routing_mode and not args.routing_migrate:
        try:
            PROJECT_ROOT = resolve_project_root(Path.cwd(), args.project)
            if PROJECT_ROOT is None:
                if args.route_decide is not None:
                    _routing_output(routing.cli_envelope(False, "route-decide", {}, ("PROJECT_ROOT_UNRESOLVED",), ("ROUTING_UNAVAILABLE",)), routing_human)
                else:
                    _routing_output(routing.cli_envelope(False, "routing", {}, ("PROJECT_ROOT_UNRESOLVED",), ("ROUTING_UNAVAILABLE",)), routing_human)
                return 1
            PROJECT_KEY = project_key_for(PROJECT_ROOT)
            os.environ["SET_AGENTS_PROJECT"] = str(PROJECT_ROOT)
            # Schema migration is operator-driven.  The probe is read-only and
            # merely adds a stable diagnosis to the normal fail-closed envelope.
            ROUTING_WARNINGS = (("ROUTING_SCHEMA_MIGRATION_REQUIRED",)
                                if _routing_store().migration_required() else ())
        except ProjectIdentityError:
            _routing_output(routing.cli_envelope(False, "routing", {}, ("PROJECT_IDENTITY_INVALID",),
                                                  ("ROUTING_UNAVAILABLE",)), routing_human)
            return 1
        except ValueError:
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
        return cmd_route_terminal(args.route_terminal[0], args.route_terminal[1], args.latency_ms,
                                  args.usage, human=routing_human)
    if args.route_quota_exhausted is not None:
        return cmd_route_quota_exhausted(args.route_quota_exhausted, args.quota_error, args.latency_ms,
                                         args.usage, human=routing_human)
    if args.routing_open_runs:
        return cmd_routing_open_runs(human=routing_human)
    if args.routing_recent_writers:
        return cmd_routing_recent_writers(human=routing_human)
    if args.routing_migrate:
        return cmd_routing_migrate()
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
    if args.model_preference_show:
        try:
            return cmd_model_preference_show()
        except ModelPreferenceError as exc:
            print(f"model-preference: {exc}", file=sys.stderr)
            return 2
    # 014-model-preference-policy AC-02, round-3 R3-F-04(b)/(c): --provider is co-required
    # with --model-preference-set (an argparse-level rejection, not a silent ignore), and
    # a --model-preference-set with zero --provider is rejected before any write.
    if args.model_preference_set is not None or args.provider:
        if args.model_preference_set is None:
            print("model-preference: --provider requires --model-preference-set", file=sys.stderr)
            return 2
        if not args.provider:
            print("model-preference: --model-preference-set requires at least one --provider", file=sys.stderr)
            return 2
        if len(args.provider) != len(set(args.provider)):
            print("model-preference: duplicate --provider value", file=sys.stderr)
            return 2
        try:
            return cmd_model_preference_set(args.model_preference_set, args.provider)
        except ModelPreferenceError as exc:
            print(f"model-preference: {exc}", file=sys.stderr)
            return 2
    if args.model_preference_role_override:
        try:
            return cmd_model_preference_role_override(*args.model_preference_role_override)
        except ModelPreferenceError as exc:
            print(f"model-preference: {exc}", file=sys.stderr)
            return 2
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
    if args.vault_doctor:
        return cmd_vault_doctor(args.project, args.vault, args.dry_run, args.repair, not args.include_notes)
    if args.context:
        return cmd_context(args.project, args.json)
    if args.graph:
        return cmd_graph(args.feature_id, args.project, args.out)
    if not sys.stdin.isatty():
        parser.print_help()
        return 2
    return menu()


if __name__ == "__main__":
    raise SystemExit(main())
