"""Feature 017 PKG-B (ADR-0025) — resolve-first autonomy.

New tests only: coord_policy's sanctioned tool-catalog channel (a dedicated
positional-aware walker, mirroring test_integration_hook.py's approach for the
integration walker), the generated OpenCode permission lines, and the doctrine
markers that make the policy real in all three shared rule files.
"""

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ai/scripts"))

import coord_policy  # noqa: E402

APP = "__SET_AGENTS_ROOT__/ai/scripts/set_agents_app.py"


class ToolsChannelPolicyTests(unittest.TestCase):
    def test_catalog_verbs_are_allowed(self):
        for command in (
            f"python3 {APP} --tools",
            f"python3 {APP} --tools-install vercel --yes",
            f"python3 {APP} --tools-install gh --yes --dry-run",
            f"python3 {APP} --mcp",
            f"python3 {APP} --mcp --harness claude",
            f"python3 {APP} --mcp-add context7 --harness claude",
            f"python3 {APP} --mcp-on playwright --harness claude",
            f"python3 {APP} --mcp-off playwright",
        ):
            self.assertTrue(coord_policy.allowed(command), command)

    def test_everything_outside_the_walker_grammar_is_denied(self):
        for command in (
            # NAME must be a bare catalog key, never a path/option/empty.
            f"python3 {APP} --tools-install ../evil --yes",
            f"python3 {APP} --tools-install --yes",
            f"python3 {APP} --tools-install vercel --yes --update",
            f"python3 {APP} --tools extra",
            f"python3 {APP} --tools-install vercel --yes --yes",
            f"python3 {APP} --mcp-add context7 --harness claude --update",
            f"python3 {APP} --mcp-remove context7",
            # The historical SEC-001 escape shape, transplanted to this channel.
            f"python3 {APP} --tools-install vercel --yes --scaffold /tmp/x",
            # Wrong script entirely.
            "python3 ai/scripts/set_agents_app.py --tools",
        ):
            self.assertFalse(coord_policy.allowed(command), command)

    def test_shell_composition_around_the_channel_is_still_denied(self):
        self.assertFalse(coord_policy.allowed(f"python3 {APP} --tools && rm -rf /"))
        self.assertFalse(coord_policy.allowed(f"python3 {APP} --tools-install vercel --yes | tee /tmp/x"))


class GhReadOnlyChannelTests(unittest.TestCase):
    def test_read_only_gh_inspection_is_allowed(self):
        for command in ("gh run view 12345 --log", "gh run list --limit 5", "gh pr checks 42",
                        "gh pr view 42", "gh workflow list", "gh auth status", "gh repo view"):
            self.assertTrue(coord_policy.allowed(command), command)

    def test_mutating_or_arbitrary_gh_stays_denied(self):
        for command in ("gh api repos/o/r/dispatches", "gh pr merge 42", "gh release create v1",
                        "gh repo delete o/r", "gh run cancel 9", "gh run rerun 9",
                        "gh secret set X", "gh run view 1 | tee /tmp/x"):
            self.assertFalse(coord_policy.allowed(command), command)

    def test_opencode_orchestrator_gh_allows_come_after_the_blanket_deny(self):
        text = (ROOT / "Global/opencode/agents/orchestrator.md").read_text()
        deny = '    "gh *": deny'
        allow = '    "gh run view*": allow'
        self.assertIn(deny, text)
        self.assertIn(allow, text)
        # Last-match-wins: the specific allow must come after the blanket deny.
        self.assertLess(text.index(deny), text.index(allow))


class GeneratedPermissionTests(unittest.TestCase):
    def test_opencode_orchestrator_gains_the_tools_channel(self):
        text = (ROOT / "Global/opencode/agents/orchestrator.md").read_text()
        allow_tools = f'    "python3 {APP} --tools*": allow'
        allow_mcp = f'    "python3 {APP} --mcp*": allow'
        deny_remove = f'    "python3 {APP} --mcp-remove*": deny'
        for line in (allow_tools, allow_mcp, deny_remove):
            self.assertIn(line, text)
        # Last-match-wins list convention: the deny must come after the allow it narrows.
        self.assertLess(text.index(allow_mcp), text.index(deny_remove))


class DoctrineMarkerTests(unittest.TestCase):
    def test_resolve_first_and_named_platform_carveout_are_in_the_shared_rules(self):
        for path in ("Global/_shared/CLAUDE.md", "Global/_shared/AGENTS.opencode.md",
                     "Global/_shared/AGENTS.pi.md"):
            text = (ROOT / path).read_text()
            self.assertIn("Resolve-first (ADR-0025)", text, path)
            self.assertIn("ADR-0025", text, path)
        canonical = (ROOT / "Global/_canonical/agents/orchestrator.md").read_text()
        self.assertIn("Named-platform carve-out (ADR-0025)", canonical)
        self.assertIn("## Tool catalog — resolve first, record always (ADR-0025)", canonical)

    def test_mcp_discipline_no_longer_asks_for_the_managed_catalog(self):
        for path in ("Global/_shared/CLAUDE.md", "Global/_shared/AGENTS.opencode.md",
                     "Global/_shared/AGENTS.pi.md"):
            text = (ROOT / path).read_text()
            self.assertIn("WITHOUT asking", text, path)


if __name__ == "__main__":
    unittest.main()
