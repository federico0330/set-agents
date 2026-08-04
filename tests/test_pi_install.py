"""UI/installer follow-up — the pi lane actually installs (WSL bug report).

Contract: `install.sh` accepts `--harness pi`, provisions pnpm (pi's real
runtime: `pnpm dlx` against the pin in routing_core/catalog.py — there is no
global pi binary by design), and `--doctor-all` reports the lane honestly
instead of the structural `which("pi")` false negative.
"""

import subprocess
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ai/scripts"))


class InstallShPiTests(unittest.TestCase):
    def test_harness_pi_is_a_valid_flag_and_plans_the_lane(self):
        result = subprocess.run(
            ["bash", "install.sh", "--dry-run", "--harness", "pi", "--skip-deps"],
            cwd=ROOT, capture_output=True, text=True, timeout=120,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertRegex(result.stdout, r"(?m)^BOOTSTRAP_PLAN pi$")
        # pi alone must not drag the other harness CLIs in.
        self.assertNotRegex(result.stdout, r"BOOTSTRAP_(PLAN|OK|SKIP) (opencode|claude|codex)\b")

    def test_harness_claude_carries_the_pi_lane(self):
        # repo_config has always mapped claude -> claude-code + pi targets; the
        # CLI provisioning must match, or a fresh WSL ends with a dead pi lane.
        result = subprocess.run(
            ["bash", "install.sh", "--dry-run", "--harness", "claude", "--skip-deps"],
            cwd=ROOT, capture_output=True, text=True, timeout=120,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertRegex(result.stdout, r"(?m)^BOOTSTRAP_PLAN pi$")

    def test_the_pin_comes_from_catalog_py_not_a_duplicate(self):
        text = (ROOT / "install.sh").read_text()
        self.assertIn("from routing_core.catalog import PI_PACKAGE, PI_PINNED_VERSION", text)
        # No hardcoded copy of the version string outside catalog.py.
        from routing_core.catalog import PI_PINNED_VERSION
        self.assertNotIn(PI_PINNED_VERSION, text)

    def test_pnpm_is_in_the_recovery_catalog(self):
        import tomllib
        catalog = tomllib.loads((ROOT / "tools.toml").read_text())
        self.assertIn("pnpm", catalog["cli"])
        self.assertEqual(catalog["cli"]["pnpm"]["detect"], "pnpm")


class DoctorPiLaneTests(unittest.TestCase):
    def _pi_line(self, which_map):
        import set_agents_app
        lines = []
        with mock.patch.object(set_agents_app.shutil, "which", side_effect=which_map.get), \
             mock.patch("builtins.print", side_effect=lambda *a, **k: lines.append(" ".join(map(str, a)))), \
             mock.patch.object(set_agents_app.models_config, "load_config", side_effect=SystemExit(1)):
            set_agents_app.cmd_doctor_all()
        return next(line for line in lines if line.startswith("HARNESS pi "))

    def test_global_binary_wins(self):
        self.assertEqual(self._pi_line({"pi": "/usr/bin/pi", "pnpm": "/usr/bin/pnpm"}),
                         "HARNESS pi installed=yes")

    def test_pnpm_alone_is_the_dlx_state_not_a_false_negative(self):
        self.assertEqual(self._pi_line({"pnpm": "/usr/bin/pnpm"}),
                         "HARNESS pi installed=via-pnpm-dlx")

    def test_nothing_is_an_honest_no(self):
        self.assertEqual(self._pi_line({}), "HARNESS pi installed=no")


if __name__ == "__main__":
    unittest.main()
