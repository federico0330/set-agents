"""Tests for the RDD-inspired schema additions (docs/adr/0020-*.md and siblings):
candidate_identity, receipt, repair_ceiling, strict_tdd on `compact_package`, and their
static validate_state backstop checks. New coverage only -- never edits to
tests/test_harness.py or tests/test_routing.py.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ai/scripts"))

from feature_state_lib import model  # noqa: E402

FEATURE_STATE = ROOT / "PROYECTO/ai/scripts/feature-state.py"


def _feature(packages):
    data = model.base_state("F-01", "docs/specs/F-01/spec.md", "deadbeef")
    data["packages"] = packages
    data["current_package_id"] = packages[0]["package_id"] if packages else None
    return data


def _run(*args, cwd=None, check=True):
    return subprocess.run(
        ["python3", str(FEATURE_STATE), *args],
        cwd=cwd or ROOT, env=os.environ.copy(), text=True, capture_output=True, check=check,
    )


def _git(*args, cwd):
    return subprocess.run(["git", *args], cwd=cwd, env=os.environ.copy(),
                          text=True, capture_output=True, check=True)


def _make_repo(td):
    """A small, isolated git repo with two commits -- never SET-AGENTES's own
    history, so these tests don't drift as more commits land here."""
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
    (repo / "b.txt").write_text("new file\n")
    _git("add", "-A", cwd=repo)
    _git("commit", "-q", "-m", "candidate", cwd=repo)
    candidate_sha = _git("rev-parse", "HEAD", cwd=repo).stdout.strip()
    return repo, base_sha, candidate_sha


class CandidateIdentityUnitTests(unittest.TestCase):
    """freeze()/rederive_and_compare() against a real, isolated temp git repo."""

    def test_freeze_resolves_trees_digest_and_changed_lines(self):
        with tempfile.TemporaryDirectory() as td:
            repo, base_sha, candidate_sha = _make_repo(td)
            cwd_before = os.getcwd()
            os.chdir(repo)
            try:
                from feature_state_lib import candidate_identity as ci
                frozen = ci.freeze(base_sha, candidate_sha)
            finally:
                os.chdir(cwd_before)
            self.assertEqual(len(frozen["base_tree"]), 40)
            self.assertEqual(len(frozen["candidate_tree"]), 40)
            self.assertNotEqual(frozen["base_tree"], frozen["candidate_tree"])
            self.assertTrue(frozen["paths_digest"].startswith("sha256:"))
            # a.txt: +2/-0 lines changed (3->5 lines, same first 3); b.txt: +1/-0 new file.
            self.assertEqual(frozen["changed_lines"], 3)

    def test_rederive_matches_a_clean_freeze(self):
        with tempfile.TemporaryDirectory() as td:
            repo, base_sha, candidate_sha = _make_repo(td)
            cwd_before = os.getcwd()
            os.chdir(repo)
            try:
                from feature_state_lib import candidate_identity as ci
                frozen = ci.freeze(base_sha, candidate_sha)
                matches, fresh = ci.rederive_and_compare(frozen)
            finally:
                os.chdir(cwd_before)
            self.assertTrue(matches)
            self.assertEqual(fresh["candidate_tree"], frozen["candidate_tree"])

    def test_rederive_detects_a_tampered_candidate_tree(self):
        with tempfile.TemporaryDirectory() as td:
            repo, base_sha, candidate_sha = _make_repo(td)
            cwd_before = os.getcwd()
            os.chdir(repo)
            try:
                from feature_state_lib import candidate_identity as ci
                frozen = ci.freeze(base_sha, candidate_sha)
                tampered = dict(frozen)
                tampered["candidate_tree"] = "0" * 40
                matches, fresh = ci.rederive_and_compare(tampered)
            finally:
                os.chdir(cwd_before)
            self.assertFalse(matches)
            # `fresh` is the live recomputation, unaffected by the tampering -- it must
            # resolve to the REAL candidate commit's tree, not the tampered value.
            real_tree = _git("rev-parse", f"{candidate_sha}^{{tree}}", cwd=repo).stdout.strip()
            self.assertEqual(fresh["candidate_tree"], real_tree)
            self.assertNotEqual(fresh["candidate_tree"], "0" * 40)

    def test_rederive_detects_head_moving_after_freeze(self):
        """The exact tamper-detection property the integration receipt depends on:
        if `candidate_ref` was "HEAD" and more commits land after the freeze without
        a re-freeze, re-derivation must catch it."""
        with tempfile.TemporaryDirectory() as td:
            repo, base_sha, candidate_sha = _make_repo(td)
            cwd_before = os.getcwd()
            os.chdir(repo)
            try:
                from feature_state_lib import candidate_identity as ci
                frozen = ci.freeze(base_sha, "HEAD")
                (repo / "c.txt").write_text("sneaked in after freeze\n")
                _git("add", "-A", cwd=repo)
                _git("commit", "-q", "-m", "post-freeze", cwd=repo)
                matches, fresh = ci.rederive_and_compare(frozen)
            finally:
                os.chdir(cwd_before)
            self.assertFalse(matches)


class StrictTddCliTests(unittest.TestCase):
    """--strict-tdd on create-package/update-package, exercised via the real CLI
    (PROYECTO twin), same convention tests/test_harness.py's run()/init_state() use."""

    def _init(self, state, feature_id="feat"):
        spec = Path(state).parent / f"{feature_id}-spec.md"
        spec.parent.mkdir(parents=True, exist_ok=True)
        spec.write_text("# contract\n")
        digest = hashlib.sha256(spec.read_bytes()).hexdigest()
        _run("init", feature_id, str(spec), digest, "--state-file", str(state), "--approved-by", "test")

    def test_create_package_strict_tdd_defaults_false(self):
        with tempfile.TemporaryDirectory() as td:
            state = Path(td) / "state.json"
            self._init(state)
            _run("create-package", "PKG-01", "objective", "--state-file", str(state),
                 "--complexity", "small", "--ac", "AC-01", "--actor", "test")
            data = json.loads(state.read_text())
            self.assertIs(data["packages"][0]["strict_tdd"], False)

    def test_create_package_strict_tdd_true_is_persisted(self):
        with tempfile.TemporaryDirectory() as td:
            state = Path(td) / "state.json"
            self._init(state)
            _run("create-package", "PKG-01", "objective", "--state-file", str(state),
                 "--complexity", "small", "--ac", "AC-01", "--actor", "test", "--strict-tdd", "true")
            data = json.loads(state.read_text())
            self.assertIs(data["packages"][0]["strict_tdd"], True)

    def test_update_package_can_flip_strict_tdd(self):
        with tempfile.TemporaryDirectory() as td:
            state = Path(td) / "state.json"
            self._init(state)
            _run("create-package", "PKG-01", "objective", "--state-file", str(state),
                 "--complexity", "small", "--ac", "AC-01", "--actor", "test")
            _run("update-package", "PKG-01", "--state-file", str(state),
                 "--actor", "test", "--strict-tdd", "true")
            data = json.loads(state.read_text())
            self.assertIs(data["packages"][0]["strict_tdd"], True)


class CompactPackageDefaultsTests(unittest.TestCase):
    def test_new_fields_default_to_none_or_false(self):
        pkg = model.compact_package("PKG-01", "objective")
        self.assertIsNone(pkg["candidate_identity"])
        self.assertIsNone(pkg["receipt"])
        self.assertIsNone(pkg["repair_ceiling"])
        self.assertIs(pkg["strict_tdd"], False)

    def test_old_state_without_new_keys_stays_valid(self):
        pkg = model.compact_package("PKG-01", "objective")
        for key in ("candidate_identity", "receipt", "repair_ceiling", "strict_tdd"):
            del pkg[key]
        pkg["acceptance_criteria"] = ["AC-01"]
        pkg["status"] = "accepted"
        data = _feature([pkg])
        data["acceptance_criteria"] = ["AC-01"]
        self.assertEqual(model.validate_state(data), [])


class ReceiptCandidateIdentityValidationTests(unittest.TestCase):
    def _package(self, **overrides):
        pkg = model.compact_package("PKG-01", "objective")
        pkg["acceptance_criteria"] = ["AC-01"]
        pkg.update(overrides)
        return pkg

    def test_receipt_matching_candidate_identity_is_valid(self):
        identity = {"base_tree": "aaa", "candidate_tree": "bbb", "paths_digest": "sha256:ccc"}
        pkg = self._package(
            candidate_identity=identity,
            receipt={"base_tree": "aaa", "candidate_tree": "bbb", "paths_digest": "sha256:ccc"},
        )
        data = _feature([pkg])
        data["acceptance_criteria"] = ["AC-01"]
        self.assertEqual(model.validate_state(data), [])

    def test_receipt_mismatching_candidate_identity_is_invalid(self):
        identity = {"base_tree": "aaa", "candidate_tree": "bbb", "paths_digest": "sha256:ccc"}
        pkg = self._package(
            candidate_identity=identity,
            receipt={"base_tree": "aaa", "candidate_tree": "TAMPERED", "paths_digest": "sha256:ccc"},
        )
        data = _feature([pkg])
        data["acceptance_criteria"] = ["AC-01"]
        errors = model.validate_state(data)
        self.assertTrue(any("receipt.candidate_tree" in e for e in errors), errors)

    def test_receipt_with_no_candidate_identity_is_invalid(self):
        pkg = self._package(receipt={"base_tree": "aaa", "candidate_tree": "bbb", "paths_digest": "sha256:ccc"})
        data = _feature([pkg])
        data["acceptance_criteria"] = ["AC-01"]
        errors = model.validate_state(data)
        self.assertTrue(any("receipt.base_tree" in e for e in errors), errors)


class RepairCeilingValidationTests(unittest.TestCase):
    def _package(self, **overrides):
        pkg = model.compact_package("PKG-01", "objective")
        pkg["acceptance_criteria"] = ["AC-01"]
        pkg.update(overrides)
        return pkg

    def test_repair_within_ceiling_is_valid(self):
        pkg = self._package(
            repair_ceiling={"original_changed_lines": 86, "budget_lines": 43, "cap_source": "complexity:medium"},
            repairs=[{"finding_id": "F-1", "changed_lines": 43}],
        )
        data = _feature([pkg])
        data["acceptance_criteria"] = ["AC-01"]
        self.assertEqual(model.validate_state(data), [])

    def test_repair_exceeding_ceiling_is_invalid(self):
        pkg = self._package(
            repair_ceiling={"original_changed_lines": 86, "budget_lines": 43, "cap_source": "complexity:medium"},
            repairs=[{"finding_id": "F-1", "changed_lines": 44}],
        )
        data = _feature([pkg])
        data["acceptance_criteria"] = ["AC-01"]
        errors = model.validate_state(data)
        self.assertTrue(any("repair changed_lines" in e for e in errors), errors)

    def test_repair_without_changed_lines_recorded_is_not_flagged(self):
        # Repairs recorded before this contract existed carry no changed_lines -- never
        # backfilled, never flagged (same precedent as late_reviews/spawns elsewhere).
        pkg = self._package(
            repair_ceiling={"original_changed_lines": 86, "budget_lines": 43, "cap_source": "complexity:medium"},
            repairs=[{"finding_id": "F-1"}],
        )
        data = _feature([pkg])
        data["acceptance_criteria"] = ["AC-01"]
        self.assertEqual(model.validate_state(data), [])


class FreezeCandidateAndReceiptCliTests(unittest.TestCase):
    """freeze-candidate/record-receipt exercised through the real CLI against an
    isolated temp git repo (never SET-AGENTES's own history)."""

    def _init(self, state, feature_id="feat"):
        spec = Path(state).parent / f"{feature_id}-spec.md"
        spec.parent.mkdir(parents=True, exist_ok=True)
        spec.write_text("# contract\n")
        digest = hashlib.sha256(spec.read_bytes()).hexdigest()
        _run("init", feature_id, str(spec), digest, "--state-file", str(state), "--approved-by", "test")

    def _drive_to_gates(self, state, repo, package_id="PKG-01"):
        self._init(state)
        _run("create-package", package_id, "objective", "--state-file", str(state),
             "--complexity", "small", "--ac", "AC-01", "--task", "T1", "--actor", "test", cwd=repo)
        _run("transition", "PACKAGE_IMPLEMENTATION", "--package-id", package_id,
             "--state-file", str(state), "--actor", "test", cwd=repo)
        _run("start-task", package_id, "T1", "--state-file", str(state), "--actor", "test", cwd=repo)
        _run("complete-task", package_id, "T1", "--validation", "local-check",
             "--state-file", str(state), "--actor", "test", cwd=repo)
        _run("update-package", package_id, "--state-file", str(state), "--actor", "test",
             "--diff-ref", "candidate", "--integrated", "true", cwd=repo)
        _run("transition", "PACKAGE_GATES", "--package-id", package_id,
             "--state-file", str(state), "--actor", "test", cwd=repo)

    def _advance_from_gates_to_runtime_qa_passed(self, state, repo, package_id="PKG-01"):
        """Caller must already be at PACKAGE_GATES (via `_drive_to_gates`) --
        this does not re-init/re-create the package."""
        _run("transition", "PACKAGE_REVIEW", "--package-id", package_id,
             "--state-file", str(state), "--actor", "test", cwd=repo)
        _run("record-review", package_id, "pass", "--state-file", str(state), "--actor", "test",
             "--evidence", "clean", cwd=repo)
        _run("record-testing", package_id, "pass", "--state-file", str(state), "--actor", "test",
             "--evidence", "clean", cwd=repo)
        _run("record-runtime-qa", package_id, "pass", "--state-file", str(state), "--actor", "test",
             "--evidence", "clean", cwd=repo)

    def test_freeze_candidate_persists_identity(self):
        with tempfile.TemporaryDirectory() as td:
            repo, base_sha, candidate_sha = _make_repo(td)
            state = Path(td) / "state.json"
            self._drive_to_gates(state, repo)
            result = _run("freeze-candidate", "PKG-01", "--state-file", str(state), "--actor", "test",
                          "--baseline", base_sha, "--candidate-ref", candidate_sha, cwd=repo)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            data = json.loads(state.read_text())
            identity = data["packages"][0]["candidate_identity"]
            self.assertEqual(identity["generation"], 1)
            self.assertEqual(identity["base_tree"], _git("rev-parse", f"{base_sha}^{{tree}}", cwd=repo).stdout.strip())

    def test_freeze_candidate_rejects_wrong_phase(self):
        with tempfile.TemporaryDirectory() as td:
            repo, base_sha, candidate_sha = _make_repo(td)
            state = Path(td) / "state.json"
            self._init(state)
            _run("create-package", "PKG-01", "objective", "--state-file", str(state),
                 "--complexity", "small", "--ac", "AC-01", "--actor", "test", cwd=repo)
            result = _run("freeze-candidate", "PKG-01", "--state-file", str(state), "--actor", "test",
                          "--baseline", base_sha, "--candidate-ref", candidate_sha, cwd=repo, check=False)
            self.assertEqual(result.returncode, 2)
            self.assertIn("cannot freeze candidate from phase", result.stdout)

    def test_record_receipt_mints_after_full_acceptance_chain(self):
        with tempfile.TemporaryDirectory() as td:
            repo, base_sha, candidate_sha = _make_repo(td)
            state = Path(td) / "state.json"
            self._drive_to_gates(state, repo)
            _run("freeze-candidate", "PKG-01", "--state-file", str(state), "--actor", "test",
                 "--baseline", base_sha, "--candidate-ref", candidate_sha, cwd=repo)
            self._advance_from_gates_to_runtime_qa_passed(state, repo)
            result = _run("record-receipt", "PKG-01", "--state-file", str(state), "--actor", "test", cwd=repo)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            data = json.loads(state.read_text())
            receipt = data["packages"][0]["receipt"]
            self.assertEqual(receipt["terminal_state"], "accepted")
            self.assertEqual(receipt["review_verdict"], "pass")
            self.assertEqual(receipt["candidate_tree"], data["packages"][0]["candidate_identity"]["candidate_tree"])

    def test_record_receipt_fails_closed_without_a_freeze(self):
        with tempfile.TemporaryDirectory() as td:
            repo, base_sha, candidate_sha = _make_repo(td)
            state = Path(td) / "state.json"
            self._drive_to_gates(state, repo)
            self._advance_from_gates_to_runtime_qa_passed(state, repo)
            result = _run("record-receipt", "PKG-01", "--state-file", str(state), "--actor", "test",
                          cwd=repo, check=False)
            self.assertEqual(result.returncode, 2)
            self.assertIn("requires a prior freeze-candidate", result.stdout)

    def test_record_receipt_fails_closed_when_candidate_drifted_after_freeze(self):
        with tempfile.TemporaryDirectory() as td:
            repo, base_sha, candidate_sha = _make_repo(td)
            state = Path(td) / "state.json"
            self._drive_to_gates(state, repo)
            _run("freeze-candidate", "PKG-01", "--state-file", str(state), "--actor", "test",
                 "--baseline", base_sha, "--candidate-ref", "HEAD", cwd=repo)
            self._advance_from_gates_to_runtime_qa_passed(state, repo)
            # Someone commits more after the freeze, without re-freezing.
            (repo / "d.txt").write_text("post-freeze drift\n")
            _git("add", "-A", cwd=repo)
            _git("commit", "-q", "-m", "drift", cwd=repo)
            result = _run("record-receipt", "PKG-01", "--state-file", str(state), "--actor", "test",
                          cwd=repo, check=False)
            self.assertEqual(result.returncode, 2)
            self.assertIn("no longer matches its frozen identity", result.stdout)


if __name__ == "__main__":
    unittest.main()
