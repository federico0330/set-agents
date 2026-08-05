"""ADR-0032 — materialización en el spawn para opencode/codex y pins de modelo.

New tests only. The immutable suites keep pinning the six-role tiered roster, the
tiered-sentence regex and routing.db's DDL; this file proves the ADDITIVE layer:
per-lane argv composition (the `test_pi_effort.py` style), pin > dynamic precedence
at the service, the [model_pin] config round-trip, the new allowlist entries, the
wizard policy panel, and the doctrine markers.
"""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ai/scripts"))

import codex_spawn as cx  # noqa: E402
import coord_policy  # noqa: E402
import models_config  # noqa: E402
import opencode_spawn as oc  # noqa: E402
import routing  # noqa: E402
import set_agents_app  # noqa: E402
import setup_models  # noqa: E402
from routing_core.domain import CatalogSnapshot, StaticRoute  # noqa: E402


class _Proc:
    def __init__(self, stdout="", stderr="", returncode=0):
        self.stdout, self.stderr, self.returncode = stdout, stderr, returncode


_ROSTER = models_config.load_roster(ROOT / "roles.tsv")


class OpencodeArgvTests(unittest.TestCase):
    def test_model_ref_mapping_per_provider(self):
        self.assertEqual(oc.opencode_model_ref("openai-codex", "gpt-5.6-sol"), "openai/gpt-5.6-sol")
        self.assertEqual(oc.opencode_model_ref("opencode-zen", "kimi-k3"), "opencode/kimi-k3")
        self.assertEqual(oc.opencode_model_ref("opencode-go", "glm-5.2"), "opencode-go/glm-5.2")
        with self.assertRaises(oc.SpawnError):
            oc.opencode_model_ref("anthropic", "opus")  # the claude-code redirect owns it

    def test_valid_effort_becomes_variant_flag_before_the_agent(self):
        argv = oc.compose_argv("architect", "openai-codex", "gpt-5.6-sol", effort="high")
        index = argv.index("--variant")
        self.assertEqual(argv[index + 1], "high")
        self.assertLess(argv.index("-m"), index)
        self.assertEqual(argv[argv.index("--agent") + 1], "architect")

    def test_absent_or_unknown_effort_omits_the_flag(self):
        self.assertNotIn("--variant", oc.compose_argv("architect", "openai-codex", "gpt-5.6-sol"))
        argv = oc.compose_argv("architect", "openai-codex", "gpt-5.6-sol", effort="turbo-9000")
        self.assertNotIn("--variant", argv)
        self.assertNotIn("turbo-9000", argv)

    def test_every_route_effort_level_is_a_valid_variant_level(self):
        for effort in ("low", "medium", "high", "xhigh"):
            self.assertIn(effort, oc._OPENCODE_VARIANT_LEVELS)

    def test_task_rides_stdin_never_argv(self):
        # F-01 (review repair): a positional task would hit MAX_ARG_STRLEN (128 KiB per
        # argv element) on a real review diff and expose the text in /proc/<pid>/cmdline;
        # stdin has neither problem and removes the flag-injection channel outright.
        captured = {}

        def fake_run(argv, **kwargs):
            captured["argv"], captured["input"] = list(argv), kwargs.get("input")
            return _Proc(returncode=1)

        with mock.patch.object(oc.subprocess, "run", side_effect=fake_run):
            oc.spawn("architect", "--auto looks-like-a-flag", "openai-codex", "gpt-5.6-sol", _ROSTER)
        self.assertEqual(captured["argv"][-1], "json")  # argv ends at --format json, no positional
        self.assertNotIn("--auto looks-like-a-flag", captured["argv"])
        self.assertEqual(captured["input"], "--auto looks-like-a-flag")

    def test_never_composes_auto_approve(self):
        argv = oc.compose_argv("architect", "openai-codex", "gpt-5.6-sol", effort="high")
        self.assertNotIn("--auto", argv)


class CodexArgvTests(unittest.TestCase):
    def test_argv_carries_model_effort_and_developer_instructions(self):
        argv = cx.compose_argv("architect", "gpt-5.6-terra", "read-only", "ROLE PROMPT TEXT",
                               effort="xhigh", output_path="/tmp/out.txt")
        self.assertEqual(argv[argv.index("-m") + 1], "gpt-5.6-terra")
        self.assertIn("model_reasoning_effort=xhigh", argv)
        self.assertTrue(any(item.startswith("developer_instructions=ROLE PROMPT") for item in argv))
        self.assertEqual(argv[-1], "-")  # task rides stdin, never argv
        self.assertIn("--ephemeral", argv)
        for flag in cx._FORBIDDEN_FLAGS:
            self.assertNotIn(flag, argv)

    def test_unknown_effort_omits_the_override(self):
        argv = cx.compose_argv("architect", "gpt-5.6-terra", "read-only", "P", effort="max9000")
        self.assertFalse(any("model_reasoning_effort" in item for item in argv))

    def test_provider_other_than_openai_codex_fails_closed(self):
        with self.assertRaises(cx.SpawnError):
            cx.codex_model_id("anthropic", "opus")
        outcome, detail = cx.spawn("architect", "t", "anthropic", "opus", _ROSTER)
        self.assertEqual((outcome, detail["reason"]), ("failure", "PROVIDER_UNSUPPORTED"))

    def test_sandbox_ceiling_is_decided_by_roster_capability(self):
        self.assertEqual(cx._sandbox_mode("implementer", _ROSTER), "workspace-write")
        self.assertEqual(cx._sandbox_mode("architect", _ROSTER), "workspace-write")  # docs-rw
        self.assertEqual(cx._sandbox_mode("package-reviewer", _ROSTER), "read-only")
        self.assertEqual(cx._sandbox_mode("gate-runner", _ROSTER), "read-only")


class DispatchLifecycleTests(unittest.TestCase):
    def test_opencode_writer_threads_effort_and_closes_the_run(self):
        calls = []

        def fake_cli(args, env=None, cwd=None):
            calls.append(args[0])
            return _Proc(stdout=json.dumps({"ok": True, "data": {}}))

        with mock.patch.object(oc, "_run_app_cli", side_effect=fake_cli), \
             mock.patch.object(oc, "_persist_audit_binding"), \
             mock.patch.object(oc, "spawn", return_value=("success", {})) as spawned:
            result = oc.dispatch_writer("implementer", "task", "run1_" + "a" * 32,
                                        "openai-codex", "gpt-5.6-sol", _ROSTER, effort="xhigh")
        self.assertEqual(result["status"], "success")
        self.assertEqual(spawned.call_args.kwargs["effort"], "xhigh")
        self.assertEqual(calls, ["--route-dispatched", "--route-terminal"])

    def test_codex_writer_threads_effort_and_closes_the_run(self):
        calls = []

        def fake_cli(args, env=None, cwd=None):
            calls.append(args[0])
            return _Proc(stdout=json.dumps({"ok": True, "data": {}}))

        with mock.patch.object(cx, "_run_app_cli", side_effect=fake_cli), \
             mock.patch.object(cx, "_persist_audit_binding"), \
             mock.patch.object(cx, "spawn", return_value=("success", {})) as spawned:
            result = cx.dispatch_writer("implementer", "task", "run1_" + "a" * 32,
                                        "openai-codex", "gpt-5.6-sol", _ROSTER, effort="low")
        self.assertEqual(result["status"], "success")
        self.assertEqual(spawned.call_args.kwargs["effort"], "low")
        self.assertEqual(calls, ["--route-dispatched", "--route-terminal"])

    def test_dispatch_simulate_refuses_writer_and_review_roles_and_does_zero_bookkeeping(self):
        for module in (oc, cx):
            with mock.patch.object(module, "_run_app_cli") as cli, \
                 mock.patch.object(module, "spawn", return_value=("success", {})) as spawned:
                for role in ("implementer", "package-reviewer", "adversarial-judge"):
                    result = module.dispatch_simulate(role, "t", "openai-codex", "gpt-5.6-sol", _ROSTER)
                    self.assertEqual(result["reason"], "ROLE_CLASS_MISMATCH", (module.__name__, role))
                result = module.dispatch_simulate("architect", "t", "openai-codex", "gpt-5.6-sol", _ROSTER)
                self.assertEqual(result["status"], "success", module.__name__)
                self.assertEqual(spawned.call_args.kwargs["expect_class"], "other")
                cli.assert_not_called()  # a simulate decision authorizes nothing durable

    def test_writer_dispatch_refuses_a_review_role_before_any_lifecycle_call(self):
        for module in (oc, cx):
            with mock.patch.object(module, "_run_app_cli") as cli:
                result = module.dispatch_writer("package-reviewer", "t", "run1_" + "a" * 32,
                                                "openai-codex", "gpt-5.6-sol", _ROSTER)
            self.assertEqual(result["reason"], "ROLE_CLASS_MISMATCH", module.__name__)
            cli.assert_not_called()


def _facts(role, runtime="codex", **changes):
    data = dict(role=role, operation="change", task_class="documentation", read_write="write",
                write_started=False, risk="low", criticality="", affected_surfaces=(),
                required_tools=("read",), context_required=True, context_present=True,
                critical_coverage=True, selected_runtime=runtime)
    data.update(changes)
    return data


class PinPrecedenceTests(unittest.TestCase):
    """Pin > dynamic at the service sort, never past a hard exclusion."""

    def setUp(self):
        self.roster = _ROSTER
        roles = tuple(sorted({row["role"] for row in self.roster}))
        tools = ("read", "shell", "write")

        def route(model, tier, priority):
            rid = StaticRoute.identifier(2, "openai-codex", model, "gpt-5.6", "medium",
                                         (tier,), roles, tools, priority)
            return StaticRoute(2, "openai-codex", model, "gpt-5.6", "medium", tier, roles, tools, priority, rid)

        self.fast = route("gpt-5.6-luna", "fast", 1)
        self.frontier = route("gpt-5.6-terra", "frontier", 9)
        identities = frozenset({
            (r.route_id, "codex", r.provider, r.model, r.family, r.effort)
            for r in (self.fast, self.frontier)
        })
        self.snapshot = CatalogSnapshot((self.fast, self.frontier), identities)
        self.inventory = {("codex", "openai-codex"): {"gpt-5.6-luna", "gpt-5.6-terra"}}

    def _decide(self, model_pin=None, inventory=None):
        service = routing.RoutingService._for_tests(
            self.snapshot, self.roster, inventory or self.inventory, simulate=True, model_pin=model_pin)
        request = routing.TaskRequest("architect", "change", "documentation", selected_runtime="codex")
        facts = service._observe_for_invocation(**_facts("architect"))
        return service.route(request, facts)

    def test_unpinned_default_ordering_is_unchanged(self):
        decision = self._decide()
        self.assertEqual(decision.model, "gpt-5.6-luna")  # lowest eligible tier wins
        self.assertFalse(any(code.startswith("MODEL_PIN") for code in decision.reason_codes))

    def test_role_pin_wins_across_tiers_and_reports_model_pinned(self):
        decision = self._decide(model_pin={"architect": ("openai-codex", "gpt-5.6-terra")})
        self.assertEqual(decision.model, "gpt-5.6-terra")
        self.assertIn("MODEL_PINNED openai-codex/gpt-5.6-terra", decision.reason_codes)

    def test_global_star_pin_applies_and_role_pin_beats_it(self):
        decision = self._decide(model_pin={"*": ("openai-codex", "gpt-5.6-terra")})
        self.assertEqual(decision.model, "gpt-5.6-terra")
        decision = self._decide(model_pin={"*": ("openai-codex", "gpt-5.6-terra"),
                                           "architect": ("openai-codex", "gpt-5.6-luna")})
        self.assertEqual(decision.model, "gpt-5.6-luna")
        self.assertIn("MODEL_PINNED openai-codex/gpt-5.6-luna", decision.reason_codes)

    def test_ineligible_pin_degrades_to_dynamic_with_pin_unavailable(self):
        # The pinned model is NOT in the probed inventory: the hard
        # PROVIDER_UNAUTHENTICATED exclusion stands and the dynamic pick prevails.
        decision = self._decide(model_pin={"architect": ("openai-codex", "gpt-5.6-terra")},
                                inventory={("codex", "openai-codex"): {"gpt-5.6-luna"}})
        self.assertEqual(decision.model, "gpt-5.6-luna")
        self.assertIn("MODEL_PIN_UNAVAILABLE openai-codex/gpt-5.6-terra", decision.reason_codes)


class ModelPinConfigTests(unittest.TestCase):
    def test_pin_round_trip_validation_and_isolation(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "model-preference.toml"
            with mock.patch.object(set_agents_app, "MODEL_PREFERENCE_PATH", path):
                set_agents_app.cmd_model_pin_set("architect", "openai-codex/gpt-5.6-terra")
                set_agents_app.cmd_model_pin_set("*", "anthropic/sonnet")
                pins = set_agents_app.load_model_pin()
                self.assertEqual(pins, {"architect": ("openai-codex", "gpt-5.6-terra"),
                                        "*": ("anthropic", "sonnet")})
                # The frozen two-key public shape of load_model_preference survives.
                self.assertEqual(set_agents_app.load_model_preference(),
                                 {"preference": {}, "role_override": {}})
                # An unrelated preference write must PRESERVE the pins (serializer isolation).
                set_agents_app.cmd_model_preference_set("grunt", ["anthropic"])
                self.assertEqual(set_agents_app.load_model_pin()["architect"],
                                 ("openai-codex", "gpt-5.6-terra"))
                set_agents_app.cmd_model_pin_clear("architect")
                self.assertNotIn("architect", set_agents_app.load_model_pin())
                set_agents_app.cmd_model_pin_clear("architect")  # absent → reported, never an error

    def test_pin_write_path_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "model-preference.toml"
            with mock.patch.object(set_agents_app, "MODEL_PREFERENCE_PATH", path):
                for bad in (("nope-role", "openai-codex/gpt-5.6-sol"),
                            ("architect", "not-a-provider/gpt-5.6-sol"),
                            ("architect", "openai-codex"),
                            ("architect", "openai-codex/bad model!")):
                    with self.assertRaises(set_agents_app.ModelPreferenceError):
                        set_agents_app.cmd_model_pin_set(*bad)
                self.assertFalse(path.exists())
                path.write_text('[model_pin]\narchitect = "bogus/x"\n')
                with self.assertRaises(set_agents_app.ModelPreferenceError):
                    set_agents_app.load_model_pin()


class AllowlistTests(unittest.TestCase):
    def test_safe_argv_admits_exactly_the_three_modes_per_new_cli(self):
        for cli in (coord_policy.OPENCODE_SPAWN_CLI, coord_policy.CODEX_SPAWN_CLI):
            for mode in ("--dispatch-writer", "--dispatch-review", "--dispatch-simulate"):
                argv = ["python3", cli, mode, "--role", "architect", "--provider", "openai-codex",
                        "--model", "gpt-5.6-sol", "--effort", "high", "--task", "-"]
                self.assertTrue(coord_policy._argv_allowed(argv), (cli, mode))
            self.assertFalse(coord_policy._argv_allowed(
                ["python3", cli, "--dispatch-simulate", "--unlisted-flag", "x"]), cli)
            self.assertFalse(coord_policy._argv_allowed(["python3", cli, "--doctor"]), cli)

    def test_opencode_lane_permission_map_carries_the_paired_allow_lines(self):
        text = (ROOT / "Global/opencode/agents/orchestrator.md").read_text()
        for cli in ("opencode_spawn.py", "codex_spawn.py"):
            for mode in ("--dispatch-writer", "--dispatch-review", "--dispatch-simulate"):
                self.assertIn(f"ai/scripts/{cli} {mode}*\": allow", text, (cli, mode))


class WizardPanelTests(unittest.TestCase):
    _CONFIG = {"areas": {}, "roles": {}, "subscriptions": {}, "catalog": {"codex": ["gpt-5.6-sol"]}}

    def test_panel_declares_automatic_policy_and_keeps_the_frozen_markers(self):
        with mock.patch.object(setup_models, "_load_pins", return_value={}):
            text = "\n".join(setup_models._panel_lines(self._CONFIG, [], "go-zen"))
        self.assertIn("Automático (recomendado)", text)
        self.assertIn("DEFAULTS CURADOS", text)
        self.assertIn("ADR-0030", text)

    def test_panel_shows_pinned_roles_with_their_source(self):
        pins = {"architect": ("openai-codex", "gpt-5.6-terra")}
        with mock.patch.object(setup_models, "_load_pins", return_value=pins):
            text = "\n".join(setup_models._panel_lines(self._CONFIG, [], "go-zen"))
        self.assertIn("1 pin(s)", text)
        self.assertIn("architect=openai-codex/gpt-5.6-terra", text)

    def test_wizard_items_keep_the_pinned_prefix_and_gain_the_routing_action(self):
        source = (ROOT / "ai/scripts/setup_models.py").read_text()
        self.assertIn('"Routing: fijar modelo / automático"', source)
        self.assertIn('("Cambiar un área", "Cambiar un rol", "Suscripciones", "Guardar", "Salir sin guardar"',
                      source)


class SelectionPathTests(unittest.TestCase):
    def test_route_decide_envelope_reports_selection_path(self):
        # F-03 (review repair): hermetic — SET_AGENTS_ROUTING_TEST_ROOT keeps the
        # decision log/store out of the developer's real production root, and a
        # non-ok envelope SKIPS explicitly instead of passing vacuously.
        import os as _os
        descriptor = json.dumps({"role": "architect", "task_class": "architecture"})
        with tempfile.TemporaryDirectory() as td:
            env = dict(_os.environ, SET_AGENTS_ROUTING_TEST_ROOT=td)
            result = subprocess.run(
                [sys.executable, "ai/scripts/set_agents_app.py", "--route-decide", "-", "--json"],
                cwd=ROOT, input=descriptor, text=True, capture_output=True, timeout=300, env=env,
            )
            self.assertIn(result.returncode, (0, 1), result.stdout + result.stderr)
            envelope = json.loads(result.stdout.strip().splitlines()[-1])
            if not envelope.get("ok"):
                self.skipTest(f"route-decide not decidable on this machine: {envelope.get('reason_codes')}")
            self.assertIn(envelope["data"].get("selection_path"), ("pin", "dynamic"))
            log = Path(td) / "decisions-v1.jsonl"
            self.assertTrue(log.exists())
            self.assertIn(json.loads(log.read_text().splitlines()[-1])["selection_path"], ("pin", "dynamic"))


class DoctrineTests(unittest.TestCase):
    _FILES = (
        "Global/_canonical/agents/orchestrator.md",
        "Global/claude-code/agents/orchestrator.md",
        "Global/opencode/agents/orchestrator.md",
        "Global/codex/agents/orchestrator.toml",
        "Global/pi/agents/orchestrator.md",
    )

    def test_all_doctrine_copies_name_the_new_spawn_clis_and_residual_fallback(self):
        for path in self._FILES:
            text = (ROOT / path).read_text()
            self.assertIn("opencode_spawn.py", text, path)
            self.assertIn("codex_spawn.py", text, path)
            self.assertIn("--dispatch-simulate", text, path)
            self.assertIn("MODEL_STATIC_FALLBACK", text, path)
            self.assertIn("RESIDUAL", text, path)

    def test_every_spawn_shows_model_and_effort_on_screen(self):
        # ADR-0032 visibility: the narrated-block bracket plus the one-line provenance
        # rule for non-narrated spawns, in every orchestrator doctrine copy...
        for path in self._FILES:
            text = (ROOT / path).read_text()
            self.assertIn("Instancio <role> [<provider>/<model> · effort <effort>]", text, path)
        canonical = (ROOT / self._FILES[0]).read_text()
        self.assertIn("↳ <role>[@tier] · <provider>/<model> ·", canonical)
        # ...and the pi interactive doctrine mandates the per-call model override
        # (pi-subagents' documented `model` param, `:<thinking>` suffix) plus the `↳` line.
        pi_agents = (ROOT / "Global/pi/AGENTS.md").read_text()
        self.assertIn('model: "<provider>/<pi-model-id>[:<effort>]"', pi_agents)
        self.assertIn("↳ <role> · <provider>/<model> · effort <effort>", pi_agents)
        self.assertIn("Instancio <role> [<provider>/<model> · effort <effort>]", pi_agents)
        self.assertEqual(pi_agents, (ROOT / "Global/_shared/AGENTS.pi.md").read_text())

    def test_dispatch_results_echo_the_effort(self):
        # Visibility contract: the printed result JSON of every dispatch mode carries
        # the decision's effort so the spawn is auditable on screen, not only in state.
        for module in (oc, cx):
            with mock.patch.object(module, "spawn", return_value=("success", {})):
                result = module.dispatch_simulate("architect", "t", "openai-codex",
                                                  "gpt-5.6-sol", _ROSTER, effort="high")
                self.assertEqual(result["effort"], "high", module.__name__)
                result = module.dispatch_review("package-reviewer", "t", "openai-codex",
                                                "gpt-5.6-sol", _ROSTER, effort="xhigh")
                self.assertEqual(result["effort"], "xhigh", module.__name__)
            with mock.patch.object(module, "_run_app_cli",
                                   return_value=_Proc(stdout=json.dumps({"ok": True, "data": {}}))), \
                 mock.patch.object(module, "_persist_audit_binding"), \
                 mock.patch.object(module, "spawn", return_value=("success", {})):
                result = module.dispatch_writer("implementer", "t", "run1_" + "a" * 32,
                                                "openai-codex", "gpt-5.6-sol", _ROSTER, effort="low")
                self.assertEqual(result["effort"], "low", module.__name__)


if __name__ == "__main__":
    unittest.main()
