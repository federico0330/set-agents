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


def _run(*args, check=True):
    return subprocess.run(
        ["python3", str(FEATURE_STATE), *args],
        cwd=ROOT, env=os.environ.copy(), text=True, capture_output=True, check=check,
    )


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


if __name__ == "__main__":
    unittest.main()
