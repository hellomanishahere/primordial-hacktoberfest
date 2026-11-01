"""Tests for the 3-Stage AI Decision Extraction Pipeline."""
import unittest

from primordial.ai.pipeline import PrimordialDecisionPipeline
from primordial.connectors.dataset_loader import get_sample_discussion_by_id


class TestPipeline(unittest.TestCase):

    def setUp(self):
        self.pipeline = PrimordialDecisionPipeline()
        self.discussion = get_sample_discussion_by_id("gh:astral-sh/uv/issues/1042")

    def test_pipeline_execution(self):
        self.assertIsNotNone(self.discussion)
        res = self.pipeline.process_discussion(self.discussion)

        # Check stages
        self.assertEqual(len(res.stages), 3)

        # Stage 1: Llama 3.2-3B
        st1 = res.stages[0]
        self.assertEqual(st1.stage_num, 1)
        self.assertEqual(st1.model_name, "Llama 3.2-3B-Instruct")
        self.assertIn("problem_statement", st1.output)
        self.assertIn("participants", st1.output)

        # Stage 2: Phi-3.5-mini
        st2 = res.stages[1]
        self.assertEqual(st2.stage_num, 2)
        self.assertEqual(st2.model_name, "Phi-3.5-mini-instruct")
        self.assertIn("proposals", st2.output)
        self.assertIn("rejected_alternatives", st2.output)
        self.assertGreater(len(st2.output["rejected_alternatives"]), 0)

        # Stage 3: Qwen 2.5-Coder-7B
        st3 = res.stages[2]
        self.assertEqual(st3.stage_num, 3)
        self.assertEqual(st3.model_name, "Qwen 2.5-Coder-7B-Instruct")
        self.assertIn("accepted_option", st3.output)

        # Final Decision Record
        dec = res.final_decision
        self.assertIn("TOML", dec.accepted_option)
        self.assertEqual(dec.status, "Accepted")
        self.assertGreater(len(dec.rejected_alternatives), 0)
        self.assertGreater(len(dec.evidence_quotes), 0)
        self.assertTrue(len(dec.madr_content) > 100)

        # Verify rejected alternatives details
        yaml_rej = next(
            (ra for ra in dec.rejected_alternatives if "yaml" in ra.name.lower()), None
        )
        self.assertIsNotNone(yaml_rej)
        self.assertGreater(len(yaml_rej.rejection_reasons), 0)
        self.assertTrue(bool(yaml_rej.key_objection_quote))


if __name__ == "__main__":
    unittest.main()
