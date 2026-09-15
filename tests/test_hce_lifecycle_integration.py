"""HCE lifecycle integration tests — panel, linked repair, receipt, wrapper (AC-01/03/06/07/11)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ai/scripts"))

from tests.test_hce_convergence_core import (  # noqa: E402
    CIRCULAR_TASK,
    FEATURE_STATE,
    FINDING_IDS,
    PARENT_ID,
    _make_hce_repo,
    _minimal_state,
    _parse_json,
    _prepare_fixture,
    _reentered_fixture,
    _run_fs,
    _write_state,
)
from tests.test_hce_convergence_core import HceInspectVerifyReadOnlyTests  # noqa: E402

INTEGRATION_ACTION = ROOT / "ai/scripts/integration_action.py"
import coord_policy  # noqa: E402


def _panel_cycle(repo: Path, state: Path, exc_id: str, *, event_prefix: str = "evt-panel") -> str:
    rev = json.loads(state.read_text())["revision"]
    roles = ["--role", "package-reviewer", "--role", "security-auditor"]
    start = _run_fs(
        "start-review-panel", PARENT_ID,
        *roles,
        "--convergence-exception-id", exc_id,
        "--actor", "orchestrator",
        "--event-id", f"{event_prefix}-start",
        "--expect-revision", str(rev),
        cwd=repo, state_file=state, check=False,
    )
    assert start.returncode == 0, start.stderr + start.stdout
    rev = json.loads(state.read_text())["revision"]
    for idx, role in enumerate(["package-reviewer", "security-auditor"]):
        proc = _run_fs(
            "record-subreview", PARENT_ID, role, "repair_required",
            "--convergence-exception-id", exc_id,
            "--actor", "orchestrator",
            "--event-id", f"{event_prefix}-sub-{idx}",
            "--expect-revision", str(rev),
            cwd=repo, state_file=state, check=False,
        )
        assert proc.returncode == 0, proc.stderr + proc.stdout
        rev = json.loads(state.read_text())["revision"]
    final = _run_fs(
        "finalize-review-panel", PARENT_ID, "repair_required",
        "--convergence-exception-id", exc_id,
        "--actor", "orchestrator",
        "--event-id", f"{event_prefix}-final",
        "--expect-revision", str(rev),
        cwd=repo, state_file=state, check=False,
    )
    assert final.returncode == 0, final.stderr + final.stdout
    data = json.loads(state.read_text())
    return data["packages"][0]["convergence_exception"]["final_panel_id"]


def _consumed_fixture(td_path: Path) -> tuple[Path, Path, str, str, str]:
    repo, state, exc_id, _ = _reentered_fixture(td_path)
    _panel_cycle(repo, state, exc_id)
    rev = json.loads(state.read_text())["revision"]
    auth = _run_fs(
        "authorize-convergence", PARENT_ID,
        "--exception-id", exc_id,
        "--authorized-by", "operator",
        "--reason", "final panel bound",
        "--approval-evidence", "panel-evidence",
        "--actor", "orchestrator",
        "--event-id", "evt-life-authorize",
        "--expect-revision", str(rev),
        cwd=repo, state_file=state, check=False,
    )
    assert auth.returncode == 0, auth.stderr + auth.stdout
    rev = json.loads(state.read_text())["revision"]
    consume = _run_fs(
        "consume-convergence", PARENT_ID,
        "--exception-id", exc_id,
        "--actor", "orchestrator",
        "--event-id", "evt-life-consume",
        "--expect-revision", str(rev),
        cwd=repo, state_file=state, check=False,
    )
    assert consume.returncode == 0, consume.stderr + consume.stdout
    payload = _parse_json(consume.stdout)
    outcome_id = payload["outcome_id"]
    combined_sha = json.loads(state.read_text())["packages"][0]["convergence_exception"]["combined_review_identity"]["candidate_commit"]
    return repo, state, exc_id, outcome_id, combined_sha


class HceLifecycleFlagTests(unittest.TestCase):
    def test_start_panel_denies_missing_exception_flag(self):
        with tempfile.TemporaryDirectory() as td:
            repo, state, exc_id, _ = _reentered_fixture(Path(td))
            rev = json.loads(state.read_text())["revision"]
            proc = _run_fs(
                "start-review-panel", PARENT_ID,
                "--role", "package-reviewer",
                "--role", "security-auditor",
                "--actor", "orchestrator",
                "--event-id", "evt-no-flag",
                "--expect-revision", str(rev),
                cwd=repo, state_file=state, check=False,
            )
            self.assertEqual(proc.returncode, 2)
            payload = _parse_json(proc.stdout)
            self.assertFalse(payload["ok"])
            self.assertIn("HCE_DENIED", payload["error"])
            self.assertEqual(json.loads(state.read_text())["revision"], rev)

    def test_start_panel_denies_flag_on_ordinary_package(self):
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            repo, base_sha, original_sha, _, _ = _make_hce_repo(td_path)
            state = td_path / "ordinary.json"
            data = _minimal_state(state, repo, base_sha, original_sha)
            data["packages"][0]["convergence_exception"] = None
            data["phase"] = "PACKAGE_REVIEW"
            _write_state(state, data)
            rev = data["revision"]
            proc = _run_fs(
                "start-review-panel", PARENT_ID,
                "--role", "package-reviewer",
                "--convergence-exception-id", "00000000-0000-4000-8000-000000000001",
                "--actor", "orchestrator",
                "--event-id", "evt-ordinary-flag",
                "--expect-revision", str(rev),
                cwd=repo, state_file=state, check=False,
            )
            self.assertEqual(proc.returncode, 2)
            self.assertIn("HCE_DENIED", _parse_json(proc.stdout)["error"])


class HceLifecyclePanelTests(unittest.TestCase):
    def test_panel_binds_combined_identity_and_spends_cycle_two(self):
        with tempfile.TemporaryDirectory() as td:
            repo, state, exc_id, _ = _reentered_fixture(Path(td))
            panel_id = _panel_cycle(repo, state, exc_id)
            data = json.loads(state.read_text())
            parent = data["packages"][0]
            exc = parent["convergence_exception"]
            self.assertEqual(exc["final_panel_id"], panel_id)
            panel = parent["review_panels"][-1]
            self.assertEqual(panel["roles"], ["package-reviewer", "security-auditor"])
            self.assertEqual(panel["verdict"], "repair_required")
            self.assertIn("convergence_binding", panel)
            self.assertEqual(panel["convergence_binding"]["exception_id"], exc_id)
            self.assertEqual(parent["attempts"]["deep_review_cycles"], 2)
            self.assertEqual(data["phase"], "PACKAGE_REPAIR")

    def test_finalize_panel_denies_pass_verdict(self):
        with tempfile.TemporaryDirectory() as td:
            repo, state, exc_id, _ = _reentered_fixture(Path(td))
            rev = json.loads(state.read_text())["revision"]
            _run_fs(
                "start-review-panel", PARENT_ID,
                "--role", "package-reviewer", "--role", "security-auditor",
                "--convergence-exception-id", exc_id,
                "--actor", "orchestrator", "--event-id", "evt-pass-panel-start",
                "--expect-revision", str(rev),
                cwd=repo, state_file=state, check=False,
            )
            rev = json.loads(state.read_text())["revision"]
            for role in ("package-reviewer", "security-auditor"):
                _run_fs(
                    "record-subreview", PARENT_ID, role, "repair_required",
                    "--convergence-exception-id", exc_id,
                    "--actor", "orchestrator", "--event-id", f"evt-pass-sub-{role}",
                    "--expect-revision", str(rev),
                    cwd=repo, state_file=state, check=False,
                )
                rev = json.loads(state.read_text())["revision"]
            proc = _run_fs(
                "finalize-review-panel", PARENT_ID, "pass",
                "--convergence-exception-id", exc_id,
                "--actor", "orchestrator", "--event-id", "evt-pass-final",
                "--expect-revision", str(rev),
                cwd=repo, state_file=state, check=False,
            )
            self.assertEqual(proc.returncode, 2)
            self.assertIn("HCE_DENIED", _parse_json(proc.stdout)["error"])


class HceLifecycleLinkedRepairTests(unittest.TestCase):
    def test_linked_repair_closes_ten_and_completes_circular_task(self):
        with tempfile.TemporaryDirectory() as td:
            repo, state, exc_id, outcome_id, combined_sha = _consumed_fixture(Path(td))
            rev = json.loads(state.read_text())["revision"]
            finding_args = []
            for fid in FINDING_IDS:
                finding_args.extend(["--finding-id", fid])
            proc = _run_fs(
                "record-repair", PARENT_ID,
                *finding_args,
                "--commit", combined_sha,
                "--convergence-outcome-id", outcome_id,
                "--actor", "orchestrator",
                "--event-id", "evt-linked-repair",
                "--expect-revision", str(rev),
                cwd=repo, state_file=state, check=False,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
            data = json.loads(state.read_text())
            parent = data["packages"][0]
            self.assertEqual(data["phase"], "DELTA_REVIEW")
            repairs = parent["repairs"]
            self.assertEqual(len(repairs), 1)
            self.assertEqual(set(repairs[0]["finding_ids"]), set(FINDING_IDS))
            self.assertEqual(repairs[0]["outcome_id"], outcome_id)
            self.assertEqual(parent["attempts"]["repair_batches"], 1)
            circular = next(t for t in parent["tasks"] if t["id"] == CIRCULAR_TASK)
            self.assertEqual(circular["status"], "completed")
            for finding in parent["findings"]:
                self.assertEqual(finding["status"], "closed")
                self.assertEqual(finding["repair_attempts"], 1)

    def test_linked_repair_denies_duplicate(self):
        with tempfile.TemporaryDirectory() as td:
            repo, state, exc_id, outcome_id, combined_sha = _consumed_fixture(Path(td))
            rev = json.loads(state.read_text())["revision"]
            finding_args = []
            for fid in FINDING_IDS:
                finding_args.extend(["--finding-id", fid])
            common = [
                "record-repair", PARENT_ID,
                *finding_args,
                "--commit", combined_sha,
                "--convergence-outcome-id", outcome_id,
                "--actor", "orchestrator",
            ]
            first = _run_fs(*common, "--event-id", "evt-dup-1", "--expect-revision", str(rev),
                            cwd=repo, state_file=state, check=False)
            self.assertEqual(first.returncode, 0, first.stderr + first.stdout)
            rev = json.loads(state.read_text())["revision"]
            data = json.loads(state.read_text())
            data["phase"] = "PACKAGE_REPAIR"
            _write_state(state, data)
            second = _run_fs(*common, "--event-id", "evt-dup-2", "--expect-revision", str(rev),
                             cwd=repo, state_file=state, check=False)
            self.assertEqual(second.returncode, 2)
            self.assertIn("HCE_REPLAY", _parse_json(second.stdout)["error"])


class HceLifecycleReceiptTests(unittest.TestCase):
    def test_convergence_receipt_schema_and_original_identity_unchanged(self):
        with tempfile.TemporaryDirectory() as td:
            repo, state, exc_id, outcome_id, combined_sha = _consumed_fixture(Path(td))
            original_before = json.dumps(json.loads(state.read_text())["packages"][0]["candidate_identity"], sort_keys=True)
            rev = json.loads(state.read_text())["revision"]
            finding_args = []
            for fid in FINDING_IDS:
                finding_args.extend(["--finding-id", fid])
            _run_fs(
                "record-repair", PARENT_ID, *finding_args,
                "--commit", combined_sha,
                "--convergence-outcome-id", outcome_id,
                "--actor", "orchestrator", "--event-id", "evt-receipt-repair",
                "--expect-revision", str(rev),
                cwd=repo, state_file=state, check=False,
            )
            rev = json.loads(state.read_text())["revision"]
            closed = []
            for fid in FINDING_IDS:
                closed.extend(["--closed-finding", fid])
            _run_fs(
                "record-delta-review", PARENT_ID, "pass",
                *closed,
                "--convergence-outcome-id", outcome_id,
                "--actor", "orchestrator", "--event-id", "evt-receipt-delta",
                "--expect-revision", str(rev),
                cwd=repo, state_file=state, check=False,
            )
            rev = json.loads(state.read_text())["revision"]
            _run_fs(
                "record-testing", PARENT_ID, "pass",
                "--actor", "orchestrator", "--event-id", "evt-receipt-testing",
                "--expect-revision", str(rev),
                cwd=repo, state_file=state, check=False,
            )
            rev = json.loads(state.read_text())["revision"]
            _run_fs(
                "record-runtime-qa", PARENT_ID, "pass",
                "--actor", "orchestrator", "--event-id", "evt-receipt-runtime",
                "--expect-revision", str(rev),
                cwd=repo, state_file=state, check=False,
            )
            rev = json.loads(state.read_text())["revision"]
            _run_fs(
                "accept-package", PARENT_ID,
                "--actor", "orchestrator", "--event-id", "evt-receipt-accept",
                "--expect-revision", str(rev),
                cwd=repo, state_file=state, check=False,
            )
            rev = json.loads(state.read_text())["revision"]
            proc = _run_fs(
                "record-receipt", PARENT_ID,
                "--convergence-outcome-id", outcome_id,
                "--actor", "orchestrator",
                "--event-id", "evt-receipt",
                "--expect-revision", str(rev),
                cwd=repo, state_file=state, check=False,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
            data = json.loads(state.read_text())
            parent = data["packages"][0]
            receipt = parent["receipt"]
            self.assertEqual(receipt["schema"], "set-agentes.convergence-integration-receipt/v1")
            self.assertEqual(receipt["convergence_outcome_id"], outcome_id)
            self.assertEqual(receipt["exception_id"], exc_id)
            original_after = json.dumps(parent["candidate_identity"], sort_keys=True)
            self.assertEqual(original_after, original_before)


class HceLifecycleWrapperTests(unittest.TestCase):
    def test_absolute_wrapper_allows_adjacent_feature_state(self):
        wrapper = str(INTEGRATION_ACTION.resolve())
        inner = str((ROOT / "ai/scripts/feature-state.py").resolve())
        cmd = f"python3 {wrapper} /tmp/state.json {PARENT_ID} transition -- python3 {inner} transition INTEGRATION --package-id {PARENT_ID}"
        self.assertTrue(coord_policy.allowed(cmd))

    def test_wrapper_rejects_mismatched_state_file(self):
        with tempfile.TemporaryDirectory() as td:
            repo, state, exc_id, outcome_id, combined_sha = _consumed_fixture(Path(td))
            other_state = Path(td) / "other.json"
            other_state.write_text(state.read_text())
            cmd = [
                "python3", str(INTEGRATION_ACTION), str(state.resolve()), PARENT_ID, "record-receipt", "--",
                "python3", "ai/scripts/feature-state.py", "record-receipt", PARENT_ID,
                "--state-file", str(other_state.resolve()),
                "--convergence-outcome-id", outcome_id,
            ]
            proc = subprocess.run(cmd, cwd=repo, env=os.environ.copy(), text=True, capture_output=True, check=False)
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("state-file", proc.stdout + proc.stderr)


class HceLifecycleE2eTests(unittest.TestCase):
    def test_verify_after_linked_repair_successor(self):
        with tempfile.TemporaryDirectory() as td:
            repo, state, exc_id, outcome_id, combined_sha = _consumed_fixture(Path(td))
            rev = json.loads(state.read_text())["revision"]
            finding_args = []
            for fid in FINDING_IDS:
                finding_args.extend(["--finding-id", fid])
            _run_fs(
                "record-repair", PARENT_ID, *finding_args,
                "--commit", combined_sha,
                "--convergence-outcome-id", outcome_id,
                "--actor", "orchestrator", "--event-id", "evt-e2e-repair",
                "--expect-revision", str(rev),
                cwd=repo, state_file=state, check=False,
            )
            verify = _run_fs(
                "verify-convergence-outcome", PARENT_ID,
                "--exception-id", exc_id,
                cwd=repo, state_file=state, check=False,
            )
            self.assertEqual(verify.returncode, 0, verify.stderr + verify.stdout)
            self.assertEqual(_parse_json(verify.stdout)["result"], "HCE_REGISTERED_VALID")


if __name__ == "__main__":
    unittest.main()
