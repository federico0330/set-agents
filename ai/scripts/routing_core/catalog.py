from __future__ import annotations

import json
import re
import subprocess
import tomllib
from pathlib import Path
from .domain import CatalogSnapshot, RoutingError, StaticRoute, _sorted_strings

# The audited pair table is the single source of runtime/provider compatibility:
# a pair absent here can never authenticate, list models, or appear in identities.
_PAIR_COMMANDS = {
    ("codex", "openai-codex"): (("codex", "login", "status"),),
    ("claude-code", "anthropic"): (("claude", "auth", "status", "--json"),),
    ("opencode", "openai-codex"): (("opencode", "auth", "list", "--pure"), ("opencode", "models", "openai", "--pure")),
    ("opencode", "anthropic"): (("opencode", "auth", "list", "--pure"), ("opencode", "models", "anthropic", "--pure")),
}
# Catalog provider -> provider key as the opencode CLI prints it.
_OPENCODE_PROVIDER_KEYS = {"openai-codex": "openai", "anthropic": "anthropic"}
_ANSI = re.compile(r"\x1b\[[0-9;]*m")


def allowed_probe(runtime: str, provider: str) -> tuple[tuple[str, ...], ...] | None:
    """The closed, exact argv list for a pair; None for any unaudited pair."""
    return _PAIR_COMMANDS.get((runtime, provider))


def _configured_models(config: dict, provider: str) -> set[str]:
    key = {"openai-codex": "codex", "anthropic": "claude"}.get(provider)
    models = config.get("catalog", {}).get(key, ()) if key else ()
    if not isinstance(models, (list, tuple)):
        return set()
    return {item for item in models if isinstance(item, str) and item}


def _clean_lines(text: str) -> list[str]:
    return [line.strip() for line in _ANSI.sub("", text).splitlines() if line.strip()]


def _parse_codex_login(stdout: str) -> bool:
    """`codex login status` prints a plain-text state line, never JSON."""
    lines = _clean_lines(stdout)
    return bool(lines) and lines[0].startswith("Logged in")


def _parse_claude_auth(stdout: str) -> bool:
    """`claude auth status --json` is a JSON object; only loggedIn is read and the raw doc is discarded."""
    doc = json.loads(stdout)
    return isinstance(doc, dict) and doc.get("loggedIn") is True


def _parse_opencode_auth(stdout: str) -> set[str]:
    """`opencode auth list --pure` prints decorated credential rows, one provider name per bullet."""
    providers = set()
    for line in _clean_lines(stdout):
        if line.startswith("Error"):
            raise RoutingError("PROVIDER_UNAUTHENTICATED")
        if line.startswith(("●", "○", "*")):
            body = line.lstrip("●○* ").strip()
            if body:
                # The trailing word is the credential method (api/oauth); the rest is the provider name.
                name = body.rsplit(None, 1)[0] if len(body.split()) > 1 else body
                providers.add(name.strip().lower())
    return providers


def _parse_opencode_models(stdout: str, provider_key: str) -> set[str]:
    """`opencode models <provider> --pure` prints `<provider>/<model>` lines; errors exit 0, so text is authoritative."""
    models = set()
    for line in _clean_lines(stdout):
        if line.startswith("Error"):
            raise RoutingError("PROVIDER_UNAUTHENTICATED")
        prefix = provider_key + "/"
        if not line.startswith(prefix):
            raise RoutingError("PROVIDER_UNAUTHENTICATED")
        model = line[len(prefix):].strip()
        if model:
            models.add(model)
    return models


def probe_inventory(config: dict, timeout: float = 5.0) -> dict[tuple[str, str], set[str]]:
    """Fresh exact pair-scoped observation with per-pair parsers.

    Any surprise — missing binary, timeout, nonzero exit, unexpected shape,
    error text — makes only that pair unavailable. Model names are always the
    intersection with the canonical models.toml catalog for the provider, so a
    runtime can never widen the audited model set. Raw provider output
    (including account identifiers) is parsed and discarded, never returned.
    """
    result: dict[tuple[str, str], set[str]] = {}
    for pair, commands in _PAIR_COMMANDS.items():
        runtime, provider = pair
        allowed = _configured_models(config, provider)
        if not allowed:
            continue
        try:
            completed = [subprocess.run(argv, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                        text=True, timeout=timeout, check=False) for argv in commands]
        except (OSError, subprocess.TimeoutExpired):
            continue
        if any(item.returncode != 0 for item in completed):
            continue
        try:
            if runtime == "codex":
                models = allowed if _parse_codex_login(completed[0].stdout) else set()
            elif runtime == "claude-code":
                models = allowed if _parse_claude_auth(completed[0].stdout) else set()
            else:
                provider_key = _OPENCODE_PROVIDER_KEYS[provider]
                credentials = _parse_opencode_auth(completed[0].stdout)
                if provider_key not in credentials:
                    continue
                models = allowed & _parse_opencode_models(completed[1].stdout, provider_key)
        except (RoutingError, ValueError, KeyError, IndexError, TypeError):
            continue
        if models:
            result[pair] = models
    return result


def build_snapshot(catalog_path: Path, roster: list[dict], config: dict, digest=None) -> CatalogSnapshot:
    try:
        source = tomllib.loads(catalog_path.read_text(encoding="utf-8"))
        if set(source) != {"catalog_version", "routes"} or source["catalog_version"] != 1 or not isinstance(source["routes"], list): raise ValueError
        rows = source["routes"]
        enabled = set(config["routing"]["enabled_providers"])
    except (OSError, tomllib.TOMLDecodeError, KeyError, TypeError, ValueError) as exc: raise RoutingError("CATALOG_INVALID") from exc
    roster_names = {row["role"] for row in roster}; routes=[]; canonical_seen=set(); ids={}
    configured_models = {provider: _configured_models(config, provider) for provider in ("openai-codex", "anthropic")}
    keys = {"provider", "model", "family", "effort", "tiers", "roles", "tools", "curated_priority"}
    for row in rows:
        try:
            if set(row) != keys: raise ValueError
            provider, model, family, effort = (row[key] for key in ("provider", "model", "family", "effort"))
            tiers, roles, tools = (_sorted_strings(row[key]) for key in ("tiers", "roles", "tools"))
            priority = row["curated_priority"]
            if (provider not in enabled or model not in configured_models.get(provider, set())
                    or not isinstance(priority, int) or priority < 0 or not set(roles) <= roster_names): raise ValueError
            rid = StaticRoute.identifier(1, provider, model, family, effort, tiers, roles, tools, priority, digest or __import__("hashlib").sha256)
            canon=(1, provider, model, family, effort, tiers, roles, tools, priority)
            if canon in canonical_seen: raise RoutingError("CATALOG_INVALID")
            if rid in ids and ids[rid] != canon: raise RoutingError("CATALOG_COLLISION")
            canonical_seen.add(canon); ids[rid]=canon; routes.append(StaticRoute(*canon, rid))
        except (KeyError, TypeError, ValueError): raise RoutingError("CATALOG_INVALID")
    if not routes or set().union(*(set(route.roles) for route in routes)) != roster_names: raise RoutingError("CATALOG_INVALID")
    # Runtime compatibility is derived from the audited probe table, never hardcoded per provider.
    allowed: dict[str, set[str]] = {}
    for runtime, provider in _PAIR_COMMANDS:
        allowed.setdefault(provider, set()).add(runtime)
    identities=frozenset((r.route_id, runtime, r.provider, r.model, r.family, r.effort) for r in routes for runtime in allowed.get(r.provider, set()))
    return CatalogSnapshot(tuple(routes), identities)
