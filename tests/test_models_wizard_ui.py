"""End-user Modelos wizard — compact human header, 4 actions + Avanzado."""

import io
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ai/scripts"))

import setup_models  # noqa: E402


def _config():
    return {
        "areas": {"audit": {"claude": "opus", "codex": "gpt-5.5", "codex_effort": "high",
                            "opencode": "openai/gpt-5.5"}},
        "roles": {"debugger": {"claude": "opus"}, "implementer": {"codex": "gpt-5.4"}},
        "subscriptions": {"anthropic": True, "ollama": False},
        "routing": {"discovered_providers": []},
        "catalog": {"claude": ["opus"], "codex": ["gpt-5.5"], "cursor": ["inherit"]},
    }


class PanelLinesTests(unittest.TestCase):
    def test_panel_is_two_human_lines_no_jargon(self):
        with mock.patch.object(setup_models, "_load_pins", return_value={}), \
             mock.patch.object(setup_models.models_config, "load_models_overlay", return_value={}):
            lines = setup_models._panel_lines(_config(), [], detected=None)
        self.assertLessEqual(len(lines), 3)
        text = "\n".join(lines)
        self.assertIn("Elige solo", text)
        self.assertIn("Cuentas:", text)
        self.assertIn("anthropic", text)
        self.assertNotIn("ADR-", text)
        self.assertNotIn("models.local.toml", text)
        self.assertNotIn("discovered_providers", text)
        self.assertNotIn("✓pin", text)
        self.assertNotIn("audit", text)
        matrix = "\n".join(setup_models._overrides_matrix_lines(_config()))
        self.assertIn("audit", matrix)
        self.assertIn("2 roles distintos", matrix)

    def test_accounts_list_live_and_pinned_on(self):
        with mock.patch.object(setup_models, "_load_pins", return_value={}), \
             mock.patch.object(setup_models.models_config, "load_models_overlay", return_value={}):
            lines = setup_models._panel_lines(_config(), [], detected={"openai", "anthropic"})
        self.assertIn("anthropic", lines[1])
        self.assertIn("openai", lines[1])
        self.assertNotIn("ollama", lines[1])  # off

    def test_preference_count_when_pins_exist(self):
        with mock.patch.object(setup_models, "_load_pins",
                               return_value={"architect": ("openai-codex", "x")}), \
             mock.patch.object(setup_models.models_config, "load_models_overlay", return_value={}):
            lines = setup_models._panel_lines(_config(), [])
        self.assertIn("1 preferencia tuya", lines[0])

    def test_panel_shows_subscription_age(self):
        with mock.patch.object(setup_models, "_load_pins", return_value={}), \
             mock.patch.object(setup_models.models_config, "load_models_overlay", return_value={}):
            lines = setup_models._panel_lines(
                _config(), [], detected={"openai"},
                subscription_age_s=4 * 60 + 20,
            )
        self.assertIn("hace 4 min", lines[1])
        self.assertIn("openai", lines[1])

    def test_panel_degrades_named_when_probe_failed(self):
        with mock.patch.object(setup_models, "_load_pins", return_value={}), \
             mock.patch.object(setup_models.models_config, "load_models_overlay", return_value={}):
            lines = setup_models._panel_lines(
                _config(), [], detected=None, subscription_error=True,
            )
        self.assertIn(setup_models.SUBSCRIPTION_PROBE_FAILED, lines[1])


class StatusLinesNoDumpTests(unittest.TestCase):
    def test_status_never_dumps_python_dicts(self):
        config = _config()
        config["roles"]["tiered"] = {"tiers": {"fast": {"opencode": "x"}}}
        text = "\n".join(setup_models._status_lines(config, []))
        self.assertNotIn("{", text)
        self.assertIn("roles distintos", text)
        self.assertIn("AREA", text)


class WizardBehaviorTests(unittest.TestCase):
    def _run(self, picks, config=None):
        config = config or _config()
        with tempfile.TemporaryDirectory() as td, \
             mock.patch.dict(os.environ, {"SET_AGENTS_STATE": td}), \
             mock.patch.object(setup_models.sys.stdin, "isatty", return_value=True), \
             mock.patch.object(setup_models.models_config, "detect_subscriptions", return_value=None), \
             mock.patch.object(setup_models.tui, "with_progress",
                               side_effect=lambda msg, fn, **kwargs: fn()), \
             mock.patch.object(setup_models, "_load_pins", return_value={}), \
             mock.patch.object(setup_models.tui, "run_picker", side_effect=picks) as picker:
            buf = io.StringIO()
            with mock.patch("sys.stdout", buf):
                setup_models.wizard(config, [{"role": "audit"}],
                                    Path("roles.tsv"), Path("models.toml"))
        return config, buf.getvalue(), picker

    def test_header_is_human_and_names_the_four_evidence_sources(self):
        _, out, picker = self._run([None])
        self.assertNotIn("AREA", out)
        header = picker.call_args.kwargs["header"]
        self.assertIn("Elige solo", header)
        self.assertNotIn("ADR-", header)
        for label in ("Último envío observado", "Default de SET", "Instalado", "Routing"):
            self.assertIn(label, header)
        self.assertIn("elección temporal", header)

    def test_wizard_items_are_end_user_actions_with_progressive_options(self):
        _, _, picker = self._run([None])
        items = picker.call_args.args[0]
        self.assertEqual(
            items,
            ("Cambiar default", "Revisar roles", "Actualizar datos", "Listo",
             "Explicar /model", "Más opciones"),
        )

    def test_subscription_auto_writes_the_overlay_never_the_tracked_config(self):
        with mock.patch.object(setup_models.models_config, "write_subscription_overlay",
                               return_value={"anthropic": True}) as write:
            config, out, _ = self._run([
                setup_models.tui.Selected(5),   # Más opciones
                setup_models.tui.Selected(2),   # Cuentas
                setup_models.tui.Selected(1),   # ollama
                setup_models.tui.Selected(2),   # Auto
                setup_models.tui.Selected(3),   # Listo
            ])
        write.assert_called_once_with("ollama", None)
        self.assertEqual(config["subscriptions"], {"anthropic": True, "ollama": False})
        self.assertEqual(config["_subscriptions_overlay"], {"anthropic": True})
        self.assertIn("auto en este equipo", out)
        self.assertIn("efectivo ya", out)

    def test_discovered_provider_toggle_via_avanzado(self):
        config, out, _ = self._run([
            setup_models.tui.Selected(5),   # Más opciones
            setup_models.tui.Selected(3),   # Avanzado
            setup_models.tui.Selected(1),   # Proveedores descubiertos
            setup_models.tui.Selected(1),   # Lista manual
            setup_models.tui.Selected(3),   # opencode-zen
            setup_models.tui.Selected(5),   # Volver
            setup_models.tui.Selected(3),   # Listo
        ])
        self.assertEqual(config["routing"]["discovered_providers"], ["opencode-zen"])
        self.assertIn("MODEL_METADATA_INFERRED", out)

    def test_discovered_provider_auto_and_none_policies(self):
        config, out, _ = self._run([
            setup_models.tui.Selected(5),
            setup_models.tui.Selected(3),
            setup_models.tui.Selected(1),
            setup_models.tui.Selected(0),   # auto
            setup_models.tui.Selected(5),
            setup_models.tui.Selected(3),
        ])
        self.assertEqual(config["routing"]["discovered_providers"], "auto")
        self.assertIn("discovered_providers = auto", out)

        config, out, _ = self._run([
            setup_models.tui.Selected(5),
            setup_models.tui.Selected(3),
            setup_models.tui.Selected(1),
            setup_models.tui.Selected(2),   # Ninguno
            setup_models.tui.Selected(5),
            setup_models.tui.Selected(3),
        ])
        self.assertEqual(config["routing"]["discovered_providers"], [])

    def test_first_paint_does_not_call_detect_subscriptions(self):
        config = _config()
        with tempfile.TemporaryDirectory() as td, \
             mock.patch.dict(os.environ, {"SET_AGENTS_STATE": td}), \
             mock.patch.object(setup_models.sys.stdin, "isatty", return_value=True), \
             mock.patch.object(setup_models.models_config, "detect_subscriptions") as probe, \
             mock.patch.object(setup_models, "_load_pins", return_value={}), \
             mock.patch.object(setup_models.tui, "run_picker",
                               return_value=setup_models.tui.Selected(3)):
            setup_models.wizard(config, [{"role": "audit"}],
                                Path("roles.tsv"), Path("models.toml"))
        probe.assert_not_called()

    def test_refresh_explicitly_probes_subscriptions_and_catalog(self):
        config = _config()
        progress_messages = []

        def fake_progress(message, fn, **kwargs):
            progress_messages.append(message)
            return fn()

        with tempfile.TemporaryDirectory() as td, \
             mock.patch.dict(os.environ, {"SET_AGENTS_STATE": td}), \
             mock.patch.object(setup_models.sys.stdin, "isatty", return_value=True), \
             mock.patch.object(setup_models.models_config, "detect_subscriptions",
                               return_value={"openai"}), \
             mock.patch.object(setup_models.tui, "with_progress", side_effect=fake_progress), \
             mock.patch.object(setup_models, "_fetch_opencode_models",
                               return_value=["openai/gpt-5.5"]), \
             mock.patch.object(setup_models, "_load_pins", return_value={}), \
             mock.patch.object(setup_models.tui, "run_picker", side_effect=[
                 setup_models.tui.Selected(2),  # Actualizar datos
                 setup_models.tui.Selected(3),  # Listo
             ]) as picker:
            setup_models.wizard(config, [{"role": "audit"}],
                                Path("roles.tsv"), Path("models.toml"))
        self.assertIn("midiendo suscripciones", progress_messages)
        self.assertIn("listando modelos", progress_messages)
        self.assertEqual(picker.call_count, 2)

    def test_esc_after_campo_does_not_mutate_roles(self):
        config = _config()
        with mock.patch.object(setup_models, "available_opencode_models",
                               return_value=["openai/x"]):
            self._run([
                setup_models.tui.Selected(0),  # Cambiar default
                setup_models.tui.Selected(1),  # Por rol
                setup_models.tui.Selected(0),  # audit
                setup_models.tui.Selected(3),  # opencode
                None,                          # Esc
                setup_models.tui.Selected(3),  # Listo
            ], config=config)
        self.assertEqual(config["roles"], {
            "debugger": {"claude": "opus"}, "implementer": {"codex": "gpt-5.4"},
        })

    def test_campo_offers_model_effort_and_cursor_axes(self):
        captured = []

        def fake_choose(prompt, options, **kwargs):
            captured.append((prompt, list(options)))
            if prompt == "Area":
                return options[0]
            return None

        with mock.patch.object(setup_models, "choose", side_effect=fake_choose):
            self._run([
                setup_models.tui.Selected(0),  # Cambiar default
                setup_models.tui.Selected(0),  # Por area
                setup_models.tui.Selected(3),  # Listo
            ])
        campo = [item for item in captured if item[0] == "Campo"]
        self.assertTrue(campo)
        self.assertEqual(campo[0][1], list(setup_models.OVERRIDE_FIELDS))
        self.assertIn("cursor", campo[0][1])
        self.assertIn("codex_effort", campo[0][1])


class GroupedModelPickerTests(unittest.TestCase):
    def test_choose_groups_by_provider_and_maps_selected_index_to_the_model_id(self):
        models = ["opencode-go/a", "opencode-go/b-free", "openai/x"]
        captured = {}

        def fake_picker(items, **kwargs):
            captured["items"] = list(items)
            captured["headers"] = list(kwargs.get("headers") or [])
            captured["suffixes"] = list(kwargs.get("suffixes") or [])
            captured["current"] = kwargs.get("current")
            return setup_models.tui.Selected(2)

        with mock.patch.object(setup_models.tui, "run_picker", side_effect=fake_picker):
            result = setup_models.choose(
                "Modelo", models, current="opencode-go/b-free",
                group_by_provider=True,
                used_by={"opencode-go/a": ["implementer"]},
            )
        self.assertEqual(result, "opencode-go/b-free")
        self.assertEqual(captured["items"][0], "opencode-go (2)")
        self.assertEqual(captured["headers"], [0, 3])
        self.assertIn("← implementer", captured["suffixes"][1])

    def test_choose_without_grouping_keeps_a_flat_index_into_options(self):
        options = ["claude", "codex", "effort"]
        with mock.patch.object(
            setup_models.tui, "run_picker", return_value=setup_models.tui.Selected(1),
        ) as picker:
            result = setup_models.choose("Campo", options)
        self.assertEqual(result, "codex")
        self.assertEqual(list(picker.call_args.args[0]), options)


class ModelsInUseTests(unittest.TestCase):
    def test_models_in_use_unique_first_seen_and_walks_tier_pins(self):
        used = setup_models._models_in_use({
            "areas": {"coord": {"opencode": "openai/gpt-5.5"}},
            "roles": {
                "debugger": {"opencode": "openai/gpt-5.5"},
                "implementer": {"tiers": {"fast": {"opencode": "openai/gpt-5.6-luna"}}},
            },
        })
        self.assertEqual(
            {key: used.get(key) for key in ("openai/gpt-5.5", "openai/gpt-5.6-luna")},
            {"openai/gpt-5.5": ["coord", "debugger"],
             "openai/gpt-5.6-luna": ["implementer"]},
        )


class OverlayWriteIsValidatedTests(unittest.TestCase):
    """ADR-0071 moved area/role taste to `models.local.toml`, and with it the write moved off
    the one path that ran `validate()` -- where separation of duties lives. Both entry points
    (the CLI `--set` and this wizard's "Preferir un modelo") must refuse an illegal cell and
    leave the disk untouched. The CLI half is covered by
    `test_harness::test_setup_models_rejects_separation_violation`; this is the TUI half, which
    is the surface a person actually uses."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.state = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)
        self.overlay = self.state / "models.local.toml"
        patcher = mock.patch.dict(os.environ, {"SET_AGENTS_STATE": str(self.state)})
        patcher.start()
        self.addCleanup(patcher.stop)
        import models_config
        self.factory = models_config.load_config(ROOT / "models.toml")
        self.roster = models_config.load_roster(ROOT / "roles.tsv")

    def _pick(self, area, field, value):
        buf = io.StringIO()
        with mock.patch.object(setup_models, "choose", side_effect=[area, field, value]), \
             mock.patch.object(setup_models, "_confirm_model_mutation", return_value=True), \
             mock.patch("sys.stdout", buf):
            setup_models._edit_overlay_cell(
                self.factory, self.roster, ROOT / "roles.tsv", ROOT / "models.toml", kind="area")
        return buf.getvalue()

    def test_the_wizard_refuses_a_cell_that_breaks_separation_of_duties(self):
        writer_model = self.factory["areas"]["implement"]["codex"]
        output = self._pick("audit", "codex", writer_model)
        self.assertIn("RECHAZADO", output)
        self.assertIn("separation violation", output)
        self.assertFalse(self.overlay.exists(), "un valor ilegal nunca debe tocar el disco")

    def test_a_legal_cell_still_lands_in_the_instance_overlay(self):
        # The wizard unit must never reach build/install on a developer's HOME.
        with mock.patch.object(setup_models, "apply_overlay_model", return_value={
                "status": "pending_apply", "message": "Preferencia guardada; falta confirmar la instalación. Podés reintentar."}):
            output = self._pick("audit", "codex_effort", "low")
        self.assertIn("pending_apply: audit.codex_effort = low", output)


if __name__ == "__main__":
    unittest.main()
