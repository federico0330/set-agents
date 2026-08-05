"""ADR-0030 effort extension — the decision's effort rides pi's --thinking.

New tests only: spawn() argv composition (closed level set, advisory — never
fails a spawn), and route_and_spawn threading `data.effort` through.
"""

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ai/scripts"))

import set_agents_spawn as sas  # noqa: E402


class _Proc:
    def __init__(self, stdout="", returncode=0):
        self.stdout = stdout
        self.stderr = ""
        self.returncode = returncode


class SpawnThinkingFlagTests(unittest.TestCase):
    def _argv_for(self, effort):
        captured = {}

        def fake_run(argv, **kwargs):
            captured["argv"] = list(argv)
            return _Proc(stdout="", returncode=1)  # crash path: argv already composed

        with tempfile.NamedTemporaryFile("w", suffix=".md") as prompt:
            with mock.patch.object(sas.subprocess, "run", side_effect=fake_run):
                sas.spawn("architect", "do the thing", "openai-codex", "gpt-5.6-sol",
                          prompt.name, effort=effort)
        return captured["argv"]

    def test_valid_effort_becomes_thinking_flag(self):
        argv = self._argv_for("high")
        index = argv.index("--thinking")
        self.assertEqual(argv[index + 1], "high")
        # Composed with the model, before the untrusted task (last positional).
        self.assertLess(argv.index("--model"), index)

    def test_absent_effort_omits_the_flag(self):
        self.assertNotIn("--thinking", self._argv_for(None))

    def test_unknown_effort_is_dropped_never_fatal(self):
        argv = self._argv_for("turbo-9000")
        self.assertNotIn("--thinking", argv)
        self.assertNotIn("turbo-9000", argv)

    def test_every_route_effort_level_is_a_valid_pi_level(self):
        # routes.v1.toml/codex_effort universe ⊆ pi --thinking levels (pi --help, 0.81.1).
        for effort in ("low", "medium", "high", "xhigh"):
            self.assertIn(effort, sas._PI_THINKING_LEVELS)


class RouteAndSpawnEffortTests(unittest.TestCase):
    def test_decision_effort_reaches_spawn(self):
        decide_envelope = json.dumps({
            "ok": True, "command": "route-decide", "schema_version": 2, "reason_codes": [],
            "data": {"execution_enabled": True, "run_id": "run_x", "provider": "openai-codex",
                     "model": "gpt-5.6-sol", "effort": "xhigh"},
        })

        def fake_cli(args, env=None, cwd=None):
            if args[0] == "--route-decide":
                return _Proc(stdout=decide_envelope)
            return _Proc(stdout=json.dumps({"ok": True, "data": {}}))

        with mock.patch.object(sas, "_run_app_cli", side_effect=fake_cli), \
             mock.patch.object(sas, "spawn", return_value=("success", {})) as spawned:
            result = sas.route_and_spawn("architect", "architecture", "task text")
        self.assertEqual(result["status"], "success")
        self.assertEqual(spawned.call_args.kwargs["effort"], "xhigh")


if __name__ == "__main__":
    unittest.main()
