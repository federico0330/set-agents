"""049 PKG-D2 / AC-09 — integrated regressions across CLI, help and model identity."""

import io
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "ai/scripts/set_agents_app.py"
sys.path.insert(0, str(ROOT / "ai/scripts"))


def _run_cli(*argv, env=None, timeout=15):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *argv],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=timeout,
        env={**os.environ, **(env or {})},
    )


def _tree_bytes(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def _astra_luna_runner(project: Path, *, first="opaque/astra", last="opaque/luna"):
    """Simulate a session that moved from Astra to Luna via /model (last user wins)."""
    provider_a, model_a = first.split("/", 1)
    provider_l, model_l = last.split("/", 1)
    canonical = str(project.resolve())
    sessions = [{
        "id": "root-private-id",
        "directory": canonical,
        "parentID": None,
        "time": {"updated": 1_770_000_002_000},
    }]
    export = {
        "info": {"id": "root-private-id"},
        "messages": [
            {
                "info": {
                    "id": "msg-astra-private",
                    "role": "user",
                    "time": {"created": 1_770_000_010_000},
                    "model": {"providerID": provider_a, "modelID": model_a},
                },
                "parts": [{"text": "secret astra prompt"}],
            },
            {
                "info": {
                    "id": "msg-luna-private",
                    "role": "user",
                    "time": {"created": 1_770_000_020_000},
                    "model": {"providerID": provider_l, "modelID": model_l},
                },
                "parts": [{"text": "secret luna prompt"}],
            },
        ],
    }

    def runner(command, **kwargs):
        if command[1:3] == ["session", "list"]:
            return 0, json.dumps(sessions)
        return 0, json.dumps(export)

    return runner


class SessionIdentityIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.state = Path(self.temporary.name) / "state"
        self.home = Path(self.temporary.name) / "home"
        self.state.mkdir()
        self.home.mkdir()
        self.env = {"SET_AGENTS_STATE": str(self.state), "HOME": str(self.home)}
        overlay = self.home / ".local/state/set-agentes/models.local.toml"
        overlay.parent.mkdir(parents=True, exist_ok=True)
        overlay.write_text('[areas.coord]\nopencode = "opaque/terra"\n', encoding="utf-8")
        installed = self.home / ".config/opencode/agents/orchestrator.md"
        installed.parent.mkdir(parents=True)
        installed.write_text('---\nmodel: opaque/terra\n---\n', encoding="utf-8")

    def test_session_astra_to_luna_surfaces_last_sent_while_terra_default_stays_neutral(self):
        import model_state

        runner = _astra_luna_runner(ROOT)
        state = model_state.collect_model_state(ROOT, home=self.home, project=ROOT, runner=runner)
        rendered = json.dumps(state, ensure_ascii=False)

        self.assertEqual("opaque/luna", state["observed"]["model"])
        self.assertEqual("observed", state["observed"]["status"])
        self.assertEqual("opaque/terra", state["desired"]["model"])
        self.assertEqual("set-effective-config", state["desired"]["source"])

        human = model_state.render_human(state)
        self.assertIn("Último envío observado", human)
        self.assertIn("opaque/luna", human)
        self.assertIn("Default de SET", human)
        self.assertIn("opaque/terra", human)
        for private in ("root-private-id", "msg-astra-private", "msg-luna-private",
                        "secret astra prompt", "secret luna prompt", "session_id"):
            self.assertNotIn(private, rendered)
            self.assertNotIn(private, human)

    def test_session_observation_does_not_mutate_set_overlay_or_install_artifacts(self):
        import model_state

        before_overlay = (self.home / ".local/state/set-agentes/models.local.toml").read_bytes()
        before_installed = (self.home / ".config/opencode/agents/orchestrator.md").read_bytes()
        before_tree = _tree_bytes(self.state) | _tree_bytes(self.home)

        state = model_state.collect_model_state(
            ROOT, home=self.home, project=ROOT, runner=_astra_luna_runner(ROOT),
        )

        self.assertEqual("opaque/luna", state["observed"]["model"])
        self.assertEqual(
            before_overlay,
            (self.home / ".local/state/set-agentes/models.local.toml").read_bytes(),
        )
        self.assertEqual(
            before_installed,
            (self.home / ".config/opencode/agents/orchestrator.md").read_bytes(),
        )
        self.assertEqual(before_tree, _tree_bytes(self.state) | _tree_bytes(self.home))


class HelpIntegrationTests(unittest.TestCase):
    def test_default_help_stays_human_without_internal_flags(self):
        completed = _run_cli("--help")
        self.assertEqual(0, completed.returncode, completed.stderr)
        help_text = completed.stdout + completed.stderr
        self.assertIn("estado de sesión", help_text.lower())
        self.assertIn("--model-state", help_text)
        self.assertNotIn("--route-decide", help_text)
        self.assertNotIn("USO INTERNO", help_text)

    def test_help_avanzado_keeps_engineering_detail(self):
        for argv in (("--help", "--avanzado"), ("--avanzado", "--help")):
            with self.subTest(argv=argv):
                completed = _run_cli(*argv)
                self.assertEqual(0, completed.returncode, completed.stderr)
                help_text = completed.stdout
                self.assertIn("--route-decide", help_text)
                self.assertIn("USO INTERNO", help_text)
                self.assertIn("--model-state", help_text)

    def test_parser_level_human_vs_advanced_split(self):
        import set_agents_app as app

        default_help = app._build_parser(advanced=False).format_help()
        advanced_help = app._build_parser(advanced=True).format_help()
        self.assertIn("--model-state", default_help)
        self.assertNotIn("--route-decide", default_help)
        self.assertIn("--route-decide", advanced_help)


class ModelStateArgvIntegrationTests(unittest.TestCase):
    def test_invalid_model_state_argv_exits_two_without_partial_json(self):
        cases = (
            ("--model-state", "--json", "--update"),
            ("--model-state", "--json", "--project", "/not/a/project"),
            ("--model-state", "--json", "--route-decide", "task.json"),
        )
        for argv in cases:
            with self.subTest(argv=argv):
                completed = _run_cli(*argv)
                self.assertEqual(2, completed.returncode)
                self.assertEqual("", completed.stdout.strip())
                self.assertIn("model-state", completed.stderr.lower())
                self.assertFalse(completed.stdout.strip().startswith("{"))

    def test_valid_model_state_json_is_single_schema_object(self):
        completed = _run_cli("--model-state", "--json", "--project", str(ROOT), env={"PATH": ""})
        self.assertEqual(0, completed.returncode, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertEqual(1, payload["schema_version"])
        self.assertEqual("orchestrator", payload["scope"]["role"])
        self.assertNotIn("session_id", completed.stdout)


class CliMainHelpSmokeTests(unittest.TestCase):
    def test_main_intercepts_avanzado_help_without_system_exit(self):
        import set_agents_app as app

        for argv in (["set_agents_app.py", "--help", "--avanzado"],
                     ["set_agents_app.py", "--avanzado", "--help"]):
            with self.subTest(argv=argv):
                buf = io.StringIO()
                with mock.patch("sys.argv", argv), mock.patch("sys.stdout", buf):
                    self.assertEqual(0, app.main())
                self.assertIn("--route-decide", buf.getvalue())

    def test_main_default_help_hides_internal_flags(self):
        import set_agents_app as app

        buf = io.StringIO()
        with mock.patch("sys.argv", ["set_agents_app.py", "--help"]), mock.patch("sys.stdout", buf):
            with self.assertRaises(SystemExit):
                app.main()
        self.assertNotIn("--route-decide", buf.getvalue())
        self.assertTrue(re.search(r"--model-state\b", buf.getvalue()))


if __name__ == "__main__":
    unittest.main()
