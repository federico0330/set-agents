import io
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ai/scripts"))
import set_agents_app as app  # noqa: E402
import setup_models  # noqa: E402


class HomeFirstPaintTests(unittest.TestCase):
    def test_first_frame_is_cache_only_and_has_human_actions(self):
        with mock.patch.object(app, "banner"), \
             mock.patch.object(app, "launch_update_check") as update, \
             mock.patch.object(app, "measure_hosts") as hosts, \
             mock.patch.object(app, "drift_state") as drift, \
             mock.patch.object(app, "first_run") as first, \
             mock.patch.object(app, "experto_activo", return_value=False), \
             mock.patch.object(app.tui, "run_picker", return_value=None) as picker, \
             mock.patch("sys.stdout", io.StringIO()):
            self.assertEqual(app.menu(), 0)
        update.assert_not_called(); hosts.assert_not_called(); drift.assert_not_called(); first.assert_not_called()
        labels = picker.call_args.args[0]
        self.assertEqual(tuple(labels[:7]), tuple(app._menu_rows(app.visible_actions(False)))[:7])
        for expected in ("Estado", "Configurar", "Modelos", "Forma de trabajo", "Actualizar estado", "Modo experto", "Salir"):
            self.assertTrue(any(expected in row for row in labels))

    def test_refresh_failure_keeps_cache_and_is_retryable(self):
        ctx = {"drift": "ok", "update_badge": "al día"}
        with mock.patch.object(app, "launch_update_check", side_effect=OSError("no")), \
             mock.patch.object(app, "measure_hosts_visibly", side_effect=OSError("no")), \
             mock.patch.object(app, "drift_state", return_value="ok") as drift, \
             mock.patch.object(app.tui, "with_progress", side_effect=lambda _l, fn, **_k: fn()), \
             mock.patch("sys.stderr", io.StringIO()) as err:
            app._run_home_action("actualizar", {}, ctx)
        self.assertEqual(ctx["update_badge"], "al día")
        drift.assert_called_once()
        self.assertEqual(ctx["drift"], "ok")
        self.assertIn("reintentar", err.getvalue().lower())

    def test_host_failure_does_not_skip_drift_refresh(self):
        ctx = {"drift": "stale", "update_badge": "al día"}
        with mock.patch.object(app, "launch_update_check", return_value="al día"), \
             mock.patch.object(app, "measure_hosts_visibly", side_effect=OSError("no")), \
             mock.patch.object(app, "drift_state", return_value="ok") as drift, \
             mock.patch.object(app.tui, "with_progress", side_effect=lambda _l, fn, **_k: fn()), \
             mock.patch("sys.stderr", io.StringIO()):
            app._run_home_action("actualizar", {}, ctx)
        drift.assert_called_once()
        self.assertEqual(ctx["drift"], "ok")


class ModelsPresentationTests(unittest.TestCase):
    def test_model_panel_names_four_evidence_sources_and_model_is_temporary(self):
        state = {
            "observed": {"model": "opaque/luna", "source": "opencode-sanitized-export", "reason": None},
            "desired": {"model": "opaque/terra", "source": "set-effective-config", "reason": None},
            "installed": {"model": "opaque/terra", "source": "installed-role-artifact", "reason": None},
            "routing": {"status": "dynamic", "source": "model-preference.toml", "reason": None},
        }
        text = "\n".join(setup_models._model_state_lines(state))
        self.assertIn("Último envío observado", text)
        self.assertIn("Default de SET", text)
        self.assertIn("Instalado", text)
        self.assertIn("Routing", text)
        self.assertIn("elección temporal", text)
        self.assertNotIn("modelo actual", text.lower())

    def test_plugin_warning_is_read_only(self):
        warnings = setup_models.plugin_model_warnings((ROOT / "not-here-gentle-logo.tsx",))
        self.assertEqual([], warnings, "un path ausente no es una referencia configurada")

    def test_pending_convergence_and_stale_are_visible(self):
        state = {
            "observed": {"model": "opaque/luna", "source": "opencode", "reason": "timeout"},
            "desired": {"model": "opaque/terra", "source": "set-effective-config"},
            "installed": {"model": "opaque/old", "source": "installed-role-artifact"},
            "routing": {"status": "dynamic", "source": "model-preference.toml"},
            "convergence": {"status": "pending_apply"},
            "refresh": {"observed": {"status": "stale", "checked_at": "2026-01-01T00:00:00Z"}},
        }
        text = "\n".join(setup_models._model_state_lines(state))
        self.assertIn("pendiente de aplicar", text)
        self.assertIn("desactualizado", text)
        self.assertIn("la consulta venció", text)

    def test_first_frame_seeds_host_counts_from_disk(self):
        with mock.patch.object(app, "_load_host_counts_cache", return_value={"opencode": 3}), \
             mock.patch.object(app.ui.GLOBAL_CACHE, "get", return_value=None), \
             mock.patch.object(app.ui.GLOBAL_CACHE, "set") as cache_set:
            app._seed_host_counts_cache()
        cache_set.assert_called_once_with("host_counts", {"opencode": 3})


if __name__ == "__main__":
    unittest.main()
