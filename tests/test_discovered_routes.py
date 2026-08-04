"""Feature 017 PKG-B1/B2 (ADR-0029) — synthesized routes from the discovered inventory.

New tests only. The immutable contracts stay untouched and are re-asserted here
from THIS feature's angle: `build_snapshot` never widens (the effective path is a
separate entry point), `ROUTING_PROVIDERS` stays closed (discovered_providers is
a different key), and with the flag absent the composition is byte-identical.
"""

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ai/scripts"))

import models_config  # noqa: E402
from routing_core import catalog as routing_catalog  # noqa: E402
from routing_core import inference  # noqa: E402

CATALOG = ROOT / "ai/catalogs/routes.v1.toml"


def _fixtures():
    config = models_config.load_config()
    roster = models_config.load_roster()
    return config, roster


class InferenceGoldenTests(unittest.TestCase):
    def test_vendor_stems(self):
        for model, stem in (
            ("kimi-k2.7-code", "kimi"), ("openai/gpt-5.6-terra", "gpt"),
            ("claude-opus-4-8", "claude"), ("opus", "claude"),
            ("deepseek-v4-pro", "deepseek"), ("nemotron-super-ultra", "nemotron"),
            ("qwen3-max", "qwen"), ("gemini-3.5-flash", "gemini"),
            ("glm-5.2", "glm"), ("totally-unknown-model", "totally-unknown-model"),
        ):
            self.assertEqual(inference.vendor_stem(model), stem, model)

    def test_tiers_unknown_is_never_frontier(self):
        for model, tier in (
            ("deepseek-v4-pro", "frontier"), ("gpt-5.6-terra", "frontier"),
            ("kimi-k2.7-code", "balanced"), ("gemini-3.5-flash", "fast"),
            ("glm-5.2-mini", "fast"), ("some-mystery-model", "balanced"),
        ):
            self.assertEqual(inference.infer_tier(model), tier, model)
        self.assertNotEqual(inference.infer_tier("unheard-of-frontier-killer"), "frontier")


class EffectiveSnapshotTests(unittest.TestCase):
    def test_flag_absent_is_byte_identical_to_the_curated_snapshot(self):
        config, roster = _fixtures()
        inventory = {("opencode", "opencode-zen"): {"kimi-k2.7-code"}}
        base = routing_catalog.build_snapshot(CATALOG, roster, config)
        effective, inferred = routing_catalog.build_effective_snapshot(CATALOG, roster, config, inventory)
        self.assertEqual(effective, base)
        self.assertEqual(inferred, frozenset())

    def test_discovered_model_synthesizes_a_marked_route(self):
        config, roster = _fixtures()
        config["routing"]["discovered_providers"] = ["opencode-zen"]
        inventory = {("opencode", "opencode-zen"): {"kimi-k2.7-code"}}
        effective, inferred = routing_catalog.build_effective_snapshot(CATALOG, roster, config, inventory)
        synthesized = [r for r in effective.routes if r.provider == "opencode-zen"]
        self.assertEqual(len(synthesized), 1)
        route = synthesized[0]
        self.assertEqual(route.model, "kimi-k2.7-code")
        self.assertEqual(route.family, "kimi")
        self.assertEqual(route.tier, "balanced")
        self.assertIn(route.route_id, inferred)
        # Identity only for the runtime that actually observed it.
        self.assertTrue(effective.identity_allowed(
            (route.route_id, "opencode", "opencode-zen", "kimi-k2.7-code", "kimi", "medium")))
        self.assertFalse(effective.identity_allowed(
            (route.route_id, "codex", "opencode-zen", "kimi-k2.7-code", "kimi", "medium")))
        # Every curated route survives untouched.
        base = routing_catalog.build_snapshot(CATALOG, roster, config)
        self.assertTrue(set(base.routes) <= set(effective.routes))

    def test_curated_canonical_twin_is_never_synthesized(self):
        config, roster = _fixtures()
        config["routing"]["discovered_providers"] = ["anthropic"]
        # "opus" is curated in routes.v1.toml for anthropic — the discovered pool
        # offering the same id must not produce a synthesized twin.
        inventory = {("claude-code", "anthropic"): {"opus"}}
        effective, inferred = routing_catalog.build_effective_snapshot(CATALOG, roster, config, inventory)
        self.assertEqual(inferred, frozenset())
        base = routing_catalog.build_snapshot(CATALOG, roster, config)
        self.assertEqual(len(effective.routes), len(base.routes))

    def test_catalog_exclude_vetoes_a_discovered_id(self):
        config, roster = _fixtures()
        config["routing"]["discovered_providers"] = ["opencode-zen"]
        config["catalog"]["exclude"] = ["opencode-zen:kimi-k2.7-code"]
        inventory = {("opencode", "opencode-zen"): {"kimi-k2.7-code", "glm-5.2"}}
        effective, inferred = routing_catalog.build_effective_snapshot(CATALOG, roster, config, inventory)
        models = {r.model for r in effective.routes if r.provider == "opencode-zen"}
        self.assertEqual(models, {"glm-5.2"})
        self.assertEqual(len(inferred), 1)

    def test_unaudited_provider_in_config_is_ignored(self):
        config, roster = _fixtures()
        # Bypass load-time validation on purpose to prove the builder's own guard.
        config["routing"]["discovered_providers"] = ["evil-provider"]
        inventory = {("opencode", "evil-provider"): {"model-x"}}
        effective, inferred = routing_catalog.build_effective_snapshot(CATALOG, roster, config, inventory)
        self.assertEqual(inferred, frozenset())

    def test_synthesized_priority_always_loses_to_curated(self):
        config, roster = _fixtures()
        config["routing"]["discovered_providers"] = ["opencode-zen"]
        inventory = {("opencode", "opencode-zen"): {"kimi-k2.7-code"}}
        effective, _ = routing_catalog.build_effective_snapshot(CATALOG, roster, config, inventory)
        curated_max = max(r.curated_priority for r in effective.routes if r.provider != "opencode-zen")
        synthesized_min = min(r.curated_priority for r in effective.routes if r.provider == "opencode-zen")
        self.assertGreater(synthesized_min, curated_max)


class ConfigValidationTests(unittest.TestCase):
    def test_discovered_providers_key_validates_and_defaults_empty(self):
        config = models_config.load_config()
        self.assertEqual(config["routing"]["discovered_providers"], [])
        self.assertNotIn("opencode-zen", models_config.ROUTING_PROVIDERS)  # closed set untouched

    def test_emit_preserves_discovered_providers_and_exclude(self):
        config = models_config.load_config()
        config["routing"]["discovered_providers"] = ["opencode-zen"]
        config["catalog"]["exclude"] = ["opencode-zen:bad-model"]
        text = models_config.emit(config)
        self.assertIn('discovered_providers = ["opencode-zen"]', text)
        self.assertIn('exclude = ["opencode-zen:bad-model"]', text)

    def test_emit_of_an_untouched_config_has_no_new_lines(self):
        text = models_config.emit(models_config.load_config())
        self.assertNotIn("discovered_providers", text)
        self.assertNotIn("exclude =", text)


class ServiceSealBackCompatTests(unittest.TestCase):
    def test_inferred_ids_default_is_empty_for_test_compositions(self):
        from routing_core.service import RoutingService
        config, roster = _fixtures()
        snapshot = routing_catalog.build_snapshot(CATALOG, roster, config)
        service = RoutingService._for_tests(snapshot, roster, {})
        self.assertEqual(service._inferred_ids, frozenset())


if __name__ == "__main__":
    unittest.main()
