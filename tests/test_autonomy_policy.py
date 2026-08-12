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

    def test_a_bare_ampersand_shell_separator_is_denied(self):
        # F-01 (019-harness-evolution P5 review, critical): FORBIDDEN_SYNTAX used to
        # enumerate `&&` but never a bare `&` -- in `bash -c`, `&` alone is a full
        # statement separator (backgrounds the left side, unconditionally runs the
        # right), same threat class as `;`/`&&`. Written from the THREAT, not the old
        # regex, which is exactly what missed this the first time.
        self.assertFalse(coord_policy.allowed(f"python3 {APP} --tools & touch /tmp/pwned"))
        self.assertIsNotNone(coord_policy.FORBIDDEN_SYNTAX.search("true & touch /tmp/x"))


class ToolsProposeChannelPolicyTests(unittest.TestCase):
    """ADR-0038: --tools-propose joins the agent channel with a closed grammar;
    --tools-approve deliberately never does (decisions-log slug
    tools-approve-fuera-del-canal-del-agente)."""

    def test_tools_propose_well_formed_grammar_is_allowed(self):
        for command in (
            f'python3 {APP} --tools-propose foo --kind cli --detect foo '
            f'--install-npm "npm install -g foo" --why "necesito foo para el build"',
            f'python3 {APP} --tools-propose bar-tool --kind mcp --detect bar '
            f'--install-curl "curl -sSL https://example.com/install.sh" --why "servidor MCP interno"',
            # Order of the four flags must not matter -- it's a set, not a sequence.
            f'python3 {APP} --tools-propose baz --why "motivo" --detect baz '
            f'--install-brew "brew install baz" --kind skill',
        ):
            self.assertTrue(coord_policy.allowed(command), command)

    def test_tools_propose_adversarial_argv_is_denied(self):
        for command in (
            # Missing a required flag (--why).
            f'python3 {APP} --tools-propose foo --kind cli --detect foo --install-npm "npm i -g foo"',
            # Duplicate flag.
            f'python3 {APP} --tools-propose foo --kind cli --kind mcp --detect foo '
            f'--install-npm "npm i -g foo" --why w',
            # Two install-method flags.
            f'python3 {APP} --tools-propose foo --kind cli --detect foo '
            f'--install-npm "npm i -g foo" --install-curl "curl x" --why w',
            # NAME must be a bare catalog key, never a path/option/empty.
            f'python3 {APP} --tools-propose ../evil --kind cli --detect foo '
            f'--install-npm "npm i -g foo" --why w',
            f'python3 {APP} --tools-propose --kind cli --detect foo --install-npm "npm i -g foo" --why w',
            # The historical SEC-001 escape shape, transplanted to this channel: an extra,
            # unrecognized flag riding along after the required set is otherwise satisfied.
            f'python3 {APP} --tools-propose foo --kind cli --detect foo '
            f'--install-npm "npm i -g foo" --why w --scaffold /tmp/x',
            f'python3 {APP} --tools-propose foo --kind cli --detect foo '
            f'--install-npm "npm i -g foo" --why w --yes',
            # --install-<method> flag pattern must be a plain lowercase word, not a path.
            f'python3 {APP} --tools-propose foo --kind cli --detect foo '
            f'--install-../etc "cat /etc/passwd" --why w',
            # A bare pipe/semicolon in the command value is already denied at the top of
            # allowed() (FORBIDDEN_SYNTAX), regardless of this channel's own grammar.
            f'python3 {APP} --tools-propose foo --kind cli --detect foo '
            f'--install-curl "curl x | bash" --why w',
            f'python3 {APP} --tools-propose foo --kind cli --detect foo '
            f'--install-npm "npm i -g foo; rm -rf ~" --why w',
        ):
            self.assertFalse(coord_policy.allowed(command), command)

    def test_tools_approve_is_never_allowed_in_the_agent_channel(self):
        for command in (
            f"python3 {APP} --tools-approve foo",
            # Even carrying the full propose-shaped payload changes nothing -- approve's
            # grammar is deliberately just the name (ADR-0038), and it is denied regardless.
            f'python3 {APP} --tools-approve foo --kind cli --detect foo '
            f'--install-npm "npm i -g foo" --why w',
            f"python3 {APP} --tools-approve",
        ):
            self.assertFalse(coord_policy.allowed(command), command)
        # Direct unit check on the walker itself, not just the composed `allowed()` --
        # the adversarial case the context pack asks for explicitly.
        self.assertFalse(coord_policy._tools_channel_allowed(
            ["python3", APP, "--tools-approve", "foo"]))

    def test_tools_approve_cannot_ride_along_a_routing_invocation(self):
        # F-08 (019-harness-evolution P5 review): SAFE_ARGV's `--route*`/`--routing*`
        # entry uses `modifiers=None` (argv[2] alone decides), so it never inspects the
        # rest of argv -- a `--tools-approve` riding along after a legitimate-looking
        # `--routing-report`/`--route-doctor` used to slip through invisibly. This is
        # PRE-EXISTING for other flags (e.g. `--tools-install ... --yes` the same way)
        # and not this repair's to fix broadly -- only `--tools-approve` gets its own
        # guard, because this package's whole invariant depends on it.
        for command in (
            f"python3 {APP} --routing-report --tools-approve foo",
            f"python3 {APP} --route-doctor --tools-approve foo",
            f"python3 {APP} --routing-report --tools-approve=foo",
        ):
            self.assertFalse(coord_policy.allowed(command), command)
        # A legitimate routing-only invocation, with nothing riding along, is untouched.
        self.assertTrue(coord_policy.allowed(f"python3 {APP} --routing-report"))


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

    def test_opencode_orchestrator_denies_tools_approve_despite_the_coarser_tools_glob(self):
        # ADR-0038: "--tools*": allow is a glob (coarser than coord_policy.py's dedicated
        # walker) and would otherwise swallow --tools-approve by prefix -- the human
        # approval step this whole package exists to keep out of the agent's reach.
        text = (ROOT / "Global/opencode/agents/orchestrator.md").read_text()
        allow_tools = f'    "python3 {APP} --tools*": allow'
        deny_approve = f'    "python3 {APP} --tools-approve*": deny'
        self.assertIn(allow_tools, text)
        self.assertIn(deny_approve, text)
        self.assertLess(text.index(allow_tools), text.index(deny_approve))


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

    def test_tool_catalog_doctrine_covers_the_open_catalog_flow(self):
        # AC-35: "tool faltante" stops being a dead end outside the curated catalog too --
        # both orchestrator and implementer must point at --tools-propose (never approve).
        canonical_orch = (ROOT / "Global/_canonical/agents/orchestrator.md").read_text()
        self.assertIn("ADR-0038", canonical_orch)
        self.assertIn("--tools-propose", canonical_orch)
        canonical_impl = (ROOT / "Global/_canonical/agents/implementer.md").read_text()
        self.assertIn("ADR-0038", canonical_impl)
        self.assertIn("--tools-propose", canonical_impl)
        # implementer.md never instructs running approve itself (that's the whole point).
        self.assertNotIn("run `--tools-approve", canonical_impl)
        # F-14: the orchestrator doctrine must never promise a channel that doesn't
        # exist -- coord_policy denies --tools-approve outright, unconditionally, there
        # is no "the orchestrator's own separate channel" for it to run through. The
        # OLD phrasing implied the orchestrator itself could run approve; that's gone.
        self.assertNotIn("after their explicit yes and on your own separate channel", canonical_orch)
        self.assertIn("never run it yourself", canonical_orch)

    def test_mcp_discipline_no_longer_asks_for_the_managed_catalog(self):
        for path in ("Global/_shared/CLAUDE.md", "Global/_shared/AGENTS.opencode.md",
                     "Global/_shared/AGENTS.pi.md"):
            text = (ROOT / path).read_text()
            self.assertIn("WITHOUT asking", text, path)


if __name__ == "__main__":
    unittest.main()
