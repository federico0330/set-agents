"""026-orquestador-elige-modelo, P2 (AC-04..AC-07) -- `--route-decide`'s ephemeral,
per-instance `model_request`.

New tests only, additive alongside the existing immutable suites. This file proves the
central AC-05 claim directly, service-level: `model_request` is a soft SORT factor that
runs strictly AFTER the hard-exclusion loop (`RoutingService.route`, service.py) --
never before it, never able to widen the candidate set past a hard barrier
(REVIEW_PROVIDER_CONFLICT, REVIEW_MODEL_CONFLICT, TIER_INSUFFICIENT,
PROVIDER_UNAUTHENTICATED for a never-audited pair, or a model simply absent from the
curated catalog/ceiling). One test per barrier (AC-05), a positive control proving the
preference DOES move the order among genuinely eligible candidates, an explicit
before/after-the-exclusion-loop comparison, AC-04's closed descriptor-key set, AC-06's
named "why not" reason code, and AC-07's ephemerality (never written to
`model-preference.toml`, never leaks into a later decision).
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ai/scripts"))

import models_config  # noqa: E402
import routing  # noqa: E402
import set_agents_app  # noqa: E402
from routing_core.domain import CatalogSnapshot, StaticRoute  # noqa: E402

_ROSTER = models_config.load_roster(ROOT / "roles.tsv")
_FULL_ROLES = ("implementer", "package-reviewer")
_TOOLS = ("read", "shell", "write")


def _route(provider, model, tier, family, roles=_FULL_ROLES, effort="medium", curated_priority=1):
    rid = StaticRoute.identifier(2, provider, model, family, effort, (tier,), roles, _TOOLS, curated_priority)
    return StaticRoute(2, provider, model, family, effort, tier, roles, _TOOLS, curated_priority, rid)


def _facts(role, runtime, **changes):
    data = dict(role=role, operation="change", task_class="documentation", read_write="write",
                write_started=False, risk="low", criticality="", affected_surfaces=(),
                required_tools=("read",), context_required=True, context_present=True,
                critical_coverage=True, selected_runtime=runtime)
    data.update(changes)
    return data


@unittest.skipIf(os.name != "posix", "routing store requires POSIX file locking (WAL mode)")
class ModelRequestBarrierTests(unittest.TestCase):
    """AC-05: one test per named barrier -- the requested model is denied, the denial
    names the barrier, and a genuinely eligible alternative still wins. Nothing here
    ever asserts through `set_agents_app._decide_status`/the CLI envelope's ok/exit
    classification -- that helper's `_DECIDE_OK_NON_EXECUTABLE_REASONS` closed-tuple
    check (routing_cli.py) only special-cases `RUNTIME_REDIRECTED`/`BILLING_RANK `
    prefixes. 027 PKG-3 (D-5/AC-07) closed the gap this docstring used to describe for
    `MODEL_PINNED` and this AC's own `MODEL_REQUEST_APPLIED`/`MODEL_REQUEST_UNAVAILABLE`
    markers (see `tests/test_routing.py::test_decide_status_helper_matrix` and
    `test_route_decide_cli_hermetic_matrix`) -- a VERIFIED review decision carrying any
    of those three no longer misclassifies as ok=false at the CLI layer.
    `MODEL_PIN_UNAVAILABLE` (pre-existing, ADR-0032) is deliberately NOT one of them: it
    is a known, measured gap, out of 027 PKG-3's approved AC-07 scope (spec.md D-5 names
    only `MODEL_PINNED` and the two `MODEL_REQUEST_*` codes), recorded as an
    orchestrator decision rather than silently widened here. Every assertion below still
    reads `RouteDecision` fields directly (`.provider`, `.model`, `.exclusions`,
    `.reason_codes`, `.independence_verified`), never the CLI's ok/exit computation --
    that discipline is unaffected by the gap narrowing."""

    def _service(self, snapshot, inventory, td):
        return routing.RoutingService._for_tests(
            snapshot, _ROSTER, inventory, routing.RoutingStore._for_tests(Path(td) / "state"))

    def test_review_provider_conflict_barrier_denies_the_requested_model(self):
        # "El usuario pidió poder elegir, no poder saltear": a model sharing the
        # writer's PROVIDER is exactly what reviewer independence forbids -- requesting
        # it explicitly must still be denied.
        writer_route = _route("anthropic", "opus", "frontier", "opus")
        same_provider_reviewer = _route("anthropic", "sonnet", "frontier", "sonnet")
        alt_reviewer = _route("opencode-zen", "kimi-k2.7-code", "frontier", "kimi")
        identities = frozenset(
            (r.route_id, "opencode", r.provider, r.model, r.family, r.effort)
            for r in (writer_route, same_provider_reviewer, alt_reviewer))
        snapshot = CatalogSnapshot((writer_route, same_provider_reviewer, alt_reviewer), identities)
        inventory = {("opencode", "anthropic"): {"opus", "sonnet"}, ("opencode", "opencode-zen"): {"kimi-k2.7-code"}}
        with tempfile.TemporaryDirectory() as td:
            svc = self._service(snapshot, inventory, td)
            writer = svc.route(routing.TaskRequest("implementer", "change", "documentation", selected_runtime="opencode"),
                               svc._observe_for_invocation(**_facts("implementer", "opencode")))
            self.assertTrue(writer.execution_enabled, writer.reason_codes)
            svc.store.mark_dispatched(writer.run_id); svc.store.close_run(writer.run_id, "success")
            review_facts = svc._observe_for_invocation(
                **_facts("package-reviewer", "opencode", operation="inspection", read_write="read"))
            review = svc.route(
                routing.TaskRequest("package-reviewer", "inspection", "documentation", selected_runtime="opencode"),
                review_facts, review_of_run_id=writer.run_id, model_request=("anthropic", "sonnet"))
        # Denied: the requested identity never wins.
        self.assertNotEqual((review.provider, review.model), ("anthropic", "sonnet"))
        self.assertEqual((review.provider, review.model), ("opencode-zen", "kimi-k2.7-code"))
        self.assertTrue(review.independence_verified)
        # The exclusion carries the barrier's own name.
        self.assertIn({"route_id": same_provider_reviewer.route_id, "reason": "REVIEW_PROVIDER_CONFLICT"},
                      review.exclusions)
        # AC-06: the decision's own reason_codes name the requested model and why.
        self.assertIn("MODEL_REQUEST_UNAVAILABLE requested=anthropic/sonnet reason=REVIEW_PROVIDER_CONFLICT",
                      review.reason_codes)

    def test_review_model_conflict_barrier_denies_the_requested_model(self):
        # Same underlying model, different provider spelling (the real, documented
        # anthropic/opus <-> opencode-zen/claude-opus-4-8 alias, `catalog.canonical_model`)
        # -- REVIEW_MODEL_CONFLICT, the layer-2 defense-in-depth exclusion (repair SEC-001).
        writer_route = _route("anthropic", "opus", "frontier", "opus")
        alias_reviewer = _route("opencode-zen", "claude-opus-4-8", "frontier", "claude-opus")
        alt_reviewer = _route("opencode-go", "kimi-k3", "frontier", "kimi")
        identities = frozenset(
            (r.route_id, "opencode", r.provider, r.model, r.family, r.effort)
            for r in (writer_route, alias_reviewer, alt_reviewer))
        snapshot = CatalogSnapshot((writer_route, alias_reviewer, alt_reviewer), identities)
        inventory = {("opencode", "anthropic"): {"opus"}, ("opencode", "opencode-zen"): {"claude-opus-4-8"},
                     ("opencode", "opencode-go"): {"kimi-k3"}}
        with tempfile.TemporaryDirectory() as td:
            svc = self._service(snapshot, inventory, td)
            writer = svc.route(routing.TaskRequest("implementer", "change", "documentation", selected_runtime="opencode"),
                               svc._observe_for_invocation(**_facts("implementer", "opencode")))
            self.assertTrue(writer.execution_enabled, writer.reason_codes)
            svc.store.mark_dispatched(writer.run_id); svc.store.close_run(writer.run_id, "success")
            review_facts = svc._observe_for_invocation(
                **_facts("package-reviewer", "opencode", operation="inspection", read_write="read"))
            review = svc.route(
                routing.TaskRequest("package-reviewer", "inspection", "documentation", selected_runtime="opencode"),
                review_facts, review_of_run_id=writer.run_id, model_request=("opencode-zen", "claude-opus-4-8"))
        self.assertNotEqual((review.provider, review.model), ("opencode-zen", "claude-opus-4-8"))
        self.assertEqual((review.provider, review.model), ("opencode-go", "kimi-k3"))
        self.assertTrue(review.independence_verified)
        self.assertIn({"route_id": alias_reviewer.route_id, "reason": "REVIEW_MODEL_CONFLICT"}, review.exclusions)
        self.assertIn("MODEL_REQUEST_UNAVAILABLE requested=opencode-zen/claude-opus-4-8 reason=REVIEW_MODEL_CONFLICT",
                      review.reason_codes)

    def test_tier_insufficient_barrier_denies_the_requested_model(self):
        # `implementation`+`low` risk requires `balanced` (routing_core.domain.required_tier).
        # The requested candidate only reaches `fast` -- TIER_INSUFFICIENT.
        fast_candidate = _route("openai-codex", "gpt-5.6-sol", "fast", "gpt-5.6", roles=("implementer",))
        balanced_candidate = _route("opencode-zen", "kimi-k2.7-code", "balanced", "kimi", roles=("implementer",))
        identities = frozenset(
            (r.route_id, "opencode", r.provider, r.model, r.family, r.effort)
            for r in (fast_candidate, balanced_candidate))
        snapshot = CatalogSnapshot((fast_candidate, balanced_candidate), identities)
        inventory = {("opencode", "openai-codex"): {"gpt-5.6-sol"}, ("opencode", "opencode-zen"): {"kimi-k2.7-code"}}
        with tempfile.TemporaryDirectory() as td:
            svc = self._service(snapshot, inventory, td)
            facts = svc._observe_for_invocation(**_facts("implementer", "opencode", task_class="implementation"))
            decision = svc.route(
                routing.TaskRequest("implementer", "change", "implementation", selected_runtime="opencode"),
                facts, model_request=("openai-codex", "gpt-5.6-sol"))
        self.assertTrue(decision.execution_enabled, decision.reason_codes)
        self.assertNotEqual((decision.provider, decision.model), ("openai-codex", "gpt-5.6-sol"))
        self.assertEqual((decision.provider, decision.model), ("opencode-zen", "kimi-k2.7-code"))
        self.assertIn({"route_id": fast_candidate.route_id, "reason": "TIER_INSUFFICIENT"}, decision.exclusions)
        self.assertIn("MODEL_REQUEST_UNAVAILABLE requested=openai-codex/gpt-5.6-sol reason=TIER_INSUFFICIENT",
                      decision.reason_codes)

    def test_unaudited_pair_barrier_denies_the_requested_model(self):
        # "Par no auditado": the (runtime, provider) pair the requested candidate would
        # need is never in `_PAIR_COMMANDS`/never authenticated -- `route()` cannot
        # structurally distinguish "genuinely never audited" from "audited but not
        # currently authenticated"; both surface as PROVIDER_UNAUTHENTICATED, which is
        # the honest, accurate reason either way.
        eligible = _route("anthropic", "opus", "balanced", "opus", roles=("implementer",))
        unaudited = _route("opencode-zen", "kimi-k2.7-code", "balanced", "kimi", roles=("implementer",))
        identities = frozenset(
            (r.route_id, "claude-code", r.provider, r.model, r.family, r.effort)
            for r in (eligible, unaudited))
        snapshot = CatalogSnapshot((eligible, unaudited), identities)
        # The opencode-zen pair is simply absent -- never probed, never authenticated.
        inventory = {("claude-code", "anthropic"): {"opus"}}
        with tempfile.TemporaryDirectory() as td:
            svc = self._service(snapshot, inventory, td)
            facts = svc._observe_for_invocation(**_facts("implementer", "claude-code", task_class="implementation"))
            decision = svc.route(
                routing.TaskRequest("implementer", "change", "implementation", selected_runtime="claude-code"),
                facts, model_request=("opencode-zen", "kimi-k2.7-code"))
        self.assertTrue(decision.execution_enabled, decision.reason_codes)
        self.assertNotEqual((decision.provider, decision.model), ("opencode-zen", "kimi-k2.7-code"))
        self.assertEqual((decision.provider, decision.model), ("anthropic", "opus"))
        self.assertIn({"route_id": unaudited.route_id, "reason": "PROVIDER_UNAUTHENTICATED"}, decision.exclusions)
        self.assertIn("MODEL_REQUEST_UNAVAILABLE requested=opencode-zen/kimi-k2.7-code reason=PROVIDER_UNAUTHENTICATED",
                      decision.reason_codes)

    def test_catalog_ceiling_barrier_denies_a_model_outside_the_curated_set(self):
        # "Techo de catalogo" (resolve_ceiling, 022/P2): a model outside the curated
        # ceiling never becomes a `StaticRoute` at all (`catalog.build_snapshot`) -- by
        # the time `route()` runs, that is observably identical to "not in the
        # catalog", which is exactly what this test proves against the REAL,
        # production catalog (`ai/catalogs/routes.v1.toml` + `models.toml`), not a
        # synthetic snapshot -- "opencode-zen" is a real, valid provider (so this is
        # not simply another unaudited-pair case), the specific model id just never
        # was curated.
        config = models_config.load_config(ROOT / "models.toml")
        inventory = {("codex", "openai-codex"): set(config["catalog"]["codex"])}
        with tempfile.TemporaryDirectory() as td:
            svc = routing._compose_for_tests(config, _ROSTER, inventory, Path(td) / "state", simulate=False)
            facts = svc._observe_for_invocation(**_facts("implementer", "codex", task_class="mechanical"))
            decision = svc.route(
                routing.TaskRequest("implementer", "change", "mechanical", selected_runtime="codex"),
                facts, model_request=("opencode-zen", "definitely-not-a-curated-model-xyz"))
        self.assertTrue(decision.execution_enabled, decision.reason_codes)
        self.assertNotEqual((decision.provider, decision.model),
                            ("opencode-zen", "definitely-not-a-curated-model-xyz"))
        self.assertIn(
            "MODEL_REQUEST_UNAVAILABLE requested=opencode-zen/definitely-not-a-curated-model-xyz reason=NOT_IN_CATALOG",
            decision.reason_codes)

    def test_model_request_applied_when_the_requested_model_is_genuinely_eligible(self):
        # Positive control: two same-tier, same-billing-kind candidates that would
        # otherwise tie-break on `curated_priority` (route_a wins by default);
        # requesting route_b flips the winner -- proving `model_request` really is a
        # live sort factor, not dead code.
        route_a = _route("openai-codex", "gpt-5.6-sol", "balanced", "gpt-5.6", roles=("implementer",), curated_priority=1)
        route_b = _route("opencode-go", "kimi-k3", "balanced", "kimi", roles=("implementer",), curated_priority=5)
        identities = frozenset(
            (r.route_id, "opencode", r.provider, r.model, r.family, r.effort) for r in (route_a, route_b))
        snapshot = CatalogSnapshot((route_a, route_b), identities)
        inventory = {("opencode", "openai-codex"): {"gpt-5.6-sol"}, ("opencode", "opencode-go"): {"kimi-k3"}}
        with tempfile.TemporaryDirectory() as td:
            svc = self._service(snapshot, inventory, td)
            facts = svc._observe_for_invocation(**_facts("implementer", "opencode", task_class="implementation"))
            default = svc.route(
                routing.TaskRequest("implementer", "change", "implementation", selected_runtime="opencode"), facts)
        self.assertEqual((default.provider, default.model), ("openai-codex", "gpt-5.6-sol"))
        with tempfile.TemporaryDirectory() as td:
            svc = self._service(snapshot, inventory, td)
            facts = svc._observe_for_invocation(**_facts("implementer", "opencode", task_class="implementation"))
            biased = svc.route(
                routing.TaskRequest("implementer", "change", "implementation", selected_runtime="opencode"),
                facts, model_request=("opencode-go", "kimi-k3"))
        self.assertEqual((biased.provider, biased.model), ("opencode-go", "kimi-k3"))
        self.assertIn("MODEL_REQUEST_APPLIED opencode-go/kimi-k3", biased.reason_codes)

    def test_model_request_outranked_when_eligible_but_a_lower_tier_still_wins(self):
        # AC-06's third bucket: the requested candidate is NOT hard-excluded (it is a
        # genuinely eligible route, unlike the 5 barrier tests above) but a DIFFERENT,
        # lower-tier candidate still wins -- tier ordering predates this AC and
        # `model_request` never outranks it (`service.py` sort key: TIER_ORDER sits
        # BEFORE the new factor). "Eligible" is not the same as "chosen", and this is
        # still named, never silent.
        fast_candidate = _route("openai-codex", "gpt-5.6-sol", "fast", "gpt-5.6", roles=("implementer",))
        balanced_candidate = _route("opencode-zen", "kimi-k2.7-code", "balanced", "kimi", roles=("implementer",))
        identities = frozenset(
            (r.route_id, "opencode", r.provider, r.model, r.family, r.effort)
            for r in (fast_candidate, balanced_candidate))
        snapshot = CatalogSnapshot((fast_candidate, balanced_candidate), identities)
        inventory = {("opencode", "openai-codex"): {"gpt-5.6-sol"}, ("opencode", "opencode-zen"): {"kimi-k2.7-code"}}
        with tempfile.TemporaryDirectory() as td:
            svc = self._service(snapshot, inventory, td)
            # `documentation`+`low` needs only `fast` (routing_core.domain.required_tier)
            # -- BOTH candidates are eligible (a higher tier always satisfies a lower
            # floor), so `balanced_candidate` is not hard-excluded here.
            facts = svc._observe_for_invocation(**_facts("implementer", "opencode", task_class="documentation"))
            decision = svc.route(
                routing.TaskRequest("implementer", "change", "documentation", selected_runtime="opencode"),
                facts, model_request=("opencode-zen", "kimi-k2.7-code"))
        self.assertNotIn({"route_id": balanced_candidate.route_id, "reason": "TIER_INSUFFICIENT"}, decision.exclusions)
        self.assertEqual((decision.provider, decision.model), ("openai-codex", "gpt-5.6-sol"))
        self.assertIn("MODEL_REQUEST_UNAVAILABLE requested=opencode-zen/kimi-k2.7-code reason=OUTRANKED",
                      decision.reason_codes)

    def test_model_request_enters_after_the_exclusion_loop_never_before_it(self):
        # The sharpest, most direct proof of AC-05's central claim: for the SAME
        # scenario, the exclusion list (and the winner) is BYTE-IDENTICAL with and
        # without `model_request` set to a value that violates a hard exclusion --
        # the preference never touches the exclusion loop's own output, only the
        # sort ordering of whatever the loop already let through.
        writer_route = _route("anthropic", "opus", "frontier", "opus")
        same_provider_reviewer = _route("anthropic", "sonnet", "frontier", "sonnet")
        alt_reviewer = _route("opencode-zen", "kimi-k2.7-code", "frontier", "kimi")
        identities = frozenset(
            (r.route_id, "opencode", r.provider, r.model, r.family, r.effort)
            for r in (writer_route, same_provider_reviewer, alt_reviewer))
        snapshot = CatalogSnapshot((writer_route, same_provider_reviewer, alt_reviewer), identities)
        inventory = {("opencode", "anthropic"): {"opus", "sonnet"}, ("opencode", "opencode-zen"): {"kimi-k2.7-code"}}

        def _review(model_request):
            with tempfile.TemporaryDirectory() as td:
                svc = self._service(snapshot, inventory, td)
                writer = svc.route(routing.TaskRequest("implementer", "change", "documentation", selected_runtime="opencode"),
                                   svc._observe_for_invocation(**_facts("implementer", "opencode")))
                svc.store.mark_dispatched(writer.run_id); svc.store.close_run(writer.run_id, "success")
                review_facts = svc._observe_for_invocation(
                    **_facts("package-reviewer", "opencode", operation="inspection", read_write="read"))
                return svc.route(
                    routing.TaskRequest("package-reviewer", "inspection", "documentation", selected_runtime="opencode"),
                    review_facts, review_of_run_id=writer.run_id, model_request=model_request)

        without_request = _review(None)
        with_request = _review(("anthropic", "sonnet"))  # the violating identity, explicitly requested
        # Same excluded set (the barrier reasons are untouched by the preference)...
        self.assertEqual(without_request.exclusions, with_request.exclusions)
        # ...and the same winner (no bypass: the preference could not smuggle the
        # violating identity past the exclusion loop it never runs before).
        self.assertEqual((without_request.provider, without_request.model),
                         (with_request.provider, with_request.model))
        # The only observable difference is the additive, honest "why not" marker.
        self.assertFalse(any(c.startswith("MODEL_REQUEST_") for c in without_request.reason_codes))
        self.assertIn("MODEL_REQUEST_UNAVAILABLE requested=anthropic/sonnet reason=REVIEW_PROVIDER_CONFLICT",
                      with_request.reason_codes)


class ModelRequestDescriptorValidationTests(unittest.TestCase):
    """AC-04: `_validate_model_request` -- the value-shape validator `cmd_route_decide`
    calls for the ONE new closed-set key."""

    def test_valid_provider_model_string_parses(self):
        self.assertEqual(set_agents_app._validate_model_request("openai-codex/gpt-5.6-sol"),
                         ("openai-codex", "gpt-5.6-sol"))

    def test_malformed_shapes_all_raise_value_error(self):
        for bad in ("openai-codex", "not-a-real-provider/gpt-5.6-sol", "openai-codex/bad model!",
                    "openai-codex/", "/gpt-5.6-sol", 5, None, [], {"provider": "openai-codex"}):
            with self.assertRaises(ValueError, msg=bad):
                set_agents_app._validate_model_request(bad)


@unittest.skipIf(os.name != "posix", "routing store requires POSIX file locking (WAL mode)")
class ModelRequestCliTests(unittest.TestCase):
    """AC-04 (closed key set, end to end via the real CLI) / AC-06 (the marker reaches
    the JSON envelope) / AC-07 (ephemeral: nothing written, nothing leaks into the next
    decision) -- writer-role scenarios throughout. These scenarios never needed the
    review-role `_decide_status` gap documented on `ModelRequestBarrierTests` above (that
    gap, now narrowed to `MODEL_PIN_UNAVAILABLE` only by 027 PKG-3, only ever affected a
    VERIFIED review-role decision, never a writer one) -- writer-role coverage here was
    always independent of it, not a sidestep of a still-open hole."""

    def _probe_stubs(self, td):
        # Same fixture shape as tests/test_routing.py's `_probe_stubs`: codex/claude
        # report authenticated, opencode lists exactly `openai/gpt-5.6-sol`.
        bins = Path(td) / "bin"; bins.mkdir(); log = Path(td) / "probes.log"
        scripts = {
            "codex": '#!/bin/sh\necho "$0 $@" >> %s\necho "Logged in using ChatGPT" 1>&2\n' % log,
            "claude": '#!/bin/sh\necho "$0 $@" >> %s\necho \'{"loggedIn": true}\'\n' % log,
            "opencode": ('#!/bin/sh\necho "$0 $@" >> %s\n'
                         'if [ "$1" = "auth" ]; then printf "\\342\\227\\217  OpenAI oauth\\n"; exit 0; fi\n'
                         'if [ "$2" = "openai" ]; then echo "openai/gpt-5.6-sol"; exit 0; fi\n'
                         'echo "Error: Provider not found: $2"; exit 0\n') % log,
        }
        for name, body in scripts.items():
            path = bins / name; path.write_text(body); path.chmod(0o755)
        return bins, log

    def _cli_env(self, routing_root, state_dir, bins=None):
        env = dict(os.environ)
        env["SET_AGENTS_ROUTING_TEST_ROOT"] = str(routing_root)
        env["SET_AGENTS_STATE"] = str(state_dir)  # AC-07: redirects MODEL_PREFERENCE_PATH too
        if bins is not None: env["PATH"] = f"{bins}:{env['PATH']}"
        return env

    def _cli_run(self, args, env, input_text=None):
        return subprocess.run([sys.executable, "ai/scripts/set_agents_app.py", *args],
                              cwd=ROOT, text=True, capture_output=True, env=env, input=input_text)

    def test_unknown_key_still_rejected_after_model_request_joins_the_allowed_set(self):
        # AC-04: the closed set gained exactly ONE key -- an unrelated bogus key is
        # still a PARSE failure, exit 2. Fails before any catalog/probe access, so no
        # stub bins/temp roots are needed at all.
        env = dict(os.environ)
        descriptor = json.dumps({"role": "implementer", "task_class": "mechanical", "bogus_key": "x"})
        result = self._cli_run(["--route-decide", "-", "--json"], env, descriptor)
        self.assertEqual(result.returncode, 2, (result.stdout, result.stderr))
        self.assertIn("ROUTING_INPUT_INVALID", result.stdout)

    def test_malformed_model_request_value_is_a_parse_error_not_a_silent_degrade(self):
        env = dict(os.environ)
        for bad in ("openai-codex", "not-a-real-provider/gpt-5.6-sol", "openai-codex/bad model!"):
            descriptor = json.dumps({"role": "implementer", "task_class": "mechanical", "model_request": bad})
            result = self._cli_run(["--route-decide", "-", "--json"], env, descriptor)
            self.assertEqual(result.returncode, 2, (bad, result.stdout, result.stderr))
            self.assertIn("ROUTING_INPUT_INVALID", result.stdout)

    def test_valid_model_request_key_flows_end_to_end_and_names_itself_when_applied(self):
        # The catalog's own default winner for mechanical+codex is openai-codex/gpt-5.6-luna
        # (curated_priority 10); anthropic/haiku is a second, genuinely eligible fast-tier
        # candidate (curated_priority 20) -- requesting it by name must flip the pick.
        with tempfile.TemporaryDirectory() as td:
            bins, _log = self._probe_stubs(td)
            env = self._cli_env(Path(td) / "routing-root", Path(td) / "state", bins)
            descriptor = json.dumps({"role": "implementer", "task_class": "mechanical",
                                     "selected_runtime": "codex", "model_request": "anthropic/haiku"})
            result = self._cli_run(["--route-decide", "-", "--json"], env, descriptor)
        self.assertEqual(result.returncode, 0, (result.stdout, result.stderr))
        data = json.loads(result.stdout)["data"]
        self.assertTrue(data["execution_enabled"])
        self.assertEqual((data["provider"], data["model"]), ("anthropic", "haiku"))
        self.assertIn("MODEL_REQUEST_APPLIED anthropic/haiku", data["reason_codes"])

    def test_model_request_never_writes_model_preference_toml(self):
        # AC-07: ephemeral -- the sibling preference file never even gets CREATED by a
        # `--route-decide` call carrying `model_request`.
        with tempfile.TemporaryDirectory() as td:
            bins, _log = self._probe_stubs(td)
            state_dir = Path(td) / "state"
            env = self._cli_env(Path(td) / "routing-root", state_dir, bins)
            descriptor = json.dumps({"role": "implementer", "task_class": "mechanical",
                                     "selected_runtime": "codex", "model_request": "openai-codex/gpt-5.6-sol"})
            result = self._cli_run(["--route-decide", "-", "--json"], env, descriptor)
            self.assertEqual(result.returncode, 0, (result.stdout, result.stderr))
            self.assertFalse((state_dir / "model-preference.toml").exists())

    def test_model_request_does_not_bias_a_later_decide_call_without_it(self):
        # AC-07: never alters the persistent pin/preference state a LATER decision
        # (same process lifetime, same routing root) reads -- the baseline winner
        # (openai-codex/gpt-5.6-luna) before and after an intervening call that
        # requests, and gets, the DIFFERENT eligible anthropic/haiku identity is
        # unchanged.
        with tempfile.TemporaryDirectory() as td:
            bins, _log = self._probe_stubs(td)
            env = self._cli_env(Path(td) / "routing-root", Path(td) / "state", bins)
            plain_descriptor = json.dumps({"role": "implementer", "task_class": "mechanical",
                                           "selected_runtime": "codex"})
            baseline = self._cli_run(["--route-decide", "-", "--json"], env, plain_descriptor)
            self.assertEqual(baseline.returncode, 0, (baseline.stdout, baseline.stderr))
            baseline_model = json.loads(baseline.stdout)["data"]["model"]
            requested_descriptor = json.dumps({"role": "implementer", "task_class": "mechanical",
                                               "selected_runtime": "codex",
                                               "model_request": "anthropic/haiku"})
            biased = self._cli_run(["--route-decide", "-", "--json"], env, requested_descriptor)
            self.assertEqual(biased.returncode, 0, (biased.stdout, biased.stderr))
            self.assertEqual(json.loads(biased.stdout)["data"]["model"], "haiku")
            after = self._cli_run(["--route-decide", "-", "--json"], env, plain_descriptor)
            self.assertEqual(after.returncode, 0, (after.stdout, after.stderr))
            self.assertEqual(json.loads(after.stdout)["data"]["model"], baseline_model)
            self.assertNotEqual(baseline_model, "haiku")


if __name__ == "__main__":
    unittest.main()
