import json
import os
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ai/scripts"))
import setup_models  # noqa: E402


class RestoreAndRoutingTests(unittest.TestCase):
    def test_restore_removes_only_model_overrides_and_preserves_host_bytes(self):
        with tempfile.TemporaryDirectory() as td:
            overlay = Path(td) / "models.local.toml"
            original = "[areas.build]\nopencode = \"x\"\n[hosts.agy]\nmodel = \"keep\"\n"
            overlay.write_text(original, encoding="utf-8")
            with mock.patch.object(setup_models.models_config, "models_overlay_path", return_value=overlay):
                result = setup_models.restore_set_defaults()
            self.assertTrue(result["changed"])
            self.assertEqual(overlay.read_text(encoding="utf-8"), "[hosts.agy]\nmodel = \"keep\"\n")

    def test_restore_pending_when_install_fails(self):
        with tempfile.TemporaryDirectory() as td:
            overlay = Path(td) / "models.local.toml"
            overlay.write_text("[areas.build]\nopencode = \"x\"\n", encoding="utf-8")
            with mock.patch.object(setup_models.models_config, "models_overlay_path", return_value=overlay), \
                 mock.patch.object(setup_models.models_config, "load_roster", return_value=[]), \
                 mock.patch.object(setup_models, "_store_model_state_pending") as pending, \
                 mock.patch.object(setup_models, "_run_installer", return_value=1):
                result = setup_models.restore_set_defaults(
                    factory={"runtime": {"primary": "opencode"}, "areas": {}, "roles": {}},
                    roles_path=Path(td) / "roles.tsv", runtime="opencode")
            self.assertEqual(result["status"], "pending_apply")
            pending.assert_called_once()

    def test_restore_pending_when_install_raises_after_persist(self):
        with tempfile.TemporaryDirectory() as td:
            overlay = Path(td) / "models.local.toml"
            overlay.write_text("[areas.build]\nopencode = \"x\"\n", encoding="utf-8")
            with mock.patch.object(setup_models.models_config, "models_overlay_path", return_value=overlay), \
                 mock.patch.object(setup_models.models_config, "load_roster", return_value=[]), \
                 mock.patch.object(setup_models, "_store_model_state_pending") as pending, \
                 mock.patch.object(setup_models, "_run_installer", side_effect=RuntimeError("boom")):
                result = setup_models.restore_set_defaults(
                    factory={"runtime": {"primary": "opencode"}, "areas": {}, "roles": {}},
                    roles_path=Path(td) / "roles.tsv", runtime="opencode")
            self.assertEqual(result["status"], "pending_apply")
            self.assertIn("reintentar", result["message"].lower())
            pending.assert_called_once()

    def test_restore_applied_updates_desired_before_cache(self):
        row = {"role": "orchestrator", "class": "build"}
        factory = {"runtime": {"primary": "opencode"}, "areas": {}, "roles": {"orchestrator": {"opencode": "opaque/restored"}}}
        desired = {"model": "opaque/restored", "source": "set-effective-config", "status": "resolved"}
        installed = {"status": "installed", "model": "opaque/restored"}
        with tempfile.TemporaryDirectory() as td:
            overlay = Path(td) / "models.local.toml"
            overlay.write_text("[areas.build]\nopencode = \"x\"\n", encoding="utf-8")
            with mock.patch.object(setup_models.models_config, "models_overlay_path", return_value=overlay), \
                 mock.patch.object(setup_models.models_config, "load_roster", return_value=[row]), \
                 mock.patch.object(setup_models.models_config, "effective_models_config", return_value=factory), \
                 mock.patch.object(setup_models.models_config, "resolve_role", return_value={"opencode": "opaque/restored"}), \
                 mock.patch.object(setup_models.model_state, "_desired_from_resolved", return_value=desired), \
                 mock.patch.object(setup_models, "_run_installer", return_value=0), \
                 mock.patch.object(setup_models, "_load_disk_model_state", return_value={"schema_version": 1}), \
                 mock.patch.object(setup_models, "_sync_model_state_cache") as sync:
                result = setup_models.restore_set_defaults(
                    factory=factory, roles_path=Path(td) / "roles.tsv", runtime="opencode",
                    readback=lambda *_a, **_k: installed)
            self.assertEqual(result["status"], "applied")
            synced = sync.call_args.args[0]
            self.assertEqual(synced["desired"], desired)
            self.assertEqual(synced["convergence"], {"status": "applied"})

    def test_router_auto_only_removes_pins(self):
        app = mock.Mock()
        app._read_model_preference_raw.return_value = {"preference": {"build": ["x"]}, "model_pin": {"*": "x/y"}}
        app._serialize_model_preference.return_value = "serialized"
        app.MODEL_PREFERENCE_PATH = Path("/tmp/not-written")
        with mock.patch.dict(sys.modules, {"set_agents_app": app}):
            self.assertTrue(setup_models.router_choose_automatically())
        app.atomic_write.assert_called_once_with(app.MODEL_PREFERENCE_PATH, "serialized")
        self.assertNotIn("model_pin", app._serialize_model_preference.call_args.args[0])
        self.assertIn("preference", app._serialize_model_preference.call_args.args[0])


class ApplyTests(unittest.TestCase):
    def test_install_failure_keeps_intent_pending(self):
        with tempfile.TemporaryDirectory() as td, \
             mock.patch.object(setup_models, "_locked_preference_writer") as lock, \
             mock.patch.object(setup_models, "write_overlay_cell") as persist, \
             mock.patch.object(setup_models.models_config, "effective_models_config", return_value={"roles": {}}), \
             mock.patch.object(setup_models.models_config, "load_roster", return_value=[]), \
             mock.patch.object(setup_models.fcntl, "flock"):
            lock.return_value = mock.MagicMock()
            result = setup_models.apply_overlay_model(("roles", "other"), "opencode", "opaque/new",
                factory={}, roles_path=Path(td) / "roles.tsv", runtime="opencode", install=lambda: 1)
        persist.assert_called_once()
        self.assertEqual(result["status"], "pending_apply")

    def test_area_edit_never_claims_applied_from_orchestrator_readback(self):
        with tempfile.TemporaryDirectory() as td, \
             mock.patch.object(setup_models, "_locked_preference_writer") as lock, \
             mock.patch.object(setup_models, "write_overlay_cell"), \
             mock.patch.object(setup_models, "_store_model_state_pending") as pending, \
             mock.patch.object(setup_models.models_config, "effective_models_config", return_value={"roles": {}}), \
             mock.patch.object(setup_models.models_config, "load_roster", return_value=[]), \
             mock.patch.object(setup_models.fcntl, "flock"):
            lock.return_value = mock.MagicMock()
            result = setup_models.apply_overlay_model(("areas", "audit"), "opencode", "opaque/new",
                factory={}, roles_path=Path(td) / "roles.tsv", runtime="opencode",
                install=lambda: 0, readback=lambda *_a, **_k: {"status": "installed", "model": "same/old"})
        self.assertEqual(result["status"], "pending_apply")
        pending.assert_called_once()

    def test_second_writer_fails_before_persist(self):
        with mock.patch.object(setup_models, "_locked_preference_writer", side_effect=setup_models.ModelsError("ocupado")), \
             mock.patch.object(setup_models, "write_overlay_cell") as persist:
            with self.assertRaises(setup_models.ModelsError):
                setup_models.apply_overlay_model(("roles", "other"), "opencode", "opaque/new",
                    factory={}, roles_path=Path("roles.tsv"), runtime="opencode", install=lambda: 0)
        persist.assert_not_called()


class CacheAndRefreshTests(unittest.TestCase):
    def test_cache_round_trip_syncs_disk_and_ram(self):
        with tempfile.TemporaryDirectory() as td:
            cache = Path(td) / "model-state.json"
            with mock.patch.object(setup_models, "_model_state_cache_path", return_value=cache), \
                 mock.patch.object(setup_models.ui.GLOBAL_CACHE, "set") as cache_set:
                state = {"schema_version": 1, "convergence": {"status": "pending_apply"}}
                setup_models._sync_model_state_cache(state)
            self.assertEqual(json.loads(cache.read_text(encoding="utf-8"))["convergence"]["status"], "pending_apply")
            cache_set.assert_called_once_with("model_state", state)

    def test_mixed_refresh_preserves_stale_source(self):
        prior = {
            "observed": {"model": "opaque/a", "status": "observed", "source": "opencode"},
            "desired": {"model": "opaque/b", "status": "resolved", "source": "set-effective-config"},
            "installed": {"status": "unavailable"},
            "routing": {"status": "dynamic", "source": "model-preference.toml"},
            "refresh": {"observed": {"checked_at": "2026-01-01T00:00:00Z", "status": "fresh"}},
            "convergence": {"status": "applied"},
        }
        with mock.patch.object(setup_models, "_cached_model_state", return_value=prior), \
             mock.patch.object(setup_models.model_state, "collect_model_state", side_effect=OSError("no")), \
             mock.patch.object(setup_models, "_sync_model_state_cache") as sync:
            state, error = setup_models._refresh_model_state()
        self.assertIn("reintent", error.lower())
        merged = sync.call_args.args[0]
        self.assertEqual(merged["observed"]["model"], "opaque/a")
        self.assertEqual(merged["refresh"]["observed"]["status"], "stale")
        self.assertEqual(merged["refresh"]["observed"]["checked_at"], "2026-01-01T00:00:00Z")


class PinWriterLockTests(unittest.TestCase):
    def test_model_pin_set_fails_before_mutate_when_lock_held(self):
        import set_agents_app as app
        lock_path = Path(tempfile.mkdtemp()) / "models-apply.lock"
        lock_path.write_text("", encoding="utf-8")
        handle = lock_path.open("a+", encoding="utf-8")
        setup_models.fcntl.flock(handle.fileno(), setup_models.fcntl.LOCK_EX)
        try:
            with mock.patch.object(setup_models, "_preference_lock_path", return_value=lock_path), \
                 mock.patch.object(app, "atomic_write") as write:
                with self.assertRaises(setup_models.ModelsError):
                    app.cmd_model_pin_set("orchestrator", "openai-codex/gpt-5")
            write.assert_not_called()
        finally:
            setup_models.fcntl.flock(handle.fileno(), setup_models.fcntl.LOCK_UN)
            handle.close()

    def test_model_pin_clear_fails_before_mutate_when_lock_held(self):
        import set_agents_app as app
        lock_path = Path(tempfile.mkdtemp()) / "models-apply.lock"
        lock_path.write_text("", encoding="utf-8")
        handle = lock_path.open("a+", encoding="utf-8")
        setup_models.fcntl.flock(handle.fileno(), setup_models.fcntl.LOCK_EX)
        try:
            with mock.patch.object(setup_models, "_preference_lock_path", return_value=lock_path), \
                 mock.patch.object(app, "atomic_write") as write:
                with self.assertRaises(setup_models.ModelsError):
                    app.cmd_model_pin_clear("orchestrator")
            write.assert_not_called()
        finally:
            setup_models.fcntl.flock(handle.fileno(), setup_models.fcntl.LOCK_UN)
            handle.close()


class ConcurrencyAndSubprocessTests(unittest.TestCase):
    def test_concurrent_host_pin_writer_blocks(self):
        lock_path = Path(tempfile.mkdtemp()) / "models-apply.lock"
        lock_path.write_text("", encoding="utf-8")
        handle = lock_path.open("a+", encoding="utf-8")
        setup_models.fcntl.flock(handle.fileno(), setup_models.fcntl.LOCK_EX)
        try:
            with mock.patch.object(setup_models, "_preference_lock_path", return_value=lock_path):
                with self.assertRaises(setup_models.ModelsError):
                    setup_models.write_host_pin_locked("agy", "model", "x/y")
        finally:
            setup_models.fcntl.flock(handle.fileno(), setup_models.fcntl.LOCK_UN)
            handle.close()

    def test_catalog_subprocess_respects_byte_limit(self):
        huge = b"x/y\n" + b"a" * (setup_models._CHILD_BUDGET + 1)
        with mock.patch.object(setup_models.model_state, "_bounded_child", return_value=("limited", huge, len(huge))), \
             mock.patch.object(setup_models.shutil, "which", return_value="/bin/opencode"):
            models = setup_models._fetch_opencode_models({"areas": {}, "roles": {}})
        self.assertEqual(models, [])

    def test_sanitize_rejects_unicode_format_chars(self):
        self.assertIsNone(setup_models._sanitize_model_id("openai/\u202Eevil"))


if __name__ == "__main__":
    unittest.main()
