"""AC-2.5 — Models wizard first paint is not blocked by a frozen probe.

A probe that sleeps 5 seconds must still let the first run_picker (the first
frame) happen in under 300 ms. Disk cache / pins are what that frame shows.
"""

import os
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ai/scripts"))

import setup_models  # noqa: E402

FIRST_PAINT_BUDGET_S = 0.3
PROBE_FREEZE_S = 5.0


def _config():
    return {
        "areas": {"audit": {"claude": "opus", "codex": "gpt-5.5", "codex_effort": "high",
                            "opencode": "openai/gpt-5.5"}},
        "roles": {},
        "subscriptions": {"anthropic": True},
        "routing": {"discovered_providers": []},
    }


class FirstPaintTests(unittest.TestCase):
    def test_frozen_probe_does_not_delay_first_frame_past_300ms(self):
        probe_started = []

        def frozen_probe(_config):
            probe_started.append(time.monotonic())
            time.sleep(PROBE_FREEZE_S)
            return {"openai"}

        first_frame = []

        def fake_picker(*_args, **_kwargs):
            first_frame.append(time.monotonic())
            return setup_models.tui.Selected(4)  # Salir sin guardar (index 4, pinned)

        with tempfile.TemporaryDirectory() as td, \
             mock.patch.dict(os.environ, {"SET_AGENTS_STATE": td}), \
             mock.patch.object(setup_models.sys.stdin, "isatty", return_value=True), \
             mock.patch.object(setup_models.models_config, "detect_subscriptions",
                               side_effect=frozen_probe), \
             mock.patch.object(setup_models.tui, "run_picker", side_effect=fake_picker):
            started = time.monotonic()
            rc = setup_models.wizard(
                _config(), [{"role": "audit"}],
                Path("roles.tsv"), Path("models.toml"),
            )

        self.assertEqual(rc, 0)
        self.assertEqual(len(first_frame), 1, "wizard must paint once before exiting")
        self.assertLess(
            first_frame[0] - started,
            FIRST_PAINT_BUDGET_S,
            f"first frame took {first_frame[0] - started:.3f}s; probe must not run first",
        )
        self.assertTrue(
            not probe_started or probe_started[0] >= first_frame[0],
            "detect_subscriptions must not run before the first run_picker",
        )


if __name__ == "__main__":
    unittest.main()
