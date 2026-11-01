"""Tests for evidence quote verification."""
import unittest

from primordial.connectors.dataset_loader import get_sample_discussion_by_id
from primordial.models import EvidenceQuote
from primordial.verification.evidence import (
    find_quote_in_text,
    verify_evidence_quote,
    verify_evidence_quotes,
)


class TestEvidenceVerification(unittest.TestCase):

    def setUp(self):
        self.discussion = get_sample_discussion_by_id("gh:astral-sh/uv/issues/1042")

    def test_exact_quote_match(self):
        text = "YAML is notoriously difficult to parse securely due to arbitrary type coercion."
        verified, conf, offset, snippet = find_quote_in_text(
            "YAML is notoriously difficult to parse securely", text
        )
        self.assertTrue(verified)
        self.assertEqual(conf, 1.0)
        self.assertEqual(offset, 0)

    def test_fuzzy_quote_match(self):
        text = "YAML is notoriously difficult to parse securely due to arbitrary type coercion."
        verified, conf, offset, snippet = find_quote_in_text(
            "yaml is notoriously difficult to parse securely", text
        )
        self.assertTrue(verified)
        self.assertGreaterEqual(conf, 0.9)

    def test_nonexistent_quote(self):
        text = "We should use TOML for configuration."
        verified, conf, offset, snippet = find_quote_in_text(
            "Completely unrelated sentence that never appeared", text
        )
        self.assertFalse(verified)
        self.assertEqual(conf, 0.0)

    def test_verify_evidence_quote_against_discussion(self):
        quote = EvidenceQuote(
            id="eq-1",
            quote="YAML is notoriously difficult to parse securely due to arbitrary type coercion and code execution CVEs in standard parsers.",
            author="security-auditor-eva",
            comment_id="c-102",
            comment_url="",
        )
        verified_eq = verify_evidence_quote(quote, self.discussion)
        self.assertTrue(verified_eq.verified)
        self.assertGreaterEqual(verified_eq.confidence, 0.95)
        self.assertEqual(verified_eq.comment_id, "c-102")
        self.assertTrue(bool(verified_eq.comment_url))


if __name__ == "__main__":
    unittest.main()
