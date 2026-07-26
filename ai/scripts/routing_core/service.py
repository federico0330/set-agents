"""Trusted use case.  Observation and durable authorization are deliberately internal."""
from __future__ import annotations

import secrets
import time
from pathlib import Path
from .catalog import build_snapshot, probe_inventory
from .domain import (RISK_ORDER, RoutingError, StaticRoute, TaskRequest, _ObservedTaskFacts,
                     combined_risk, RouteDecision)


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

    def __init__(self, catalog_path, roster, config, store=None, simulate=False, clock=time.time):
        catalog_path = Path(catalog_path)
        self._seal(build_snapshot(catalog_path, roster, config), roster,
                   probe_inventory(config), store, simulate, clock,
                   recheck=lambda: build_snapshot(catalog_path, roster, config))

    @classmethod
    def _for_tests(cls, snapshot, roster, inventory, store=None, simulate=False, clock=time.time):
        """Private hermetic seam; production callers never reach it."""
        service = cls.__new__(cls)
        service._seal(snapshot, roster, inventory, store, simulate, clock, recheck=lambda: snapshot)
        return service

    def _seal(self, snapshot, roster, inventory, store, simulate, clock, recheck):
        self.snapshot = snapshot
        self.roster = {item["role"]: item for item in roster}
        self.inventory = {key: frozenset(values) for key, values in inventory.items()}
        self.store, self.simulate, self.clock = store, simulate, clock
        self._facts = {}
        self._recheck = recheck
        self._issuer = _AuthorizationIssuer()
        if store is not None: store._bind_issuer(self._issuer)

    # Explicitly private composition seam. Production callers receive facts from harness composition.
    def _observe_for_invocation(self, **fields):
        issuer = _FactsIssuer(self.clock); facts = issuer.observe(**fields)
        # Only this exact immutable object is an observation for the current
        # invocation; a copied or hand-built fact object is never accepted.
        self._facts[id(facts)] = issuer
        return facts

    def route(self, request: TaskRequest, facts, review_of_run_id=None) -> RouteDecision:
        issuer = self._facts.pop(id(facts), None)
        if not isinstance(request, TaskRequest) or issuer is None or not issuer.consume(facts, set(self.roster)):
            return RouteDecision(None, None, None, None, None, None, False, ("FACTS_INCOMPLETE",))
        # Caller claims are validated against the same closed vocabularies as observed facts.
        if request.risk not in RISK_ORDER or not isinstance(request.required_tools, (tuple, list)):
            return RouteDecision(None,None,None,None,None,None,False,("FACTS_INCOMPLETE",))
        role_class = self._role_class(facts.role)
        if role_class == "review":
            # P1R persists only writers; a review decision is selected but never becomes a writer authorization.
            if not review_of_run_id or self.store is None: return RouteDecision(None,None,None,None,None,None,False,("REVIEW_IDENTITY_INVALID",))
            try: writer = self.store.implementation_identity(review_of_run_id)
            except RoutingError: return RouteDecision(None,None,None,None,None,None,False,("REVIEW_IDENTITY_INVALID",))
        else: writer = None
        conflicts = (request.role != facts.role or request.operation != facts.operation or request.task_class != facts.task_class
                     or request.selected_runtime not in (None, facts.selected_runtime))
        if conflicts:
            return RouteDecision(None,None,None,None,None,None,False,("FACTS_INCOMPLETE",))
        # Conservative combination: a request can raise the observed risk, never lower it.
        risk = combined_risk(facts.risk, request.risk)
        needs_context = facts.context_required or risk == "high" or bool(facts.criticality)
        candidates, exclusions = [], []
        for route in self.snapshot.routes:
            identity=(route.route_id, facts.selected_runtime, route.provider, route.model, route.family, route.effort)
            reason = None
            if not self.snapshot.identity_allowed(identity): reason="RUNTIME_UNAVAILABLE"
            elif facts.selected_runtime == "pi": reason="PI_SIMULATION_ONLY"
            elif route.model not in self.inventory.get((facts.selected_runtime, route.provider), frozenset()): reason="PROVIDER_UNAUTHENTICATED"
            elif facts.role not in route.roles: reason="ROLE_INCOMPATIBLE"
            elif not set(facts.required_tools).union(request.required_tools).issubset(route.tools): reason="TOOLS_MISSING"
            elif needs_context and (not facts.context_present or not facts.critical_coverage): reason="CONTEXT_MISSING"
            elif writer and route.family == writer.family: reason="REVIEW_FAMILY_CONFLICT"
            if reason: exclusions.append({"route_id": route.route_id, "reason": reason})
            else: candidates.append((route, identity))
        candidates.sort(key=lambda x: ((x[0].provider == writer.provider) if writer else False, x[0].curated_priority, x[0].route_id))
        if not candidates:
            return RouteDecision(None,None,None,None,None,None,False,("REVIEWER_INDEPENDENCE_UNAVAILABLE" if writer else "NO_ELIGIBLE_ROUTE",),tuple(exclusions))
        selected, identity = candidates[0]; fallback = candidates[1][1] if len(candidates) > 1 else None
        if self.simulate or role_class != "writer":
            return RouteDecision(*identity, False, (), tuple(exclusions), fallback)
        # The static binding is recomputed from the route's canonical fields and the
        # identity is revalidated against a fresh on-disk snapshot before the durable,
        # one-use authorization. Inventory was probed fresh for this invocation;
        # re-probing per authorization is an approved exception (ADR-0005 R3).
        recomputed = StaticRoute.identifier(selected.catalog_version, selected.provider, selected.model, selected.family,
                                            selected.effort, selected.tiers, selected.roles, selected.tools, selected.curated_priority)
        try:
            fresh = self._recheck()
        except RoutingError:
            return RouteDecision(None,None,None,None,None,None,False,("CATALOG_INVALID",))
        if recomputed != selected.route_id or not fresh.identity_allowed(identity) or (fallback and not fresh.identity_allowed(fallback)):
            return RouteDecision(None,None,None,None,None,None,False,("AUTHORIZATION_INVALID",))
        if selected.model not in self.inventory.get((facts.selected_runtime, selected.provider), frozenset()):
            return RouteDecision(None,None,None,None,None,None,False,("PROVIDER_UNAUTHENTICATED",))
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
