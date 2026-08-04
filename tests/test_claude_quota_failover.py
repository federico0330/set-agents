"""Feature 017 PKG-C1 (ADR-0029) — Claude-Code-lane quota failover.

Unit tests over the two pure pieces: the second settled signature in
`classify_pi_terminal_error`, and `_classify_result`'s normalization of the
Claude Code error document into that signature. The durable rail itself
(`close_exhausted_and_authorize_replacement`) is feature 011's and stays
covered by its own immutable tests.
"""

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ai/scripts"))

import claude_code_spawn  # noqa: E402
from routing_core.domain import classify_pi_terminal_error  # noqa: E402


def _doc(**overrides):
    base = {"is_error": True, "subtype": "error_during_execution",
            "api_error_status": 429,
            "result": "Claude API error: you are out of extra usage for this billing cycle"}
    base.update(overrides)
    return json.dumps(base)


class SecondSettledSignatureTests(unittest.TestCase):
    def test_claude_lane_429_usage_marker_is_quota_exhausted(self):
        normalized = {"settled": True, "provider": "anthropic", "lane": "claude-code", "http_status": 429,
                      "type": "error_during_execution", "marker": "out of extra usage today"}
        self.assertEqual(classify_pi_terminal_error(normalized), "quota_exhausted")

    def test_usage_limit_wording_also_matches(self):
        normalized = {"settled": True, "provider": "anthropic", "lane": "claude-code", "http_status": 429,
                      "type": "x", "marker": "You have reached your usage limit."}
        self.assertEqual(classify_pi_terminal_error(normalized), "quota_exhausted")

    def test_the_original_pi_signature_is_untouched(self):
        normalized = {"settled": True, "provider": "anthropic", "http_status": 400,
                      "type": "invalid_request_error", "marker": "out of extra usage"}
        self.assertEqual(classify_pi_terminal_error(normalized), "quota_exhausted")

    def test_a_plain_404_is_never_quota(self):
        normalized = {"settled": True, "provider": "anthropic", "http_status": 404,
                      "type": "not_found_error", "marker": "model not found"}
        self.assertEqual(classify_pi_terminal_error(normalized), "unknown_failure")

    def test_429_without_the_marker_is_not_quota(self):
        normalized = {"settled": True, "provider": "anthropic", "lane": "claude-code", "http_status": 429,
                      "type": "x", "marker": "overloaded, retry shortly"}
        self.assertEqual(classify_pi_terminal_error(normalized), "unknown_failure")


    def test_429_without_the_lane_discriminator_is_not_quota(self):
        # The immutable 011 contract: a Pi-shaped dict at 429 never classifies.
        normalized = {"settled": True, "provider": "anthropic", "http_status": 429,
                      "type": "invalid_request_error", "marker": "out of extra usage"}
        self.assertEqual(classify_pi_terminal_error(normalized), "unknown_failure")

class ClassifyResultQuotaTests(unittest.TestCase):
    def test_quota_error_document_lands_in_detail(self):
        outcome, detail = claude_code_spawn._classify_result(1, _doc(), "", "anthropic", "sonnet")
        self.assertEqual(outcome, "failure")
        self.assertIn("quota_error", detail)
        self.assertEqual(classify_pi_terminal_error(detail["quota_error"]), "quota_exhausted")

    def test_non_quota_error_has_no_quota_error_key(self):
        doc = _doc(api_error_status=404, result="model not found")
        outcome, detail = claude_code_spawn._classify_result(1, doc, "", "anthropic", "sonnet")
        self.assertEqual(outcome, "failure")
        self.assertNotIn("quota_error", detail)

    def test_success_path_is_untouched(self):
        doc = json.dumps({"is_error": False, "result": "done",
                          "modelUsage": {"claude-sonnet-5": {"canonicalModel": "claude-sonnet-5"}}})
        outcome, detail = claude_code_spawn._classify_result(0, doc, "", "anthropic", "sonnet")
        self.assertEqual(outcome, "success")
        self.assertNotIn("quota_error", detail)


if __name__ == "__main__":
    unittest.main()
