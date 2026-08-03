"""Tests for the integration hook triad (docs/adr/0020-*.md): coord_policy.py's
denial of a direct, unwrapped `transition ... INTEGRATION` (including argv
reordering that a naive substring check would miss), and the
integration_gate.py/integration_action.py wrapper end-to-end against a real,
self-contained synthetic git repo. New coverage only -- never edits to
tests/test_harness.py or tests/test_routing.py.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ai/scripts"))

import coord_policy  # noqa: E402

INTEGRATION_ACTION = ROOT / "ai/scripts/integration_action.py"


def _git(*args, cwd):
    return subprocess.run(["git", *args], cwd=cwd, env=os.environ.copy(),
                          text=True, capture_output=True, check=True)


class TransitionBlockUnitTests(unittest.TestCase):
    """coord_policy.allowed() must deny a direct INTEGRATION transition
    regardless of argument order, and allow the wrapped form syntactically."""

    def test_denies_to_phase_immediately_after_transition(self):
        self.assertFalse(coord_policy.allowed(
            "python3 ai/scripts/feature-state.py transition INTEGRATION --package-id PKG-01 --actor x"
        ))

    def test_denies_to_phase_after_reordered_flags(self):
        # The exact case a naive "transition INTEGRATION" substring/prefix check misses.
        self.assertFalse(coord_policy.allowed(
            "python3 ai/scripts/feature-state.py transition --actor x --package-id PKG-01 INTEGRATION"
        ))

    def test_allows_transition_to_every_other_phase(self):
        for phase in ("PACKAGE_GATES", "PACKAGE_REVIEW", "PACKAGE_REPAIR", "DONE", "BLOCKED"):
            with self.subTest(phase=phase):
                self.assertTrue(coord_policy.allowed(
                    f"python3 ai/scripts/feature-state.py transition {phase} --package-id PKG-01 --actor x"
                ))

    def test_allows_the_wrapped_form_syntactically(self):
        self.assertTrue(coord_policy.allowed(
            "python3 ~/.claude/hooks/integration_action.py state.json PKG-01 transition -- "
            "python3 ai/scripts/feature-state.py transition INTEGRATION --package-id PKG-01"
        ))

    def test_allows_every_other_feature_state_subcommand_untouched(self):
        self.assertTrue(coord_policy.allowed(
            "python3 ai/scripts/feature-state.py record-gate repair-ceiling fail --package-id PKG-01"
        ))


def _make_scaffolded_repo(td):
    """A synthetic, self-contained git repo carrying its own copy of
    ai/scripts/feature-state.py + feature_state_lib/ (mirroring what
    sync-project.sh actually scaffolds into a real client project) --
    so the WRAPPED command (`python3 ai/scripts/feature-state.py ...`,
    resolved relative to this repo's own cwd) can actually run, without
    touching SET-AGENTES's own git history."""
    repo = Path(td) / "repo"
    repo.mkdir()
    (repo / "ai/scripts").mkdir(parents=True)
    shutil.copy2(ROOT / "PROYECTO/ai/scripts/feature-state.py", repo / "ai/scripts/feature-state.py")
    shutil.copytree(ROOT / "PROYECTO/ai/scripts/feature_state_lib", repo / "ai/scripts/feature_state_lib")
    _git("init", "-q", cwd=repo)
    _git("config", "user.email", "test@example.com", cwd=repo)
    _git("config", "user.name", "Test", cwd=repo)
    _git("add", "-A", cwd=repo)
    _git("commit", "-q", "-m", "scaffold", cwd=repo)
    base_sha = _git("rev-parse", "HEAD", cwd=repo).stdout.strip()
    (repo / "src.txt").write_text("hello\n")
    _git("add", "-A", cwd=repo)
    _git("commit", "-q", "-m", "candidate", cwd=repo)
    candidate_sha = _git("rev-parse", "HEAD", cwd=repo).stdout.strip()
    return repo, base_sha, candidate_sha


def _fs(*args, cwd, check=True):
    return subprocess.run(
        ["python3", "ai/scripts/feature-state.py", *args],
        cwd=cwd, env=os.environ.copy(), text=True, capture_output=True, check=check,
    )


def _drive_to_receipt(repo, base_sha, candidate_sha, package_id="PKG-01", feature_id="feat",
                       freeze_candidate_ref=None):
    # Defaults to the fixed candidate_sha (immune to later commits, the common/safe
    # case). Tests that need to prove drift-after-freeze pass "HEAD" explicitly --
    # a fixed sha's tree cannot change just because a later commit lands on top of it.
    freeze_candidate_ref = freeze_candidate_ref or candidate_sha
    spec = repo / f"{feature_id}-spec.md"
    spec.write_text("# contract\n")
    digest = hashlib.sha256(spec.read_bytes()).hexdigest()
    state = repo / "state.json"
    _fs("init", feature_id, str(spec), digest, "--state-file", str(state), "--approved-by", "test", cwd=repo)
    _fs("create-package", package_id, "objective", "--state-file", str(state),
        "--complexity", "small", "--ac", "AC-01", "--task", "T1", "--actor", "test", cwd=repo)
    _fs("transition", "PACKAGE_IMPLEMENTATION", "--package-id", package_id,
        "--state-file", str(state), "--actor", "test", cwd=repo)
    _fs("start-task", package_id, "T1", "--state-file", str(state), "--actor", "test", cwd=repo)
    _fs("complete-task", package_id, "T1", "--validation", "local-check",
        "--state-file", str(state), "--actor", "test", cwd=repo)
    _fs("update-package", package_id, "--state-file", str(state), "--actor", "test",
        "--diff-ref", "candidate", "--integrated", "true", cwd=repo)
    _fs("transition", "PACKAGE_GATES", "--package-id", package_id,
        "--state-file", str(state), "--actor", "test", cwd=repo)
    _fs("freeze-candidate", package_id, "--state-file", str(state), "--actor", "test",
        "--baseline", base_sha, "--candidate-ref", freeze_candidate_ref, cwd=repo)
    _fs("transition", "PACKAGE_REVIEW", "--package-id", package_id,
        "--state-file", str(state), "--actor", "test", cwd=repo)
    _fs("record-review", package_id, "pass", "--state-file", str(state), "--actor", "test",
        "--evidence", "clean", cwd=repo)
    _fs("record-testing", package_id, "pass", "--state-file", str(state), "--actor", "test",
        "--evidence", "clean", cwd=repo)
    _fs("record-runtime-qa", package_id, "pass", "--state-file", str(state), "--actor", "test",
        "--evidence", "clean", cwd=repo)
    _fs("record-receipt", package_id, "--state-file", str(state), "--actor", "test", cwd=repo)
    _fs("accept-package", package_id, "--state-file", str(state), "--actor", "test", cwd=repo)
    return state


class IntegrationActionEndToEndTests(unittest.TestCase):
    def _wrapped_transition_command(self, package_id, state):
        return [
            "python3", "ai/scripts/feature-state.py", "transition", "INTEGRATION",
            "--package-id", package_id, "--actor", "test", "--state-file", str(state),
        ]

    def test_wrapped_transition_succeeds_after_a_real_receipt(self):
        with tempfile.TemporaryDirectory() as td:
            repo, base_sha, candidate_sha = _make_scaffolded_repo(td)
            state = _drive_to_receipt(repo, base_sha, candidate_sha)
            result = subprocess.run(
                ["python3", str(INTEGRATION_ACTION), str(state), "PKG-01", "transition",
                 "--", *self._wrapped_transition_command("PKG-01", state)],
                cwd=repo, text=True, capture_output=True, check=False,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            data = json.loads(state.read_text())
            self.assertEqual(data["phase"], "INTEGRATION")

    def test_wrapped_transition_fails_closed_without_a_receipt(self):
        with tempfile.TemporaryDirectory() as td:
            repo, base_sha, candidate_sha = _make_scaffolded_repo(td)
            spec = repo / "feat-spec.md"
            spec.write_text("# contract\n")
            digest = hashlib.sha256(spec.read_bytes()).hexdigest()
            state = repo / "state.json"
            _fs("init", "feat", str(spec), digest, "--state-file", str(state), "--approved-by", "test", cwd=repo)
            _fs("create-package", "PKG-01", "objective", "--state-file", str(state),
                "--complexity", "small", "--ac", "AC-01", "--task", "T1", "--actor", "test", cwd=repo)
            # Never driven past PACKAGE_PLANNING -- no receipt, no candidate_identity.
            result = subprocess.run(
                ["python3", str(INTEGRATION_ACTION), str(state), "PKG-01", "transition",
                 "--", *self._wrapped_transition_command("PKG-01", state)],
                cwd=repo, text=True, capture_output=True, check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("receipt is required", result.stdout + result.stderr)
            data = json.loads(state.read_text())
            self.assertNotEqual(data["phase"], "INTEGRATION")

    def test_wrapped_transition_fails_closed_when_repo_drifted_after_receipt(self):
        with tempfile.TemporaryDirectory() as td:
            repo, base_sha, candidate_sha = _make_scaffolded_repo(td)
            # freeze against HEAD (not the fixed sha) so a later commit actually drifts it.
            state = _drive_to_receipt(repo, base_sha, candidate_sha, freeze_candidate_ref="HEAD")
            # A commit lands after the receipt was minted, without a re-freeze.
            (repo / "sneaked.txt").write_text("drift\n")
            _git("add", "-A", cwd=repo)
            _git("commit", "-q", "-m", "post-receipt drift", cwd=repo)
            result = subprocess.run(
                ["python3", str(INTEGRATION_ACTION), str(state), "PKG-01", "transition",
                 "--", *self._wrapped_transition_command("PKG-01", state)],
                cwd=repo, text=True, capture_output=True, check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("no longer matches the live repo", result.stdout + result.stderr)
            data = json.loads(state.read_text())
            self.assertNotEqual(data["phase"], "INTEGRATION")

    def test_rejects_a_mismatched_package_id_before_running_anything(self):
        with tempfile.TemporaryDirectory() as td:
            repo, base_sha, candidate_sha = _make_scaffolded_repo(td)
            state = _drive_to_receipt(repo, base_sha, candidate_sha, package_id="PKG-01")
            # The wrapper's own package_id (arg 2) says PKG-01, but the wrapped command
            # targets a different package -- must be rejected before the subprocess runs.
            result = subprocess.run(
                ["python3", str(INTEGRATION_ACTION), str(state), "PKG-01", "transition",
                 "--", "python3", "ai/scripts/feature-state.py", "transition", "INTEGRATION",
                 "--package-id", "PKG-99", "--actor", "test"],
                cwd=repo, text=True, capture_output=True, check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("must match the checked package_id", result.stdout + result.stderr)

    def test_rejects_a_non_integration_transition_smuggled_through_the_wrapper(self):
        with tempfile.TemporaryDirectory() as td:
            repo, base_sha, candidate_sha = _make_scaffolded_repo(td)
            state = _drive_to_receipt(repo, base_sha, candidate_sha)
            result = subprocess.run(
                ["python3", str(INTEGRATION_ACTION), str(state), "PKG-01", "transition",
                 "--", "python3", "ai/scripts/feature-state.py", "transition", "DONE",
                 "--package-id", "PKG-01", "--actor", "test"],
                cwd=repo, text=True, capture_output=True, check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("only the INTEGRATION transition", result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
