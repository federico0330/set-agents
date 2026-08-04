"""UI/installer follow-up — the opencode lane derives from the probe.

The manual use-go-zen.sh/use-zen.sh/use-local.sh wrappers are gone;
`models_config.auto_profile()` maps live probed pairs to a lane, and
build.sh writes `active-profile` only when the file is missing (an existing
lane, auto or hand-set, is never flipped silently).
"""

import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ai/scripts"))

import models_config  # noqa: E402


def _probe(live_pairs):
    return {("opencode", provider): ["m"] for provider in live_pairs}


class AutoProfileTests(unittest.TestCase):
    def _derive(self, inventory):
        with mock.patch("routing_core.catalog.probe_inventory", return_value=inventory):
            return models_config.auto_profile(config={})

    def test_both_opencode_pairs_live_is_go_zen(self):
        self.assertEqual(self._derive(_probe(["opencode-zen", "opencode-go"])), "go-zen")

    def test_zen_only_is_zen(self):
        self.assertEqual(self._derive(_probe(["opencode-zen"])), "zen")

    def test_no_opencode_pair_is_local(self):
        self.assertEqual(self._derive(_probe(["anthropic", "openai-codex"])), "local")
        self.assertEqual(self._derive({}), "local")

    def test_probe_failure_is_none_never_a_guess(self):
        with mock.patch("routing_core.catalog.probe_inventory", side_effect=OSError("down")):
            self.assertIsNone(models_config.auto_profile(config={}))

    def test_dead_pair_rows_do_not_count(self):
        inventory = {("opencode", "opencode-go"): [], ("opencode", "opencode-zen"): ["m"]}
        with mock.patch("routing_core.catalog.probe_inventory", return_value=inventory):
            self.assertEqual(models_config.auto_profile(config={}), "zen")


class WrappersAreGoneTests(unittest.TestCase):
    def test_the_manual_lane_scripts_no_longer_exist(self):
        for name in ("use-go-zen.sh", "use-zen.sh", "use-local.sh"):
            self.assertFalse((ROOT / name).exists(), name)

    def test_build_sh_only_writes_a_missing_active_profile(self):
        text = (ROOT / "build.sh").read_text()
        self.assertIn("ensure_active_profile", text)
        self.assertIn('[ -f "$ROOT/active-profile" ] && return 0', text)
        self.assertIn("PROFILE_AUTO", text)


if __name__ == "__main__":
    unittest.main()
