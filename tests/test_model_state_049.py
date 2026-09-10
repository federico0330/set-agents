import json
import sys
import tempfile
import shutil
import subprocess
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ai/scripts"))


class ModelStateSchemaTests(unittest.TestCase):
    def test_schema_v1_is_singular_and_uses_only_closed_reasons(self):
        import model_state

        state = model_state.empty_state("opencode")
        self.assertEqual(1, state["schema_version"])
        self.assertEqual({"runtime": "opencode", "role": "orchestrator"}, state["scope"])
        self.assertEqual("unobserved", state["observed"]["status"])
        self.assertEqual("not_checked", state["refresh"]["observed"]["reason"])
        self.assertIsNone(state["refresh"]["observed"]["checked_at"])
        self.assertNotIn("session_id", json.dumps(state))
        reasons = set(model_state.ModelStateReason)
        self.assertEqual({
            "not_checked", "unsupported_runtime", "opencode_absent", "project_unresolved",
            "timeout", "invalid_json", "output_limit", "session_limit", "no_project_root",
            "no_submitted_message", "cache_read_failed", "probe_failed", "child_failed",
            "not_installed", "unavailable",
        }, {item.value for item in reasons})

    def test_non_opencode_is_unobserved_without_runner(self):
        import model_state

        called = []
        observed = model_state.observe_opencode(Path("/tmp/p"), runtime="codex", runner=lambda *a, **k: called.append(a))
        self.assertEqual("unsupported_runtime", observed["reason"])
        self.assertEqual([], called)


class DesiredInstalledRoutingTests(unittest.TestCase):
    def test_desired_installed_and_pinned_are_independent_evidence(self):
        import model_state
        with tempfile.TemporaryDirectory() as td:
            home = Path(td)
            config = {"areas": {"coord": {"opencode": "opaque/future-model"}},
                      "roles": {"orchestrator": {}}}
            row = {"role": "orchestrator", "duty": "coord"}
            target = home / ".config/opencode/agents/orchestrator.md"
            target.parent.mkdir(parents=True)
            target.write_text("---\nmodel: opaque/installed-model\n---\n", encoding="utf-8")
            preference = home / "model-preference.toml"
            preference.write_text('[model_pin]\norchestrator = "opaque/pin"\n', encoding="utf-8")
            desired = model_state.desired_state(config, row, "opencode")
            installed = model_state.installed_state("opencode", home)
            routing = model_state.routing_state(preference)
        self.assertEqual("opaque/future-model", desired["model"])
        self.assertEqual("opaque/installed-model", installed["model"])
        self.assertEqual("pinned", routing["status"])

    def test_missing_installed_file_and_no_pin_do_not_become_errors(self):
        import model_state
        with tempfile.TemporaryDirectory() as td:
            home = Path(td)
            installed = model_state.installed_state("opencode", home)
            routing = model_state.routing_state(home / "missing.toml")
        self.assertEqual(("absent", "not_installed"), (installed["status"], installed["reason"]))
        self.assertEqual(("dynamic", None), (routing["status"], routing["reason"]))


class OpenCodeObserverTests(unittest.TestCase):
    def test_official_11814_shape_uses_epoch_roots_and_structured_model(self):
        """RED: the documented 1.18.14 shape is not the old string-only double."""
        import model_state
        project = Path("/tmp/project").resolve()
        sessions = [
            {"id": "old-id", "directory": str(project), "parentID": None,
             "time": {"updated": 1_770_000_001_000}},
            {"id": "child-id", "directory": str(project), "parentID": "old-id",
             "time": {"updated": 1_770_000_003_000}},
            {"id": "new-id", "directory": str(project), "parentID": None,
             "time": {"updated": 1_770_000_002_000}},
        ]
        export = {"messages": [
            {"info": {"id": "assistant-id", "role": "assistant",
                        "time": {"created": 1_770_000_010_000},
                        "model": {"providerID": "ignored", "modelID": "ignored"}}},
            {"info": {"id": "user-id", "role": "user",
                        "time": {"created": 1_770_000_020_000},
                        "model": {"providerID": "opaque-provider", "modelID": "opaque-model"}}},
        ]}
        commands = []
        def runner(command, **kwargs):
            commands.append(command)
            return 0, json.dumps(sessions if command[1] == "session" else export)
        observed = model_state.observe_opencode(project, runtime="opencode", runner=runner)
        self.assertEqual(("observed", "opaque-provider/opaque-model", "2026-02-02T02:40:20.000Z"),
                         (observed["status"], observed["model"], observed["observed_at"]))
        self.assertEqual("new-id", commands[1][-1])

    def test_empty_list_output_aggregate_limit_and_oserror_are_closed_degradations(self):
        import model_state
        project = Path("/tmp/project").resolve()
        calls = []
        def empty(command, **kwargs):
            calls.append(command)
            return 0, ""
        observed = model_state.observe_opencode(project, runtime="opencode", runner=empty)
        self.assertEqual(("unobserved", "invalid_json"), (observed["status"], observed["reason"]))
        self.assertEqual(1, len(calls))

        calls.clear()
        def over_aggregate(command, **kwargs):
            calls.append(command)
            return 0, " " * (1024 * 1024 + 1)
        observed = model_state.observe_opencode(project, runtime="opencode", runner=over_aggregate)
        self.assertEqual(("unobserved", "output_limit"), (observed["status"], observed["reason"]))
        self.assertEqual(1, len(calls))

        observed = model_state.observe_opencode(
            project, runtime="opencode", runner=lambda *a, **k: (_ for _ in ()).throw(PermissionError("no")))
        self.assertEqual(("unobserved", "child_failed"), (observed["status"], observed["reason"]))

    def test_file_not_found_maps_to_absent(self):
        import model_state
        observed = model_state.observe_opencode(
            Path("/tmp/project"), runtime="opencode",
            runner=lambda *a, **k: (_ for _ in ()).throw(FileNotFoundError("missing")))
        self.assertEqual(("unobserved", "opencode_absent"), (observed["status"], observed["reason"]))

    def test_real_child_capture_is_bounded_and_reaped(self):
        import model_state
        status, output, used = model_state._bounded_child(
            [sys.executable, "-c", "import sys; sys.stdout.write('x' * (1024 * 1024 + 65536)); sys.stderr.write('y')"],
            str(ROOT), 3, 1024 * 1024)
        self.assertEqual("limited", status)
        self.assertLessEqual(len(output), 1024 * 1024)
        self.assertLessEqual(used, 1024 * 1024)

    def test_real_child_nonzero_is_failed(self):
        import model_state
        status, output, used = model_state._bounded_child(
            [sys.executable, "-c", "import sys; sys.stdout.write('private'); sys.exit(7)"],
            str(ROOT), 3, 1024 * 1024)
        self.assertEqual("failed", status)
        self.assertEqual(b"private", output)
        self.assertEqual(len(b"private"), used)

    def test_equal_submissions_use_message_id_only_as_internal_descending_tiebreak(self):
        import model_state
        project = Path("/tmp/project").resolve()
        sessions = [{"id": "root-id", "directory": str(project), "parentID": None,
                     "time": {"updated": 1_770_000_001_000}}]
        exported = {"messages": [
            {"info": {"id": "alpha-private", "role": "user", "time": {"created": 1_770_000_020_000},
                      "model": {"providerID": "opaque", "modelID": "first"}}},
            {"info": {"id": "zeta-private", "role": "user", "time": {"created": 1_770_000_020_000},
                      "model": {"providerID": "opaque", "modelID": "second"}}},
        ]}
        def runner(command, **kwargs):
            return 0, json.dumps(sessions if command[1] == "session" else exported)
        observed = model_state.observe_opencode(project, runtime="opencode", runner=runner)
        self.assertEqual("opaque/second", observed["model"])
        self.assertNotIn("zeta-private", json.dumps(observed))
    def test_selects_latest_canonical_root_and_never_returns_ids_or_transcript(self):
        import model_state
        project = Path("/tmp/project").resolve()
        commands = []
        sessions = [
            {"id": "old-id", "directory": str(project), "parentID": None, "time": {"updated": 1_770_000_001_000}},
            {"id": "child-id", "directory": str(project), "parentID": "old-id", "time": {"updated": 1_770_000_003_000}},
            {"id": "other-id", "directory": str(project) + "-other", "parentID": None, "time": {"updated": 1_770_000_004_000}},
            {"id": "new-id", "directory": str(project), "parentID": None, "time": {"updated": 1_770_000_002_000}},
        ]
        export = {"info": {"id": "new-id"}, "messages": [
            {"info": {"id": "assistant-id", "role": "assistant", "time": {"created": 1_770_000_003_000}, "model": {"providerID": "leak", "modelID": "no"}}, "parts": [{"text": "secret assistant answer"}]},
            {"info": {"id": "user-id", "role": "user", "time": {"created": 1_770_000_002_000}, "model": {"providerID": "opaque", "modelID": "sent-model"}}, "parts": [{"text": "secret prompt"}]},
        ]}
        def runner(command, **kwargs):
            commands.append(command)
            return 0, json.dumps(sessions if command[1:3] == ["session", "list"] else export)
        observed = model_state.observe_opencode(project, runtime="opencode", runner=runner)
        rendered = json.dumps(observed)
        self.assertEqual(("observed", "opaque/sent-model"), (observed["status"], observed["model"]))
        self.assertEqual(["opencode", "session", "list", "--format", "json", "--pure"], commands[0])
        self.assertEqual(["opencode", "export", "--sanitize", "--pure", "new-id"], commands[1])
        for private in ("new-id", "user-id", "secret prompt", "secret assistant answer"):
            self.assertNotIn(private, rendered)

    def test_malformed_timeout_and_more_than_twenty_roots_degrade_without_export(self):
        import model_state
        project = Path("/tmp/project").resolve()
        failures = [
            (lambda command, **kwargs: (0, "not json"), "invalid_json"),
            (lambda command, **kwargs: (_ for _ in ()).throw(subprocess.TimeoutExpired(command, 1)), "timeout"),
            (lambda command, **kwargs: (0, json.dumps([{"id": str(i), "directory": str(project), "parentID": None, "time": {"updated": i}} for i in range(21)])), "session_limit"),
        ]
        for runner, reason in failures:
            with self.subTest(reason=reason):
                observed = model_state.observe_opencode(project, runtime="opencode", runner=runner)
                self.assertEqual(("unobserved", reason), (observed["status"], observed["reason"]))

    def test_export_output_limit_and_empty_messages_are_safe_degradations(self):
        import model_state
        project = Path("/tmp/project").resolve()
        roots = [{"id": "root-id", "directory": str(project), "parentID": None, "time": {"updated": 1_770_000_001_000}}]
        def too_large(command, **kwargs):
            return 0, json.dumps(roots) if command[1] == "session" else "x" * (1024 * 1024 + 1)
        def no_messages(command, **kwargs):
            return 0, json.dumps(roots if command[1] == "session" else {"info": {}, "messages": []})
        for runner, reason in ((too_large, "output_limit"), (no_messages, "no_submitted_message")):
            with self.subTest(reason=reason):
                observed = model_state.observe_opencode(project, runtime="opencode", runner=runner)
                self.assertEqual(("unobserved", reason, None),
                                 (observed["status"], observed["reason"], observed["model"]))


class AggregateStateTests(unittest.TestCase):
    def test_collects_effective_desired_readback_routing_and_refreshes(self):
        import model_state
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "root"
            root.mkdir()
            shutil.copy(ROOT / "roles.tsv", root / "roles.tsv")
            shutil.copy(ROOT / "models.toml", root / "models.toml")
            home = Path(td) / "home"
            installed = home / ".config/opencode/agents/orchestrator.md"
            installed.parent.mkdir(parents=True)
            installed.write_text("---\nmodel: openai/gpt-5.5\n---\n", encoding="utf-8")
            state = model_state.collect_model_state(root, home=home, project=None, runner=None)
        self.assertEqual("openai/gpt-5.5", state["desired"]["model"])
        self.assertEqual("applied", state["convergence"]["status"])
        self.assertEqual("fresh", state["refresh"]["desired"]["status"])
        self.assertEqual("project_unresolved", state["observed"]["reason"])


class InstalledAndRenderTests(unittest.TestCase):
    def test_reads_actual_orchestrator_artifact_for_every_supported_runtime(self):
        import model_state
        with tempfile.TemporaryDirectory() as td:
            home = Path(td)
            fixtures = {
                "opencode": (home / ".config/opencode/agents/orchestrator.md", "---\nmodel: opaque/open\n---\n"),
                "codex": (home / ".codex/agents/orchestrator.toml", 'model = "opaque/codex"\n'),
                "claude-code": (home / ".claude/agents/orchestrator.md", "---\nmodel: opaque/claude\n---\n"),
                "cursor": (home / ".cursor/agents/orchestrator.md", "---\nmodel: opaque/cursor\n---\n"),
            }
            for runtime, (path, contents) in fixtures.items():
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(contents, encoding="utf-8")
                installed = model_state.installed_state(runtime, home)
                self.assertEqual(("installed", {"opencode": "opaque/open", "codex": "opaque/codex", "claude-code": "opaque/claude", "cursor": "opaque/cursor"}[runtime], None),
                                 (installed["status"], installed["model"], installed["reason"]))

    def test_human_renderer_escapes_controls_without_changing_json(self):
        import model_state
        state = model_state.empty_state("opencode")
        opaque = "opaque/\x1b]52;c;secret\x07"
        state["desired"] = {"status": "resolved", "source": "test", "model": opaque, "reason": None}
        self.assertEqual(opaque, json.loads(json.dumps(state))["desired"]["model"])
        rendered = model_state.render_human(state)
        self.assertIn("\\x1b", rendered)
        self.assertNotIn("\x1b", rendered)

    def test_human_renderer_escapes_c1_without_changing_json(self):
        import model_state
        state = model_state.empty_state("opencode")
        opaque = "opaque/\u0085c1"
        state["installed"] = {"status": "installed", "source": "test", "model": opaque, "reason": None}
        self.assertEqual(opaque, json.loads(json.dumps(state))["installed"]["model"])
        rendered = model_state.render_human(state)
        self.assertIn("\\x85", rendered)
        self.assertNotIn("\u0085", rendered)


class ModelStateCliTests(unittest.TestCase):
    def test_model_state_json_is_one_schema_object(self):
        script = ROOT / "ai/scripts/set_agents_app.py"
        completed = subprocess.run([sys.executable, str(script), "--model-state", "--json", "--project", str(ROOT)],
                                   text=True, capture_output=True, cwd=ROOT, timeout=10,
                                   env={**dict(__import__("os").environ), "PATH": ""})
        self.assertEqual(0, completed.returncode, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertEqual((1, "orchestrator"), (payload["schema_version"], payload["scope"]["role"]))
        self.assertNotIn("session_id", completed.stdout)

    def test_model_state_rejects_mutating_or_invalid_project_input_without_json(self):
        script = ROOT / "ai/scripts/set_agents_app.py"
        for argv in (("--model-state", "--json", "--update"), ("--model-state", "--json", "--project", "/not/a/project")):
            with self.subTest(argv=argv):
                completed = subprocess.run([sys.executable, str(script), *argv], text=True,
                                           capture_output=True, cwd=ROOT, timeout=10)
                self.assertEqual(2, completed.returncode)
                self.assertEqual("", completed.stdout)
                self.assertIn("model-state", completed.stderr)
