"""Feature 017 PKG-F — solo-Claude-Code onboarding.

New tests only (the immutable suites are never edited): the general doctor
(`--doctor-all`), the install-scope record written by install.py, and the
scope-aware drift check that keeps a partial install from reading the
never-installed harness trees as drift.
"""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class DoctorAllTests(unittest.TestCase):
    def test_doctor_all_reports_harnesses_tools_and_never_leaks_credentials(self):
        result = subprocess.run(
            [sys.executable, "ai/scripts/set_agents_app.py", "--doctor-all"],
            cwd=ROOT, text=True, capture_output=True, timeout=300,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        for harness in ("claude-code", "opencode", "codex"):
            self.assertRegex(result.stdout, rf"(?m)^HARNESS {harness} installed=(yes|no)$")
        # pi resolves via pnpm dlx (no global binary expected): a third honest state.
        self.assertRegex(result.stdout, r"(?m)^HARNESS pi installed=(yes|no|via-pnpm-dlx)$")
        self.assertRegex(result.stdout, r"(?m)^INSTALL_SCOPE ")
        self.assertRegex(result.stdout, r"(?m)^TOOL \S+ installed=(yes|no)$")
        # Same redaction contract as the pi doctor: never credential material.
        self.assertNotIn("apiKey", result.stdout)
        self.assertNotIn("token", result.stdout.lower())

    def test_bare_doctor_contract_is_untouched(self):
        # The immutable suite pins this too; asserting it here makes the coupling
        # explicit for THIS package: --doctor-all must not have widened --doctor.
        result = subprocess.run(
            [sys.executable, "ai/scripts/set_agents_app.py", "--doctor", "--json"],
            cwd=ROOT, text=True, capture_output=True, timeout=60,
        )
        self.assertEqual(result.returncode, 2)
        self.assertEqual(json.loads(result.stdout)["reason_codes"], ["DOCTOR_HARNESS_UNSUPPORTED"])


class ScopedInstallDriftTests(unittest.TestCase):
    def test_targeted_install_records_scope_and_drift_check_honors_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            staging = tmp / "staging"
            home = tmp / "home"
            home.mkdir()
            subprocess.run(
                [sys.executable, "ai/scripts/generate.py", "--output", str(staging)],
                cwd=ROOT, check=True, capture_output=True, text=True,
            )
            result = subprocess.run(
                [sys.executable, "ai/scripts/install.py", "--staging", str(staging),
                 "--home", str(home), "--target", "claude-code", "--target", "pi"],
                cwd=ROOT, capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            scope_path = home / ".local/state/set-agentes/install-targets.json"
            self.assertTrue(scope_path.exists())
            self.assertEqual(json.loads(scope_path.read_text()), ["claude-code", "pi"])
            # The opencode/codex trees were never installed on this "machine";
            # the scope record must keep the drift check from counting them.
            drift = subprocess.run(
                ["bash", "ai/scripts/check-drift.sh"],
                cwd=ROOT, env={
                    # Include sys.executable's directory first so check-drift.sh's
                    # `python3` resolves to the same interpreter (which has tomllib).
                    # On CI, /usr/bin/python3 may be Python 3.10 (no tomllib).
                    "PATH": str(Path(sys.executable).parent) + ":/usr/bin:/bin",
                    "HOME": str(home), "DRIFT_HOME": str(home)},
                capture_output=True, text=True,
            )
            self.assertEqual(drift.returncode, 0, drift.stdout + drift.stderr)
            self.assertIn("DRIFT_OK", drift.stdout)

    def test_full_install_records_full_scope(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            staging = tmp / "staging"
            home = tmp / "home"
            home.mkdir()
            subprocess.run(
                [sys.executable, "ai/scripts/generate.py", "--output", str(staging)],
                cwd=ROOT, check=True, capture_output=True, text=True,
            )
            result = subprocess.run(
                [sys.executable, "ai/scripts/install.py", "--staging", str(staging), "--home", str(home)],
                cwd=ROOT, capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            scope_path = home / ".local/state/set-agentes/install-targets.json"
            self.assertEqual(json.loads(scope_path.read_text()),
                             ["claude-code", "codex", "opencode", "pi"])


class InstallShHarnessFlagTests(unittest.TestCase):
    def test_dry_run_with_harness_claude_never_mentions_opencode_or_codex_install(self):
        result = subprocess.run(
            ["bash", "install.sh", "--dry-run", "--harness", "claude", "--skip-deps"],
            cwd=ROOT, capture_output=True, text=True, timeout=120,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotRegex(result.stdout, r"BOOTSTRAP_(PLAN|OK|SKIP) opencode")
        self.assertNotRegex(result.stdout, r"BOOTSTRAP_(PLAN|OK|SKIP) codex")
        self.assertNotRegex(result.stdout, r"AUTH_(OK|NEEDED) (opencode|codex)")

    def test_invalid_harness_value_is_a_usage_error(self):
        result = subprocess.run(
            ["bash", "install.sh", "--harness", "vim"],
            cwd=ROOT, capture_output=True, text=True, timeout=60,
        )
        self.assertEqual(result.returncode, 2)


if __name__ == "__main__":
    unittest.main()
