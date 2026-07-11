import json
import os
import subprocess
import tempfile
import time
import tomllib
import unittest
import filecmp
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(*args, env=None, check=True):
    return subprocess.run(
        args,
        cwd=ROOT,
        env={**os.environ, **(env or {})},
        text=True,
        capture_output=True,
        check=check,
    )


class HarnessTests(unittest.TestCase):
    def test_check_and_native_codex_agents(self):
        run("./build.sh", "--check")
        run("./build.sh")
        agents = sorted((ROOT / "Global/codex/agents").glob("*.toml"))
        self.assertGreaterEqual(len(agents), 21)
        for path in agents:
            data = tomllib.loads(path.read_text())
            self.assertEqual(data["name"], path.stem)
            self.assertIn(data["sandbox_mode"], {"read-only", "workspace-write"})
            self.assertTrue(data["developer_instructions"].strip())

    def test_coordinator_policy(self):
        allowed = [
            "git status --short", "git diff --stat", "dotnet --list-sdks",
            "node --version", "npm ls --depth=0", "python --version",
            "pip list", "go version", "rustup toolchain list", "opencode models",
        ]
        denied = [
            "echo x > file", "printf x | tee file", "sed -i s/a/b/ file",
            "npm install x", "git add .", "git commit -m x", "git push",
            "gh pr create", "./ai/scripts/mcp.sh on", "./ai/scripts/loop.sh",
            "git diff --output=changed.patch", "rg --pre 'touch owned' pattern", "fd -x touch owned",
            "node --version -e 'require(\"fs\").writeFileSync(\"x\",\"y\")'",
            "git diff --stat>owned", "git diff --stat|tee owned", "git diff --stat&&git status",
        ]
        for command in allowed:
            self.assertEqual(run("python3", "ai/scripts/coord_policy.py", command, check=False).returncode, 0, command)
        for command in denied:
            self.assertEqual(run("python3", "ai/scripts/coord_policy.py", command, check=False).returncode, 2, command)

    def test_profile_switch_does_not_rewrite_roster(self):
        before = (ROOT / "roles.tsv").read_bytes()
        with tempfile.TemporaryDirectory() as td:
            run("./build.sh", "--profile", "zen", "--output", td)
        self.assertEqual(before, (ROOT / "roles.tsv").read_bytes())

    def test_local_profile_generates_and_validates(self):
        # The `local` profile (leaf agents on Ollama, judgment roles hosted) must
        # generate and pass separation-of-duties just like go-zen/zen.
        with tempfile.TemporaryDirectory() as td:
            result = run("python3", "ai/scripts/generate.py", "--profile", "local",
                         "--output", str(Path(td) / "out"), check=False)
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_invalid_separation_graph_is_rejected(self):
        roster = (ROOT / "roles.tsv").read_text().replace(
            "adversarial-judge\tsubagent\t0.0\treview-ro\tjudge\topenai/gpt-5.6-sol",
            "adversarial-judge\tsubagent\t0.0\treview-ro\tjudge\topencode-go/kimi-k2.7-code",
        )
        with tempfile.TemporaryDirectory() as td:
            roles = Path(td) / "roles.tsv"
            roles.write_text(roster)
            result = run("python3", "ai/scripts/generate.py", "--profile", "go-zen", "--output", str(Path(td) / "out"), "--roles", str(roles), check=False)
        self.assertEqual(result.returncode, 2)
        self.assertIn("separation violation", result.stderr)

        mutating_auditor = (ROOT / "roles.tsv").read_text().replace("auditor\tsubagent\t0.0\treview-ro\taudit", "auditor\tsubagent\t0.0\tcode-rw\taudit")
        with tempfile.TemporaryDirectory() as td:
            roles = Path(td) / "roles.tsv"
            roles.write_text(mutating_auditor)
            result = run("python3", "ai/scripts/generate.py", "--profile", "go-zen", "--output", str(Path(td) / "out"), "--roles", str(roles), check=False)
        self.assertEqual(result.returncode, 2)
        self.assertIn("mutating capability", result.stderr)

        family_overlap = (ROOT / "roles.tsv").read_text().replace("auditor\tsubagent\t0.0\treview-ro\taudit\topencode-go/minimax-m3\topenai/gpt-5.5\topenai/gpt-5.5\topus\tgpt-5.6-sol", "auditor\tsubagent\t0.0\treview-ro\taudit\topencode-go/minimax-m3\topenai/gpt-5.5\topenai/gpt-5.5\topus\tgpt-5.6-terra")
        with tempfile.TemporaryDirectory() as td:
            roles = Path(td) / "roles.tsv"
            roles.write_text(family_overlap)
            result = run("python3", "ai/scripts/generate.py", "--profile", "go-zen", "--output", str(Path(td) / "out"), "--roles", str(roles), check=False)
        self.assertEqual(result.returncode, 2)
        self.assertIn("gpt-5.6-terra", result.stderr)

    def test_generated_mcp_is_off(self):
        run("./build.sh")
        data = json.loads((ROOT / "Global/opencode/opencode.json").read_text())
        self.assertTrue(data["mcp"])
        self.assertTrue(all(not item["enabled"] for item in data["mcp"].values()))
        overlay = json.loads((ROOT / "Global/claude-code/settings.overlay.json").read_text())
        self.assertFalse(overlay["enabledPlugins"]["engram@engram"])

    def test_release_gate_requires_two_confirmations(self):
        base = {"verify": "pass", "audits": "pass", "judge": "JUDGE_PASS", "surfaces": [], "audits_ran": ["auditor"]}
        with tempfile.TemporaryDirectory() as td:
            state = Path(td) / "state.json"
            state.write_text(json.dumps(base))
            self.assertEqual(run("python3", "ai/scripts/release_gate.py", str(state), "commit", check=False).returncode, 0)
            self.assertEqual(run("python3", "ai/scripts/release_gate.py", str(state), "publish", check=False).returncode, 2)
            state.write_text(json.dumps({**base, "publish_confirmed": True}))
            self.assertEqual(run("python3", "ai/scripts/release_gate.py", str(state), "publish", check=False).returncode, 0)
            self.assertEqual(run("python3", "ai/scripts/release_gate.py", str(state), "merge", check=False).returncode, 2)
            state.write_text(json.dumps({**base, "publish_confirmed": True, "remote_checks": "pass", "merge_confirmed": True}))
            self.assertEqual(run("python3", "ai/scripts/release_gate.py", str(state), "merge", check=False).returncode, 0)

    def test_release_requires_audit_coverage(self):
        green = {"verify": "pass", "audits": "pass", "judge": "JUDGE_PASS"}
        with tempfile.TemporaryDirectory() as td:
            state = Path(td) / "state.json"
            # green gates but no surface coverage declared → blocked
            state.write_text(json.dumps(green))
            self.assertEqual(run("python3", "ai/scripts/release_gate.py", str(state), "commit", check=False).returncode, 2)
            # auth surface without its mandatory auditors → blocked, names the missing auditor
            state.write_text(json.dumps({**green, "surfaces": ["auth"], "audits_ran": ["auditor"]}))
            blocked = run("python3", "ai/scripts/release_gate.py", str(state), "commit", check=False)
            self.assertEqual(blocked.returncode, 2)
            self.assertIn("security-auditor", blocked.stderr)
            # auth surface WITH the mandatory auditors recorded → allowed
            state.write_text(json.dumps({**green, "surfaces": ["auth"],
                                         "audits_ran": ["auditor", "security-auditor", "red-team"]}))
            self.assertEqual(run("python3", "ai/scripts/release_gate.py", str(state), "commit", check=False).returncode, 0)

    def test_release_action_blocks_destructive_publishes(self):
        base = {"verify": "pass", "audits": "pass", "judge": "JUDGE_PASS", "publish_confirmed": True,
                "surfaces": [], "audits_ran": ["auditor"]}
        with tempfile.TemporaryDirectory() as td:
            state = Path(td) / "state.json"
            state.write_text(json.dumps(base))
            blocked = [
                ["git", "push", "--mirror", "origin", "main"],
                ["git", "push", "--delete", "origin", "main"],
                ["git", "push", "origin", ":main"],
                ["git", "push", "origin", "main", ";", "touch", "owned"],
            ]
            for command in blocked:
                result = run("python3", "ai/scripts/release_action.py", str(state), "publish", "--", *command, check=False)
                self.assertNotEqual(result.returncode, 0, command)
                self.assertTrue(
                    any(marker in (result.stderr + result.stdout).lower() for marker in ("blocked", "plain branch push", "unsafe")),
                    command,
                )

    def test_claude_release_guard_blocks_shell_syntax(self):
        payload = json.dumps({"tool_input": {"command": "python3 ~/.claude/hooks/release_action.py state publish -- git push origin main ; touch owned"}})
        blocked = subprocess.run(["python3", "ai/scripts/claude_release_guard.py"], input=payload, text=True, capture_output=True)
        self.assertEqual(blocked.returncode, 2)
        self.assertIn("blocked", blocked.stderr.lower())

    def test_release_harnesses_require_gated_wrapper(self):
        run("./build.sh")
        oc = (ROOT / "Global/opencode/agents/github-release-manager.md").read_text()
        claude = (ROOT / "Global/claude-code/agents/github-release-manager.md").read_text()
        codex = tomllib.loads((ROOT / "Global/codex/agents/github-release-manager.toml").read_text())
        self.assertIn('"git commit*": deny', oc)
        self.assertIn("release_action.py", oc)
        self.assertIn("claude_release_guard.py", claude)
        self.assertEqual(codex["sandbox_mode"], "read-only")
        self.assertIn("read-only", codex["developer_instructions"])
        payload = json.dumps({"tool_input": {"command": "git push origin main"}})
        blocked = subprocess.run(["python3", "ai/scripts/claude_release_guard.py"], input=payload, text=True, capture_output=True)
        self.assertEqual(blocked.returncode, 2)

    def test_legacy_codex_prompts_are_not_deleted_if_customized(self):
        with tempfile.TemporaryDirectory() as home, tempfile.TemporaryDirectory() as staging_dir:
            home_path = Path(home)
            legacy = home_path / ".codex/prompts/orchestrator.md"
            legacy.parent.mkdir(parents=True, exist_ok=True)
            legacy.write_text("custom legacy prompt\n")
            run("./build.sh", "--output", staging_dir)
            result = run("python3", "ai/scripts/install.py", "--staging", staging_dir, "--home", home)
            self.assertEqual(legacy.read_text(), "custom legacy prompt\n")
            self.assertIn("LEGACY_CONFLICTS=.codex/prompts/orchestrator.md", result.stdout)

    def test_memory_fallback_does_not_block(self):
        with tempfile.TemporaryDirectory() as td:
            log = Path(td) / "memory.md"
            start = time.monotonic()
            run("python3", "ai/scripts/save_memory.py", "verified fix", "--log", str(log), "--engram-command", "sleep 5", "--timeout", "0.1")
            self.assertLess(time.monotonic() - start, 2)
            self.assertIn("verified fix", log.read_text())

    def test_bootstrap_preserves_existing_content_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as td:
            target = Path(td)
            existing = target / "AGENTS.md"
            existing.write_text("custom rules\n")
            first = run("python3", "ai/scripts/bootstrap_project.py", td)
            self.assertEqual(existing.read_text(), "custom rules\n")
            self.assertTrue((target / "docs/project/overview.md").exists())
            second = run("python3", "ai/scripts/bootstrap_project.py", td)
            self.assertIn("BOOTSTRAP_CREATED=", first.stdout)
            self.assertIn("BOOTSTRAP_CONFLICTS=AGENTS.md", first.stdout)
            self.assertIn("BOOTSTRAP_CREATED=", second.stdout)
            self.assertIn("BOOTSTRAP_CONFLICTS=AGENTS.md", second.stdout)
            self.assertTrue((target / ".opencode/AGENTS.md").exists())
            self.assertTrue((target / ".claude/CLAUDE.md").exists())
            self.assertTrue((target / ".codex/config.toml").exists())

    def test_managed_install_preserves_unrelated_and_rolls_back(self):
        with tempfile.TemporaryDirectory() as td, tempfile.TemporaryDirectory() as staging_dir:
            home = Path(td)
            (home / ".claude").mkdir()
            (home / ".config/opencode").mkdir(parents=True)
            (home / ".codex").mkdir()
            unrelated = home / ".claude/custom-plugin.txt"
            unrelated.write_text("keep\n")
            claude_settings = home / ".claude/settings.json"
            claude_settings.write_text(json.dumps({"enabledPlugins": {"custom@local": True, "engram@engram": True}}))
            oc_settings = home / ".config/opencode/opencode.json"
            oc_settings.write_text(json.dumps({"plugin": ["custom"], "mcp": {"playwright": {"enabled": True}}}))
            (home / ".codex/config.toml").write_text('[agents]\nmax_threads = 9\n\n[mcp_servers.playwright]\ncommand = "npx"\nenabled = true\n')
            run("./build.sh", "--output", staging_dir)
            run("python3", "ai/scripts/install.py", "--staging", staging_dir, "--home", td)
            self.assertEqual(unrelated.read_text(), "keep\n")
            self.assertTrue(json.loads(claude_settings.read_text())["enabledPlugins"]["custom@local"])
            self.assertFalse(json.loads(claude_settings.read_text())["enabledPlugins"]["engram@engram"])
            self.assertEqual(json.loads(oc_settings.read_text())["plugin"], ["custom"])
            codex_config = tomllib.loads((home / ".codex/config.toml").read_text())
            self.assertTrue(codex_config["features"]["multi_agent"])
            self.assertEqual(codex_config["agents"]["max_depth"], 1)
            self.assertEqual(codex_config["agents"]["max_threads"], 4)
            self.assertFalse(codex_config["mcp_servers"]["playwright"]["enabled"])
            before = claude_settings.read_bytes()
            failed = run("python3", "ai/scripts/install.py", "--staging", staging_dir, "--home", td, env={"SET_AGENTS_FORCE_SMOKE_FAIL": "1"}, check=False)
            self.assertNotEqual(failed.returncode, 0)
            self.assertEqual(claude_settings.read_bytes(), before)
            self.assertEqual(unrelated.read_text(), "keep\n")

    def test_install_prunes_orphaned_managed_files_but_keeps_user_files(self):
        with tempfile.TemporaryDirectory() as td, tempfile.TemporaryDirectory() as staging_dir:
            home = Path(td)
            (home / ".claude").mkdir()
            (home / ".config/opencode").mkdir(parents=True)
            (home / ".codex").mkdir()
            run("./build.sh", "--output", staging_dir)
            run("python3", "ai/scripts/install.py", "--staging", staging_dir, "--home", td)

            manifest = home / ".local/state/set-agentes/managed-files.json"
            self.assertTrue(manifest.exists(), "install must record a managed-files manifest")
            recorded = json.loads(manifest.read_text())
            self.assertIn(".claude/skills/regression-tests/SKILL.md", recorded)

            # A file we USED to manage (renamed away) — recorded in the manifest, must be pruned.
            orphan = home / ".claude/skills/tdd/SKILL.md"
            orphan.parent.mkdir(parents=True)
            orphan.write_text("stale tdd skill\n")
            # A user file living beside it — NOT in the manifest, must be preserved.
            user_sibling = orphan.parent / "user-notes.md"
            user_sibling.write_text("mine\n")
            # An orphan whose directory becomes empty — the empty dir must be cleaned up too.
            lone_orphan = home / ".claude/skills/deadskill/SKILL.md"
            lone_orphan.parent.mkdir(parents=True)
            lone_orphan.write_text("gone\n")
            # A user file outside any managed subtree — must never be touched.
            untouched = home / ".claude/custom-plugin.txt"
            untouched.write_text("keep\n")
            manifest.write_text(json.dumps(recorded + [
                ".claude/skills/tdd/SKILL.md",
                ".claude/skills/deadskill/SKILL.md",
            ], indent=2))

            result = run("python3", "ai/scripts/install.py", "--staging", staging_dir, "--home", td)
            self.assertIn("PRUNED_ORPHANS=", result.stdout)
            self.assertFalse(orphan.exists(), "recorded orphan must be pruned")
            self.assertTrue(user_sibling.exists(), "unrecorded user file must be preserved")
            self.assertEqual(user_sibling.read_text(), "mine\n")
            self.assertFalse(lone_orphan.exists(), "recorded orphan must be pruned")
            self.assertFalse(lone_orphan.parent.exists(), "emptied directory must be cleaned up")
            self.assertEqual(untouched.read_text(), "keep\n")
            # The manifest no longer lists the pruned paths.
            self.assertNotIn(".claude/skills/tdd/SKILL.md", json.loads(manifest.read_text()))

    def test_generation_is_reproducible(self):
        with tempfile.TemporaryDirectory() as one, tempfile.TemporaryDirectory() as two:
            run("./build.sh", "--output", one)
            run("./build.sh", "--output", two)
            comparison = filecmp.dircmp(one, two)
            self.assertFalse(comparison.left_only or comparison.right_only or comparison.diff_files or comparison.funny_files)

    def test_gate_guard_blocks_execution_flags(self):
        for command in ("go test -exec /bin/sh ./...", "go test -exec=/tmp/evil ./...", "go test -toolexec evil ./...", "cargo test --config target.runner='evil'", "cargo test --config=target.runner='evil'"):
            payload = json.dumps({"tool_input": {"command": command}})
            result = subprocess.run(["python3", "ai/scripts/claude_gate_guard.py"], input=payload, text=True, capture_output=True)
            self.assertEqual(result.returncode, 2, command)
        gate = (ROOT / "Global/opencode/agents/gate-runner.md").read_text()
        self.assertIn('"*--config*": deny', gate)
        self.assertIn('"*--runner*": deny', gate)
        self.assertIn('"*-exec*": deny', gate)
        self.assertIn('"*>*": deny', gate)
        self.assertIn('"*|*": deny', gate)


if __name__ == "__main__":
    unittest.main()
