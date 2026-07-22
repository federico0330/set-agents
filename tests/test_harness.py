import json
import os
import re
import subprocess
import sys
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

    def test_shell_scripts_parse(self):
        scripts = sorted(
            path for pattern in ("*.sh", "ai/scripts/*.sh", "PROYECTO/ai/scripts/*.sh")
            for path in ROOT.glob(pattern)
        )
        self.assertGreaterEqual(len(scripts), 5)
        for script in scripts:
            with self.subTest(script=str(script.relative_to(ROOT))):
                run("bash", "-n", str(script))

    def _bootstrap_env(self, td, tools):
        """Fake HOME + stub PATH (stubs first, system dirs for bash/coreutils)."""
        stubs = Path(td) / "stubs"
        stubs.mkdir(exist_ok=True)
        for tool in tools:
            stub = stubs / tool
            stub.write_text("#!/bin/sh\necho stub-1.0\n")
            stub.chmod(0o755)
        # Keep the SAME interpreter under the constrained PATH: on macOS
        # /usr/bin/python3 is the old CLT one (no tomllib) and would crash the app.
        python_link = stubs / "python3"
        if not python_link.exists():
            python_link.symlink_to(sys.executable)
        home = Path(td) / "home"
        home.mkdir(exist_ok=True)
        return {"PATH": f"{stubs}:/usr/bin:/bin", "HOME": str(home)}, stubs

    def test_install_sh_dry_run_plans_missing_tools(self):
        with tempfile.TemporaryDirectory() as td:
            # Virgin machine: base deps come from /usr/bin, agent CLIs are absent.
            env, _ = self._bootstrap_env(td, ())
            result = run("bash", "install.sh", "--dry-run", env=env)
            for cli in ("opencode", "claude", "codex"):
                self.assertIn(f"BOOTSTRAP_PLAN {cli}", result.stdout)
                self.assertIn(f"AUTH_NEEDED {cli}", result.stdout)
            self.assertIn("BOOTSTRAP_PLAN repo-config", result.stdout)
            self.assertIn("BOOTSTRAP_DONE", result.stdout)
            # Fully provisioned machine: everything is a skip, nothing planned.
            env, _ = self._bootstrap_env(td, ("opencode", "claude", "codex"))
            result = run("bash", "install.sh", "--dry-run", env=env)
            for cli in ("opencode", "claude", "codex"):
                self.assertIn(f"BOOTSTRAP_SKIP {cli}", result.stdout)
                self.assertNotIn(f"BOOTSTRAP_PLAN {cli}", result.stdout)
            self.assertIn("BOOTSTRAP_DONE", result.stdout)

    def test_install_sh_dry_run_never_touches_network(self):
        with tempfile.TemporaryDirectory() as td:
            env, stubs = self._bootstrap_env(td, ())
            sentinel = Path(td) / "curl-was-called"
            curl = stubs / "curl"
            # --version is a local probe, anything else means a network fetch.
            curl.write_text(
                f'#!/bin/sh\ncase "$1" in --version) echo stub-curl-1.0;; *) touch {sentinel};; esac\n'
            )
            curl.chmod(0o755)
            run("bash", "install.sh", "--dry-run", env=env)
            self.assertFalse(sentinel.exists())

    # ------------------------------------------------------- models_config
    FIXTURES = ROOT / "tests/fixtures"

    @staticmethod
    def _import(name):
        import importlib.util
        spec = importlib.util.spec_from_file_location(name, ROOT / "ai/scripts" / f"{name}.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def _models_fixture(self, td, mutate=None):
        """Load the fixture config, optionally mutate it, and write it via emit()."""
        mc = self._import("models_config")
        config = mc.load_config(self.FIXTURES / "models.toml")
        if mutate:
            mutate(config)
        path = Path(td) / "models.toml"
        path.write_text(mc.emit(config))
        return mc, path

    def test_models_config_resolves_area_and_role_override(self):
        mc = self._import("models_config")
        roles = {
            row["role"]: row
            for row in mc.load_roles("zen", self.FIXTURES / "roles.tsv", self.FIXTURES / "models.toml")
        }
        # Pure area inheritance.
        self.assertEqual(roles["implementer"]["opencode_model"], "opencode/kimi-k2.7-code")
        self.assertEqual(roles["implementer"]["codex_effort"], "medium")
        # Role override wins field by field; untouched fields fall back to the area.
        self.assertEqual(roles["debugger"]["codex_effort"], "high")
        self.assertEqual(roles["debugger"]["opencode_model"], "openai/gpt-5.4")
        self.assertEqual(roles["debugger"]["codex_model"], "gpt-5.6-terra")
        # Lane merge is per lane: the go-zen lane is not overridden for debugger.
        go = {
            row["role"]: row
            for row in mc.load_roles("go-zen", self.FIXTURES / "roles.tsv", self.FIXTURES / "models.toml")
        }
        self.assertEqual(go["debugger"]["opencode_model"], "openai/gpt-5.6-terra")

    def test_models_config_rejects_incomplete_area(self):
        with tempfile.TemporaryDirectory() as td:
            def drop_field(config):
                del config["areas"]["coord"]["codex"]
            mc, models = self._models_fixture(td, drop_field)
            with self.assertRaisesRegex(ValueError, "unresolved codex_model"):
                mc.load_roles("zen", self.FIXTURES / "roles.tsv", models)

    def test_models_config_rejects_inactive_subscription(self):
        with tempfile.TemporaryDirectory() as td:
            def drop_zen(config):
                config["subscriptions"]["zen"] = False
            mc, models = self._models_fixture(td, drop_zen)
            with self.assertRaisesRegex(ValueError, "needs the 'zen' subscription"):
                mc.load_roles("zen", self.FIXTURES / "roles.tsv", models)
            # The go-zen lane of the fixture uses no zen-subscription model: still fine.
            mc.load_roles("go-zen", self.FIXTURES / "roles.tsv", models)

    def test_models_config_rejects_orphan_role_override(self):
        with tempfile.TemporaryDirectory() as td:
            def orphan(config):
                config["roles"]["ghost-role"] = {"codex_effort": "low"}
            mc, models = self._models_fixture(td, orphan)
            with self.assertRaisesRegex(ValueError, r"roles.ghost-role.*does not match"):
                mc.load_roles("zen", self.FIXTURES / "roles.tsv", models)

    def test_models_config_rejects_legacy_roster_header(self):
        mc = self._import("models_config")
        with tempfile.TemporaryDirectory() as td:
            legacy = Path(td) / "roles.tsv"
            legacy.write_text(
                "role\tmode\ttemperature\tcapability\tduty\topencode_go\topencode_zen"
                "\topencode_local\tclaude_model\tcodex_model\tcodex_effort\n"
            )
            with self.assertRaisesRegex(ValueError, "migrated model routing"):
                mc.load_roles("zen", legacy, self.FIXTURES / "models.toml")

    def test_models_config_separation_violation(self):
        with tempfile.TemporaryDirectory() as td:
            def collide(config):
                # judge inherits the implementer's codex family -> doctrine violation
                config["areas"]["judge"]["codex"] = "gpt-5.6-terra"
            mc, models = self._models_fixture(td, collide)
            with self.assertRaisesRegex(ValueError, "separation violation"):
                mc.load_roles("zen", self.FIXTURES / "roles.tsv", models)

    def test_models_config_families_override_separation(self):
        with tempfile.TemporaryDirectory() as td:
            def collide_by_suffix(config):
                # Default family strips -mini: gpt-5.4-mini collides with gpt-5.4.
                config["areas"]["implement"]["codex"] = "gpt-5.4"
                config["areas"]["judge"]["codex"] = "gpt-5.4-mini"
            mc, models = self._models_fixture(td, collide_by_suffix)
            with self.assertRaisesRegex(ValueError, "separation violation"):
                mc.load_roles("zen", self.FIXTURES / "roles.tsv", models)

            def separate_by_family(config):
                collide_by_suffix(config)
                config["families"]["gpt-5.4-mini"] = "gpt-5.4-mini-reviewer"
            mc, models = self._models_fixture(td, separate_by_family)
            mc.load_roles("zen", self.FIXTURES / "roles.tsv", models)

    def test_models_config_emit_roundtrip(self):
        with tempfile.TemporaryDirectory() as td:
            mc, models = self._models_fixture(td)
            first = models.read_text()
            second = mc.emit(mc.load_config(models))
            self.assertEqual(first, second)
            self.assertEqual(first, (self.FIXTURES / "models.toml").read_text())

    # -------------------------------------------------------- setup-models
    def _setup_models(self, td, *args, check=False):
        """Run setup_models.py against a working copy of the repo config."""
        models = Path(td) / "models.toml"
        if not models.exists():
            models.write_text((ROOT / "models.toml").read_text())
        return run(
            "python3", "ai/scripts/setup_models.py",
            "--models", str(models), "--profile", "go-zen", *args, check=check,
        ), models

    def test_setup_models_set_and_check_roundtrip(self):
        with tempfile.TemporaryDirectory() as td:
            result, models = self._setup_models(td, "--set", "audit.codex_effort=high")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("MODELS_WRITTEN", result.stdout)
            first = models.read_text()
            self.assertIn('codex_effort = "high"', first)
            # Re-applying the same change is a byte-identical no-op (deterministic emitter).
            result, _ = self._setup_models(td, "--set", "audit.codex_effort=high")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(first, models.read_text())
            result, _ = self._setup_models(td, "--check")
            self.assertIn("MODELS_CHECK_PASS", result.stdout)

    def test_setup_models_rejects_separation_violation(self):
        with tempfile.TemporaryDirectory() as td:
            _, models = self._setup_models(td, "--status")
            before = models.read_text()
            result, _ = self._setup_models(td, "--set", "audit.codex=gpt-5.6-terra")
            self.assertEqual(result.returncode, 2)
            self.assertIn("separation violation", result.stderr)
            self.assertEqual(before, models.read_text(), "invalid change must never be written")

    def test_setup_models_drop_subscription_lists_affected(self):
        with tempfile.TemporaryDirectory() as td:
            _, models = self._setup_models(td, "--status")
            before = models.read_text()
            result, _ = self._setup_models(td, "--drop", "zen")
            self.assertEqual(result.returncode, 2)
            match = re.search(r"AFFECTED=(\d+)", result.stdout)
            self.assertIsNotNone(match)
            self.assertGreater(int(match.group(1)), 0)
            self.assertIn("MODELS_NOT_WRITTEN", result.stdout)
            self.assertEqual(before, models.read_text())
            # Dropping a subscription nothing resolves to goes through.
            result, _ = self._setup_models(td, "--drop", "ollama")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("MODELS_WRITTEN", result.stdout)

    def test_setup_models_check_validates_all_lanes(self):
        with tempfile.TemporaryDirectory() as td:
            # Break only the zen lane: judge model into the implementer family.
            result, models = self._setup_models(
                td, "--set", "judge.opencode.zen=opencode/kimi-k2.7-code",
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("separation violation", result.stderr)
            # The active profile (go-zen) alone would have validated: prove --check
            # covers every lane by checking the untouched copy still passes.
            result, _ = self._setup_models(td, "--check")
            self.assertIn("MODELS_CHECK_PASS", result.stdout)

    def test_setup_models_add_model_extends_catalog(self):
        with tempfile.TemporaryDirectory() as td:
            result, models = self._setup_models(td, "--add-model", "codex=gpt-6-nova")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('"gpt-6-nova"', models.read_text())
            result, _ = self._setup_models(td, "--check")
            self.assertIn("MODELS_CHECK_PASS", result.stdout)

    # ---------------------------------------------------------- set-agents
    GIT_ENV = {
        "GIT_AUTHOR_NAME": "test", "GIT_AUTHOR_EMAIL": "t@t",
        "GIT_COMMITTER_NAME": "test", "GIT_COMMITTER_EMAIL": "t@t",
    }

    def _fake_origin_pair(self, td):
        """Bare origin + seed pushing commits + a clone acting as the app's repo."""
        origin = Path(td) / "origin.git"
        run("git", "init", "--quiet", "--bare", "-b", "main", str(origin))
        seed = Path(td) / "seed"
        run("git", "clone", "--quiet", str(origin), str(seed))
        (seed / "file.txt").write_text("v1\n")
        run("git", "-C", str(seed), "add", ".", env=self.GIT_ENV)
        run("git", "-C", str(seed), "commit", "--quiet", "-m", "v1", env=self.GIT_ENV)
        run("git", "-C", str(seed), "push", "--quiet", "origin", "main", env=self.GIT_ENV)
        app_root = Path(td) / "app"
        run("git", "clone", "--quiet", str(origin), str(app_root))
        return seed, app_root

    def _push_commit(self, seed, content):
        (seed / "file.txt").write_text(content)
        run("git", "-C", str(seed), "commit", "--quiet", "-am", content, env=self.GIT_ENV)
        run("git", "-C", str(seed), "push", "--quiet", "origin", "main", env=self.GIT_ENV)

    def test_set_agents_update_flow(self):
        with tempfile.TemporaryDirectory() as td:
            seed, app_root = self._fake_origin_pair(td)
            env = {"SET_AGENTS_ROOT": str(app_root), "SET_AGENTS_STATE": str(Path(td) / "state")}
            result = run("bash", "set-agents", "--check-update", env=env)
            self.assertIn("UPDATE_AVAILABLE=0", result.stdout)
            self._push_commit(seed, "v2\n")
            result = run("bash", "set-agents", "--check-update", env=env)
            self.assertIn("UPDATE_AVAILABLE=1", result.stdout)
            result = run("bash", "set-agents", "--update", "--no-install", env=env)
            self.assertIn("UPDATE_APPLIED", result.stdout)
            self.assertEqual((app_root / "file.txt").read_text(), "v2\n")
            # Dirty tree must block, applied update must converge to 0.
            self._push_commit(seed, "v3\n")
            (app_root / "file.txt").write_text("local change\n")
            result = run("bash", "set-agents", "--update", "--no-install", env=env, check=False)
            self.assertEqual(result.returncode, 1)
            self.assertIn("UPDATE_BLOCKED", result.stdout)

    def test_set_agents_status_and_auto_update_config(self):
        with tempfile.TemporaryDirectory() as td:
            env, _ = self._bootstrap_env(td, ())
            env["SET_AGENTS_STATE"] = str(Path(td) / "state")
            result = run("bash", "set-agents", "--auto-update", "off", env=env)
            self.assertIn("AUTO_UPDATE=off", result.stdout)
            result = run("bash", "set-agents", "--status", env=env)
            self.assertRegex(result.stdout, r"APP_STATUS sha=\S+ drift=(ok|stale|unknown) update=\S+ auto_update=off")

    def test_install_sh_creates_set_agents_link(self):
        with tempfile.TemporaryDirectory() as td:
            env, _ = self._bootstrap_env(td, ("opencode", "claude", "codex"))
            result = run("bash", "install.sh", "--dry-run", env=env)
            self.assertIn("BOOTSTRAP_PLAN set-agents-link", result.stdout)
            result = run(
                "bash", "install.sh", "--skip-deps", "--skip-auth", "--no-install", "--yes",
                env=env,
            )
            self.assertIn("BOOTSTRAP_OK set-agents-link", result.stdout)
            link = Path(env["HOME"]) / ".local/bin/set-agents"
            self.assertEqual(link.resolve(), ROOT / "set-agents")
            result = run(
                "bash", "install.sh", "--skip-deps", "--skip-auth", "--no-install", "--yes",
                env=env,
            )
            self.assertIn("BOOTSTRAP_SKIP set-agents-link", result.stdout)

    def test_set_agents_tools_catalog(self):
        with tempfile.TemporaryDirectory() as td:
            env, stubs = self._bootstrap_env(td, ("npm", "jq"))
            sentinel = Path(td) / "curl-was-called"
            curl = stubs / "curl"
            curl.write_text(f"#!/bin/sh\ntouch {sentinel}\n")
            curl.chmod(0o755)
            env["SET_AGENTS_STATE"] = str(Path(td) / "state")
            result = run("bash", "set-agents", "--tools", env=env)
            self.assertIn("TOOL jq installed=yes", result.stdout)
            self.assertIn("TOOL supabase installed=no", result.stdout)
            self.assertIn("TOOL vercel installed=no", result.stdout)
            # Dry-run plans the right method and never fetches anything.
            result = run("bash", "set-agents", "--tools-install", "vercel", "--dry-run", env=env)
            self.assertIn("TOOL_PLAN vercel method=npm", result.stdout)
            # supabase has no automatable method on Linux (npm global is blocked upstream).
            result = run("bash", "set-agents", "--tools-install", "supabase", env=env, check=False)
            self.assertEqual(result.returncode, 1)
            self.assertIn("TOOL_MANUAL supabase", result.stdout)
            result = run("bash", "set-agents", "--tools-install", "jq", "--dry-run", env=env)
            self.assertIn("TOOL_SKIP jq", result.stdout)
            result = run("bash", "set-agents", "--tools-install", "ghost", env=env, check=False)
            self.assertEqual(result.returncode, 2)
            self.assertIn("TOOL_UNKNOWN", result.stdout)
            self.assertFalse(sentinel.exists())

    def _mcp_home(self, td):
        """Fake HOME with all five MCP targets present (CLIs stubbed on PATH)."""
        env, _ = self._bootstrap_env(td, ("opencode", "claude", "codex", "gemini"))
        home = Path(env["HOME"])
        (home / ".config/opencode").mkdir(parents=True, exist_ok=True)
        (home / ".config/opencode/opencode.json").write_text('{"mcp": {}}\n')
        (home / ".codex").mkdir(exist_ok=True)
        (home / ".codex/config.toml").write_text('[features]\nmulti_agent = true\n')
        (home / ".cursor").mkdir(exist_ok=True)
        env["SET_AGENTS_STATE"] = str(Path(td) / "state")
        return env, home

    def test_set_agents_mcp_across_harnesses(self):
        with tempfile.TemporaryDirectory() as td:
            env, home = self._mcp_home(td)
            result = run("bash", "set-agents", "--mcp-add", "supabase", env=env)
            for harness in ("opencode", "claude", "codex", "cursor", "gemini"):
                self.assertIn(f"MCP_ADDED supabase harness={harness}", result.stdout)
            oc = json.loads((home / ".config/opencode/opencode.json").read_text())
            self.assertFalse(oc["mcp"]["supabase"]["enabled"], "opencode adds disabled per policy")
            self.assertEqual(oc["mcp"]["supabase"]["command"][0], "npx")
            codex = tomllib.loads((home / ".codex/config.toml").read_text())
            self.assertFalse(codex["mcp_servers"]["supabase"]["enabled"])
            self.assertTrue(codex["features"]["multi_agent"], "existing sections preserved")
            claude = json.loads((home / ".claude.json").read_text())
            self.assertEqual(claude["mcpServers"]["supabase"]["command"], "npx")
            self.assertIn("supabase", json.loads((home / ".cursor/mcp.json").read_text())["mcpServers"])
            # Toggle on/off where the format supports it.
            result = run("bash", "set-agents", "--mcp-on", "supabase", "--harness", "opencode", env=env)
            self.assertIn("MCP_SET supabase harness=opencode state=on", result.stdout)
            result = run("bash", "set-agents", "--mcp-off", "supabase", "--harness", "codex", env=env)
            self.assertIn("MCP_SET supabase harness=codex state=off", result.stdout)
            # claude off == removed; managed servers stay off-limits on opencode.
            result = run("bash", "set-agents", "--mcp-off", "supabase", "--harness", "claude", env=env)
            self.assertIn("MCP_SET supabase harness=claude state=absent", result.stdout)
            result = run("bash", "set-agents", "--mcp-add", "context7", "--harness", "opencode", env=env)
            self.assertIn("MCP_MANAGED context7", result.stdout)
            self.assertNotIn("context7", json.loads((home / ".config/opencode/opencode.json").read_text())["mcp"])
            # Remove cleans up and backups exist for touched files.
            run("bash", "set-agents", "--mcp-remove", "supabase", env=env)
            result = run("bash", "set-agents", "--mcp", env=env)
            self.assertNotIn("supabase harness=opencode state=off", result.stdout)
            for line in result.stdout.splitlines():
                if line.startswith("MCP supabase"):
                    self.assertIn("state=absent", line)
            self.assertTrue((home / ".config/opencode/opencode.json.bak").exists())

    def test_set_agents_plugins(self):
        with tempfile.TemporaryDirectory() as td:
            env, home = self._mcp_home(td)
            (home / ".claude").mkdir(exist_ok=True)
            (home / ".claude/settings.json").write_text(json.dumps({"enabledPlugins": {"foo@bar": True}}))
            result = run("bash", "set-agents", "--plugins", env=env)
            self.assertIn("PLUGIN foo@bar enabled=true", result.stdout)
            result = run("bash", "set-agents", "--plugin-off", "foo@bar", env=env)
            self.assertIn("PLUGIN_SET foo@bar enabled=false", result.stdout)
            settings = json.loads((home / ".claude/settings.json").read_text())
            self.assertFalse(settings["enabledPlugins"]["foo@bar"])
            result = run("bash", "set-agents", "--plugin-on", "engram@engram", env=env, check=False)
            self.assertEqual(result.returncode, 1)
            self.assertIn("PLUGIN_MANAGED", result.stdout)

    def test_set_agents_launcher_resolves_symlink_without_readlink_f(self):
        # macOS has no `readlink -f`: the launcher must resolve its own symlink chain.
        with tempfile.TemporaryDirectory() as td:
            link = Path(td) / "bin" / "set-agents"
            link.parent.mkdir()
            link.symlink_to(ROOT / "set-agents")
            env = {"SET_AGENTS_STATE": str(Path(td) / "state")}
            result = run("bash", str(link), "--status", env=env)
            self.assertIn("APP_STATUS", result.stdout)

    def test_install_sh_redirects_windows_gitbash_to_ps1(self):
        with tempfile.TemporaryDirectory() as td:
            env, stubs = self._bootstrap_env(td, ())
            uname = stubs / "uname"
            uname.write_text('#!/bin/sh\necho MINGW64_NT-10.0-19045\n')
            uname.chmod(0o755)
            result = run("bash", "install.sh", "--dry-run", env=env, check=False)
            self.assertEqual(result.returncode, 2)
            self.assertIn("install.ps1", result.stdout)

    def test_windows_bootstrap_artifacts(self):
        ps1 = (ROOT / "install.ps1").read_text()
        for marker in ("PS_PLAN", "PS_SKIP", "PS_NEED_ADMIN", "BOOTSTRAP_DONE_WINDOWS",
                       "gh auth login", "gh repo clone federico0330/SET-AGENTS", "[switch]$DryRun",
                       # invisibility upgrades: self-elevation, reboot auto-resume, auto user
                       "-Verb RunAs", "RunOnce", "/etc/wsl.conf", "sudoers.d/set-agents",
                       "README.md"):
            self.assertIn(marker, ps1)
        cmd = (ROOT / "set-agents.cmd").read_text()
        self.assertIn('wsl -e bash -lc "\\"$HOME/SET-AGENTS/set-agents\\" \\"$@\\"" set-agents %*', cmd)
        import shutil as _shutil
        if _shutil.which("pwsh"):
            # Full syntax validation when PowerShell Core is available locally;
            # CI's windows job always does this regardless.
            run("pwsh", "-NoProfile", "-Command",
                f"$null = [ScriptBlock]::Create((Get-Content -Raw '{ROOT / 'install.ps1'}'))")

    def test_readme_covers_all_oses(self):
        readme = (ROOT / "README.md").read_text()
        for section in ("Windows", "Linux", "macOS", "WSL", "Qué vas a ver la primera vez",
                        "UAC", "sudoers.d/set-agents", "gh auth login"):
            self.assertIn(section, readme)
        result = run("bash", "set-agents", "--help")
        self.assertIn("README.md", result.stdout)

    def test_banner_degrades_without_tty(self):
        with tempfile.TemporaryDirectory() as td:
            env, _ = self._bootstrap_env(td, ())
            env["SET_AGENTS_STATE"] = str(Path(td) / "state")
            for flags in (["--status"], ["--help"], ["--tools"]):
                result = run("bash", "set-agents", *flags, env=env)
                self.assertNotIn("\x1b[", result.stdout, f"ANSI leaked into non-TTY output of {flags}")

    # ---------------------------------------------------------- living notes
    def _notes_project(self, td):
        """Canonical project layout: ai/state/features + docs/notas, one feature."""
        root = Path(td)
        (root / "docs/notas").mkdir(parents=True)
        state = root / "ai/state/features/feat-x.json"
        state.parent.mkdir(parents=True)
        run("python3", str(FEATURE_STATE), "init", "feat-x", "docs/specs/feat-x/spec.md", "hash-abc",
            "--state-file", str(state), "--ac", "AC-1")
        run("python3", str(FEATURE_STATE), "create-package", "PKG-01", "Slice observable",
            "--state-file", str(state), "--ac", "AC-1", "--task", "T-001", "--task", "T-002",
            "--owned-path", "src/**", "--complexity", "small",
            "--selected-role", "implementer", "--selected-model", "openai/gpt-5.6-terra",
            "--routing-reason", "tareas chicas y relacionadas")
        return root, state

    def test_sync_notes_renders_hub_feature_and_package_notes(self):
        with tempfile.TemporaryDirectory() as td:
            root, state = self._notes_project(td)
            hub = (root / "docs/notas/00 - Proyecto.md").read_text()
            self.assertIn("[[features/feat-x|feat-x]]", hub)
            self.assertIn("## Qué falta", hub)
            feature = (root / "docs/notas/features/feat-x.md").read_text()
            self.assertIn("[[features/feat-x/PKG-01|PKG-01]]", feature)
            self.assertIn("hash-abc", feature)
            self.assertIn("tareas chicas y relacionadas", feature)
            package = (root / "docs/notas/features/feat-x/PKG-01.md").read_text()
            self.assertIn("- [ ] T-001 (planned)", package)
            self.assertIn("↩ [[features/feat-x|feat-x]]", package)
            result = run(
                "python3", str(FEATURE_STATE), "sync-notes",
                "--state-dir", str(root / "ai/state"),
            )
            self.assertIn("NOTES_SYNCED", result.stdout)

    def test_notes_are_idempotent_and_preserve_manual_edits(self):
        with tempfile.TemporaryDirectory() as td:
            root, state = self._notes_project(td)
            hub_path = root / "docs/notas/00 - Proyecto.md"
            run("python3", str(FEATURE_STATE), "sync-notes", "--state-dir", str(root / "ai/state"))
            first = hub_path.read_bytes()
            run("python3", str(FEATURE_STATE), "sync-notes", "--state-dir", str(root / "ai/state"))
            self.assertEqual(first, hub_path.read_bytes(), "sync-notes must be byte-idempotent")
            hub_path.write_text(hub_path.read_text() + "\nMi apunte del café.\n")
            run("python3", str(FEATURE_STATE), "sync-notes", "--state-dir", str(root / "ai/state"))
            after = hub_path.read_text()
            self.assertIn("Mi apunte del café.", after, "manual text outside the auto block must survive")

    def test_notes_autorender_on_state_mutation_and_optin_by_dir(self):
        with tempfile.TemporaryDirectory() as td:
            root, state = self._notes_project(td)
            package_note = root / "docs/notas/features/feat-x/PKG-01.md"
            self.assertIn("- [ ] T-001", package_note.read_text())
            run("python3", str(FEATURE_STATE), "transition", "PACKAGE_IMPLEMENTATION",
                "--package-id", "PKG-01", "--state-file", str(state))
            run("python3", str(FEATURE_STATE), "complete-task", "PKG-01", "T-001",
                "--actor", "implementer", "--validation", "focused-test", "--state-file", str(state))
            self.assertIn("- [x] T-001 (completed)", package_note.read_text(),
                          "a state mutation must refresh notes without calling sync-notes")
        with tempfile.TemporaryDirectory() as td:
            # No docs/notas/ -> strictly opt-in, nothing gets created.
            root = Path(td)
            state = root / "ai/state/features/feat-y.json"
            state.parent.mkdir(parents=True)
            run("python3", str(FEATURE_STATE), "init", "feat-y", "spec.md", "h",
                "--state-file", str(state), "--ac", "AC-1")
            self.assertFalse((root / "docs/notas").exists())

    def test_log_decision_appends_and_renders_note(self):
        with tempfile.TemporaryDirectory() as td:
            root, state = self._notes_project(td)
            log = root / "ai/state/decisions-log.jsonl"
            for _ in range(2):  # second run must dedupe
                result = run(
                    "python3", str(FEATURE_STATE), "log-decision",
                    "--title", "SQLite y no Postgres", "--context", "proyecto chico, un solo host",
                    "--decision", "usamos SQLite embebido", "--consequences", "migrar si crece",
                    "--feature-id", "feat-x", "--log-file", str(log),
                )
            self.assertIn('"deduped": true', result.stdout)
            self.assertEqual(len(log.read_text().strip().splitlines()), 1)
            notes = list((root / "docs/notas/decisiones").glob("* sqlite-y-no-postgres.md"))
            self.assertEqual(len(notes), 1)
            body = notes[0].read_text()
            self.assertIn("[[features/feat-x|feat-x]]", body)
            self.assertIn("usamos SQLite embebido", body)
            feature = (root / "docs/notas/features/feat-x.md").read_text()
            self.assertIn("SQLite y no Postgres", feature)

    def test_vault_init_seeds_company_vault(self):
        with tempfile.TemporaryDirectory() as td:
            env = {"SET_AGENTS_STATE": str(Path(td) / "state")}
            company = Path(td) / "empresa"
            result = run("bash", "set-agents", "--vault-init", str(company), "--company", "IEY", env=env)
            self.assertIn("VAULT_INIT_OK", result.stdout)
            hub = company / "obsidian/00 - INICIO.md"
            for section in ("## Rol", "## Forma de trabajo", "## Entrega de resultados", "## Qué falta por proyecto"):
                self.assertIn(section, hub.read_text())
            self.assertTrue((company / "obsidian/IEY/contexto.md").exists())
            self.assertTrue((company / "obsidian/Proyectos").is_dir())
            # Re-run never clobbers manual edits.
            hub.write_text(hub.read_text().replace("_TODO: quién sos", "Soy el dev principal"))
            result = run("bash", "set-agents", "--vault-init", str(company), "--company", "IEY", env=env)
            self.assertIn("VAULT_INIT_SKIP", result.stdout)
            self.assertIn("Soy el dev principal", hub.read_text())

    def test_vault_link_creates_seed_and_symlink(self):
        with tempfile.TemporaryDirectory() as td:
            env = {"SET_AGENTS_STATE": str(Path(td) / "state")}
            company = Path(td) / "empresa"
            run("bash", "set-agents", "--vault-init", str(company), env=env)
            project = company / "mi-app"
            project.mkdir()
            result = run("bash", "set-agents", "--vault-link", str(project), env=env)
            self.assertIn("VAULT_LINK_OK", result.stdout)
            seed = project / "docs/notas/00 - Proyecto.md"
            self.assertIn("notas:auto", seed.read_text())
            link = company / "obsidian/Proyectos/mi-app"
            self.assertTrue(link.is_symlink())
            self.assertEqual(link.resolve(), seed.parent.resolve())
            result = run("bash", "set-agents", "--vault-link", str(project), env=env)
            self.assertIn("VAULT_LINK_SKIP", result.stdout)
            # A link pointing elsewhere is never clobbered.
            other = Path(td) / "otro"
            other.mkdir()
            link.unlink()
            link.symlink_to(other)
            result = run("bash", "set-agents", "--vault-link", str(project), env=env, check=False)
            self.assertEqual(result.returncode, 1)
            self.assertIn("VAULT_LINK_CONFLICT", result.stdout)
            # End to end with the notes engine: a real feature renders through the symlink.
            link.unlink()
            link.symlink_to(seed.parent)
            state = project / "ai/state/features/feat-v.json"
            state.parent.mkdir(parents=True)
            run("python3", str(FEATURE_STATE), "init", "feat-v", "spec.md", "h",
                "--state-file", str(state), "--ac", "AC-1")
            self.assertIn("[[features/feat-v|feat-v]]", (link / "00 - Proyecto.md").read_text())

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
        models_before = (ROOT / "models.toml").read_bytes()
        with tempfile.TemporaryDirectory() as td:
            run("./build.sh", "--profile", "zen", "--output", td)
        self.assertEqual(before, (ROOT / "roles.tsv").read_bytes())
        self.assertEqual(models_before, (ROOT / "models.toml").read_bytes())

    def test_local_profile_generates_and_validates(self):
        # The `local` profile (leaf agents on Ollama, judgment roles hosted) must
        # generate and pass separation-of-duties just like go-zen/zen.
        with tempfile.TemporaryDirectory() as td:
            result = run("python3", "ai/scripts/generate.py", "--profile", "local",
                         "--output", str(Path(td) / "out"), check=False)
            self.assertEqual(result.returncode, 0, result.stderr)

    def _repo_models_variant(self, td, mutate):
        """Copy the repo's models.toml with a mutation, via the deterministic emitter."""
        mc = self._import("models_config")
        config = mc.load_config(ROOT / "models.toml")
        mutate(config)
        path = Path(td) / "models.toml"
        path.write_text(mc.emit(config))
        return path

    def test_invalid_separation_graph_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            def judge_on_implementer_model(config):
                config["areas"]["judge"]["opencode"]["go-zen"] = "openai/gpt-5.6-terra"
            models = self._repo_models_variant(td, judge_on_implementer_model)
            result = run("python3", "ai/scripts/generate.py", "--profile", "go-zen", "--output", str(Path(td) / "out"), "--models", str(models), check=False)
        self.assertEqual(result.returncode, 2)
        self.assertIn("separation violation", result.stderr)

        mutating_reviewer = (ROOT / "roles.tsv").read_text().replace(
            "package-reviewer\tsubagent\t0.0\treview-ro\taudit",
            "package-reviewer\tsubagent\t0.0\tcode-rw\taudit",
        )
        with tempfile.TemporaryDirectory() as td:
            roles = Path(td) / "roles.tsv"
            roles.write_text(mutating_reviewer)
            result = run("python3", "ai/scripts/generate.py", "--profile", "go-zen", "--output", str(Path(td) / "out"), "--roles", str(roles), check=False)
        self.assertEqual(result.returncode, 2)
        self.assertIn("mutating capability", result.stderr)

        with tempfile.TemporaryDirectory() as td:
            def audit_on_implementer_codex(config):
                config["areas"]["audit"]["codex"] = "gpt-5.6-terra"
            models = self._repo_models_variant(td, audit_on_implementer_codex)
            result = run("python3", "ai/scripts/generate.py", "--profile", "go-zen", "--output", str(Path(td) / "out"), "--models", str(models), check=False)
        self.assertEqual(result.returncode, 2)
        self.assertIn("gpt-5.6-terra", result.stderr)

    def test_roles_tsv_with_model_columns_rejected_with_hint(self):
        legacy_header = "\t".join([
            "role", "mode", "temperature", "capability", "duty", "opencode_go",
            "opencode_zen", "opencode_local", "claude_model", "codex_model", "codex_effort",
        ])
        legacy_row = "\t".join([
            "orchestrator", "primary", "0.1", "coord-ro", "coord", "openai/gpt-5.6-terra",
            "openai/gpt-5.4", "openai/gpt-5.4", "fable", "gpt-5.6-terra", "high",
        ])
        with tempfile.TemporaryDirectory() as td:
            roles = Path(td) / "roles.tsv"
            roles.write_text(legacy_header + "\n" + legacy_row + "\n")
            result = run("python3", "ai/scripts/generate.py", "--profile", "go-zen", "--output", str(Path(td) / "out"), "--roles", str(roles), check=False)
        self.assertEqual(result.returncode, 2)
        self.assertIn("models.toml", result.stderr)

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
            oc_settings.write_text(json.dumps({
                "plugin": ["custom"],
                # playwright is managed (must land disabled); supabase is the user's own
                # server and must survive the install still enabled.
                "mcp": {"playwright": {"enabled": True}, "supabase": {"type": "local", "enabled": True}},
            }))
            (home / ".codex/config.toml").write_text('[agents]\nmax_threads = 9\n\n[mcp_servers.playwright]\ncommand = "npx"\nenabled = true\n')
            run("./build.sh", "--output", staging_dir)
            run("python3", "ai/scripts/install.py", "--staging", staging_dir, "--home", td)
            self.assertEqual(unrelated.read_text(), "keep\n")
            self.assertTrue(json.loads(claude_settings.read_text())["enabledPlugins"]["custom@local"])
            self.assertFalse(json.loads(claude_settings.read_text())["enabledPlugins"]["engram@engram"])
            self.assertEqual(json.loads(oc_settings.read_text())["plugin"], ["custom"])
            oc_mcp = json.loads(oc_settings.read_text())["mcp"]
            self.assertFalse(oc_mcp["playwright"]["enabled"])
            self.assertTrue(oc_mcp["supabase"]["enabled"], "user MCP must stay enabled and not fail smoke")
            # Installed config must be machine-portable: no placeholder, no federico path,
            # brave-cdp resolved to THIS repo's root, engram resolved via PATH.
            raw = oc_settings.read_text()
            self.assertNotIn("__SET_AGENTS_ROOT__", raw)
            self.assertNotIn("/home/federico/.local/bin/engram", raw)
            self.assertEqual(oc_mcp["engram"]["command"][0], "engram")
            self.assertEqual(
                oc_mcp["brave-cdp"]["command"][0],
                str(ROOT / "PROYECTO/ai/scripts/brave-cdp-mcp.sh"),
            )
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

    def test_rpl_p0a_package_gate_runner_is_opencode_only_and_strictly_scoped(self):
        run("./build.sh")
        agent = ROOT / "Global/opencode/agents/package-gate-runner.md"
        text = agent.read_text()
        self.assertTrue(agent.exists())
        self.assertFalse((ROOT / "Global/claude-code/agents/package-gate-runner.md").exists())
        self.assertFalse((ROOT / "Global/codex/agents/package-gate-runner.toml").exists())

        catch_all = text.index('    "*": deny', text.index("  bash:"))
        ownership = text.index(
            '    "python3 ai/scripts/check-owned-paths.py --state-file '
            '/home/federico/iey/iey-ai/ai/state/features/replenishment-v2.json '
            '--package-id RPL-P0A --baseline 4ef70b0ab6da": allow'
        )
        self.assertLess(catch_all, ownership)
        self.assertIn('    "git *": deny', text)
        self.assertLess(text.index('    "git *": deny'), text.index('    "git status": allow'))
        self.assertIn('    "git log --oneline -5": allow', text)
        self.assertIn(
            '    "/tmp/opencode/rpl-p0a-gates-4ef70b0ab6da/**": allow', text
        )
        self.assertIn(
            '    "/home/federico/iey/iey-ai/ai/state/features/replenishment-v2.json": allow', text
        )
        self.assertIn(
            '    "NODE_PATH=/home/federico/iey/iey-ai/node_modules '
            '/home/federico/iey/iey-ai/node_modules/.bin/prisma validate": allow', text
        )
        self.assertIn(
            '    "NODE_PATH=/home/federico/iey/iey-ai/node_modules '
            '/home/federico/iey/iey-ai/node_modules/.bin/vitest run '
            'src/lib/modules/contabilium-ingestion/repositories/__tests__/'
            'ledger-rls.integration.test.ts": allow', text
        )
        self.assertIn("record-gate replenishment-v2 --description *", text)
        self.assertIn('    "*--next-id*": deny', text)
        self.assertIn('    "*verify.sh*": deny', text)
        self.assertNotIn('    "*verify.sh*": allow', text)
        self.assertNotIn('    "NODE_PATH=*', text)

        orchestrator = (ROOT / "Global/opencode/agents/orchestrator.md").read_text()
        self.assertIn('    "package-gate-runner": allow', orchestrator)
        self.assertIn("For `replenishment-v2` package `RPL-P0A` only", orchestrator)
        self.assertNotIn(
            "package-gate-runner",
            (ROOT / "Global/claude-code/agents/orchestrator.md").read_text(),
        )
        self.assertNotIn(
            "package-gate-runner",
            tomllib.loads((ROOT / "Global/codex/agents/orchestrator.toml").read_text())["developer_instructions"],
        )

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

    def test_non_runtime_package_accepts_without_runtime_qa(self):
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

        # Declared non-runtime package: accept-ready after testing, runtime QA waived.
        with tempfile.TemporaryDirectory() as td:
            state = Path(td) / "feature.json"
            run("python3", str(FEATURE_STATE), "init", "feat", "spec.md", "hash", "--state-file", str(state), "--ac", "AC-1")
            drive_to_testing(state, ("--runtime-surface", "false"))
            data = json.loads(state.read_text())
            self.assertEqual(data["packages"][0]["status"], "accept_ready")
            self.assertTrue(data["packages"][0]["runtime_qa"][-1]["waived"])
            self.run_state(state, "accept-package", "PKG-01", "--actor", "orchestrator")
            data = json.loads(state.read_text())
            self.assertEqual(data["phase"], "PACKAGE_ACCEPTED")
        # Default (runtime surface true): acceptance still demands real runtime QA.
        with tempfile.TemporaryDirectory() as td:
            state = Path(td) / "feature.json"
            run("python3", str(FEATURE_STATE), "init", "feat", "spec.md", "hash", "--state-file", str(state), "--ac", "AC-1")
            drive_to_testing(state)
            result = self.run_state(state, "accept-package", "PKG-01", "--actor", "orchestrator", check=False)
            self.assertEqual(result.returncode, 2)
            self.assertIn("runtime QA", result.stdout)

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
