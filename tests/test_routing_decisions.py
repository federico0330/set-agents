"""ADR-0031 — per-spawn routing observability: the decisions sidecar log.

New tests only. The routing store's frozen schema and the ADR-0030 doctrine
suite stay untouched; this file proves the ADDITIVE audit layer: every
`--route-decide` (simulate included) appends one line to `decisions-v1.jsonl`,
the envelope carries the same `decision_id`, the append is best-effort, and
`--routing-decisions` is the read-only query over it.
"""

import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ai/scripts"))

DECISION_ID_RE = re.compile(r"^dec1_[0-9a-f]{32}$")


class RoutingDecisionsLogTests(unittest.TestCase):
    def _probe_stubs(self, td):
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
        return bins

    def _cli_env(self, routing_root, bins=None):
        env = dict(os.environ); env["SET_AGENTS_ROUTING_TEST_ROOT"] = str(routing_root)
        if bins is not None: env["PATH"] = f"{bins}:{env['PATH']}"
        return env

    def _cli_run(self, args, env, input_text=None):
        return subprocess.run([sys.executable, "ai/scripts/set_agents_app.py", *args],
                              cwd=ROOT, text=True, capture_output=True, env=env, input=input_text)

    def _decide_simulate(self, env):
        # docs-rw role ("other" role_class) -> simulate envelope, the exact class of
        # decision that pre-0031 left zero durable trace (store=None).
        descriptor = json.dumps({"role": "product-analyst", "task_class": "documentation",
                                 "selected_runtime": "claude-code"})
        return self._cli_run(["--route-decide", "-", "--json"], env, descriptor)

    def test_a_simulate_decision_appends_one_line_and_the_envelope_carries_its_id(self):
        with tempfile.TemporaryDirectory() as td:
            routing_root = Path(td) / "routing-root"
            env = self._cli_env(routing_root, self._probe_stubs(td))
            result = self._decide_simulate(env)
            self.assertEqual(result.returncode, 0, (result.stdout, result.stderr))
            envelope = json.loads(result.stdout)
            decision_id = envelope["data"]["decision_id"]
            self.assertRegex(decision_id, DECISION_ID_RE)
            lines = (routing_root / "decisions-v1.jsonl").read_text().splitlines()
            self.assertEqual(len(lines), 1)
            entry = json.loads(lines[0])
        self.assertEqual(entry["decision_id"], decision_id)
        self.assertTrue(entry["simulate"])
        self.assertIsNone(entry["run_id"])  # simulate never mints a durable run
        self.assertEqual(entry["role"], "product-analyst")
        self.assertEqual(entry["task_class"], "documentation")
        self.assertIn("model", entry)
        self.assertIn("provider", entry)
        self.assertIn("at", entry)

    def test_the_append_is_best_effort_and_never_breaks_the_envelope(self):
        # The log path exists but is not appendable (a directory squats on it).
        # The one-JSON-line envelope and the exit code must be exactly as without
        # the log; the failure leaves no partial artifacts behind.
        with tempfile.TemporaryDirectory() as td:
            routing_root = Path(td) / "routing-root"
            (routing_root / "decisions-v1.jsonl").mkdir(parents=True)
            env = self._cli_env(routing_root, self._probe_stubs(td))
            result = self._decide_simulate(env)
            self.assertEqual(result.returncode, 0, (result.stdout, result.stderr))
            envelope = json.loads(result.stdout)
            self.assertTrue(envelope["ok"])
            self.assertRegex(envelope["data"]["decision_id"], DECISION_ID_RE)
            self.assertEqual(len(result.stdout.strip().splitlines()), 1)

    def test_routing_decisions_reads_the_tail_and_an_absent_log_is_a_legitimate_zero(self):
        with tempfile.TemporaryDirectory() as td:
            routing_root = Path(td) / "routing-root"
            env = self._cli_env(routing_root, self._probe_stubs(td))
            empty = self._cli_run(["--routing-decisions", "--json"], env)
            self.assertEqual(empty.returncode, 0, (empty.stdout, empty.stderr))
            self.assertEqual(json.loads(empty.stdout)["data"]["decisions"], [])

            first = json.loads(self._decide_simulate(env).stdout)["data"]["decision_id"]
            second = json.loads(self._decide_simulate(env).stdout)["data"]["decision_id"]
            listed = self._cli_run(["--routing-decisions", "--json"], env)
            self.assertEqual(listed.returncode, 0, (listed.stdout, listed.stderr))
            decisions = json.loads(listed.stdout)["data"]["decisions"]
            self.assertEqual([d["decision_id"] for d in decisions], [first, second])

            limited = self._cli_run(["--routing-decisions", "--limit", "1", "--json"], env)
            tail = json.loads(limited.stdout)["data"]["decisions"]
            self.assertEqual([d["decision_id"] for d in tail], [second])

    def test_limit_without_routing_decisions_is_modifier_misuse(self):
        with tempfile.TemporaryDirectory() as td:
            env = self._cli_env(Path(td) / "routing-root")
            result = self._cli_run(["--routing-report", "--limit", "5", "--json"], env)
            self.assertEqual(result.returncode, 2, (result.stdout, result.stderr))
            self.assertIn("ROUTING_INPUT_INVALID", result.stdout)


class DoctrineTests(unittest.TestCase):
    DOCTRINE_FILES = (
        "Global/_canonical/agents/orchestrator.md",
        "Global/claude-code/agents/orchestrator.md",
        "Global/opencode/agents/orchestrator.md",
        "Global/pi/agents/orchestrator.md",
        "Global/codex/agents/orchestrator.toml",
    )

    def test_adr_0031_markers_in_all_five_doctrine_files(self):
        for path in self.DOCTRINE_FILES:
            text = (ROOT / path).read_text()
            self.assertIn("ADR-0031", text, path)
            self.assertIn("--route-id", text, path)


if __name__ == "__main__":
    unittest.main()
