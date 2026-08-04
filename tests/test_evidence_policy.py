"""Feature 017 PKG-C (ADR-0026) — evidence over memory.

New tests only: the web-tools grant for analysis roles in both generated lanes,
the transversal evidence rule in the three shared doctrine files, the new
spawn-prompt skill, and the least-privilege boundary (mechanical roles never
gain the web).
"""

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

ANALYSIS = ("architect", "brainstormer", "package-reviewer", "security-auditor",
            "debugger", "product-analyst")
MECHANICAL = ("gate-runner", "local-gate-runner", "implementer", "integrator")


class ClaudeWebToolsTests(unittest.TestCase):
    def _tools_line(self, role):
        text = (ROOT / f"Global/claude-code/agents/{role}.md").read_text()
        match = re.search(r"(?m)^tools: (.+)$", text)
        self.assertIsNotNone(match, role)
        return match.group(1)

    def test_analysis_roles_have_web_tools(self):
        for role in ANALYSIS:
            line = self._tools_line(role)
            self.assertIn("WebSearch", line, role)
            self.assertIn("WebFetch", line, role)

    def test_mechanical_roles_never_gain_web_tools(self):
        for role in MECHANICAL:
            line = self._tools_line(role)
            self.assertNotIn("WebSearch", line, role)
            self.assertNotIn("WebFetch", line, role)


class OpenCodeWebToolsTests(unittest.TestCase):
    def test_analysis_roles_allow_webfetch(self):
        for role in ANALYSIS:
            text = (ROOT / f"Global/opencode/agents/{role}.md").read_text()
            self.assertIn("webfetch: allow", text, role)
            self.assertIn("websearch: allow", text, role)

    def test_gate_runner_does_not_allow_webfetch(self):
        text = (ROOT / "Global/opencode/agents/local-gate-runner.md").read_text()
        self.assertIn("webfetch: deny", text)


class DoctrineTests(unittest.TestCase):
    def test_evidence_rule_present_in_all_shared_doctrine(self):
        for path in ("Global/_shared/CLAUDE.md", "Global/_shared/AGENTS.opencode.md",
                     "Global/_shared/AGENTS.pi.md"):
            text = (ROOT / path).read_text()
            self.assertIn("## Evidence over memory (ADR-0026)", text, path)
            self.assertIn("sin verificar", text, path)

    def test_brainstormer_has_evidence_section(self):
        text = (ROOT / "Global/_canonical/agents/brainstormer.md").read_text()
        self.assertIn("## Evidence (ADR-0026", text)
        self.assertIn("file:line", text)

    def test_consult_mode_demands_claims_evidence_table(self):
        orchestrator = (ROOT / "Global/_canonical/agents/orchestrator.md").read_text()
        self.assertIn("claims→evidence", orchestrator)
        consult = (ROOT / "Global/_canonical/commands/consult.md").read_text()
        self.assertIn("claims→evidence", consult)

    def test_spawn_prompt_skill_exists_and_is_referenced(self):
        skill = (ROOT / "Global/_canonical/skills/spawn-prompt/SKILL.md").read_text()
        for section in ("CONTEXTO", "TAREA", "EVIDENCIA EXIGIDA", "FORMATO DE SALIDA",
                        "FUERA DE ALCANCE", "PRESUPUESTO"):
            self.assertIn(section, skill)
        orchestrator = (ROOT / "Global/_canonical/agents/orchestrator.md").read_text()
        self.assertIn("`spawn-prompt` skill", orchestrator)
        # Propagated to the generated trees by build.sh:
        self.assertTrue((ROOT / "Global/claude-code/skills/spawn-prompt/SKILL.md").exists())
        self.assertTrue((ROOT / "Global/opencode/skills/spawn-prompt/SKILL.md").exists())


if __name__ == "__main__":
    unittest.main()
