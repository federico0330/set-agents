"""Tests for the bounded-repair ceiling (docs/adr/0023-*.md): the freeze-on-first-
record-repair logic in cli_repair.py, the immediate block on a repair-ceiling gate
failure in cmd_record_gate, and ai/scripts/check-repair-ceiling.py itself. New
coverage only -- never edits to tests/test_harness.py or tests/test_routing.py.
"""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FEATURE_STATE = ROOT / "PROYECTO/ai/scripts/feature-state.py"
CHECK_CEILING = ROOT / "ai/scripts/check-repair-ceiling.py"


def _run(*args, cwd=None, check=True):
    return subprocess.run(
        ["python3", str(FEATURE_STATE), *args],
        cwd=cwd or ROOT, env=os.environ.copy(), text=True, capture_output=True, check=check,
    )


def _git(*args, cwd):
    return subprocess.run(["git", *args], cwd=cwd, env=os.environ.copy(),
                          text=True, capture_output=True, check=True)


def _make_repo(td):
    repo = Path(td) / "repo"
    repo.mkdir()
    _git("init", "-q", cwd=repo)
    _git("config", "user.email", "test@example.com", cwd=repo)
    _git("config", "user.name", "Test", cwd=repo)
    (repo / "a.txt").write_text("one\ntwo\nthree\n")
    _git("add", "a.txt", cwd=repo)
    _git("commit", "-q", "-m", "base", cwd=repo)
    base_sha = _git("rev-parse", "HEAD", cwd=repo).stdout.strip()
    (repo / "a.txt").write_text("one\ntwo\nthree\nfour\nfive\n")
    _git("add", "-A", cwd=repo)
    _git("commit", "-q", "-m", "candidate", cwd=repo)
    candidate_sha = _git("rev-parse", "HEAD", cwd=repo).stdout.strip()
    return repo, base_sha, candidate_sha


class RepairCeilingCliTests(unittest.TestCase):
    def _init(self, state, feature_id="feat"):
        import hashlib
        spec = Path(state).parent / f"{feature_id}-spec.md"
        spec.parent.mkdir(parents=True, exist_ok=True)
        spec.write_text("# contract\n")
        digest = hashlib.sha256(spec.read_bytes()).hexdigest()
        axes_log = Path(state).parent.parent / "axes-log.jsonl"
        axes_log.parent.mkdir(parents=True, exist_ok=True)
        axes_rows = [
            {"at": "2026-08-15T00:00:00Z", "feature_id": feature_id, "axis": axis,
             "stance": "deferred", "origin": "n/a", "reason": "not decided yet"}
            for axis in ("data-store", "api-gateway", "deploy-platform", "audience", "embeddings",
                         "realtime", "mobile", "auth", "cost", "legal")
        ]
        axes_log.write_text("\n".join(json.dumps(row, sort_keys=True) for row in axes_rows) + "\n")
        _run("init", feature_id, str(spec), digest, "--state-file", str(state),
             "--approved-by", "test", "--axes-log", str(axes_log),
             "--risk-signal", "user-asked-full-pipeline")

    def _drive_to_review_required(self, state, repo, base_sha, candidate_sha,
                                  complexity="small", package_id="PKG-01"):
        """init -> package -> gates -> freeze -> review with one LOW finding
        (verdict repair_required) -> PACKAGE_REPAIR, no verification needed
        (require_verified is a no-op below medium severity)."""
        self._init(state)
        _run("create-package", package_id, "objective", "--state-file", str(state),
             "--complexity", complexity, "--ac", "AC-01", "--task", "T1", "--actor", "test", cwd=repo)
        pack = Path(state).parent / "context" / f"{package_id}.md"
        pack.parent.mkdir(parents=True, exist_ok=True)
        pack.write_text("# pack\n")
        _run("transition", "PACKAGE_IMPLEMENTATION", "--package-id", package_id,
             "--state-file", str(state), "--actor", "test", cwd=repo)
        _run("start-task", package_id, "T1", "--state-file", str(state), "--actor", "test", cwd=repo)
        _run("complete-task", package_id, "T1", "--validation", "local-check",
             "--state-file", str(state), "--actor", "test", cwd=repo)
        _run("update-package", package_id, "--state-file", str(state), "--actor", "test",
             "--diff-ref", "candidate", "--integrated", "true", cwd=repo)
        _run("transition", "PACKAGE_GATES", "--package-id", package_id,
             "--state-file", str(state), "--actor", "test", cwd=repo)
        _run("freeze-candidate", package_id, "--state-file", str(state), "--actor", "test",
             "--baseline", base_sha, "--candidate-ref", candidate_sha, cwd=repo)
        _run("transition", "PACKAGE_REVIEW", "--package-id", package_id,
             "--state-file", str(state), "--actor", "test", cwd=repo)
        finding = json.dumps({"id": "F-1", "severity": "low", "category": "correctness",
                              "acceptance_criterion": "AC-01", "file": "a.txt", "line": 1,
                              "evidence": "e", "reproduction": "r", "required_outcome": "o",
                              "suggested_scope": "s"})
        _run("record-review", package_id, "repair_required", "--state-file", str(state),
             "--actor", "test", "--finding", finding, "--evidence", "found one", cwd=repo)

    def test_repair_ceiling_freezes_from_candidate_identity_and_complexity(self):
        with tempfile.TemporaryDirectory() as td:
            repo, base_sha, candidate_sha = _make_repo(td)
            state = Path(td) / "state.json"
            self._drive_to_review_required(state, repo, base_sha, candidate_sha, complexity="small")
            original = json.loads(state.read_text())["packages"][0]["candidate_identity"]["changed_lines"]
            _run("record-repair", "PKG-01", "--state-file", str(state), "--actor", "repair-agent",
                 "--finding-id", "F-1", "--changed-file", "a.txt", cwd=repo)
            data = json.loads(state.read_text())
            ceiling = data["packages"][0]["repair_ceiling"]
            self.assertEqual(ceiling["original_changed_lines"], original)
            self.assertEqual(ceiling["cap_source"], "complexity:small")
            expected_budget = min(40, -(-original // 2))
            self.assertEqual(ceiling["budget_lines"], expected_budget)

    def test_repair_ceiling_stays_none_without_a_prior_freeze(self):
        with tempfile.TemporaryDirectory() as td:
            repo, base_sha, candidate_sha = _make_repo(td)
            state = Path(td) / "state.json"
            self._init(state)
            _run("create-package", "PKG-01", "objective", "--state-file", str(state),
                 "--complexity", "small", "--ac", "AC-01", "--task", "T1", "--actor", "test", cwd=repo)
            pack = Path(state).parent / "context" / "PKG-01.md"
            pack.parent.mkdir(parents=True, exist_ok=True)
            pack.write_text("# pack\n")
            _run("transition", "PACKAGE_IMPLEMENTATION", "--package-id", "PKG-01",
                 "--state-file", str(state), "--actor", "test", cwd=repo)
            _run("start-task", "PKG-01", "T1", "--state-file", str(state), "--actor", "test", cwd=repo)
            _run("complete-task", "PKG-01", "T1", "--validation", "local-check",
                 "--state-file", str(state), "--actor", "test", cwd=repo)
            _run("update-package", "PKG-01", "--state-file", str(state), "--actor", "test",
                 "--diff-ref", "candidate", "--integrated", "true", cwd=repo)
            _run("transition", "PACKAGE_GATES", "--package-id", "PKG-01",
                 "--state-file", str(state), "--actor", "test", cwd=repo)
            # No freeze-candidate here -- candidate_identity stays None.
            _run("transition", "PACKAGE_REVIEW", "--package-id", "PKG-01",
                 "--state-file", str(state), "--actor", "test", cwd=repo)
            finding = json.dumps({"id": "F-1", "severity": "low", "category": "correctness",
                                  "acceptance_criterion": "AC-01", "file": "a.txt", "line": 1,
                                  "evidence": "e", "reproduction": "r", "required_outcome": "o",
                                  "suggested_scope": "s"})
            _run("record-review", "PKG-01", "repair_required", "--state-file", str(state),
                 "--actor", "test", "--finding", finding, "--evidence", "found one", cwd=repo)
            _run("record-repair", "PKG-01", "--state-file", str(state), "--actor", "repair-agent",
                 "--finding-id", "F-1", "--changed-file", "a.txt", cwd=repo)
            data = json.loads(state.read_text())
            self.assertIsNone(data["packages"][0]["repair_ceiling"])

    def test_record_gate_repair_ceiling_fail_blocks_immediately(self):
        with tempfile.TemporaryDirectory() as td:
            repo, base_sha, candidate_sha = _make_repo(td)
            state = Path(td) / "state.json"
            self._drive_to_review_required(state, repo, base_sha, candidate_sha, complexity="small")
            _run("record-repair", "PKG-01", "--state-file", str(state), "--actor", "repair-agent",
                 "--finding-id", "F-1", "--changed-file", "a.txt", cwd=repo)
            result = _run("record-gate", "repair-ceiling", "fail", "--package-id", "PKG-01",
                          "--state-file", str(state), "--actor", "test",
                          "--evidence", "over budget", cwd=repo)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            data = json.loads(state.read_text())
            self.assertEqual(data["phase"], "BLOCKED")
            self.assertEqual(data["final_state"], "BLOCKED")
            self.assertTrue(any("repair exceeded its frozen line ceiling" in b.get("reason", "")
                                for b in data["blockers"]))

    def test_record_gate_repair_ceiling_pass_does_not_block(self):
        with tempfile.TemporaryDirectory() as td:
            repo, base_sha, candidate_sha = _make_repo(td)
            state = Path(td) / "state.json"
            self._drive_to_review_required(state, repo, base_sha, candidate_sha, complexity="small")
            _run("record-repair", "PKG-01", "--state-file", str(state), "--actor", "repair-agent",
                 "--finding-id", "F-1", "--changed-file", "a.txt", cwd=repo)
            result = _run("record-gate", "repair-ceiling", "pass", "--package-id", "PKG-01",
                          "--state-file", str(state), "--actor", "test",
                          "--evidence", "within budget", cwd=repo)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            data = json.loads(state.read_text())
            self.assertNotEqual(data["phase"], "BLOCKED")


class CheckRepairCeilingScriptTests(unittest.TestCase):
    def test_no_ceiling_frozen_passes_trivially(self):
        with tempfile.TemporaryDirectory() as td:
            state = Path(td) / "state.json"
            state.write_text(json.dumps({"packages": [{"package_id": "PKG-01", "repair_ceiling": None}]}))
            result = subprocess.run(
                ["python3", str(CHECK_CEILING), "--state-file", str(state), "--package-id", "PKG-01"],
                text=True, capture_output=True, check=True,
            )
            self.assertIn("REPAIR_CEILING_PASS", result.stdout)

    def test_within_budget_via_explicit_changed_lines_passes(self):
        with tempfile.TemporaryDirectory() as td:
            state = Path(td) / "state.json"
            state.write_text(json.dumps({
                "packages": [{"package_id": "PKG-01",
                              "repair_ceiling": {"budget_lines": 10}}],
            }))
            result = subprocess.run(
                ["python3", str(CHECK_CEILING), "--state-file", str(state), "--package-id", "PKG-01",
                 "--changed-lines", "5"],
                text=True, capture_output=True, check=True,
            )
            self.assertIn("REPAIR_CEILING_PASS", result.stdout)

    def test_over_budget_via_explicit_changed_lines_fails(self):
        with tempfile.TemporaryDirectory() as td:
            state = Path(td) / "state.json"
            state.write_text(json.dumps({
                "packages": [{"package_id": "PKG-01",
                              "repair_ceiling": {"budget_lines": 10}}],
            }))
            result = subprocess.run(
                ["python3", str(CHECK_CEILING), "--state-file", str(state), "--package-id", "PKG-01",
                 "--changed-lines", "11"],
                text=True, capture_output=True, check=False,
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("REPAIR_CEILING_FAIL", result.stdout)

    def test_git_measured_over_budget_fails(self):
        with tempfile.TemporaryDirectory() as td:
            repo, base_sha, candidate_sha = _make_repo(td)
            # a.txt gained 2 lines (three->five) between base and candidate; budget=1 must fail.
            state = Path(td) / "state.json"
            state.write_text(json.dumps({
                "packages": [{"package_id": "PKG-01",
                              "repair_ceiling": {"budget_lines": 1},
                              "candidate_identity": {"candidate_tree": candidate_sha}}],
            }))
            result = subprocess.run(
                ["python3", str(CHECK_CEILING), "--state-file", str(state), "--package-id", "PKG-01",
                 "--baseline", base_sha],
                cwd=repo, text=True, capture_output=True, check=False,
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("REPAIR_CEILING_FAIL", result.stdout)


if __name__ == "__main__":
    unittest.main()
