"""UI refresh — the Modelos wizard stops dumping and learns ADR-0029.

New tests only. The immutable suite pins WIZARD_ITEMS indexes 0-4 and the
dropped-cells hint; here we cover the compact panel (`_panel_lines`), the
end of the double status dump, the tri-state subscriptions branch, and the
discovered-providers toggle.
"""

import io
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ai/scripts"))

import setup_models  # noqa: E402


def _config():
    return {
        "areas": {"audit": {"claude": "opus", "codex": "gpt-5.5", "codex_effort": "high",
                            "opencode": {"go-zen": "openai/gpt-5.5"}}},
        "roles": {"debugger": {"claude": "opus"}, "implementer": {"codex": "gpt-5.4"}},
        "subscriptions": {"anthropic": True, "ollama": False},
        "routing": {"discovered_providers": []},
    }


class PanelLinesTests(unittest.TestCase):
    def test_panel_is_compact_overrides_collapse_to_a_count(self):
        lines = setup_models._panel_lines(_config(), [], "go-zen", detected=None)
        text = "\n".join(lines)
        self.assertIn("audit", text)
        self.assertIn("overrides de rol: 2", text)
        self.assertNotIn("debugger:", text)  # the old per-role dump is gone

    def test_tri_state_origins_pin_off_and_auto(self):
        lines = setup_models._panel_lines(_config(), [], "go-zen", detected={"openai", "anthropic"})
        subs_line = lines[0]
        self.assertIn("anthropic=✓pin", subs_line)
        self.assertIn("ollama=✗off", subs_line)
        self.assertIn("openai=auto✓", subs_line)  # absent key, probe-alive

    def test_discovered_providers_surface_when_configured(self):
        config = _config()
        config["routing"]["discovered_providers"] = ["opencode-zen"]
        text = "\n".join(setup_models._panel_lines(config, [], "go-zen"))
        self.assertIn("opencode-zen", text)


class WizardBehaviorTests(unittest.TestCase):
    def _run(self, picks, config=None):
        config = config or _config()
        with mock.patch.object(setup_models.sys.stdin, "isatty", return_value=True), \
             mock.patch.object(setup_models.models_config, "detect_subscriptions", return_value=None), \
             mock.patch.object(setup_models.tui, "run_picker", side_effect=picks) as picker:
            buf = io.StringIO()
            with mock.patch("sys.stdout", buf):
                setup_models.wizard(config, [{"role": "audit"}], "go-zen",
                                    Path("roles.tsv"), Path("models.toml"))
        return config, buf.getvalue(), picker

    def test_the_status_avalanche_is_gone_from_stdout(self):
        _, out, picker = self._run([None])  # Esc right away
        self.assertNotIn("AREA", out)
        self.assertIn("AREA", picker.call_args.kwargs["header"])  # lives in the picker frame

    def test_subscription_auto_removes_the_key(self):
        config, out, _ = self._run([
            setup_models.tui.Selected(2),   # Suscripciones
            setup_models.tui.Selected(1),   # choose(): "ollama" (sorted: anthropic, ollama)
            setup_models.tui.Selected(2),   # tri-state: Auto (borrar la línea)
            setup_models.tui.Selected(4),   # Salir sin guardar
        ])
        self.assertNotIn("ollama", config["subscriptions"])
        self.assertIn("auto", out)

    def test_discovered_provider_toggle_round_trips(self):
        config, out, _ = self._run([
            setup_models.tui.Selected(6),   # Proveedores descubiertos
            setup_models.tui.Selected(0),   # opencode-zen
            setup_models.tui.Selected(4),   # Salir sin guardar
        ])
        self.assertEqual(config["routing"]["discovered_providers"], ["opencode-zen"])
        self.assertIn("MODEL_METADATA_INFERRED", out)


if __name__ == "__main__":
    unittest.main()
