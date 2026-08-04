"""Feature 017 PKG-A1/A2 (ADR-0029) — probe-backed subscription tri-state and
universal-alias claude frontmatter.

New tests only. The immutable contract (explicit `false` dies:
tests/test_harness.py::test_models_config_rejects_inactive_subscription) is
untouched; these cover the two NEW states: absent-and-detected, and
absent-and-undetected (warn-and-keep, build never dies).
"""

import contextlib
import io
import os
import re
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ai/scripts"))

import models_config  # noqa: E402


def _models_toml_without(line_prefix: str, replacement: str = "") -> str:
    text = (ROOT / "models.toml").read_text()
    pattern = re.compile(rf"(?m)^{re.escape(line_prefix)} *= *\w+\n")
    self_check = pattern.search(text)
    assert self_check, f"models.toml no longer has a '{line_prefix} =' line"
    return pattern.sub(replacement, text)


class SubscriptionTriStateTests(unittest.TestCase):
    def setUp(self):
        self._orig_detect = models_config.detect_subscriptions
        os.environ.pop("SET_AGENTS_STRICT_MODELS", None)

    def tearDown(self):
        models_config.detect_subscriptions = self._orig_detect
        os.environ.pop("SET_AGENTS_STRICT_MODELS", None)

    def _load(self, toml_text):
        with tempfile.NamedTemporaryFile("w", suffix=".toml", delete=False) as handle:
            handle.write(toml_text)
            path = handle.name
        try:
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                roles = models_config.load_roles("go-zen", models_path=path)
            return roles, stderr.getvalue()
        finally:
            os.unlink(path)

    def test_explicit_false_still_dies(self):
        toml_text = _models_toml_without("openai", "openai = false\n")
        models_config.detect_subscriptions = lambda config: {"openai", "anthropic", "zen"}
        with self.assertRaises(models_config.ModelsError):
            self._load(toml_text)

    def test_absent_and_detected_loads_silently(self):
        toml_text = _models_toml_without("openai")
        models_config.detect_subscriptions = lambda config: {"openai", "anthropic", "zen"}
        roles, stderr = self._load(toml_text)
        self.assertTrue(roles)
        self.assertNotIn("WARN degraded", stderr)

    def test_absent_and_undetected_warns_but_never_dies(self):
        toml_text = _models_toml_without("openai")
        models_config.detect_subscriptions = lambda config: {"anthropic"}
        roles, stderr = self._load(toml_text)
        self.assertTrue(roles)
        self.assertIn("WARN degraded", stderr)
        self.assertIn("PROVIDER_UNAUTHENTICATED", stderr)

    def test_probe_failure_on_absent_key_also_warns_and_keeps(self):
        toml_text = _models_toml_without("openai")
        models_config.detect_subscriptions = lambda config: None
        roles, stderr = self._load(toml_text)
        self.assertTrue(roles)
        self.assertIn("WARN degraded", stderr)

    def test_strict_env_restores_the_historical_die(self):
        toml_text = _models_toml_without("openai")
        models_config.detect_subscriptions = lambda config: set()
        os.environ["SET_AGENTS_STRICT_MODELS"] = "1"
        with self.assertRaises(models_config.ModelsError):
            self._load(toml_text)

    def test_detect_never_returns_credential_material(self):
        # Shape contract: a set of subscription names (or None) — nothing else.
        result = models_config.detect_subscriptions(models_config.load_config())
        if result is not None:
            self.assertIsInstance(result, set)
            self.assertTrue(result <= {"openai", "anthropic", "zen", "ollama"})


class UniversalAliasFrontmatterTests(unittest.TestCase):
    def test_every_claude_agent_pins_a_universal_alias_or_omits_model(self):
        for path in sorted((ROOT / "Global/claude-code/agents").glob("*.md")):
            match = re.search(r"(?m)^model: (.+)$", path.read_text())
            if match:
                self.assertIn(match.group(1).strip(), {"sonnet", "opus", "haiku"}, path.name)

    def test_fable_curated_roles_omit_the_model_line(self):
        # package-reviewer/adversarial-judge are curated to `fable` in models.toml —
        # a non-universal alias, so their generated frontmatter must omit model:.
        for role in ("package-reviewer", "adversarial-judge"):
            text = (ROOT / f"Global/claude-code/agents/{role}.md").read_text()
            self.assertNotRegex(text, r"(?m)^model: ", role)


if __name__ == "__main__":
    unittest.main()
