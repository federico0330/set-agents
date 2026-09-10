"""049 PKG-A: the per-machine models overlay reaches only local projections."""

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import tests


ROOT = Path(__file__).resolve().parents[1]


def run(*args, env=None, check=True):
    return subprocess.run(
        args, cwd=ROOT, text=True, capture_output=True, check=check,
        env={**os.environ, "PYTHONUTF8": "1", **(env or {})},
    )


def tree_bytes(root):
    """A recursive, byte-level projection that does not trust mtimes."""
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*")) if path.is_file()
    }


class EffectiveProjectionTests(unittest.TestCase):
    def setUp(self):
        tests.require_posix_toolchain()
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.state = self.root / "state"
        self.home = self.root / "home"
        self.state.mkdir()
        self.home.mkdir()
        # A legal opaque value.  It changes only the implementer's local Codex
        # agent and leaves the factory catalog and every tracked artifact alone.
        (self.state / "models.local.toml").write_text(
            '[roles.implementer]\ncodex = "gpt-5.6-luna"\n', encoding="utf-8"
        )
        self.env = {"SET_AGENTS_STATE": str(self.state), "HOME": str(self.home)}

    def test_effective_flag_changes_local_agent_but_default_is_factory(self):
        factory = self.root / "factory"
        effective = self.root / "effective"
        run(sys.executable, "ai/scripts/generate.py", "--output", str(factory), env=self.env)
        run(sys.executable, "ai/scripts/generate.py", "--output", str(effective), "--effective", env=self.env)
        factory_agent = (factory / "codex/agents/implementer.toml").read_text(encoding="utf-8")
        effective_agent = (effective / "codex/agents/implementer.toml").read_text(encoding="utf-8")
        self.assertIn('model = "gpt-5.6-terra"', factory_agent)
        self.assertIn('model = "gpt-5.6-luna"', effective_agent)

    def test_absent_overlay_is_byte_identical_to_factory(self):
        (self.state / "models.local.toml").unlink()
        factory = self.root / "factory"
        effective = self.root / "effective"
        run(sys.executable, "ai/scripts/generate.py", "--output", str(factory), env=self.env)
        run(sys.executable, "ai/scripts/generate.py", "--output", str(effective), "--effective", env=self.env)
        self.assertEqual(tree_bytes(factory), tree_bytes(effective))

    def test_build_check_and_diff_are_factory_only(self):
        checked = run("./build.sh", "--check", env=self.env)
        self.assertEqual(checked.returncode, 0, checked.stdout + checked.stderr)
        (self.state / "models.local.toml").unlink()
        baseline = run("./build.sh", "--diff", env=self.env)
        (self.state / "models.local.toml").write_text(
            '[roles.implementer]\ncodex = "gpt-5.6-luna"\n', encoding="utf-8"
        )
        shown = run("./build.sh", "--diff", env=self.env)
        self.assertEqual(shown.returncode, 0, shown.stdout + shown.stderr)
        self.assertEqual(shown.stdout, baseline.stdout,
                         "an overlay must not change Global factory diff")

    def test_drift_compares_against_effective_installation(self):
        installed = run("./build.sh", "--install", "--yes", "--target", "codex", env=self.env)
        self.assertEqual(installed.returncode, 0, installed.stdout + installed.stderr)
        agent = (self.home / ".codex/agents/implementer.toml").read_text(encoding="utf-8")
        self.assertIn('model = "gpt-5.6-luna"', agent)
        drift = run("ai/scripts/check-drift.sh", env={**self.env, "DRIFT_HOME": str(self.home)})
        self.assertEqual(drift.returncode, 0, drift.stdout + drift.stderr)
        self.assertIn("DRIFT_OK", drift.stdout)

    def test_drift_detects_cursor_change_in_mixed_target_scope(self):
        installed = run(
            "./build.sh", "--install", "--yes", "--target", "codex", "--target", "cursor", env=self.env,
        )
        self.assertEqual(installed.returncode, 0, installed.stdout + installed.stderr)
        cursor_agents = self.home / ".cursor/AGENTS.md"
        cursor_agents.write_text(cursor_agents.read_text(encoding="utf-8") + "\nlocal drift\n", encoding="utf-8")

        drift = run("ai/scripts/check-drift.sh", env={**self.env, "DRIFT_HOME": str(self.home)}, check=False)

        self.assertEqual(drift.returncode, 1, drift.stdout + drift.stderr)
        self.assertIn("DRIFT_DETECTED", drift.stdout)


if __name__ == "__main__":
    unittest.main()
