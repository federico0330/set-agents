#!/usr/bin/env python3
"""Model routing source of truth: load, validate, and emit models.toml + roles.tsv.

roles.tsv holds structure only (role, mode, temperature, capability, duty);
models.toml declares subscriptions, the model catalog, and the model assigned
to each area (duty), with optional per-role overrides. The go-zen/zen/local
profiles survive as lanes of the opencode dimension.
"""

import csv
import json
import re
import sys
import tomllib
import os
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LANES = ("go-zen", "zen", "local")
PERMISSION_PROFILES = ("guarded", "yolo")
DUTY_ORDER = ("coord", "analysis", "docs", "implement", "gate", "audit", "judge", "release", "memory", "ops")
ROSTER_COLUMNS = {"role", "mode", "temperature", "capability", "duty"}
LEGACY_MODEL_COLUMNS = {"opencode_go", "opencode_zen", "opencode_local", "claude_model", "codex_model", "codex_effort"}
CAPABILITIES = {"coord-ro", "review-ro", "docs-rw", "factory-rw", "code-rw", "gate-ro", "release", "memory-rw", "run-ro"}
READ_ONLY = {"coord-ro", "review-ro"}
IMPLEMENT_DUTIES = {"implement"}
REVIEW_DUTIES = {"audit", "judge"}
AREA_FIELDS = ("claude", "codex", "codex_effort", "opencode")
# The one role-override field that is NOT an area field: a lane-aware tier table
# consumed only by load_role_tiers, never by resolve_role's base merge. Areas never
# declare it — only [roles.<role>] may.
TIER_FIELD = "tiers"
RUNTIMES = ("opencode", "claude-code", "codex", "pi")
MODEL_TIERS = ("fast", "balanced", "frontier")
ROUTING_PROVIDERS = {"openai-codex", "anthropic"}
# ADR-0029 (017 PKG-B2): providers eligible for SYNTHESIZED routes (probe-discovered,
# tier/family inferred). Distinct from ROUTING_PROVIDERS on purpose — the curated
# allowlist stays closed (immutable contract "probeable, never routable, by 012 alone");
# this is the separate, opt-in surface that makes a discovered model routable.
DISCOVERABLE_PROVIDERS = {"openai-codex", "anthropic", "opencode-zen", "opencode-go"}
ROUTING_DEFAULTS = {
    "enabled_providers": ["openai-codex", "anthropic"], "xhigh_benchmarked": False,
    "discovered_providers": [],
    "max_enabled": False, "fallback_limit": 1, "single_writer": True,
    "sla": {"fast": {"checkpoint_minutes": 18, "cutoff_minutes": 20, "ceiling_minutes": 30}},
    "budgets": {"direct_spawns": 0, "fast_spawns": 1, "scoped_spawns": 4,
                "feature_spawns_per_package": 12, "incident_spawns": 2},
}
# Which subscription a resolved opencode model consumes, by provider prefix.
# Extendable per repo via the optional [providers] table in models.toml.
SUBSCRIPTION_BY_PREFIX = {
    "openai": "openai",
    "opencode": "zen",
    "opencode-go": "zen",
    "anthropic": "anthropic",
    "ollama": "ollama",
}
OPENCODE_MODEL_RE = re.compile(r"[a-z0-9][a-z0-9-]*/[A-Za-z0-9][A-Za-z0-9._:-]*")
# Single source of truth for the repo-managed MCP servers (installer smoke
# check, drift, and the set-agents MCP catalog all import this).
MANAGED_MCP = ("engram", "context7", "playwright", "brave-cdp")
_OPENCODE_FAMILY_SUFFIX = re.compile(r"(?:-mini|-flash-free|-code-free)$")

EMIT_HEADER = (
    "# models.toml — model routing source of truth (subscriptions, areas, role overrides).\n"
    "# Edit by hand or via ./setup-models.sh; the wizard rewrites this file\n"
    "# deterministically and does not preserve standalone comments.\n"
)


class ModelsError(ValueError):
    pass


def active_profile():
    """Per-machine lane selection; untracked, so a fresh clone defaults to go-zen."""
    try:
        return (ROOT / "active-profile").read_text().strip() or "go-zen"
    except OSError:
        return "go-zen"


def die(message):
    raise ModelsError(message)


# --------------------------------------------------------------------- load

def load_roster(roles_path=None):
    """Structure-only roster. Model routing lives in models.toml."""
    path = Path(roles_path or ROOT / "roles.tsv")
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        header = set(reader.fieldnames or ())
        if header & LEGACY_MODEL_COLUMNS:
            die(
                "roles.tsv still has model columns — this repo migrated model routing "
                "to models.toml (run git pull, or see COMO-CAMBIAR-MODELO.md)"
            )
        if header != ROSTER_COLUMNS:
            die("roles.tsv has an invalid header")
        roles = list(reader)
    names = [row["role"] for row in roles]
    if len(names) != len(set(names)):
        die("roles.tsv contains duplicate roles")
    for row in roles:
        if row["capability"] not in CAPABILITIES:
            die(f"{row['role']}: invalid capability {row['capability']}")
        if row["mode"] not in {"primary", "subagent"}:
            die(f"{row['role']}: invalid mode")
        if row["duty"] in REVIEW_DUTIES and row["capability"] != "review-ro":
            die(f"separation violation: {row['role']} reviews with mutating capability {row['capability']}")
        if row["duty"] == "implement" and row["capability"] != "code-rw":
            die(f"separation violation: {row['role']} implements without code-rw")
    return roles


def load_config(models_path=None):
    path = Path(models_path or ROOT / "models.toml")
    config = tomllib.loads(path.read_text())
    schema = config.get("schema")
    if schema not in (1, 2):
        die("models.toml: unsupported schema (expected schema = 1 or 2)")
    for section in ("subscriptions", "catalog", "session", "areas"):
        if not isinstance(config.get(section), dict) or not config[section]:
            die(f"models.toml: missing or empty [{section}]")
    for key in ("claude", "codex", "codex_effort"):
        values = config["catalog"].get(key)
        if not isinstance(values, list) or not values or not all(isinstance(item, str) and item for item in values) or len(values) != len(set(values)):
            die(f"models.toml: [catalog].{key} must be a non-empty list of strings")
    # 012 discovered-inventory AC-04: optional declared allowlist ceiling for the two
    # probeable-only OpenCode-lane providers (routing_core/catalog.py consumes these via
    # _configured_models; absent entirely is valid — a repo with neither subscription
    # simply never populates them, and probe_inventory then finds nothing configured).
    for key in ("opencode_zen", "opencode_go"):
        values = config["catalog"].get(key)
        if values is not None and (not isinstance(values, list) or not values
                                    or not all(isinstance(item, str) and item for item in values)
                                    or len(values) != len(set(values))):
            die(f"models.toml: [catalog].{key} must be a non-empty list of strings")
    small = config["session"].get("opencode_small_model")
    if not isinstance(small, dict) or set(small) != set(LANES):
        die("models.toml: [session].opencode_small_model must cover exactly the lanes " + ", ".join(LANES))
    config.setdefault("families", {})
    config.setdefault("roles", {})
    config.setdefault("providers", {})
    permissions = config.setdefault("permissions", {})
    if not isinstance(permissions, dict):
        die("models.toml: [permissions] must be a table")
    for key in permissions:
        if key != "profile":
            die(f"models.toml: [permissions] has unknown field {key}")
    if permissions.get("profile") not in (None, *PERMISSION_PROFILES):
        die("models.toml: [permissions].profile must be one of " + ", ".join(PERMISSION_PROFILES))
    _normalize_schema2(config, schema)
    return config


def _table(config, name, defaults, allowed):
    value = config.get(name, {})
    if not isinstance(value, dict):
        die(f"models.toml: [{name}] must be a table")
    unknown = set(value) - set(allowed)
    if unknown:
        die(f"models.toml: [{name}] has unknown field {sorted(unknown)[0]}")
    config[name] = {**defaults, **value}


def _normalize_schema2(config, source_schema):
    """Normalize legacy input in memory; source files are never changed on load."""
    _table(config, "runtime", {"primary": "opencode", "fallbacks": []}, ("primary", "fallbacks"))
    runtime = config["runtime"]
    if not isinstance(runtime["primary"], str) or runtime["primary"] not in RUNTIMES:
        die("models.toml: [runtime].primary is invalid")
    if not isinstance(runtime["fallbacks"], list) or not all(isinstance(item, str) and item in RUNTIMES for item in runtime["fallbacks"]):
        die("models.toml: [runtime].fallbacks must be runtime IDs")
    if len(runtime["fallbacks"]) != len(set(runtime["fallbacks"])) or runtime["primary"] in runtime["fallbacks"]:
        die("models.toml: [runtime].fallbacks must be unique and exclude primary")
    orch = config.setdefault("orchestrator", {})
    if not isinstance(orch, dict):
        die("models.toml: [orchestrator] must be a table")
    if set(orch) - {"pi"}:
        die("models.toml: [orchestrator] has unknown field")
    pi = orch.get("pi", {})
    if not isinstance(pi, dict) or set(pi) - {"model", "effort"}:
        die("models.toml: [orchestrator.pi] has unknown field")
    orch["pi"] = {"model": "gpt-5.6", "effort": "medium", **pi}
    if orch["pi"]["model"] not in ("gpt-5.6", "gpt-5.6-sol") or orch["pi"]["effort"] != "medium":
        die("models.toml: [orchestrator.pi] requires gpt-5.6|gpt-5.6-sol at medium effort")
    # Authentication is an observed runtime fact, never inferred from a subscription flag.
    # Configuration can only prove that the catalog is capable of resolving Sol.
    if runtime["primary"] == "pi" and not ({"gpt-5.6", "gpt-5.6-sol"} & set(config["catalog"]["codex"])):
        die("models.toml: Pi primary requires a catalog Sol parent")
    _table(config, "routing", {k: v for k, v in ROUTING_DEFAULTS.items() if k not in ("sla", "budgets")},
           ("enabled_providers", "xhigh_benchmarked", "max_enabled", "fallback_limit", "single_writer", "sla", "budgets",
            "discovered_providers"))
    routing = config["routing"]
    if not isinstance(routing.get("sla", {}), dict) or set(routing.get("sla", {})) - {"fast"}:
        die("models.toml: [routing.sla] has unknown field")
    if not isinstance(routing.get("budgets", {}), dict) or set(routing.get("budgets", {})) - set(ROUTING_DEFAULTS["budgets"]):
        die("models.toml: [routing.budgets] has unknown field")
    routing["sla"] = {**ROUTING_DEFAULTS["sla"], **routing.get("sla", {})}
    routing["budgets"] = {**ROUTING_DEFAULTS["budgets"], **routing.get("budgets", {})}
    # ADR-0029: closed to the audited probe set; empty (the default) disables the
    # synthesized-routes path entirely — production behavior identical to pre-017.
    discovered = routing.get("discovered_providers", [])
    if (not isinstance(discovered, list) or len(discovered) != len(set(discovered))
            or not all(isinstance(x, str) and x in DISCOVERABLE_PROVIDERS for x in discovered)):
        die("models.toml: [routing].discovered_providers must be a unique list within the audited provider set")
    if (not isinstance(routing["enabled_providers"], list) or not routing["enabled_providers"] or not all(isinstance(x, str) and x in ROUTING_PROVIDERS for x in routing["enabled_providers"])
            or len(routing["enabled_providers"]) != len(set(routing["enabled_providers"]))
            or not isinstance(routing["xhigh_benchmarked"], bool) or routing["max_enabled"] is not False
            or not isinstance(routing["single_writer"], bool) or not isinstance(routing["fallback_limit"], int) or isinstance(routing["fallback_limit"], bool) or routing["fallback_limit"] != 1):
        die("models.toml: invalid [routing] values")
    fast = routing["sla"].get("fast")
    if not isinstance(fast, dict) or set(fast) != {"checkpoint_minutes", "cutoff_minutes", "ceiling_minutes"}:
        die("models.toml: [routing.sla.fast] is invalid")
    if (not all(isinstance(fast[x], int) and not isinstance(fast[x], bool) for x in fast)
            or [fast[x] for x in ("checkpoint_minutes", "cutoff_minutes", "ceiling_minutes")] != [18, 20, 30]):
        die("models.toml: [routing.sla.fast] must be 18/20/30")
    if (routing["budgets"] != ROUTING_DEFAULTS["budgets"] or not all(isinstance(v, int) and not isinstance(v, bool) for v in routing["budgets"].values())):
        die("models.toml: [routing.budgets] is invalid")
    # Keep this internal marker out of serialized configuration.
    config["_source_schema"] = source_schema


def permission_profile(models_path=None):
    """OpenCode permission posture: guarded (prompt-heavy) or yolo (hard denies only)."""
    return load_config(models_path)["permissions"].get("profile", "guarded")


# ADR-0029 (017 PKG-A1): provider→subscription map for probe-backed detection.
_PROVIDER_SUBSCRIPTION = {
    "openai-codex": "openai",
    "anthropic": "anthropic",
    "opencode-zen": "zen",
    "opencode-go": "zen",
}


def detect_subscriptions(config):
    """Probe-backed subscription detection (ADR-0029): which subscriptions this
    machine can actually use, derived from authenticated pairs. Lazy import (no
    routing_core dependency at module load), shared probe cache, and `None` on
    any failure — the caller treats that as "no probe info", never as "nothing".
    Never reads or returns credential material."""
    try:
        from routing_core.catalog import probe_inventory
        state = Path.home() / ".local/state/set-agentes"
        inventory = probe_inventory(config, cache_root=state)
    except Exception:
        return None
    return {
        _PROVIDER_SUBSCRIPTION[provider]
        for (_, provider), models in inventory.items()
        if models and provider in _PROVIDER_SUBSCRIPTION
    }


def auto_profile(config=None):
    """The lane is derived from the probe, never hand-picked (the old use-*.sh
    scripts are gone). Both opencode pairs live → go-zen; only opencode-zen →
    zen; probe fine but no opencode pair → local. None on probe failure — the
    caller keeps whatever active-profile already says and never dies."""
    try:
        from routing_core.catalog import probe_inventory
        cfg = config if config is not None else load_config()
        state = Path.home() / ".local/state/set-agentes"
        inventory = probe_inventory(cfg, cache_root=state)
    except Exception:
        return None
    live = {provider for (_, provider), models in inventory.items() if models}
    if "opencode-go" in live:
        return "go-zen"
    if "opencode-zen" in live:
        return "zen"
    return "local"


def subscription_of(model, config):
    prefix = model.split("/", 1)[0]
    providers = {**SUBSCRIPTION_BY_PREFIX, **config["providers"]}
    if prefix not in providers:
        die(f"unknown provider prefix '{prefix}' in {model} — add it to [providers] in models.toml")
    return providers[prefix]


def family(field, value, families):
    """Model family used by the implementer/reviewer separation doctrine."""
    if value in families:
        return families[value]
    if field == "opencode_model":
        return _OPENCODE_FAMILY_SUFFIX.sub("", value)
    if field == "codex_model":
        return value.removesuffix("-mini")
    return value


def resolve_role(row, config, profile):
    """Field-by-field merge: [roles.<role>] over [areas.<duty>]; opencode lane by lane."""
    area = config["areas"].get(row["duty"])
    if area is None:
        die(f"{row['role']}: no [areas.{row['duty']}] in models.toml")
    override = config["roles"].get(row["role"], {})
    for source, label, allow_tiers in ((area, f"areas.{row['duty']}", False), (override, f"roles.{row['role']}", True)):
        for key in source:
            if key == TIER_FIELD and allow_tiers:
                continue
            if key not in AREA_FIELDS:
                die(f"models.toml: [{label}] has unknown field {key}")
    lanes = {**area.get("opencode", {}), **override.get("opencode", {})}
    for lane_map, label in ((area.get("opencode", {}), f"areas.{row['duty']}"), (override.get("opencode", {}), f"roles.{row['role']}")):
        for lane in lane_map:
            if lane not in LANES:
                die(f"models.toml: [{label}].opencode has unknown lane {lane}")
    resolved = {
        "claude_model": override.get("claude", area.get("claude")),
        "codex_model": override.get("codex", area.get("codex")),
        "codex_effort": override.get("codex_effort", area.get("codex_effort")),
        "opencode_model": lanes.get(profile),
    }
    for key, value in resolved.items():
        if not value:
            die(f"{row['role']}: unresolved {key} for profile {profile} (area {row['duty']})")
    return resolved


def load_roles(profile, roles_path=None, models_path=None):
    """Full contract: roster + models.toml resolved and validated for one profile."""
    if profile not in LANES:
        die(f"unsupported profile: {profile}")
    roles = load_roster(roles_path)
    config = load_config(models_path)
    known = {row["role"] for row in roles}
    for name in config["roles"]:
        if name not in known:
            die(f"models.toml: [roles.{name}] does not match any role in roles.tsv")
    subscriptions = config["subscriptions"]
    catalog = config["catalog"]
    detected_subscriptions = None  # ADR-0029: lazily probed, only when an absent key is hit
    for row in roles:
        row.update(resolve_role(row, config, profile))
        if row["claude_model"] not in catalog["claude"]:
            die(f"{row['role']}: claude model {row['claude_model']} not in [catalog].claude")
        if row["codex_model"] not in catalog["codex"]:
            die(f"{row['role']}: codex model {row['codex_model']} not in [catalog].codex")
        if row["codex_effort"] not in catalog["codex_effort"]:
            die(f"{row['role']}: codex effort {row['codex_effort']} not in [catalog].codex_effort")
        if not OPENCODE_MODEL_RE.fullmatch(row["opencode_model"]):
            die(f"{row['role']}: invalid OpenCode model id")
        subscription = subscription_of(row["opencode_model"], config)
        if not subscriptions.get(subscription):
            # ADR-0029 tri-state (017 PKG-A1): an EXPLICIT `false` is curated intent and
            # still dies (the immutable contract). An ABSENT key means "auto": the probe
            # decides. Undetected (or probe unavailable) degrades to a WARN that keeps
            # the pin — the build never dies for a subscription nobody explicitly
            # disabled; live routing already excludes it as PROVIDER_UNAUTHENTICATED.
            # SET_AGENTS_STRICT_MODELS=1 restores the historical die for CI.
            if subscription in subscriptions or os.environ.get("SET_AGENTS_STRICT_MODELS") == "1":
                die(
                    f"{row['role']}: {row['opencode_model']} needs the '{subscription}' subscription, "
                    "which is inactive in models.toml — reassign it (./setup-models.sh) or re-enable the subscription"
                )
            if detected_subscriptions is None:
                detected_subscriptions = detect_subscriptions(config)
            if detected_subscriptions is None or subscription not in detected_subscriptions:
                print(
                    f"WARN degraded {row['role']}: {row['opencode_model']} necesita la suscripción "
                    f"'{subscription}' y el probe no la detectó en esta máquina — se mantiene el pin "
                    "(el routing en vivo la excluye como PROVIDER_UNAUTHENTICATED); si la diste de "
                    "baja a propósito, declarala false en models.toml o remapeá con ./setup-models.sh",
                    file=sys.stderr,
                )

    implementers = [r for r in roles if r["duty"] in IMPLEMENT_DUTIES]
    reviewers = [r for r in roles if r["duty"] in REVIEW_DUTIES]
    for field in ("opencode_model", "claude_model", "codex_model"):
        implementation_families = {family(field, r[field], config["families"]) for r in implementers}
        for reviewer in reviewers:
            if family(field, reviewer[field], config["families"]) in implementation_families:
                die(f"separation violation: {reviewer['role']} shares {field}={reviewer[field]} with implementation")
    if not any(r["duty"] == "judge" for r in roles):
        die("adversarial judge is required")
    return roles


def load_role_tiers(config, profile):
    """Per-role, OpenCode-lane tier tables: {role: {tier: opencode_model}}.

    A role with no [roles.<role>.tiers] table is absent from the result (base-only,
    one emitted agent). A role WITH a tiers table must cover the full closed
    vocabulary — fast, balanced, frontier — no partial fan-out. Each [roles.<role>.
    tiers.<tier>] declares exactly one field, `opencode`, a lane map covering every
    LANE (or an explicit "default" fallback). Every resolved model passes the SAME
    validation any other role's opencode_model passes: OPENCODE_MODEL_RE + an active
    subscription (subscription_of) — never a codex/claude catalog-list membership
    check, since tiers are an OpenCode-only surface with no claude/codex twin.
    """
    if profile not in LANES:
        die(f"unsupported profile: {profile}")
    subscriptions = config["subscriptions"]
    result = {}
    for role, override in config.get("roles", {}).items():
        if not isinstance(override, dict) or TIER_FIELD not in override:
            continue
        tiers = override[TIER_FIELD]
        if not isinstance(tiers, dict):
            die(f"models.toml: [roles.{role}.{TIER_FIELD}] must be a table")
        unknown = set(tiers) - set(MODEL_TIERS)
        if unknown:
            die(f"models.toml: [roles.{role}.{TIER_FIELD}] has unknown tier {sorted(unknown)[0]}")
        missing = set(MODEL_TIERS) - set(tiers)
        if missing:
            die(f"models.toml: [roles.{role}.{TIER_FIELD}] missing tier {sorted(missing)[0]}")
        resolved = {}
        for tier in MODEL_TIERS:
            label = f"roles.{role}.{TIER_FIELD}.{tier}"
            table = tiers[tier]
            if not isinstance(table, dict) or set(table) != {"opencode"}:
                die(f"models.toml: [{label}] must declare exactly 'opencode'")
            lane_map = table["opencode"]
            if not isinstance(lane_map, dict):
                die(f"models.toml: [{label}.opencode] must be a table")
            lane_unknown = set(lane_map) - set(LANES) - {"default"}
            if lane_unknown:
                die(f"models.toml: [{label}.opencode] has unknown lane {sorted(lane_unknown)[0]}")
            if profile in lane_map:
                model = lane_map[profile]
            elif "default" in lane_map:
                model = lane_map["default"]
            else:
                die(f"models.toml: [{label}.opencode] missing lane {profile} and no default")
            if not isinstance(model, str) or not model:
                die(f"models.toml: [{label}.opencode] lane {profile} must be a non-empty string")
            if not OPENCODE_MODEL_RE.fullmatch(model):
                die(f"{role}: invalid OpenCode tier model id for tier {tier}")
            subscription = subscription_of(model, config)
            if not subscriptions.get(subscription):
                die(
                    f"{role}: tier {tier} model {model} needs the '{subscription}' subscription, "
                    "which is inactive in models.toml — reassign it (./setup-models.sh) or re-enable the subscription"
                )
            resolved[tier] = model
        result[role] = resolved
    return result


def small_model(profile, models_path=None):
    return load_config(models_path)["session"]["opencode_small_model"][profile]


def codex_orchestrator(roles_path=None, models_path=None):
    """Session-level Codex model/effort: profile-independent orchestrator resolution."""
    config = load_config(models_path)
    for row in load_roster(roles_path):
        if row["role"] == "orchestrator":
            resolved = resolve_role(row, config, LANES[0])
            return resolved["codex_model"], resolved["codex_effort"]
    die("orchestrator row missing from roles.tsv")


# --------------------------------------------------------------------- emit

def _value(item):
    return json.dumps(item)


def _inline(mapping, keys):
    parts = [f"{_value(key)} = {_value(mapping[key])}" for key in keys if key in mapping]
    return "{ " + ", ".join(parts) + " }"


def emit(config):
    """Deterministic emitter for the fixed models.toml schema (load(emit(x)) == x)."""
    lines = [EMIT_HEADER + "schema = 2", ""]
    lines.append("[subscriptions]")
    for key in sorted(config["subscriptions"]):
        lines.append(f"{key} = {'true' if config['subscriptions'][key] else 'false'}")
    lines.append("")
    lines.append("[catalog]")
    for key in ("claude", "codex", "codex_effort"):
        values = ", ".join(_value(item) for item in sorted(config["catalog"][key]))
        lines.append(f"{key} = [{values}]")
    # 012 AC-04: optional, so only emitted when present — round-trips without inventing an
    # empty allowlist for a repo that never configured either OpenCode-lane provider.
    for key in ("opencode_zen", "opencode_go"):
        if key in config["catalog"]:
            values = ", ".join(_value(item) for item in sorted(config["catalog"][key]))
            lines.append(f"{key} = [{values}]")
    # ADR-0029: discovered-model vetoes ("provider:model" strings), preserved like the
    # allowlists above and for the same site-5 reason.
    if config["catalog"].get("exclude"):
        values = ", ".join(_value(item) for item in sorted(config["catalog"]["exclude"]))
        lines.append(f"exclude = [{values}]")
    if config.get("providers"):
        lines.append("")
        lines.append("[providers]")
        for key in sorted(config["providers"]):
            lines.append(f"{_value(key)} = {_value(config['providers'][key])}")
    if config.get("families"):
        lines.append("")
        lines.append("[families]")
        for key in sorted(config["families"]):
            lines.append(f"{_value(key)} = {_value(config['families'][key])}")
    lines.append("")
    lines.append("[session]")
    lines.append(f"opencode_small_model = {_inline(config['session']['opencode_small_model'], LANES)}")
    if config.get("permissions"):
        lines.append("")
        lines.append("[permissions]")
        for key in sorted(config["permissions"]):
            lines.append(f"{key} = {_value(config['permissions'][key])}")
    lines.extend(["", "[runtime]", f"primary = {_value(config['runtime']['primary'])}",
                  f"fallbacks = {_value(config['runtime']['fallbacks'])}", "", "[orchestrator.pi]"])
    lines.append(f"model = {_value(config['orchestrator']['pi']['model'])}")
    lines.append(f"effort = {_value(config['orchestrator']['pi']['effort'])}")
    lines.extend(["", "[routing]"])
    for key in ("enabled_providers", "xhigh_benchmarked", "max_enabled", "fallback_limit", "single_writer"):
        lines.append(f"{key} = {_value(config['routing'][key])}")
    # ADR-0029: preserved across re-emits (the "site 5" lesson from the opencode_zen/
    # opencode_go allowlists — a key the wizard drops on rewrite is data loss). Only
    # emitted when configured, so an untouched repo emits byte-identical output.
    if config["routing"].get("discovered_providers"):
        lines.append(f"discovered_providers = {_value(config['routing']['discovered_providers'])}")
    lines.extend(["", "[routing.sla.fast]"])
    for key in ("checkpoint_minutes", "cutoff_minutes", "ceiling_minutes"):
        lines.append(f"{key} = {config['routing']['sla']['fast'][key]}")
    lines.extend(["", "[routing.budgets]"])
    for key in ("direct_spawns", "fast_spawns", "scoped_spawns", "feature_spawns_per_package", "incident_spawns"):
        lines.append(f"{key} = {config['routing']['budgets'][key]}")
    duties = [d for d in DUTY_ORDER if d in config["areas"]]
    duties += sorted(set(config["areas"]) - set(duties))
    for duty in duties:
        area = config["areas"][duty]
        lines.append("")
        lines.append(f"[areas.{duty}]")
        for field in ("claude", "codex", "codex_effort"):
            if field in area:
                lines.append(f"{field} = {_value(area[field])}")
        if "opencode" in area:
            lines.append(f"opencode = {_inline(area['opencode'], LANES)}")
    for role in sorted(config.get("roles", {})):
        override = config["roles"][role]
        lines.append("")
        lines.append(f"[roles.{role}]")
        for field in ("claude", "codex", "codex_effort"):
            if field in override:
                lines.append(f"{field} = {_value(override[field])}")
        if "opencode" in override:
            lines.append(f"opencode = {_inline(override['opencode'], LANES)}")
        if TIER_FIELD in override:
            tiers = override[TIER_FIELD]
            for tier in MODEL_TIERS:
                if tier not in tiers:
                    continue
                lines.append("")
                lines.append(f"[roles.{role}.{TIER_FIELD}.{tier}]")
                lines.append(f"opencode = {_inline(tiers[tier]['opencode'], (*LANES, 'default'))}")
    return "\n".join(lines) + "\n"


def emit_atomic(path, config):
    """Write normalized schema 2 atomically; callers never observe a partial config."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(emit(config))
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
