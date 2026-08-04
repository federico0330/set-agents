from __future__ import annotations

import dataclasses
import hashlib
import time
from typing import Iterable


class RoutingError(ValueError):
    """A stable public reason code; never attach host/provider detail."""


# Closed vocabularies: any value outside these sets is FACTS_INCOMPLETE, never a passthrough.
TASK_CLASSES = {"inspection", "documentation", "mechanical", "implementation", "architecture", "security",
                "money", "migration", "concurrency", "public-contract", "incident"}
CRITICAL = {"architecture", "security", "money", "migration", "concurrency", "public-contract"}
RISK_ORDER = {"low": 0, "medium": 1, "high": 2}
OPERATIONS = {"inspection", "change"}
TIER_ORDER = {"fast": 0, "balanced": 1, "frontier": 2}
SELECTED_RUNTIMES = {"opencode", "claude-code", "codex", "pi"}
_FAST_ELIGIBLE = {"mechanical", "documentation", "inspection"}

# Feature 011 deliberately recognizes one *normalized* Pi result only.  Keeping this
# pure and allowlisted prevents error wording, raw stderr, or a partial event from ever
# becoming a paid failover decision.
def classify_pi_terminal_error(error) -> str:
    """Return ``quota_exhausted`` only for the fixed settled Anthropic signature.

    ``error`` is a bounded normalized facts object assembled at the Pi adapter; raw
    provider payloads are intentionally neither accepted nor persisted here.
    """
    if not isinstance(error, dict):
        return "unknown_failure"
    if (error.get("settled") is True and error.get("provider") == "anthropic"
            and error.get("http_status") == 400
            and error.get("type") == "invalid_request_error"
            and error.get("marker") == "out of extra usage"):
        return "quota_exhausted"
    # 017 PKG-C1 (ADR-0029): the SECOND settled signature — the Claude Code lane.
    # `claude --print --output-format json` reports quota exhaustion as api_error_status
    # 429 with the usage-limit wording in the result text (spec 015's live-proven error
    # shape). The explicit `lane` discriminator keeps this DISJOINT from the Pi
    # signature by construction: the immutable 011 contract pins that no variant of
    # the Pi-shaped dict (which never carries `lane`) classifies at 429, and this
    # branch can only ever match a dict the Claude Code adapter itself normalized.
    if (error.get("settled") is True and error.get("provider") == "anthropic"
            and error.get("lane") == "claude-code"
            and error.get("http_status") == 429
            and isinstance(error.get("marker"), str)
            and ("out of extra usage" in error["marker"]
                 or "usage limit" in error["marker"].lower())):
        return "quota_exhausted"
    if error.get("rate_limited") is True:
        return "rate_limited"
    return "unknown_failure"


def required_tier(task_class: str, risk: str) -> str:
    """Pure required-tier resolution over validated facts (contract 004 §Tier model)."""
    if task_class not in TASK_CLASSES or risk not in RISK_ORDER:
        raise RoutingError("FACTS_INCOMPLETE")
    if task_class in CRITICAL or risk == "high":
        return "frontier"
    if task_class in _FAST_ELIGIBLE and risk == "low":
        return "fast"
    return "balanced"


def combined_risk(observed: str, requested: str) -> str:
    """Caller claims can only raise risk; an observed high risk is never downgraded."""
    if observed not in RISK_ORDER or requested not in RISK_ORDER:
        raise RoutingError("FACTS_INCOMPLETE")
    return observed if RISK_ORDER[observed] >= RISK_ORDER[requested] else requested


# AC-01/AC-05 (014-model-preference-policy): the single, closed four-value role-class
# resolver every consumer of this contract's taxonomy reuses -- never re-derived a
# second time. `build`/`grunt` are, by definition, the exact predicates
# `RoutingService._role_class` already computes as `"writer"`/`"review"`
# (service.py:312-317) -- reused literally, not reconstructed as an equivalent compound
# condition (R2-F-03). `decision` is a new predicate (`duty in {"coord","docs"}`) this
# contract adds; every other role is `unscoped`. An explicit `role_override` (AC-02's
# `[role_override]` table, keyed by role name -> one of the three named classes) takes
# precedence over the default predicate below -- never the other way around.
BIAS_CLASSES = ("decision", "grunt", "build", "unscoped")
_BIAS_DECISION_DUTIES = {"coord", "docs"}
_BIAS_GRUNT_DUTIES = {"audit", "judge"}


def resolve_bias_class(role: str, row: dict, role_override: dict | None = None) -> str:
    """AC-01/AC-05: resolve `role`'s closed role-class from `row` (a roster item with at
    least `capability`/`duty` keys), honoring AC-02's per-role override precedence.

    Returns one of `BIAS_CLASSES`, never a role-by-role provider list -- that would
    reopen `007-P0`'s exact flaw (a hand-maintained, per-role table disconnected from a
    class model).
    """
    if role_override and role in role_override:
        return role_override[role]
    if row.get("capability") == "code-rw":
        return "build"
    if row.get("capability") == "review-ro" and row.get("duty") in _BIAS_GRUNT_DUTIES:
        return "grunt"
    if row.get("duty") in _BIAS_DECISION_DUTIES:
        return "decision"
    return "unscoped"


def _fail(code: str) -> None:
    raise RoutingError(code)


def _sorted_strings(values: Iterable[str]) -> tuple[str, ...]:
    if not isinstance(values, (list, tuple, set)) or not values or not all(isinstance(x, str) and x for x in values):
        _fail("CATALOG_INVALID")
    result = tuple(sorted(values, key=lambda value: value.encode("utf-8")))
    if len(set(result)) != len(result):
        _fail("CATALOG_INVALID")
    return result


def _lp(value: str) -> bytes:
    raw = value.encode("utf-8")
    return len(raw).to_bytes(4, "big") + raw


def canonical_static_binding(catalog_version: int, provider: str, model: str, family: str, effort: str,
                             tiers: Iterable[str], roles: Iterable[str], tools: Iterable[str], priority: int) -> bytes:
    """Unambiguous, versioned UTF-8 encoding used by the static-id contract."""
    if not isinstance(catalog_version, int) or not isinstance(priority, int):
        _fail("CATALOG_INVALID")
    fields = (str(catalog_version), provider, model, family, effort)
    if not all(isinstance(x, str) and x for x in fields[1:]):
        _fail("CATALOG_INVALID")
    out = bytearray(b"routing-v1\0")
    for field in fields:
        out.extend(_lp(field))
    for group in (tiers, roles, tools):
        items = _sorted_strings(group)
        out.extend(len(items).to_bytes(4, "big"))
        for item in items:
            out.extend(_lp(item))
    out.extend(str(priority).encode("ascii"))
    return bytes(out)


@dataclasses.dataclass(frozen=True)
class TaskRequest:
    role: str
    operation: str
    task_class: str = "inspection"
    risk: str = "low"
    required_tools: tuple[str, ...] = ()
    selected_runtime: str | None = None


@dataclasses.dataclass(frozen=True)
class _ObservedTaskFacts:
    role: str | None; operation: str | None; task_class: str | None
    read_write: str | None; write_started: bool | None; risk: str | None; criticality: str | None
    affected_surfaces: tuple[str, ...] | None; required_tools: tuple[str, ...] | None
    context_required: bool | None; context_present: bool | None; critical_coverage: bool | None
    selected_runtime: str | None; facts_version: str | None; observed_at: float | None
    ambiguous: bool = False
    # This is intentionally non-serializable and is minted by the fact builder/composition only.
    _scope: object | None = dataclasses.field(default=None, repr=False, compare=False)

    def validate(self, roster: set[str], scope: object | None, now: float | None = None) -> tuple[bool, tuple[str, ...]]:
        now = time.time() if now is None else now
        fields = (self.role, self.operation, self.task_class, self.read_write, self.write_started, self.risk,
                  self.criticality, self.affected_surfaces, self.required_tools, self.context_required,
                  self.context_present, self.critical_coverage, self.selected_runtime, self.facts_version, self.observed_at)
        valid = (all(value is not None for value in fields) and self.role in roster and self.read_write in {"read", "write"}
                 and self.operation in OPERATIONS and self.task_class in TASK_CLASSES
                 and self.risk in RISK_ORDER and (self.criticality == "" or self.criticality in CRITICAL)
                 and self.selected_runtime in SELECTED_RUNTIMES
                 # F05: an unhashable/non-string member must degrade here, before any `set(...)`
                 # call downstream ever sees it (backlog N-1 covers the request side only).
                 and isinstance(self.required_tools, (tuple, list))
                 and all(isinstance(tool, str) for tool in self.required_tools)
                 and self.facts_version == "routing-v2" and isinstance(self.observed_at, (int, float)) and not isinstance(self.observed_at, bool)
                 and self.observed_at <= now and now - self.observed_at <= 30 and not self.ambiguous
                 and scope is not None and self._scope is scope)
        return valid, () if valid else ("FACTS_INCOMPLETE",)


@dataclasses.dataclass(frozen=True)
class StaticRoute:
    catalog_version: int; provider: str; model: str; family: str; effort: str
    # Single tier per row (contract 004); the canonical binding encodes it as a
    # one-element group so the 003 static-ID tuple shape is unchanged.
    tier: str; roles: tuple[str, ...]; tools: tuple[str, ...]; curated_priority: int; route_id: str

    @staticmethod
    def identifier(catalog_version, provider, model, family, effort, tiers, roles, tools, curated_priority, digest=hashlib.sha256):
        return "rt1_" + digest(canonical_static_binding(catalog_version, provider, model, family, effort, tiers, roles, tools, curated_priority)).hexdigest()[:16]


@dataclasses.dataclass(frozen=True)
class CatalogSnapshot:
    routes: tuple[StaticRoute, ...]
    identities: frozenset[tuple[str, str, str, str, str, str]]
    def identity_allowed(self, identity: tuple[str, str, str, str, str, str]) -> bool: return identity in self.identities


@dataclasses.dataclass(frozen=True)
class ImplementationIdentity:
    provider: str; family: str; route_id: str; runtime: str; model: str; effort: str


@dataclasses.dataclass(frozen=True)
class RouteDecision:
    route_id: str | None; runtime: str | None; provider: str | None; model: str | None; family: str | None; effort: str | None
    execution_enabled: bool; reason_codes: tuple[str, ...] = (); exclusions: tuple[dict[str, str], ...] = ()
    fallback_identity: tuple[str, str, str, str, str, str] | None = None
    run_id: str | None = None
    # SEC-A01: a POSITIVE, additive signal — true only for a review decision that
    # matched a real terminal writer AND survived the family+provider exclusion.
    # An unverified reviewer decision (or any non-review decision) never sets it.
    independence_verified: bool = False
    # AC-08 (014-model-preference-policy): the resolved role-class (`resolve_bias_class`,
    # one of `BIAS_CLASSES` above) and whether AC-02's config supplied a non-default
    # preference for it. Deliberately named `bias_class`, not `role_class`, so it never
    # collides with `cmd_route_decide`'s own, differently-valued `role_class` envelope
    # key (`{"writer","review","other"}`, set_agents_app.py:230-233/418/449) -- same
    # envelope, same decision, two independent classifications, disjoint vocabularies.
    # `None` only for the two refusals strictly before `service.py:170` (`role_class`
    # itself, which this resolver piggybacks the same `facts.role` lookup on, not yet
    # known); populated for every refusal reachable only after that line.
    bias_class: str | None = None
    preference_configured: bool = False
    @property
    def identity(self):
        return None if None in (self.route_id, self.runtime, self.provider, self.model, self.family, self.effort) else (self.route_id, self.runtime, self.provider, self.model, self.family, self.effort)
    def to_dict(self):
        return dataclasses.asdict(self)
