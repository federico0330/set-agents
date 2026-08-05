"""ADR-0030 — decide siempre: una decisión de routing por spawn, 28/28 roles.

New tests only. The immutable suite keeps pinning the six-role tiered roster
and the tiered-sentence regex; this file proves the ADDITIVE layer: the
decide-always doctrine markers, the router serving a non-tiered role, and the
wizard's fallback re-label.
"""

import json
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ai/scripts"))

DOCTRINE_FILES = (
    "Global/_canonical/agents/orchestrator.md",
    "Global/claude-code/agents/orchestrator.md",
    "Global/opencode/agents/orchestrator.md",
    "Global/codex/agents/orchestrator.toml",
)

# Local copy (never imported from the immutable suite): the six-name tiered
# sentence must survive the decide-always addition in all four doctrine files.
TIERED_SENTENCE_RE = re.compile(
    r"`implementer`, `debugger`, `package-reviewer`, `delta-reviewer`, `security-auditor`, and\s+"
    r"`finding-verifier` are \*\*tiered roles\*\*"
)


class DoctrineTests(unittest.TestCase):
    def test_decide_always_markers_in_all_four_doctrine_files(self):
        for path in DOCTRINE_FILES:
            text = (ROOT / path).read_text()
            self.assertIn("ADR-0030", text, path)
            self.assertIn("MODEL_STATIC_FALLBACK", text, path)

    def test_the_immutable_tiered_sentence_survived(self):
        for path in DOCTRINE_FILES:
            self.assertTrue(TIERED_SENTENCE_RE.search((ROOT / path).read_text()), path)

    def test_simulate_never_authorizes_durable_runs(self):
        canonical = (ROOT / DOCTRINE_FILES[0]).read_text()
        self.assertIn("Never fabricate enforcement", canonical)


class NonTieredDecisionTests(unittest.TestCase):
    def test_route_decide_serves_a_non_tiered_role(self):
        # architect has no [roles.architect.tiers.*] table; ADR-0030's premise is
        # that the router still returns a full decision envelope for it. Exit 0
        # (decided) and 1 (facts/degrade) are both live-machine-dependent OKs;
        # only the envelope shape is the contract here.
        descriptor = json.dumps({"role": "architect", "task_class": "architecture"})
        result = subprocess.run(
            [sys.executable, "ai/scripts/set_agents_app.py", "--route-decide", "-", "--json"],
            cwd=ROOT, input=descriptor, text=True, capture_output=True, timeout=300,
        )
        self.assertIn(result.returncode, (0, 1), result.stdout + result.stderr)
        envelope = json.loads(result.stdout.strip().splitlines()[-1])
        self.assertEqual(envelope["command"], "route-decide")
        if envelope.get("ok"):
            self.assertIn("model", envelope["data"])
            self.assertIn("provider", envelope["data"])


class PanelRelabelTests(unittest.TestCase):
    def test_panel_names_the_table_as_curated_fallback(self):
        import setup_models
        config = {"areas": {}, "roles": {"debugger": {"tiers": {}}}, "subscriptions": {}}
        text = "\n".join(setup_models._panel_lines(config, [], "go-zen"))
        self.assertIn("DEFAULTS CURADOS", text)
        self.assertIn("ADR-0030", text)
        self.assertIn("variantes @tier: 1", text)


if __name__ == "__main__":
    unittest.main()
