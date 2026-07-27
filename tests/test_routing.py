import os
import dataclasses
import json
import signal
import sqlite3
import subprocess
import sys
import tempfile
import textwrap
import time
import types
import unittest
from pathlib import Path
from unittest import mock

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"ai/scripts"))
import models_config
import routing
import set_agents_app
import set_agents_spawn
from routing_core import catalog as routing_catalog

class RoutingTests(unittest.TestCase):
    def setUp(self):
        self.config=models_config.load_config(ROOT/"models.toml")
        self.roster=models_config.load_roster(ROOT/"roles.tsv")
        self.inventory={("codex","openai-codex"):{"gpt-5.6-sol"},("claude-code","anthropic"):{"opus"},
                        ("opencode","openai-codex"):{"gpt-5.6-sol"},("opencode","anthropic"):{"opus"}}

    def facts(self, role="product-analyst", runtime="claude-code", **changes):
        data=dict(role=role,operation="change",task_class="documentation",read_write="write",write_started=False,
                  risk="low",criticality="",affected_surfaces=(),required_tools=("read",),context_required=True,
                  context_present=True,critical_coverage=True,selected_runtime=runtime)
        data.update(changes); return data

    def service(self, root=None, inventory=None, simulate=False, reprobe=None):
        return routing._compose_for_tests(self.config,self.roster,inventory or self.inventory,root,simulate=simulate,reprobe=reprobe)

    def observed(self, service, role="product-analyst", runtime="claude-code", **changes):
        return service._observe_for_invocation(**self.facts(role, runtime, **changes))

    def authorize(self, svc, role="implementer", runtime="codex"):
        decision=svc.route(routing.TaskRequest(role,"change","documentation",selected_runtime=runtime),
                           self.observed(svc,role,runtime))
        self.assertTrue(decision.execution_enabled, decision.reason_codes)
        return decision

    def test_static_ids_exclude_runtime_and_catalog_is_immutable(self):
        service=self.service(simulate=True); routes=service.snapshot.routes
        self.assertTrue(all(r.route_id.startswith("rt1_") and len(r.route_id)==20 for r in routes))
        openai=next(r for r in routes if r.provider=="openai-codex")
        self.assertIn((openai.route_id,"codex",openai.provider,openai.model,openai.family,openai.effort),service.snapshot.identities)
        self.assertIn((openai.route_id,"opencode",openai.provider,openai.model,openai.family,openai.effort),service.snapshot.identities)

    def test_facts_are_internal_single_use_and_conflicts_disable_execution(self):
        with tempfile.TemporaryDirectory() as td:
            svc=self.service(Path(td)/"state"); request=routing.TaskRequest("implementer","change","documentation",selected_runtime="codex")
            stale=dataclasses.replace(self.observed(svc,role="implementer",runtime="codex"),observed_at=time.time()-301)
            decision=svc.route(request,stale)
            self.assertFalse(decision.execution_enabled); self.assertEqual(decision.reason_codes,("FACTS_INCOMPLETE",))
            facts=self.observed(svc,role="implementer",runtime="codex")
            self.assertFalse(svc.route(request,dataclasses.replace(facts)).execution_enabled)
            self.assertTrue(svc.route(request,facts).execution_enabled)
            self.assertFalse(svc.route(request,facts).execution_enabled)  # exact facts are single-use
            decision=svc.route(routing.TaskRequest("product-analyst","change","documentation",selected_runtime="codex"),self.observed(svc,role="implementer",runtime="codex"))
            self.assertFalse(decision.execution_enabled); self.assertEqual(decision.reason_codes,("FACTS_INCOMPLETE",))

    def test_observed_risk_is_never_downgraded_and_enums_are_closed(self):
        svc=self.service(simulate=True)
        # A low-risk request cannot downgrade an observed high risk: the combined
        # risk stays high, so missing critical coverage excludes every route.
        request=routing.TaskRequest("product-analyst","change","documentation",risk="low",selected_runtime="claude-code")
        facts=self.observed(svc,risk="high",context_required=False,context_present=False,critical_coverage=False)
        decision=svc.route(request,facts)
        self.assertFalse(decision.execution_enabled)
        self.assertIn("NO_ELIGIBLE_ROUTE",decision.reason_codes)
        # v2 catalog: openai rows are runtime-unavailable for claude-code, unauthenticated anthropic tiers
        # fall to auth, and the eligible frontier route is excluded for context — not risk passthrough.
        self.assertEqual({item["reason"] for item in decision.exclusions},
                         {"RUNTIME_UNAVAILABLE","PROVIDER_UNAUTHENTICATED","CONTEXT_MISSING"})
        # The same observation with low risk routes normally.
        ok=svc.route(routing.TaskRequest("product-analyst","change","documentation",risk="low",selected_runtime="claude-code"),
                     self.observed(svc,risk="low",context_required=False,context_present=False,critical_coverage=False))
        self.assertIsNotNone(ok.route_id)
        # Values outside the closed vocabularies are FACTS_INCOMPLETE, request and facts alike.
        bad=svc.route(routing.TaskRequest("product-analyst","change","documentation",risk="extreme",selected_runtime="claude-code"),self.observed(svc))
        self.assertEqual(bad.reason_codes,("FACTS_INCOMPLETE",))
        bad=svc.route(routing.TaskRequest("product-analyst","change","documentation",selected_runtime="claude-code"),self.observed(svc,risk="extreme"))
        self.assertEqual(bad.reason_codes,("FACTS_INCOMPLETE",))

    def test_pi_is_pair_scoped_and_fails_closed_without_a_probed_pair(self):
        # T-305: pi is now in the audited pair table (RUNTIME_UNAVAILABLE no longer fires
        # for it, since no route.v1.toml row narrows `runtimes`), so an unprobed pi pair
        # fails closed via the SAME PROVIDER_UNAUTHENTICATED path every other runtime uses
        # — never RUNTIME_UNAVAILABLE, and never vacuously executable.
        svc=self.service(simulate=True); d=svc.route(routing.TaskRequest("product-analyst","change","documentation",selected_runtime="pi"),self.observed(svc,runtime="pi"))
        self.assertFalse(d.execution_enabled); self.assertIn("NO_ELIGIBLE_ROUTE",d.reason_codes)
        self.assertIsNone(d.route_id)  # N08: not vacuously true under simulate=True — no candidate at all
        self.assertTrue(d.exclusions); self.assertTrue(all(item["reason"]=="PROVIDER_UNAUTHENTICATED" for item in d.exclusions))
        self.assertFalse(any(item["reason"]=="RUNTIME_UNAVAILABLE" for item in d.exclusions))
        unavailable=self.service(simulate=True,inventory={("codex","openai-codex"):{"gpt-5.6-sol"}})
        d=unavailable.route(routing.TaskRequest("product-analyst","change","documentation",selected_runtime="opencode"),self.observed(unavailable,runtime="opencode"))
        self.assertFalse(d.execution_enabled); self.assertIsNone(d.route_id)
        self.assertEqual(d.reason_codes,("NO_ELIGIBLE_ROUTE",))
        # A real (non-simulate, writer-role) authorization attempt over an unprobed pi pair
        # is excluded the same way — no durable authorization without a fresh positive probe.
        with tempfile.TemporaryDirectory() as td:
            real=self.service(Path(td)/"state")
            d=real.route(routing.TaskRequest("implementer","change","documentation",selected_runtime="pi"),
                         self.observed(real,"implementer","pi"))
            self.assertFalse(d.execution_enabled); self.assertIsNone(d.route_id)
            self.assertEqual(d.reason_codes,("NO_ELIGIBLE_ROUTE",))
            self.assertTrue(all(item["reason"]=="PROVIDER_UNAUTHENTICATED" for item in d.exclusions))
            self.assertEqual(real.store.open_runs(),[])  # never durably authorized

    def test_pi_becomes_executable_once_probed_positive_by_the_normal_inventory_check(self):
        # T-305 flip: with PI_SIMULATION_ONLY=False, a pi pair that a probe (real or
        # cached) confirmed positive authorizes exactly like any other runtime — proving
        # the flip only REMOVES a blanket exclusion, it never adds a new authorization path.
        with tempfile.TemporaryDirectory() as td:
            inventory=dict(self.inventory); inventory[("pi","openai-codex")]={"gpt-5.6-sol"}
            svc=self.service(Path(td)/"state",inventory=inventory)
            request=routing.TaskRequest("implementer","change","documentation",selected_runtime="pi")
            d=svc.route(request,self.observed(svc,"implementer","pi"))
            self.assertTrue(d.execution_enabled, d.reason_codes)
            self.assertEqual((d.runtime,d.provider,d.model),("pi","openai-codex","gpt-5.6-sol"))
            self.assertIsNotNone(d.run_id)
            self.assertEqual(svc.store.open_runs()[0]["run_id"],d.run_id)

    def test_probe_parsers_are_pair_specific_and_fail_closed(self):
        # Parsers are validated hermetically against recorded shapes; live CLI
        # output is deliberately not asserted (it changes across versions).
        self.assertTrue(routing_catalog._parse_codex_login("Logged in using ChatGPT\n"))
        self.assertFalse(routing_catalog._parse_codex_login("Not logged in\n"))
        self.assertTrue(routing_catalog._parse_claude_auth('{"loggedIn": true, "authMethod": "claude.ai"}'))
        self.assertFalse(routing_catalog._parse_claude_auth('{"loggedIn": false}'))
        with self.assertRaises(ValueError): routing_catalog._parse_claude_auth("Logged in")
        auth="\x1b[90m│\n●  OpenAI \x1b[90moauth\x1b[0m\n●  OpenCode Zen api\n└  2 credentials\n"
        self.assertEqual(routing_catalog._parse_opencode_auth(auth),{"openai","opencode zen"})
        models="\x1b[0mopenai/gpt-5.6-sol\nopenai/gpt-5.4\n"
        self.assertEqual(routing_catalog._parse_opencode_models(models,"openai"),{"gpt-5.6-sol","gpt-5.4"})
        # opencode exits 0 on unknown providers; the error text must fail the pair.
        with self.assertRaises(routing.RoutingError):
            routing_catalog._parse_opencode_models("Error: Provider not found: anthropic\n","anthropic")
        with self.assertRaises(routing.RoutingError):
            routing_catalog._parse_opencode_models("anthropic/opus\nunexpected junk\n","anthropic")
        # T-305: `pi --list-models` column table — openai-codex ids are catalog-IDENTITY
        # (spike-verified); anthropic raw ids are translated through PI_MODEL_MAP so a
        # short catalog name only survives if ITS curated Pi id is present in the table.
        table=("provider      model                       context  max-out\n"
              "anthropic     claude-opus-4-8             1M       128K\n"
              "anthropic     claude-sonnet-5             1M       128K\n"
              "anthropic     claude-sonnet-4-5           1M       64K\n"  # not in PI_MODEL_MAP -> ignored
              "openai-codex  gpt-5.6-luna                272K     128K\n")
        self.assertEqual(routing_catalog._parse_pi_models(table,"openai-codex"),{"gpt-5.6-luna"})
        self.assertEqual(routing_catalog._parse_pi_models(table,"anthropic"),{"opus","sonnet"})
        self.assertEqual(routing_catalog._parse_pi_models(table,"google"),set())  # audited pair only, but never raises
        with self.assertRaises(routing.RoutingError):
            routing_catalog._parse_pi_models("No models available. Use /login to authenticate.\n","anthropic")
        # No `--` separator (live QA finding): pnpm dlx forwards it VERBATIM into pi's own
        # parser, which chokes on a real multi-flag spawn (only pi's early-exit flags like
        # --version/--list-models tolerate the stray token, masking the bug for probes).
        self.assertEqual(routing_catalog.pi_pinned_argv("--list-models"),
                         ("pnpm","dlx","--package",f"{routing_catalog.PI_PACKAGE}@{routing_catalog.PI_PINNED_VERSION}",
                          "pi","--list-models"))
        self.assertEqual(routing_catalog.PI_MODEL_MAP["anthropic"],
                         {"opus":"claude-opus-4-8","sonnet":"claude-sonnet-5","haiku":"claude-haiku-4-5"})

    def test_pi_auth_provider_keys_reads_names_only_and_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            home=Path(td); agent=home/".pi/agent"; agent.mkdir(parents=True)
            (agent/"auth.json").write_text(json.dumps(
                {"anthropic":{"apiKey":"sk-should-never-be-read"},"openai-codex":{"apiKey":"also-secret"}}))
            with mock.patch.object(routing_catalog.Path,"home",return_value=home):
                self.assertEqual(routing_catalog.pi_auth_provider_keys(),frozenset({"anthropic","openai-codex"}))
            # Missing file, foreign JSON shape, and corrupt JSON all fail closed to empty —
            # never raise, and the function never returns anything but top-level key names.
            with mock.patch.object(routing_catalog.Path,"home",return_value=home/"nope"):
                self.assertEqual(routing_catalog.pi_auth_provider_keys(),frozenset())
            (agent/"auth.json").write_text(json.dumps(["not","a","dict"]))
            with mock.patch.object(routing_catalog.Path,"home",return_value=home):
                self.assertEqual(routing_catalog.pi_auth_provider_keys(),frozenset())
            (agent/"auth.json").write_text("not json at all")
            with mock.patch.object(routing_catalog.Path,"home",return_value=home):
                self.assertEqual(routing_catalog.pi_auth_provider_keys(),frozenset())

    _PI_STUB = textwrap.dedent('''
        import sys, json
        args = sys.argv[1:]
        task = args[-1]
        target = args[args.index("--model") + 1]
        provider, model = target.split("/", 1)
        if task == "SIMULATE:crash-exit":
            sys.exit(1)
        if task == "SIMULATE:crash-no-settle":
            print(json.dumps({"type": "agent_start"}))
            sys.exit(0)
        if task == "SIMULATE:crash-with-secret":
            print("Error: upstream auth failed, Authorization: Bearer sk-ant-totally-secret-value-12345", file=sys.stderr)
            sys.exit(1)
        if task == "SIMULATE:fallback":
            # SEC-A04: the echoed model still matches target_id -- only stderr reveals
            # that pi silently substituted a different real model's config underneath.
            print('Warning: Model "' + model + '" not found for provider "' + provider
                  + '". Using custom model id.', file=sys.stderr)
        if task == "SIMULATE:mismatch":
            model = "unexpected-model"
        stop_reason = "error" if task == "SIMULATE:turn-error" else "stop"
        message = {"role": "assistant", "provider": provider, "model": model, "stopReason": stop_reason,
                  "usage": {"cost": {"total": 0.001}}}
        if stop_reason == "error":
            message["errorMessage"] = "boom"
        print(json.dumps({"type": "agent_start"}))
        print(json.dumps({"type": "message_end", "message": message}))
        print(json.dumps({"type": "agent_settled"}))
    ''')

    def _stub_pi(self, td):
        path = Path(td) / "stub_pi.py"; path.write_text(self._PI_STUB); return path

    def _patched_pi_argv(self, stub):
        return lambda *a: (sys.executable, str(stub), *a)

    def test_spawn_guard_flags_are_unconditional_and_default_tools_are_readonly(self):
        # T-304/AC-11g: --no-session/--no-extensions are on EVERY invocation the spawner
        # builds, and the default tool allowlist has no write/edit/bash tool at all — a
        # protected-path write has no tool to go through, regardless of guard tier.
        self.assertFalse({"write","edit","bash"} & set(set_agents_spawn.GUARD_TOOLS_READONLY))
        with tempfile.TemporaryDirectory() as td:
            stub=self._stub_pi(td); captured={}
            def fake_argv(*a): captured["args"]=a; return (sys.executable,str(stub),*a)
            with mock.patch.object(set_agents_spawn.catalog,"pi_pinned_argv",side_effect=fake_argv):
                prompt=Path(td)/"role.md"; prompt.write_text("You are a test role.")
                outcome,detail=set_agents_spawn.spawn("implementer","SIMULATE:success","openai-codex",
                                                       "gpt-5.6-luna",prompt,cwd=td)
            self.assertEqual(outcome,"success"); self.assertEqual(detail["model"],"openai-codex/gpt-5.6-luna")
            self.assertIn("--no-session",captured["args"]); self.assertIn("--no-extensions",captured["args"])
            self.assertIn("--no-context-files",captured["args"])  # SEC-A02: unconditional too
            idx=captured["args"].index("--tools")
            self.assertEqual(captured["args"][idx+1],",".join(set_agents_spawn.GUARD_TOOLS_READONLY))
            # Guards never relax even when the caller widens the tool tier.
            captured.clear()
            with mock.patch.object(set_agents_spawn.catalog,"pi_pinned_argv",side_effect=fake_argv):
                set_agents_spawn.spawn("implementer","SIMULATE:success","openai-codex","gpt-5.6-luna",prompt,
                                       guard_tools=set_agents_spawn.GUARD_TOOLS_CODE_RW,cwd=td)
            self.assertIn("--no-session",captured["args"]); self.assertIn("--no-extensions",captured["args"])
            self.assertIn("--no-context-files",captured["args"])

    def test_spawn_refuses_a_task_that_lexically_looks_like_a_flag(self):
        # SEC-A01: pinned pi rejects a `--` end-of-options sentinel outright, so a
        # hostile trailing token could otherwise be consumed by pi's OWN parser as an
        # option (live-confirmed: a task of exactly "--offline" is silently swallowed,
        # never reaching pi as message text) -- e.g. "--tools=bash,edit,write" attempting
        # to widen the tool allowlist past the read-only guard. spawn() must refuse
        # BEFORE ever building the argv or starting any subprocess.
        with tempfile.TemporaryDirectory() as td:
            prompt=Path(td)/"role.md"; prompt.write_text("role")
            with mock.patch.object(set_agents_spawn,"subprocess") as subprocess_mock:
                for hostile_task in ("--tools=bash,edit,write", "-x", "--offline"):
                    outcome,detail=set_agents_spawn.spawn("implementer",hostile_task,"openai-codex",
                                                          "gpt-5.6-luna",prompt,cwd=td)
                    self.assertEqual(outcome,"failure")
                    self.assertEqual(detail["reason"],"TASK_LOOKS_LIKE_FLAG")
                subprocess_mock.run.assert_not_called()  # refused before any subprocess ever started
            # A leading space before the dash is still a hostile task once stripped.
            outcome,detail=set_agents_spawn.spawn("implementer","   --tools=bash,edit,write","openai-codex",
                                                  "gpt-5.6-luna",prompt,cwd=td)
            self.assertEqual(outcome,"failure"); self.assertEqual(detail["reason"],"TASK_LOOKS_LIKE_FLAG")
            # An ordinary task (no leading dash) is completely unaffected.
            with tempfile.TemporaryDirectory() as td2:
                stub=self._stub_pi(td2)
                with mock.patch.object(set_agents_spawn.catalog,"pi_pinned_argv",side_effect=self._patched_pi_argv(stub)):
                    outcome,detail=set_agents_spawn.spawn("implementer","SIMULATE:success","openai-codex",
                                                          "gpt-5.6-luna",prompt,cwd=td2)
                self.assertEqual(outcome,"success")

    def test_spawn_detects_stderr_model_fallback_marker_and_never_trusts_the_echoed_model(self):
        # SEC-A04 (DiD): pi's CLI subprocess mode never threads the SDK's
        # `modelFallbackMessage` into the --mode json stdout stream (verified against the
        # pinned 0.81.1 source: it is wired only into InteractiveMode). pi's own CLI
        # model resolver instead prints an equivalent plain-text warning to STDERR when it
        # silently substitutes a different real model's config under the requested id --
        # even though the assistant message still echoes the REQUESTED (mismatched) id,
        # so the plain observed==target_id check alone cannot catch it.
        with tempfile.TemporaryDirectory() as td:
            stub=self._stub_pi(td); prompt=Path(td)/"role.md"; prompt.write_text("role")
            with mock.patch.object(set_agents_spawn.catalog,"pi_pinned_argv",side_effect=self._patched_pi_argv(stub)):
                outcome,detail=set_agents_spawn.spawn("implementer","SIMULATE:fallback","openai-codex","gpt-5.6-luna",prompt,cwd=td)
            self.assertEqual(outcome,"model_mismatch")
            self.assertEqual(detail["reason"],"PI_MODEL_FALLBACK")

    def test_spawn_never_persists_raw_stderr_secrets(self):
        # SEC-A05 (DiD): the child inherits the full os.environ; a crash's stderr is
        # redacted for known secret shapes and kept short, never a raw dump.
        with tempfile.TemporaryDirectory() as td:
            stub=self._stub_pi(td); prompt=Path(td)/"role.md"; prompt.write_text("role")
            with mock.patch.object(set_agents_spawn.catalog,"pi_pinned_argv",side_effect=self._patched_pi_argv(stub)):
                outcome,detail=set_agents_spawn.spawn("implementer","SIMULATE:crash-with-secret","openai-codex","gpt-5.6-luna",prompt,cwd=td)
            self.assertEqual(outcome,"failure"); self.assertEqual(detail["reason"],"PI_CRASH")
            self.assertNotIn("sk-ant-totally-secret-value-12345",detail["stderr"])
            self.assertIn("[REDACTED]",detail["stderr"])

    def test_spawn_crash_paths_close_as_failure_never_success(self):
        # T-303: exit != 0, or a completed process that never reaches `agent_settled`,
        # both close as failure — the two literal crash conditions in the contract.
        with tempfile.TemporaryDirectory() as td:
            stub=self._stub_pi(td); prompt=Path(td)/"role.md"; prompt.write_text("role")
            with mock.patch.object(set_agents_spawn.catalog,"pi_pinned_argv",side_effect=self._patched_pi_argv(stub)):
                outcome,detail=set_agents_spawn.spawn("implementer","SIMULATE:crash-exit","openai-codex","gpt-5.6-luna",prompt,cwd=td)
                self.assertEqual(outcome,"failure"); self.assertEqual(detail["reason"],"PI_CRASH")
                outcome,detail=set_agents_spawn.spawn("implementer","SIMULATE:crash-no-settle","openai-codex","gpt-5.6-luna",prompt,cwd=td)
                self.assertEqual(outcome,"failure"); self.assertEqual(detail["reason"],"PI_CRASH")

    def test_spawn_model_mismatch_and_turn_error_are_never_reported_as_success(self):
        with tempfile.TemporaryDirectory() as td:
            stub=self._stub_pi(td); prompt=Path(td)/"role.md"; prompt.write_text("role")
            with mock.patch.object(set_agents_spawn.catalog,"pi_pinned_argv",side_effect=self._patched_pi_argv(stub)):
                outcome,detail=set_agents_spawn.spawn("implementer","SIMULATE:mismatch","openai-codex","gpt-5.6-luna",prompt,cwd=td)
                self.assertEqual(outcome,"model_mismatch"); self.assertEqual(detail["expected"],"openai-codex/gpt-5.6-luna")
                outcome,detail=set_agents_spawn.spawn("implementer","SIMULATE:turn-error","openai-codex","gpt-5.6-luna",prompt,cwd=td)
                self.assertEqual(outcome,"failure"); self.assertEqual(detail["reason"],"PI_TURN_ERROR")

    def test_spawn_rejects_unmapped_model_and_missing_role_prompt(self):
        outcome,detail=set_agents_spawn.spawn("implementer","x","anthropic","no-such-tier",Path("/nonexistent-role.md"))
        self.assertEqual(outcome,"failure"); self.assertEqual(detail["reason"],"MODEL_ID_UNMAPPED")
        with tempfile.TemporaryDirectory() as td:
            outcome,detail=set_agents_spawn.spawn("implementer","x","openai-codex","gpt-5.6-luna",Path(td)/"missing.md")
            self.assertEqual(outcome,"failure"); self.assertEqual(detail["reason"],"ROLE_PROMPT_MISSING")

    def test_spawn_default_cwd_is_an_isolated_scratch_dir_cleaned_up_after(self):
        # T-304 argv/cwd/env guard: with no explicit cwd, spawn() never runs pi in the
        # caller's own working directory, and never leaves the scratch dir behind.
        with tempfile.TemporaryDirectory() as td:
            stub=self._stub_pi(td); prompt=Path(td)/"role.md"; prompt.write_text("role")
            seen={}
            real_run=set_agents_spawn.subprocess.run
            def spy_run(argv,cwd=None,**kwargs):
                seen["cwd"]=str(cwd); return real_run(argv,cwd=cwd,**kwargs)
            with mock.patch.object(set_agents_spawn.catalog,"pi_pinned_argv",side_effect=self._patched_pi_argv(stub)), \
                 mock.patch.object(set_agents_spawn.subprocess,"run",side_effect=spy_run):
                set_agents_spawn.spawn("implementer","SIMULATE:success","openai-codex","gpt-5.6-luna",prompt)
            self.assertNotEqual(seen["cwd"],os.getcwd())
            self.assertFalse(Path(seen["cwd"]).exists())

    def test_doctor_is_green_only_when_version_auth_and_list_models_all_agree(self):
        def fake_run(argv,**kwargs):
            if argv[-1]=="--version":
                return types.SimpleNamespace(returncode=0,stdout=set_agents_spawn.catalog.PI_PINNED_VERSION+"\n",stderr="")
            return types.SimpleNamespace(returncode=0,stdout="provider model\nanthropic claude-haiku-4-5\n",stderr="")
        with mock.patch.object(set_agents_spawn.subprocess,"run",side_effect=fake_run), \
             mock.patch.object(set_agents_spawn.catalog,"pi_auth_provider_keys",return_value=frozenset({"anthropic","openai-codex"})):
            report=set_agents_spawn.doctor()
        self.assertTrue(report["doctor_green"]); self.assertTrue(report["version_ok"]); self.assertTrue(report["list_models_ok"])
        self.assertEqual(report["auth_providers"],["anthropic","openai-codex"])
        with mock.patch.object(set_agents_spawn.subprocess,"run",side_effect=fake_run), \
             mock.patch.object(set_agents_spawn.catalog,"pi_auth_provider_keys",return_value=frozenset()):
            self.assertFalse(set_agents_spawn.doctor()["doctor_green"])  # auth missing -> never green

    def test_route_and_spawn_sequences_decide_dispatch_spawn_terminal(self):
        calls=[]
        def fake_cli(args,env=None,timeout=60,cwd=None):
            calls.append(args)
            if args[0]=="--route-decide":
                payload={"ok":True,"data":{"execution_enabled":True,"run_id":"run1_"+"0"*32,
                                          "provider":"openai-codex","model":"gpt-5.6-luna"},"reason_codes":[]}
            else:
                payload={"ok":True,"data":{},"reason_codes":[]}
            return types.SimpleNamespace(stdout=json.dumps(payload)+"\n",returncode=0)
        with mock.patch.object(set_agents_spawn,"_run_app_cli",side_effect=fake_cli), \
             mock.patch.object(set_agents_spawn,"spawn",return_value=("success",{"model":"openai-codex/gpt-5.6-luna","usage":{}})):
            result=set_agents_spawn.route_and_spawn("implementer","documentation","do the thing")
        self.assertEqual(result["status"],"success")
        self.assertEqual([c[0] for c in calls],["--route-decide","--route-dispatched","--route-terminal"])
        self.assertEqual(calls[2][1],"run1_"+"0"*32); self.assertEqual(calls[2][2],"success")

    def test_route_and_spawn_keeps_the_full_lifecycle_in_the_user_project(self):
        """P1 delta: every lifecycle mutation discovers the same user PROJECT_ROOT."""
        calls=[]
        def fake_cli(args, env=None, timeout=60, cwd=None):
            calls.append((args, cwd))
            payload={"ok":True,"data":{"execution_enabled":True,"run_id":"run1_"+"9"*32,
                                           "provider":"openai-codex","model":"gpt-5.6-luna"},"reason_codes":[]} \
                if args[0] == "--route-decide" else {"ok":True,"data":{},"reason_codes":[]}
            return types.SimpleNamespace(stdout=json.dumps(payload)+"\n", returncode=0)
        with tempfile.TemporaryDirectory() as td:
            project=Path(td)/"user-project"; nested=project/"src"/"feature"
            nested.mkdir(parents=True)
            with mock.patch.object(set_agents_spawn,"_run_app_cli",side_effect=fake_cli), \
                 mock.patch.object(set_agents_spawn,"spawn",return_value=("success",{})):
                result=set_agents_spawn.route_and_spawn("implementer","documentation","do it", spawn_cwd=nested)
        self.assertEqual(result["status"],"success")
        self.assertEqual([args[0] for args, _ in calls], ["--route-decide","--route-dispatched","--route-terminal"])
        self.assertTrue(all(cwd == nested.resolve() for _, cwd in calls))

    def test_route_and_spawn_persists_the_user_project_key_through_the_real_lifecycle(self):
        """P1 delta: real CLI lifecycle data is scoped to the user's nested project."""
        with tempfile.TemporaryDirectory() as td:
            sandbox=Path(td); project=sandbox/"user-project"; nested=project/"src"/"feature"
            (project/"ai/state/features").mkdir(parents=True); nested.mkdir(parents=True)
            identity="proj1_" + "c" * 32
            (project/"ai/state/project.json").write_text(json.dumps({"schema":1,"project_key":identity,"created_at":"2026-07-27T00:00:00Z"}))
            home=sandbox/"home"; auth=home/".pi/agent"; auth.mkdir(parents=True)
            (auth/"auth.json").write_text(json.dumps({"openai-codex": {}}))
            bins=sandbox/"bin"; bins.mkdir()
            pnpm=bins/"pnpm"
            pnpm.write_text("#!/bin/sh\nprintf 'provider model\\nopenai-codex gpt-5.6-sol\\n'\n")
            pnpm.chmod(0o755)
            env={"HOME":str(home), "PATH":f"{bins}:{os.environ['PATH']}"}
            with mock.patch.dict(os.environ, env, clear=False), \
                 mock.patch.object(set_agents_spawn,"spawn",return_value=("success",{})) as spawn_mock:
                result=set_agents_spawn.route_and_spawn(
                    "implementer", "mechanical", "do it", routing_test_root=str(sandbox/"routing"), spawn_cwd=nested,
                )
            self.assertEqual(result["status"], "success", result)
            self.assertEqual(spawn_mock.call_args.kwargs["cwd"], nested)
            with sqlite3.connect(f"file:{sandbox / 'routing/routing.db'}?mode=ro", uri=True) as connection:
                self.assertEqual(
                    connection.execute("SELECT project_key,state FROM dispatches WHERE run_id=?", (result["run_id"],)).fetchone(),
                    (identity, "terminal_success"),
                )

    def test_route_and_spawn_refuses_non_executable_decision_without_spawning(self):
        def fake_cli(args,env=None,timeout=60,cwd=None):
            self.assertEqual(args[0],"--route-decide")  # never reaches dispatch/spawn
            payload={"ok":True,"data":{"execution_enabled":False},"reason_codes":["REVIEW_IDENTITY_UNVERIFIED"]}
            return types.SimpleNamespace(stdout=json.dumps(payload)+"\n",returncode=0)
        with mock.patch.object(set_agents_spawn,"_run_app_cli",side_effect=fake_cli), \
             mock.patch.object(set_agents_spawn,"spawn") as spawn_mock:
            result=set_agents_spawn.route_and_spawn("package-reviewer","documentation","review it")
        self.assertEqual(result["status"],"refused"); spawn_mock.assert_not_called()

    def test_route_and_spawn_closes_run_as_failure_when_the_child_crashes(self):
        def fake_cli(args,env=None,timeout=60,cwd=None):
            if args[0]=="--route-decide":
                payload={"ok":True,"data":{"execution_enabled":True,"run_id":"run1_"+"1"*32,
                                          "provider":"anthropic","model":"haiku"},"reason_codes":[]}
            else:
                payload={"ok":True,"data":{},"reason_codes":[]}
            return types.SimpleNamespace(stdout=json.dumps(payload)+"\n",returncode=0)
        with mock.patch.object(set_agents_spawn,"_run_app_cli",side_effect=fake_cli) as cli_mock, \
             mock.patch.object(set_agents_spawn,"spawn",return_value=("failure",{"reason":"PI_CRASH"})):
            result=set_agents_spawn.route_and_spawn("implementer","documentation","do it")
        self.assertEqual(result["status"],"failure")
        terminal_call=cli_mock.call_args_list[-1][0][0]
        self.assertEqual(terminal_call[0],"--route-terminal"); self.assertEqual(terminal_call[2],"failure")

    def test_route_and_spawn_never_exposes_a_code_rw_override_and_always_spawns_readonly(self):
        # SEC-A02: route_and_spawn has no `guard_tools` parameter at all -- code-rw is not
        # reachable from this (or main()'s) lifecycle entry point.
        with self.assertRaises(TypeError):
            set_agents_spawn.route_and_spawn("implementer","documentation","do it",
                                             guard_tools=set_agents_spawn.GUARD_TOOLS_CODE_RW)
        def fake_cli(args,env=None,timeout=60,cwd=None):
            if args[0]=="--route-decide":
                payload={"ok":True,"data":{"execution_enabled":True,"run_id":"run1_"+"4"*32,
                                          "provider":"openai-codex","model":"gpt-5.6-luna"},"reason_codes":[]}
            else:
                payload={"ok":True,"data":{},"reason_codes":[]}
            return types.SimpleNamespace(stdout=json.dumps(payload)+"\n",returncode=0)
        with mock.patch.object(set_agents_spawn,"_run_app_cli",side_effect=fake_cli), \
             mock.patch.object(set_agents_spawn,"spawn",return_value=("success",{"model":"openai-codex/gpt-5.6-luna","usage":{}})) as spawn_mock:
            set_agents_spawn.route_and_spawn("implementer","documentation","do the thing")
        self.assertEqual(spawn_mock.call_args.kwargs["guard_tools"],set_agents_spawn.GUARD_TOOLS_READONLY)

    def test_route_and_spawn_closes_run_as_failure_when_a_lifecycle_cli_call_raises(self):
        # SEC-A03/PKG-N01: an exception from `_run_app_cli` (e.g. TimeoutExpired/OSError)
        # AFTER authorization must never leave the run open -- a best-effort
        # --route-terminal failure close is attempted and the child is never spawned.
        terminal_calls=[]
        def fake_cli(args,env=None,timeout=60,cwd=None):
            if args[0]=="--route-decide":
                payload={"ok":True,"data":{"execution_enabled":True,"run_id":"run1_"+"2"*32,
                                          "provider":"openai-codex","model":"gpt-5.6-luna"},"reason_codes":[]}
                return types.SimpleNamespace(stdout=json.dumps(payload)+"\n",returncode=0)
            if args[0]=="--route-dispatched":
                raise subprocess.TimeoutExpired(cmd="route-dispatched",timeout=60)
            terminal_calls.append((args, cwd))
            return types.SimpleNamespace(stdout=json.dumps({"ok":True,"data":{},"reason_codes":[]})+"\n",returncode=0)
        with mock.patch.object(set_agents_spawn,"_run_app_cli",side_effect=fake_cli), \
             mock.patch.object(set_agents_spawn,"spawn") as spawn_mock:
            result=set_agents_spawn.route_and_spawn("implementer","documentation","do it")
        spawn_mock.assert_not_called()  # dispatch itself raised -- the child is never spawned
        self.assertEqual(result["status"],"failure"); self.assertEqual(result["run_id"],"run1_"+"2"*32)
        self.assertEqual(result["reason"],"ORCHESTRATION_EXCEPTION")
        self.assertEqual(len(terminal_calls),1)
        self.assertEqual(terminal_calls[0][0][0],"--route-terminal"); self.assertEqual(terminal_calls[0][0][2],"failure")
        self.assertEqual(terminal_calls[0][1], Path.cwd().resolve())

    def test_route_and_spawn_survives_a_terminal_cli_exception_after_a_successful_spawn(self):
        # SEC-A03/PKG-N01: even once the child spawn genuinely succeeded, an exception
        # raised by the CLOSING --route-terminal call itself must not escape -- the
        # function catches it, best-effort retries the close, and reports failure rather
        # than silently claiming success for a run whose terminal state is now uncertain.
        calls=[]
        def fake_cli(args,env=None,timeout=60,cwd=None):
            calls.append(args[0])
            if args[0]=="--route-decide":
                payload={"ok":True,"data":{"execution_enabled":True,"run_id":"run1_"+"5"*32,
                                          "provider":"openai-codex","model":"gpt-5.6-luna"},"reason_codes":[]}
                return types.SimpleNamespace(stdout=json.dumps(payload)+"\n",returncode=0)
            if args[0]=="--route-dispatched":
                return types.SimpleNamespace(stdout=json.dumps({"ok":True,"data":{},"reason_codes":[]})+"\n",returncode=0)
            raise OSError("boom")  # every --route-terminal attempt raises
        with mock.patch.object(set_agents_spawn,"_run_app_cli",side_effect=fake_cli), \
             mock.patch.object(set_agents_spawn,"spawn",return_value=("success",{"model":"openai-codex/gpt-5.6-luna","usage":{}})):
            result=set_agents_spawn.route_and_spawn("implementer","documentation","do it")
        self.assertEqual(result["status"],"failure")  # never reported success once the close itself failed
        self.assertEqual(result["reason"],"ORCHESTRATION_EXCEPTION")
        self.assertEqual(calls.count("--route-terminal"),2)  # the original attempt + the best-effort close

    def test_cmd_doctor_requires_harness_pi_and_never_leaks_credential_values(self):
        result=subprocess.run([sys.executable,"ai/scripts/set_agents_app.py","--doctor","--json"],cwd=ROOT,text=True,capture_output=True)
        self.assertEqual(result.returncode,2); self.assertEqual(json.loads(result.stdout)["reason_codes"],["DOCTOR_HARNESS_UNSUPPORTED"])
        result=subprocess.run([sys.executable,"ai/scripts/set_agents_app.py","--doctor","--harness","pi","--json"],cwd=ROOT,text=True,capture_output=True)
        self.assertIn(result.returncode,(0,1))
        data=json.loads(result.stdout)
        self.assertEqual(set(data["data"]),{"pinned_version","version_ok","auth_providers","list_models_ok","doctor_green"})
        self.assertNotIn("apiKey",result.stdout); self.assertNotIn("token",result.stdout.lower())
        for provider in data["data"]["auth_providers"]:
            self.assertIn(provider,{"anthropic","openai-codex","openai","google"})

    def test_sqlite_authorization_closes_fallback_before_dispatch(self):
        with tempfile.TemporaryDirectory() as td:
            svc=self.service(Path(td)/"state")
            d=self.authorize(svc)
            svc.store.mark_dispatched(d.run_id)
            with self.assertRaisesRegex(routing.RoutingError,"FALLBACK_DENIED"): svc.store.consume_fallback(d.run_id)
            self.assertEqual(os.stat(Path(td)/"state").st_mode & 0o777,0o700)
            self.assertEqual(os.stat(Path(td)/"state/routing.db").st_mode & 0o777,0o600)

    def test_review_identity_only_comes_from_terminal_writer(self):
        with tempfile.TemporaryDirectory() as td:
            svc=self.service(Path(td)/"state")
            d=self.authorize(svc)
            run=d.run_id; svc.store.mark_dispatched(run); svc.store.terminal(run,"success")
            review=svc.route(routing.TaskRequest("package-reviewer","change","documentation",selected_runtime="claude-code"),self.observed(svc,"package-reviewer","claude-code"),run)
            self.assertFalse(review.execution_enabled); self.assertNotEqual(review.family,"gpt-5.6")
            # SEC-A01: a genuinely independent (different-provider, different-family) verified
            # review decision sets the positive flag.
            self.assertTrue(review.independence_verified)

    def test_review_provider_conflict_excludes_same_provider_siblings(self):
        # F04: with only ONE provider authenticated, a repopulated per-model-family catalog
        # must not let a same-provider sibling model satisfy reviewer independence — 003's
        # fail-closed REVIEWER_INDEPENDENCE_UNAVAILABLE is restored via a hard exclusion.
        with tempfile.TemporaryDirectory() as td:
            single_provider={("claude-code","anthropic"):{"haiku","sonnet","opus"}}
            svc=self.service(Path(td)/"state",inventory=single_provider)
            request=routing.TaskRequest("implementer","change","documentation",selected_runtime="claude-code")
            d=svc.route(request,self.observed(svc,"implementer","claude-code"))
            self.assertTrue(d.execution_enabled, d.reason_codes); self.assertEqual(d.provider,"anthropic")
            svc.store.mark_dispatched(d.run_id); svc.store.terminal(d.run_id,"success")
            review=svc.route(routing.TaskRequest("package-reviewer","change","documentation",selected_runtime="claude-code"),
                             self.observed(svc,"package-reviewer","claude-code"),d.run_id)
            self.assertFalse(review.execution_enabled)
            self.assertEqual(review.reason_codes,("REVIEWER_INDEPENDENCE_UNAVAILABLE",))
            self.assertFalse(review.independence_verified)
            conflicts={item["reason"] for item in review.exclusions}
            self.assertIn("REVIEW_PROVIDER_CONFLICT",conflicts)

    def test_rejected_lifecycle_operations_are_audited(self):
        with tempfile.TemporaryDirectory() as td:
            svc=self.service(Path(td)/"state"); store=svc.store
            d=self.authorize(svc); store.mark_dispatched(d.run_id)
            with self.assertRaisesRegex(routing.RoutingError,"FALLBACK_DENIED"): store.consume_fallback(d.run_id)
            with self.assertRaisesRegex(routing.RoutingError,"STATE_CONFLICT"): store.mark_dispatched(d.run_id)
            c=store._connect()
            try:
                reasons={row[0] for row in c.execute("SELECT reason_family FROM events WHERE event_type='rejected'")}
                self.assertEqual(reasons,{"FALLBACK_DENIED","STATE_CONFLICT"})
                exclusions=c.execute("SELECT COALESCE(SUM(exclusion_count),0) FROM metric_rollups").fetchone()[0]
                self.assertEqual(exclusions,2)
            finally: c.close()

    def test_fallback_counters_record_actual_identity_outcomes(self):
        with tempfile.TemporaryDirectory() as td:
            inventory=dict(self.inventory)
            svc=self.service(Path(td)/"state",inventory=inventory)
            d=self.authorize(svc,role="implementer",runtime="opencode")
            self.assertIsNotNone(d.fallback_identity)
            consumed=svc.store.consume_fallback(d.run_id)
            self.assertEqual(consumed,d.fallback_identity)
            svc.store.terminal(d.run_id,"success",latency_ms=42)
            c=svc.store._connect()
            try:
                consumed_count,success_count=c.execute("SELECT COALESCE(SUM(fallback_consumed_count),0),COALESCE(SUM(fallback_success_count),0) FROM metric_rollups").fetchone()
                self.assertEqual((consumed_count,success_count),(1,1))
                # The terminal event audits the actually dispatched (fallback) identity, not the selected one.
                terminal_route=c.execute("SELECT route_id FROM events WHERE event_type='terminal'").fetchone()[0]
                self.assertEqual(terminal_route,d.fallback_identity[0])
            finally: c.close()

    def test_explain_cli_is_schema_two_and_creates_no_decision_state(self):
        state=Path.home()/".local/state/set-agentes/routing-v2"
        # AM-2 amendment: the regenerable probe cache is the ONE file explain may write;
        # decision/lifecycle state (the SQLite DB and sidecars) must stay untouched.
        snapshot=lambda: sorted(p for p in state.glob("*") if p.name != "probe-cache.json") if state.exists() else []
        db=state/"routing.db"; db_before=db.read_bytes() if db.is_file() else None
        before=snapshot()
        result=subprocess.run([sys.executable,"ai/scripts/set_agents_app.py","--route-explain","documentation","--json"],cwd=ROOT,text=True,capture_output=True)
        self.assertIn(result.returncode,(0,1),result.stderr); self.assertEqual(result.stdout.count("\n"),1)
        data=json.loads(result.stdout); self.assertEqual(set(data),{"schema_version","ok","command","data","warnings","reason_codes"}); self.assertEqual(data["schema_version"],2)
        self.assertEqual(before,snapshot())
        self.assertEqual(db_before,db.read_bytes() if db.is_file() else None)

    def test_cli_mode_exclusion_covers_every_non_routing_argument(self):
        # Any argument other than --json combined with an observability mode is a
        # total conflict (exit 2), including plain modifiers such as --yes.
        for extra in (["--yes"],["--no-install"],["--harness","claude"]):
            result=subprocess.run([sys.executable,"ai/scripts/set_agents_app.py","--route-explain","documentation","--json",*extra],
                                  cwd=ROOT,text=True,capture_output=True)
            self.assertEqual(result.returncode,2,(extra,result.stdout,result.stderr))
            self.assertIn("ROUTING_INPUT_INVALID",result.stdout)

    def test_gate_and_telemetry_negative_cases(self):
        gates=routing.gate_specs(ROOT); gate=gates["v2:python-compile"]
        self.assertIn("v2:routing-unit",gates)
        self.assertEqual(routing.run_gate(gate,ROOT,{"PYTHONUTF8":"1"}),0)
        self.assertTrue(Path(gate.argv[0]).is_absolute())
        with self.assertRaises(ValueError): routing.run_gate(dataclasses.replace(gate,argv=("python3","-c","pass")),ROOT)
        with self.assertRaises(ValueError): routing.run_gate(gate,ROOT,{"PATH":"/tmp"})

    def test_existing_invalid_sqlite_is_byte_preserving_and_legacy_is_nofollow(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)/"state"; root.mkdir(mode=0o700)
            db=root/"routing.db"; db.write_bytes(b"not sqlite"); db.chmod(0o600)
            before=db.read_bytes()
            with self.assertRaisesRegex(routing.RoutingError,"ROUTING_UNAVAILABLE"):
                routing.RoutingStore._for_tests(root).report()
            self.assertEqual(before,db.read_bytes())
            legacy=Path(td)/"legacy/routing"; legacy.mkdir(parents=True)
            candidate=legacy/"routing-events-2026-7.jsonl"; candidate.write_text("keep")
            self.assertEqual(routing.legacy_warnings(legacy.parent),("LEGACY_ROUTING_STATE_PRESENT",))
            link=legacy/"routing.lock"; link.symlink_to(candidate)
            self.assertEqual(routing.legacy_warnings(legacy.parent),("LEGACY_ROUTING_STATE_PRESENT","LEGACY_ROUTING_STATE_UNSAFE"))

    def test_schema_drift_fails_closed_byte_identically(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)/"state"
            store=routing.RoutingStore._for_tests(root); store.report()  # creates a pristine database
            c=sqlite3.connect(root/"routing.db"); c.execute("DROP INDEX dispatches_review"); c.execute("VACUUM"); c.close()
            before=(root/"routing.db").read_bytes()
            with self.assertRaisesRegex(routing.RoutingError,"ROUTING_UNAVAILABLE"):
                routing.RoutingStore._for_tests(root).report()
            self.assertEqual(before,(root/"routing.db").read_bytes())
            # A downlevel schema version is rejected the same way.
            c=sqlite3.connect(root/"routing.db"); c.execute("UPDATE meta SET value='2' WHERE key='schema_version'"); c.commit(); c.close()
            with self.assertRaisesRegex(routing.RoutingError,"ROUTING_UNAVAILABLE"):
                routing.RoutingStore._for_tests(root).report()

    def test_concurrent_writer_lock_fails_closed_without_corruption(self):
        with tempfile.TemporaryDirectory() as td:
            svc=self.service(Path(td)/"state"); store=svc.store
            first=self.authorize(svc)
            holder=store._connect()
            try:
                holder.execute("BEGIN IMMEDIATE")
                # busy_timeout=0: a concurrent writer loses immediately and fail-closed.
                request=routing.TaskRequest("implementer","change","documentation",selected_runtime="codex")
                decision=svc.route(request,self.observed(svc,"implementer","codex"))
                self.assertFalse(decision.execution_enabled)
                self.assertEqual(decision.reason_codes,("ROUTING_UNAVAILABLE",))
                holder.execute("ROLLBACK")
            finally: holder.close()
            second=self.authorize(svc)  # the lock loser left a consistent database behind
            c=store._connect()
            try:
                runs={row[0] for row in c.execute("SELECT run_id FROM dispatches")}
                self.assertEqual(runs,{first.run_id,second.run_id})
            finally: c.close()

    def test_crash_between_begin_and_commit_preserves_consistency(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)/"state"
            svc=self.service(root); d=self.authorize(svc)
            script=textwrap.dedent(f"""
                import os, signal, sys
                from pathlib import Path
                sys.path.insert(0, {str(ROOT/'ai/scripts')!r})
                from routing_core.store import RoutingStore
                store=RoutingStore._for_tests(Path({str(root)!r}))
                c=store._connect(); c.execute("BEGIN IMMEDIATE")
                store._event(c,"terminal",("rt","codex","openai-codex","gpt-5.6-sol","gpt-5.6","medium"),"success","none",10)
                os.kill(os.getpid(), signal.SIGKILL)
            """)
            result=subprocess.run([sys.executable,"-c",script],cwd=ROOT,capture_output=True,text=True)
            self.assertEqual(result.returncode,-signal.SIGKILL,result.stderr)
            report=routing.RoutingStore._for_tests(root).report()
            # The killed transaction never becomes visible and the database stays fully usable.
            self.assertEqual(report["retained_events"],1)  # only the original authorization event
            svc2=self.service(root); self.authorize(svc2)

    def test_retention_bound_holds_within_the_writing_transaction(self):
        with tempfile.TemporaryDirectory() as td:
            svc=self.service(Path(td)/"state"); store=svc.store
            conn=store._connect()
            try:
                now=store._now(); conn.execute("BEGIN IMMEDIATE")
                rows=[(now-120*86400*1000 if n==0 else now,"terminal","rt","codex","openai-codex","gpt-5.6-sol","gpt-5.6","success","none",n,"100+") for n in range(10005)]
                conn.executemany("INSERT INTO events(occurred_at,event_type,route_id,runtime,provider,model,family,outcome,reason_family,latency_ms,latency_bucket) VALUES(?,?,?,?,?,?,?,?,?,?,?)",rows)
                conn.execute("COMMIT")
            finally: conn.close()
            # The next write path compacts in its own transaction: bound holds at COMMIT.
            self.authorize(svc)
            c=store._connect()
            try:
                self.assertLessEqual(c.execute("SELECT COUNT(*) FROM events").fetchone()[0],10000)
                compacted=c.execute("SELECT COALESCE(SUM(compacted_count),0) FROM metric_rollups").fetchone()[0]
                self.assertGreater(compacted,0)
            finally: c.close()

    def test_database_bytes_never_contain_private_task_or_account_data(self):
        with tempfile.TemporaryDirectory() as td:
            svc=self.service(Path(td)/"state")
            d=self.authorize(svc); svc.store.mark_dispatched(d.run_id); svc.store.terminal(d.run_id,"success",latency_ms=10)
            blob=b"".join((Path(td)/"state"/name).read_bytes() for name in os.listdir(Path(td)/"state"))
            for secret in (b"documentation",b"change",os.environ.get("USER","@@none@@").encode(),str(Path.home()).encode(),b"@gmail",b"password",b"token"):
                self.assertNotIn(secret,blob)

    def test_required_tier_matrix_is_total(self):
        from routing_core import domain
        for task_class in sorted(domain.TASK_CLASSES):
            for risk in sorted(domain.RISK_ORDER):
                tier = domain.required_tier(task_class, risk)
                if task_class in domain.CRITICAL or risk == "high":
                    self.assertEqual(tier, "frontier", (task_class, risk))
                elif task_class in {"mechanical","documentation","inspection"} and risk == "low":
                    self.assertEqual(tier, "fast", (task_class, risk))
                else:
                    self.assertEqual(tier, "balanced", (task_class, risk))
        with self.assertRaises(routing.RoutingError): domain.required_tier("nope", "low")
        with self.assertRaises(routing.RoutingError): domain.required_tier("security", "nope")

    def test_tier_selection_fast_wins_and_insufficient_excludes(self):
        inv = {("codex","openai-codex"):{"gpt-5.6-luna","gpt-5.6-sol","gpt-5.6-terra"}}
        with tempfile.TemporaryDirectory() as td:
            svc=self.service(Path(td)/"s", inventory=inv)
            d=svc.route(routing.TaskRequest("implementer","change","mechanical",selected_runtime="codex"),
                        self.observed(svc,"implementer","codex",task_class="mechanical",context_required=False))
            self.assertTrue(d.execution_enabled); self.assertEqual(d.model,"gpt-5.6-luna")  # fast WINS
            d2=svc.route(routing.TaskRequest("implementer","change","security",risk="high",selected_runtime="codex"),
                         self.observed(svc,"implementer","codex",task_class="security",risk="high",criticality="security"))
            self.assertEqual(d2.model,"gpt-5.6-terra")
            insufficient={item["route_id"] for item in d2.exclusions if item["reason"]=="TIER_INSUFFICIENT"}
            self.assertEqual(len(insufficient),2)  # luna and sol tiers are below frontier
            svc.store.abandon(d.run_id); svc.store.abandon(d2.run_id)

    def test_tier_insufficient_never_masks_a_more_fundamental_exclusion(self):
        # F10: hard exclusions (role/tools/context/independence) are evaluated BEFORE
        # TIER_INSUFFICIENT, so a route that is ALSO missing context reports CONTEXT_MISSING
        # on every candidate route — never a masking TIER_INSUFFICIENT for the lower tiers.
        inv={("codex","openai-codex"):{"gpt-5.6-luna","gpt-5.6-sol","gpt-5.6-terra"}}
        with tempfile.TemporaryDirectory() as td:
            svc=self.service(Path(td)/"s", inventory=inv)
            d=svc.route(routing.TaskRequest("implementer","change","security",risk="high",selected_runtime="codex"),
                        self.observed(svc,"implementer","codex",task_class="security",risk="high",
                                     criticality="security",context_present=False,critical_coverage=False))
            self.assertFalse(d.execution_enabled)
            reason_set={item["reason"] for item in d.exclusions}
            # Anthropic rows are RUNTIME_UNAVAILABLE (codex never pairs with anthropic — a
            # harder, earlier exclusion); every codex row (fast/balanced/frontier alike) is
            # CONTEXT_MISSING, never TIER_INSUFFICIENT.
            self.assertEqual(reason_set,{"CONTEXT_MISSING","RUNTIME_UNAVAILABLE"})
            codex_reasons={item["reason"] for item in d.exclusions if item["route_id"] in
                          {r.route_id for r in svc.snapshot.routes if r.provider=="openai-codex"}}
            self.assertEqual(codex_reasons,{"CONTEXT_MISSING"})

    def test_descriptor_risk_only_raises_the_derived_base(self):
        svc=self.service(simulate=True)
        # Observed high risk + requested low: frontier still required (raise-only, AM-1).
        tier_of=lambda d: next(r.tier for r in svc.snapshot.routes if r.route_id==d.route_id)
        d=svc.route(routing.TaskRequest("product-analyst","change","documentation",risk="low",selected_runtime="claude-code"),
                    self.observed(svc,risk="high"))
        self.assertIsNotNone(d.route_id); self.assertEqual(tier_of(d),"frontier")
        # Observed low + requested high: the request raises to frontier symmetrically.
        d2=svc.route(routing.TaskRequest("product-analyst","change","documentation",risk="high",selected_runtime="claude-code"),
                     self.observed(svc,risk="low"))
        self.assertIsNotNone(d2.route_id); self.assertEqual(tier_of(d2),"frontier")

    def test_unhashable_required_tools_degrades_not_raises(self):
        svc=self.service(simulate=True)
        request=routing.TaskRequest("product-analyst","change","documentation",required_tools=(["read"],),selected_runtime="claude-code")
        d=svc.route(request,self.observed(svc))
        self.assertEqual(d.reason_codes,("FACTS_INCOMPLETE",))

    def test_facts_unhashable_required_tools_degrades_not_raises(self):
        # F05: the N-1 guard covers facts.required_tools too — not just the request side —
        # so a non-str member never reaches the `set(facts.required_tools)` call downstream.
        svc=self.service(simulate=True)
        request=routing.TaskRequest("product-analyst","change","documentation",selected_runtime="claude-code")
        facts=self.observed(svc,required_tools=(["read"],))
        d=svc.route(request,facts)
        self.assertEqual(d.reason_codes,("FACTS_INCOMPLETE",))

    def test_compose_for_tests_requires_explicit_root(self):
        with self.assertRaises(ValueError):
            routing._compose_for_tests(self.config,self.roster,self.inventory)

    def _probe_stubs(self, td):
        bins=Path(td)/"bin"; bins.mkdir(); log=Path(td)/"probes.log"
        scripts={
            "codex": '#!/bin/sh\necho "$0 $@" >> %s\necho "Logged in using ChatGPT" 1>&2\n' % log,
            "claude": '#!/bin/sh\necho "$0 $@" >> %s\necho \'{"loggedIn": true}\'\n' % log,
            "opencode": ('#!/bin/sh\necho "$0 $@" >> %s\n'
                         'if [ "$1" = "auth" ]; then printf "\\342\\227\\217  OpenAI oauth\\n"; exit 0; fi\n'
                         'if [ "$2" = "openai" ]; then echo "openai/gpt-5.6-sol"; exit 0; fi\n'
                         'echo "Error: Provider not found: $2"; exit 0\n') % log,
        }
        for name, body in scripts.items():
            path=bins/name; path.write_text(body); path.chmod(0o755)
        return bins, log

    def test_probe_cache_is_filtering_only_redacted_and_invalidated(self):
        from routing_core import catalog as cat
        with tempfile.TemporaryDirectory() as td:
            bins, log = self._probe_stubs(td)
            cache_root=Path(td)/"root"; cache_root.mkdir(mode=0o700)
            env_patch={"PATH": f"{bins}:{os.environ['PATH']}"}
            old=os.environ["PATH"]; os.environ["PATH"]=env_patch["PATH"]
            try:
                cold=cat.probe_inventory(self.config, cache_root=cache_root, now=1000.0)
                self.assertEqual(cold[("codex","openai-codex")], set(self.config["catalog"]["codex"]))
                self.assertEqual(cold[("opencode","openai-codex")],{"gpt-5.6-sol"})
                self.assertNotIn(("opencode","anthropic"),cold)  # Error: with exit 0 fails the pair
                self.assertTrue(log.read_text())
                cache=cache_root/"probe-cache.json"
                self.assertEqual(cache.stat().st_mode & 0o777, 0o600)
                doc=json.loads(cache.read_text())
                self.assertEqual(set(doc),{"key","at","pairs"})  # redacted pair->models only
                # Warm within TTL: the two POSITIVE pairs are never re-probed, but the one
                # NEGATIVE pair (F06b: never cached, so it costs a retry every call, not the
                # whole TTL) is retried — its stub is deterministic, so the result is unchanged.
                log.write_text("")
                warm=cat.probe_inventory(self.config, cache_root=cache_root, now=1100.0)
                self.assertEqual(warm,cold)
                retried=log.read_text()
                self.assertIn("bin/opencode",retried)
                self.assertNotIn("bin/codex",retried); self.assertNotIn("bin/claude",retried)
                # Expired TTL reprobes; corrupt cache is ignored fail-closed; digest change invalidates.
                for breaker in (lambda: cat.probe_inventory(self.config, cache_root=cache_root, now=1000.0+9999),
                                lambda: (cache.write_text("{corrupt"), cat.probe_inventory(self.config, cache_root=cache_root, now=1100.0))[-1]):
                    log.write_text(""); result=breaker()
                    self.assertEqual(result,cold); self.assertNotEqual(log.read_text(),"")
                changed=json.loads(json.dumps(self.config)); changed["routing"]=dict(changed["routing"], fallback_limit=9)
                log.write_text(""); cat.probe_inventory(changed, cache_root=cache_root, now=1100.0)
                self.assertNotEqual(log.read_text(),"")
                # pairs= path is always fresh and never cached.
                log.write_text(""); pairwise=cat.probe_inventory(self.config, cache_root=None, pairs=[("codex","openai-codex")])
                self.assertEqual(set(pairwise),{("codex","openai-codex")}); self.assertNotEqual(log.read_text(),"")
            finally:
                os.environ["PATH"]=old

    def test_probe_cache_recovers_a_negative_pair_within_ttl(self):
        # F06(b): a transient failure is never remembered for the whole TTL — the very
        # next call, still well inside the 300s window, sees the recovery immediately.
        from routing_core import catalog as cat
        with tempfile.TemporaryDirectory() as td:
            bins, log = self._probe_stubs(td)
            cache_root=Path(td)/"root"; cache_root.mkdir(mode=0o700)
            old=os.environ["PATH"]; os.environ["PATH"]=f"{bins}:{old}"
            try:
                cold=cat.probe_inventory(self.config, cache_root=cache_root, now=1000.0)
                self.assertNotIn(("opencode","anthropic"),cold)  # negative: never persisted
                # Flip the stub so opencode now authenticates anthropic too, then probe again
                # a second later (well inside TTL): the recovered pair must show up immediately.
                (bins/"opencode").write_text('#!/bin/sh\necho "$0 $@" >> %s\n'
                    'if [ "$1" = "auth" ]; then printf "\\342\\227\\217  OpenAI oauth\\n\\342\\227\\217  Anthropic oauth\\n"; exit 0; fi\n'
                    'if [ "$2" = "openai" ]; then echo "openai/gpt-5.6-sol"; exit 0; fi\n'
                    'echo "anthropic/opus"\n' % log)
                (bins/"opencode").chmod(0o755)
                recovered=cat.probe_inventory(self.config, cache_root=cache_root, now=1001.0)
                self.assertIn(("opencode","anthropic"),recovered)
                self.assertEqual(recovered[("opencode","anthropic")],{"opus"})
                # The still-cached positives are untouched by the recovery.
                self.assertEqual(recovered[("codex","openai-codex")],cold[("codex","openai-codex")])
            finally:
                os.environ["PATH"]=old

    def test_probe_cache_read_reintersects_with_configured_models(self):
        # F09: even a key-matching, byte-valid cache document can never widen the audited
        # set beyond the live models.toml catalog — a foreign/stale model name is dropped.
        from routing_core import catalog as cat
        with tempfile.TemporaryDirectory() as td:
            cache_root=Path(td)/"root"; cache_root.mkdir(mode=0o700)
            key=cat._cache_key(self.config)
            doc={"key":key,"at":1000.0,"pairs":{"codex|openai-codex":["gpt-5.6-luna","totally-bogus-model"]}}
            path=cache_root/"probe-cache.json"; path.write_text(json.dumps(doc)); path.chmod(0o600)
            out=cat._read_probe_cache(cache_root,key,1000.5,self.config)
            self.assertEqual(out,{("codex","openai-codex"):{"gpt-5.6-luna"}})

    def test_probe_cache_ignores_unvalidated_directory(self):
        # SEC-A03: the cache root must pass the same private-dir discipline as the store
        # (no symlink, this uid's 0700 dir) — `Path.is_dir()` alone follows symlinks.
        from routing_core import catalog as cat
        with tempfile.TemporaryDirectory() as td:
            real=Path(td)/"real"; real.mkdir(mode=0o700)
            link=Path(td)/"link"; link.symlink_to(real)
            self.assertFalse(cat._validate_cache_dir(link))
            wrong_mode=Path(td)/"wrong"; wrong_mode.mkdir(mode=0o755)
            self.assertFalse(cat._validate_cache_dir(wrong_mode))
            self.assertTrue(cat._validate_cache_dir(real))
            # A write attempt against an unvalidated root never creates anything.
            cat._write_probe_cache(link,"key",{("codex","openai-codex"):{"gpt-5.6-luna"}},1000.0)
            self.assertEqual(list(real.iterdir()),[])

    def test_probe_cache_write_false_is_read_only(self):
        # SEC-A03: the simulate/explain lane may READ a warm cache but must never WRITE one
        # (preserves the "no mutation" contract even though live probes still run to fill it).
        from routing_core import catalog as cat
        with tempfile.TemporaryDirectory() as td:
            bins, log = self._probe_stubs(td)
            cache_root=Path(td)/"root"; cache_root.mkdir(mode=0o700)
            old=os.environ["PATH"]; os.environ["PATH"]=f"{bins}:{old}"
            try:
                result=cat.probe_inventory(self.config, cache_root=cache_root, now=1000.0, cache_write=False)
                self.assertTrue(result)
                self.assertFalse((cache_root/"probe-cache.json").exists())
                # A subsequent normal (writable) call still persists it.
                cat.probe_inventory(self.config, cache_root=cache_root, now=1001.0)
                self.assertTrue((cache_root/"probe-cache.json").exists())
            finally:
                os.environ["PATH"]=old

    def test_probe_pi_pair_timeout_is_raised_to_the_cold_pnpm_allowance(self):
        # PKG-N02: the doctor already allows 60s (set_agents_spawn.DOCTOR_TIMEOUT_SECONDS)
        # for a cold `pnpm dlx` resolution; probe_inventory's own default (20s, sized for
        # the other three runtimes' fast local CLI probes) must not silently time out a
        # cold pi store -- only the pi pairs get the floor, every other pair keeps the
        # caller's own timeout.
        from routing_core import catalog as cat
        captured=[]
        def fake_run(argv,**kwargs):
            captured.append((argv,kwargs.get("timeout")))
            if argv[:2]==("pnpm","dlx"):
                return types.SimpleNamespace(returncode=0,stdout="provider model\nopenai-codex gpt-5.6-luna\n",stderr="")
            return types.SimpleNamespace(returncode=0,stdout="Logged in using ChatGPT\n",stderr="")
        with mock.patch.object(cat.subprocess,"run",side_effect=fake_run), \
             mock.patch.object(cat,"pi_auth_provider_keys",return_value=frozenset({"openai-codex"})):
            result=cat.probe_inventory(self.config, cache_root=None,
                                       pairs=[("pi","openai-codex"),("codex","openai-codex")], timeout=5.0)
        self.assertEqual(result[("pi","openai-codex")],{"gpt-5.6-luna"})
        pi_timeout=next(t for a,t in captured if a[:2]==("pnpm","dlx"))
        codex_timeout=next(t for a,t in captured if a[0]=="codex")
        self.assertGreaterEqual(pi_timeout,cat.PI_PROBE_MIN_TIMEOUT_SECONDS)
        self.assertEqual(codex_timeout,5.0)  # non-pi pairs are never slowed by the pi floor

    def test_fresh_selected_reprobe_gates_writer_authorization(self):
        calls=[]
        def verifying(pairs): calls.append(tuple(pairs)); return {p:{"gpt-5.6-luna"} for p in pairs}
        inv={("codex","openai-codex"):{"gpt-5.6-luna"}}
        with tempfile.TemporaryDirectory() as td:
            svc=self.service(Path(td)/"s",inventory=inv,reprobe=verifying)
            d=svc.route(routing.TaskRequest("implementer","change","mechanical",selected_runtime="codex"),
                        self.observed(svc,"implementer","codex",task_class="mechanical",context_required=False))
            self.assertTrue(d.execution_enabled)
            self.assertEqual(calls,[(("codex","openai-codex"),)])  # exactly the selected pair, once
            svc.store.abandon(d.run_id)
        def refusing(pairs): return {p:set() for p in pairs}
        with tempfile.TemporaryDirectory() as td:
            svc=self.service(Path(td)/"s",inventory=inv,reprobe=refusing)
            d=svc.route(routing.TaskRequest("implementer","change","mechanical",selected_runtime="codex"),
                        self.observed(svc,"implementer","codex",task_class="mechanical",context_required=False))
            self.assertFalse(d.execution_enabled); self.assertEqual(d.reason_codes,("PROVIDER_UNAUTHENTICATED",))
            self.assertEqual(svc.store.open_runs(),[])  # nothing was durably authorized

    def test_abandoned_closes_authorized_and_is_never_review_identity(self):
        inv={("codex","openai-codex"):{"gpt-5.6-luna"}}
        with tempfile.TemporaryDirectory() as td:
            svc=self.service(Path(td)/"s",inventory=inv)
            d=svc.route(routing.TaskRequest("implementer","change","mechanical",selected_runtime="codex"),
                        self.observed(svc,"implementer","codex",task_class="mechanical",context_required=False))
            self.assertEqual([r["run_id"] for r in svc.store.open_runs()],[d.run_id])
            with self.assertRaisesRegex(routing.RoutingError,"STATE_CONFLICT"):
                svc.store.terminal(d.run_id,"success")  # never terminal_success without dispatch
            svc.store.abandon(d.run_id)
            self.assertEqual(svc.store.open_runs(),[])
            self.assertEqual(svc.store.recent_writers(),[])
            with self.assertRaisesRegex(routing.RoutingError,"REVIEW_IDENTITY_INVALID"):
                svc.store.implementation_identity(d.run_id)
            with self.assertRaisesRegex(routing.RoutingError,"STATE_CONFLICT"):
                svc.store.abandon(d.run_id)  # abandoned is terminal

    def test_abandoned_check_forbids_actual_identity(self):
        # N03: the DDL itself, not just application code, refuses an abandoned row that
        # somehow carries a dispatched (actual) identity.
        with tempfile.TemporaryDirectory() as td:
            store=routing.RoutingStore._for_tests(Path(td)/"s"); store.report()  # creates a pristine database
            c=sqlite3.connect(store.db_path)
            try:
                with self.assertRaises(sqlite3.IntegrityError):
                    c.execute(
                        "INSERT INTO dispatches (run_id,role,role_class,selected_route_id,selected_runtime,"
                        "selected_provider,selected_model,selected_family,selected_effort,actual_route_id,"
                        "actual_runtime,actual_provider,actual_model,actual_family,actual_effort,state,"
                        "fallback_window_open,authorized_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                        ("run1_"+"a"*32,"implementer","writer","rt","codex","openai-codex","gpt-5.6-sol","gpt-5.6","medium",
                         "rt","codex","openai-codex","gpt-5.6-sol","gpt-5.6","medium",  # actual_* set: forbidden on abandoned
                         "abandoned",0,0,0))
            finally:
                c.close()

    def test_close_run_never_writes_a_spurious_rejected_event(self):
        # F02: a successful close (either lane) writes ZERO rejected events, and a close
        # attempt against a run that cannot be closed writes exactly ONE — never the
        # try-terminal-then-except-abandon double-transaction pattern this replaces.
        inv={("codex","openai-codex"):{"gpt-5.6-luna"}}

        def rejected_count(store):
            c=store._connect()
            try: return c.execute("SELECT COUNT(*) FROM events WHERE event_type='rejected'").fetchone()[0]
            finally: c.close()

        with tempfile.TemporaryDirectory() as td:
            svc=self.service(Path(td)/"s",inventory=inv)
            d=svc.route(routing.TaskRequest("implementer","change","mechanical",selected_runtime="codex"),
                        self.observed(svc,"implementer","codex",task_class="mechanical",context_required=False))
            state=svc.store.close_run(d.run_id,"failure")  # authorized, never dispatched -> abandoned
            self.assertEqual(state,"abandoned")
            self.assertEqual(rejected_count(svc.store),0)
            self.assertEqual([r["state"] for r in svc.store.recent_writers()],[])

        with tempfile.TemporaryDirectory() as td:
            svc=self.service(Path(td)/"s",inventory=inv)
            d=svc.route(routing.TaskRequest("implementer","change","mechanical",selected_runtime="codex"),
                        self.observed(svc,"implementer","codex",task_class="mechanical",context_required=False))
            svc.store.mark_dispatched(d.run_id)
            state=svc.store.close_run(d.run_id,"success")
            self.assertEqual(state,"terminal_success")
            self.assertEqual(rejected_count(svc.store),0)

        with tempfile.TemporaryDirectory() as td:
            svc=self.service(Path(td)/"s",inventory=inv)
            # A run_id that never existed: exactly one rejected event, not two.
            with self.assertRaisesRegex(routing.RoutingError,"STATE_CONFLICT"):
                svc.store.close_run("run1_"+"0"*32,"failure")
            self.assertEqual(rejected_count(svc.store),1)
            # Closing an already-terminal run: still exactly one rejected event.
            d=svc.route(routing.TaskRequest("implementer","change","mechanical",selected_runtime="codex"),
                        self.observed(svc,"implementer","codex",task_class="mechanical",context_required=False))
            svc.store.mark_dispatched(d.run_id); svc.store.terminal(d.run_id,"success")
            with self.assertRaisesRegex(routing.RoutingError,"STATE_CONFLICT"):
                svc.store.close_run(d.run_id,"failure")
            self.assertEqual(rejected_count(svc.store),2)

    def test_unverified_review_reports_tier_without_execution(self):
        svc=self.service(simulate=True)
        facts=self.observed(svc,"package-reviewer","claude-code",context_required=False)
        d=svc.route(routing.TaskRequest("package-reviewer","change","documentation",selected_runtime="claude-code"),facts,unverified_review=True)
        self.assertFalse(d.execution_enabled); self.assertEqual(d.reason_codes,("REVIEW_IDENTITY_UNVERIFIED",))
        self.assertIsNotNone(d.model)
        strict=svc.route(routing.TaskRequest("package-reviewer","change","documentation",selected_runtime="claude-code"),
                         self.observed(svc,"package-reviewer","claude-code",context_required=False))
        self.assertEqual(strict.reason_codes,("REVIEW_IDENTITY_INVALID",))  # default stays 003-strict

    def test_dispatch_cli_mode_and_modifier_exclusion(self):
        cases=(["--route-decide","-","--routing-report"],
               ["--fresh-probes","--routing-report"],
               ["--latency-ms","5","--route-decide","-"],
               ["--route-terminal","run1_"+"a"*32,"success","--yes"],
               ["--route-decide","-","--yes"])  # N11: the real total-exclusion case (not the
               # argparse "expected one argument" usage error of `--route-decide --json --yes`)
        for extra in cases:
            result=subprocess.run([sys.executable,"ai/scripts/set_agents_app.py","--json",*extra],
                                  cwd=ROOT,text=True,capture_output=True,stdin=subprocess.DEVNULL)
            self.assertEqual(result.returncode,2,(extra,result.stdout,result.stderr))
            self.assertIn("ROUTING_INPUT_INVALID",result.stdout)
        bad=subprocess.run([sys.executable,"ai/scripts/set_agents_app.py","--route-dispatched","not-a-run","--json"],
                           cwd=ROOT,text=True,capture_output=True)
        self.assertEqual(bad.returncode,2); self.assertIn("ROUTING_INPUT_INVALID",bad.stdout)

    def test_compaction_keeps_bounded_events_and_percentiles(self):
        with tempfile.TemporaryDirectory() as td:
            svc=self.service(Path(td)/"state")
            store=svc.store; conn=store._connect()
            try:
                now=store._now(); conn.execute("BEGIN IMMEDIATE")
                conn.executemany("INSERT INTO events(occurred_at,event_type,route_id,runtime,provider,model,family,outcome,reason_family,latency_ms,latency_bucket) VALUES(?,?,?,?,?,?,?,?,?,?,?)",[(now,"terminal","rt", "codex","openai-codex","gpt-5.6-sol","gpt-5.6","success","none",n,"100+") for n in (10,20,30)])
                conn.execute("COMMIT")
            finally: conn.close()
            report=store.report(); self.assertEqual((report["p50_ms"],report["p90_ms"]),(20,30))

    # ------------------------------------------------------------- F01/F02/F03/F07/N04 CLI

    def _cli_env(self, routing_root, bins=None):
        env=dict(os.environ); env["SET_AGENTS_ROUTING_TEST_ROOT"]=str(routing_root)
        if bins is not None: env["PATH"]=f"{bins}:{env['PATH']}"
        return env

    def _cli_run(self, args, env, input_text=None):
        return subprocess.run([sys.executable,"ai/scripts/set_agents_app.py",*args],
                              cwd=ROOT,text=True,capture_output=True,env=env,input=input_text)

    def test_routing_migrate_uses_harness_identity_and_test_store(self):
        """The explicit schema-4 migration is testable and backfills the harness key."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "routing-root"
            store = routing.RoutingStore._for_tests(root)
            store._safe_dir(create=True)
            fd = os.open(store.db_path, os.O_CREAT | os.O_EXCL | os.O_RDWR, 0o600)
            os.close(fd)
            connection = sqlite3.connect(f"file:{store.db_path}?mode=rw", uri=True, isolation_level=None)
            try:
                store._configure(connection)
                # Frozen schema-4 fixture: this is the exact pre-005 dispatches
                # layout, including the index that migration must replace.
                connection.executescript("""
BEGIN EXCLUSIVE;
CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE dispatches (
 run_id TEXT PRIMARY KEY CHECK(run_id GLOB 'run1_[0-9a-f]*' AND length(run_id)=37), role TEXT NOT NULL, role_class TEXT NOT NULL CHECK(role_class='writer'),
 selected_route_id TEXT NOT NULL, selected_runtime TEXT NOT NULL, selected_provider TEXT NOT NULL, selected_model TEXT NOT NULL, selected_family TEXT NOT NULL, selected_effort TEXT NOT NULL,
 fallback_route_id TEXT, fallback_runtime TEXT, fallback_provider TEXT, fallback_model TEXT, fallback_family TEXT, fallback_effort TEXT,
 actual_route_id TEXT, actual_runtime TEXT, actual_provider TEXT, actual_model TEXT, actual_family TEXT, actual_effort TEXT,
 state TEXT NOT NULL CHECK(state IN ('authorized','dispatched','terminal_success','terminal_failure','abandoned')), partial_write INTEGER NOT NULL DEFAULT 0 CHECK(partial_write IN (0,1)), fallback_window_open INTEGER NOT NULL CHECK(fallback_window_open IN (0,1)), fallback_consumed INTEGER NOT NULL DEFAULT 0 CHECK(fallback_consumed IN (0,1)),
 authorized_at INTEGER NOT NULL, dispatched_at INTEGER, partial_write_at INTEGER, fallback_consumed_at INTEGER, terminal_at INTEGER, updated_at INTEGER NOT NULL,
 CHECK((fallback_route_id IS NULL AND fallback_runtime IS NULL AND fallback_provider IS NULL AND fallback_model IS NULL AND fallback_family IS NULL AND fallback_effort IS NULL) OR (fallback_route_id IS NOT NULL AND fallback_runtime IS NOT NULL AND fallback_provider IS NOT NULL AND fallback_model IS NOT NULL AND fallback_family IS NOT NULL AND fallback_effort IS NOT NULL)),
 CHECK((actual_route_id IS NULL AND actual_runtime IS NULL AND actual_provider IS NULL AND actual_model IS NULL AND actual_family IS NULL AND actual_effort IS NULL) OR (actual_route_id IS NOT NULL AND actual_runtime IS NOT NULL AND actual_provider IS NOT NULL AND actual_model IS NOT NULL AND actual_family IS NOT NULL AND actual_effort IS NOT NULL)),
 CHECK(state IN ('authorized','abandoned') OR actual_route_id IS NOT NULL),
 -- N03: abandoned is a never-dispatched close — it can never carry an actual (dispatched)
 -- identity. Its close timestamp is `updated_at` (documented here): `terminal_at`'s ordering
 -- CHECK below requires dispatched_at, which a never-dispatched row never has.
 CHECK(state<>'abandoned' OR (actual_route_id IS NULL AND actual_runtime IS NULL AND actual_provider IS NULL AND actual_model IS NULL AND actual_family IS NULL AND actual_effort IS NULL)),
 CHECK(state NOT IN ('terminal_success','terminal_failure','abandoned') OR fallback_window_open=0),
 CHECK(dispatched_at IS NULL OR dispatched_at>=authorized_at),
 CHECK(terminal_at IS NULL OR (dispatched_at IS NOT NULL AND terminal_at>=dispatched_at)),
 CHECK(fallback_consumed=0 OR fallback_route_id IS NOT NULL));
CREATE TABLE events (event_id INTEGER PRIMARY KEY, occurred_at INTEGER NOT NULL, event_type TEXT NOT NULL, route_id TEXT, runtime TEXT, provider TEXT, model TEXT, family TEXT, outcome TEXT NOT NULL, reason_family TEXT NOT NULL, latency_ms INTEGER, latency_bucket TEXT NOT NULL);
CREATE TABLE metric_rollups (route_key TEXT NOT NULL, runtime TEXT NOT NULL, provider TEXT NOT NULL, model TEXT NOT NULL, family TEXT NOT NULL, outcome TEXT NOT NULL, reason_family TEXT NOT NULL, latency_bucket TEXT NOT NULL, lifetime_count INTEGER NOT NULL, lifetime_latency_sum_ms INTEGER NOT NULL, compacted_count INTEGER NOT NULL, exclusion_count INTEGER NOT NULL, fallback_offered_count INTEGER NOT NULL, fallback_consumed_count INTEGER NOT NULL, fallback_success_count INTEGER NOT NULL, fallback_failure_count INTEGER NOT NULL, PRIMARY KEY(route_key,runtime,provider,model,family,outcome,reason_family,latency_bucket));
CREATE INDEX events_retention ON events(occurred_at,event_id); CREATE INDEX events_route_retention ON events(route_id,occurred_at,event_id); CREATE INDEX dispatches_review ON dispatches(role,state,terminal_at);
""")
                connection.execute("INSERT INTO meta VALUES('schema_version','4')")
                connection.execute("INSERT INTO meta VALUES('installation_hmac_salt','a' || printf('%063d', 0))")
                connection.execute("INSERT INTO dispatches VALUES(" + ",".join("?" for _ in range(31)) + ")", (
                    "run1_" + "a" * 32, "implementer", "writer", "r", "codex", "openai-codex", "gpt-5.6-sol", "gpt-5.6", "high",
                    None, None, None, None, None, None, None, None, None, None, None, None,
                    "authorized", 0, 1, 0, 1, None, None, None, None, 1,
                ))
                connection.execute("COMMIT")
            finally:
                connection.close()
            identity = json.loads((ROOT / "ai/state/project.json").read_text())["project_key"]
            result = self._cli_run(["--routing-migrate"], self._cli_env(root))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertRegex(result.stdout, r"ROUTING_MIGRATE_OK from=4 to=5 rows=1 backup=.+")
            migrated = sqlite3.connect(f"file:{store.db_path}?mode=ro", uri=True)
            try:
                self.assertEqual(dict(migrated.execute("SELECT key,value FROM meta"))["schema_version"], "5")
                self.assertEqual(migrated.execute("SELECT project_key FROM dispatches").fetchone(), (identity,))
            finally:
                migrated.close()
            self.assertEqual(len(list((root / "backups").glob("routing-v4-*.db"))), 1)
            routing.RoutingStore._for_tests(root, project_key=identity)._validate_existing_readonly()

    def test_project_scoped_lifecycle_cannot_mutate_a_foreign_run(self):
        """P1-REV-001: opaque run ids are never a cross-project write capability."""
        project_b = "proj1_" + "b" * 32
        with tempfile.TemporaryDirectory() as td:
            svc = self.service(Path(td) / "routing", inventory={("codex", "openai-codex"): {"gpt-5.6-sol"}})
            decision = svc.route(
                routing.TaskRequest("implementer", "change", "mechanical", selected_runtime="codex"),
                self.observed(svc, "implementer", "codex", task_class="mechanical", context_required=False),
            )
            foreign = routing.RoutingStore._for_tests(Path(td) / "routing", project_key=project_b)
            for operation, error in (
                (lambda: foreign.mark_dispatched(decision.run_id), "STATE_CONFLICT"),
                (lambda: foreign.consume_fallback(decision.run_id), "FALLBACK_DENIED"),
                (lambda: foreign.abandon(decision.run_id), "STATE_CONFLICT"),
                (lambda: foreign.close_run(decision.run_id, "failure"), "STATE_CONFLICT"),
            ):
                with self.assertRaisesRegex(routing.RoutingError, error):
                    operation()
            self.assertEqual(svc.store.open_runs()[0]["state"], "authorized")

            svc.store.mark_dispatched(decision.run_id)
            for operation in (
                lambda: foreign.mark_partial(decision.run_id),
                lambda: foreign.terminal(decision.run_id, "failure"),
                lambda: foreign.close_run(decision.run_id, "success"),
            ):
                with self.assertRaisesRegex(routing.RoutingError, "STATE_CONFLICT"):
                    operation()
            self.assertEqual(svc.store.open_runs()[0]["state"], "dispatched")
            svc.store.terminal(decision.run_id, "success")
            self.assertEqual(foreign.recent_writers(), [])
            with self.assertRaisesRegex(routing.RoutingError, "REVIEW_IDENTITY_INVALID"):
                foreign.implementation_identity(decision.run_id)

    def test_project_identity_fallback_corruption_and_nonregular_files_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / ".git").mkdir()
            # A Git-only project has no state directory and deliberately uses the
            # normalized path hash rather than rejecting routing outright.
            self.assertRegex(set_agents_app.project_key_for(root), r"^proj1_[0-9a-f]{32}$")
            identity = root / "ai/state/project.json"
            identity.parent.mkdir(parents=True)
            identity.write_text("{not json")
            with self.assertRaises(set_agents_app.ProjectIdentityError):
                set_agents_app.project_key_for(root)
            identity.unlink()
            os.mkfifo(identity)
            started = time.monotonic()
            self.assertIsNone(set_agents_app._safe_read(identity, limit=1024))
            self.assertLess(time.monotonic() - started, 1.0)

    def test_malformed_project_feature_documents_degrade_without_traceback(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            features = root / "ai/state/features"
            features.mkdir(parents=True)
            (features / "bad.json").write_text(json.dumps({"feature_id": "bad", "packages": {"not": "a list"}}))
            (features / "also-bad.json").write_text(json.dumps({"feature_id": "also-bad", "packages": ["not-a-dict"]}))
            old_root, old_project = set_agents_app.ROOT, set_agents_app.PROJECT_ROOT
            set_agents_app.ROOT = root
            set_agents_app.PROJECT_ROOT = root
            try:
                self.assertIsNone(set_agents_app._load_feature_doc(features / "bad.json"))
                self.assertEqual(set_agents_app._resolve_context_pack("bad", None), (False, "bad", None))
                self.assertEqual(set_agents_app._resolve_context_pack(None, None), (None, None, None))
            finally:
                set_agents_app.ROOT, set_agents_app.PROJECT_ROOT = old_root, old_project

    def test_schema_four_warning_is_informational_and_never_auto_migrates(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            project = root / "git-only"
            project.mkdir(); (project / ".git").mkdir()
            routing_root = root / "routing"
            store = routing.RoutingStore._for_tests(routing_root)
            store._safe_dir(create=True)
            fd = os.open(store.db_path, os.O_CREAT | os.O_EXCL | os.O_RDWR, 0o600)
            os.close(fd)
            conn = sqlite3.connect(store.db_path)
            try:
                conn.execute("CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
                conn.execute("INSERT INTO meta VALUES('schema_version','4')")
                conn.commit()
            finally:
                conn.close()
            env = self._cli_env(routing_root)
            result = subprocess.run(
                [sys.executable, "ai/scripts/set_agents_app.py", "--routing-report", "--project", str(project), "--json"],
                cwd=ROOT, text=True, capture_output=True, env=env,
            )
            self.assertEqual(result.returncode, 1, result.stderr)
            envelope = json.loads(result.stdout)
            self.assertIn("ROUTING_SCHEMA_MIGRATION_REQUIRED", envelope["warnings"])
            check = sqlite3.connect(store.db_path)
            try:
                self.assertEqual(dict(check.execute("SELECT key,value FROM meta"))["schema_version"], "4")
            finally:
                check.close()

    def test_route_decide_cli_hermetic_matrix(self):
        # N04/F01/F02/F07: a fully hermetic decide->dispatched->terminal(->abandoned) cycle
        # against a temp routing root (the F07 seam), driving every role_class shape of the
        # F01 reason->exit table through the real CLI subprocess.
        with tempfile.TemporaryDirectory() as td:
            bins, log = self._probe_stubs(td)
            env=self._cli_env(Path(td)/"routing-root", bins)

            def decide(descriptor):
                return self._cli_run(["--route-decide","-","--json"],env,json.dumps(descriptor))

            # Writer: executable, ok=true, exit 0.
            writer=decide({"role":"implementer","task_class":"mechanical","selected_runtime":"codex"})
            self.assertEqual(writer.returncode,0,(writer.stdout,writer.stderr))
            wdata=json.loads(writer.stdout)
            self.assertTrue(wdata["ok"]); self.assertTrue(wdata["data"]["execution_enabled"])
            self.assertEqual(wdata["data"]["reason_codes"],[])
            run_id=wdata["data"]["run_id"]; self.assertTrue(run_id.startswith("run1_"))
            self.assertEqual(wdata["data"]["tier"],"fast")

            # docs-rw ("other" role_class): non-executable, empty reason_codes, still ok=true.
            other=decide({"role":"product-analyst","task_class":"documentation","selected_runtime":"claude-code"})
            self.assertEqual(other.returncode,0,(other.stdout,other.stderr))
            odata=json.loads(other.stdout)
            self.assertTrue(odata["ok"]); self.assertFalse(odata["data"]["execution_enabled"])
            self.assertEqual(odata["data"]["reason_codes"],[])

            # Reviewer without review_of_run_id: unverified, ok=true, exit 0, tier still reported.
            unverified=decide({"role":"package-reviewer","task_class":"documentation","selected_runtime":"claude-code"})
            self.assertEqual(unverified.returncode,0,(unverified.stdout,unverified.stderr))
            udata=json.loads(unverified.stdout)
            self.assertTrue(udata["ok"]); self.assertFalse(udata["data"]["execution_enabled"])
            self.assertEqual(udata["data"]["reason_codes"],["REVIEW_IDENTITY_UNVERIFIED"])
            self.assertIsNotNone(udata["data"]["model"])
            self.assertFalse(udata["data"]["independence_verified"])

            # An unknown role: ok=false, exit 1 — the "other side" of the F01 table.
            unknown=decide({"role":"nonexistent-role","task_class":"documentation"})
            self.assertEqual(unknown.returncode,1,(unknown.stdout,unknown.stderr))
            self.assertFalse(json.loads(unknown.stdout)["ok"])

            # F07/lifecycle: dispatched -> terminal(success), all via CLI against the temp root.
            dispatched=self._cli_run(["--route-dispatched",run_id,"--json"],env)
            self.assertEqual(dispatched.returncode,0,(dispatched.stdout,dispatched.stderr))
            self.assertEqual(json.loads(dispatched.stdout)["data"]["state"],"dispatched")
            terminal=self._cli_run(["--route-terminal",run_id,"success","--json"],env)
            self.assertEqual(terminal.returncode,0,(terminal.stdout,terminal.stderr))
            self.assertEqual(json.loads(terminal.stdout)["data"]["state"],"terminal_success")

            recent=self._cli_run(["--routing-recent-writers","--json"],env)
            self.assertEqual(recent.returncode,0)
            self.assertEqual([r["run_id"] for r in json.loads(recent.stdout)["data"]["recent_writers"]],[run_id])

            # Reviewer WITH a verified review_of_run_id: a candidate is found (a different
            # provider/family than the writer above), ok=true, independence_verified true.
            verified=decide({"role":"package-reviewer","task_class":"documentation","selected_runtime":"claude-code",
                             "review_of_run_id":run_id})
            self.assertEqual(verified.returncode,0,(verified.stdout,verified.stderr))
            vdata=json.loads(verified.stdout)
            self.assertTrue(vdata["ok"]); self.assertFalse(vdata["data"]["execution_enabled"])
            self.assertEqual(vdata["data"]["reason_codes"],[])
            self.assertTrue(vdata["data"]["independence_verified"])
            self.assertNotEqual(vdata["data"]["provider"],"openai-codex")

            # A second writer decide, closed as failure BEFORE dispatch -> abandoned (F02/F07).
            second=decide({"role":"implementer","task_class":"mechanical","selected_runtime":"codex"})
            second_run=json.loads(second.stdout)["data"]["run_id"]
            abandoned=self._cli_run(["--route-terminal",second_run,"failure","--json"],env)
            self.assertEqual(abandoned.returncode,0,(abandoned.stdout,abandoned.stderr))
            self.assertEqual(json.loads(abandoned.stdout)["data"]["state"],"abandoned")
            open_runs=json.loads(self._cli_run(["--routing-open-runs","--json"],env).stdout)["data"]["open_runs"]
            self.assertEqual(open_runs,[])

    def test_route_decide_cli_lock_fails_closed(self):
        # F01: SQLITE busy (holder BEGIN IMMEDIATE) ⇒ ROUTING_UNAVAILABLE, exit 1, no retry.
        with tempfile.TemporaryDirectory() as td:
            bins, log = self._probe_stubs(td)
            routing_root=Path(td)/"routing-root"
            env=self._cli_env(routing_root, bins)
            descriptor=json.dumps({"role":"implementer","task_class":"mechanical","selected_runtime":"codex"})
            first=self._cli_run(["--route-decide","-","--json"],env,descriptor)
            self.assertEqual(first.returncode,0,(first.stdout,first.stderr))
            holder=sqlite3.connect(routing_root/"routing.db")
            holder.execute("PRAGMA busy_timeout=0")
            holder.execute("BEGIN IMMEDIATE")
            try:
                locked=self._cli_run(["--route-decide","-","--json"],env,descriptor)
                self.assertEqual(locked.returncode,1,(locked.stdout,locked.stderr))
                ldata=json.loads(locked.stdout)
                self.assertFalse(ldata["ok"]); self.assertEqual(ldata["reason_codes"],["ROUTING_UNAVAILABLE"])
            finally:
                holder.execute("ROLLBACK"); holder.close()

    def test_route_terminal_latency_bound_rejects_without_traceback(self):
        # SEC-A02: an out-of-range (OverflowError-at-bind-time) or negative --latency-ms is a
        # PARSE failure at the CLI, before it ever reaches the store — exit 2, one JSON line,
        # never a traceback.
        with tempfile.TemporaryDirectory() as td:
            env=self._cli_env(Path(td)/"routing-root")
            run_id="run1_"+"a"*32
            for bad in (str(2**70), "-5"):
                result=self._cli_run(["--route-terminal",run_id,"success","--latency-ms",bad,"--json"],env)
                self.assertEqual(result.returncode,2,(bad,result.stdout,result.stderr))
                self.assertEqual(result.stdout.count("\n"),1)
                self.assertNotIn("Traceback",result.stderr)
                self.assertIn("ROUTING_INPUT_INVALID",result.stdout)

    def test_route_decide_empty_string_never_falls_through_to_menu(self):
        # F08/N11: `--route-decide ""` is PRESENT (an empty string), not ABSENT — truthiness
        # would let it fall through every mode check into the interactive menu/help.
        result=subprocess.run([sys.executable,"ai/scripts/set_agents_app.py","--route-decide","","--json"],
                              cwd=ROOT,text=True,capture_output=True,stdin=subprocess.DEVNULL)
        self.assertEqual(result.returncode,2,(result.stdout,result.stderr))
        self.assertEqual(result.stdout.count("\n"),1)
        self.assertIn("ROUTING_INPUT_INVALID",result.stdout)

    def test_route_decide_descriptor_enum_violations_are_parse_errors(self):
        # F01: a risk/selected_runtime outside the closed enum is caught at PARSE (exit 2),
        # never reaching the service to degrade into a generic FACTS_INCOMPLETE.
        for bad in ({"role":"implementer","task_class":"documentation","risk":"extreme"},
                    {"role":"implementer","task_class":"documentation","selected_runtime":"bogus"}):
            result=subprocess.run([sys.executable,"ai/scripts/set_agents_app.py","--route-decide","-","--json"],
                                  cwd=ROOT,text=True,capture_output=True,input=json.dumps(bad))
            self.assertEqual(result.returncode,2,(bad,result.stdout,result.stderr))
            self.assertIn("ROUTING_INPUT_INVALID",result.stdout)

    def test_decide_status_helper_matrix(self):
        # F01: the centralized reason->exit helper, exhaustively.
        RD=routing.RouteDecision
        self.assertEqual(set_agents_app._decide_status(RD(*[None]*6,True,())),(True,0))
        self.assertEqual(set_agents_app._decide_status(RD(*[None]*6,False,())),(True,0))
        self.assertEqual(set_agents_app._decide_status(RD(*[None]*6,False,("REVIEW_IDENTITY_UNVERIFIED",))),(True,0))
        for reason in ("FACTS_INCOMPLETE","NO_ELIGIBLE_ROUTE","REVIEW_IDENTITY_INVALID","PROVIDER_UNAUTHENTICATED",
                      "AUTHORIZATION_INVALID","AUTHORIZATION_REPLAY","CATALOG_INVALID","STATE_CONFLICT",
                      "ROUTING_UNAVAILABLE","REVIEWER_INDEPENDENCE_UNAVAILABLE"):
            self.assertEqual(set_agents_app._decide_status(RD(*[None]*6,False,(reason,))),(False,1),reason)

    def test_validate_context_pack_path_rejects_unsafe_values(self):
        # SEC-A02: non-str, absolute, and traversal-outside-ROOT all degrade to "no pack" —
        # never a bare `ROOT / pack` (which silently discards ROOT for an absolute value).
        old_root=set_agents_app.ROOT
        with tempfile.TemporaryDirectory() as td:
            set_agents_app.ROOT=Path(td)
            try:
                self.assertIsNone(set_agents_app._validate_context_pack_path(None))
                self.assertIsNone(set_agents_app._validate_context_pack_path(123))
                self.assertIsNone(set_agents_app._validate_context_pack_path([]))
                self.assertIsNone(set_agents_app._validate_context_pack_path(""))
                self.assertIsNone(set_agents_app._validate_context_pack_path("/etc/passwd"))
                self.assertIsNone(set_agents_app._validate_context_pack_path("../outside.md"))
                (Path(td)/"docs").mkdir()
                (Path(td)/"docs/pack.md").write_text("x")
                self.assertEqual(set_agents_app._validate_context_pack_path("docs/pack.md"),
                                 (Path(td)/"docs/pack.md").resolve())
            finally:
                set_agents_app.ROOT=old_root

    def _write_feature_doc(self, root, name, phase, pkg_status, updated_at=None, context_pack="docs/pack.md", pkg_updated_at=None):
        doc={"feature_id":name,"phase":phase,"current_package_id":"P1","updated_at":updated_at,
             "packages":[{"package_id":"P1","status":pkg_status,"context_pack":context_pack,"updated_at":pkg_updated_at}]}
        (root/"ai/state/features"/f"{name}.json").write_text(json.dumps(doc))

    def test_resolve_context_pack_phase_freshness_and_default_resolution(self):
        # F03/N05/N06: existence AND freshness, the phase filter applies even with an explicit
        # feature_id, and the default resolution picks the feature whose CURRENT package is
        # actively executing (not merely "feature phase isn't terminal").
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); (root/"ai/state/features").mkdir(parents=True); (root/"docs").mkdir()
            pack=root/"docs/pack.md"; pack.write_text("ctx")
            old_root=set_agents_app.ROOT; set_agents_app.ROOT=root
            try:
                # (a) Explicit feature_id, but the feature is BLOCKED: never flips CONTEXT_MISSING.
                self._write_feature_doc(root,"blocked-feat","BLOCKED","in_progress")
                self.assertEqual(set_agents_app._resolve_context_pack("blocked-feat",None),(False,"blocked-feat","P1"))
                # (b) Explicit feature_id, active, fresh pack (mtime just touched): True.
                self._write_feature_doc(root,"active-feat","PACKAGE_GATES","in_progress","2020-01-01T00:00:00+00:00")
                os.utime(pack,(time.time(),time.time()))
                self.assertEqual(set_agents_app._resolve_context_pack("active-feat",None),(True,"active-feat","P1"))
                # (c) Same shape, but the pack PREDATES the package's own updated_at: stale ⇒ False.
                self._write_feature_doc(root,"stale-feat","PACKAGE_GATES","in_progress",
                                        pkg_updated_at="2099-01-01T00:00:00+00:00")
                self.assertEqual(set_agents_app._resolve_context_pack("stale-feat",None),(False,"stale-feat","P1"))
                # (d) No feature_id, TWO candidates whose current package is actively executing
                # (active-feat and stale-feat both qualify) ⇒ CONTEXT_UNRESOLVED (None), distinct
                # from a resolved-but-missing pack.
                ok,_,_=set_agents_app._resolve_context_pack(None,None)
                self.assertIsNone(ok)
                # (e) A package sitting at a TERMINAL status (e.g. already accepted) is never a
                # default candidate even though its feature's phase isn't DONE/BLOCKED — remove
                # the freshness-ambiguity contributor (stale-feat) but KEEP accepted-feat: if the
                # terminal-package-status filter were broken, this would still resolve to
                # ambiguous (None) instead of the single remaining active-feat.
                self._write_feature_doc(root,"accepted-feat","PACKAGE_ACCEPTED","accepted")
                (root/"ai/state/features"/"stale-feat.json").unlink()
                ok,fid,pid=set_agents_app._resolve_context_pack(None,None)
                self.assertEqual((ok,fid,pid),(True,"active-feat","P1"))
            finally:
                set_agents_app.ROOT=old_root

    def test_resolve_context_pack_opens_only_the_named_file(self):
        # N10 (perf): with an explicit feature_id, resolution never globs the directory.
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); (root/"ai/state/features").mkdir(parents=True)
            self._write_feature_doc(root,"only-me","PACKAGE_GATES","in_progress",context_pack=None)
            old_root=set_agents_app.ROOT; set_agents_app.ROOT=root
            try:
                with mock.patch.object(Path,"glob",side_effect=AssertionError("must not glob with an explicit feature_id")):
                    result=set_agents_app._resolve_context_pack("only-me",None)
                self.assertEqual(result,(False,"only-me","P1"))  # no context_pack ⇒ False, but no crash/glob
            finally:
                set_agents_app.ROOT=old_root

    def _toml_row(self, row):
        lines=["[[routes]]"]
        for key, value in row.items():
            if isinstance(value, str):
                lines.append(f'{key} = "{value}"')
            elif isinstance(value, list):
                items=", ".join(f'"{item}"' for item in value)
                lines.append(f'{key} = [{items}]')
            else:
                lines.append(f'{key} = {value}')
        return "\n".join(lines)

    def _write_catalog(self, td, rows):
        text="catalog_version = 2\n\n" + "\n\n".join(self._toml_row(row) for row in rows) + "\n"
        path=Path(td)/"routes.toml"; path.write_text(text)
        return path

    def test_catalog_negative_matrix(self):
        # N04: the closed-schema/enum negative matrix, isolated from the roster-coverage check
        # (each case raises during its own row's validation, before coverage is even reached).
        base=dict(provider="openai-codex", model="gpt-5.6-luna", family="gpt-5.6", effort="low",
                  tier="fast", roles=["implementer"], tools=["read","shell","write"], curated_priority=10)
        cases={
            "tiers-list (old schema)": {**{k:v for k,v in base.items() if k!="tier"}, "tiers":["fast"]},
            "unknown tier": {**base, "tier":"ultra"},
            "xhigh unbenchmarked": {**base, "effort":"xhigh"},
            "codex effort not configured": {**base, "effort":"nope"},
            "anthropic effort not medium": {**base, "provider":"anthropic", "model":"haiku", "family":"haiku", "effort":"low"},
            "unaudited runtime": {**base, "runtimes":["pi"]},
        }
        with tempfile.TemporaryDirectory() as td:
            for label, row in cases.items():
                path=self._write_catalog(td,[row])
                with self.assertRaises(routing.RoutingError, msg=label):
                    routing_catalog.build_snapshot(path, self.roster, self.config)
            # Two rows differing ONLY in `runtimes` collapse to the same canonical tuple
            # (AC-12: runtimes is never part of the static-ID) and stay a duplicate.
            path=self._write_catalog(td,[{**base,"runtimes":["codex"]},{**base,"runtimes":["opencode"]}])
            with self.assertRaises(routing.RoutingError):
                routing_catalog.build_snapshot(path, self.roster, self.config)

if __name__ == "__main__": unittest.main()
