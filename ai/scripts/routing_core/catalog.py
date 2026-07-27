from __future__ import annotations

import hashlib
import json
import os
import re
import stat as _stat
import subprocess
import time
import tomllib
from pathlib import Path
from .domain import CatalogSnapshot, RoutingError, StaticRoute, _sorted_strings

# ADR-0006 (AM-2): probe cache is a filtering-only optimization. TTL bounds staleness;
# the invalidation key covers uid and the canonical catalog/routing config.
PROBE_CACHE_TTL = 300.0

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


def _parse_codex_login(stdout: str, stderr: str = "") -> bool:
    """`codex login status` prints a plain-text state line (observed on stderr), never JSON."""
    lines = _clean_lines(stdout) or _clean_lines(stderr)
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


def _cache_key(config: dict) -> str:
    canon = json.dumps({"catalog": config.get("catalog", {}), "routing": config.get("routing", {})},
                       sort_keys=True, default=str)
    return hashlib.sha256(f"{os.getuid()}\n{canon}".encode("utf-8")).hexdigest()


def _validate_cache_dir(root: Path) -> bool:
    """Same private-directory discipline as the store: no symlink, this uid's 0700 dir.

    Never creates or chmods anything; an unvalidated root just means the cache
    is skipped (read AND write) and every pair is probed fresh (SEC-A03/F06).
    """
    try:
        st = root.lstat()
    except OSError:
        return False
    return (_stat.S_ISDIR(st.st_mode) and not _stat.S_ISLNK(st.st_mode)
            and st.st_uid == os.getuid() and _stat.S_IMODE(st.st_mode) == 0o700)


def _read_probe_cache(cache_root, key: str, now: float, config: dict):
    """Valid cache or None; anything unexpected is ignored fail-closed (fresh probes run).

    Only PAIRS PRESENT are ever positive (F06: negatives are never persisted,
    so a transient failure costs one retry, never the full TTL). Every entry
    is re-intersected with the live `_configured_models` catalog on read
    (F09), so a stale-but-key-matching cache can never widen the audited set.
    """
    root = Path(cache_root)
    if not _validate_cache_dir(root):
        return None
    try:
        path = root / "probe-cache.json"
        st = path.lstat()
        if _stat.S_ISLNK(st.st_mode) or not _stat.S_ISREG(st.st_mode) or st.st_uid != os.getuid() or _stat.S_IMODE(st.st_mode) != 0o600:
            return None
        doc = json.loads(path.read_text(encoding="utf-8"))
        if (not isinstance(doc, dict) or doc.get("key") != key
                or not isinstance(doc.get("at"), (int, float)) or isinstance(doc.get("at"), bool)
                or doc["at"] > now or now - doc["at"] > PROBE_CACHE_TTL
                or not isinstance(doc.get("pairs"), dict)):
            return None
        out: dict[tuple[str, str], set[str]] = {}
        for name, models in doc["pairs"].items():
            runtime, _, provider = str(name).partition("|")
            if (runtime, provider) not in _PAIR_COMMANDS or not isinstance(models, list) or not all(isinstance(m, str) for m in models):
                return None
            intersected = set(models) & _configured_models(config, provider)
            if intersected:  # empty after intersection ⇒ treated as absent, retried like any negative
                out[(runtime, provider)] = intersected
        return out
    except (OSError, ValueError):
        return None


def _write_probe_cache(cache_root, key: str, result: dict, now: float) -> None:
    """Atomic 0600 tmp+rename under the managed root; content is redacted pair->models only."""
    root = Path(cache_root)
    if not _validate_cache_dir(root):
        return  # the store owns root creation; never create or chmod it from here
    tmp = root / f".probe-cache.{os.getpid()}.tmp"
    doc = {"key": key, "at": now,
           "pairs": {f"{runtime}|{provider}": sorted(models) for (runtime, provider), models in result.items()}}
    old = os.umask(0o077)
    try:
        tmp.write_text(json.dumps(doc, sort_keys=True), encoding="utf-8")
        os.chmod(tmp, 0o600)
        os.replace(tmp, root / "probe-cache.json")
    except OSError:
        try: tmp.unlink()
        except OSError: pass
    finally:
        os.umask(old)


def _probe_pairs(config: dict, pairs, timeout: float, ran=None) -> dict[tuple[str, str], set[str]]:
    """Fresh, uncached, pair-scoped subprocess observation for exactly `pairs`.

    Any surprise — missing binary, timeout, nonzero exit, unexpected shape,
    error text — makes only that pair unavailable (never raises). A pair
    without any resulting model is simply absent from the returned dict:
    negative results are never a first-class cached value (F06).
    """
    result: dict[tuple[str, str], set[str]] = {}
    # Identical argvs across pairs (e.g. `opencode auth list` for both opencode pairs) run once.
    ran = {} if ran is None else ran
    # Non-interactive probe environment: opencode's TUI writer blocks forever on a
    # non-TTY stdout unless CI/TERM signal a dumb terminal (observed 2026-07-26).
    probe_env = dict(os.environ, CI="1", NO_COLOR="1", TERM="dumb")
    for pair in pairs:
        runtime, provider = pair
        commands = _PAIR_COMMANDS[pair]
        allowed = _configured_models(config, provider)
        if not allowed:
            continue
        completed, failed = [], False
        for argv in commands:
            if argv not in ran:
                try:
                    ran[argv] = subprocess.run(argv, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                               text=True, timeout=timeout, check=False, env=probe_env)
                except (OSError, subprocess.TimeoutExpired):
                    ran[argv] = None
            if ran[argv] is None:
                failed = True; break
            completed.append(ran[argv])
        if failed:
            continue
        if any(item.returncode != 0 for item in completed):
            continue
        try:
            if runtime == "codex":
                models = allowed if _parse_codex_login(completed[0].stdout, completed[0].stderr) else set()
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


def probe_inventory(config: dict, timeout: float = 20.0, cache_root=None, fresh: bool = False,
                    pairs=None, now=None, cache_write: bool = True) -> dict[tuple[str, str], set[str]]:
    """Fresh exact pair-scoped observation with per-pair parsers.

    Any surprise — missing binary, timeout, nonzero exit, unexpected shape,
    error text — makes only that pair unavailable. Model names are always the
    intersection with the canonical models.toml catalog for the provider, so a
    runtime can never widen the audited model set. Raw provider output
    (including account identifiers) is parsed and discarded, never returned.

    `pairs` restricts probing to those exact pairs, always fresh and never
    cached (the AM-2 fresh-selected path). Otherwise, with `cache_root`, a
    valid unexpired cache (ADR-0006 key) filters candidates; pairs ABSENT
    from that cache (never-seen or previously negative, F06) are always
    re-probed fresh regardless of TTL, so a transient failure only ever
    costs one retry, never the whole cache window. `cache_write=False`
    (SEC-A03: the simulate/explain lane) reads a warm cache but never
    persists one, preserving explain's no-mutation contract.
    """
    now = time.time() if now is None else now
    if pairs is not None:
        selected = [pair for pair in pairs if pair in _PAIR_COMMANDS]
        return _probe_pairs(config, selected, timeout)
    all_pairs = list(_PAIR_COMMANDS)
    use_cache = cache_root is not None and _validate_cache_dir(Path(cache_root))
    key = _cache_key(config) if use_cache else None
    cached = _read_probe_cache(cache_root, key, now, config) if (use_cache and not fresh) else None
    if cached is not None:
        missing = [pair for pair in all_pairs if pair not in cached]
        if not missing:
            return cached
        merged = dict(cached)
        merged.update(_probe_pairs(config, missing, timeout))
    else:
        merged = _probe_pairs(config, all_pairs, timeout)
    if use_cache and cache_write:
        _write_probe_cache(cache_root, key, merged, now)
    return merged


def build_snapshot(catalog_path: Path, roster: list[dict], config: dict, digest=None) -> CatalogSnapshot:
    from .domain import TIER_ORDER
    try:
        source = tomllib.loads(catalog_path.read_text(encoding="utf-8"))
        if set(source) != {"catalog_version", "routes"} or source["catalog_version"] != 2 or not isinstance(source["routes"], list): raise ValueError
        rows = source["routes"]
        enabled = set(config["routing"]["enabled_providers"])
        codex_efforts = set(config["catalog"].get("codex_effort", ()))
        xhigh_ok = bool(config.get("routing", {}).get("xhigh_benchmarked", False))
    except (OSError, tomllib.TOMLDecodeError, KeyError, TypeError, ValueError) as exc: raise RoutingError("CATALOG_INVALID") from exc
    roster_names = {row["role"] for row in roster}; routes=[]; canonical_seen=set(); ids={}; route_runtimes={}
    configured_models = {provider: _configured_models(config, provider) for provider in ("openai-codex", "anthropic")}
    # Closed row schema: required keys plus the allowlisted-optional `runtimes` (contract 004 AC-12:
    # never part of the canonical static-ID tuple; rows differing only in runtimes stay duplicates).
    required_keys = {"provider", "model", "family", "effort", "tier", "roles", "tools", "curated_priority"}
    optional_keys = {"runtimes"}
    audited: dict[str, set[str]] = {}
    for runtime, provider in _PAIR_COMMANDS:
        audited.setdefault(provider, set()).add(runtime)
    for row in rows:
        try:
            if not required_keys <= set(row) or set(row) - required_keys - optional_keys: raise ValueError
            provider, model, family, effort, tier = (row[key] for key in ("provider", "model", "family", "effort", "tier"))
            roles, tools = (_sorted_strings(row[key]) for key in ("roles", "tools"))
            priority = row["curated_priority"]
            if (provider not in enabled or model not in configured_models.get(provider, set())
                    or not isinstance(tier, str) or tier not in TIER_ORDER
                    or not isinstance(priority, int) or priority < 0 or not set(roles) <= roster_names): raise ValueError
            if provider == "openai-codex" and (effort not in codex_efforts or (effort == "xhigh" and not xhigh_ok)): raise ValueError
            if provider == "anthropic" and effort != "medium": raise ValueError
            runtimes = None
            if "runtimes" in row:
                runtimes = _sorted_strings(row["runtimes"])
                if not set(runtimes) <= audited.get(provider, set()): raise ValueError
            rid = StaticRoute.identifier(2, provider, model, family, effort, (tier,), roles, tools, priority, digest or __import__("hashlib").sha256)
            canon=(2, provider, model, family, effort, (tier,), roles, tools, priority)
            if canon in canonical_seen: raise RoutingError("CATALOG_INVALID")
            if rid in ids and ids[rid] != canon: raise RoutingError("CATALOG_COLLISION")
            canonical_seen.add(canon); ids[rid]=canon
            route = StaticRoute(2, provider, model, family, effort, tier, roles, tools, priority, rid)
            routes.append(route); route_runtimes[rid] = set(runtimes) if runtimes else None
        except (KeyError, TypeError, ValueError): raise RoutingError("CATALOG_INVALID")
    if not routes or set().union(*(set(route.roles) for route in routes)) != roster_names: raise RoutingError("CATALOG_INVALID")
    # Runtime compatibility derives from the audited probe table, optionally narrowed per route.
    identities=frozenset((r.route_id, runtime, r.provider, r.model, r.family, r.effort)
                         for r in routes
                         for runtime in (route_runtimes[r.route_id] or audited.get(r.provider, set())))
    return CatalogSnapshot(tuple(routes), identities)
