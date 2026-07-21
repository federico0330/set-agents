import json
import os
import re
import subprocess
import tempfile
import time
import tomllib
import unittest
import filecmp
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FEATURE_STATE = ROOT / "PROYECTO/ai/scripts/feature-state.py"
CHECK_OWNED = ROOT / "PROYECTO/ai/scripts/check-owned-paths.py"
COST_REPORT = ROOT / "ai/scripts/cost-report.py"


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
    def run_state(self, state, *args, check=True):
        return run("python3", str(FEATURE_STATE), *args, "--state-file", str(state), check=check)

    def create_ready_package(self, td, *, max_cycles=2, review=True):
        state = Path(td) / "feature.json"
        run("python3", str(FEATURE_STATE), "init", "feat", "docs/specs/feat/spec.md", "hash",
            "--state-file", str(state), "--ac", "AC-1", "--ac", "AC-2",
            "--max-deep-review-cycles", str(max_cycles))
        self.run_state(
            state, "create-package", "PKG-01", "Observable slice",
            "--ac", "AC-1", "--ac", "AC-2",
            "--task", "T-001", "--task", "T-002", "--task", "T-003",
            "--owned-path", "src/**", "--owned-path", "tests/**",
            "--complexity", "medium",
            "--selected-role", "implementer",
            "--selected-model", "openai/gpt-5.6-terra",
            "--routing-reason", "three related tasks across code and tests",
        )
        self.run_state(state, "transition", "PACKAGE_IMPLEMENTATION", "--package-id", "PKG-01")
        for task_id in ("T-001", "T-002", "T-003"):
            self.run_state(state, "complete-task", "PKG-01", task_id, "--actor", "implementer", "--validation", "focused-test")
        self.run_state(state, "transition", "PACKAGE_GATES", "--package-id", "PKG-01")
        self.run_state(state, "record-gate", "package verify", "pass", "--package-id", "PKG-01", "--evidence", "ok")
        self.run_state(state, "update-package", "PKG-01", "--integrated", "true", "--diff-ref", "HEAD..work")
        self.run_state(state, "transition", "PACKAGE_REVIEW", "--package-id", "PKG-01")
        if review:
            finding_a = json.dumps({"id": "F-001", "severity": "high", "category": "correctness"})
            finding_b = json.dumps({"id": "F-002", "severity": "medium", "category": "testing"})
            self.run_state(
                state, "record-review", "PKG-01", "repair_required",
                "--actor", "package-reviewer", "--finding", finding_a, "--finding", finding_b,
            )
        return state

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
        gate_runner = tomllib.loads((ROOT / "Global/codex/agents/gate-runner.toml").read_text())
        self.assertEqual(gate_runner["sandbox_mode"], "read-only")

    def test_coordinator_policy(self):
        allowed = [
            "git status --short", "git diff --stat", "dotnet --list-sdks",
            "node --version", "npm ls --depth=0", "python --version",
            "pip list", "go version", "rustup toolchain list", "opencode models",
            # The state CLI is the orchestrator's sanctioned mutation channel: every
            # subcommand must pass without a permission prompt.
            "python3 ai/scripts/feature-state.py status feat-x",
            "python3 ai/scripts/feature-state.py record-spawn PKG-01 implementer --state-file ai/state/features/feat-x.json",
            "python3 ai/scripts/feature-state.py init feat-x docs/specs/feat-x/spec.md abc123 --mode scoped",
        ]
        denied = [
            "echo x > file", "printf x | tee file", "sed -i s/a/b/ file",
            "npm install x", "git add .", "git commit -m x", "git push",
            "gh pr create", "./ai/scripts/mcp.sh on", "./ai/scripts/loop.sh",
            "git diff --output=changed.patch", "rg --pre 'touch owned' pattern", "fd -x touch owned",
            "node --version -e 'require(\"fs\").writeFileSync(\"x\",\"y\")'",
            "git diff --stat>owned", "git diff --stat|tee owned", "git diff --stat&&git status",
            # Shell composition around the state CLI stays blocked.
            "python3 ai/scripts/feature-state.py status feat-x > owned",
            "python3 ai/scripts/feature-state.py status feat-x && git push",
            "python3 other/feature-state.py status feat-x",
        ]
        for command in allowed:
            self.assertEqual(run("python3", "ai/scripts/coord_policy.py", command, check=False).returncode, 0, command)
        for command in denied:
            self.assertEqual(run("python3", "ai/scripts/coord_policy.py", command, check=False).returncode, 2, command)

    def test_oc_steps_meet_role_floors(self):
        # Regression guard for the mid-task cutoff pain: step budgets are a circuit
        # breaker, not the anti-loop mechanism, so key roles must keep enough steps
        # to finish a bounded task in one instantiation.
        floors = {
            "orchestrator": 50,
            "implementer": 30,
            "frontend-engineer": 30,
            "repair-agent": 24,
            "package-reviewer": 18,
            "gate-runner": 12,
        }
        with tempfile.TemporaryDirectory() as td:
            run("python3", "ai/scripts/generate.py", "--profile", "go-zen", "--output", str(Path(td) / "out"))
            for role, floor in floors.items():
                text = (Path(td) / "out/opencode/agents" / f"{role}.md").read_text()
                match = re.search(r"^steps: (\d+)$", text, re.MULTILINE)
                self.assertIsNotNone(match, role)
                self.assertGreaterEqual(int(match.group(1)), floor, role)

    def test_render_status_reflects_multi_feature_state(self):
        with tempfile.TemporaryDirectory() as td:
            features = Path(td) / "ai/state/features"
            for feature_id, mode in (("feat-a", "scoped"), ("feat-b", "quick-fix")):
                run("python3", str(FEATURE_STATE), "init", feature_id,
                    f"docs/specs/{feature_id}/spec.md", "hash", "--mode", mode,
                    "--state-file", str(features / f"{feature_id}.json"))
            run("python3", str(FEATURE_STATE), "log-quickfix",
                "--summary", "fix header typo", "--result", "done",
                "--file", "src/app.ts", "--gate", "verify pass",
                "--log-file", str(Path(td) / "ai/state/quickfix-log.jsonl"))
            status = (Path(td) / "ai/state/STATUS.md").read_text()
            self.assertIn("feat-a", status)
            self.assertIn("feat-b", status)
            self.assertIn("scoped", status)
            self.assertIn("quick-fix", status)
            self.assertIn("fix header typo", status)

    def test_log_quickfix_appends_and_renders(self):
        with tempfile.TemporaryDirectory() as td:
            log = Path(td) / "ai/state/quickfix-log.jsonl"
            for summary in ("first fix", "second fix"):
                run("python3", str(FEATURE_STATE), "log-quickfix",
                    "--summary", summary, "--result", "done", "--log-file", str(log))
            entries = [json.loads(line) for line in log.read_text().splitlines()]
            self.assertEqual([e["summary"] for e in entries], ["first fix", "second fix"])
            status = (Path(td) / "ai/state/STATUS.md").read_text()
            self.assertIn("second fix", status)
            self.assertIn("sin features registradas", status)

    def test_log_narrative_appends_and_renders(self):
        with tempfile.TemporaryDirectory() as td:
            log = Path(td) / "ai/state/narrative-log.jsonl"
            run("python3", str(FEATURE_STATE), "init", "feat-n",
                "docs/specs/feat-n/spec.md", "hash", "--mode", "scoped",
                "--state-file", str(Path(td) / "ai/state/features/feat-n.json"))
            run("python3", str(FEATURE_STATE), "log-narrative",
                "--client", "ya podés cobrar con tarjeta",
                "--tech", "cierre del paquete de pagos, gate verde",
                "--role", "implementer", "--feature-id", "feat-n", "--result", "done",
                "--log-file", str(log))
            entries = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]
            self.assertEqual(len(entries), 1)
            self.assertEqual(entries[0]["client"], "ya podés cobrar con tarjeta")
            # The dashboard carries the tail of the story...
            status = (Path(td) / "ai/state/STATUS.md").read_text(encoding="utf-8")
            self.assertIn("## Bitácora", status)
            self.assertIn("ya podés cobrar con tarjeta", status)
            self.assertIn("Ingeniería:", status)
            # ...and the per-feature file carries all of it. No docs/specs/ dir
            # here, so it must land on the internal fallback path.
            bitacora = (Path(td) / "ai/state/bitacora/feat-n.md").read_text(encoding="utf-8")
            self.assertIn("Bitácora — feat-n", bitacora)
            self.assertIn("cierre del paquete de pagos", bitacora)

    def test_record_spawn_carries_dual_register(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            state = root / "ai/state/features/feat-s.json"
            # A delivery folder exists, so the bitacora must prefer it over the
            # internal fallback — it is what the client actually receives.
            (root / "docs/specs/feat-s").mkdir(parents=True)
            run("python3", str(FEATURE_STATE), "init", "feat-s",
                "docs/specs/feat-s/spec.md", "hash", "--mode", "scoped", "--state-file", str(state))
            run("python3", str(FEATURE_STATE), "create-package", "PKG-00", "reprovisión",
                "--state-file", str(state), "--task", "T-1", "--ac", "AC-1",
                "--complexity", "small", "--owned-path", "src/db")
            run("python3", str(FEATURE_STATE), "record-spawn", "PKG-00", "implementer",
                "--state-file", str(state),
                "--client", "los datos ya no se pierden entre corridas",
                "--tech", "el paquete toca schema; small, así que solo package-reviewer")
            data = json.loads(state.read_text(encoding="utf-8"))
            spawn = [e for e in data["history"] if e["event"] == "record-spawn"][-1]
            self.assertEqual(spawn["metadata"]["client"], "los datos ya no se pierden entre corridas")
            self.assertIn("package-reviewer", spawn["metadata"]["tech"])
            bitacora = (root / "docs/specs/feat-s/bitacora.md").read_text(encoding="utf-8")
            self.assertIn("los datos ya no se pierden entre corridas", bitacora)
            self.assertIn("PKG-00 · implementer · started", bitacora)
            self.assertFalse((root / "ai/state/bitacora/feat-s.md").exists())

    def test_orchestrator_narration_reaches_all_three_harnesses(self):
        # The user reads the harness through OpenCode, Claude Code and Codex.
        # generate.py copies the canonical body verbatim into all three, so this
        # is the test that proves the transparency protocol is not OpenCode-only.
        run("./build.sh")
        artifacts = [
            (ROOT / "Global/opencode/agents/orchestrator.md").read_text(encoding="utf-8"),
            (ROOT / "Global/claude-code/agents/orchestrator.md").read_text(encoding="utf-8"),
            (ROOT / "Global/codex/agents/orchestrator.toml").read_text(encoding="utf-8"),
        ]
        for text in artifacts:
            self.assertIn("▸ Instancio", text)
            self.assertIn("Cliente:", text)
            self.assertIn("Ingeniería:", text)
            # Both halves of the cadence, and the durability rule that keeps the
            # narration out of chat-only limbo.
            self.assertIn("terminó", text)
            self.assertIn("log-narrative", text)
            self.assertIn("record-spawn --client", text)
            # The end-of-turn block must survive alongside the new protocol.
            self.assertIn("Necesito de vos:", text)

    def test_shared_doctrine_covers_narration(self):
        for name in ("AGENTS.opencode.md", "CLAUDE.md", "AGENTS.codex.md"):
            text = (ROOT / "Global/_shared" / name).read_text(encoding="utf-8")
            self.assertIn("## Narration", text, name)
            self.assertIn("two labelled registers", text, name)
            self.assertIn("log-narrative", text, name)
            self.assertIn("bitacora.md", text, name)

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
            "adversarial-judge\tsubagent\t0.0\treview-ro\tjudge\topenai/gpt-5.3-codex-spark",
        )
        with tempfile.TemporaryDirectory() as td:
            roles = Path(td) / "roles.tsv"
            roles.write_text(roster)
            result = run("python3", "ai/scripts/generate.py", "--profile", "go-zen", "--output", str(Path(td) / "out"), "--roles", str(roles), check=False)
        self.assertEqual(result.returncode, 2)
        self.assertIn("separation violation", result.stderr)

        mutating_reviewer = (ROOT / "roles.tsv").read_text().replace("package-reviewer\tsubagent\t0.0\treview-ro\taudit", "package-reviewer\tsubagent\t0.0\tcode-rw\taudit")
        with tempfile.TemporaryDirectory() as td:
            roles = Path(td) / "roles.tsv"
            roles.write_text(mutating_reviewer)
            result = run("python3", "ai/scripts/generate.py", "--profile", "go-zen", "--output", str(Path(td) / "out"), "--roles", str(roles), check=False)
        self.assertEqual(result.returncode, 2)
        self.assertIn("mutating capability", result.stderr)

        family_overlap = (ROOT / "roles.tsv").read_text().replace("package-reviewer\tsubagent\t0.0\treview-ro\taudit\topenai/gpt-5.6-sol\topenai/gpt-5.5\topenai/gpt-5.5\topus\tgpt-5.6-sol", "package-reviewer\tsubagent\t0.0\treview-ro\taudit\topenai/gpt-5.6-sol\topenai/gpt-5.5\topenai/gpt-5.5\topus\tgpt-5.6-terra")
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

    def test_orchestrator_delegation_graph_is_broad_but_state_governed(self):
        run("./build.sh")
        oc = (ROOT / "Global/opencode/agents/orchestrator.md").read_text()
        claude = (ROOT / "Global/claude-code/agents/orchestrator.md").read_text()
        allowed = ["spec-challenger", "package-planner", "implementer", "package-reviewer", "repair-agent", "delta-reviewer", "integrator"]
        specialists = ["security-auditor"]
        for role in allowed:
            self.assertIn(f'"{role}": allow', oc)
            self.assertIn(role, claude)
        for role in specialists:
            self.assertIn(f'"{role}": allow', oc)
            self.assertIn(role, claude)
        self.assertIn("start-review-panel", oc)
        self.assertIn("record-subreview", oc)

    def test_runtime_verifier_can_manage_browser_mcp_gate(self):
        run("./build.sh")
        oc = (ROOT / "Global/opencode/agents/runtime-verifier.md").read_text()
        claude = (ROOT / "Global/claude-code/agents/runtime-verifier.md").read_text()
        codex = tomllib.loads((ROOT / "Global/codex/agents/runtime-verifier.toml").read_text())["developer_instructions"]
        for text in (oc, claude, codex):
            self.assertIn("mcp.sh browser-gate auto", text)
            self.assertIn("Do not ask the user to toggle MCP", text)
            self.assertNotIn("do not try to enable MCP yourself", text)
        self.assertIn('"./ai/scripts/mcp.sh browser-gate*": allow', oc)
        self.assertIn('"./ai/scripts/e2e.sh*": allow', oc)
        self.assertNotIn('"*mcp.sh*": deny', oc)

    def test_mcp_browser_gate_toggles_playwright_without_manual_steps(self):
        with tempfile.TemporaryDirectory() as td:
            cfg = Path(td) / "opencode.json"
            cfg.write_text(json.dumps({
                "mcp": {
                    "playwright": {"enabled": False},
                    "brave-cdp": {"enabled": False},
                }
            }))
            enabled = run(
                str(ROOT / "PROYECTO/ai/scripts/mcp.sh"), "browser-gate", "playwright",
                env={"OPENCODE_CONFIG": str(cfg)},
            )
            self.assertIn("BROWSER_GATE_READY mode=playwright", enabled.stdout)
            self.assertTrue(json.loads(cfg.read_text())["mcp"]["playwright"]["enabled"])
            disabled = run(
                str(ROOT / "PROYECTO/ai/scripts/mcp.sh"), "off", "playwright",
                env={"OPENCODE_CONFIG": str(cfg)},
            )
            self.assertIn("MCP_SET server=playwright enabled=false", disabled.stdout)
            self.assertFalse(json.loads(cfg.read_text())["mcp"]["playwright"]["enabled"])

    def test_claude_ask_guard_fails_open_except_always_denied(self):
        # Known-good and merely-uncommon commands both fall through (exit 0) to Claude Code's
        # own native permission prompt instead of a silent hard block.
        for command in ("./ai/scripts/mcp.sh browser-gate auto", "./ai/scripts/mcp.sh on context7", "docker ps", "cat some/file.py"):
            payload = json.dumps({"tool_input": {"command": command}})
            result = subprocess.run(["python3", "ai/scripts/claude_ask_guard.py"], input=payload, text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, (command, result.stderr))
        # The short, irreducible safety net still hard-blocks regardless of role.
        for dangerous in ("sudo rm -rf /", "rm -rf /", "git push --force origin main", "git push -f origin main", "gh repo delete owner/repo"):
            payload = json.dumps({"tool_input": {"command": dangerous}})
            blocked = subprocess.run(["python3", "ai/scripts/claude_ask_guard.py"], input=payload, text=True, capture_output=True)
            self.assertEqual(blocked.returncode, 2, dangerous)

    def test_release_gate_requires_two_confirmations(self):
        base = {"verify": "pass", "audits": "pass", "judge": "JUDGE_PASS", "surfaces": [], "audits_ran": ["package-reviewer"]}
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
            # auth surface without its mandatory reviewer → blocked, names the missing reviewer
            state.write_text(json.dumps({**green, "surfaces": ["auth"], "audits_ran": ["package-reviewer"]}))
            blocked = run("python3", "ai/scripts/release_gate.py", str(state), "commit", check=False)
            self.assertEqual(blocked.returncode, 2)
            self.assertIn("security-auditor", blocked.stderr)
            # auth surface WITH the mandatory reviewers recorded → allowed
            state.write_text(json.dumps({**green, "surfaces": ["auth"],
                                         "audits_ran": ["package-reviewer", "security-auditor"]}))
            self.assertEqual(run("python3", "ai/scripts/release_gate.py", str(state), "commit", check=False).returncode, 0)

    def test_release_action_blocks_destructive_publishes(self):
        base = {"verify": "pass", "audits": "pass", "judge": "JUDGE_PASS", "publish_confirmed": True,
                "surfaces": [], "audits_ran": ["package-reviewer"]}
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
        self.assertIn('"gh repo delete*": deny', oc)
        self.assertIn('"python3 ~/.config/opencode/hooks/release_action.py*": allow', oc)
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
            self.assertTrue((target / "docs/architecture/overview.md").exists())
            self.assertTrue((target / "docs/adr/README.md").exists())
            self.assertTrue((target / "docs/specs/README.md").exists())
            # per-domain knowledge seeds are created but an existing (grown) file is preserved
            knowledge = target / "docs/ai/knowledge/security.md"
            self.assertTrue(knowledge.exists())
            knowledge.write_text("grown department memory\n")
            second = run("python3", "ai/scripts/bootstrap_project.py", td)
            self.assertEqual(knowledge.read_text(), "grown department memory\n")
            self.assertTrue((target / "docs/ai/knowledge/algorithms.md").exists())
            self.assertIn("BOOTSTRAP_CREATED=", first.stdout)
            self.assertIn("BOOTSTRAP_CONFLICTS=AGENTS.md", first.stdout)
            self.assertIn("BOOTSTRAP_CREATED=", second.stdout)
            self.assertIn("BOOTSTRAP_CONFLICTS=AGENTS.md", second.stdout)
            self.assertTrue((target / ".opencode/AGENTS.md").exists())
            self.assertTrue((target / ".claude/CLAUDE.md").exists())
            self.assertTrue((target / ".codex/config.toml").exists())

    def test_domain_knowledge_is_wired_through_the_canon(self):
        run("./build.sh")
        wiring = {
            "security-auditor": "docs/ai/knowledge/security.md",
            "package-reviewer": "docs/ai/knowledge/data.md",
            "architect": "docs/ai/knowledge/architecture.md",
            "spec-challenger": "docs/ai/knowledge/architecture.md",
            "implementer": "docs/ai/knowledge/data.md",
            "frontend-engineer": "docs/ai/knowledge/frontend.md",
            "ux-ui-designer": "docs/ai/knowledge/frontend.md",
        }
        for agent, reference in wiring.items():
            text = (ROOT / "Global/claude-code/agents" / f"{agent}.md").read_text()
            self.assertIn(reference, text, agent)
        scribe = (ROOT / "Global/claude-code/agents/memory-scribe.md").read_text()
        self.assertIn("ONLY writer", scribe)
        self.assertIn("docs/ai/knowledge/", scribe)
        orchestrator = (ROOT / "Global/claude-code/agents/orchestrator.md").read_text()
        self.assertIn("MANDATORY at feature close", orchestrator)
        for domain in ("security", "data", "architecture", "algorithms", "frontend"):
            self.assertTrue((ROOT / "PROYECTO/docs/ai/knowledge" / f"{domain}.md").exists(), domain)
            self.assertTrue((ROOT / "knowledge" / f"{domain}.md").exists(), domain)

    def test_consult_mode_is_wired_and_never_starts_pipeline(self):
        run("./build.sh")
        triage = (ROOT / "Global/claude-code/skills/request-triage/SKILL.md").read_text()
        orchestrator = (ROOT / "Global/claude-code/agents/orchestrator.md").read_text()
        self.assertIn("Consult / analysis", triage)
        self.assertIn("NEVER starts the pipeline", triage)
        self.assertIn("NO `init`, NO state file, NO pipeline", triage)
        self.assertIn("## Consult mode", orchestrator)
        self.assertIn("NEVER starts the pipeline", orchestrator)
        for harness in ("opencode", "claude-code"):
            self.assertTrue((ROOT / "Global" / harness / "commands/consult.md").exists(), harness)
            self.assertTrue((ROOT / "Global" / harness / "commands/status.md").exists(), harness)
        # scoped is the default lane; full SDD stays opt-in.
        self.assertIn("scoped-feature — the DEFAULT".lower(), triage.lower())
        self.assertIn("opt-in", triage)

    def test_architecture_gate_is_wired_through_the_canon(self):
        run("./build.sh")
        orchestrator = (ROOT / "Global/claude-code/agents/orchestrator.md").read_text()
        architect = (ROOT / "Global/claude-code/agents/architect.md").read_text()
        spec_challenger = (ROOT / "Global/claude-code/agents/spec-challenger.md").read_text()
        design_skill = (ROOT / "Global/claude-code/skills/system-design-decisions/SKILL.md").read_text()
        triage_skill = (ROOT / "Global/claude-code/skills/request-triage/SKILL.md").read_text()
        # The orchestrator must recognize a missing architecture ADR as a question-worthy category that
        # overrides "a safe default exists, so continue".
        self.assertIn("vector vs relational", orchestrator)
        self.assertIn("API Gateway", orchestrator)
        self.assertIn("VPS/IaaS", orchestrator)
        self.assertIn("excuse skipping the question", orchestrator)
        # architect must own the living architecture doc and the ADR index, not just loose ADR files.
        self.assertIn("docs/architecture/overview.md", architect)
        self.assertIn("docs/adr/README.md", architect)
        # spec-challenger must treat an unaddressed architecture axis as a blocking finding.
        self.assertIn("category: architecture", spec_challenger)
        # the design-time skill must cover the three named axes, not just the generic scale framework.
        self.assertIn("Vector / embedding store", design_skill)
        self.assertIn("API Gateway", design_skill)
        self.assertIn("Deploy platform", design_skill)
        # the transversal red-flag check must apply even outside full feature/SDD mode.
        self.assertIn("Architecture red-flags", triage_skill)
        self.assertIn("including quick-fix", triage_skill)

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

    def test_sync_project_copies_generic_scripts_and_guards_active_state(self):
        with tempfile.TemporaryDirectory() as td:
            project = Path(td)
            (project / "ai/scripts").mkdir(parents=True)
            (project / "ai/scripts/run.sh").write_text("#!/bin/sh\necho project-specific\n")
            (project / "ai/scripts/feature-state.py").write_text("# old divergent copy\n")
            # incompatible ACTIVE state → abort
            states = project / "ai/state/features"
            states.mkdir(parents=True)
            (states / "f.json").write_text(json.dumps({"phase": "PACKAGE_PLANNING", "foo": 1}))
            aborted = run("ai/scripts/sync-project.sh", str(project), check=False)
            self.assertEqual(aborted.returncode, 1)
            self.assertIn("SYNC_ABORTED", aborted.stdout + aborted.stderr)
            self.assertIn("old divergent", (project / "ai/scripts/feature-state.py").read_text())
            # terminal state → syncs, backs up the old copy, leaves run.sh alone
            (states / "f.json").write_text(json.dumps({"phase": "BLOCKED", "foo": 1}))
            ok = run("ai/scripts/sync-project.sh", str(project))
            self.assertIn("SYNC_OK", ok.stdout)
            self.assertIn("state machine", (project / "ai/scripts/feature-state.py").read_text())
            self.assertIn("project-specific", (project / "ai/scripts/run.sh").read_text())
            backups = list((project / "ai/state").glob("sync-backup-*/feature-state.py"))
            self.assertTrue(backups and "old divergent" in backups[0].read_text())
            # global domain knowledge is distributed read-only; project knowledge is never touched
            self.assertTrue((project / "docs/ai/knowledge/_global/security.md").exists())
            self.assertIn("cross-proyecto", (project / "docs/ai/knowledge/_global/security.md").read_text().lower())
            self.assertFalse((project / "docs/ai/knowledge/security.md").exists())

    def test_check_drift_detects_stale_and_clean_install(self):
        with tempfile.TemporaryDirectory() as td:
            home = Path(td)
            for sub in (".claude", ".config/opencode", ".codex"):
                (home / sub).mkdir(parents=True)
            # empty fake home = everything differs
            stale = run("ai/scripts/check-drift.sh", env={"DRIFT_HOME": td}, check=False)
            self.assertEqual(stale.returncode, 1)
            self.assertIn("DRIFT_DETECTED", stale.stdout)
            # install into the fake home, then drift must be clean
            with tempfile.TemporaryDirectory() as staging_dir:
                run("./build.sh", "--output", staging_dir)
                run("python3", "ai/scripts/install.py", "--staging", staging_dir, "--home", td)
            clean = run("ai/scripts/check-drift.sh", env={"DRIFT_HOME": td})
            self.assertIn("DRIFT_OK", clean.stdout)

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

    def test_gate_guard_fails_open_except_always_denied(self):
        # A gate command with an unexpected flag (e.g. -exec) now falls through to Claude Code's
        # native permission prompt instead of a silent hard block — only the short always-dangerous
        # list still blocks outright.
        for command in ("go test -exec /bin/sh ./...", "go test -exec=/tmp/evil ./...", "go test -toolexec evil ./...", "cargo test --config target.runner='evil'"):
            payload = json.dumps({"tool_input": {"command": command}})
            result = subprocess.run(["python3", "ai/scripts/claude_ask_guard.py"], input=payload, text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, command)
        gate = (ROOT / "Global/opencode/agents/gate-runner.md").read_text()
        self.assertIn('"*": ask', gate)
        self.assertIn('"sudo *": deny', gate)
        self.assertIn('"rm -rf*": deny', gate)
        self.assertIn('"git push --force*": deny', gate)
        self.assertIn('"gh repo delete*": deny', gate)

    def test_generic_harness_has_no_project_specific_leaks(self):
        # The generic harness must never bake one project's paths, feature ids, worktrees, or
        # baselines into the artifacts every project receives. Project-specific bounded agents (e.g.
        # a package-gate-runner scoped to one feature/worktree) live as per-project overrides in
        # <repo>/.opencode/agent/, not in the canonical source-of-truth.
        run("./build.sh")
        # No package-gate-runner is generated into any harness, and none ships from the canonical source.
        self.assertFalse((ROOT / "Global/opencode/agents/package-gate-runner.md").exists())
        self.assertFalse((ROOT / "Global/claude-code/agents/package-gate-runner.md").exists())
        self.assertFalse((ROOT / "Global/codex/agents/package-gate-runner.toml").exists())
        self.assertFalse((ROOT / "Global/_canonical/opencode-agents/package-gate-runner.md").exists())

        # No orchestrator, on any harness, mentions a specific feature/package/worktree/baseline.
        leaks = ("replenishment-v2", "RPL-P0A", "4ef70b0ab6da", "002-local-uat-identities")
        oc_orch = (ROOT / "Global/opencode/agents/orchestrator.md").read_text()
        cc_orch = (ROOT / "Global/claude-code/agents/orchestrator.md").read_text()
        cx_orch = tomllib.loads(
            (ROOT / "Global/codex/agents/orchestrator.toml").read_text()
        )["developer_instructions"]
        for leak in leaks:
            for text in (oc_orch, cc_orch, cx_orch):
                self.assertNotIn(leak, text)

        # The orchestrator still permits delegating to a project-provided package-gate-runner, so a
        # project override under <repo>/.opencode/agent/ stays reachable without any hardcoded path.
        self.assertIn('    "package-gate-runner": allow', oc_orch)

        # The generic local-gate-runner is scoped to the canonical state location, not one project's file.
        oc_local_gate = (ROOT / "Global/opencode/agents/local-gate-runner.md").read_text()
        self.assertIn('    "ai/state/features/*.json": allow', oc_local_gate)
        for leak in leaks:
            self.assertNotIn(leak, oc_local_gate)

    def test_package_workflow_happy_path_executes_real_transitions(self):
        with tempfile.TemporaryDirectory() as td:
            state = self.create_ready_package(td)
            self.run_state(
                state, "record-repair", "PKG-01", "--actor", "repair-agent",
                "--finding-id", "F-001", "--finding-id", "F-002",
                "--changed-file", "src/example.py", "--verification", "focused-test",
            )
            self.run_state(
                state, "record-delta-review", "PKG-01", "pass", "--actor", "delta-reviewer",
                "--closed-finding", "F-001", "--closed-finding", "F-002",
            )
            self.run_state(state, "record-testing", "PKG-01", "pass", "--actor", "gate-runner", "--command", "verify")
            self.run_state(
                state, "record-runtime-qa", "PKG-01", "pass", "--actor", "runtime-verifier",
                "--url", "http://localhost:3000", "--browser", "playwright", "--check", "customer-visible flow works",
            )
            self.run_state(state, "accept-package", "PKG-01", "--actor", "orchestrator")
            self.run_state(state, "transition", "INTEGRATION")
            self.run_state(state, "record-gate", "global verify", "pass", "--global-gate", "--evidence", "ok")
            self.run_state(state, "transition", "DONE")
            data = json.loads(state.read_text())
        self.assertEqual(data["phase"], "DONE")
        self.assertEqual(data["metrics"]["task_deep_reviews"], 0)
        self.assertEqual(data["metrics"]["package_reviews"], 1)
        self.assertEqual(data["metrics"]["repair_batches"], 1)
        self.assertEqual(data["metrics"]["delta_reviews"], 1)
        self.assertEqual(len(data["packages"][0]["tasks"]), 3)
        self.assertEqual(data["packages"][0]["testing"][-1]["status"], "pass")
        self.assertEqual(data["packages"][0]["runtime_qa"][-1]["status"], "pass")

    def test_review_panel_allows_many_subagents_as_one_cycle(self):
        with tempfile.TemporaryDirectory() as td:
            state = self.create_ready_package(td, review=False)
            self.run_state(
                state, "start-review-panel", "PKG-01",
                "--role", "package-reviewer", "--role", "security-auditor", "--role", "db-auditor", "--role", "performance-auditor",
            )
            self.run_state(state, "record-subreview", "PKG-01", "package-reviewer", "pass", "--actor", "package-reviewer")
            finding = json.dumps({"id": "F-SEC-001", "severity": "high", "category": "security"})
            self.run_state(state, "record-subreview", "PKG-01", "security-auditor", "repair_required", "--actor", "security-auditor", "--finding", finding)
            self.run_state(state, "record-subreview", "PKG-01", "db-auditor", "pass", "--actor", "db-auditor")
            self.run_state(state, "record-subreview", "PKG-01", "performance-auditor", "pass", "--actor", "performance-auditor")
            self.run_state(state, "finalize-review-panel", "PKG-01", "repair_required", "--actor", "package-reviewer")
            data = json.loads(state.read_text())
        self.assertEqual(data["metrics"]["package_reviews"], 1)
        self.assertEqual(data["packages"][0]["attempts"]["deep_review_cycles"], 1)
        self.assertEqual(len(data["packages"][0]["review_panels"][0]["subreviews"]), 4)
        self.assertEqual(data["phase"], "PACKAGE_REPAIR")

    def test_package_review_requires_completed_tasks(self):
        with tempfile.TemporaryDirectory() as td:
            state = Path(td) / "feature.json"
            run("python3", str(FEATURE_STATE), "init", "feat", "spec.md", "hash", "--state-file", str(state), "--ac", "AC-1")
            self.run_state(
                state, "create-package", "PKG-01", "Slice",
                "--ac", "AC-1", "--task", "T-001", "--task", "T-002",
                "--owned-path", "src/**", "--complexity", "medium",
            )
            self.run_state(state, "transition", "PACKAGE_IMPLEMENTATION", "--package-id", "PKG-01")
            self.run_state(state, "complete-task", "PKG-01", "T-001", "--actor", "implementer", "--validation", "unit")
            self.run_state(state, "transition", "PACKAGE_GATES", "--package-id", "PKG-01")
            self.run_state(state, "record-gate", "package verify", "pass", "--package-id", "PKG-01")
            self.run_state(state, "update-package", "PKG-01", "--integrated", "true", "--diff-ref", "diff")
            result = self.run_state(state, "transition", "PACKAGE_REVIEW", "--package-id", "PKG-01", check=False)
        self.assertEqual(result.returncode, 2)
        self.assertIn("tasks are not all completed", result.stdout)

    def test_failed_gate_blocks_package_review_path(self):
        with tempfile.TemporaryDirectory() as td:
            state = Path(td) / "feature.json"
            run("python3", str(FEATURE_STATE), "init", "feat", "spec.md", "hash", "--state-file", str(state), "--ac", "AC-1")
            self.run_state(
                state, "create-package", "PKG-01", "Slice",
                "--ac", "AC-1", "--task", "T-001", "--task", "T-002",
                "--owned-path", "src/**", "--complexity", "medium",
            )
            self.run_state(state, "transition", "PACKAGE_IMPLEMENTATION", "--package-id", "PKG-01")
            self.run_state(state, "complete-task", "PKG-01", "T-001", "--actor", "implementer", "--validation", "unit")
            self.run_state(state, "complete-task", "PKG-01", "T-002", "--actor", "implementer", "--validation", "unit")
            self.run_state(state, "transition", "PACKAGE_GATES", "--package-id", "PKG-01")
            self.run_state(state, "update-package", "PKG-01", "--integrated", "true", "--diff-ref", "diff")
            self.run_state(state, "record-gate", "package verify", "fail", "--package-id", "PKG-01")
            nxt = self.run_state(state, "next")
            self.assertIn("PACKAGE_IMPLEMENTATION", nxt.stdout)
            result = self.run_state(state, "transition", "PACKAGE_REVIEW", "--package-id", "PKG-01", check=False)
        self.assertEqual(result.returncode, 2)
        self.assertIn("required gates", result.stdout)

    def test_gate_failure_budget_blocks(self):
        # The gates<->implementation loop used to have no cap of its own; repeated
        # gate failures must now hit a hard budget instead of burning spawns.
        with tempfile.TemporaryDirectory() as td:
            state = Path(td) / "feature.json"
            run("python3", str(FEATURE_STATE), "init", "feat", "spec.md", "hash", "--state-file", str(state), "--ac", "AC-1")
            self.run_state(
                state, "create-package", "PKG-01", "Slice",
                "--ac", "AC-1", "--task", "T-001", "--task", "T-002",
                "--owned-path", "src/**", "--complexity", "medium",
            )
            self.run_state(state, "transition", "PACKAGE_IMPLEMENTATION", "--package-id", "PKG-01")
            self.run_state(state, "complete-task", "PKG-01", "T-001", "--actor", "implementer", "--validation", "unit")
            self.run_state(state, "complete-task", "PKG-01", "T-002", "--actor", "implementer", "--validation", "unit")
            self.run_state(state, "transition", "PACKAGE_GATES", "--package-id", "PKG-01")
            for attempt in range(1, 4):
                self.run_state(state, "record-gate", "package verify", "fail",
                               "--package-id", "PKG-01", "--evidence", f"failure {attempt}")
            data = json.loads(state.read_text())
        self.assertEqual(data["phase"], "BLOCKED")
        self.assertIn("gate failure budget exhausted", json.dumps(data["blockers"]))
        self.assertEqual(data["packages"][0]["attempts"]["gate_failures"], 3)

    def test_skip_delta_requires_low_severity_and_small_diff(self):
        # Legal waiver: all findings <= medium and <= 3 changed files.
        with tempfile.TemporaryDirectory() as td:
            state = self.create_ready_package(td, review=False)
            finding = json.dumps({"id": "F-101", "severity": "medium", "category": "testing"})
            self.run_state(state, "record-review", "PKG-01", "repair_required",
                           "--actor", "package-reviewer", "--finding", finding)
            self.run_state(state, "record-repair", "PKG-01", "--actor", "repair-agent",
                           "--finding-id", "F-101", "--changed-file", "src/a.py", "--skip-delta")
            data = json.loads(state.read_text())
            self.assertEqual(data["phase"], "PACKAGE_TESTING")
            self.assertTrue(data["packages"][0]["repairs"][-1]["delta_waived"])
        # Illegal waiver: a high-severity finding rejects --skip-delta.
        with tempfile.TemporaryDirectory() as td:
            state = self.create_ready_package(td)
            result = self.run_state(state, "record-repair", "PKG-01", "--actor", "repair-agent",
                                    "--finding-id", "F-001", "--finding-id", "F-002",
                                    "--changed-file", "src/a.py", "--skip-delta", check=False)
            self.assertEqual(result.returncode, 2)
            self.assertIn("skip-delta", result.stdout)
            data = json.loads(state.read_text())
            self.assertEqual(data["phase"], "PACKAGE_REPAIR")
        # Illegal waiver: more than 3 changed files rejects --skip-delta.
        with tempfile.TemporaryDirectory() as td:
            state = self.create_ready_package(td, review=False)
            finding = json.dumps({"id": "F-101", "severity": "low", "category": "style"})
            self.run_state(state, "record-review", "PKG-01", "repair_required",
                           "--actor", "package-reviewer", "--finding", finding)
            files = [arg for i in range(4) for arg in ("--changed-file", f"src/f{i}.py")]
            result = self.run_state(state, "record-repair", "PKG-01", "--actor", "repair-agent",
                                    "--finding-id", "F-101", *files, "--skip-delta", check=False)
            self.assertEqual(result.returncode, 2)
            self.assertIn("3 changed files", result.stdout)

    def test_non_runtime_waiver_requires_independent_signer(self):
        def drive_to_testing(state, extra_create_args=()):
            self.run_state(
                state, "create-package", "PKG-01", "Slice",
                "--ac", "AC-1", "--task", "T-001", "--task", "T-002",
                "--owned-path", "src/**", "--complexity", "medium", *extra_create_args,
            )
            self.run_state(state, "transition", "PACKAGE_IMPLEMENTATION", "--package-id", "PKG-01")
            for task_id in ("T-001", "T-002"):
                self.run_state(state, "complete-task", "PKG-01", task_id, "--actor", "implementer", "--validation", "unit")
            self.run_state(state, "transition", "PACKAGE_GATES", "--package-id", "PKG-01")
            self.run_state(state, "record-gate", "package verify", "pass", "--package-id", "PKG-01", "--evidence", "ok")
            self.run_state(state, "update-package", "PKG-01", "--integrated", "true", "--diff-ref", "diff")
            self.run_state(state, "transition", "PACKAGE_REVIEW", "--package-id", "PKG-01")
            self.run_state(state, "record-review", "PKG-01", "pass", "--actor", "package-reviewer")
            self.run_state(state, "record-testing", "PKG-01", "pass", "--actor", "gate-runner", "--command", "verify")

        # Declared non-runtime package: testing alone no longer auto-waives runtime QA.
        with tempfile.TemporaryDirectory() as td:
            state = Path(td) / "feature.json"
            run("python3", str(FEATURE_STATE), "init", "feat", "spec.md", "hash", "--state-file", str(state), "--ac", "AC-1")
            drive_to_testing(state, ("--runtime-surface", "false"))
            data = json.loads(state.read_text())
            self.assertEqual(data["packages"][0]["status"], "runtime_qa_required")
            self.assertFalse(data["packages"][0]["runtime_qa"])
            # The planner that scoped the risk cannot sign its own waiver.
            result = self.run_state(state, "confirm-runtime-waiver", "PKG-01", "--actor", "package-planner", check=False)
            self.assertEqual(result.returncode, 2)
            self.assertIn("independent reviewer", result.stdout)
            # An independent reviewer can.
            self.run_state(state, "confirm-runtime-waiver", "PKG-01", "--actor", "package-reviewer", "--reason", "pure library slice")
            data = json.loads(state.read_text())
            self.assertEqual(data["packages"][0]["status"], "accept_ready")
            self.assertTrue(data["packages"][0]["runtime_qa"][-1]["waived"])
            self.assertEqual(data["packages"][0]["runtime_qa"][-1]["confirmed_by"], "package-reviewer")
            self.run_state(state, "accept-package", "PKG-01", "--actor", "orchestrator")
            data = json.loads(state.read_text())
            self.assertEqual(data["phase"], "PACKAGE_ACCEPTED")
        # A runtime-surface package cannot be waived; acceptance demands real runtime QA.
        with tempfile.TemporaryDirectory() as td:
            state = Path(td) / "feature.json"
            run("python3", str(FEATURE_STATE), "init", "feat", "spec.md", "hash", "--state-file", str(state), "--ac", "AC-1")
            drive_to_testing(state)
            result = self.run_state(state, "confirm-runtime-waiver", "PKG-01", "--actor", "package-reviewer", check=False)
            self.assertEqual(result.returncode, 2)
            self.assertIn("declares a runtime surface", result.stdout)
            result = self.run_state(state, "accept-package", "PKG-01", "--actor", "orchestrator", check=False)
            self.assertEqual(result.returncode, 2)
            self.assertIn("runtime QA", result.stdout)

    def test_required_gate_floor_blocks_review(self):
        with tempfile.TemporaryDirectory() as td:
            state = Path(td) / "feature.json"
            run("python3", str(FEATURE_STATE), "init", "feat", "spec.md", "hash", "--state-file", str(state), "--ac", "AC-1")
            self.run_state(
                state, "create-package", "PKG-01", "Slice",
                "--ac", "AC-1", "--task", "T-001", "--task", "T-002",
                "--owned-path", "src/**", "--complexity", "medium",
            )
            self.run_state(state, "transition", "PACKAGE_IMPLEMENTATION", "--package-id", "PKG-01")
            for task_id in ("T-001", "T-002"):
                self.run_state(state, "complete-task", "PKG-01", task_id, "--actor", "implementer", "--validation", "unit")
            self.run_state(state, "transition", "PACKAGE_GATES", "--package-id", "PKG-01")
            # A gate that proves nothing about typecheck/test/lint does not satisfy the floor.
            self.run_state(state, "record-gate", "smoke check", "pass", "--package-id", "PKG-01", "--evidence", "ok")
            self.run_state(state, "update-package", "PKG-01", "--integrated", "true", "--diff-ref", "diff")
            result = self.run_state(state, "transition", "PACKAGE_REVIEW", "--package-id", "PKG-01", check=False)
            self.assertEqual(result.returncode, 2)
            self.assertIn("minimum gate floor", result.stdout)
            # A passing verify gate (verify.sh runs lint+typecheck+test+build) clears the floor.
            self.run_state(state, "record-gate", "package verify", "pass", "--package-id", "PKG-01", "--evidence", "ok")
            self.run_state(state, "transition", "PACKAGE_REVIEW", "--package-id", "PKG-01")
            data = json.loads(state.read_text())
            self.assertEqual(data["phase"], "PACKAGE_REVIEW")

    def test_gate_cache_hit_short_circuits(self):
        with tempfile.TemporaryDirectory() as td:
            state = Path(td) / "feature.json"
            run("python3", str(FEATURE_STATE), "init", "feat", "spec.md", "hash", "--state-file", str(state), "--ac", "AC-1")
            self.run_state(
                state, "create-package", "PKG-01", "Slice", "--ac", "AC-1",
                "--task", "T-001", "--task", "T-002", "--owned-path", "src/**", "--complexity", "medium",
            )
            self.run_state(state, "transition", "PACKAGE_IMPLEMENTATION", "--package-id", "PKG-01")
            for task_id in ("T-001", "T-002"):
                self.run_state(state, "complete-task", "PKG-01", task_id, "--actor", "implementer", "--validation", "unit")
            self.run_state(state, "transition", "PACKAGE_GATES", "--package-id", "PKG-01")
            self.run_state(
                state, "record-gate", "package verify", "pass", "--package-id", "PKG-01",
                "--evidence", "ok", "--diff-hash", "abc123",
            )
            hit = self.run_state(state, "check-gate-cache", "package verify", "--package-id", "PKG-01", "--diff-hash", "abc123")
            self.assertIn("CACHE_HIT", hit.stdout)
            # A changed diff or a different gate name is a miss.
            miss = self.run_state(state, "check-gate-cache", "package verify", "--package-id", "PKG-01", "--diff-hash", "zzz")
            self.assertIn("CACHE_MISS", miss.stdout)
            miss2 = self.run_state(state, "check-gate-cache", "other gate", "--package-id", "PKG-01", "--diff-hash", "abc123")
            self.assertIn("CACHE_MISS", miss2.stdout)
            # The cache query is read-only: it neither adds nor duplicates a gate.
            data = json.loads(state.read_text())
            verify_gates = [g for g in data["packages"][0]["gates"] if g["name"] == "package verify"]
            self.assertEqual(len(verify_gates), 1)
            self.assertEqual(verify_gates[0]["diff_hash"], "abc123")

    def test_ready_packages_schedules_disjoint_respecting_deps(self):
        with tempfile.TemporaryDirectory() as td:
            state = Path(td) / "feature.json"
            run("python3", str(FEATURE_STATE), "init", "feat", "spec.md", "hash", "--state-file", str(state),
                "--ac", "AC-1", "--ac", "AC-2", "--ac", "AC-3", "--ac", "AC-4")
            self.run_state(state, "create-package", "PKG-01", "A", "--ac", "AC-1", "--task", "T-1",
                           "--owned-path", "src/a/**", "--complexity", "small")
            self.run_state(state, "create-package", "PKG-02", "B", "--ac", "AC-2", "--task", "T-1",
                           "--owned-path", "src/b/**", "--complexity", "small", "--depends-on", "PKG-01")
            self.run_state(state, "create-package", "PKG-03", "C", "--ac", "AC-3", "--task", "T-1",
                           "--owned-path", "src/a/sub/**", "--complexity", "small")
            self.run_state(state, "create-package", "PKG-04", "D", "--ac", "AC-4", "--task", "T-1",
                           "--owned-path", "src/d/**", "--complexity", "small")
            result = json.loads(self.run_state(state, "ready-packages").stdout)
            # PKG-01 and PKG-04 have disjoint ownership and no unmet deps -> parallelizable.
            self.assertIn("PKG-01", result["ready"])
            self.assertIn("PKG-04", result["ready"])
            # PKG-02 depends on the not-yet-accepted PKG-01.
            self.assertIn("PKG-02", result["blocked_by_deps"])
            # PKG-03 (src/a/sub) overlaps PKG-01 (src/a) -> cannot run concurrently.
            self.assertIn("PKG-03", result["blocked_by_overlap"])
            self.assertNotIn("PKG-03", result["ready"])

    def test_packages_hold_independent_phases(self):
        with tempfile.TemporaryDirectory() as td:
            state = Path(td) / "feature.json"
            run("python3", str(FEATURE_STATE), "init", "feat", "spec.md", "hash", "--state-file", str(state),
                "--ac", "AC-1", "--ac", "AC-2")
            self.run_state(state, "create-package", "PKG-01", "A", "--ac", "AC-1", "--task", "T-1",
                           "--owned-path", "src/a/**", "--complexity", "small")
            self.run_state(state, "create-package", "PKG-02", "B", "--ac", "AC-2", "--task", "T-1",
                           "--owned-path", "src/b/**", "--complexity", "small")
            # Advance PKG-01 to its GATES phase.
            self.run_state(state, "transition", "PACKAGE_IMPLEMENTATION", "--package-id", "PKG-01")
            self.run_state(state, "complete-task", "PKG-01", "T-1", "--actor", "implementer", "--validation", "unit")
            self.run_state(state, "transition", "PACKAGE_GATES", "--package-id", "PKG-01")
            # Now touch PKG-02: this moves the global working phase, but must NOT disturb PKG-01.
            self.run_state(state, "transition", "PACKAGE_IMPLEMENTATION", "--package-id", "PKG-02")
            data = json.loads(state.read_text())
            pkgs = {p["package_id"]: p for p in data["packages"]}
            self.assertEqual(pkgs["PKG-01"]["phase"], "PACKAGE_GATES")
            self.assertEqual(pkgs["PKG-02"]["phase"], "PACKAGE_IMPLEMENTATION")
            # PKG-01 continues from its OWN GATES phase even though the last global op was on PKG-02.
            # If transitions used a single global phase, IMPLEMENTATION -> PACKAGE_REVIEW would be illegal.
            self.run_state(state, "record-gate", "package verify", "pass", "--package-id", "PKG-01", "--evidence", "ok")
            self.run_state(state, "update-package", "PKG-01", "--integrated", "true", "--diff-ref", "d")
            self.run_state(state, "transition", "PACKAGE_REVIEW", "--package-id", "PKG-01")
            data = json.loads(state.read_text())
            pkgs = {p["package_id"]: p for p in data["packages"]}
            self.assertEqual(pkgs["PKG-01"]["phase"], "PACKAGE_REVIEW")
            self.assertEqual(pkgs["PKG-02"]["phase"], "PACKAGE_IMPLEMENTATION")

    def test_migrate_upgrades_v1_and_validate_detects_old(self):
        with tempfile.TemporaryDirectory() as td:
            state = Path(td) / "feature.json"
            run("python3", str(FEATURE_STATE), "init", "feat", "spec.md", "hash", "--state-file", str(state), "--ac", "AC-1")
            self.run_state(state, "create-package", "PKG-01", "A", "--ac", "AC-1", "--task", "T-1",
                           "--owned-path", "src/**", "--complexity", "small")
            # Simulate a pre-v2 file: bump down and strip the per-package phase.
            data = json.loads(state.read_text())
            data["schema_version"] = 1
            for package in data["packages"]:
                package.pop("phase", None)
            state.write_text(json.dumps(data))
            # validate flags the old schema.
            result = self.run_state(state, "validate", check=False)
            self.assertEqual(result.returncode, 2)
            self.assertIn("schema_version", result.stdout)
            # migrate upgrades in place; validate then passes and every package has a phase.
            self.run_state(state, "migrate")
            migrated = json.loads(state.read_text())
            self.assertEqual(migrated["schema_version"], 2)
            self.assertEqual(migrated["packages"][0]["phase"], "PACKAGE_PLANNING")
            self.run_state(state, "validate")  # check=True: raises if it does not pass

    def test_consolidated_findings_and_delta_review_do_not_increment_full_review(self):
        with tempfile.TemporaryDirectory() as td:
            state = self.create_ready_package(td)
            self.run_state(state, "record-repair", "PKG-01", "--actor", "repair-agent", "--finding-id", "F-001", "--finding-id", "F-002")
            self.run_state(state, "record-delta-review", "PKG-01", "pass", "--actor", "delta-reviewer", "--closed-finding", "F-001", "--closed-finding", "F-002")
            data = json.loads(state.read_text())
        self.assertEqual(data["packages"][0]["reviews"][0]["findings"], ["F-001", "F-002"])
        self.assertEqual(data["packages"][0]["repairs"][0]["finding_ids"], ["F-001", "F-002"])
        self.assertEqual(data["metrics"]["package_reviews"], 1)
        self.assertEqual(data["metrics"]["delta_reviews"], 1)

    def test_retry_budget_blocks_third_review_cycle(self):
        with tempfile.TemporaryDirectory() as td:
            state = self.create_ready_package(td, max_cycles=1)
            self.run_state(state, "record-repair", "PKG-01", "--actor", "repair-agent", "--finding-id", "F-001")
            result = self.run_state(
                state, "record-delta-review", "PKG-01", "repair_required",
                "--actor", "delta-reviewer", "--requires-full-review", "--reason", "contract changed", check=False,
            )
            data = json.loads(state.read_text())
        self.assertEqual(result.returncode, 0)
        self.assertEqual(data["phase"], "BLOCKED")
        self.assertIn("deep review budget exhausted", json.dumps(data["blockers"]))

    def test_reopen_moves_blocked_back_to_planning_and_allows_new_package(self):
        with tempfile.TemporaryDirectory() as td:
            state = self.create_ready_package(td, max_cycles=1)
            self.run_state(state, "record-repair", "PKG-01", "--actor", "repair-agent", "--finding-id", "F-001")
            self.run_state(
                state, "record-delta-review", "PKG-01", "repair_required",
                "--actor", "delta-reviewer", "--requires-full-review", "--reason", "contract changed",
            )
            self.run_state(
                state, "reopen", "--reason", "split remaining scope into a new package",
                "--authorized-by", "human:agustin",
            )
            data = json.loads(state.read_text())
            self.assertEqual(data["phase"], "PACKAGE_PLANNING")
            self.assertNotIn("final_state", data)
            blocker = data["blockers"][0]
            self.assertEqual(blocker["resolved_reason"], "split remaining scope into a new package")
            self.assertEqual(blocker["resolved_by"], "human:agustin")
            self.assertEqual(data["history"][-1]["event"], "reopen")
            self.run_state(
                state, "create-package", "PKG-02", "Remaining scope",
                "--ac", "AC-1", "--task", "T-004", "--task", "T-005",
                "--owned-path", "src/**", "--complexity", "medium",
            )
            data = json.loads(state.read_text())
            self.assertEqual(len(data["packages"]), 2)
            self.assertEqual(data["packages"][1]["package_id"], "PKG-02")

    def test_reopen_requires_reason_and_authorization(self):
        with tempfile.TemporaryDirectory() as td:
            state = self.create_ready_package(td, max_cycles=1)
            self.run_state(state, "record-repair", "PKG-01", "--actor", "repair-agent", "--finding-id", "F-001")
            self.run_state(
                state, "record-delta-review", "PKG-01", "repair_required",
                "--actor", "delta-reviewer", "--requires-full-review", "--reason", "contract changed",
            )
            missing_reason = self.run_state(state, "reopen", "--authorized-by", "human:agustin", check=False)
            self.assertNotEqual(missing_reason.returncode, 0)
            missing_auth = self.run_state(state, "reopen", "--reason", "split scope", check=False)
            self.assertNotEqual(missing_auth.returncode, 0)
            data = json.loads(state.read_text())
            self.assertEqual(data["phase"], "BLOCKED")

    def test_reopen_rejected_outside_blocked_phase(self):
        with tempfile.TemporaryDirectory() as td:
            state = self.create_ready_package(td, review=False)
            result = self.run_state(
                state, "reopen", "--reason", "no real blocker", "--authorized-by", "human:agustin", check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            data = json.loads(state.read_text())
            self.assertEqual(data["phase"], "PACKAGE_REVIEW")

    def test_transition_still_rejects_leaving_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            state = self.create_ready_package(td, max_cycles=1)
            self.run_state(state, "record-repair", "PKG-01", "--actor", "repair-agent", "--finding-id", "F-001")
            self.run_state(
                state, "record-delta-review", "PKG-01", "repair_required",
                "--actor", "delta-reviewer", "--requires-full-review", "--reason", "contract changed",
            )
            result = self.run_state(
                state, "transition", "PACKAGE_PLANNING", "--package-id", "PKG-01", check=False,
            )
            self.assertNotEqual(result.returncode, 0)

    def test_cost_report_aggregates_all_three_harnesses(self):
        import sqlite3
        with tempfile.TemporaryDirectory() as td:
            home = Path(td)
            proj = "/tmp/fake-proj"
            oc = home / ".local/share/opencode"
            oc.mkdir(parents=True)
            conn = sqlite3.connect(oc / "opencode.db")
            conn.execute(
                "CREATE TABLE session (directory TEXT, model TEXT, agent TEXT, tokens_input INT,"
                " tokens_output INT, tokens_cache_read INT, tokens_cache_write INT,"
                " tokens_reasoning INT, time_updated INT)"
            )
            conn.execute(
                "INSERT INTO session VALUES (?, ?, ?, 100, 50, 10, 5, 2, 2000000000000)",
                (proj, '{"providerID": "openai", "id": "gpt-x"}', "orchestrator"),
            )
            conn.commit()
            conn.close()
            cc = home / ".claude/projects/-tmp-fake-proj"
            cc.mkdir(parents=True)
            line = json.dumps({
                "type": "assistant", "cwd": proj, "attributionAgent": "implementer",
                "message": {"model": "claude-y", "usage": {
                    "input_tokens": 30, "output_tokens": 20,
                    "cache_read_input_tokens": 7, "cache_creation_input_tokens": 3,
                }},
            })
            (cc / "s1.jsonl").write_text(line + "\n" + line + "\n")
            cx = home / ".codex"
            cx.mkdir(parents=True)
            conn = sqlite3.connect(cx / "state_5.sqlite")
            conn.execute(
                "CREATE TABLE threads (cwd TEXT, model TEXT, agent_role TEXT,"
                " tokens_used INT, updated_at INT, rollout_path TEXT)"
            )
            conn.execute("INSERT INTO threads VALUES (?, 'gpt-z', NULL, 500, 2000000000, NULL)", (proj,))
            conn.execute("INSERT INTO threads VALUES ('/other/project', 'gpt-z', NULL, 999, 2000000000, NULL)", ())
            conn.commit()
            conn.close()
            result = run("python3", str(COST_REPORT), "--home", str(home), "--project", proj)
        self.assertIn("opencode", result.stdout)
        self.assertIn("claude-code", result.stdout)
        self.assertIn("codex", result.stdout)
        self.assertIn("openai/gpt-x", result.stdout)
        self.assertNotIn("999", result.stdout)  # other project filtered out
        # totals: oc 100+50+10+5+2=167, claude (30+20+7+3)*2=120, codex 500 → 787
        self.assertIn("787", result.stdout)

    def test_init_mode_sets_physical_budgets(self):
        with tempfile.TemporaryDirectory() as td:
            state = Path(td) / "feature.json"
            run("python3", str(FEATURE_STATE), "init", "feat", "spec.md", "hash",
                "--state-file", str(state), "--ac", "AC-1", "--mode", "quick-fix")
            self.run_state(
                state, "create-package", "PKG-01", "Fix",
                "--ac", "AC-1", "--task", "T-001",
                "--owned-path", "src/**", "--complexity", "small",
            )
            data = json.loads(state.read_text())
            self.assertEqual(data["mode"], "quick-fix")
            self.assertEqual(data["budgets"]["max_spawns_per_package"], 4)
            self.assertEqual(data["budgets"]["max_deep_review_cycles"], 1)
            for role in ("implementer", "gate-runner", "gate-runner", "debugger"):
                self.run_state(state, "record-spawn", "PKG-01", role)
            result = self.run_state(state, "record-spawn", "PKG-01", "package-reviewer", check=False)
            data = json.loads(state.read_text())
        self.assertEqual(result.returncode, 0)
        self.assertEqual(data["phase"], "BLOCKED")
        # explicit flag still wins over the mode default
        with tempfile.TemporaryDirectory() as td:
            state = Path(td) / "feature.json"
            run("python3", str(FEATURE_STATE), "init", "feat", "spec.md", "hash",
                "--state-file", str(state), "--ac", "AC-1", "--mode", "quick-fix",
                "--max-spawns-per-package", "9")
            data = json.loads(state.read_text())
        self.assertEqual(data["budgets"]["max_spawns_per_package"], 9)

    def test_spawn_budget_blocks_after_limit(self):
        with tempfile.TemporaryDirectory() as td:
            state = Path(td) / "feature.json"
            run("python3", str(FEATURE_STATE), "init", "feat", "spec.md", "hash",
                "--state-file", str(state), "--ac", "AC-1", "--max-spawns-per-package", "2")
            self.run_state(
                state, "create-package", "PKG-01", "Slice",
                "--ac", "AC-1", "--task", "T-001",
                "--owned-path", "src/**", "--complexity", "small",
            )
            self.run_state(state, "record-spawn", "PKG-01", "implementer", "--purpose", "implement T-001")
            self.run_state(state, "record-spawn", "PKG-01", "gate-runner", "--purpose", "package gates")
            result = self.run_state(state, "record-spawn", "PKG-01", "package-reviewer", check=False)
            data = json.loads(state.read_text())
        self.assertEqual(result.returncode, 0)
        self.assertEqual(data["phase"], "BLOCKED")
        self.assertIn("spawn budget exhausted", json.dumps(data["blockers"]))
        self.assertEqual(data["packages"][0]["attempts"]["spawns"], 2)

    def test_accept_package_rejects_open_findings_and_bad_actors(self):
        with tempfile.TemporaryDirectory() as td:
            state = self.create_ready_package(td, review=False)
            finding = json.dumps({"id": "F-001", "severity": "high", "category": "correctness"})
            self.run_state(state, "record-review", "PKG-01", "pass", "--actor", "package-reviewer", "--finding", finding)
            self.run_state(state, "record-testing", "PKG-01", "pass", "--actor", "gate-runner", "--command", "verify")
            self.run_state(state, "record-runtime-qa", "PKG-01", "pass", "--actor", "runtime-verifier", "--url", "http://localhost:3000")
            result = self.run_state(state, "accept-package", "PKG-01", "--actor", "repair-agent", check=False)
        self.assertEqual(result.returncode, 2)
        self.assertIn("repair-agent cannot accept packages", result.stdout)
        self.assertIn("critical/high findings", result.stdout)

    def test_resume_and_invalid_transition_are_deterministic(self):
        with tempfile.TemporaryDirectory() as td:
            state = Path(td) / "feature.json"
            run("python3", str(FEATURE_STATE), "init", "feat", "spec.md", "hash", "--state-file", str(state), "--ac", "AC-1")
            self.run_state(
                state, "create-package", "PKG-01", "Slice",
                "--ac", "AC-1", "--task", "T-001", "--task", "T-002",
                "--owned-path", "src/**", "--complexity", "medium",
            )
            self.run_state(state, "transition", "PACKAGE_IMPLEMENTATION", "--package-id", "PKG-01")
            resume = self.run_state(state, "resume")
            invalid = self.run_state(state, "transition", "PACKAGE_ACCEPTED", "--package-id", "PKG-01", check=False)
        self.assertIn("continue local implementation", resume.stdout)
        self.assertEqual(invalid.returncode, 2)
        self.assertIn("illegal transition", invalid.stdout)

    def test_stale_revision_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            state = Path(td) / "feature.json"
            run("python3", str(FEATURE_STATE), "init", "feat", "spec.md", "hash", "--state-file", str(state), "--ac", "AC-1")
            self.run_state(
                state, "create-package", "PKG-01", "Slice",
                "--ac", "AC-1", "--task", "T-001", "--task", "T-002",
                "--owned-path", "src/**", "--complexity", "medium",
            )
            result = self.run_state(state, "transition", "PACKAGE_IMPLEMENTATION", "--package-id", "PKG-01", "--expect-revision", "0", check=False)
        self.assertEqual(result.returncode, 2)
        self.assertIn("stale revision", result.stdout)

    def test_owned_paths_gate(self):
        with tempfile.TemporaryDirectory() as td:
            state = Path(td) / "feature.json"
            data = {
                "packages": [{
                    "package_id": "PKG-01",
                    "owned_paths": ["src/**"],
                    "shared_paths": ["config/*.json"],
                    "read_only_paths": ["README.md"],
                    "approved_exceptions": [{"path": "generated/**", "status": "approved"}],
                }]
            }
            state.write_text(json.dumps(data))
            allowed = run("python3", str(CHECK_OWNED), "--state-file", str(state), "--package-id", "PKG-01", "--changed-file", "src/app.py", "--changed-file", "config/app.json")
            exception = run("python3", str(CHECK_OWNED), "--state-file", str(state), "--package-id", "PKG-01", "--changed-file", "generated/out.txt")
            out_of_scope = run("python3", str(CHECK_OWNED), "--state-file", str(state), "--package-id", "PKG-01", "--changed-file", "docs/spec.md", check=False)
            read_only = run("python3", str(CHECK_OWNED), "--state-file", str(state), "--package-id", "PKG-01", "--changed-file", "README.md", check=False)
        self.assertIn("OWNERSHIP_PASS", allowed.stdout)
        self.assertIn("OWNERSHIP_PASS", exception.stdout)
        self.assertEqual(out_of_scope.returncode, 2)
        self.assertEqual(read_only.returncode, 2)
        self.assertIn("OWNERSHIP_FAIL", out_of_scope.stdout)
        self.assertIn("read_only_violations", read_only.stdout)

    def test_active_docs_do_not_teach_task_by_task_deep_audit(self):
        active = "\n".join([
            (ROOT / "PROYECTO/prompt.md").read_text(),
            (ROOT / "PROYECTO/README.md").read_text(),
            (ROOT / "PROYECTO/docs/specs/000-ejemplo/tasks.md").read_text(),
        ])
        banned = ["/next-task T-001", "hasta AUDIT_PASS", "repetí implementar", "auditar cada tarea"]
        for pattern in banned:
            self.assertNotIn(pattern, active)


if __name__ == "__main__":
    unittest.main()
