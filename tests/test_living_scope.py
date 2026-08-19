"""Feature 017 PKG-E (ADR-0028) — living scope: spec drift detection, amend-spec,
supersede-package. Real CLI against a synthetic project (suite convention)."""

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FEATURE_STATE = ROOT / "PROYECTO/ai/scripts/feature-state.py"


def _run(tmp, *args, check=False):
    result = subprocess.run(
        [sys.executable, str(FEATURE_STATE), *args],
        cwd=tmp, capture_output=True, text=True,
    )
    if check and result.returncode != 0:
        raise AssertionError(result.stdout + result.stderr)
    return result


def _axes_log(tmp: Path, fid: str) -> Path:
    axes_log = tmp / "ai/state/axes-log.jsonl"
    axes_log.parent.mkdir(parents=True, exist_ok=True)
    axes_rows = [
        {"at": "2026-08-15T00:00:00Z", "feature_id": fid, "axis": axis,
         "stance": "deferred", "origin": "n/a", "reason": "not decided yet"}
        for axis in ("data-store", "api-gateway", "deploy-platform", "audience", "embeddings",
                     "realtime", "mobile", "auth", "cost", "legal")
    ]
    axes_log.write_text("\n".join(json.dumps(row, sort_keys=True) for row in axes_rows) + "\n")
    return axes_log


def _init_feature(tmp: Path, fid="020-scope"):
    spec = tmp / "docs/specs" / fid / "spec.md"
    spec.parent.mkdir(parents=True, exist_ok=True)
    spec.write_text("# Spec v1\n\nAlcance original.\n", encoding="utf-8")
    digest = hashlib.sha256(spec.read_bytes()).hexdigest()
    (tmp / "ai/state/features").mkdir(parents=True, exist_ok=True)
    axes_log = _axes_log(tmp, fid)
    _run(tmp, "init", fid, str(spec.relative_to(tmp)), digest,
         "--approved-by", "tester", "--ac", "AC-01", "--axes-log", str(axes_log),
         "--risk-signal", "user-asked-full-pipeline", check=True)
    return fid, spec


class SpecDriftTests(unittest.TestCase):
    def test_next_warns_on_drift_and_stays_silent_when_clean(self):
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            fid, spec = _init_feature(tmp)
            clean = json.loads(_run(tmp, "next", fid, check=True).stdout)
            self.assertNotIn("spec_drift", clean)
            spec.write_text("# Spec v2 (editado sin aprobar)\n", encoding="utf-8")
            drifted = json.loads(_run(tmp, "next", fid, check=True).stdout)
            self.assertIn("SPEC_DRIFT", drifted.get("spec_drift", ""))
            resumed = json.loads(_run(tmp, "resume", fid, check=True).stdout)
            self.assertIn("SPEC_DRIFT", resumed.get("spec_drift", ""))

    def test_amend_spec_records_history_and_clears_drift(self):
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            fid, spec = _init_feature(tmp)
            spec.write_text("# Spec v2\n\nAlcance nuevo aprobado.\n", encoding="utf-8")
            result = _run(tmp, "amend-spec", "--feature-id", fid,
                          "--reason", "el cliente amplió el alcance",
                          "--approved-by", "tester", check=True)
            state = json.loads(result.stdout)["state"]
            self.assertEqual(len(state["spec_amendments"]), 1)
            amendment = state["spec_amendments"][0]
            self.assertEqual(amendment["reason"], "el cliente amplió el alcance")
            self.assertNotEqual(amendment["old_hash"], amendment["hash"])
            self.assertEqual(state["approved_spec"]["hash"], amendment["hash"])
            clean = json.loads(_run(tmp, "next", fid, check=True).stdout)
            self.assertNotIn("spec_drift", clean)

    def test_amend_spec_refuses_when_nothing_changed(self):
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            fid, _ = _init_feature(tmp)
            result = _run(tmp, "amend-spec", "--feature-id", fid,
                          "--reason", "x", "--approved-by", "tester")
            self.assertEqual(result.returncode, 2)
            self.assertIn("nada que enmendar", result.stdout)


class SupersedePackageTests(unittest.TestCase):
    def _create_package(self, tmp, fid, pid="PKG-01"):
        _run(tmp, "create-package", pid, "objetivo obsoleto", "--feature-id", fid,
             "--ac", "AC-01", "--owned-path", "src/", "--complexity", "small",
             "--task", "T1: tarea única", check=True)
        return pid

    def test_superseded_package_stops_blocking_and_its_acs_stop_counting(self):
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            fid, spec = _init_feature(tmp)
            pid = self._create_package(tmp, fid)
            result = _run(tmp, "supersede-package", pid, "--feature-id", fid,
                          "--reason", "el alcance nuevo lo dejó sin objeto", check=True)
            state = json.loads(result.stdout)["state"]
            package = state["packages"][0]
            self.assertEqual(package["status"], "superseded")
            self.assertEqual(package["superseded"]["reason"], "el alcance nuevo lo dejó sin objeto")
            # done_ready: the superseded package no longer blocks on status, but its
            # AC is uncovered again — exactly the honest remaining error.
            sys.path.insert(0, str(ROOT / "ai/scripts"))
            from feature_state_lib.model import done_ready
            errors = done_ready(state)
            self.assertNotIn("all packages must be accepted", errors)
            self.assertIn("not all acceptance criteria are covered by accepted packages", errors)

    def test_an_accepted_package_cannot_be_superseded(self):
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            fid, _ = _init_feature(tmp)
            pid = self._create_package(tmp, fid)
            # Force-accept via raw state edit (unit-level shortcut: the CLI's own
            # accept path needs the whole pipeline, which is not under test here).
            state_file = tmp / "ai/state/features" / f"{fid}.json"
            data = json.loads(state_file.read_text())
            data["packages"][0]["status"] = "accepted"
            state_file.write_text(json.dumps(data))
            result = _run(tmp, "supersede-package", pid, "--feature-id", fid,
                          "--reason", "no debería poder")
            self.assertEqual(result.returncode, 2)
            self.assertIn("no se retira", result.stdout)


class AcceptUnderDriftTests(unittest.TestCase):
    def test_accept_package_refuses_under_spec_drift(self):
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            fid, spec = _init_feature(tmp)
            # Reach PACKAGE_RUNTIME_QA cheaply: accept-package checks drift BEFORE
            # phase/package preconditions would matter, so a hand-set phase is enough.
            state_file = tmp / "ai/state/features" / f"{fid}.json"
            data = json.loads(state_file.read_text())
            data["phase"] = "PACKAGE_RUNTIME_QA"
            state_file.write_text(json.dumps(data))
            spec.write_text("# Spec cambiado sin aprobar\n", encoding="utf-8")
            result = _run(tmp, "accept-package", "PKG-01", "--feature-id", fid)
            self.assertEqual(result.returncode, 2)
            self.assertIn("SPEC_DRIFT", result.stdout)


class DoctrineTests(unittest.TestCase):
    def test_orchestrator_doctrine_names_the_amend_flow(self):
        text = (ROOT / "Global/_canonical/agents/orchestrator.md").read_text()
        self.assertIn("amend-spec", text)
        self.assertIn("supersede-package", text)
        self.assertIn("`init --force` is never the answer to a scope change", text)


if __name__ == "__main__":
    unittest.main()
