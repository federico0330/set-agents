"""Trusted use case.  Observation and durable authorization are deliberately internal."""
from __future__ import annotations

import secrets
import time
from pathlib import Path
from .catalog import build_snapshot, probe_inventory
from .domain import (RISK_ORDER, TIER_ORDER, RoutingError, StaticRoute, TaskRequest, _ObservedTaskFacts,
                     combined_risk, required_tier, RouteDecision)

# ADR-0007 (P3-pi-lane, T-305): flipped False only once the pi doctor is green (pinned
# version resolves, both audited pairs authenticate, `pi --list-models` parses — see
# `set_agents_spawn.doctor`), the T-304 guards are proven (read-only, no-delegation
# children), and the T-303 spawner closes its lifecycle including crash⇒failure — all
# evidenced in docs/specs/004-adaptive-dispatch/evidence/P3-implementation.md. With this
# False, a pi route still goes through the SAME per-decision inventory check every other
# runtime does (line below): an unauthenticated/unprobed pi pair still fails closed as
# PROVIDER_UNAUTHENTICATED, never silently authorized. Flipping back to True is the whole
# rollback — one line, no data migration, no other file touched.
PI_SIMULATION_ONLY = False


class _FactsIssuer:
    """Invocation-scoped fact issuer; absent from the public facade and serialization."""
    def __init__(self, clock): self._scope, self._clock, self._used = object(), clock, False
    def observe(self, **fields):
        if self._used: raise RoutingError("FACTS_INCOMPLETE")
        return _ObservedTaskFacts(facts_version="routing-v2", observed_at=self._clock(), _scope=self._scope, **fields)
    def consume(self, facts, roster):
        if self._used or not isinstance(facts, _ObservedTaskFacts): return False
        self._used = True
        return facts.validate(roster, self._scope, self._clock())[0]


class _AuthorizationIssuer:
    """One-use provenance registry shared only with the store instance for this composition."""
    def __init__(self): self._pending = {}
    def mint(self, identity, fallback, role, role_class, snapshot):
        nonce = secrets.token_bytes(32)
        self._pending[nonce] = (identity, fallback, role, role_class, snapshot)
        return nonce
    def consume(self, nonce, identity, fallback, role, role_class, snapshot):
        value = self._pending.pop(nonce, None)
        return value == (identity, fallback, role, role_class, snapshot)


class RoutingService:
    """Public surface: route(request, facts, review_of_run_id=None), never a permit API.

    Production composition is sealed: the snapshot and runtime inventory are
    built internally from the on-disk catalog and fresh pair probes; neither is
    a public constructor argument (in-process forgery is outside the amended
    threat model — see ADR-0005 R3 — but sealed composition means honest
    callers cannot inject them even accidentally).
    """

    def __init__(self, catalog_path, roster, config, store=None, simulate=False, clock=time.time, fresh_probes=False):
        from .store import RoutingStore
        catalog_path = Path(catalog_path)
        # Cache root is the fixed routing store root (ADR-0006), never env-derived.
        # F06(a): the private 0700 root is created/validated here in composition (never
        # chmod/adopt a foreign directory) so even a read-only simulate/explain lane can
        # read a cache warmed by a prior real decision. SEC-A03: that same lane never
        # WRITES probe-cache.json (cache_write=not simulate) — reading it is not a mutation,
        # persisting a fresh probe result is.
        try:
            cache_root = (store if store is not None else RoutingStore()).ensure_cache_root()
        except RoutingError:
            cache_root = None
        self._seal(build_snapshot(catalog_path, roster, config), roster,
                   probe_inventory(config, cache_root=cache_root, fresh=fresh_probes, cache_write=not simulate),
                   store, simulate, clock,
                   recheck=lambda: build_snapshot(catalog_path, roster, config),
                   reprobe=None if simulate else (lambda pairs: probe_inventory(config, pairs=pairs)))

    @classmethod
    def _for_tests(cls, snapshot, roster, inventory, store=None, simulate=False, clock=time.time, reprobe=None):
        """Private hermetic seam; production callers never reach it."""
        service = cls.__new__(cls)
        if reprobe is None:
            reprobe = lambda pairs: {pair: set(inventory.get(pair, set())) for pair in pairs}
        service._seal(snapshot, roster, inventory, store, simulate, clock, recheck=lambda: snapshot, reprobe=reprobe)
        return service

    def _seal(self, snapshot, roster, inventory, store, simulate, clock, recheck, reprobe):
        self.snapshot = snapshot
        self.roster = {item["role"]: item for item in roster}
        self.inventory = {key: frozenset(values) for key, values in inventory.items()}
        self.store, self.simulate, self.clock = store, simulate, clock
        self._facts = {}
        self._recheck = recheck
        self._reprobe = reprobe
        self._issuer = _AuthorizationIssuer()
        if store is not None: store._bind_issuer(self._issuer)

    # Explicitly private composition seam. Production callers receive facts from harness composition.
    def _observe_for_invocation(self, **fields):
        issuer = _FactsIssuer(self.clock); facts = issuer.observe(**fields)
        # Only this exact immutable object is an observation for the current
        # invocation; a copied or hand-built fact object is never accepted.
        self._facts[id(facts)] = issuer
        return facts

    def route(self, request: TaskRequest, facts, review_of_run_id=None, unverified_review=False) -> RouteDecision:
        issuer = self._facts.pop(id(facts), None)
        if not isinstance(request, TaskRequest) or issuer is None or not issuer.consume(facts, set(self.roster)):
            return RouteDecision(None, None, None, None, None, None, False, ("FACTS_INCOMPLETE",))
        # Caller claims are validated against the same closed vocabularies as observed facts;
        # every member must be a string so malformed intent degrades, never raises (backlog N-1).
        if (request.risk not in RISK_ORDER or not isinstance(request.required_tools, (tuple, list))
                or not all(isinstance(tool, str) for tool in request.required_tools)):
            return RouteDecision(None,None,None,None,None,None,False,("FACTS_INCOMPLETE",))
        role_class = self._role_class(facts.role)
        unverified = False
        if role_class == "review":
            # P1R persists only writers; a review decision is selected but never becomes a writer authorization.
            if not review_of_run_id or self.store is None:
                if not unverified_review:
                    return RouteDecision(None,None,None,None,None,None,False,("REVIEW_IDENTITY_INVALID",))
                # Contract 004 AC-03: tier/model still reported, execution stays disabled, and the
                # doctrine forbids a routed spawn on an unverified reviewer decision.
                writer, unverified = None, True
            else:
                try: writer = self.store.implementation_identity(review_of_run_id)
                except RoutingError: return RouteDecision(None,None,None,None,None,None,False,("REVIEW_IDENTITY_INVALID",))
        else: writer = None
        conflicts = (request.role != facts.role or request.operation != facts.operation or request.task_class != facts.task_class
                     or request.selected_runtime not in (None, facts.selected_runtime))
        if conflicts:
            return RouteDecision(None,None,None,None,None,None,False,("FACTS_INCOMPLETE",))
        # Conservative combination: a request can raise the observed risk, never lower it.
        risk = combined_risk(facts.risk, request.risk)
        need = required_tier(facts.task_class, risk)
        needs_context = facts.context_required or risk == "high" or bool(facts.criticality)
        candidates, exclusions = [], []
        for route in self.snapshot.routes:
            identity=(route.route_id, facts.selected_runtime, route.provider, route.model, route.family, route.effort)
            reason = None
            # F10: hard exclusions (identity/auth/role/tools/context/independence) filter
            # BEFORE tier ordering, so TIER_INSUFFICIENT never masks a more fundamental
            # reason on the same candidate set (contract 004 §Tier model, precedence).
            if not self.snapshot.identity_allowed(identity): reason="RUNTIME_UNAVAILABLE"
            elif PI_SIMULATION_ONLY and facts.selected_runtime == "pi": reason="PI_SIMULATION_ONLY"
            elif route.model not in self.inventory.get((facts.selected_runtime, route.provider), frozenset()): reason="PROVIDER_UNAUTHENTICATED"
            elif facts.role not in route.roles: reason="ROLE_INCOMPATIBLE"
            elif not set(facts.required_tools).union(request.required_tools).issubset(route.tools): reason="TOOLS_MISSING"
            elif needs_context and (not facts.context_present or not facts.critical_coverage): reason="CONTEXT_MISSING"
            elif writer and route.family == writer.family: reason="REVIEW_FAMILY_CONFLICT"
            # F04: a reviewer sharing the writer's PROVIDER is excluded too — a repopulated,
            # per-model-family catalog otherwise lets a single authenticated provider satisfy
            # "independence" with a same-provider sibling model, degrading 003's fail-closed
            # REVIEWER_INDEPENDENCE_UNAVAILABLE. Different-provider preference (below) stays a
            # soft sort key on TOP of this hard exclusion, not instead of it.
            elif writer and route.provider == writer.provider: reason="REVIEW_PROVIDER_CONFLICT"
            elif TIER_ORDER[route.tier] < TIER_ORDER[need]: reason="TIER_INSUFFICIENT"
            if reason: exclusions.append({"route_id": route.route_id, "reason": reason})
            else: candidates.append((route, identity))
        # Lowest eligible tier >= required wins; 003's reviewer different-provider preference stays first.
        candidates.sort(key=lambda x: ((x[0].provider == writer.provider) if writer else False, TIER_ORDER[x[0].tier], x[0].curated_priority, x[0].route_id))
        if not candidates:
            return RouteDecision(None,None,None,None,None,None,False,("REVIEWER_INDEPENDENCE_UNAVAILABLE" if writer else "NO_ELIGIBLE_ROUTE",),tuple(exclusions))
        selected, identity = candidates[0]; fallback = candidates[1][1] if len(candidates) > 1 else None
        if self.simulate or role_class != "writer":
            # SEC-A01: independence_verified is positive proof, never inferred from the absence of a
            # reason code — true only for a review decision that matched a real terminal writer and
            # survived the family+provider hard exclusions above; an unverified reviewer never sets it.
            verified = role_class == "review" and writer is not None and not unverified
            return RouteDecision(*identity, False, ("REVIEW_IDENTITY_UNVERIFIED",) if unverified else (), tuple(exclusions),
                                 fallback, independence_verified=verified)
        # The static binding is recomputed from the route's canonical fields and the
        # identity is revalidated against a fresh on-disk snapshot before the durable,
        # one-use authorization. Inventory was probed fresh for this invocation;
        # re-probing per authorization is an approved exception (ADR-0005 R3).
        recomputed = StaticRoute.identifier(selected.catalog_version, selected.provider, selected.model, selected.family,
                                            selected.effort, (selected.tier,), selected.roles, selected.tools, selected.curated_priority)
        try:
            fresh = self._recheck()
        except RoutingError:
            return RouteDecision(None,None,None,None,None,None,False,("CATALOG_INVALID",))
        if recomputed != selected.route_id or not fresh.identity_allowed(identity) or (fallback and not fresh.identity_allowed(fallback)):
            return RouteDecision(None,None,None,None,None,None,False,("AUTHORIZATION_INVALID",))
        if selected.model not in self.inventory.get((facts.selected_runtime, selected.provider), frozenset()):
            return RouteDecision(None,None,None,None,None,None,False,("PROVIDER_UNAUTHENTICATED",))
        # AM-2 fresh-selected: the cache only filtered candidates; the pair that is about to be
        # durably authorized (and the fallback's, if different) is re-probed fresh right now.
        if self._reprobe is not None:
            pairs = {(facts.selected_runtime, selected.provider)}
            if fallback: pairs.add((facts.selected_runtime, fallback[2]))
            try:
                verified = self._reprobe(sorted(pairs))
            except Exception:
                return RouteDecision(None,None,None,None,None,None,False,("PROVIDER_UNAUTHENTICATED",))
            if selected.model not in verified.get((facts.selected_runtime, selected.provider), set()):
                return RouteDecision(None,None,None,None,None,None,False,("PROVIDER_UNAUTHENTICATED",))
            if fallback and fallback[3] not in verified.get((facts.selected_runtime, fallback[2]), set()):
                fallback = None  # an unverified fallback is dropped, never durably offered
        run_id = self.store.new_run_id()
        nonce = self._issuer.mint(identity, fallback, facts.role, role_class, self.snapshot)
        try:
            self.store._authorize_issued(run_id, nonce, identity, fallback, facts.role, role_class, self.snapshot)
        except RoutingError as exc:
            return RouteDecision(None,None,None,None,None,None,False,(str(exc),))
        return RouteDecision(*identity, True, (), tuple(exclusions), fallback, run_id)

    def _role_class(self, role):
        item = self.roster.get(role)
        if not item: raise RoutingError("FACTS_INCOMPLETE")
        if item["capability"] == "code-rw": return "writer"
        if item["capability"] == "review-ro" and item["duty"] in {"audit", "judge"}: return "review"
        return "other"
