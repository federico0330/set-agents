"""Trusted use case.  Observation and durable authorization are deliberately internal."""
from __future__ import annotations

import secrets
import time
from pathlib import Path
from .catalog import build_snapshot, canonical_model, probe_inventory, billing_rank
from .inference import vendor_stem as _vendor_stem, stem_resolved as _stem_resolved
from .domain import (RISK_ORDER, TIER_ORDER, RoutingError, StaticRoute, TaskRequest, _ObservedTaskFacts,
                     combined_risk, required_tier, RouteDecision, resolve_bias_class)

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

# AC-01 (015-anthropic-dispatch-parity): the ONLY provider-scoped runtime redirect this
# contract configures. `anthropic` requested on whatever lane the caller asked for falls
# through to `claude-code` ONLY when that REQUESTED `(runtime, provider)` pair has no
# inventory entry at all (see `_effective_runtime` below for the exact, pair-level-
# presence trigger) — `claude-code` is where Claude Code's real OAuth subscription is
# already live-authenticated (`## Contexto` §C of the spec), never a metered API key.
# A closed, single-entry map on purpose: extending this to another provider, or
# widening it to override an already-authenticated pair (e.g. redirecting an
# already-working `("pi","anthropic")` decision away from `pi`), is explicitly out of
# scope (Non-goals: no widening of `openai-codex`'s reachable runtimes — that is
# `011`'s quota-failover territory — and no change to `pi`'s own dispatch lane).
_PROVIDER_RUNTIME_REDIRECTS = {"anthropic": "claude-code"}

# F-03 (015 repair panel RP-01): the requested-pair-presence check above was the ONLY
# guard AC-01 originally had, and it is silent about a requested pair that is
# GENUINELY ABSENT from inventory on the `pi` lane specifically -- under the literal
# original rule, that case redirects. `set_agents_spawn.route_and_spawn` (the REAL `pi`
# lane spawner, ADR-0007) never reads `RouteDecision.runtime` at all -- it always spawns
# on `pi` regardless of what this service decided. If the redirect fired for a `pi`
# request, a decision authorized (post-redirect) for `claude-code` would get spawned on
# `pi` instead by that ignorant caller -- converting a fail-closed `NO_ELIGIBLE_ROUTE`
# into a fail-open authorization silently executed on the wrong lane, without ever
# invoking `claude_code_spawn.py`'s CLI-level tool ceiling (D4/D5) at all. The safest,
# most conservative fix: `pi` is a categorically redirect-EXEMPT requested lane,
# regardless of pair presence/absence -- even when the redirect target
# (`claude-code`/`anthropic`) is separately, fully authenticated. This is stricter than,
# and supersedes, the pair-presence check alone for this one lane.
_NEVER_REDIRECT_FROM_RUNTIMES = frozenset({"pi"})


def _bias_rank(provider: str, preference: tuple) -> int:
    """AC-04: rank a candidate's provider by AC-02's ordered, class-scoped preference
    list -- sort-tuple position 3, strictly between tier (position 2) and
    `curated_priority` (today's position 3, shifting to 4). A provider named in the list
    ranks by its list position; a provider absent from a non-empty list, and every
    provider alike when the list is empty (no preference configured for this decision's
    resolved class, or the role is `unscoped`), ranks at one fixed, tied, constant value
    equal to the list's length -- never excluded, never a separate code branch for the
    absent-configuration case (AC-04 point 4: an empty list makes every candidate compare
    equal at this position, so ordering falls through unchanged to `curated_priority`)."""
    try:
        return preference.index(provider)
    except ValueError:
        return len(preference)


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
        # AC-04/AC-02 (014-model-preference-policy): `config` is the one channel already
        # available here without touching `routing.py`'s read-only `compose()` signature
        # -- the app-layer CLI (set_agents_app.py) injects the sibling file's already-
        # loaded, already-validated `{"preference": {...}, "role_override": {...}}` under
        # this internal-marker key (the same `_source_schema`-style convention
        # models_config.py already uses for a value that is never itself serialized back
        # to models.toml). Absent entirely (every other production/test caller) is the
        # unbiased default, never a crash.
        model_preference = config.pop("_model_preference", None) if isinstance(config, dict) else None
        preference = dict((model_preference or {}).get("preference") or {})
        role_override = dict((model_preference or {}).get("role_override") or {})
        # ADR-0032: user model pins ride the same injected channel. `{role_or_star:
        # (provider, model)}` — a SOFT sort-level override only: pins never bypass the
        # hard-exclusion loop in route() (auth/independence/tier floor), so a pinned
        # identity that is not eligible degrades to the dynamic pick with an additive
        # MODEL_PIN_UNAVAILABLE reason code, never a fabricated authorization.
        model_pin = dict((model_preference or {}).get("model_pin") or {})
        inventory = probe_inventory(config, cache_root=cache_root, fresh=fresh_probes, cache_write=not simulate)
        # ADR-0029 (017 PKG-B2), extended by ADR-0034 (019 PKG-1): the OPT-IN
        # discovered-routes path. With [routing].discovered_providers unset entirely from
        # a config that skips models_config validation (e.g. a bare {} in a unit test),
        # this branch is dead and composition is byte-for-byte the pre-017 sealed shape —
        # same builder, same recheck lambda. ADR-0034's new default is the STRING "auto",
        # which now also takes this branch: `catalog.resolve_discovered_providers` (the
        # SAME pure function `build_effective_snapshot` calls internally) derives the
        # concrete provider set from the ACTUAL probed inventory every time, so the
        # initial composition and this `recheck` lambda — which re-probes a fresh
        # inventory — necessarily derive from the SAME rule, never two independently
        # drifting universes (a real hazard: derive-then-diverge would fail every
        # synthesized authorization as AUTHORIZATION_INVALID on its own re-check). With
        # providers declared (or "auto" resolving non-empty), the snapshot (and the
        # authorization revalidation recheck) both flow through build_effective_snapshot,
        # so a synthesized route revalidates against the same effective universe it was
        # selected from — never against the narrower curated snapshot.
        discovery_configured = isinstance(config, dict) and bool((config.get("routing") or {}).get("discovered_providers"))
        if discovery_configured:
            from .catalog import build_effective_snapshot
            snapshot, inferred_ids = build_effective_snapshot(catalog_path, roster, config, inventory)
            recheck = lambda: build_effective_snapshot(  # noqa: E731
                catalog_path, roster, config,
                probe_inventory(config, cache_root=cache_root, cache_write=not simulate))[0]
        else:
            snapshot, inferred_ids = build_snapshot(catalog_path, roster, config), frozenset()
            recheck = lambda: build_snapshot(catalog_path, roster, config)  # noqa: E731
        self._seal(snapshot, roster, inventory,
                   store, simulate, clock,
                   recheck=recheck,
                   reprobe=None if simulate else (lambda pairs: probe_inventory(config, pairs=pairs)),
                   preference=preference, role_override=role_override, inferred_ids=inferred_ids,
                   model_pin=model_pin)

    @classmethod
    def _for_tests(cls, snapshot, roster, inventory, store=None, simulate=False, clock=time.time, reprobe=None,
                    preference=None, role_override=None, model_pin=None):
        """Private hermetic seam; production callers never reach it.

        `preference`/`role_override` (AC-04): the resolved sibling-config tables a
        production caller would otherwise inject via `config["_model_preference"]`
        (`__init__` above) -- both default to empty, the unbiased default, so every
        existing call site of this seam stays byte-identical (AC-04c) without updating
        its call.
        """
        service = cls.__new__(cls)
        if reprobe is None:
            reprobe = lambda pairs: {pair: set(inventory.get(pair, set())) for pair in pairs}
        service._seal(snapshot, roster, inventory, store, simulate, clock, recheck=lambda: snapshot, reprobe=reprobe,
                       preference=preference, role_override=role_override, model_pin=model_pin)
        return service

    def _seal(self, snapshot, roster, inventory, store, simulate, clock, recheck, reprobe, preference=None, role_override=None, inferred_ids=frozenset(), model_pin=None):
        self.snapshot = snapshot
        self.roster = {item["role"]: item for item in roster}
        self.inventory = {key: frozenset(values) for key, values in inventory.items()}
        self.store, self.simulate, self.clock = store, simulate, clock
        self._facts = {}
        self._recheck = recheck
        self._reprobe = reprobe
        # ADR-0029: route_ids whose tier/family are inferred (empty on the curated path
        # and in every pre-017 composition, including _for_tests callers that never
        # pass the parameter).
        self._inferred_ids = frozenset(inferred_ids)
        self._issuer = _AuthorizationIssuer()
        # AC-02/AC-04: preference values are stored as tuples (an ordered rank, `_bias_rank`
        # indexes into it) -- never mutated after construction, matching the sealed-composition
        # discipline every other collection on this instance already follows.
        self._bias_preference = {key: tuple(value) for key, value in (preference or {}).items()}
        self._bias_role_override = dict(role_override or {})
        # ADR-0032: normalized to (provider, model) tuples; role entry beats the `*` global.
        self._model_pin = {key: tuple(value) for key, value in (model_pin or {}).items()}
        if store is not None: store._bind_issuer(self._issuer)

    # Explicitly private composition seam. Production callers receive facts from harness composition.
    def _observe_for_invocation(self, **fields):
        issuer = _FactsIssuer(self.clock); facts = issuer.observe(**fields)
        # Only this exact immutable object is an observation for the current
        # invocation; a copied or hand-built fact object is never accepted.
        self._facts[id(facts)] = issuer
        return facts

    def _effective_runtime(self, runtime: str, provider: str) -> str:
        """AC-01: resolve the runtime a route's identity/auth is actually evaluated
        against. Fires ONLY when the REQUESTED `(runtime, provider)` pair has NO
        inventory entry AT ALL — `self.inventory` never stores an empty-model pair
        (`catalog._probe_pairs`'s own `if models: result[pair] = models`, the pair is
        simply absent otherwise), so this is a genuine pair-level PRESENCE check, never
        a per-model completeness check (R3-05). A present-but-model-incomplete pair
        (e.g. `("pi","anthropic")` probed but missing one tier's model) is left
        untouched here — the ordinary per-model `PROVIDER_UNAUTHENTICATED` check at
        the call site still excludes it correctly, on the requested lane, never
        redirected. Never fires when the requested lane already IS the redirect
        target (idempotent), and never fires for a provider absent from
        `_PROVIDER_RUNTIME_REDIRECTS` (`openai-codex`'s behavior stays byte-identical
        to before this AC). This is the one requirement that keeps AC-01's own
        Non-goal true in code, not merely in prose: an already-authenticated
        `("pi","anthropic")` decision is never redirected away from `pi`. F-03 (015
        repair): `pi` is ALSO categorically redirect-EXEMPT as a REQUESTED lane even
        when its own pair is GENUINELY ABSENT from inventory (not merely incomplete) —
        `set_agents_spawn.route_and_spawn`, the real `pi`-lane spawner, never reads
        `RouteDecision.runtime` and always spawns on `pi` regardless, so redirecting a
        `pi`-requested decision to `claude-code` would authorize one lane and execute on
        another — see `_NEVER_REDIRECT_FROM_RUNTIMES` above."""
        redirect = _PROVIDER_RUNTIME_REDIRECTS.get(provider)
        if (redirect is not None and redirect != runtime and runtime not in _NEVER_REDIRECT_FROM_RUNTIMES
                and (runtime, provider) not in self.inventory):
            return redirect
        return runtime

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
        # AC-01/AC-05/AC-08 (014-model-preference-policy): resolved exactly once, right
        # after `role_class` (the pre-existing 3-value classification this contract's own
        # resolver piggybacks the same `facts.role`/roster lookup on) is known -- `None`
        # only for the two refusals strictly before this point (`:206`/`:211` above,
        # unreachable from here). `bias_preference` is the resolved class's ordered
        # provider list from AC-02's config, or `()` (the unbiased default) when the
        # class has no configured entry -- `preference_configured` is true only when that
        # list is genuinely non-empty (AC-08).
        bias_class = resolve_bias_class(facts.role, self.roster[facts.role], self._bias_role_override)
        bias_preference = self._bias_preference.get(bias_class, ())
        preference_configured = bool(bias_preference)
        # ADR-0032: role pin beats the `*` global; None means unpinned (every candidate
        # ranks equal at the pin position, ordering falls through unchanged).
        pin = self._model_pin.get(facts.role) or self._model_pin.get("*")
        unverified = False
        if role_class == "review":
            # P1R persists only writers; a review decision is selected but never becomes a writer authorization.
            if not review_of_run_id or self.store is None:
                if not unverified_review:
                    return RouteDecision(None,None,None,None,None,None,False,("REVIEW_IDENTITY_INVALID",),bias_class=bias_class,preference_configured=preference_configured)
                # Contract 004 AC-03: tier/model still reported, execution stays disabled, and the
                # doctrine forbids a routed spawn on an unverified reviewer decision.
                writer, unverified = None, True
            else:
                try: writer = self.store.implementation_identity(review_of_run_id)
                except RoutingError: return RouteDecision(None,None,None,None,None,None,False,("REVIEW_IDENTITY_INVALID",),bias_class=bias_class,preference_configured=preference_configured)
        else: writer = None
        # AC-01 non-goal: this conflict check governs a disjoint concern (whether the
        # CALLER's own requested lane conflicts with the resolved one) and is
        # deliberately left reading the raw, requested `facts.selected_runtime` — never
        # the per-candidate effective runtime the exclusion loop below computes.
        conflicts = (request.role != facts.role or request.operation != facts.operation or request.task_class != facts.task_class
                     or request.selected_runtime not in (None, facts.selected_runtime))
        if conflicts:
            return RouteDecision(None,None,None,None,None,None,False,("FACTS_INCOMPLETE",),bias_class=bias_class,preference_configured=preference_configured)
        # Conservative combination: a request can raise the observed risk, never lower it.
        risk = combined_risk(facts.risk, request.risk)
        need = required_tier(facts.task_class, risk)
        needs_context = facts.context_required or risk == "high" or bool(facts.criticality)
        candidates, exclusions = [], []
        for route in self.snapshot.routes:
            # AC-01: the identity/auth check below is evaluated against this route's
            # own EFFECTIVE runtime, not blindly against the caller's requested
            # `facts.selected_runtime` — `_effective_runtime` only ever differs from
            # the requested one for `route.provider == "anthropic"`, and only when the
            # requested pair has no inventory entry at all. `identity[1]` (this value)
            # is what the final `RouteDecision.runtime` reports, so a decision that
            # will actually execute on the redirected lane says so in its own audit
            # trail (spec AC-01). `build_snapshot`/`identity_allowed` already admit
            # the `claude-code`/`anthropic` identity with zero catalog change (§B).
            effective_runtime = self._effective_runtime(facts.selected_runtime, route.provider)
            identity=(route.route_id, effective_runtime, route.provider, route.model, route.family, route.effort)
            reason = None
            # F10: hard exclusions (identity/auth/role/tools/context/independence) filter
            # BEFORE tier ordering, so TIER_INSUFFICIENT never masks a more fundamental
            # reason on the same candidate set (contract 004 §Tier model, precedence).
            if not self.snapshot.identity_allowed(identity): reason="RUNTIME_UNAVAILABLE"
            elif self.store is not None and self.store.provider_exhausted(route.provider): reason="PROVIDER_EXHAUSTED"
            # AC-01 (counted, unchanged): this pi-specific simulation guard reads the
            # caller's literal REQUESTED lane, never the effective/redirected one — it
            # governs whether the caller is asking pi to run in ambient-auth simulation
            # mode at all, a concern unrelated to provider-inventory redirect.
            elif PI_SIMULATION_ONLY and facts.selected_runtime == "pi": reason="PI_SIMULATION_ONLY"
            elif route.model not in self.inventory.get((effective_runtime, route.provider), frozenset()): reason="PROVIDER_UNAUTHENTICATED"
            elif facts.role not in route.roles: reason="ROLE_INCOMPATIBLE"
            elif not set(facts.required_tools).union(request.required_tools).issubset(route.tools): reason="TOOLS_MISSING"
            elif needs_context and (not facts.context_present or not facts.critical_coverage): reason="CONTEXT_MISSING"
            elif writer and route.family == writer.family: reason="REVIEW_FAMILY_CONFLICT"
            # ADR-0034 (AC-06): a synthesized reviewer candidate whose OWN vendor stem
            # never resolved against any known pattern (`inference.stem_resolved`) can
            # never be PROVEN independent of the writer — it is excluded outright,
            # fail-closed, before the stem-equality comparison below even runs. This is
            # the "inference can only remove independence, never grant it" rule (ADR-0029
            # d.3) applied to the resolution step itself, not just the comparison: an
            # unresolved stem is not a weaker signal of independence, it is NO signal.
            elif (writer and route.route_id in self._inferred_ids
                  and not _stem_resolved(route.model)): reason="REVIEW_IDENTITY_UNRESOLVED_INFERRED"
            # ADR-0029 d.3: inference only ever REMOVES independence. A synthesized
            # candidate compares by coarse vendor stem against the writer's model —
            # an inferred kimi-* reviewer is never independent of any kimi-* writer,
            # whatever the curated (finer) families would have said. Curated-vs-curated
            # pairs never reach this branch (the set is empty on the curated path).
            elif (writer and route.route_id in self._inferred_ids
                  and _vendor_stem(route.model) == _vendor_stem(writer.model)): reason="REVIEW_FAMILY_CONFLICT"
            # Repair SEC-001 (panel RP-01, security-auditor, critical, 012 repair):
            # defense in depth, independent of AC-07's build_snapshot-time guard above. A
            # reviewer candidate whose (provider, model) normalizes to the SAME canonical
            # model as the writer's — even under a DIFFERENT provider string and a
            # DIFFERENT curated `family` a curator got wrong — is excluded here too. This
            # is the layer that actually closes the hole if the catalog-time guard is
            # ever bypassed (a stale snapshot, a future code path that skips
            # build_snapshot, or a curator mistake this repair's layer-1 fix does not
            # anticipate): REVIEW_FAMILY_CONFLICT above only catches a matching curated
            # `family`, which a wrong-but-differing curation defeats by construction.
            elif writer and canonical_model(route.provider, route.model) == canonical_model(writer.provider, writer.model): reason="REVIEW_MODEL_CONFLICT"
            # F04: a reviewer sharing the writer's PROVIDER is excluded too — a repopulated,
            # per-model-family catalog otherwise lets a single authenticated provider satisfy
            # "independence" with a same-provider sibling model, degrading 003's fail-closed
            # REVIEWER_INDEPENDENCE_UNAVAILABLE. Different-provider preference (below) stays a
            # soft sort key on TOP of this hard exclusion, not instead of it.
            elif writer and route.provider == writer.provider: reason="REVIEW_PROVIDER_CONFLICT"
            elif TIER_ORDER[route.tier] < TIER_ORDER[need]: reason="TIER_INSUFFICIENT"
            if reason: exclusions.append({"route_id": route.route_id, "reason": reason})
            else: candidates.append((route, identity))
        # Lowest eligible tier >= required wins; 003's reviewer different-provider preference
        # stays first. AC-04 (014-model-preference-policy): `_bias_rank` is inserted at
        # position 3, strictly between tier (position 2) and `curated_priority` (today's
        # position 3, shifted to 4) -- never before the independence/tier boundary, never a
        # change to which candidates reach this sort (the exclusion loop above, untouched).
        # ADR-0032: the pin rank sits BETWEEN the reviewer different-provider preference
        # and tier — a pinned identity that survived every hard exclusion above wins even
        # across tiers (the tier FLOOR was already enforced as TIER_INSUFFICIENT), but a
        # pin never outranks reviewer independence. Unpinned decisions rank every
        # candidate equal here, leaving the pre-ADR-0032 ordering byte-identical.
        # ADR-0034 (AC-04): `is_inferred` sits immediately BEFORE `curated_priority` — a
        # curated row (0) always outranks a synthesized one (1) at equal tier/bias, as an
        # EXPLICIT flag rather than relying on every synthesized row's `curated_priority`
        # happening to be a large magic number (1000, `inference.synthesize_route_row`).
        # ADR-0035 (AC-13): `billing_rank` is inserted HERE, strictly between `TIER_ORDER`
        # (position 2) and `_bias_rank` (today's position 3, shifted to 4) — a subscription
        # or free-suffixed candidate outranks a metered one only among candidates ALREADY
        # tied on independence/pin/tier; the exclusion loop above (identity, auth, role,
        # tools, context, reviewer independence, tier floor) is completely untouched, so a
        # metered candidate that is the ONLY one to satisfy the tier floor or the ONLY one
        # to survive the independence exclusions still wins here exactly as before this
        # ADR — cost is an ordering criterion among survivors, never an eligibility one.
        # Final tuple this ADR leaves:
        # (same_provider_as_writer, pin_rank, TIER_ORDER, billing_rank, _bias_rank,
        #  is_inferred, curated_priority, route_id).
        candidates.sort(key=lambda x: ((x[0].provider == writer.provider) if writer else False, 0 if pin and (x[0].provider, x[0].model) == pin else 1, TIER_ORDER[x[0].tier], billing_rank(x[0].provider, x[0].model), _bias_rank(x[0].provider, bias_preference), 1 if x[0].route_id in self._inferred_ids else 0, x[0].curated_priority, x[0].route_id))
        if not candidates:
            return RouteDecision(None,None,None,None,None,None,False,("REVIEWER_INDEPENDENCE_UNAVAILABLE" if writer else "NO_ELIGIBLE_ROUTE",),tuple(exclusions),bias_class=bias_class,preference_configured=preference_configured)
        # ADR-0034 (AC-08): the block below used to run ONCE against the top-ranked
        # candidate and abort with PROVIDER_UNAUTHENTICATED the moment the FRESH reprobe
        # rejected it -- wasting every other still-eligible candidate a dynamic
        # inventory may offer. It now retries against the next already-filtered
        # candidate (never a re-run of the exclusion loop above -- independence/tier/
        # tools were already enforced for every entry in `candidates`) specifically when
        # the reprobe rejects the current pick; every other failure mode below
        # (CATALOG_INVALID, AUTHORIZATION_INVALID, the invocation-time inventory check)
        # still returns immediately on whatever candidate it hit, unchanged, exactly as
        # before this ADR -- only a reprobe rejection re-ranks and loops.
        while True:
            selected, identity = candidates[0]; fallback = candidates[1][1] if len(candidates) > 1 else None
            # AC-09 (016-audit-debt-repayment): purely additive audit-trail element. When the
            # SELECTED candidate's effective runtime (identity[1], already computed by
            # `_effective_runtime` in the exclusion loop above) differs from the caller's
            # literal requested `facts.selected_runtime`, a redirect happened for this
            # decision. Recorded as an extra `reason_codes` entry alongside whatever codes a
            # branch already emits — never replaces or reorders an existing code, never
            # changes `success`/`runtime`/`identity`/`fallback`. Distinguishable from every
            # existing code (none of them share this prefix).
            redirect_reason = (
                (f"RUNTIME_REDIRECTED requested={facts.selected_runtime} effective={identity[1]}",)
                if identity[1] != facts.selected_runtime else ()
            )
            # ADR-0029: a decision carried by a synthesized route says so, always — the
            # inferred tier/family are surfaced next to the selection instead of passing
            # as curation-grade fact. Purely additive to reason_codes, like the redirect.
            if selected.route_id in self._inferred_ids:
                redirect_reason = redirect_reason + (
                    f"MODEL_METADATA_INFERRED tier={selected.tier} family={selected.family}",)
            # ADR-0035 (AC-14): the billing rank that decided this candidate's position
            # among its tier/independence-tied peers, always surfaced -- purely additive
            # to reason_codes, same discipline as RUNTIME_REDIRECTED/MODEL_METADATA_INFERRED
            # above: never replaces or reorders an existing code, never changes
            # `success`/`runtime`/`identity`/`fallback`.
            redirect_reason = redirect_reason + (
                f"BILLING_RANK provider={selected.provider} rank={billing_rank(selected.provider, selected.model)}",)
            # ADR-0032: a pinned decision always says so — MODEL_PINNED when the user's pin
            # is what actually got selected, MODEL_PIN_UNAVAILABLE when a pin exists but the
            # pinned identity was excluded/absent and the dynamic pick prevailed. Purely
            # additive to reason_codes, same discipline as RUNTIME_REDIRECTED above.
            if pin:
                marker = "MODEL_PINNED" if (selected.provider, selected.model) == pin else "MODEL_PIN_UNAVAILABLE"
                redirect_reason = redirect_reason + (f"{marker} {pin[0]}/{pin[1]}",)
            if self.simulate or role_class != "writer":
                # SEC-A01: independence_verified is positive proof, never inferred from the absence of a
                # reason code — true only for a review decision that matched a real terminal writer and
                # survived the family+model+provider hard exclusions above (REVIEW_MODEL_CONFLICT added
                # 012 repair SEC-001); an unverified reviewer never sets it.
                verified = role_class == "review" and writer is not None and not unverified
                return RouteDecision(*identity, False,
                                     (("REVIEW_IDENTITY_UNVERIFIED",) if unverified else ()) + redirect_reason,
                                     tuple(exclusions), fallback, independence_verified=verified,
                                     bias_class=bias_class, preference_configured=preference_configured)
            # The static binding is recomputed from the route's canonical fields and the
            # identity is revalidated against a fresh on-disk snapshot before the durable,
            # one-use authorization. Inventory was probed fresh for this invocation;
            # re-probing per authorization is an approved exception (ADR-0005 R3).
            recomputed = StaticRoute.identifier(selected.catalog_version, selected.provider, selected.model, selected.family,
                                                selected.effort, (selected.tier,), selected.roles, selected.tools, selected.curated_priority)
            try:
                fresh = self._recheck()
            except RoutingError:
                return RouteDecision(None,None,None,None,None,None,False,("CATALOG_INVALID",),bias_class=bias_class,preference_configured=preference_configured)
            if recomputed != selected.route_id or not fresh.identity_allowed(identity) or (fallback and not fresh.identity_allowed(fallback)):
                return RouteDecision(None,None,None,None,None,None,False,("AUTHORIZATION_INVALID",),bias_class=bias_class,preference_configured=preference_configured)
            # AC-01: `identity[1]`/`fallback[1]` ARE the effective runtimes already computed
            # per-candidate in the exclusion loop above (identity index 1 in the
            # `(route_id, runtime, provider, model, family, effort)` tuple) — reused here
            # rather than recomputed, so the post-selection re-check can never drift from
            # what the candidate was actually authorized under, including for a fallback on
            # a DIFFERENT provider than `selected` (each carries its own effective runtime).
            if selected.model not in self.inventory.get((identity[1], selected.provider), frozenset()):
                return RouteDecision(None,None,None,None,None,None,False,("PROVIDER_UNAUTHENTICATED",),bias_class=bias_class,preference_configured=preference_configured)
            # AM-2 fresh-selected: the cache only filtered candidates; the pair that is about to be
            # durably authorized (and the fallback's, if different) is re-probed fresh right now.
            if self._reprobe is not None:
                pairs = {(identity[1], selected.provider)}
                if fallback: pairs.add((fallback[1], fallback[2]))
                try:
                    verified = self._reprobe(sorted(pairs))
                except Exception:
                    return RouteDecision(None,None,None,None,None,None,False,("PROVIDER_UNAUTHENTICATED",),bias_class=bias_class,preference_configured=preference_configured)
                if selected.model not in verified.get((identity[1], selected.provider), set()):
                    # ADR-0034 (AC-08): the top pick failed its fresh reprobe -- drop it and
                    # retry with the NEXT already-filtered candidate rather than aborting;
                    # only exhausting every candidate returns PROVIDER_UNAUTHENTICATED.
                    # F-04 (P1 repair): the dropped candidate leaves a trace in the durable
                    # `exclusions` list -- additive only, same discipline as
                    # RUNTIME_REDIRECTED/MODEL_PIN_UNAVAILABLE above: never replaces or
                    # reorders an existing exclusion, never changes success/runtime/
                    # identity/fallback. Without this, a winner that was NOT the top-ranked
                    # candidate shows up in decisions-v1.jsonl with no explanation at all.
                    exclusions.append({"route_id": selected.route_id,
                                        "reason": f"REPROBE_REJECTED {selected.provider}/{selected.model}"})
                    candidates = candidates[1:]
                    if not candidates:
                        return RouteDecision(None,None,None,None,None,None,False,("PROVIDER_UNAUTHENTICATED",),bias_class=bias_class,preference_configured=preference_configured)
                    continue
                if fallback and fallback[3] not in verified.get((fallback[1], fallback[2]), set()):
                    fallback = None  # an unverified fallback is dropped, never durably offered
            break
        run_id = self.store.new_run_id()
        nonce = self._issuer.mint(identity, fallback, facts.role, role_class, self.snapshot)
        try:
            self.store._authorize_issued(run_id, nonce, identity, fallback, facts.role, role_class, self.snapshot)
        except RoutingError as exc:
            return RouteDecision(None,None,None,None,None,None,False,(str(exc),),bias_class=bias_class,preference_configured=preference_configured)
        return RouteDecision(*identity, True, redirect_reason, tuple(exclusions), fallback, run_id,
                             bias_class=bias_class, preference_configured=preference_configured)

    def _role_class(self, role):
        item = self.roster.get(role)
        if not item: raise RoutingError("FACTS_INCOMPLETE")
        if item["capability"] == "code-rw": return "writer"
        if item["capability"] == "review-ro" and item["duty"] in {"audit", "judge"}: return "review"
        return "other"
