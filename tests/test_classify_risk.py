"""Tests for ai/scripts/classify-risk.py (docs/adr/0021-*.md/0023-*.md): evidence-based
risk classification against a package's frozen candidate_identity. Never edits to
tests/test_harness.py or tests/test_routing.py.
"""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLASSIFY_RISK = ROOT / "ai/scripts/classify-risk.py"


def _import_classify_risk():
    spec = importlib.util.spec_from_file_location("classify_risk", CLASSIFY_RISK)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _git(*args, cwd):
    return subprocess.run(["git", *args], cwd=cwd, env=os.environ.copy(),
                          text=True, capture_output=True, check=True)


def _repo_with_commits(td, files_before, files_after):
    repo = Path(td) / "repo"
    repo.mkdir()
    _git("init", "-q", cwd=repo)
    _git("config", "user.email", "test@example.com", cwd=repo)
    _git("config", "user.name", "Test", cwd=repo)
    for rel, content in files_before.items():
        path = repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
    _git("add", "-A", cwd=repo)
    _git("commit", "-q", "-m", "base", cwd=repo)
    base_sha = _git("rev-parse", "HEAD", cwd=repo).stdout.strip()
    for rel, content in files_after.items():
        path = repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
    _git("add", "-A", cwd=repo)
    _git("commit", "-q", "-m", "candidate", cwd=repo)
    candidate_sha = _git("rev-parse", "HEAD", cwd=repo).stdout.strip()
    base_tree = _git("rev-parse", f"{base_sha}^{{tree}}", cwd=repo).stdout.strip()
    candidate_tree = _git("rev-parse", f"{candidate_sha}^{{tree}}", cwd=repo).stdout.strip()
    return repo, base_tree, candidate_tree


class ClassifyRiskUnitTests(unittest.TestCase):
    def test_unrelated_docs_change_is_low(self):
        with tempfile.TemporaryDirectory() as td:
            repo, base_tree, candidate_tree = _repo_with_commits(
                td, {"README.md": "hello\n"}, {"README.md": "hello world\n"},
            )
            cwd_before = os.getcwd()
            os.chdir(repo)
            try:
                cr = _import_classify_risk()
                level, reasons = cr.classify(base_tree, candidate_tree)
            finally:
                os.chdir(cwd_before)
            self.assertEqual(level, "low")
            self.assertEqual(reasons, [])

    def test_auth_path_is_high_even_for_a_tiny_diff(self):
        with tempfile.TemporaryDirectory() as td:
            repo, base_tree, candidate_tree = _repo_with_commits(
                td, {"src/util.py": "x = 1\n"},
                {"src/util.py": "x = 1\n", "src/auth/login.py": "def login(): pass\n"},
            )
            cwd_before = os.getcwd()
            os.chdir(repo)
            try:
                cr = _import_classify_risk()
                level, reasons = cr.classify(base_tree, candidate_tree)
            finally:
                os.chdir(cwd_before)
            self.assertEqual(level, "high")
            self.assertTrue(any("path:auth" in r for r in reasons), reasons)

    def test_large_mechanical_rename_with_no_signal_is_low(self):
        """Size never selects a tier -- a 200-line rename with zero named
        signals must stay low, unlike a size-based heuristic would score it."""
        with tempfile.TemporaryDirectory() as td:
            big = "\n".join(f"line {i}" for i in range(200)) + "\n"
            repo, base_tree, candidate_tree = _repo_with_commits(
                td, {"src/old_name.py": big}, {"src/new_name.py": big},
            )
            cwd_before = os.getcwd()
            os.chdir(repo)
            try:
                cr = _import_classify_risk()
                level, reasons = cr.classify(base_tree, candidate_tree)
            finally:
                os.chdir(cwd_before)
            self.assertEqual(level, "low")

    def test_shell_workflow_file_is_medium(self):
        with tempfile.TemporaryDirectory() as td:
            repo, base_tree, candidate_tree = _repo_with_commits(
                td, {"README.md": "x\n"}, {"README.md": "x\n", "deploy.sh": "echo hi\n"},
            )
            cwd_before = os.getcwd()
            os.chdir(repo)
            try:
                cr = _import_classify_risk()
                level, reasons = cr.classify(base_tree, candidate_tree)
            finally:
                os.chdir(cwd_before)
            self.assertEqual(level, "medium")

    def test_subprocess_spawn_content_signal_is_high(self):
        with tempfile.TemporaryDirectory() as td:
            repo, base_tree, candidate_tree = _repo_with_commits(
                td, {"README.md": "x\n"},
                {"README.md": "x\n", "src/runner.py": "import subprocess\nsubprocess.run(['ls'])\n"},
            )
            cwd_before = os.getcwd()
            os.chdir(repo)
            try:
                cr = _import_classify_risk()
                level, reasons = cr.classify(base_tree, candidate_tree)
            finally:
                os.chdir(cwd_before)
            self.assertEqual(level, "high")
            self.assertTrue(any("subprocess-spawn" in r for r in reasons), reasons)

    def test_executable_mode_added_is_high(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td) / "repo"
            repo.mkdir()
            _git("init", "-q", cwd=repo)
            _git("config", "user.email", "test@example.com", cwd=repo)
            _git("config", "user.name", "Test", cwd=repo)
            (repo / "tool.sh").write_text("#!/bin/sh\necho hi\n")
            _git("add", "-A", cwd=repo)
            _git("commit", "-q", "-m", "base", cwd=repo)
            base_tree = _git("rev-parse", "HEAD^{tree}", cwd=repo).stdout.strip()
            os.chmod(repo / "tool.sh", 0o755)
            _git("add", "-A", cwd=repo)
            _git("commit", "-q", "-m", "chmod +x", cwd=repo)
            candidate_tree = _git("rev-parse", "HEAD^{tree}", cwd=repo).stdout.strip()
            cwd_before = os.getcwd()
            os.chdir(repo)
            try:
                cr = _import_classify_risk()
                level, reasons = cr.classify(base_tree, candidate_tree)
            finally:
                os.chdir(cwd_before)
            self.assertEqual(level, "high")
            self.assertTrue(any("executable-mode-added" in r for r in reasons), reasons)


class ClassifyRiskCliTests(unittest.TestCase):
    def test_cli_requires_a_prior_freeze(self):
        with tempfile.TemporaryDirectory() as td:
            repo, base_tree, candidate_tree = _repo_with_commits(
                td, {"README.md": "x\n"}, {"README.md": "y\n"},
            )
            state = Path(td) / "state.json"
            state.write_text(json.dumps({"packages": [{"package_id": "PKG-01", "candidate_identity": None}]}))
            result = subprocess.run(
                ["python3", str(CLASSIFY_RISK), "--state-file", str(state), "--package-id", "PKG-01"],
                cwd=repo, text=True, capture_output=True, check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("NO_CANDIDATE_IDENTITY", result.stdout + result.stderr)

    def test_cli_prints_risk_level_line(self):
        with tempfile.TemporaryDirectory() as td:
            repo, base_tree, candidate_tree = _repo_with_commits(
                td, {"src/util.py": "x = 1\n"}, {"src/auth/login.py": "def login(): pass\n"},
            )
            state = Path(td) / "state.json"
            state.write_text(json.dumps({
                "packages": [{"package_id": "PKG-01",
                              "candidate_identity": {"base_tree": base_tree, "candidate_tree": candidate_tree}}],
            }))
            result = subprocess.run(
                ["python3", str(CLASSIFY_RISK), "--state-file", str(state), "--package-id", "PKG-01"],
                cwd=repo, text=True, capture_output=True, check=True,
            )
            self.assertIn("RISK_LEVEL high", result.stdout)


if __name__ == "__main__":
    unittest.main()
