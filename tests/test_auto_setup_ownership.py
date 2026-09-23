#!/usr/bin/env python3
"""ADR-0077: auto-setup ownership — migrate, deferred, bus, packs overlay."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "ai" / "scripts"
sys.path.insert(0, str(SCRIPTS))


class MigrateLegacyTests(unittest.TestCase):
    def _run(self, *args, cwd=None):
        return subprocess.run(
            [sys.executable, str(SCRIPTS / "feature-state.py"), *args],
            cwd=cwd or ROOT,
            capture_output=True,
            text=True,
        )

    def test_migrate_dict_packages_and_missing_schema(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "012.json"
            path.write_text(json.dumps({
                "feature_id": "012-legacy",
                "phase": "PACKAGE_PLANNING",
                "revision": 3,
                "approved_spec": {"path": "docs/specs/x/spec.md", "hash": "abc"},
                "packages": {
                    "P1": {
                        "package_id": "P1",
                        "objective": "x",
                        "tasks": [],
                        "owned_paths": [],
                        "read_only_paths": [],
                        "status": "planned",
                        "attempts": {},
                        "acceptance_criteria": [],
                    }
                },
                "history": [{"event": "legacy"}],
                "budgets": {
                    "max_deep_review_cycles": 2,
                    "max_repairs_per_finding": 2,
                    "max_package_subdivisions": 1,
                },
            }), encoding="utf-8")
            result = self._run("migrate-legacy-state", "--state-file", str(path))
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            payload = json.loads(result.stdout)
            self.assertTrue(payload["changed"])
            self.assertTrue(Path(payload["backup"]).is_file())
            data = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(data["schema_version"], 1)
            self.assertIsInstance(data["packages"], list)
            self.assertEqual(data["packages"][0]["package_id"], "P1")

    def test_resume_auto_migrates_without_user_command(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "legacy.json"
            path.write_text(json.dumps({
                "feature_id": "legacy-auto",
                "phase": "PACKAGE_PLANNING",
                "revision": 0,
                "approved_spec": {"path": "docs/specs/x/spec.md", "hash": "abc"},
                "packages": [],
                "history": [],
                "blockers": [],
                "global_gates": [],
                "acceptance_criteria": [],
                "metrics": {},
                "budgets": {
                    "max_deep_review_cycles": 2,
                    "max_repairs_per_finding": 2,
                    "max_package_subdivisions": 1,
                    "max_spawns_per_package": 12,
                    "max_gate_failures_per_package": 3,
                    "max_verifications_per_package": 3,
                },
            }), encoding="utf-8")
            result = self._run("resume", "--state-file", str(path))
            self.assertIn("MIGRATED_LEGACY", result.stderr)
            data = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(data["schema_version"], 1)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


class DeferredAndBusTests(unittest.TestCase):
    def test_log_deferred_not_read_by_describe_next_step(self):
        import feature_state_lib.render_status as rs
        import feature_state_lib.cli_reporting as reporting
        from feature_state_lib.model import base_state

        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / reporting.DEFERRED_LOG).write_text(
                json.dumps({
                    "at": "2026-01-01T00:00:00Z",
                    "summary": "also improve X",
                    "why_deferred": "out of scope",
                    "actor": "orchestrator",
                }) + "\n",
                encoding="utf-8",
            )
            data = base_state("f1", "docs/specs/x/spec.md", "hash")
            data["phase"] = "DONE"
            data["final_state"] = "DONE"
            # Deferred improvements must not become the live next step.
            self.assertEqual(rs.describe_next_step(data), "—")
            self.assertIn("never reads", rs.describe_next_step.__doc__)
            self.assertEqual(reporting.DEFERRED_LOG, "deferred-log.jsonl")

    def test_bus_roundtrip(self):
        from feature_state_lib import cli_bus
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            posted = cli_bus.bus_post(
                topic="handoff",
                from_role="implementer",
                to_role="orchestrator",
                body="P1 done, gates green",
                state_dir=state_dir,
            )
            self.assertTrue(posted["ok"])
            listed = cli_bus.bus_list(topic="handoff", to_role="orchestrator", state_dir=state_dir)
            self.assertEqual(len(listed["entries"]), 1)
            self.assertEqual(listed["entries"][0]["body"], "P1 done, gates green")


class PacksOverlayTests(unittest.TestCase):
    def test_always_on_plus_project_enabled(self):
        import packs_config
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            (project / "packs.local.toml").write_text(
                'enabled = ["data", "ml"]\n', encoding="utf-8")
            profile = packs_config.resolve_profile(
                harness_root=ROOT,
                project_root=project,
                which=lambda _: True,
            )
            ids = {p.pack_id for p in profile.active}
            self.assertIn("software-engineering", ids)
            self.assertIn("security", ids)
            self.assertIn("data", ids)
            self.assertIn("ml", ids)
            lines = "\n".join(packs_config.profile_lines(profile))
            self.assertIn("Global (harness)", lines)
            self.assertIn("Proyecto", lines)
            self.assertIn("Máquina", lines)

    def test_ownership_adr_rejects_new_auto_setup_agent(self):
        adr = (ROOT / "docs/adr/0077-auto-setup-orquestador-y-bootstrapper.md").read_text(
            encoding="utf-8")
        self.assertIn("project-bootstrapper", adr)
        self.assertIn("orquestador", adr.lower())
        self.assertIn("**No** se crea un agente", adr)
        boot = (ROOT / "Global/_canonical/agents/project-bootstrapper.md").read_text(
            encoding="utf-8")
        self.assertIn("packs.local.toml", boot)
        self.assertIn("ADR-0077", boot)
        orch = (ROOT / "Global/_canonical/agents/orchestrator.md").read_text(encoding="utf-8")
        self.assertIn("ADR-0077", orch)
        self.assertIn("project-bootstrapper", orch)
        self.assertIn("log-deferred", orch)


class ConsolePerfilTests(unittest.TestCase):
    def test_perfil_row_in_simple_home(self):
        import set_agents_app as app
        keys = [a.key for a in app.visible_actions(experto=False)]
        self.assertIn("perfil", keys)
        self.assertLess(keys.index("perfil"), keys.index("configurar"))


if __name__ == "__main__":
    unittest.main()
