"""HCE core convergence tests (AC-01–05, AC-08–10, CLI AC-11).

Uses committed temporary Git repos, canonical external state, isolated CWD.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
import uuid
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ai/scripts"))
from feature_state_lib.convergence_git import (  # noqa: E402
    git_common_dir,
    measure_combined_identity,
    measure_original_identity,
    paths_digest_b64,
)
from feature_state_lib import candidate_identity  # noqa: E402
from feature_state_lib.convergence_constants import SCHEMA  # noqa: E402
from feature_state_lib.convergence_policy import (  # noqa: E402
    canonical_json_digest,
    compute_binding_digest,
    finding_snapshot_from_package,
)
FEATURE_STATE = ROOT / "ai/scripts/feature-state.py"
CHECK_OWNED = ROOT / "ai/scripts/check-owned-paths.py"

PROFILE = "SVR-P1A1-DISCOVERY/v1"
FEATURE_ID = "sync-vps-runtime"
PARENT_ID = "SVR-P1A1-DISCOVERY"
CHILD_A = "SVR-P1A1A-TS-RESOLVER"
CHILD_B = "SVR-P1A1B-STRUCTURAL-DISCOVERY"
CIRCULAR_TASK = (
    "Converge accepted TypeScript resolver and structural discovery children "
    "with full final panel and all ten original finding closures"
)

PATH_RESOLVER = "scripts/sync-vps/typescript-dispatch-resolver.ts"
PATH_RESOLVER_TEST = "scripts/sync-vps/__tests__/typescript-dispatch-resolver.test.ts"
PATH_DISCOVERY = "scripts/sync-vps/source-discovery.ts"
PATH_DISCOVERY_TEST = "scripts/sync-vps/__tests__/source-discovery.test.ts"
ALL_FOUR_PATHS = [PATH_RESOLVER, PATH_RESOLVER_TEST, PATH_DISCOVERY, PATH_DISCOVERY_TEST]

FINDING_IDS = [f"SVR-P1A1-{n:03d}" for n in range(1, 11)]


def _git(*args, cwd: Path, check: bool = True):
    return subprocess.run(
        ["git", *args], cwd=cwd, env=os.environ.copy(), text=True,
        capture_output=True, check=check,
    )


def _run_fs(*args, cwd: Path, state_file: Path, check: bool = True):
    # absolute() preserves symlink final component; resolve() would hide alias tests
    cmd = ["python3", str(FEATURE_STATE), *args, "--state-file", str(state_file.absolute())]
    return subprocess.run(cmd, cwd=cwd, env=os.environ.copy(), text=True, capture_output=True, check=check)


def _run_owned(*args, check: bool = True):
    return subprocess.run(
        ["python3", str(CHECK_OWNED), *args],
        env=os.environ.copy(), text=True, capture_output=True, check=check,
    )


def _canonical_digest(obj: dict) -> str:
    payload = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return "sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _paths_digest_b64(paths: list[str]) -> str:
    records = b"".join(len(p.encode()).to_bytes(8, "big") + p.encode() for p in sorted(paths, key=lambda x: x.encode()))
    return "sha256:" + hashlib.sha256(records).hexdigest()


def _make_hce_repo(td: Path) -> tuple[Path, str, str, str, str]:
    """Create repo with base, original parent candidate, and combined child-B HEAD."""
    repo = td / "worktree"
    repo.mkdir(parents=True)
    sync = repo / "scripts/sync-vps"
    tests_dir = sync / "__tests__"
    tests_dir.mkdir(parents=True)

    _git("init", "-q", cwd=repo)
    _git("config", "user.email", "hce@test.local", cwd=repo)
    _git("config", "user.name", "HCE Test", cwd=repo)

    # Base commit (empty scaffold)
    (repo / "README.md").write_text("base\n")
    _git("add", "-A", cwd=repo)
    _git("commit", "-q", "-m", "base", cwd=repo)
    base_sha = _git("rev-parse", "HEAD", cwd=repo).stdout.strip()
    base_tree = _git("rev-parse", f"{base_sha}^{{tree}}", cwd=repo).stdout.strip()

    # Original parent candidate: discovery files only (336 added lines for profile constant)
    (sync / "source-discovery.ts").write_text("// discovery v1\n" * 252)
    (tests_dir / "source-discovery.test.ts").write_text("// discovery test v1\n" * 84)
    _git("add", "-A", cwd=repo)
    _git("commit", "-q", "-m", "original-parent", cwd=repo)
    original_sha = _git("rev-parse", "HEAD", cwd=repo).stdout.strip()
    original_tree = _git("rev-parse", f"{original_sha}^{{tree}}", cwd=repo).stdout.strip()

    # Child A output on top of original
    (sync / "typescript-dispatch-resolver.ts").write_text("// resolver\n" * 15)
    (tests_dir / "typescript-dispatch-resolver.test.ts").write_text("// resolver test\n" * 8)
    _git("add", "-A", cwd=repo)
    _git("commit", "-q", "-m", "child-a", cwd=repo)
    child_a_sha = _git("rev-parse", "HEAD", cwd=repo).stdout.strip()

    # Child B output on top of A (combined final)
    (sync / "source-discovery.ts").write_text("// discovery v2 combined\n" * 25)
    (tests_dir / "source-discovery.test.ts").write_text("// discovery test v2\n" * 12)
    _git("add", "-A", cwd=repo)
    _git("commit", "-q", "-m", "child-b-final", cwd=repo)
    combined_sha = _git("rev-parse", "HEAD", cwd=repo).stdout.strip()
    combined_tree = _git("rev-parse", f"{combined_sha}^{{tree}}", cwd=repo).stdout.strip()

    child_a_sha = _git("rev-parse", "HEAD~1", cwd=repo).stdout.strip()
    return repo, base_sha, original_sha, child_a_sha, combined_sha


def _finding(id_: str) -> dict:
    evidence_obj = {"id": id_, "evidence": f"evidence for {id_}"}
    definition_obj = {"id": id_, "required_outcome": "fix", "severity": "high"}
    return {
        "id": id_,
        "severity": "high",
        "category": "correctness",
        "acceptance_criterion": "AC-02",
        "file": PATH_DISCOVERY,
        "line": 1,
        "evidence": f"evidence for {id_}",
        "reproduction": "repro",
        "required_outcome": "fix",
        "status": "open",
        "verified_at": "2026-09-15T13:08:58+00:00",
        "verified_by": "finding-verifier",
        "verified_verdict": "upheld",
        "repair_attempts": 0,
        "verification_digest": _canonical_digest(evidence_obj),
        "definition_digest": _canonical_digest(definition_obj),
    }


def _derive_original_identity(repo: Path, base_sha: str, original_sha: str) -> dict:
    seed = {
        "baseline_ref": base_sha,
        "candidate_ref": original_sha,
        "generation": 1,
        "frozen_at": "2026-09-15T12:45:54+00:00",
        "frozen_by": "gate-runner",
    }
    prev = os.getcwd()
    os.chdir(repo)
    try:
        measured = measure_original_identity(repo, seed)
    finally:
        os.chdir(prev)
    measured["generation"] = 1
    measured["frozen_at"] = seed["frozen_at"]
    measured["frozen_by"] = seed["frozen_by"]
    return measured


def _minimal_state(state_path: Path, repo: Path, base_sha: str, original_sha: str, revision: int = 0) -> dict:
    candidate_identity = _derive_original_identity(repo, base_sha, original_sha)
    assert candidate_identity["changed_lines"] == 336, candidate_identity["changed_lines"]
    parent = {
        "package_id": PARENT_ID,
        "objective": "P1A1 discovery",
        "status": "planning",
        "complexity": "high",
        "acceptance_criteria": ["AC-02", "AC-03"],
        "owned_paths": [PATH_DISCOVERY, PATH_DISCOVERY_TEST],
        "read_only_paths": [],
        "shared_paths": [],
        "approved_exceptions": [],
        "attempts": {"deep_review_cycles": 1, "repair_batches": 0, "spawns": 0, "subdivisions": 0},
        "candidate_identity": candidate_identity,
        "findings": [_finding(fid) for fid in FINDING_IDS],
        "review_panels": [{
            "panel_id": "SVR-P1A1-REVIEW-01",
            "status": "completed",
            "verdict": "repair_required",
            "started_at": "2026-09-15T12:47:38+00:00",
            "completed_at": "2026-09-15T12:59:47+00:00",
            "roles": ["package-reviewer", "security-auditor"],
            "subreviews": [],
        }],
        "repairs": [],
        "repair_ceiling": None,
        "tasks": [
            {"id": "task-done", "status": "completed", "blockers": [], "local_validations": []},
            {"id": CIRCULAR_TASK, "status": "planned", "blockers": [], "local_validations": []},
        ],
        "gates": [],
        "delta_reviews": [],
        "receipt": None,
    }
    child_a_pkg = {
        "package_id": CHILD_A,
        "objective": "resolver",
        "status": "accepted",
        "acceptance_criteria": ["AC-02"],
        "owned_paths": [PATH_RESOLVER, PATH_RESOLVER_TEST],
        "read_only_paths": [],
        "shared_paths": [],
        "approved_exceptions": [],
        "attempts": {},
        "tasks": [],
        "findings": [],
        "receipt": None,
        "candidate_identity": None,
    }
    child_b_pkg = deepcopy(child_a_pkg)
    child_b_pkg.update({
        "package_id": CHILD_B,
        "objective": "structural",
        "owned_paths": [PATH_DISCOVERY, PATH_DISCOVERY_TEST],
    })
    return {
        "schema_version": 1,
        "revision": revision,
        "updated_at": "2026-09-15T14:00:00+00:00",
        "feature_id": FEATURE_ID,
        "phase": "PACKAGE_PLANNING",
        "mode": "feature",
        "approved_spec": {"path": "docs/spec.md", "hash": "abc" * 10 + "abcd"},
        "budgets": {"max_deep_review_cycles": 2, "max_repairs_per_finding": 3, "max_package_subdivisions": 1},
        "acceptance_criteria": ["AC-02", "AC-03"],
        "packages": [parent, child_a_pkg, child_b_pkg],
        "current_package_id": PARENT_ID,
        "history": [],
    }


def _write_state(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def _parse_json(stdout: str) -> dict:
    return json.loads(stdout.strip())


def _freeze(repo: Path, baseline: str, candidate: str, generation: int = 1) -> dict:
    prev = os.getcwd()
    os.chdir(repo)
    try:
        frozen = candidate_identity.freeze(baseline, candidate)
    finally:
        os.chdir(prev)
    frozen["generation"] = generation
    frozen["frozen_at"] = "2026-09-15T14:00:00+00:00"
    frozen["frozen_by"] = "test"
    return frozen


def _receipt(package_id: str, frozen: dict) -> dict:
    return {
        "schema": "set-agentes.integration-receipt/v1",
        "package_id": package_id,
        "generation": frozen["generation"],
        "base_tree": frozen["base_tree"],
        "candidate_tree": frozen["candidate_tree"],
        "paths_digest": frozen["paths_digest"],
        "review_verdict": "pass",
        "delta_review_verdict": "pass",
        "verifications_summary": {"upheld": 0, "refuted": 0},
        "terminal_state": "accepted",
        "minted_at": "2026-09-15T14:00:00+00:00",
        "minted_by": "test",
    }


def _attach_accepted_children(data: dict, repo: Path, original_sha: str, child_a_sha: str, combined_sha: str) -> None:
    child_a_id = CHILD_A
    child_b_id = CHILD_B
    frozen_a = _freeze(repo, original_sha, child_a_sha)
    frozen_b = _freeze(repo, child_a_sha, combined_sha)
    packages = {p["package_id"]: p for p in data["packages"]}
    packages[child_a_id]["status"] = "accepted"
    packages[child_a_id]["candidate_identity"] = frozen_a
    packages[child_a_id]["receipt"] = _receipt(child_a_id, frozen_a)
    packages[child_b_id]["status"] = "accepted"
    packages[child_b_id]["candidate_identity"] = frozen_b
    packages[child_b_id]["receipt"] = _receipt(child_b_id, frozen_b)


def _prepare_fixture(td_path: Path) -> tuple[Path, Path, str, bytes]:
    repo, base_sha, original_sha, child_a_sha, combined_sha = _make_hce_repo(td_path)
    state = td_path / "state.json"
    data = _minimal_state(state, repo, base_sha, original_sha)
    _attach_accepted_children(data, repo, original_sha, child_a_sha, combined_sha)
    original_bytes = json.dumps(data["packages"][0]["candidate_identity"], sort_keys=True).encode()
    _write_state(state, data)
    proc = _run_fs(
        "prepare-convergence", PARENT_ID,
        "--profile", PROFILE,
        "--authorized-by", "operator",
        "--reason", "approved workflow",
        "--approval-evidence", "ticket-1",
        "--actor", "orchestrator",
        "--event-id", "evt-prepare-reenter",
        "--expect-revision", "0",
        cwd=repo, state_file=state, check=False,
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    exc_id = _parse_json(proc.stdout)["exception_id"]
    return repo, state, exc_id, original_bytes


def _reentered_fixture(td_path: Path) -> tuple[Path, Path, str, bytes]:
    repo, state, exc_id, original_bytes = _prepare_fixture(td_path)
    rev = json.loads(state.read_text())["revision"]
    proc = _run_fs(
        "reenter-convergence", PARENT_ID,
        "--exception-id", exc_id,
        "--actor", "orchestrator",
        "--event-id", "evt-reenter-1",
        "--expect-revision", str(rev),
        cwd=repo, state_file=state, check=False,
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    return repo, state, exc_id, original_bytes


class HcePrepareTests(unittest.TestCase):
    def test_prepare_convergence_creates_prepared_record(self):
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            repo, base_sha, original_sha, _, _ = _make_hce_repo(td_path)
            state = td_path / "state.json"
            _write_state(state, _minimal_state(state, repo, base_sha, original_sha))
            before = state.read_bytes()
            proc = _run_fs(
                "prepare-convergence", PARENT_ID,
                "--profile", PROFILE,
                "--authorized-by", "operator",
                "--reason", "approved workflow",
                "--approval-evidence", "ticket-1",
                "--actor", "orchestrator",
                "--event-id", "evt-prepare-1",
                "--expect-revision", "0",
                cwd=repo, state_file=state, check=False,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            payload = _parse_json(proc.stdout)
            self.assertTrue(payload["ok"])
            self.assertEqual(payload["result"], "HCE_PREPARED")
            self.assertEqual(payload["package_id"], PARENT_ID)
            self.assertIn("exception_id", payload)
            data = json.loads(state.read_text())
            exc = data["packages"][0]["convergence_exception"]
            self.assertEqual(exc["status"], "prepared")
            self.assertEqual(exc["profile"], PROFILE)
            self.assertEqual(exc["repair_ceiling_initialization"]["budget_lines"], 168)
            self.assertEqual(exc["repair_ceiling_initialization"]["original_changed_lines"], 336)

    def test_prepare_denies_wrong_profile_exit2_no_write(self):
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            repo, base_sha, original_sha, _, _ = _make_hce_repo(td_path)
            state = td_path / "state.json"
            _write_state(state, _minimal_state(state, repo, base_sha, original_sha))
            before_rev = json.loads(state.read_text())["revision"]
            proc = _run_fs(
                "prepare-convergence", PARENT_ID,
                "--profile", "WRONG/v1",
                "--authorized-by", "operator",
                "--reason", "r",
                "--approval-evidence", "e",
                "--actor", "orchestrator",
                "--event-id", "evt-prepare-bad",
                "--expect-revision", "0",
                cwd=repo, state_file=state, check=False,
            )
            self.assertEqual(proc.returncode, 2)
            payload = _parse_json(proc.stdout)
            self.assertFalse(payload["ok"])
            self.assertIn("HCE_DENIED", payload["error"])
            self.assertEqual(json.loads(state.read_text())["revision"], before_rev)


class HceCanonicalPathTests(unittest.TestCase):
    def test_symlink_state_path_denies_before_mutation(self):
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            repo, base_sha, original_sha, _, _ = _make_hce_repo(td_path)
            real_state = td_path / "real-state.json"
            _write_state(real_state, _minimal_state(real_state, repo, base_sha, original_sha))
            link = td_path / "link-state.json"
            link.symlink_to(real_state)
            proc = _run_fs(
                "prepare-convergence", PARENT_ID,
                "--profile", PROFILE,
                "--authorized-by", "operator",
                "--reason", "r",
                "--approval-evidence", "e",
                "--actor", "orchestrator",
                "--event-id", "evt-symlink",
                "--expect-revision", "0",
                cwd=repo, state_file=link, check=False,
            )
            self.assertEqual(proc.returncode, 2)
            payload = _parse_json(proc.stdout)
            self.assertFalse(payload["ok"])
            self.assertIn("HCE_STATE_PATH_MISMATCH", payload["error"])
            self.assertEqual(json.loads(real_state.read_text())["revision"], 0)


class HceInspectVerifyReadOnlyTests(unittest.TestCase):
    def _authorized_fixture(self, td_path: Path) -> tuple[Path, Path, str]:
        repo, state, exc_id, _ = _reentered_fixture(td_path)
        data = json.loads(state.read_text())
        parent = data["packages"][0]
        panel_id = "SVR-P1A1-FINAL-PANEL"
        parent["review_panels"].append({
            "panel_id": panel_id,
            "status": "completed",
            "verdict": "repair_required",
            "started_at": "2026-09-15T15:00:00+00:00",
            "completed_at": "2026-09-15T15:30:00+00:00",
            "roles": ["package-reviewer", "security-auditor"],
            "subreviews": [],
        })
        parent["convergence_exception"]["final_panel_id"] = panel_id
        parent["status"] = "repair_required"
        data["phase"] = "PACKAGE_REPAIR"
        _write_state(state, data)
        rev = data["revision"]
        proc = _run_fs(
            "authorize-convergence", PARENT_ID,
            "--exception-id", exc_id,
            "--authorized-by", "operator",
            "--reason", "final panel bound",
            "--approval-evidence", "panel-evidence",
            "--actor", "orchestrator",
            "--event-id", "evt-authorize-fixture",
            "--expect-revision", str(rev),
            cwd=repo, state_file=state, check=False,
        )
        assert proc.returncode == 0, proc.stderr + proc.stdout
        return repo, state, exc_id

    def test_inspect_returns_eligible_without_revision_change(self):
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            repo, state, exc_id = self._authorized_fixture(td_path)
            rev_before = json.loads(state.read_text())["revision"]
            proc = _run_fs(
                "inspect-convergence", PARENT_ID,
                "--exception-id", exc_id,
                cwd=repo, state_file=state, check=False,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            payload = _parse_json(proc.stdout)
            self.assertEqual(payload["result"], "HCE_ELIGIBLE")
            self.assertEqual(json.loads(state.read_text())["revision"], rev_before)

    def test_verify_denies_before_consumption(self):
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            repo, state, exc_id = self._authorized_fixture(td_path)
            rev_before = json.loads(state.read_text())["revision"]
            proc = _run_fs(
                "verify-convergence-outcome", PARENT_ID,
                "--exception-id", exc_id,
                cwd=repo, state_file=state, check=False,
            )
            self.assertEqual(proc.returncode, 2)
            payload = _parse_json(proc.stdout)
            self.assertFalse(payload["ok"])
            self.assertEqual(json.loads(state.read_text())["revision"], rev_before)


class HceConsumeReplayTests(unittest.TestCase):
    def test_consume_emits_pass_and_replay_denies(self):
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            repo, state, exc_id = HceInspectVerifyReadOnlyTests()._authorized_fixture(td_path)
            rev = json.loads(state.read_text())["revision"]
            proc = _run_fs(
                "consume-convergence", PARENT_ID,
                "--exception-id", exc_id,
                "--actor", "orchestrator",
                "--event-id", "evt-consume-1",
                "--expect-revision", str(rev),
                cwd=repo, state_file=state, check=False,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
            payload = _parse_json(proc.stdout)
            self.assertEqual(payload["result"], "HCE_PASS")
            self.assertIn("outcome_id", payload)
            outcome_id = payload["outcome_id"]
            data = json.loads(state.read_text())
            self.assertEqual(data["packages"][0]["convergence_exception"]["status"], "consumed")
            self.assertIsNotNone(data["packages"][0]["convergence_exception"]["consumption"])
            replay = _run_fs(
                "consume-convergence", PARENT_ID,
                "--exception-id", exc_id,
                "--actor", "orchestrator",
                "--event-id", "evt-consume-1",
                "--expect-revision", str(data["revision"]),
                cwd=repo, state_file=state, check=False,
            )
            self.assertEqual(replay.returncode, 2)
            replay_payload = _parse_json(replay.stdout)
            self.assertIn("HCE_REPLAY", replay_payload["error"])
            verify = _run_fs(
                "verify-convergence-outcome", PARENT_ID,
                "--exception-id", exc_id,
                cwd=repo, state_file=state, check=False,
            )
            self.assertEqual(verify.returncode, 0)
            verify_payload = _parse_json(verify.stdout)
            self.assertEqual(verify_payload["result"], "HCE_REGISTERED_VALID")
            self.assertEqual(verify_payload["outcome_id"], outcome_id)


class HceOwnershipModeTests(unittest.TestCase):
    def test_convergence_ownership_four_path_union_passes(self):
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            repo, state, exc_id = HceInspectVerifyReadOnlyTests()._authorized_fixture(td_path)
            proc = _run_owned(
                "--state-file", str(state.resolve()),
                "--package-id", PARENT_ID,
                "--convergence-exception-id", exc_id,
                check=False,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
            self.assertIn("OWNERSHIP_PASS", proc.stdout)

    def test_convergence_ownership_rejects_baseline_override(self):
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            repo, state, exc_id = HceInspectVerifyReadOnlyTests()._authorized_fixture(td_path)
            proc = _run_owned(
                "--state-file", str(state.resolve()),
                "--package-id", PARENT_ID,
                "--convergence-exception-id", exc_id,
                "--baseline", "HEAD~99",
                check=False,
            )
            self.assertEqual(proc.returncode, 2)
            payload = _parse_json(proc.stdout)
            self.assertFalse(payload["ok"])


class HceTriangulationTests(unittest.TestCase):
    def test_inspect_denies_stale_combined_commit(self):
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            repo, state, exc_id = HceInspectVerifyReadOnlyTests()._authorized_fixture(td_path)
            data = json.loads(state.read_text())
            data["packages"][0]["convergence_exception"]["combined_review_identity"]["candidate_commit"] = "0" * 40
            _write_state(state, data)
            proc = _run_fs(
                "inspect-convergence", PARENT_ID,
                "--exception-id", exc_id,
                cwd=repo, state_file=state, check=False,
            )
            self.assertEqual(proc.returncode, 2)
            self.assertIn("HCE_STALE", _parse_json(proc.stdout)["error"])

    def test_prepare_replay_same_event_is_noop(self):
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            repo, base_sha, original_sha, _, _ = _make_hce_repo(td_path)
            state = td_path / "state.json"
            _write_state(state, _minimal_state(state, repo, base_sha, original_sha))
            common = [
                "prepare-convergence", PARENT_ID,
                "--profile", PROFILE,
                "--authorized-by", "operator",
                "--reason", "approved workflow",
                "--approval-evidence", "ticket-1",
                "--actor", "orchestrator",
                "--event-id", "evt-prepare-replay",
                "--expect-revision", "0",
            ]
            first = _run_fs(*common, cwd=repo, state_file=state, check=False)
            self.assertEqual(first.returncode, 0)
            rev1 = json.loads(state.read_text())["revision"]
            replay_args = common[:-1] + [str(rev1)]
            second = _run_fs(*replay_args, cwd=repo, state_file=state, check=False)
            self.assertEqual(second.returncode, 0, second.stderr + second.stdout)
            payload = _parse_json(second.stdout)
            self.assertEqual(json.loads(state.read_text())["revision"], rev1)


class HceReenterTests(unittest.TestCase):
    def test_reenter_fills_snapshots_and_enters_review(self):
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            repo, state, exc_id, original_bytes = _prepare_fixture(td_path)
            rev = json.loads(state.read_text())["revision"]
            proc = _run_fs(
                "reenter-convergence", PARENT_ID,
                "--exception-id", exc_id,
                "--actor", "orchestrator",
                "--event-id", "evt-reenter-happy",
                "--expect-revision", str(rev),
                cwd=repo, state_file=state, check=False,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
            payload = _parse_json(proc.stdout)
            self.assertEqual(payload["result"], "HCE_REENTERED")
            data = json.loads(state.read_text())
            parent = data["packages"][0]
            exc = parent["convergence_exception"]
            self.assertEqual(exc["status"], "prepared")
            self.assertEqual(len(exc["children"]), 2)
            self.assertIsNotNone(exc["combined_review_identity"])
            self.assertIsNotNone(exc["binding_digest"])
            self.assertEqual(exc["worktree_realpath"], str(repo.resolve()))
            self.assertIsNotNone(exc["reentry"])
            self.assertEqual(data["phase"], "PACKAGE_REVIEW")
            self.assertEqual(parent["diff_ref"], exc["combined_review_identity"]["candidate_commit"])
            self.assertTrue(parent["integrated"])
            after_bytes = json.dumps(parent["candidate_identity"], sort_keys=True).encode()
            self.assertEqual(after_bytes, original_bytes)

    def test_reenter_denies_missing_child_receipt(self):
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            repo, state, exc_id, _ = _prepare_fixture(td_path)
            data = json.loads(state.read_text())
            data["packages"][1]["receipt"] = None
            _write_state(state, data)
            rev = data["revision"]
            proc = _run_fs(
                "reenter-convergence", PARENT_ID,
                "--exception-id", exc_id,
                "--actor", "orchestrator",
                "--event-id", "evt-reenter-no-receipt",
                "--expect-revision", str(rev),
                cwd=repo, state_file=state, check=False,
            )
            self.assertEqual(proc.returncode, 2)
            self.assertIn("HCE_STALE", _parse_json(proc.stdout)["error"])
            self.assertEqual(json.loads(state.read_text())["revision"], rev)

    def test_reenter_denies_stale_receipt_tree(self):
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            repo, state, exc_id, _ = _prepare_fixture(td_path)
            data = json.loads(state.read_text())
            stale_tree = "0" * 40
            child = data["packages"][1]
            child["candidate_identity"]["base_tree"] = stale_tree
            child["receipt"]["base_tree"] = stale_tree
            _write_state(state, data)
            rev = data["revision"]
            proc = _run_fs(
                "reenter-convergence", PARENT_ID,
                "--exception-id", exc_id,
                "--actor", "orchestrator",
                "--event-id", "evt-reenter-stale",
                "--expect-revision", str(rev),
                cwd=repo, state_file=state, check=False,
            )
            self.assertEqual(proc.returncode, 2)
            self.assertIn("HCE_STALE", _parse_json(proc.stdout)["error"])

    def test_reenter_denies_dirty_worktree(self):
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            repo, state, exc_id, _ = _prepare_fixture(td_path)
            (repo / "scripts/sync-vps/dirty.ts").write_text("x\n")
            rev = json.loads(state.read_text())["revision"]
            proc = _run_fs(
                "reenter-convergence", PARENT_ID,
                "--exception-id", exc_id,
                "--actor", "orchestrator",
                "--event-id", "evt-reenter-dirty",
                "--expect-revision", str(rev),
                cwd=repo, state_file=state, check=False,
            )
            self.assertEqual(proc.returncode, 2)
            self.assertIn("HCE_DIRTY_WORKTREE", _parse_json(proc.stdout)["error"])

    def test_reenter_denies_symlink_state_path(self):
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            repo, state, exc_id, _ = _prepare_fixture(td_path)
            link = td_path / "link-state.json"
            link.symlink_to(state)
            rev = json.loads(state.read_text())["revision"]
            proc = _run_fs(
                "reenter-convergence", PARENT_ID,
                "--exception-id", exc_id,
                "--actor", "orchestrator",
                "--event-id", "evt-reenter-symlink",
                "--expect-revision", str(rev),
                cwd=repo, state_file=link, check=False,
            )
            self.assertEqual(proc.returncode, 2)
            self.assertIn("HCE_STATE_PATH_MISMATCH", _parse_json(proc.stdout)["error"])


class HceAuthorizeTests(unittest.TestCase):
    def _authorize_ready_fixture(self, td_path: Path) -> tuple[Path, Path, str]:
        repo, state, exc_id, _ = _reentered_fixture(td_path)
        data = json.loads(state.read_text())
        parent = data["packages"][0]
        panel_id = "SVR-P1A1-FINAL-PANEL"
        parent["review_panels"].append({
            "panel_id": panel_id,
            "status": "completed",
            "verdict": "repair_required",
            "started_at": "2026-09-15T15:00:00+00:00",
            "completed_at": "2026-09-15T15:30:00+00:00",
            "roles": ["package-reviewer", "security-auditor"],
            "subreviews": [],
        })
        parent["convergence_exception"]["final_panel_id"] = panel_id
        parent["status"] = "repair_required"
        data["phase"] = "PACKAGE_REPAIR"
        _write_state(state, data)
        return repo, state, exc_id

    def test_authorize_moves_prepared_to_authorized(self):
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            repo, state, exc_id = self._authorize_ready_fixture(td_path)
            rev = json.loads(state.read_text())["revision"]
            proc = _run_fs(
                "authorize-convergence", PARENT_ID,
                "--exception-id", exc_id,
                "--authorized-by", "operator",
                "--reason", "final panel bound",
                "--approval-evidence", "panel-evidence",
                "--actor", "orchestrator",
                "--event-id", "evt-authorize-1",
                "--expect-revision", str(rev),
                cwd=repo, state_file=state, check=False,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
            payload = _parse_json(proc.stdout)
            self.assertEqual(payload["result"], "HCE_AUTHORIZED")
            exc = json.loads(state.read_text())["packages"][0]["convergence_exception"]
            self.assertEqual(exc["status"], "authorized")
            self.assertIsNotNone(exc["authorization"])
            self.assertEqual(exc["authorization"]["panel_id"], "SVR-P1A1-FINAL-PANEL")

    def test_authorize_denies_without_final_panel(self):
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            repo, state, exc_id, _ = _reentered_fixture(td_path)
            data = json.loads(state.read_text())
            data["phase"] = "PACKAGE_REPAIR"
            _write_state(state, data)
            rev = data["revision"]
            proc = _run_fs(
                "authorize-convergence", PARENT_ID,
                "--exception-id", exc_id,
                "--authorized-by", "operator",
                "--reason", "r",
                "--approval-evidence", "e",
                "--actor", "orchestrator",
                "--event-id", "evt-authorize-nopanel",
                "--expect-revision", str(rev),
                cwd=repo, state_file=state, check=False,
            )
            self.assertEqual(proc.returncode, 2)
            self.assertIn("HCE_DENIED", _parse_json(proc.stdout)["error"])

    def test_authorize_denies_wrong_phase(self):
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            repo, state, exc_id, _ = _reentered_fixture(td_path)
            rev = json.loads(state.read_text())["revision"]
            proc = _run_fs(
                "authorize-convergence", PARENT_ID,
                "--exception-id", exc_id,
                "--authorized-by", "operator",
                "--reason", "r",
                "--approval-evidence", "e",
                "--actor", "orchestrator",
                "--event-id", "evt-authorize-phase",
                "--expect-revision", str(rev),
                cwd=repo, state_file=state, check=False,
            )
            self.assertEqual(proc.returncode, 2)
            self.assertIn("HCE_DENIED", _parse_json(proc.stdout)["error"])

    def test_authorize_replay_same_event_is_noop(self):
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            repo, state, exc_id = self._authorize_ready_fixture(td_path)
            rev = json.loads(state.read_text())["revision"]
            common = [
                "authorize-convergence", PARENT_ID,
                "--exception-id", exc_id,
                "--authorized-by", "operator",
                "--reason", "final panel bound",
                "--approval-evidence", "panel-evidence",
                "--actor", "orchestrator",
                "--event-id", "evt-authorize-replay",
                "--expect-revision", str(rev),
            ]
            first = _run_fs(*common, cwd=repo, state_file=state, check=False)
            self.assertEqual(first.returncode, 0)
            rev1 = json.loads(state.read_text())["revision"]
            second = _run_fs(*common[:-1], str(rev1), cwd=repo, state_file=state, check=False)
            self.assertEqual(second.returncode, 0)
            self.assertEqual(json.loads(state.read_text())["revision"], rev1)


class HceDirtyWorktreeTests(unittest.TestCase):
    def test_dirty_worktree_denies_consume(self):
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            repo, state, exc_id = HceInspectVerifyReadOnlyTests()._authorized_fixture(td_path)
            rev_before = json.loads(state.read_text())["revision"]
            (repo / "scripts/sync-vps/dirty.ts").write_text("dirty\n")
            proc = _run_fs(
                "consume-convergence", PARENT_ID,
                "--exception-id", exc_id,
                "--actor", "orchestrator",
                "--event-id", "evt-dirty",
                "--expect-revision", str(rev_before),
                cwd=repo, state_file=state, check=False,
            )
            self.assertEqual(proc.returncode, 2)
            payload = _parse_json(proc.stdout)
            self.assertIn("HCE_DIRTY_WORKTREE", payload["error"])
            self.assertEqual(json.loads(state.read_text())["revision"], rev_before)


class HceNegativeSecurityTests(unittest.TestCase):
    def test_parent_symlink_alias_denies_prepare_zero_write(self):
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            repo, base_sha, original_sha, _, _ = _make_hce_repo(td_path)
            real_dir = td_path / "real"
            real_dir.mkdir()
            real_state = real_dir / "state.json"
            _write_state(real_state, _minimal_state(real_state, repo, base_sha, original_sha))
            alias_dir = td_path / "alias"
            alias_dir.symlink_to(real_dir)
            alias_state = alias_dir / "state.json"
            rev_before = json.loads(real_state.read_text())["revision"]
            proc = _run_fs(
                "prepare-convergence", PARENT_ID,
                "--profile", PROFILE,
                "--authorized-by", "operator",
                "--reason", "r",
                "--approval-evidence", "e",
                "--actor", "orchestrator",
                "--event-id", "evt-parent-symlink",
                "--expect-revision", "0",
                cwd=repo, state_file=alias_state, check=False,
            )
            self.assertEqual(proc.returncode, 2)
            payload = _parse_json(proc.stdout)
            self.assertFalse(payload["ok"])
            self.assertEqual(payload["code"], "HCE_STATE_PATH_MISMATCH")
            self.assertEqual(json.loads(real_state.read_text())["revision"], rev_before)

    def test_hardlinked_state_path_denies_prepare(self):
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            repo, base_sha, original_sha, _, _ = _make_hce_repo(td_path)
            primary = td_path / "state-primary.json"
            _write_state(primary, _minimal_state(primary, repo, base_sha, original_sha))
            hardlink = td_path / "state-hardlink.json"
            os.link(primary, hardlink)
            rev_before = json.loads(primary.read_text())["revision"]
            proc = _run_fs(
                "prepare-convergence", PARENT_ID,
                "--profile", PROFILE,
                "--authorized-by", "operator",
                "--reason", "r",
                "--approval-evidence", "e",
                "--actor", "orchestrator",
                "--event-id", "evt-hardlink",
                "--expect-revision", "0",
                cwd=repo, state_file=hardlink, check=False,
            )
            self.assertEqual(proc.returncode, 2)
            payload = _parse_json(proc.stdout)
            self.assertEqual(payload["code"], "HCE_STATE_PATH_MISMATCH")
            self.assertEqual(json.loads(primary.read_text())["revision"], rev_before)

    def test_symlink_git_entry_denies_reenter(self):
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            repo = td_path / "worktree"
            sync = repo / "scripts/sync-vps"
            tests_dir = sync / "__tests__"
            tests_dir.mkdir(parents=True)
            _git("init", "-q", cwd=repo)
            _git("config", "user.email", "hce@test.local", cwd=repo)
            _git("config", "user.name", "HCE Test", cwd=repo)
            (repo / "README.md").write_text("base\n")
            _git("add", "-A", cwd=repo)
            _git("commit", "-q", "-m", "base", cwd=repo)
            base_sha = _git("rev-parse", "HEAD", cwd=repo).stdout.strip()
            (sync / "source-discovery.ts").write_text("// discovery v1\n" * 252)
            (tests_dir / "source-discovery.test.ts").write_text("// discovery test v1\n" * 84)
            _git("add", "-A", cwd=repo)
            _git("commit", "-q", "-m", "original-parent", cwd=repo)
            original_sha = _git("rev-parse", "HEAD", cwd=repo).stdout.strip()
            (sync / "owned-target.ts").write_text("// target\n")
            (sync / "typescript-dispatch-resolver.ts").symlink_to("owned-target.ts")
            (tests_dir / "typescript-dispatch-resolver.test.ts").write_text("// resolver test\n" * 8)
            _git("add", "-A", cwd=repo)
            _git("commit", "-q", "-m", "child-a-symlink", cwd=repo)
            child_a_sha = _git("rev-parse", "HEAD", cwd=repo).stdout.strip()
            (sync / "source-discovery.ts").write_text("// discovery v2 combined\n" * 25)
            (tests_dir / "source-discovery.test.ts").write_text("// discovery test v2\n" * 12)
            _git("add", "-A", cwd=repo)
            _git("commit", "-q", "-m", "child-b-final", cwd=repo)
            combined_sha = _git("rev-parse", "HEAD", cwd=repo).stdout.strip()
            state = td_path / "state.json"
            data = _minimal_state(state, repo, base_sha, original_sha)
            _attach_accepted_children(data, repo, original_sha, child_a_sha, combined_sha)
            _write_state(state, data)
            prep = _run_fs(
                "prepare-convergence", PARENT_ID,
                "--profile", PROFILE,
                "--authorized-by", "operator",
                "--reason", "r",
                "--approval-evidence", "e",
                "--actor", "orchestrator",
                "--event-id", "evt-prepare-symlink",
                "--expect-revision", "0",
                cwd=repo, state_file=state, check=False,
            )
            self.assertEqual(prep.returncode, 0, prep.stdout + prep.stderr)
            exc_id = _parse_json(prep.stdout)["exception_id"]
            rev = json.loads(state.read_text())["revision"]
            proc = _run_fs(
                "reenter-convergence", PARENT_ID,
                "--exception-id", exc_id,
                "--actor", "orchestrator",
                "--event-id", "evt-symlink-entry",
                "--expect-revision", str(rev),
                cwd=repo, state_file=state, check=False,
            )
            self.assertEqual(proc.returncode, 2)
            payload = _parse_json(proc.stdout)
            self.assertEqual(payload["code"], "HCE_UNSUPPORTED_GIT_ENTRY")
            self.assertEqual(json.loads(state.read_text())["revision"], rev)

    def test_prepare_denies_extra_planned_task(self):
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            repo, base_sha, original_sha, _, _ = _make_hce_repo(td_path)
            state = td_path / "state.json"
            data = _minimal_state(state, repo, base_sha, original_sha)
            data["packages"][0]["tasks"].append(
                {"id": "extra-task", "status": "planned", "blockers": [], "local_validations": []}
            )
            _write_state(state, data)
            proc = _run_fs(
                "prepare-convergence", PARENT_ID,
                "--profile", PROFILE,
                "--authorized-by", "operator",
                "--reason", "r",
                "--approval-evidence", "e",
                "--actor", "orchestrator",
                "--event-id", "evt-extra-task",
                "--expect-revision", "0",
                cwd=repo, state_file=state, check=False,
            )
            self.assertEqual(proc.returncode, 2)
            payload = _parse_json(proc.stdout)
            self.assertEqual(payload["code"], "HCE_DENIED")
            self.assertEqual(json.loads(state.read_text())["revision"], 0)

    def test_prepare_denies_invented_finding_digest(self):
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            repo, base_sha, original_sha, _, _ = _make_hce_repo(td_path)
            state = td_path / "state.json"
            data = _minimal_state(state, repo, base_sha, original_sha)
            data["packages"][0]["findings"][0]["verification_digest"] = "sha256:" + "a" * 64
            _write_state(state, data)
            proc = _run_fs(
                "prepare-convergence", PARENT_ID,
                "--profile", PROFILE,
                "--authorized-by", "operator",
                "--reason", "r",
                "--approval-evidence", "e",
                "--actor", "orchestrator",
                "--event-id", "evt-bad-digest",
                "--expect-revision", "0",
                cwd=repo, state_file=state, check=False,
            )
            self.assertEqual(proc.returncode, 2)
            payload = _parse_json(proc.stdout)
            self.assertEqual(payload["code"], "HCE_DENIED")
            self.assertEqual(json.loads(state.read_text())["revision"], 0)

    def test_consume_denies_finding_snapshot_tamper(self):
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            repo, state, exc_id = HceInspectVerifyReadOnlyTests()._authorized_fixture(td_path)
            data = json.loads(state.read_text())
            data["packages"][0]["findings"][0]["status"] = "closed"
            _write_state(state, data)
            rev = data["revision"]
            proc = _run_fs(
                "consume-convergence", PARENT_ID,
                "--exception-id", exc_id,
                "--actor", "orchestrator",
                "--event-id", "evt-tamper-finding",
                "--expect-revision", str(rev),
                cwd=repo, state_file=state, check=False,
            )
            self.assertEqual(proc.returncode, 2)
            payload = _parse_json(proc.stdout)
            self.assertEqual(payload.get("code"), "HCE_STALE")
            self.assertEqual(json.loads(state.read_text())["revision"], rev)

    def test_verify_denies_missing_ceiling_gate_linkage(self):
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            repo, state, exc_id = HceInspectVerifyReadOnlyTests()._authorized_fixture(td_path)
            rev = json.loads(state.read_text())["revision"]
            consume = _run_fs(
                "consume-convergence", PARENT_ID,
                "--exception-id", exc_id,
                "--actor", "orchestrator",
                "--event-id", "evt-consume-verify",
                "--expect-revision", str(rev),
                cwd=repo, state_file=state, check=False,
            )
            self.assertEqual(consume.returncode, 0, consume.stdout + consume.stderr)
            data = json.loads(state.read_text())
            data["packages"][0]["gates"] = []
            _write_state(state, data)
            verify = _run_fs(
                "verify-convergence-outcome", PARENT_ID,
                "--exception-id", exc_id,
                cwd=repo, state_file=state, check=False,
            )
            self.assertEqual(verify.returncode, 2)
            payload = _parse_json(verify.stdout)
            self.assertEqual(payload["code"], "HCE_OUTCOME_INVALID")

    def test_ownership_mode_ignores_tampered_snapshot_for_owned_paths(self):
        from feature_state_lib.convergence_constants import FOUR_PATH_UNION  # noqa: E402

        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            repo, state, exc_id = HceInspectVerifyReadOnlyTests()._authorized_fixture(td_path)
            data = json.loads(state.read_text())
            data["packages"][0]["convergence_exception"]["ownership_snapshot"].append(
                {"child_package_id": "EVIL", "owned_paths": ["scripts/sync-vps/evil.ts"]}
            )
            _write_state(state, data)
            proc = _run_owned(
                "--state-file", str(state.resolve()),
                "--package-id", PARENT_ID,
                "--convergence-exception-id", exc_id,
                check=False,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
            payload = _parse_json(proc.stdout.split("OWNERSHIP_PASS")[0].strip())
            self.assertEqual(sorted(payload["owned_paths"]), sorted(FOUR_PATH_UNION))
            self.assertNotIn("scripts/sync-vps/evil.ts", payload["owned_paths"])

    def test_missing_actor_returns_json_denial_not_usage(self):
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            repo, base_sha, original_sha, _, _ = _make_hce_repo(td_path)
            state = td_path / "state.json"
            _write_state(state, _minimal_state(state, repo, base_sha, original_sha))
            cmd = [
                "python3", str(FEATURE_STATE),
                "prepare-convergence", PARENT_ID,
                "--profile", PROFILE,
                "--authorized-by", "operator",
                "--reason", "r",
                "--approval-evidence", "e",
                "--event-id", "evt-no-actor",
                "--expect-revision", "0",
                "--state-file", str(state.resolve()),
            ]
            proc = subprocess.run(cmd, cwd=repo, env=os.environ.copy(), text=True, capture_output=True, check=False)
            self.assertEqual(proc.returncode, 2)
            self.assertNotIn("usage:", proc.stderr.lower())
            payload = _parse_json(proc.stdout)
            self.assertEqual(payload["code"], "HCE_DENIED")
            self.assertEqual(json.loads(state.read_text())["revision"], 0)

    def test_committed_render_failure_reports_recovery_metadata(self):
        import argparse
        import importlib.util
        from unittest.mock import patch

        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            repo, state, exc_id = HceInspectVerifyReadOnlyTests()._authorized_fixture(td_path)
            rev = json.loads(state.read_text())["revision"]
            spec = importlib.util.spec_from_file_location("feature_state_main", FEATURE_STATE)
            fs_mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(fs_mod)
            args = argparse.Namespace(
                state_file=str(state.resolve()),
                expect_revision=rev,
                actor="orchestrator",
                event_id="evt-render-fail",
                package_id=PARENT_ID,
                exception_id=exc_id,
                no_render=False,
            )

            def _mark_consumed(data: dict) -> bool:
                package = fs_mod.package_by_id(data, PARENT_ID)
                exc = package["convergence_exception"]
                exc["status"] = "consumed"
                exc["consumption"] = {
                    "outcome_id": str(uuid.uuid4()),
                    "at": "2026-09-15T16:00:00+00:00",
                    "actor": "orchestrator",
                    "event_id": "evt-render-fail",
                    "binding_digest": exc.get("binding_digest"),
                    "combined_review_identity": exc.get("combined_review_identity"),
                    "panel_id": exc.get("final_panel_id"),
                    "committed_revision": int(data.get("revision", 0)) + 1,
                }
                return True

            with patch.object(fs_mod, "render_status", side_effect=RuntimeError("render boom")):
                with patch.object(fs_mod, "render_bitacora"):
                    with patch.object(fs_mod, "render_notes"):
                        with patch.object(fs_mod, "render_modules"):
                            with self.assertRaises(fs_mod.HceCommittedRenderFailed) as ctx:
                                fs_mod.mutate(state, args, "consume-convergence", _mark_consumed)
            err = ctx.exception
            self.assertEqual(err.token, "HCE_COMMITTED_RENDER_FAILED")
            self.assertTrue(err.fields.get("state_committed"))
            self.assertIn("outcome_id", err.fields)
            data = json.loads(state.read_text())
            self.assertEqual(data["packages"][0]["convergence_exception"]["status"], "consumed")
            replay = _run_fs(
                "consume-convergence", PARENT_ID,
                "--exception-id", exc_id,
                "--actor", "orchestrator",
                "--event-id", "evt-render-fail-replay",
                "--expect-revision", str(data["revision"]),
                cwd=repo, state_file=state, check=False,
            )
            self.assertEqual(replay.returncode, 2)
            replay_payload = _parse_json(replay.stdout)
            self.assertEqual(replay_payload["code"], "HCE_REPLAY")


class HceSchemaValidationTests(unittest.TestCase):
    def test_validate_state_rejects_unknown_convergence_key(self):
        from feature_state_lib.model import validate_state

        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            repo, base_sha, original_sha, _, _ = _make_hce_repo(td_path)
            state = td_path / "state.json"
            data = _minimal_state(state, repo, base_sha, original_sha)
            data["packages"][0]["convergence_exception"] = {"schema": SCHEMA, "evil": True}
            errors = validate_state(data)
            self.assertTrue(any("unknown keys" in err for err in errors))


if __name__ == "__main__":
    unittest.main()
