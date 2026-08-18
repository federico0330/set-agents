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


def _toml_with_subscription(name: str, value) -> str:
    """The repo's own loaded config, with `[subscriptions].<name>` set to `value`
    (True/False) or removed entirely (`value=None` -- absent, i.e. auto), then
    re-emitted. ADR-0048 (024 C2, AC-03) leaves the tracked file's [subscriptions]
    empty, so there is no longer a live 'openai = true' line to regex-match and
    strip (the old `_models_toml_without` technique this replaces) -- load+mutate+
    emit is the same idiom test_harness.py's `_repo_models_variant` already uses."""
    config = models_config.load_config()
    if value is None:
        config["subscriptions"].pop(name, None)
    else:
        config["subscriptions"][name] = value
    return models_config.emit(config)


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
        toml_text = _toml_with_subscription("openai", False)
        models_config.detect_subscriptions = lambda config: {"openai", "anthropic", "zen"}
        with self.assertRaises(models_config.ModelsError):
            self._load(toml_text)

    def test_absent_and_detected_loads_silently(self):
        toml_text = _toml_with_subscription("openai", None)
        models_config.detect_subscriptions = lambda config: {"openai", "anthropic", "zen"}
        roles, stderr = self._load(toml_text)
        self.assertTrue(roles)
        self.assertNotIn("WARN degraded", stderr)

    def test_absent_and_undetected_warns_but_never_dies(self):
        toml_text = _toml_with_subscription("openai", None)
        models_config.detect_subscriptions = lambda config: {"anthropic"}
        roles, stderr = self._load(toml_text)
        self.assertTrue(roles)
        self.assertIn("WARN degraded", stderr)
        self.assertIn("PROVIDER_UNAUTHENTICATED", stderr)

    def test_probe_failure_on_absent_key_also_warns_and_keeps(self):
        toml_text = _toml_with_subscription("openai", None)
        models_config.detect_subscriptions = lambda config: None
        roles, stderr = self._load(toml_text)
        self.assertTrue(roles)
        self.assertIn("WARN degraded", stderr)

    def test_strict_env_restores_the_historical_die(self):
        toml_text = _toml_with_subscription("openai", None)
        models_config.detect_subscriptions = lambda config: set()
        os.environ["SET_AGENTS_STRICT_MODELS"] = "1"
        with self.assertRaises(models_config.ModelsError):
            self._load(toml_text)

    # ADR-0048 (024 C2): `load_role_tiers` pre-dated ADR-0029 and, uniquely among the
    # two subscription-consuming loaders, never got its tri-state tolerance -- this was
    # invisible for the whole life of this contract because the tracked [subscriptions]
    # always declared every USED provider explicitly `true`. AC-03 (neutral tracked
    # default) turned the gap into a hard, unconditional `die()` on every tiered role,
    # on every machine, on every build -- caught live by `verify.sh` after 024 C2's own
    # subscriptions edit. These three mirror `load_roles`'s own tri-state tests above,
    # against `load_role_tiers` instead.
    def test_tier_table_explicit_false_still_dies(self):
        config = models_config.load_config()
        config["subscriptions"]["openai"] = False
        with self.assertRaises(models_config.ModelsError):
            models_config.load_role_tiers(config, "go-zen")

    def test_tier_table_absent_and_detected_loads_silently(self):
        config = models_config.load_config()
        config["subscriptions"].pop("openai", None)
        models_config.detect_subscriptions = lambda cfg: {"openai", "anthropic", "zen"}
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            tiers = models_config.load_role_tiers(config, "go-zen")
        self.assertTrue(tiers)
        self.assertNotIn("WARN degraded", stderr.getvalue())

    def test_tier_table_absent_and_undetected_warns_but_never_dies(self):
        config = models_config.load_config()
        config["subscriptions"].pop("openai", None)
        models_config.detect_subscriptions = lambda cfg: {"anthropic"}
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            tiers = models_config.load_role_tiers(config, "go-zen")
        self.assertTrue(tiers)
        self.assertIn("WARN degraded", stderr.getvalue())

    def test_detect_never_returns_credential_material(self):
        # Shape contract: a set of subscription names (or None) — nothing else.
        result = models_config.detect_subscriptions(models_config.load_config())
        if result is not None:
            self.assertIsInstance(result, set)
            self.assertTrue(result <= {"openai", "anthropic", "zen", "ollama"})

    def test_wizard_cache_ttl_starts_at_10_and_60_minutes(self):
        self.assertEqual(models_config.WIZARD_SUBSCRIPTIONS_TTL_SECONDS, 10 * 60)
        self.assertEqual(models_config.WIZARD_CATALOG_TTL_SECONDS, 60 * 60)

    def test_wizard_cache_round_trip_is_names_and_ids_only(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "wizard-live-cache.json"
            now = 1_700_000_000.0
            models_config.write_wizard_live_cache(
                "subscriptions",
                {"at": now, "names": ["openai", "anthropic"], "error": False},
                path=path,
            )
            models_config.write_wizard_live_cache(
                "catalog",
                {"at": now, "ids": ["openai/gpt-5.5", "anthropic/claude-opus-4"]},
                path=path,
            )
            doc = models_config.load_wizard_live_cache(path)
            self.assertEqual(set(doc["subscriptions"]["names"]), {"openai", "anthropic"})
            self.assertEqual(doc["catalog"]["ids"], ["openai/gpt-5.5", "anthropic/claude-opus-4"])
            raw = path.read_text(encoding="utf-8")
            self.assertNotIn("sk-", raw)
            self.assertNotIn("KEY=", raw)
            self.assertNotIn("HOME", raw)
            self.assertTrue(
                models_config.wizard_cache_entry_fresh(
                    doc["subscriptions"], models_config.WIZARD_SUBSCRIPTIONS_TTL_SECONDS,
                    now=now + 9 * 60,
                ),
            )
            self.assertFalse(
                models_config.wizard_cache_entry_fresh(
                    doc["subscriptions"], models_config.WIZARD_SUBSCRIPTIONS_TTL_SECONDS,
                    now=now + 11 * 60,
                ),
            )

    def test_wizard_cache_rejects_non_id_payloads(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "wizard-live-cache.json"
            models_config.write_wizard_live_cache(
                "subscriptions",
                {"at": 1.0, "names": ["OPENAI_API_KEY=secret"], "error": False},
                path=path,
            )
            self.assertEqual(models_config.load_wizard_live_cache(path), {})


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
