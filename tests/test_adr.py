"""Tests for MADR generation."""
import unittest

from primordial.adr.generator import generate_madr
from primordial.ai.pipeline import PrimordialDecisionPipeline
from primordial.connectors.dataset_loader import get_sample_discussion_by_id


class TestADRGenerator(unittest.TestCase):

    def setUp(self):
        self.pipeline = PrimordialDecisionPipeline()
        self.discussion = get_sample_discussion_by_id("gh:astral-sh/uv/issues/1042")
        self.result = self.pipeline.process_discussion(self.discussion)
        self.decision = self.result.final_decision

    def test_madr_sections_present(self):
        madr = generate_madr(self.decision, self.discussion)

        self.assertIn("# ADR-", madr)
        self.assertIn("* Status: **Accepted**", madr)
        self.assertIn("## Context and Problem Statement", madr)
        self.assertIn("## Considered Options", madr)
        self.assertIn("## Decision Outcome", madr)
        self.assertIn("### Positive Consequences", madr)
        self.assertIn("## Pros and Cons of Rejected Options", madr)
        self.assertIn("## Code Grounding & Impacted Components", madr)
        self.assertIn("## Verified Evidence Citations", madr)


if __name__ == "__main__":
    unittest.main()
