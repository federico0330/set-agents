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
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LANES = ("go-zen", "zen", "local")
DUTY_ORDER = ("coord", "analysis", "docs", "implement", "gate", "audit", "judge", "release", "memory", "ops")
ROSTER_COLUMNS = {"role", "mode", "temperature", "capability", "duty"}
LEGACY_MODEL_COLUMNS = {"opencode_go", "opencode_zen", "opencode_local", "claude_model", "codex_model", "codex_effort"}
CAPABILITIES = {"coord-ro", "review-ro", "docs-rw", "factory-rw", "code-rw", "gate-ro", "release", "memory-rw", "run-ro"}
READ_ONLY = {"coord-ro", "review-ro"}
IMPLEMENT_DUTIES = {"implement"}
REVIEW_DUTIES = {"audit", "judge"}
AREA_FIELDS = ("claude", "codex", "codex_effort", "opencode")
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
_OPENCODE_FAMILY_SUFFIX = re.compile(r"(?:-mini|-flash-free|-code-free)$")

EMIT_HEADER = (
    "# models.toml — model routing source of truth (subscriptions, areas, role overrides).\n"
    "# Edit by hand or via ./setup-models.sh; the wizard rewrites this file\n"
    "# deterministically and does not preserve standalone comments.\n"
)


class ModelsError(ValueError):
    pass


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
    if config.get("schema") != 1:
        die("models.toml: unsupported schema (expected schema = 1)")
    for section in ("subscriptions", "catalog", "session", "areas"):
        if not isinstance(config.get(section), dict) or not config[section]:
            die(f"models.toml: missing or empty [{section}]")
    for key in ("claude", "codex", "codex_effort"):
        values = config["catalog"].get(key)
        if not values or not all(isinstance(item, str) for item in values):
            die(f"models.toml: [catalog].{key} must be a non-empty list of strings")
    small = config["session"].get("opencode_small_model")
    if not isinstance(small, dict) or set(small) != set(LANES):
        die("models.toml: [session].opencode_small_model must cover exactly the lanes " + ", ".join(LANES))
    config.setdefault("families", {})
    config.setdefault("roles", {})
    config.setdefault("providers", {})
    return config


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
    for source, label in ((area, f"areas.{row['duty']}"), (override, f"roles.{row['role']}")):
        for key in source:
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
            die(
                f"{row['role']}: {row['opencode_model']} needs the '{subscription}' subscription, "
                "which is inactive in models.toml — reassign it (./setup-models.sh) or re-enable the subscription"
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
    lines = [EMIT_HEADER + "schema = 1", ""]
    lines.append("[subscriptions]")
    for key in sorted(config["subscriptions"]):
        lines.append(f"{key} = {'true' if config['subscriptions'][key] else 'false'}")
    lines.append("")
    lines.append("[catalog]")
    for key in ("claude", "codex", "codex_effort"):
        values = ", ".join(_value(item) for item in sorted(config["catalog"][key]))
        lines.append(f"{key} = [{values}]")
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
    return "\n".join(lines) + "\n"
